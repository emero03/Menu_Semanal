"""Planificador del menú semanal.

Puntúa una semana completa (7 comidas + 7 cenas) y busca una buena combinación:

- **Valoración**: las recetas de 5 ★ salen más y pueden repetirse; las de 1 ★, de vez en cuando.
- **Día equilibrado**: kcal de comida + cena cerca de su parte del objetivo diario, con
  proteína, verdura e hidratos, y sin dos platos del mismo tipo el mismo día.
- **Semana equilibrada** (recomendaciones AESAN): legumbres ≥ 4, pescado ≥ 3,
  carne ≤ 3 (poca roja y procesada), huevos ≤ 3 platos, algún plato de verdura.
- **Batch cooking**: premia platos distintos que comparten elaboración (carne picada,
  pollo, garbanzos... o la "base" que pongas en la receta) en días distintos.
- **Variedad**: penaliza repetir lo de las semanas anteriores según la valoración.
- **Despensa**: un pequeño empujón a las recetas cuyos ingredientes ya tienes.

La búsqueda es voraz con varios arranques aleatorios y luego mejora local (cambiar un
plato o intercambiar dos). Solo usa sumas, productos y comparaciones, y su propio
generador de números aleatorios, para que la vista previa en JavaScript dé el mismo
resultado con la misma semilla.
"""

from __future__ import annotations

from typing import Any, Final

from .const import DAYS, DINNER_SHARE, LUNCH_SHARE, SLOTS

FREE: Final = "free"  # hueco libre (comer fuera...): no se rellena

RATING_PREF: Final = {1: -3.0, 2: -1.0, 3: 1.0, 4: 2.5, 5: 4.0}
# Penalización por haberla comido hace N semanas (según su valoración)
RECENCY: Final = {
    5: {1: 2.5, 2: 0.5},
    4: {1: 4.0, 2: 1.5},
    3: {1: 5.0, 2: 2.5, 3: 1.0},
    2: {1: 7.0, 2: 5.0, 3: 3.0, 4: 1.0},
    1: {1: 10.0, 2: 8.0, 3: 6.0, 4: 4.0},
}
# Repetir una receta en la misma semana (por cada repetición)
REPEAT: Final = {5: 3.5, 4: 6.0, 3: 12.0, 2: 12.0, 1: 12.0}

# Objetivos semanales (para 14 platos, por persona). Se escalan si hay huecos libres.
# Legumbres, pescado y carne cuentan raciones (platos con suficiente cantidad, sea cual sea
# su componente principal); huevos cuenta huevos; verdura y cereal, platos de ese tipo.
WEEK_TARGETS: Final[list[dict[str, Any]]] = [
    {"id": "legumbre", "min": 4, "max": None, "weight": 5.0},
    {"id": "pescado", "min": 3, "max": 5, "weight": 4.0},
    {"id": "carne", "min": None, "max": 3, "weight": 4.0},
    {"id": "huevo", "min": None, "max": 4, "weight": 1.5},
    {"id": "verdura", "min": 2, "max": None, "weight": 2.0},
    {"id": "cereal", "min": None, "max": 4, "weight": 1.0},
]
MAX_RED: Final = 1.5  # platos con carne roja a la semana
MAX_PROCESSED: Final = 1.0  # platos con embutido/procesada

# Mínimos diarios por persona entre comida y cena
DAY_PROTEIN: Final = 35.0
DAY_VEG: Final = 250.0
DAY_CARBS: Final = 60.0
MEAL_VEG: Final = 40.0

BATCH_BONUS: Final = 1.5
PANTRY_BONUS: Final = 1.5

RESTARTS: Final = 6
MAX_CANDIDATES: Final = 20
PASSES: Final = 2
RANK_WEIGHTS: Final = (0.55, 0.25, 0.13, 0.07)
CHANGE_WEIGHTS: Final = (0.6, 0.28, 0.12)


class Rng:
    """mulberry32: el mismo generador en Python y en la vista previa (JavaScript)."""

    def __init__(self, seed: int) -> None:
        self.a = seed & 0xFFFFFFFF

    def random(self) -> float:
        m = 0xFFFFFFFF
        self.a = (self.a + 0x6D2B79F5) & m
        a = self.a
        t = ((a ^ (a >> 15)) * (a | 1)) & m
        t = ((t + (((t ^ (t >> 7)) * (t | 61)) & m)) & m) ^ t
        return ((t ^ (t >> 14)) & m) / 4294967296

    def below(self, n: int) -> int:
        return int(self.random() * n)


class Cand:
    """Receta preparada para puntuar rápido."""

    __slots__ = (
        "id", "recipe", "meals", "cat", "rating", "kcal", "protein", "carbs", "veg",
        "known", "bases", "red", "processed", "base_score", "counts",
    )

    def __init__(self, recipe: dict[str, Any], info: dict[str, Any], ctx_settings: dict[str, Any],
                 weeks_ago: int | None, pantry: float, jitter: float) -> None:
        self.id = recipe["id"]
        self.recipe = recipe
        self.meals = tuple(recipe.get("meals") or ())
        self.cat = recipe.get("category") or "otros"
        rating = int(recipe.get("rating") or 3)
        self.rating = 1 if rating < 1 else 5 if rating > 5 else rating
        self.known = bool(info.get("known")) or bool(info.get("kcal_manual"))
        self.kcal = info.get("kcal")
        self.protein = info["protein"] if info.get("protein") is not None else 20.0
        self.carbs = info["carbs"] if info.get("carbs") is not None else 35.0
        self.veg = info.get("veg_g", 0.0) if info.get("known") else 120.0
        self.bases = tuple(b["key"] for b in info.get("bases", []))
        self.counts = recipe_counts(self.cat, info)
        self.red = bool(info.get("red_meat"))
        self.processed = bool(info.get("processed"))
        recency = 0.0
        if weeks_ago is not None:
            recency = RECENCY[self.rating].get(weeks_ago, 0.0)
        bonus = PANTRY_BONUS * pantry if ctx_settings.get("prefer_pantry") else 0.0
        self.base_score = RATING_PREF[self.rating] + jitter + bonus - recency


def recipe_counts(cat: str, info: dict[str, Any]) -> dict[str, float]:
    """Lo que aporta un plato a los objetivos semanales."""
    portions = info.get("portions") if info.get("known") else None
    if portions:
        legume = 1.0 if portions["legumbre"] else 0.0
        fish = 1.0 if portions["pescado"] else 0.0
        meat = 1.0 if portions["carne"] else 0.0
        eggs = float(portions["huevos"])
    else:
        legume = 1.0 if cat == "legumbre" else 0.0
        fish = 1.0 if cat == "pescado" else 0.0
        meat = 1.0 if cat == "carne" else 0.0
        eggs = 2.0 if cat == "huevo" else 0.0
    return {
        "legumbre": legume,
        "pescado": fish,
        "carne": meat,
        "huevo": eggs,
        "verdura": 1.0 if cat == "verdura" else 0.0,
        "cereal": 1.0 if cat == "cereal" else 0.0,
    }


class Context:
    """Todo lo que necesita la puntuación de una semana."""

    def __init__(
        self,
        recipes: list[dict[str, Any]],
        infos: dict[str, dict[str, Any]],
        settings: dict[str, Any],
        history: dict[str, int] | None = None,
        pantry: dict[str, float] | None = None,
        seed: int = 1,
    ) -> None:
        self.rng = Rng(seed)
        self.settings = settings
        self.batch = bool(settings.get("batch", True))
        kcal_day = float(settings.get("kcal_day") or 2000)
        self.t_lunch = kcal_day * LUNCH_SHARE
        self.t_dinner = kcal_day * DINNER_SHARE
        history = history or {}
        pantry = pantry or {}
        self.cands: list[Cand] = []
        for recipe in recipes:
            # Un poco de azar por receta para que cada "Generar" dé una semana distinta
            jitter = self.rng.random()
            self.cands.append(
                Cand(recipe, infos[recipe["id"]], settings, history.get(recipe["id"]),
                     pantry.get(recipe["id"], 0.0), jitter)
            )
        self.by_id = {c.id: c for c in self.cands}
        self.by_meal = (
            [c for c in self.cands if "lunch" in c.meals],
            [c for c in self.cands if "dinner" in c.meals],
        )
        self.planned = SLOTS

    # ------------------------------------------------------------ puntuación
    def score(self, assign: list[Cand | None]) -> float:
        total = 0.0
        counts = {"legumbre": 0.0, "pescado": 0.0, "carne": 0.0, "huevo": 0.0, "verdura": 0.0, "cereal": 0.0}
        uses: dict[str, list[int]] = {}
        base_days: dict[str, list[int]] = {}
        base_ids: dict[str, list[str]] = {}
        red = 0
        processed = 0
        for s in range(SLOTS):
            r = assign[s]
            if r is None:
                continue
            total += r.base_score
            for key, value in r.counts.items():
                counts[key] += value
            if r.id in uses:
                uses[r.id].append(s)
            else:
                uses[r.id] = [s]
            if r.red:
                red += 1
            if r.processed:
                processed += 1
            if s >= 2:
                prev = assign[s - 2]
                if prev is not None and prev.cat == r.cat and r.cat != "otros":
                    total -= 0.75
            if self.batch:
                day = s // 2
                for key in r.bases:
                    days = base_days.get(key)
                    if days is None:
                        base_days[key] = [day]
                        base_ids[key] = [r.id]
                    else:
                        if day not in days:
                            days.append(day)
                        if r.id not in base_ids[key]:
                            base_ids[key].append(r.id)

        for d in range(DAYS):
            total -= self._day_penalty(assign[2 * d], assign[2 * d + 1])

        f = self.planned / SLOTS
        for target in WEEK_TARGETS:
            n = counts[target["id"]]
            if target["min"] is not None and n < target["min"] * f:
                total -= target["weight"] * (target["min"] * f - n)
            if target["max"] is not None and n > target["max"] * f:
                total -= target["weight"] * (n - target["max"] * f)
        if red > MAX_RED * f:
            total -= red - MAX_RED * f
        if processed > MAX_PROCESSED * f:
            total -= processed - MAX_PROCESSED * f

        for rid, slots in uses.items():
            c = len(slots)
            if c < 2:
                continue
            rating = self.by_id[rid].rating
            total -= (c - 1) * REPEAT[rating]
            if c > 2:
                total -= (c - 2) * 15.0
            for i in range(1, c):
                gap = slots[i] // 2 - slots[i - 1] // 2
                if gap == 0:
                    total -= 20.0
                elif gap == 1:
                    total -= 3.0

        if self.batch:
            for key, days in base_days.items():
                if len(days) >= 2 and len(base_ids[key]) >= 2:
                    total += BATCH_BONUS
        return total

    def _day_penalty(self, a: Cand | None, b: Cand | None) -> float:
        pen = 0.0
        kcal = 0.0
        protein = 0.0
        veg = 0.0
        carbs = 0.0
        for r, target in ((a, self.t_lunch), (b, self.t_dinner)):
            if r is None:
                continue
            k = r.kcal if r.kcal is not None else target
            dev = abs(k - target) / target
            if dev > 0.25:
                pen += (dev - 0.25) * 3.0
            kcal += k
            protein += r.protein
            veg += r.veg
            carbs += r.carbs
            if r.known and r.veg < MEAL_VEG:
                pen += 0.5
        if a is not None and b is not None:
            t = self.t_lunch + self.t_dinner
            dev = abs(kcal - t) / t
            if dev > 0.1:
                pen += (dev - 0.1) * 6.0
            if protein < DAY_PROTEIN:
                pen += (DAY_PROTEIN - protein) * 0.08
            if veg < DAY_VEG:
                pen += (DAY_VEG - veg) * 0.012
            if carbs < DAY_CARBS:
                pen += (DAY_CARBS - carbs) * 0.03
            if a.cat == b.cat:
                pen += 1.0 if a.cat in ("verdura", "otros") else 2.0
        return pen

    # ------------------------------------------------------------ búsqueda
    def _sample(self, cands: list[Cand], k: int) -> list[Cand]:
        pool = list(cands)
        n = len(pool)
        k = n if k > n else k
        for i in range(k):
            j = i + self.rng.below(n - i)
            pool[i], pool[j] = pool[j], pool[i]
        return pool[:k]

    def _shuffle(self, items: list[int]) -> None:
        for i in range(len(items) - 1, 0, -1):
            j = self.rng.below(i + 1)
            items[i], items[j] = items[j], items[i]

    def _rank_pick(self, n: int, weights: tuple[float, ...]) -> int:
        size = n if n < len(weights) else len(weights)
        total = 0.0
        for i in range(size):
            total += weights[i]
        x = self.rng.random() * total
        for i in range(size):
            x -= weights[i]
            if x < 0:
                return i
        return size - 1

    def _greedy(self, assign: list[Cand | None], fixed: list[bool]) -> None:
        order = [s for s in range(SLOTS) if not fixed[s]]
        self._shuffle(order)
        for s in order:
            cands = self.by_meal[s % 2]
            if not cands:
                continue
            scored: list[tuple[float, int, Cand]] = []
            for i, r in enumerate(self._sample(cands, MAX_CANDIDATES)):
                assign[s] = r
                scored.append((self.score(assign), i, r))
            scored.sort(key=lambda t: (-t[0], t[1]))
            assign[s] = scored[self._rank_pick(len(scored), RANK_WEIGHTS)][2]

    def _improve(self, assign: list[Cand | None], fixed: list[bool]) -> float:
        best = self.score(assign)
        for _ in range(PASSES):
            improved = False
            # 1) cambiar un plato por otro
            for s in range(SLOTS):
                if fixed[s]:
                    continue
                keep = assign[s]
                for r in self._sample(self.by_meal[s % 2], MAX_CANDIDATES):
                    if r is keep:
                        continue
                    assign[s] = r
                    value = self.score(assign)
                    if value > best + 1e-9:
                        best = value
                        keep = r
                        improved = True
                assign[s] = keep
            # 2) intercambiar dos platos (mueve una receta de día sin cambiarla)
            for s1 in range(SLOTS):
                if fixed[s1]:
                    continue
                for s2 in range(s1 + 1, SLOTS):
                    if fixed[s2]:
                        continue
                    a, b = assign[s1], assign[s2]
                    if a is None or b is None or a is b:
                        continue
                    if s1 % 2 != s2 % 2 and (
                        ("dinner" if s1 % 2 else "lunch") not in b.meals
                        or ("dinner" if s2 % 2 else "lunch") not in a.meals
                    ):
                        continue
                    assign[s1], assign[s2] = b, a
                    value = self.score(assign)
                    if value > best + 1e-9:
                        best = value
                        improved = True
                    else:
                        assign[s1], assign[s2] = a, b
            if not improved:
                break
        return best

    def generate(self, fixed_slots: list[Any]) -> list[Cand | None]:
        """Rellena la semana. fixed_slots: por hueco, None (a rellenar), FREE o un id de receta fijado."""
        base: list[Cand | None] = []
        fixed: list[bool] = []
        for value in fixed_slots:
            if value is None:
                base.append(None)
                fixed.append(False)
            elif value == FREE:
                base.append(None)
                fixed.append(True)
            else:
                base.append(self.by_id.get(value))
                fixed.append(True)
        self.planned = sum(1 for s in range(SLOTS) if not (fixed[s] and base[s] is None))
        best: list[Cand | None] = list(base)
        best_value: float | None = None
        for _ in range(RESTARTS):
            assign = list(base)
            self._greedy(assign, fixed)
            value = self._improve(assign, fixed)
            if best_value is None or value > best_value + 1e-9:
                best, best_value = list(assign), value
        return best

    def change(self, assign_ids: list[str | None], slot: int, rejected: list[str]) -> tuple[Cand | None, bool]:
        """CAMBIO: otra receta parecida para un hueco. Devuelve (receta, se_reinició_la_ronda)."""
        assign: list[Cand | None] = [self.by_id.get(i) if i else None for i in assign_ids]
        self.planned = sum(1 for i in assign_ids if i)
        if assign[slot] is None:
            self.planned += 1
        cur = assign[slot]
        meal = self.by_meal[slot % 2]
        cands = [r for r in meal if r is not cur and r.id not in rejected]
        restarted = False
        if not cands:
            cands = [r for r in meal if r is not cur]
            restarted = True
        if not cands:
            return None, restarted
        target = self.t_dinner if slot % 2 else self.t_lunch
        scored: list[tuple[float, int, Cand]] = []
        for i, r in enumerate(cands):
            assign[slot] = r
            value = self.score(assign)
            if cur is not None:
                if r.cat == cur.cat:
                    value += 4.0
                if r.kcal is not None and cur.kcal is not None:
                    diff = abs(r.kcal - cur.kcal) / target
                    value -= 3.0 * (diff if diff < 1 else 1.0)
            scored.append((value, i, r))
        scored.sort(key=lambda t: (-t[0], t[1]))
        return scored[self._rank_pick(len(scored), CHANGE_WEIGHTS)][2], restarted


def _round1(value: float) -> float:
    return float(int(value * 10 + 0.5)) / 10


def _round(value: float) -> int:
    return int(value + 0.5) if value >= 0 else -int(-value + 0.5)


def week_targets(planned: int) -> list[dict[str, Any]]:
    f = planned / SLOTS
    out = []
    for t in WEEK_TARGETS:
        out.append(
            {
                "id": t["id"],
                "min": _round(t["min"] * f) if t["min"] is not None else None,
                "max": _round(t["max"] * f) if t["max"] is not None else None,
            }
        )
    return out


def summarize(
    slots: list[dict[str, Any] | None],
    recipes: dict[str, dict[str, Any]],
    infos: dict[str, dict[str, Any]],
    settings: dict[str, Any],
    base_amounts: dict[str, dict[str, float]] | None = None,
) -> dict[str, Any]:
    """Resumen de una semana para el panel: totales por día, tipos de plato y batch cooking."""
    kcal_day = float(settings.get("kcal_day") or 2000)
    targets = {"lunch": kcal_day * LUNCH_SHARE, "dinner": kcal_day * DINNER_SHARE}
    days = []
    counts: dict[str, int] = {}
    portions = {"legumbre": 0.0, "pescado": 0.0, "carne": 0.0, "huevo": 0.0, "verdura": 0.0, "cereal": 0.0}
    planned = 0
    groups: dict[str, dict[str, Any]] = {}
    cook: dict[str, dict[str, Any]] = {}
    for d in range(DAYS):
        day = {"kcal": 0.0, "protein": 0.0, "carbs": 0.0, "fat": 0.0, "veg": 0.0, "meals": 0, "unknown": False}
        for m, meal in enumerate(("lunch", "dinner")):
            slot = slots[2 * d + m]
            if slot is None or slot.get("free"):
                continue
            planned += 1
            recipe = recipes.get(slot.get("recipe_id") or "")
            if recipe is None:
                continue
            info = infos[recipe["id"]]
            day["meals"] += 1
            cat = recipe.get("category") or "otros"
            counts[cat] = counts.get(cat, 0) + 1
            for key, value in recipe_counts(cat, info).items():
                portions[key] += value
            if info.get("kcal") is None:
                day["unknown"] = True
                day["kcal"] += targets[meal]
            else:
                day["kcal"] += info["kcal"]
            for key, field in (("protein", "protein"), ("carbs", "carbs"), ("fat", "fat")):
                if info.get(field) is not None:
                    day[key] += info[field]
            day["veg"] += info.get("veg_g", 0.0)
            entry = cook.setdefault(recipe["id"], {"recipe_id": recipe["id"], "slots": []})
            entry["slots"].append([d, meal])
            for base in info.get("bases", []):
                group = groups.setdefault(base["key"], {"key": base["key"], "name": base["name"], "slots": [], "recipes": []})
                group["slots"].append([d, meal, recipe["id"]])
                if recipe["id"] not in group["recipes"]:
                    group["recipes"].append(recipe["id"])
        for key in ("kcal", "protein", "carbs", "fat", "veg"):
            day[key] = float(_round(day[key]))
        full = day["meals"] == 2
        day["target"] = float(_round(targets["lunch"] + targets["dinner"]))
        day["ok_protein"] = day["protein"] >= DAY_PROTEIN if full else None
        day["ok_veg"] = day["veg"] >= DAY_VEG if full else None
        day["ok_carbs"] = day["carbs"] >= DAY_CARBS if full else None
        days.append(day)

    batch = []
    for key, group in groups.items():
        day_set = {s[0] for s in group["slots"]}
        if len(group["recipes"]) >= 2 and len(day_set) >= 2:
            amount = (base_amounts or {}).get(key)
            batch.append({**group, "amount": amount})
    weekly = []
    for t in week_targets(planned):
        n = _round1(portions[t["id"]])
        ok = (t["min"] is None or n >= t["min"]) and (t["max"] is None or n <= t["max"])
        weekly.append({**t, "count": n, "ok": ok})
    return {
        "days": days,
        "counts": counts,
        "weekly": weekly,
        "batch": batch,
        "cook": list(cook.values()),
        "planned": planned,
        "targets": {k: float(_round(v)) for k, v in targets.items()},
    }
