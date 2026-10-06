"""Constantes de la integración Menú Semanal."""

from __future__ import annotations

from typing import Final

DOMAIN: Final = "menu_semanal"
NAME: Final = "Menú Semanal"
VERSION: Final = "1.0.0"

STORAGE_KEY: Final = DOMAIN
STORAGE_VERSION: Final = 1
SAVE_DELAY: Final = 1

# Panel lateral y ficheros estáticos
PANEL_URL_PATH: Final = "menu-semanal"
PANEL_ICON: Final = "mdi:calendar-week"
PANEL_COMPONENT: Final = "menu-semanal-panel"
STATIC_URL: Final = "/menu_semanal_static"
FRONTEND_FILE: Final = "menu-semanal.js"

# Integraciones hermanas
DESPENSA_DOMAIN: Final = "despensa"  # https://github.com/emero03/ha-despensa
CESTA_DOMAIN: Final = "cesta"  # https://github.com/emero03/ha-cesta

# Semana: 7 días (lunes a domingo) x 2 comidas
DAYS: Final = 7
MEALS: Final = ("lunch", "dinner")
MEAL_NAMES: Final = {"lunch": "Comida", "dinner": "Cena"}
DAY_NAMES: Final = ("Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo")
SLOTS: Final = DAYS * len(MEALS)

# Límites
MAX_RECIPES: Final = 500
MAX_INGREDIENTS: Final = 40
KEEP_WEEKS: Final = 16  # semanas pasadas que se guardan (para no repetir recetas y como historial)
HISTORY_WEEKS: Final = 4  # semanas anteriores que mira el planificador

# Reparto de las calorías del día: el resto va al desayuno, media mañana y merienda.
LUNCH_SHARE: Final = 0.35
DINNER_SHARE: Final = 0.30

DEFAULT_SETTINGS: Final[dict[str, object]] = {
    "people": 2,  # comensales: escala las cantidades al comprobar la despensa
    "kcal_day": 2000,  # ingesta de referencia de un adulto (kcal/día)
    "batch": True,  # agrupar recetas que comparten elaboración (batch cooking)
    "prefer_pantry": True,  # dar preferencia a recetas con ingredientes que ya hay
}

# Componente principal de cada receta: decide el color del borde.
CATEGORIES: Final[list[dict[str, str]]] = [
    {"id": "carne", "name": "Carne", "icon": "🥩", "color": "#795548"},
    {"id": "pescado", "name": "Pescado", "icon": "🐟", "color": "#1E88E5"},
    {"id": "huevo", "name": "Huevos", "icon": "🥚", "color": "#FBC02D"},
    {"id": "legumbre", "name": "Legumbres", "icon": "🫘", "color": "#E64A19"},
    {"id": "verdura", "name": "Verduras", "icon": "🥦", "color": "#43A047"},
    {"id": "cereal", "name": "Pasta y arroz", "icon": "🍝", "color": "#8E24AA"},
    {"id": "otros", "name": "Otros", "icon": "🍽️", "color": "#78909C"},
]
CATEGORY_IDS: Final = tuple(c["id"] for c in CATEGORIES)
FALLBACK_CATEGORY: Final = "otros"

# Unidades de los ingredientes de una receta
UNITS: Final[dict[str, dict[str, object]]] = {
    "g": {"name": "g", "kind": "mass", "factor": 1},
    "kg": {"name": "kg", "kind": "mass", "factor": 1000},
    "ml": {"name": "ml", "kind": "mass", "factor": 1},  # 1 ml ≈ 1 g: suficiente para estimar
    "l": {"name": "l", "kind": "mass", "factor": 1000},
    "cda": {"name": "cda", "kind": "mass", "factor": 15},  # cucharada
    "cdta": {"name": "cdta", "kind": "mass", "factor": 5},  # cucharadita
    "ud": {"name": "ud", "kind": "count", "factor": 1},
    "gusto": {"name": "al gusto", "kind": "any", "factor": 0},
}
DEFAULT_UNIT: Final = "g"

DEFAULT_ICON: Final = "🍽️"

# Servicios
SERVICE_GENERATE: Final = "generate"
SERVICE_CHECK: Final = "check_ingredients"
SERVICE_GET_MENU: Final = "get_menu"

ATTR_WEEK: Final = "week"
ATTR_ADD_TO_CESTA: Final = "add_to_cesta"
ATTR_DAY: Final = "day"
