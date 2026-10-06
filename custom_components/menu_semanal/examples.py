"""Recetas de ejemplo (para 4 raciones) para empezar a probar el planificador.

Se cargan solo si lo pides desde ⚙️ Ajustes o desde la pantalla vacía de Recetas.
Puedes cambiarlas, puntuarlas o borrarlas como cualquier otra.
"""

from __future__ import annotations

from typing import Any, Final

L, D, B = ["lunch"], ["dinner"], ["lunch", "dinner"]


def _i(name: str, qty: float | None, unit: str = "g") -> dict[str, Any]:
    return {"name": name, "qty": qty, "unit": unit}


GUSTO = "gusto"

EXAMPLES: Final[list[dict[str, Any]]] = [
    # ---------------------------------------------------------------- legumbres
    {"name": "Lentejas estofadas con verduras", "icon": "🍲", "meals": L, "category": "legumbre", "rating": 5, "ingredients": [
        _i("Lentejas", 320), _i("Zanahorias", 2, "ud"), _i("Pimiento verde", 1, "ud"), _i("Cebolla", 1, "ud"),
        _i("Patatas", 2, "ud"), _i("Ajos", 2, "ud"), _i("Tomate triturado", 200), _i("Aceite de oliva", 3, "cda"),
        _i("Pimentón", None, GUSTO), _i("Laurel", None, GUSTO)]},
    {"name": "Potaje de garbanzos con bacalao y espinacas", "icon": "🥘", "meals": L, "category": "legumbre", "rating": 4, "ingredients": [
        _i("Garbanzos", 320), _i("Bacalao desalado", 300), _i("Espinacas", 250), _i("Patatas", 2, "ud"),
        _i("Cebolla", 1, "ud"), _i("Ajos", 2, "ud"), _i("Huevos", 2, "ud"), _i("Aceite de oliva", 3, "cda"),
        _i("Pimentón", None, GUSTO)]},
    {"name": "Alubias blancas con verduras", "icon": "🫘", "meals": L, "category": "legumbre", "rating": 3, "ingredients": [
        _i("Alubias", 320), _i("Puerros", 2, "ud"), _i("Zanahorias", 2, "ud"), _i("Pimiento rojo", 1, "ud"),
        _i("Calabacín", 1, "ud"), _i("Patatas", 2, "ud"), _i("Ajos", 2, "ud"), _i("Aceite de oliva", 3, "cda")]},
    {"name": "Garbanzos con espinacas y huevo", "icon": "🥬", "meals": B, "category": "legumbre", "rating": 4, "ingredients": [
        _i("Garbanzos cocidos", 800), _i("Espinacas", 300), _i("Huevos", 4, "ud"), _i("Cebolla", 1, "ud"),
        _i("Ajos", 2, "ud"), _i("Tomate triturado", 200), _i("Aceite de oliva", 2, "cda"), _i("Comino", None, GUSTO)]},
    {"name": "Ensalada de lentejas", "icon": "🥗", "meals": D, "category": "legumbre", "rating": 3, "ingredients": [
        _i("Lentejas cocidas", 600), _i("Tomates", 2, "ud"), _i("Pepino", 1, "ud"), _i("Pimiento rojo", 1, "ud"),
        _i("Cebolla morada", 1, "ud"), _i("Atún en lata", 2, "ud"), _i("Huevos", 2, "ud"),
        _i("Aceite de oliva", 3, "cda"), _i("Vinagre", 1, "cda")]},
    {"name": "Crema de lentejas rojas y calabaza", "icon": "🥣", "meals": D, "category": "legumbre", "rating": 4, "ingredients": [
        _i("Lentejas rojas", 250), _i("Calabaza", 400), _i("Zanahorias", 2, "ud"), _i("Cebolla", 1, "ud"),
        _i("Caldo de verduras", 1, "l"), _i("Aceite de oliva", 2, "cda"), _i("Comino", None, GUSTO), _i("Pan", 120)]},
    # ------------------------------------------------------------------ pescado
    {"name": "Merluza en salsa verde con patatas", "icon": "🐟", "meals": B, "category": "pescado", "rating": 4, "ingredients": [
        _i("Merluza", 600), _i("Patatas", 3, "ud"), _i("Guisantes", 150), _i("Ajos", 3, "ud"),
        _i("Caldo de pescado", 300, "ml"), _i("Harina", 1, "cda"), _i("Vino blanco", 50, "ml"),
        _i("Aceite de oliva", 3, "cda"), _i("Perejil", None, GUSTO)]},
    {"name": "Salmón al horno con verduras", "icon": "🍣", "meals": D, "category": "pescado", "rating": 5, "ingredients": [
        _i("Salmón", 500), _i("Calabacín", 1, "ud"), _i("Pimiento rojo", 1, "ud"), _i("Cebolla", 1, "ud"),
        _i("Tomates cherry", 200), _i("Patatas", 2, "ud"), _i("Aceite de oliva", 2, "cda"), _i("Limón", 1, "ud")]},
    {"name": "Bacalao con tomate y arroz blanco", "icon": "🍅", "meals": L, "category": "pescado", "rating": 3, "ingredients": [
        _i("Bacalao desalado", 600), _i("Tomate triturado", 400), _i("Cebolla", 1, "ud"), _i("Pimiento verde", 1, "ud"),
        _i("Ajos", 2, "ud"), _i("Arroz", 240), _i("Aceite de oliva", 3, "cda")]},
    {"name": "Lubina a la plancha con ensalada", "icon": "🐠", "meals": D, "category": "pescado", "rating": 4, "ingredients": [
        _i("Lubina", 600), _i("Lechuga", 1, "ud"), _i("Tomates", 2, "ud"), _i("Pepino", 1, "ud"),
        _i("Ajos", 2, "ud"), _i("Aceite de oliva", 3, "cda"), _i("Pan", 120)]},
    {"name": "Paella de marisco", "icon": "🥘", "meals": L, "category": "pescado", "rating": 4, "ingredients": [
        _i("Arroz bomba", 320), _i("Gambas", 300), _i("Calamares", 250), _i("Mejillones", 400),
        _i("Pimiento rojo", 1, "ud"), _i("Tomate triturado", 150), _i("Ajos", 3, "ud"),
        _i("Caldo de pescado", 1, "l"), _i("Aceite de oliva", 4, "cda"), _i("Azafrán", None, GUSTO)]},
    {"name": "Wok de verduras con langostinos", "icon": "🍜", "meals": D, "category": "pescado", "rating": 4, "ingredients": [
        _i("Noodles", 250), _i("Langostinos", 300), _i("Verduras para wok", 600), _i("Salsa de soja", 3, "cda"),
        _i("Ajos", 2, "ud"), _i("Aceite de oliva", 2, "cda"), _i("Jengibre", None, GUSTO)]},
    # -------------------------------------------------------------------- carne
    {"name": "Cuscús con carne picada y verduras", "icon": "🥘", "meals": L, "category": "carne", "rating": 4, "ingredients": [
        _i("Cuscús", 320), _i("Carne picada", 500), _i("Calabacín", 1, "ud"), _i("Zanahorias", 2, "ud"),
        _i("Cebolla", 1, "ud"), _i("Pimiento rojo", 1, "ud"), _i("Caldo de verduras", 400, "ml"),
        _i("Aceite de oliva", 2, "cda"), _i("Comino", None, GUSTO)]},
    {"name": "Albóndigas en salsa con arroz", "icon": "🧆", "meals": L, "category": "carne", "rating": 4, "ingredients": [
        _i("Carne picada", 500), _i("Huevos", 1, "ud"), _i("Pan rallado", 50), _i("Cebolla", 1, "ud"),
        _i("Ajos", 2, "ud"), _i("Tomate triturado", 400), _i("Zanahorias", 1, "ud"), _i("Vino blanco", 100, "ml"),
        _i("Arroz", 240), _i("Aceite de oliva", 2, "cda")]},
    {"name": "Pollo al horno con patatas", "icon": "🍗", "meals": L, "category": "carne", "rating": 4, "ingredients": [
        _i("Muslos de pollo", 6, "ud"), _i("Patatas", 4, "ud"), _i("Cebolla", 1, "ud"), _i("Pimiento rojo", 1, "ud"),
        _i("Ajos", 3, "ud"), _i("Vino blanco", 100, "ml"), _i("Aceite de oliva", 3, "cda"), _i("Tomillo", None, GUSTO)]},
    {"name": "Pollo al curry con arroz basmati", "icon": "🍛", "meals": L, "category": "carne", "rating": 5, "ingredients": [
        _i("Pechuga de pollo", 600), _i("Arroz basmati", 280), _i("Cebolla", 1, "ud"), _i("Leche de coco", 400, "ml"),
        _i("Espinacas", 200), _i("Curry", 2, "cda")]},
    {"name": "Fajitas de pollo", "icon": "🌯", "meals": D, "category": "carne", "rating": 4, "ingredients": [
        _i("Pechuga de pollo", 500), _i("Tortillas de trigo", 8, "ud"), _i("Pimiento rojo", 1, "ud"),
        _i("Pimiento verde", 1, "ud"), _i("Cebolla", 1, "ud"), _i("Yogur griego", 1, "ud"),
        _i("Aceite de oliva", 2, "cda"), _i("Especias", None, GUSTO)]},
    {"name": "Ensalada de pollo y quinoa", "icon": "🥗", "meals": D, "category": "carne", "rating": 3, "ingredients": [
        _i("Quinoa", 200), _i("Pechuga de pollo", 400), _i("Tomates cherry", 200), _i("Pepino", 1, "ud"),
        _i("Aguacate", 1, "ud"), _i("Lechuga", 1, "ud"), _i("Aceite de oliva", 3, "cda"), _i("Limón", 1, "ud")]},
    {"name": "Hamburguesas caseras con ensalada", "icon": "🍔", "meals": D, "category": "carne", "rating": 3, "ingredients": [
        _i("Hamburguesas", 4, "ud"), _i("Pan", 240), _i("Lechuga", 1, "ud"), _i("Tomates", 2, "ud"),
        _i("Cebolla", 1, "ud"), _i("Queso en lonchas", 4, "ud")]},
    # ------------------------------------------------------------ pasta y arroz
    {"name": "Espaguetis a la boloñesa", "icon": "🍝", "meals": L, "category": "cereal", "rating": 5, "ingredients": [
        _i("Espaguetis", 320), _i("Carne picada", 500), _i("Tomate triturado", 400), _i("Cebolla", 1, "ud"),
        _i("Zanahorias", 1, "ud"), _i("Ajos", 2, "ud"), _i("Queso rallado", 40), _i("Aceite de oliva", 2, "cda"),
        _i("Orégano", None, GUSTO)]},
    {"name": "Arroz con pollo y verduras", "icon": "🥘", "meals": L, "category": "cereal", "rating": 4, "ingredients": [
        _i("Arroz", 320), _i("Contramuslos de pollo", 500), _i("Pimiento rojo", 1, "ud"), _i("Judías verdes", 200),
        _i("Tomate triturado", 200), _i("Cebolla", 1, "ud"), _i("Ajos", 2, "ud"), _i("Caldo de pollo", 1, "l"),
        _i("Aceite de oliva", 3, "cda"), _i("Azafrán", None, GUSTO)]},
    {"name": "Ensalada de pasta con atún", "icon": "🥙", "meals": B, "category": "cereal", "rating": 3, "ingredients": [
        _i("Pasta", 300), _i("Atún en lata", 3, "ud"), _i("Tomates cherry", 250), _i("Maíz dulce", 150),
        _i("Pimiento rojo", 1, "ud"), _i("Aceitunas", 60), _i("Huevos", 2, "ud"), _i("Aceite de oliva", 3, "cda")]},
    {"name": "Macarrones con tomate y atún", "icon": "🍝", "meals": L, "category": "cereal", "rating": 3, "ingredients": [
        _i("Macarrones", 320), _i("Tomate frito", 300), _i("Atún en lata", 3, "ud"), _i("Cebolla", 1, "ud"),
        _i("Queso rallado", 40), _i("Aceite de oliva", 1, "cda")]},
    {"name": "Lasaña de verduras", "icon": "🫕", "meals": L, "category": "cereal", "rating": 2, "ingredients": [
        _i("Placas de lasaña", 250), _i("Espinacas", 300), _i("Calabacín", 1, "ud"), _i("Champiñones", 200),
        _i("Cebolla", 1, "ud"), _i("Bechamel", 500), _i("Tomate frito", 200), _i("Queso rallado", 100)],
        "base": "Pisto"},
    # ------------------------------------------------------------------- huevos
    {"name": "Tortilla de patatas con ensalada", "icon": "🍳", "meals": D, "category": "huevo", "rating": 5, "ingredients": [
        _i("Huevos", 8, "ud"), _i("Patatas", 4, "ud"), _i("Cebolla", 1, "ud"), _i("Lechuga", 1, "ud"),
        _i("Tomates", 2, "ud"), _i("Aceite de oliva", 5, "cda")]},
    {"name": "Revuelto de champiñones y trigueros", "icon": "🍄", "meals": D, "category": "huevo", "rating": 3, "ingredients": [
        _i("Huevos", 8, "ud"), _i("Champiñones", 300), _i("Espárragos trigueros", 250), _i("Ajos", 2, "ud"),
        _i("Aceite de oliva", 2, "cda"), _i("Pan", 160)]},
    {"name": "Huevos al horno con tomate y pimiento", "icon": "🥚", "meals": D, "category": "huevo", "rating": 4, "ingredients": [
        _i("Huevos", 8, "ud"), _i("Tomate triturado", 800), _i("Pimiento rojo", 2, "ud"), _i("Cebolla", 1, "ud"),
        _i("Ajos", 2, "ud"), _i("Aceite de oliva", 2, "cda"), _i("Pan", 160), _i("Comino", None, GUSTO)]},
    # ----------------------------------------------------------------- verduras
    {"name": "Crema de calabacín con jamón", "icon": "🥒", "meals": D, "category": "verdura", "rating": 4, "ingredients": [
        _i("Calabacín", 4, "ud"), _i("Puerros", 1, "ud"), _i("Patatas", 1, "ud"), _i("Queso fresco", 100),
        _i("Caldo de verduras", 500, "ml"), _i("Taquitos de jamón", 80), _i("Aceite de oliva", 2, "cda"), _i("Pan", 120)]},
    {"name": "Pisto con huevo", "icon": "🫑", "meals": B, "category": "verdura", "rating": 4, "ingredients": [
        _i("Calabacín", 2, "ud"), _i("Berenjena", 1, "ud"), _i("Pimiento rojo", 1, "ud"), _i("Pimiento verde", 1, "ud"),
        _i("Cebolla", 2, "ud"), _i("Tomate triturado", 400), _i("Huevos", 4, "ud"), _i("Aceite de oliva", 4, "cda"),
        _i("Pan", 120)], "base": "Pisto"},
    {"name": "Menestra de verduras con patatas", "icon": "🥕", "meals": B, "category": "verdura", "rating": 3, "ingredients": [
        _i("Menestra", 800), _i("Patatas", 2, "ud"), _i("Taquitos de jamón", 60), _i("Ajos", 2, "ud"),
        _i("Aceite de oliva", 3, "cda"), _i("Pan", 120)]},
    {"name": "Coliflor gratinada", "icon": "🥦", "meals": D, "category": "verdura", "rating": 3, "ingredients": [
        _i("Coliflor", 1, "ud"), _i("Patatas", 2, "ud"), _i("Bechamel", 300), _i("Queso rallado", 80),
        _i("Jamón cocido", 100), _i("Pan", 120)]},
    {"name": "Ensalada de tomate, aguacate y queso fresco", "icon": "🥗", "meals": D, "category": "verdura", "rating": 4, "ingredients": [
        _i("Tomates", 4, "ud"), _i("Aguacates", 2, "ud"), _i("Queso fresco", 250), _i("Cebolla morada", 1, "ud"),
        _i("Aceite de oliva", 3, "cda"), _i("Pan", 160)]},
    {"name": "Judías verdes con patatas y huevo", "icon": "🫛", "meals": D, "category": "verdura", "rating": 3, "ingredients": [
        _i("Judías verdes", 600), _i("Patatas", 3, "ud"), _i("Huevos", 2, "ud"), _i("Ajos", 2, "ud"),
        _i("Aceite de oliva", 3, "cda"), _i("Pimentón", None, GUSTO)]},
]
