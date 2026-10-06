"""Tabla de composición aproximada y estimación nutricional de las recetas.

Valores por 100 g de porción comestible, en crudo salvo que el nombre diga «cocido».
Son medias redondeadas de tablas de composición españolas (tipo BEDCA): sirven para
estimar un menú, no para una dieta clínica.

Cada alimento tiene un grupo, que es lo que usa el planificador para equilibrar el día
(proteína, verdura, hidratos) y la semana (legumbres, pescado, carne, huevos...).
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any, Final

from .catalog import _stems, normalize
from .const import UNITS

# Grupos de alimentos
G_MEAT: Final = "carne"  # aves y conejo
G_RED: Final = "carne_roja"  # ternera, cerdo, cordero
G_PROCESSED: Final = "procesada"  # embutidos, bacon, salchichas
G_FISH: Final = "pescado"
G_EGG: Final = "huevo"
G_LEGUME: Final = "legumbre"
G_CEREAL: Final = "cereal"
G_TUBER: Final = "tuberculo"
G_VEG: Final = "verdura"
G_FRUIT: Final = "fruta"
G_DAIRY: Final = "lacteo"
G_FAT: Final = "grasa"
G_OTHER: Final = "otros"

# (nombres, kcal, proteína, hidratos, grasa, grupo, gramos por unidad, base de batch cooking)
# "gramos por unidad" es lo que pesa 1 ud (un huevo, una cebolla...); None si no tiene sentido.
# "base" agrupa recetas que se pueden cocinar juntas: dos platos con carne picada se
# aprovechan del mismo sofrito; dos con garbanzos, de la misma olla.
FOODS: Final[list[tuple[list[str], float, float, float, float, str, float | None, str | None]]] = [
    # --- aves y conejo
    (["pollo", "pollo entero", "contramuslos de pollo"], 135, 20, 0, 6, G_MEAT, 250, "Pollo"),
    (["pechuga de pollo", "filetes de pollo", "pollo troceado"], 110, 23, 0, 2, G_MEAT, 200, "Pollo"),
    (["muslos de pollo"], 170, 18, 0, 11, G_MEAT, 150, "Pollo"),
    (["alitas de pollo"], 200, 18, 0, 14, G_MEAT, 40, "Pollo"),
    (["pavo", "pechuga de pavo", "filetes de pavo"], 110, 22, 0, 2, G_MEAT, 150, "Pavo"),
    (["conejo"], 135, 21, 0, 5.5, G_MEAT, None, "Conejo"),
    # --- carne roja
    (["carne picada", "carne picada mixta", "carne picada de ternera"], 230, 18, 0, 17, G_RED, None, "Carne picada"),
    (["ternera", "filetes de ternera", "carne de ternera", "ternera para guisar", "babilla"], 130, 21, 0, 5, G_RED, None, "Ternera"),
    (["lomo de cerdo", "cinta de lomo", "filetes de lomo"], 150, 21, 0, 7, G_RED, None, "Cerdo"),
    (["cerdo", "carne de cerdo", "secreto", "presa"], 220, 18, 0, 16, G_RED, None, "Cerdo"),
    (["solomillo", "solomillo de cerdo"], 140, 21, 0, 6, G_RED, None, "Cerdo"),
    (["costillas", "costillas de cerdo"], 280, 17, 0, 23, G_RED, None, "Costillas"),
    (["chuletas", "chuletas de cerdo"], 230, 18, 0, 17, G_RED, None, "Cerdo"),
    (["cordero", "chuletas de cordero", "paletilla de cordero"], 250, 17, 0, 20, G_RED, None, "Cordero"),
    (["hamburguesas", "hamburguesa de ternera"], 250, 16, 3, 19, G_RED, 120, None),
    # --- procesada
    (["salchichas", "salchichas frescas"], 280, 12, 2, 25, G_PROCESSED, 50, None),
    (["chorizo"], 450, 22, 2, 39, G_PROCESSED, None, None),
    (["bacon", "beicon", "panceta", "taquitos de bacon"], 330, 13, 0, 31, G_PROCESSED, None, None),
    (["jamon serrano", "taquitos de jamon"], 240, 30, 0, 13, G_PROCESSED, None, None),
    (["jamon cocido", "jamon york"], 115, 19, 1, 4, G_PROCESSED, None, None),
    (["pavo en lonchas", "fiambre de pavo"], 100, 18, 2, 2, G_PROCESSED, None, None),
    (["morcilla"], 380, 15, 15, 30, G_PROCESSED, None, None),
    # --- pescado y marisco
    (["salmon", "lomos de salmon"], 200, 20, 0, 13, G_FISH, 125, None),
    (["merluza", "lomos de merluza", "filetes de merluza", "pescadilla"], 80, 17, 0, 1.5, G_FISH, 125, None),
    (["bacalao", "bacalao desalado", "lomos de bacalao"], 80, 18, 0, 0.7, G_FISH, 150, None),
    (["atun fresco", "bonito", "bonito del norte"], 140, 23, 0, 5, G_FISH, 150, None),
    (["atun en lata", "atun", "atun al natural", "atun en aceite"], 190, 25, 0, 10, G_FISH, 60, None),
    (["dorada", "lubina"], 110, 20, 0, 3.5, G_FISH, 300, None),
    (["sardinas", "boquerones", "caballa", "jurel"], 140, 20, 0, 7, G_FISH, None, None),
    (["sardinas en lata", "caballa en lata"], 210, 24, 0, 13, G_FISH, 85, None),
    (["gambas", "langostinos", "gambas congeladas", "gambas peladas"], 90, 20, 0, 1, G_FISH, None, None),
    (["calamares", "sepia", "chipirones"], 85, 16, 2, 1.5, G_FISH, None, None),
    (["pulpo"], 80, 15, 2, 1, G_FISH, None, None),
    (["mejillones", "almejas"], 85, 12, 3, 2, G_FISH, None, None),
    (["surimi", "palitos de cangrejo"], 100, 8, 15, 1, G_FISH, 15, None),
    (["varitas de merluza"], 200, 12, 18, 9, G_FISH, 30, None),
    # --- huevos
    (["huevos", "huevo", "huevos camperos"], 145, 12.5, 0.7, 10, G_EGG, 55, None),
    # --- legumbres
    (["lentejas", "lentejas pardinas", "lentejas rojas"], 330, 24, 50, 1.5, G_LEGUME, None, "Lentejas"),
    (["garbanzos"], 360, 20, 55, 6, G_LEGUME, None, "Garbanzos"),
    (["alubias", "judias blancas", "alubias blancas", "alubias rojas", "judias pintas"], 330, 22, 50, 1.5, G_LEGUME, None, "Alubias"),
    (["lentejas cocidas", "lentejas en bote"], 110, 8, 17, 0.5, G_LEGUME, None, "Lentejas"),
    (["garbanzos cocidos", "garbanzos en bote"], 120, 7, 17, 2, G_LEGUME, None, "Garbanzos"),
    (["alubias cocidas", "alubias en bote"], 100, 7, 15, 0.5, G_LEGUME, None, "Alubias"),
    (["soja texturizada"], 330, 50, 20, 1, G_LEGUME, None, None),
    (["tofu"], 125, 13, 2, 7.5, G_LEGUME, None, None),
    (["hummus"], 170, 7, 14, 10, G_LEGUME, None, None),
    # --- cereales
    (["arroz", "arroz redondo", "arroz largo", "arroz basmati", "arroz bomba"], 350, 7, 78, 0.6, G_CEREAL, None, "Arroz"),
    (["arroz integral"], 350, 7.5, 74, 2.5, G_CEREAL, None, "Arroz"),
    (["arroz cocido"], 130, 2.7, 28, 0.3, G_CEREAL, None, "Arroz"),
    (["pasta", "espaguetis", "macarrones", "fideos", "tallarines", "penne", "spaghetti", "fusilli", "lasana", "placas de lasana", "noodles"], 355, 12, 72, 1.5, G_CEREAL, None, None),
    (["pasta integral"], 350, 13, 65, 2.5, G_CEREAL, None, None),
    (["pasta fresca", "tortellini", "raviolis"], 280, 11, 50, 4, G_CEREAL, None, None),
    (["cuscus"], 360, 12.5, 72, 1, G_CEREAL, None, None),
    (["quinoa"], 370, 14, 64, 6, G_CEREAL, None, "Quinoa"),
    (["bulgur"], 340, 12, 69, 1.3, G_CEREAL, None, None),
    (["pan", "barra de pan", "pan integral"], 260, 9, 50, 3, G_CEREAL, None, None),
    (["pan de molde"], 260, 9, 47, 4, G_CEREAL, 25, None),
    (["pan rallado"], 360, 12, 72, 3, G_CEREAL, None, None),
    (["harina", "harina de trigo", "maicena"], 350, 10, 74, 1.2, G_CEREAL, None, None),
    (["tortillas de trigo", "tortillas mexicanas", "wraps"], 300, 8, 50, 7, G_CEREAL, 40, None),
    (["masa de hojaldre", "hojaldre"], 400, 6, 37, 25, G_CEREAL, None, None),
    (["masa de pizza", "base de pizza"], 270, 8, 50, 4, G_CEREAL, None, None),
    (["copos de avena", "avena"], 370, 13, 60, 7, G_CEREAL, None, None),
    # --- tubérculos
    (["patatas", "patata"], 80, 2, 17, 0.1, G_TUBER, 200, None),
    (["boniato", "batata"], 90, 1.6, 20, 0.1, G_TUBER, 250, None),
    (["patatas congeladas"], 150, 2.5, 25, 5, G_TUBER, None, None),
    # --- verduras y hortalizas
    (["tomates", "tomate", "tomate pera", "tomate rama"], 20, 0.9, 3.5, 0.2, G_VEG, 120, None),
    (["tomates cherry"], 20, 0.9, 3.5, 0.2, G_VEG, 15, None),
    (["tomate triturado", "tomate natural triturado", "tomate troceado"], 25, 1.2, 4, 0.2, G_VEG, None, None),
    (["tomate frito", "salsa de tomate"], 85, 1.5, 9, 4.5, G_VEG, None, None),
    (["tomate concentrado"], 80, 4.5, 15, 0.5, G_VEG, None, None),
    (["cebollas", "cebolla", "cebolla morada"], 40, 1.1, 8, 0.1, G_VEG, 150, None),
    (["cebolletas", "cebolleta", "chalotas"], 30, 1.5, 5, 0.2, G_VEG, 60, None),
    (["ajos", "ajo", "dientes de ajo"], 120, 6, 25, 0.5, G_VEG, 5, None),
    (["pimientos", "pimiento", "pimiento rojo", "pimiento verde", "pimiento amarillo", "pimiento italiano"], 25, 1, 4.5, 0.3, G_VEG, 150, None),
    (["pimientos asados", "pimientos del piquillo"], 30, 1, 5, 0.3, G_VEG, 30, None),
    (["zanahorias", "zanahoria"], 40, 0.9, 8, 0.2, G_VEG, 80, None),
    (["calabacines", "calabacin"], 17, 1.2, 2.5, 0.3, G_VEG, 250, None),
    (["berenjenas", "berenjena"], 25, 1, 4, 0.2, G_VEG, 250, None),
    (["brocoli"], 34, 2.8, 4, 0.4, G_VEG, 300, None),
    (["coliflor"], 25, 2, 3, 0.3, G_VEG, 600, None),
    (["espinacas", "espinacas frescas", "espinacas congeladas"], 23, 2.9, 1.5, 0.4, G_VEG, None, None),
    (["acelgas"], 20, 1.8, 3, 0.2, G_VEG, None, None),
    (["lechuga", "lechuga romana", "cogollos"], 15, 1.3, 1.5, 0.2, G_VEG, 300, None),
    (["ensalada en bolsa", "rucula", "canonigos", "brotes tiernos", "mezclum"], 20, 2, 2, 0.4, G_VEG, None, None),
    (["pepinos", "pepino"], 15, 0.7, 3, 0.1, G_VEG, 200, None),
    (["judias verdes"], 30, 1.8, 4.5, 0.2, G_VEG, None, None),
    (["guisantes", "guisantes congelados"], 80, 5, 10, 0.4, G_VEG, None, None),
    (["champinones", "setas", "champiñones laminados"], 25, 3, 1, 0.3, G_VEG, 20, None),
    (["puerros", "puerro"], 30, 1.5, 5.5, 0.3, G_VEG, 150, None),
    (["calabaza"], 26, 1, 5, 0.1, G_VEG, None, None),
    (["alcachofas", "alcachofa"], 45, 3, 5, 0.2, G_VEG, 120, None),
    (["esparragos", "esparragos verdes", "esparragos trigueros"], 25, 2.2, 2, 0.2, G_VEG, 20, None),
    (["apio"], 16, 0.7, 2, 0.2, G_VEG, 40, None),
    (["col", "repollo", "lombarda", "coles de bruselas"], 25, 1.3, 4, 0.1, G_VEG, None, None),
    (["verduras congeladas", "menestra", "salteado de verduras", "verduras para wok"], 50, 3, 7, 0.5, G_VEG, None, None),
    (["maiz dulce", "maiz"], 85, 3, 15, 1, G_VEG, None, None),
    (["gazpacho"], 50, 1, 4, 3.5, G_VEG, None, None),
    (["remolacha"], 43, 1.6, 8, 0.2, G_VEG, 100, None),
    (["rabanos"], 16, 0.7, 2, 0.1, G_VEG, 10, None),
    # --- frutas
    (["limones", "limon", "lima"], 30, 0.7, 3, 0.3, G_FRUIT, 100, None),
    (["manzanas", "manzana"], 52, 0.3, 12, 0.2, G_FRUIT, 180, None),
    (["platanos", "platano"], 90, 1.2, 20, 0.3, G_FRUIT, 120, None),
    (["naranjas", "naranja"], 45, 0.8, 9, 0.2, G_FRUIT, 200, None),
    (["aguacates", "aguacate"], 160, 2, 2, 15, G_FRUIT, 170, None),
    (["pina"], 50, 0.5, 11, 0.1, G_FRUIT, None, None),
    (["pasas", "uvas pasas"], 300, 3, 70, 0.5, G_FRUIT, None, None),
    # --- lácteos
    (["leche", "leche semidesnatada", "leche entera", "leche desnatada", "bebida de avena", "bebida de soja"], 47, 3.2, 4.7, 1.6, G_DAIRY, None, None),
    (["nata para cocinar", "nata", "nata ligera"], 200, 2.5, 4, 18, G_DAIRY, None, None),
    (["nata para montar"], 340, 2, 3, 35, G_DAIRY, None, None),
    (["queso", "queso curado", "queso semicurado", "queso manchego", "parmesano", "queso parmesano"], 380, 25, 1, 31, G_DAIRY, None, None),
    (["queso rallado"], 400, 30, 2, 30, G_DAIRY, None, None),
    (["queso fresco", "queso de burgos", "queso batido", "queso crema", "requeson"], 150, 12, 3, 10, G_DAIRY, None, None),
    (["mozzarella", "queso mozzarella"], 250, 18, 2, 19, G_DAIRY, 125, None),
    (["queso de cabra", "rulo de cabra", "queso feta", "feta"], 290, 18, 1, 24, G_DAIRY, None, None),
    (["queso en lonchas"], 330, 22, 1, 27, G_DAIRY, 20, None),
    (["yogures", "yogur", "yogur natural"], 60, 4, 5, 3, G_DAIRY, 125, None),
    (["yogur griego"], 120, 6, 4, 10, G_DAIRY, 125, None),
    (["bechamel"], 120, 3.5, 9, 8, G_DAIRY, None, None),
    # --- grasas y frutos secos
    (["aceite de oliva", "aceite", "aceite de girasol", "aove", "aceite de oliva virgen extra"], 900, 0, 0, 100, G_FAT, None, None),
    (["mantequilla", "margarina"], 740, 0.7, 0.6, 82, G_FAT, None, None),
    (["aceitunas"], 140, 1, 1, 14, G_FAT, 4, None),
    (["frutos secos", "nueces", "almendras", "avellanas", "pinones", "anacardos", "cacahuetes"], 620, 18, 8, 55, G_FAT, None, None),
    (["mayonesa", "alioli"], 700, 1, 1, 77, G_FAT, None, None),
    (["leche de coco"], 200, 2, 3, 20, G_FAT, None, None),
    (["pesto", "salsa pesto"], 450, 5, 6, 45, G_FAT, None, None),
    # --- otros
    (["caldo", "caldo de pollo", "caldo de verduras", "caldo de pescado", "caldo de carne", "fumet"], 7, 0.5, 0.5, 0.3, G_OTHER, None, None),
    (["vino blanco", "vino tinto", "vino"], 75, 0, 2.5, 0, G_OTHER, None, None),
    (["cerveza"], 43, 0.5, 3.5, 0, G_OTHER, None, None),
    (["azucar", "azucar moreno"], 400, 0, 100, 0, G_OTHER, None, None),
    (["miel"], 300, 0.4, 80, 0, G_OTHER, None, None),
    (["ketchup"], 110, 1.5, 25, 0.2, G_OTHER, None, None),
    (["salsa de soja"], 55, 8, 5, 0.1, G_OTHER, None, None),
    (["mostaza"], 70, 4, 5, 4, G_OTHER, None, None),
    (["vinagre", "vinagre de modena"], 20, 0, 1, 0, G_OTHER, None, None),
    (["curry", "curry en polvo", "pasta de curry"], 100, 3, 10, 5, G_OTHER, None, None),
    (["chocolate", "cacao"], 530, 6, 50, 32, G_OTHER, None, None),
    (["levadura", "levadura quimica", "levadura de panadero"], 0, 0, 0, 0, G_OTHER, None, None),
    (["agua"], 0, 0, 0, 0, G_OTHER, None, None),
    (["sal", "sal gorda", "sal en escamas"], 0, 0, 0, 0, G_OTHER, None, None),
    (["pimienta", "pimienta negra", "pimienta blanca"], 0, 0, 0, 0, G_OTHER, None, None),
    (["especias", "pimenton", "pimenton dulce", "pimenton picante", "comino", "oregano", "tomillo", "romero", "laurel", "hojas de laurel", "canela", "nuez moscada", "curcuma", "azafran", "colorante", "guindilla", "cayena", "jengibre", "perejil", "cilantro", "albahaca", "hierbabuena", "eneldo", "hierbas provenzales", "ajo en polvo", "cebolla en polvo"], 0, 0, 0, 0, G_OTHER, 1, None),
]

# Ingredientes "de fondo de armario": si no se controlan en la Despensa se dan por buenos.
BASICS: Final[frozenset[str]] = frozenset(
    normalize(n)
    for n in (
        "agua", "sal", "sal gorda", "pimienta", "pimienta negra", "especias", "pimenton", "comino",
        "oregano", "tomillo", "romero", "laurel", "canela", "nuez moscada", "curcuma", "azafran",
        "colorante", "cayena", "hierbas provenzales", "vinagre", "aceite", "aceite de oliva",
        "aceite de girasol", "aove", "ajo en polvo", "cebolla en polvo", "azucar",
    )
)

# Grupos que cuentan como "ración de proteína" del día
PROTEIN_GROUPS: Final = (G_MEAT, G_RED, G_PROCESSED, G_FISH, G_EGG, G_LEGUME)

# Gramos por ración a partir de los que un plato cuenta como "ración" de ese grupo
PORTION_MIN: Final = {"legumbre": 50.0, "pescado": 80.0, "carne": 80.0}
EGG_G: Final = 55.0

# Categoría (componente principal) que sugiere cada grupo y cuánto pesa al decidirla
_CATEGORY_OF_GROUP: Final = {
    G_MEAT: ("carne", 2.0),
    G_RED: ("carne", 2.0),
    G_PROCESSED: ("carne", 1.5),
    G_FISH: ("pescado", 2.2),
    G_EGG: ("huevo", 2.2),
    G_LEGUME: ("legumbre", 3.0),
    G_CEREAL: ("cereal", 1.4),
    G_TUBER: ("cereal", 0.5),
    G_VEG: ("verdura", 1.0),
}


def _food(entry: tuple) -> dict[str, Any]:
    names, kcal, protein, carbs, fat, group, unit_g, base = entry
    return {
        "name": names[0],
        "kcal": kcal,
        "protein": protein,
        "carbs": carbs,
        "fat": fat,
        "group": group,
        "unit_g": unit_g,
        "base": base,
    }


_INDEX: Final[dict[str, dict[str, Any]]] = {}
_STEM_INDEX: Final[dict[str, dict[str, Any]]] = {}
_STEM_LIST: Final[list[tuple[list[str], dict[str, Any]]]] = []
for _entry in FOODS:
    _data = _food(_entry)
    for _name in _entry[0]:
        _INDEX.setdefault(normalize(_name), _data)
        _words = _stems(_name)
        _STEM_INDEX.setdefault(" ".join(_words), _data)
        _STEM_LIST.append((_words, _data))


@lru_cache(maxsize=2048)
def match_food(name: str) -> dict[str, Any] | None:
    """Alimento de la tabla que corresponde a un ingrediente escrito libremente.

    "Tomates" → tomate, "pechugas de pollo" → pechuga de pollo,
    "carne picada de cerdo" → carne picada, "caldo de pollo" → caldo.
    """
    key = normalize(name)
    if not key:
        return None
    if key in _INDEX:
        return _INDEX[key]
    words = _stems(name)
    if not words:
        return None
    joined = " ".join(words)
    if joined in _STEM_INDEX:
        return _STEM_INDEX[joined]
    best: dict[str, Any] | None = None
    best_score = 0
    for cand, data in _STEM_LIST:
        size = len(cand)
        if size == 0 or size > len(words):
            continue
        for start in range(len(words) - size + 1):
            if words[start : start + size] == cand:
                score = sum(len(w) for w in cand) * 10 + (5 if start == 0 else 0)
                if score > best_score:
                    best, best_score = data, score
                break
    return best


def unit_info(unit: str | None) -> dict[str, Any]:
    return UNITS.get(unit or "", UNITS["g"])


def grams_of(ingredient: dict[str, Any], food: dict[str, Any] | None) -> float | None:
    """Gramos de un ingrediente de la receta (None si no se puede saber)."""
    qty = ingredient.get("qty")
    info = unit_info(ingredient.get("unit"))
    if info["kind"] == "any":
        return 0.0
    if qty is None:
        return None
    if info["kind"] == "count":
        if food is None or not food["unit_g"]:
            return None
        return float(qty) * food["unit_g"]
    return float(qty) * info["factor"]


def _round1(value: float) -> float:
    return float(int(value * 10 + 0.5)) / 10


def analyze(recipe: dict[str, Any]) -> dict[str, Any]:
    """Estimación por ración: kcal, macronutrientes, gramos por grupo y bases de batch cooking."""
    servings = max(1, int(recipe.get("servings") or 1))
    kcal = protein = carbs = fat = 0.0
    groups: dict[str, float] = {}
    unknown: list[str] = []
    known = 0
    bases: dict[str, str] = {}
    for ing in recipe.get("ingredients", []):
        name = str(ing.get("name") or "").strip()
        if not name:
            continue
        food = match_food(name)
        grams = grams_of(ing, food)
        if food is None or grams is None:
            if unit_info(ing.get("unit"))["kind"] != "any":
                unknown.append(name)
            continue
        known += 1
        factor = grams / 100
        kcal += food["kcal"] * factor
        protein += food["protein"] * factor
        carbs += food["carbs"] * factor
        fat += food["fat"] * factor
        groups[food["group"]] = groups.get(food["group"], 0.0) + grams
        if food["base"] and grams >= 100:
            bases[normalize(food["base"])] = food["base"]

    explicit = str(recipe.get("base") or "").strip()
    if explicit:
        bases = {normalize(explicit): explicit, **bases}

    per = {g: _round1(v / servings) for g, v in groups.items()}
    manual = recipe.get("kcal")
    estimated = _round1(kcal / servings) if known else None
    result = {
        "kcal": float(manual) if manual else estimated,
        "kcal_estimated": estimated,
        "kcal_manual": bool(manual),
        "protein": _round1(protein / servings) if known else None,
        "carbs": _round1(carbs / servings) if known else None,
        "fat": _round1(fat / servings) if known else None,
        "veg_g": per.get(G_VEG, 0.0),
        "groups": per,
        "unknown": unknown,
        "known": known,
        "suggested_category": suggest_category(groups),
        "bases": [{"key": k, "name": v} for k, v in bases.items()],
        "portions": {
            "legumbre": per.get(G_LEGUME, 0.0) >= PORTION_MIN["legumbre"],
            "pescado": per.get(G_FISH, 0.0) >= PORTION_MIN["pescado"],
            "carne": per.get(G_MEAT, 0.0) + per.get(G_RED, 0.0) + per.get(G_PROCESSED, 0.0) >= PORTION_MIN["carne"],
            "huevos": _round1(per.get(G_EGG, 0.0) / EGG_G),
        },
        "red_meat": per.get(G_RED, 0.0) >= 50,
        "processed": per.get(G_PROCESSED, 0.0) >= 25,
    }
    return result


def suggest_category(groups: dict[str, float]) -> str:
    """Componente principal según el peso de cada grupo (lo que más "manda" en el plato)."""
    score: dict[str, float] = {}
    for group, grams in groups.items():
        if group in _CATEGORY_OF_GROUP:
            cat, weight = _CATEGORY_OF_GROUP[group]
            score[cat] = score.get(cat, 0.0) + grams * weight
    if not score:
        return "otros"
    best = "otros"
    best_value = 0.0
    for cat, value in score.items():
        if value > best_value:
            best, best_value = cat, value
    return best


def foods_for_js() -> list[list[Any]]:
    """La tabla tal cual, para la vista previa (el mismo análisis en JavaScript)."""
    return [list(e) for e in FOODS]
