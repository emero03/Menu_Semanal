"""Gestor de datos de Menú Semanal: recetas, semanas planificadas y ajustes."""

from __future__ import annotations

from collections.abc import Callable
from copy import deepcopy
from datetime import date, timedelta
import logging
import random
import re
from typing import Any
import uuid

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .catalog import _stems, normalize
from .const import (
    CATEGORIES,
    CATEGORY_IDS,
    DAY_NAMES,
    DAYS,
    DEFAULT_ICON,
    DEFAULT_SETTINGS,
    DEFAULT_UNIT,
    HISTORY_WEEKS,
    KEEP_WEEKS,
    MAX_INGREDIENTS,
    MAX_RECIPES,
    MEAL_NAMES,
    MEALS,
    SAVE_DELAY,
    SLOTS,
    STORAGE_KEY,
    STORAGE_VERSION,
    UNITS,
)
from .examples import EXAMPLES
from .nutrition import analyze, grams_of, match_food
from .pantry import check as pantry_check, pantry_ratio
from .planner import FREE, Context, summarize

_LOGGER = logging.getLogger(__name__)
_HEX = re.compile(r"^#[0-9a-fA-F]{6}$")
_WEEK = re.compile(r"^(\d{4})-W(\d{2})$")


class MenuError(Exception):
    """Error de operación (receta inexistente, datos no válidos...)."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


# ---------------------------------------------------------------- semanas
def week_key(day: date) -> str:
    year, week, _ = day.isocalendar()
    return f"{year}-W{week:02d}"


def week_monday(key: str) -> date:
    match = _WEEK.match(key or "")
    if not match:
        raise MenuError("invalid_week", f"Semana no válida: {key}")
    try:
        return date.fromisocalendar(int(match.group(1)), int(match.group(2)), 1)
    except ValueError as err:
        raise MenuError("invalid_week", f"Semana no válida: {key}") from err


def shift_week(key: str, weeks: int) -> str:
    return week_key(week_monday(key) + timedelta(weeks=weeks))


def today() -> date:
    return dt_util.now().date()


def resolve_week(value: str | None) -> str:
    """"current"/"next"/"previous", una fecha (2026-10-12) o una semana ISO (2026-W42)."""
    text = normalize(str(value or "current"))
    current = week_key(today())
    if text in ("current", "actual", "esta", "esta semana", "hoy"):
        return current
    if text in ("next", "siguiente", "proxima", "la que viene", "proxima semana", "semana que viene"):
        return shift_week(current, 1)
    if text in ("previous", "anterior", "pasada", "semana pasada"):
        return shift_week(current, -1)
    upper = str(value).strip().upper()
    if _WEEK.match(upper):
        week_monday(upper)
        return upper
    try:
        return week_key(date.fromisoformat(str(value).strip()[:10]))
    except ValueError as err:
        raise MenuError("invalid_week", f"Semana no válida: {value}") from err


def _new_id() -> str:
    return uuid.uuid4().hex[:12]


def _now() -> float:
    return round(dt_util.utcnow().timestamp(), 3)


def _clean_text(value: Any, limit: int) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()[:limit]
    return text[:1].upper() + text[1:] if text else text


def _empty_slot() -> dict[str, Any]:
    return {"recipe_id": None, "free": False, "locked": False, "rejected": []}


def _number(value: Any, low: float, high: float, default: float | None) -> float | None:
    if value is None or value == "":
        return default
    try:
        number = float(str(value).replace(",", "."))
    except (TypeError, ValueError):
        return default
    if number != number:  # NaN
        return default
    return max(low, min(high, number))


class MenuManager:
    """Fuente única de verdad. Las operaciones son síncronas (bucle de eventos), salvo
    las que calculan un menú, que se hacen en un hilo aparte para no bloquear Home Assistant."""

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass
        self._store: Store[dict[str, Any]] = Store(hass, STORAGE_VERSION, STORAGE_KEY)
        self.data: dict[str, Any] = {}
        self._infos: dict[str, dict[str, Any]] = {}
        self._listeners: list[Callable[[], None]] = []
        self._deleted: dict[str, tuple[dict[str, Any], list[tuple[str, int, dict[str, Any]]]]] = {}
        self.siblings: Any = None  # puente con Despensa y Cesta (lo pone __init__)

    # ------------------------------------------------------------------ carga
    async def async_load(self) -> None:
        stored = await self._store.async_load() or {}
        self.data = {
            "recipes": stored.get("recipes", []),
            "weeks": stored.get("weeks", {}),
            "settings": {**DEFAULT_SETTINGS, **stored.get("settings", {})},
            "equivalences": stored.get("equivalences", {}),
            "colors": stored.get("colors", {}),
        }
        for recipe in self.recipes:
            self._infos[recipe["id"]] = analyze(recipe)

    @callback
    def async_add_listener(self, listener: Callable[[], None]) -> Callable[[], None]:
        self._listeners.append(listener)

        @callback
        def remove() -> None:
            if listener in self._listeners:
                self._listeners.remove(listener)

        return remove

    @callback
    def _changed(self, save: bool = True) -> None:
        if save:
            self._prune()
            self._store.async_delay_save(lambda: self.data, SAVE_DELAY)
        for listener in list(self._listeners):
            try:
                listener()
            except Exception:  # pragma: no cover - un oyente roto no debe romper el resto
                _LOGGER.exception("Error notificando un cambio de Menú Semanal")

    @callback
    def siblings_changed(self) -> None:
        """La Despensa o la Cesta han cambiado: se avisa al panel (sin guardar nada)."""
        self._changed(save=False)

    def _prune(self) -> None:
        oldest = shift_week(week_key(today()), -KEEP_WEEKS)
        for key in [k for k in self.data["weeks"] if k < oldest]:
            del self.data["weeks"][key]

    # -------------------------------------------------------------- utilidades
    @property
    def recipes(self) -> list[dict[str, Any]]:
        return self.data["recipes"]

    @property
    def settings(self) -> dict[str, Any]:
        return self.data["settings"]

    @property
    def categories(self) -> list[dict[str, str]]:
        colors = self.data["colors"]
        return [{**c, "color": colors.get(c["id"], c["color"])} for c in CATEGORIES]

    def get_recipe(self, recipe_id: str) -> dict[str, Any]:
        for recipe in self.recipes:
            if recipe["id"] == recipe_id:
                return recipe
        raise MenuError("not_found", "Esa receta ya no existe")

    def info(self, recipe_id: str) -> dict[str, Any]:
        return self._infos[recipe_id]

    def _by_id(self) -> dict[str, dict[str, Any]]:
        return {r["id"]: r for r in self.recipes}

    def find_recipe(self, name: str) -> dict[str, Any] | None:
        key = normalize(name)
        words = _stems(name)
        for recipe in self.recipes:
            if normalize(recipe["name"]) == key:
                return recipe
        return next((r for r in self.recipes if _stems(r["name"]) == words), None)

    # ---------------------------------------------------------------- recetas
    def _clean_recipe(self, payload: dict[str, Any], existing: dict[str, Any] | None) -> dict[str, Any]:
        name = _clean_text(payload.get("name"), 80)
        if not name:
            raise MenuError("invalid_name", "La receta necesita un nombre")
        other = self.find_recipe(name)
        if other is not None and (existing is None or other["id"] != existing["id"]):
            raise MenuError("duplicate", f"Ya tienes una receta llamada «{other['name']}»")

        meals = [m for m in MEALS if m in (payload.get("meals") or [])]
        if not meals:
            raise MenuError("meals_required", "Elige si la receta es para comidas, para cenas o para las dos")

        ingredients = []
        for raw in (payload.get("ingredients") or [])[:MAX_INGREDIENTS]:
            ing_name = _clean_text((raw or {}).get("name"), 80)
            if not ing_name:
                continue
            unit = raw.get("unit") if raw.get("unit") in UNITS else DEFAULT_UNIT
            qty = None if unit == "gusto" else _number(raw.get("qty"), 0, 100000, None)
            if qty is not None:
                qty = round(qty, 2)
                if qty == int(qty):
                    qty = int(qty)
            ingredients.append({"name": ing_name, "qty": qty, "unit": unit})

        recipe = {
            "id": existing["id"] if existing else _new_id(),
            "name": name,
            "icon": str(payload.get("icon") or "").strip()[:16],
            "meals": meals,
            "category": payload.get("category") if payload.get("category") in CATEGORY_IDS else None,
            "rating": int(_number(payload.get("rating"), 1, 5, 3)),
            "servings": int(_number(payload.get("servings"), 1, 20, 4)),
            "ingredients": ingredients,
            "base": _clean_text(payload.get("base"), 40),
            "kcal": None,
            "notes": str(payload.get("notes") or "").strip()[:4000],
            "created_at": existing["created_at"] if existing else _now(),
            "updated_at": _now(),
        }
        kcal = _number(payload.get("kcal"), 0, 3000, None)
        recipe["kcal"] = int(kcal) if kcal else None
        if recipe["category"] is None:
            recipe["category"] = analyze(recipe)["suggested_category"]
        if not recipe["icon"]:
            recipe["icon"] = next((c["icon"] for c in CATEGORIES if c["id"] == recipe["category"]), DEFAULT_ICON)
        return recipe

    @callback
    def save_recipe(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Crea una receta, o la actualiza si trae el id de una existente."""
        existing = None
        if payload.get("id"):
            existing = self.get_recipe(payload["id"])
        elif len(self.recipes) >= MAX_RECIPES:
            raise MenuError("too_many", f"Como mucho {MAX_RECIPES} recetas")
        recipe = self._clean_recipe(payload, existing)
        if existing is not None:
            existing.clear()
            existing.update(recipe)
            recipe = existing
        else:
            self.recipes.append(recipe)
        self._infos[recipe["id"]] = analyze(recipe)
        self._changed()
        return recipe

    @callback
    def delete_recipe(self, recipe_id: str) -> dict[str, Any]:
        """Borra una receta y la quita de esta semana y de las siguientes."""
        recipe = self.get_recipe(recipe_id)
        self.recipes.remove(recipe)
        current = week_key(today())
        removed: list[tuple[str, int, dict[str, Any]]] = []
        for key, week in self.data["weeks"].items():
            if key < current:
                continue
            for index, slot in enumerate(week["slots"]):
                if slot.get("recipe_id") == recipe_id:
                    removed.append((key, index, dict(slot)))
                    week["slots"][index] = _empty_slot()
        self._deleted = {recipe_id: (recipe, removed)}
        self._changed()
        return recipe

    @callback
    def restore_recipe(self, recipe_id: str) -> dict[str, Any]:
        """Deshace el último "Borrar receta" (y la vuelve a poner en su sitio)."""
        if recipe_id not in self._deleted:
            raise MenuError("not_found", "Ya no se puede recuperar")
        recipe, removed = self._deleted.pop(recipe_id)
        if self.find_recipe(recipe["name"]) is None:
            self.recipes.append(recipe)
            self._infos[recipe["id"]] = analyze(recipe)
            for key, index, slot in removed:
                week = self.data["weeks"].get(key)
                if week is not None and not week["slots"][index].get("recipe_id"):
                    week["slots"][index] = slot
        self._changed()
        return recipe

    @callback
    def load_examples(self) -> int:
        """Añade las recetas de ejemplo que aún no tengas (por nombre)."""
        added = 0
        for example in EXAMPLES:
            if self.find_recipe(example["name"]) is not None:
                continue
            recipe = self._clean_recipe({**deepcopy(example), "servings": 4}, None)
            self.recipes.append(recipe)
            self._infos[recipe["id"]] = analyze(recipe)
            added += 1
        if added:
            self._changed()
        return added

    @callback
    def estimate(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Estimación nutricional de una receta que se está editando (sin guardarla)."""
        draft = {
            "servings": int(_number(payload.get("servings"), 1, 20, 4)),
            "ingredients": [
                {
                    "name": str(i.get("name") or ""),
                    "qty": _number(i.get("qty"), 0, 100000, None),
                    "unit": i.get("unit") if i.get("unit") in UNITS else DEFAULT_UNIT,
                }
                for i in (payload.get("ingredients") or [])[:MAX_INGREDIENTS]
            ],
            "base": payload.get("base") or "",
            "kcal": _number(payload.get("kcal"), 0, 3000, None),
        }
        return analyze(draft)

    # ---------------------------------------------------------------- semanas
    def _week(self, key: str, create: bool = False) -> dict[str, Any] | None:
        week_monday(key)
        week = self.data["weeks"].get(key)
        if week is None and create:
            week = {"slots": [_empty_slot() for _ in range(SLOTS)], "generated_at": None}
            self.data["weeks"][key] = week
        return week

    def slots(self, key: str) -> list[dict[str, Any]]:
        week = self._week(key)
        return deepcopy(week["slots"]) if week else [_empty_slot() for _ in range(SLOTS)]

    def _history(self, key: str) -> dict[str, int]:
        """Hace cuántas semanas se comió cada receta (para no repetir demasiado)."""
        history: dict[str, int] = {}
        for ago in range(HISTORY_WEEKS, 0, -1):
            week = self.data["weeks"].get(shift_week(key, -ago))
            if not week:
                continue
            for slot in week["slots"]:
                if slot.get("recipe_id"):
                    history[slot["recipe_id"]] = ago
        return history

    def _context(self, key: str, seed: int | None = None) -> Context:
        items = self.siblings.despensa_items() if self.siblings else None
        pantry: dict[str, float] = {}
        if items and self.settings.get("prefer_pantry"):
            pantry = {r["id"]: pantry_ratio(r, items) for r in self.recipes}
        if seed is None:
            seed = random.getrandbits(31) or 1
        return Context(
            [deepcopy(r) for r in self.recipes],
            {k: deepcopy(v) for k, v in self._infos.items()},
            dict(self.settings),
            self._history(key),
            pantry,
            seed,
        )

    async def async_generate(self, key: str, seed: int | None = None) -> dict[str, Any]:
        """Genera la semana. Se respetan los platos fijados (📌) y los huecos libres."""
        if not self.recipes:
            raise MenuError("no_recipes", "Primero crea algunas recetas")
        if not any("lunch" in r["meals"] for r in self.recipes) and not any(
            "dinner" in r["meals"] for r in self.recipes
        ):
            raise MenuError("no_recipes", "Ninguna receta es para comidas ni para cenas")
        previous = self.slots(key)
        fixed: list[Any] = []
        for slot in previous:
            if slot.get("free"):
                fixed.append(FREE)
            elif slot.get("locked") and slot.get("recipe_id"):
                fixed.append(slot["recipe_id"])
            else:
                fixed.append(None)
        ctx = self._context(key, seed)
        result = await self.hass.async_add_executor_job(ctx.generate, fixed)
        week = self._week(key, create=True)
        new_slots = []
        for index, cand in enumerate(result):
            old = week["slots"][index]
            if old.get("free"):
                new_slots.append(dict(old))
            elif old.get("locked") and old.get("recipe_id") and old["recipe_id"] in ctx.by_id:
                new_slots.append({**old, "rejected": []})
            else:
                new_slots.append({"recipe_id": cand.id if cand else None, "free": False, "locked": False, "rejected": []})
        week["slots"] = new_slots
        week["generated_at"] = _now()
        self._changed()
        return {"previous": previous, "slots": deepcopy(new_slots)}

    async def async_change(self, key: str, index: int) -> dict[str, Any]:
        """CAMBIO: busca otra receta parecida para ese plato."""
        week = self._week(key, create=True)
        slot = week["slots"][index]
        previous = dict(slot)
        ids = [s.get("recipe_id") if not s.get("free") else None for s in week["slots"]]
        rejected = list(slot.get("rejected") or [])
        if slot.get("recipe_id") and slot["recipe_id"] not in rejected:
            rejected.append(slot["recipe_id"])
        ctx = self._context(key)
        cand, restarted = await self.hass.async_add_executor_job(ctx.change, ids, index, rejected)
        if cand is None:
            meal = MEAL_NAMES[MEALS[index % 2]].lower()
            raise MenuError("no_alternative", f"No hay otra receta para la {meal}")
        if restarted:
            rejected = [slot["recipe_id"]] if slot.get("recipe_id") else []
        slot = week["slots"][index] = {
            "recipe_id": cand.id,
            "free": False,
            "locked": bool(previous.get("locked")),
            "rejected": rejected,
        }
        self._changed()
        return {"previous": previous, "slot": dict(slot), "restarted": restarted}

    @callback
    def set_slot(self, key: str, index: int, recipe_id: str | None, free: bool = False) -> dict[str, Any]:
        """Elegir una receta a mano (queda fijada), dejar el hueco libre o vaciarlo."""
        if recipe_id:
            recipe = self.get_recipe(recipe_id)
            meal = MEALS[index % 2]
            if meal not in recipe["meals"]:
                raise MenuError("wrong_meal", f"«{recipe['name']}» no está marcada para la {MEAL_NAMES[meal].lower()}")
        week = self._week(key, create=True)
        previous = dict(week["slots"][index])
        if free:
            week["slots"][index] = {"recipe_id": None, "free": True, "locked": False, "rejected": []}
        elif recipe_id:
            week["slots"][index] = {"recipe_id": recipe_id, "free": False, "locked": True, "rejected": []}
        else:
            week["slots"][index] = _empty_slot()
        self._changed()
        return previous

    @callback
    def lock_slot(self, key: str, index: int, locked: bool) -> None:
        week = self._week(key, create=True)
        slot = week["slots"][index]
        if not slot.get("recipe_id"):
            raise MenuError("empty_slot", "No hay ningún plato que fijar")
        slot["locked"] = bool(locked)
        self._changed()

    @callback
    def restore_week(self, key: str, slots: list[dict[str, Any]]) -> None:
        """Deshacer: vuelve a dejar la semana como estaba."""
        if len(slots) != SLOTS:
            raise MenuError("invalid_slots", "Semana no válida")
        known = {r["id"] for r in self.recipes}
        clean = []
        for slot in slots:
            rid = slot.get("recipe_id")
            clean.append(
                {
                    "recipe_id": rid if rid in known else None,
                    "free": bool(slot.get("free")),
                    "locked": bool(slot.get("locked")) and rid in known,
                    "rejected": [r for r in slot.get("rejected") or [] if r in known],
                }
            )
        week = self._week(key, create=True)
        week["slots"] = clean
        self._changed()

    @callback
    def clear_week(self, key: str) -> list[dict[str, Any]]:
        previous = self.slots(key)
        if key in self.data["weeks"]:
            del self.data["weeks"][key]
            self._changed()
        return previous

    # ------------------------------------------------------- despensa y cesta
    def lines(self, key: str) -> tuple[list[dict[str, Any]], int]:
        """Ingredientes de la semana escalados a los comensales. En la semana en curso, desde hoy."""
        monday = week_monday(key)
        now = today()
        from_day = 0
        if monday <= now < monday + timedelta(days=7):
            from_day = now.weekday()
        elif monday + timedelta(days=7) <= now:
            from_day = DAYS
        people = int(self.settings.get("people") or 2)
        recipes = self._by_id()
        out: list[dict[str, Any]] = []
        for index, slot in enumerate(self.slots(key)):
            day = index // 2
            if day < from_day or slot.get("free") or not slot.get("recipe_id"):
                continue
            recipe = recipes.get(slot["recipe_id"])
            if recipe is None:
                continue
            factor = people / max(1, int(recipe.get("servings") or 1))
            for ing in recipe["ingredients"]:
                qty = ing.get("qty")
                out.append(
                    {
                        "name": ing["name"],
                        "qty": None if qty is None else round(float(qty) * factor, 2),
                        "unit": ing.get("unit") or DEFAULT_UNIT,
                        "recipe_id": recipe["id"],
                        "recipe": recipe["name"],
                        "day": day,
                        "meal": MEALS[index % 2],
                    }
                )
        return out, from_day

    @callback
    def check(self, key: str) -> dict[str, Any]:
        """Qué falta en la despensa para el menú de la semana."""
        lines, from_day = self.lines(key)
        items = self.siblings.despensa_items() if self.siblings else None
        in_cesta = self.siblings.cesta_names() if self.siblings else set()
        results = pantry_check(lines, items, in_cesta, self.data["equivalences"])
        return {
            "week": key,
            "from_day": from_day,
            "people": int(self.settings.get("people") or 2),
            "despensa": items is not None,
            "cesta": bool(self.siblings and self.siblings.cesta_available),
            "items": results,
            "missing": sum(1 for r in results if r["status"] == "missing"),
        }

    async def async_add_to_cesta(self, entries: list[dict[str, Any]]) -> list[str]:
        if not self.siblings or not self.siblings.cesta_available:
            raise MenuError("no_cesta", "Cesta no está instalada o no está configurada")
        return await self.siblings.async_add_to_cesta(entries)

    # ----------------------------------------------------------------- ajustes
    @callback
    def set_settings(self, **changes: Any) -> None:
        for key, value in changes.items():
            if key == "people":
                self.settings[key] = int(_number(value, 1, 12, 2))
            elif key == "kcal_day":
                self.settings[key] = int(_number(value, 1000, 4500, 2000))
            elif key in ("batch", "prefer_pantry"):
                self.settings[key] = bool(value)
        self._changed()

    @callback
    def set_color(self, category: str, color: str | None) -> None:
        if category not in CATEGORY_IDS:
            raise MenuError("invalid_category", "Tipo de plato no válido")
        if color and not _HEX.match(color):
            raise MenuError("invalid_color", "Color no válido")
        default = next(c["color"] for c in CATEGORIES if c["id"] == category)
        if not color or color.lower() == default.lower():
            self.data["colors"].pop(category, None)
        else:
            self.data["colors"][category] = color
        self._changed()

    @callback
    def set_equivalence(self, name: str, grams: float | None, volume: bool = False) -> None:
        """Cuánto pesa (o cuánto líquido trae) 1 unidad de un producto de la despensa."""
        key = normalize(name)
        if not key:
            raise MenuError("invalid_name", "Falta el producto")
        if not grams:
            self.data["equivalences"].pop(key, None)
        else:
            self.data["equivalences"][key] = {
                "name": _clean_text(name, 80),
                "grams": round(float(grams), 1),
                "volume": bool(volume),
            }
        self._changed()

    # -------------------------------------------------------------- estado
    def _base_amounts(self, slots: list[dict[str, Any]]) -> dict[str, dict[str, float]]:
        """Cuánto hay que cocinar de cada base automática (gramos para los comensales)."""
        people = int(self.settings.get("people") or 2)
        recipes = self._by_id()
        amounts: dict[str, dict[str, float]] = {}
        for slot in slots:
            recipe = recipes.get(slot.get("recipe_id") or "")
            if recipe is None or slot.get("free"):
                continue
            factor = people / max(1, int(recipe.get("servings") or 1))
            for ing in recipe["ingredients"]:
                food = match_food(ing["name"])
                if food is None or not food["base"]:
                    continue
                grams = grams_of(ing, food)
                if not grams:
                    continue
                key = normalize(food["base"])
                entry = amounts.setdefault(key, {"grams": 0.0})
                entry["grams"] = round(entry["grams"] + grams * factor)
        return amounts

    @callback
    def week_snapshot(self, key: str) -> dict[str, Any]:
        slots = self.slots(key)
        week = self.data["weeks"].get(key) or {}
        return {
            "key": key,
            "monday": week_monday(key).isoformat(),
            "slots": slots,
            "generated_at": week.get("generated_at"),
            "summary": summarize(slots, self._by_id(), self._infos, self.settings, self._base_amounts(slots)),
        }

    @callback
    def snapshot(self) -> dict[str, Any]:
        """Estado completo para el panel."""
        current = week_key(today())
        keys = set(self.data["weeks"]) | {current, shift_week(current, 1)}
        siblings = self.siblings
        items = siblings.despensa_items() if siblings else None
        return {
            "recipes": [{**deepcopy(r), "info": deepcopy(self._infos[r["id"]])} for r in self.recipes],
            "weeks": {k: self.week_snapshot(k) for k in sorted(keys)},
            "settings": dict(self.settings),
            "categories": self.categories,
            "equivalences": sorted(self.data["equivalences"].values(), key=lambda e: normalize(e["name"])),
            "today": today().isoformat(),
            "current_week": current,
            "despensa": {
                "available": items is not None,
                "items": [
                    {k: i.get(k) for k in ("id", "name", "icon", "unit", "stock", "department")} for i in items or []
                ],
            },
            "cesta": {"available": bool(siblings and siblings.cesta_available)},
        }

    # ------------------------------------------------------------ textos
    def day_text(self, key: str, day: int) -> str:
        slots = self.slots(key)
        recipes = self._by_id()
        parts = []
        for m, meal in enumerate(MEALS):
            slot = slots[2 * day + m]
            if slot.get("free"):
                parts.append(f"{MEAL_NAMES[meal]}: libre")
            elif recipe := recipes.get(slot.get("recipe_id") or ""):
                parts.append(f"{MEAL_NAMES[meal]}: {recipe['icon']} {recipe['name']}")
            else:
                parts.append(f"{MEAL_NAMES[meal]}: sin planificar")
        return f"{DAY_NAMES[day]}. " + ". ".join(parts)

    def menu_text(self, key: str) -> str:
        return "\n".join(self.day_text(key, d) for d in range(DAYS))

    def meal_today(self, meal: str) -> tuple[dict[str, Any] | None, dict[str, Any]]:
        now = today()
        key = week_key(now)
        slot = self.slots(key)[2 * now.weekday() + MEALS.index(meal)]
        recipe = None
        if slot.get("recipe_id"):
            recipe = self._by_id().get(slot["recipe_id"])
        return recipe, slot
