"""Comprobar si en la Despensa hay lo que pide el menú de la semana.

La Despensa (https://github.com/emero03/ha-despensa) cuenta unidades enteras con una
etiqueta libre ("kg", "bricks", "latas", "uds"...). Las recetas piden gramos, mililitros
o unidades. Para compararlas:

- Si la etiqueta es de peso o volumen (kg, g, l, ml...), se convierte directamente.
- Si son unidades (paquetes, latas, uds...), se usa lo que pesa una: la equivalencia que
  hayas puesto en Menú Semanal, o la de serie del producto (un paquete de pasta = 500 g),
  o lo que pesa una pieza (un huevo, una cebolla...).
- Si la receta y la despensa cuentan unidades, se comparan tal cual.
- Si no hay forma de saberlo, se da por bueno cuando queda alguna (y se avisa).

Lo básico (sal, aceite, especias...) que no controlas en la Despensa se da por bueno.
"""

from __future__ import annotations

from functools import lru_cache
import math
import re
from typing import Any, Final

from .catalog import _stems as _raw_stems, canonical_product, guess_product, normalize
from .const import UNITS
from .nutrition import BASICS, match_food

@lru_cache(maxsize=4096)
def _stems_cached(text: str) -> tuple[str, ...]:
    return tuple(_raw_stems(text))


def _stems(text: str) -> list[str]:
    return list(_stems_cached(text))


# Peso o volumen de una unidad de la despensa, si su etiqueta lo dice
LABEL_FACTORS: Final[dict[str, tuple[float, bool]]] = {
    "g": (1, False), "gr": (1, False), "grs": (1, False), "gramo": (1, False), "gramos": (1, False),
    "kg": (1000, False), "kgs": (1000, False), "kilo": (1000, False), "kilos": (1000, False),
    "kilogramo": (1000, False), "kilogramos": (1000, False),
    "ml": (1, True), "cl": (10, True), "l": (1000, True), "lt": (1000, True), "litro": (1000, True),
    "litros": (1000, True),
}

# Lo que suele traer un paquete/bote/brick de serie (g o ml) y cómo se dice en la Cesta.
PACKAGES: Final[list[tuple[list[str], float, str, bool]]] = [
    (["pasta", "espaguetis", "macarrones", "fideos", "tallarines", "noodles", "pasta integral"], 500, "paquetes", False),
    (["arroz", "arroz integral", "arroz basmati", "arroz bomba", "arroz redondo"], 1000, "paquetes", False),
    (["lentejas", "garbanzos", "alubias"], 500, "paquetes", False),
    (["garbanzos cocidos", "lentejas cocidas", "alubias cocidas"], 400, "botes", False),
    (["cuscus", "quinoa", "bulgur"], 500, "paquetes", False),
    (["harina", "azucar", "sal"], 1000, "paquetes", False),
    (["pan rallado"], 500, "paquetes", False),
    (["leche", "leche sin lactosa", "bebida de avena", "bebida de soja"], 1000, "bricks", True),
    (["nata para cocinar", "nata para montar"], 200, "bricks", True),
    (["caldo"], 1000, "bricks", True),
    (["tomate frito"], 400, "botes", False),
    (["tomate triturado"], 400, "latas", False),
    (["atun en lata"], 80, "latas", False),
    (["sardinas en lata"], 120, "latas", False),
    (["maiz dulce"], 150, "latas", False),
    (["aceite de oliva", "aceite de girasol"], 1000, "botellas", True),
    (["vinagre"], 500, "botellas", True),
    (["queso rallado"], 200, "bolsas", False),
    (["mozzarella"], 125, "uds", False),
    (["mantequilla"], 250, "uds", False),
    (["carne picada"], 500, "paquetes", False),
    (["masa de hojaldre"], 230, "uds", False),
    (["yogures", "yogur griego"], 125, "uds", False),
]

_PACKAGE_INDEX: Final[dict[str, tuple[float, str, bool]]] = {}
for _names, _amount, _label, _volume in PACKAGES:
    for _name in _names:
        _PACKAGE_INDEX[" ".join(_stems(_name))] = (_amount, _label, _volume)

# Las mismas palabras que entiende la Despensa en el detalle de la Cesta ("2 paquetes" suma 2)
_NOTE_WORDS: Final = re.compile(
    r"^(?:x|u|uds?\.?|unidades?|latas?|botes?|bricks?|botellas?|paquetes?|cajas?|bolsas?|rollos?|"
    r"piezas?|sobres?|tarros?|packs?)$"
)


PIECE_LABELS: Final = frozenset({"", "u", "ud", "uds", "unidad", "unidades", "pieza", "piezas"})


def package_for(name: str) -> tuple[float, str, bool] | None:
    """Tamaño de serie de una unidad de ese producto: (cantidad, etiqueta, es_volumen)."""
    return _PACKAGE_INDEX.get(" ".join(_stems(name)))


def label_factor(label: str | None) -> tuple[float, bool] | None:
    return LABEL_FACTORS.get(normalize(label or "").rstrip("."))


def _fmt_number(value: float) -> str:
    if abs(value - round(value)) < 0.05:
        return str(int(round(value)))
    return f"{value:.1f}".replace(".", ",")


def fmt_amount(grams: float, volume: bool = False) -> str:
    """750 → "750 g"; 1500 → "1,5 kg"; con volumen, "ml" y "l"."""
    if grams >= 1000:
        return f"{_fmt_number(grams / 1000)} {'l' if volume else 'kg'}"
    return f"{_fmt_number(grams)} {'ml' if volume else 'g'}"


def fmt_units(count: float, label: str = "") -> str:
    label = (label or "").strip()
    n = _fmt_number(count)
    if not label:
        return f"{n} ud" if n == "1" else f"{n} uds"
    if n == "1" and label == "uds":
        return "1 ud"
    if n == "1" and len(label) > 3 and label.endswith("s"):
        label = label[:-2] if re.search(r"[dlnzrj]es$", label) and len(label) > 4 else label[:-1]
    return f"{n} {label}"


def _ceil(value: float) -> int:
    return int(math.ceil(value - 1e-9))


def match_item(name: str, items: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Producto de la despensa para un ingrediente ("tomate" → Tomates, "atún" → Atún en lata)."""
    key = normalize(name)
    if not key:
        return None
    for item in items:
        if normalize(item["name"]) == key:
            return item
    words = _stems(name)
    for item in items:
        if _stems(item["name"]) == words:
            return item
    canon = canonical_product(name)
    if canon:
        ckey = normalize(canon["name"])
        for item in items:
            if normalize(item["name"]) == ckey:
                return item
    if not words:
        return None

    def contains(haystack: list[str], needle: list[str]) -> bool:
        size = len(needle)
        return any(haystack[i : i + size] == needle for i in range(len(haystack) - size + 1))

    wider = [i for i in items if contains(_stems(i["name"]), words)]
    if len(wider) > 1:
        stocked = [i for i in wider if i.get("stock", 0) > 0]
        if len(stocked) >= 1:
            wider = stocked
        wider.sort(key=lambda i: (len(i["name"]), normalize(i["name"])))
    if wider:
        return wider[0]
    narrower = [i for i in items if _stems(i["name"]) and contains(words, _stems(i["name"]))]
    if narrower:
        return max(narrower, key=lambda i: len(_stems(i["name"])))
    return None


def unit_size(item: dict[str, Any], equivalences: dict[str, dict[str, Any]]) -> tuple[float | None, bool, str]:
    """Lo que pesa una unidad de un producto de la despensa: (g o ml, es_volumen, origen)."""
    factor = label_factor(item.get("unit"))
    if factor is not None:
        return factor[0], factor[1], "label"
    eq = equivalences.get(normalize(item["name"]))
    if eq and eq.get("grams"):
        return float(eq["grams"]), bool(eq.get("volume")), "user"
    pkg = package_for(item["name"])
    if pkg is not None:
        return pkg[0], pkg[2], "default"
    # Lo que pesa una pieza (un huevo, una cebolla...), solo si se cuenta por piezas
    label = normalize(item.get("unit") or "").rstrip(".")
    food = match_food(item["name"])
    if food is not None and food["unit_g"] and label in PIECE_LABELS:
        return float(food["unit_g"]), False, "piece"
    return None, False, ""


def pantry_ratio(recipe: dict[str, Any], items: list[dict[str, Any]]) -> float:
    """Parte de los ingredientes de una receta que hay en la despensa (para dar preferencia)."""
    total = 0
    have = 0
    for ing in recipe.get("ingredients", []):
        name = str(ing.get("name") or "")
        if not name or normalize(name) in BASICS:
            continue
        total += 1
        item = match_item(name, items)
        if item is not None and item.get("stock", 0) > 0:
            have += 1
    return have / total if total else 0.0


def check(
    lines: list[dict[str, Any]],
    items: list[dict[str, Any]] | None,
    in_cesta: set[str],
    equivalences: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    """Agrupa los ingredientes de la semana por producto y dice cuánto falta de cada uno.

    lines: ingredientes ya escalados a los comensales, con la receta y el día de donde vienen.
    items: productos de la Despensa (None si no está instalada: todo lo que no es básico falta).
    """
    pantry = items or []
    groups: dict[str, dict[str, Any]] = {}
    for line in lines:
        name = str(line.get("name") or "").strip()
        if not name or normalize(name) == "agua":
            continue
        item = match_item(name, pantry) if items is not None else None
        if item is not None:
            key = f"item:{item['id']}"
            display = item["name"]
        else:
            canon = canonical_product(name)
            display = canon["name"] if canon else name[:1].upper() + name[1:]
            key = "name:" + " ".join(_stems(display))
        group = groups.get(key)
        if group is None:
            group = groups[key] = {"key": key, "name": display, "item": item, "lines": []}
        group["lines"].append(line)

    results = [_evaluate(g, in_cesta, equivalences) for g in groups.values()]
    order = {"missing": 0, "unsure": 1, "in_cesta": 2, "ok": 3, "untracked": 4}
    results.sort(key=lambda r: (order[r["status"]], normalize(r["name"])))
    return results


def _evaluate(group: dict[str, Any], in_cesta: set[str], equivalences: dict[str, dict[str, Any]]) -> dict[str, Any]:
    item = group["item"]
    name = group["name"]
    mass = 0.0  # g o ml que piden las líneas en peso/volumen
    count = 0.0  # unidades que piden las líneas en ud
    count_mass = 0.0  # esas unidades pasadas a gramos, cuando se sabe
    count_known = True
    any_only = True
    volume_lines = 0
    mass_lines = 0
    for line in group["lines"]:
        info = UNITS.get(line.get("unit") or "", UNITS["g"])
        qty = line.get("qty")
        if info["kind"] == "any" or qty is None:
            continue
        any_only = False
        if info["kind"] == "count":
            count += float(qty)
            food = match_food(line["name"])
            if food is not None and food["unit_g"]:
                count_mass += float(qty) * food["unit_g"]
            else:
                count_known = False
        else:
            mass += float(qty) * float(info["factor"])
            mass_lines += 1
            if line.get("unit") in ("ml", "l"):
                volume_lines += 1

    volume = mass_lines > 0 and volume_lines == mass_lines
    basic = normalize(name) in BASICS or any(normalize(line["name"]) in BASICS for line in group["lines"])
    pkg = package_for(name)
    canon = guess_product(name)
    out: dict[str, Any] = {
        "key": group["key"],
        "name": name,
        "icon": (item or {}).get("icon") or (canon["icon"] if canon else "🛒"),
        "department": (item or {}).get("department") or (canon["department"] if canon else "otros"),
        "item_id": (item or {}).get("id"),
        "stock": (item or {}).get("stock"),
        "unit_label": (item or {}).get("unit") or "",
        "recipes": [
            {"recipe_id": line.get("recipe_id"), "recipe": line.get("recipe"), "day": line.get("day"), "meal": line.get("meal")}
            for line in group["lines"]
        ],
        "need_text": "",
        "have_text": None,
        "missing": 0,
        "note": "",
        "equivalence": None,
        "status": "ok",
    }

    # Lo que se necesita, para mostrarlo
    if any_only:
        out["need_text"] = "al gusto"
    elif mass and count:
        total = mass + count_mass if count_known else mass
        out["need_text"] = fmt_amount(total, volume) + ("" if count_known else f" + {fmt_units(count)}")
    elif mass:
        out["need_text"] = fmt_amount(mass, volume)
    else:
        out["need_text"] = fmt_units(count)

    if item is None:
        if basic:
            out["status"] = "untracked"
            return out
        out["status"] = "missing"
        if any_only:
            out["missing"] = 1
            out["note"] = ""
        elif pkg is not None and (mass or count_known):
            total = mass + count_mass
            n = _ceil(total / pkg[0]) if total > 0 else 1
            if not mass and count and pkg[1] == "uds":
                n = _ceil(count)
            out["missing"] = n
            out["note"] = fmt_units(n, pkg[1])
        elif mass and not count:
            out["missing"] = 1
            out["note"] = fmt_amount(mass, volume)
        elif count and not mass:
            out["missing"] = _ceil(count)
            out["note"] = fmt_units(_ceil(count))
        else:
            out["missing"] = 1
            out["note"] = out["need_text"]
        return _cesta_status(out, in_cesta)

    stock = float(item.get("stock") or 0)
    label = item.get("unit") or ""
    size, size_volume, origin = unit_size(item, equivalences)
    out["equivalence"] = {"grams": size, "volume": size_volume or volume, "origin": origin}
    unit_text = fmt_units(stock, label) if label else (fmt_units(stock) if stock != 1 else "1 ud")
    out["have_text"] = unit_text
    if size and origin != "label":
        out["have_text"] = f"{unit_text} (≈ {fmt_amount(stock * size, size_volume or volume)})" if stock else unit_text

    def note_for(n: int) -> str:
        factor = label_factor(label)
        if factor is not None:
            return fmt_units(n, label)
        if label and _NOTE_WORDS.match(normalize(label)):
            return fmt_units(n, label)
        if not label and pkg is not None:
            return fmt_units(n, pkg[1])
        return fmt_units(n)

    if any_only:
        if stock <= 0:
            out["status"] = "missing"
            out["missing"] = 1
            out["note"] = note_for(1)
        return _cesta_status(out, in_cesta)

    if not mass:
        # Solo unidades: 1 ud de la receta = 1 unidad de la despensa (si la etiqueta no es de peso)
        if label_factor(label) is None:
            need = count
            missing = _ceil(need - stock)
        elif count_known:
            need_mass = count_mass
            missing = _ceil((need_mass - stock * size) / size) if size else 0
        else:
            out["status"] = "unsure" if stock > 0 else "missing"
            out["missing"] = 0 if stock > 0 else 1
            out["note"] = note_for(1) if stock <= 0 else ""
            return _cesta_status(out, in_cesta)
        if missing > 0:
            out["status"] = "missing"
            out["missing"] = missing
            out["note"] = note_for(missing)
        return _cesta_status(out, in_cesta)

    need_mass = mass + count_mass
    if size is None or (count and not count_known):
        # No se sabe lo que pesa una unidad: se da por bueno si queda alguna
        out["status"] = "unsure" if stock > 0 else "missing"
        if stock <= 0:
            out["missing"] = 1
            out["note"] = fmt_amount(need_mass, volume)
        out["equivalence"] = {"grams": None, "volume": volume, "origin": ""}
        return _cesta_status(out, in_cesta)
    missing = _ceil((need_mass - stock * size) / size)
    if missing > 0:
        out["status"] = "missing"
        out["missing"] = missing
        out["note"] = note_for(missing)
    return _cesta_status(out, in_cesta)


def _cesta_status(out: dict[str, Any], in_cesta: set[str]) -> dict[str, Any]:
    if out["status"] == "missing" and " ".join(_stems(out["name"])) in in_cesta:
        out["status"] = "in_cesta"
    return out
