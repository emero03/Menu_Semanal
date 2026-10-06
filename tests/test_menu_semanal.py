"""Tests de la integración Menú Semanal."""

from __future__ import annotations

from collections import Counter

import pytest

from homeassistant import config_entries
from homeassistant.components import frontend
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.exceptions import ServiceValidationError
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.menu_semanal.catalog import CATALOG
from custom_components.menu_semanal.const import CATEGORY_IDS, DOMAIN, SLOTS
from custom_components.menu_semanal.examples import EXAMPLES
from custom_components.menu_semanal.manager import resolve_week, shift_week, week_key, week_monday
from custom_components.menu_semanal.nutrition import FOODS, analyze, match_food
from custom_components.menu_semanal.pantry import check, fmt_amount, fmt_units, match_item
from custom_components.menu_semanal.planner import Context, Rng

from .conftest import HAS_CESTA, HAS_DESPENSA

NOW = "2026-10-04 12:00:00+02:00"  # domingo: la semana en curso es la 40 y la siguiente, la 41
CURRENT = "2026-W40"
NEXT = "2026-W41"
needs_siblings = pytest.mark.skipif(not (HAS_DESPENSA and HAS_CESTA), reason="Faltan Despensa o Cesta")


@pytest.fixture
def sunday(freezer):
    """Domingo 4 de octubre de 2026 (antes de crear Home Assistant y sus credenciales)."""
    freezer.move_to(NOW)
    return freezer


def _manager(hass: HomeAssistant):
    return hass.data[DOMAIN]


EVENTS: dict[int, list] = {}


async def _ws(client, **msg):
    """Envía un comando y devuelve su respuesta (los eventos de la suscripción se guardan aparte)."""
    await client.send_json_auto_id(msg)
    while True:
        resp = await client.receive_json()
        if resp.get("type") == "event":
            EVENTS.setdefault(id(client), []).append(resp["event"])
            continue
        return resp


def _last_event(client):
    return EVENTS[id(client)][-1]


async def _ok(client, **msg):
    resp = await _ws(client, **msg)
    assert resp["success"], resp
    return resp["result"]


def _recipe(name, meals=("lunch",), category=None, rating=3, ingredients=(), **extra):
    data = {
        "name": name,
        "meals": list(meals),
        "rating": rating,
        "servings": extra.pop("servings", 2),
        "ingredients": [{"name": n, "qty": q, "unit": u} for n, q, u in ingredients],
        **extra,
    }
    if category:
        data["category"] = category
    return data


# ----------------------------------------------------------- piezas sueltas
def test_rng_matches_javascript() -> None:
    """Los mismos números que mulberry32 en JavaScript (la vista previa depende de ello)."""
    rng = Rng(42)
    values = [round(rng.random(), 10) for _ in range(4)]
    assert values == [0.6011037519, 0.4482905590, 0.8524657935, 0.6697340414]


def test_tables_are_consistent() -> None:
    assert {c["department"] for c in CATALOG} >= {"fruta_verdura", "carne", "pescado", "despensa"}
    names = [n for entry in FOODS for n in entry[0]]
    assert len(names) == len(set(names)), "nombre repetido en la tabla de alimentos"
    for example in EXAMPLES:
        assert example["category"] in CATEGORY_IDS
        info = analyze({**example, "servings": 4})
        assert info["unknown"] == [], example["name"]
        assert 250 < info["kcal"] < 900, example["name"]


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("Tomates", "tomates"),
        ("tomate", "tomates"),
        ("Pechugas de pollo", "pechuga de pollo"),
        ("carne picada de cerdo", "carne picada"),
        ("Caldo de pollo", "caldo"),
        ("Tomate frito", "tomate frito"),
        ("Atún", "atun en lata"),
        ("Garbanzos cocidos", "garbanzos cocidos"),
        ("Aceite de oliva virgen extra", "aceite de oliva"),
        ("Cebolla morada", "cebollas"),
        ("Unicornio", None),
    ],
)
def test_match_food(name, expected) -> None:
    food = match_food(name)
    assert (food["name"] if food else None) == expected


def test_analyze_recipe() -> None:
    info = analyze(
        {
            "servings": 4,
            "ingredients": [
                {"name": "Lentejas", "qty": 320, "unit": "g"},
                {"name": "Zanahorias", "qty": 2, "unit": "ud"},
                {"name": "Aceite de oliva", "qty": 3, "unit": "cda"},
                {"name": "Sal", "qty": None, "unit": "gusto"},
                {"name": "Polvo de hadas", "qty": 5, "unit": "g"},
            ],
        }
    )
    # 320 g lentejas (1056 kcal) + 160 g zanahoria (64) + 45 g aceite (405) = 1525 / 4
    assert info["kcal"] == pytest.approx(381.3, abs=0.1)
    assert info["suggested_category"] == "legumbre"
    assert info["portions"]["legumbre"] is True
    assert info["veg_g"] == 40
    assert info["unknown"] == ["Polvo de hadas"]
    assert [b["name"] for b in info["bases"]] == ["Lentejas"]
    # kcal a mano y base propia
    manual = analyze({"servings": 2, "kcal": 650, "base": "Sofrito", "ingredients": []})
    assert manual["kcal"] == 650 and manual["kcal_manual"] is True
    assert manual["bases"] == [{"key": "sofrito", "name": "Sofrito"}]


def test_weeks(freezer) -> None:
    freezer.move_to(NOW)
    assert week_key(week_monday("2026-W01")) == "2026-W01"
    assert week_monday("2026-W41").isoformat() == "2026-10-05"
    assert shift_week("2026-W52", 1) == "2026-W53"
    assert shift_week("2026-W53", 1) == "2027-W01"
    assert resolve_week("current") == CURRENT
    assert resolve_week("próxima") == NEXT
    assert resolve_week("2026-10-12") == "2026-W42"
    assert resolve_week("2026-w42") == "2026-W42"


def test_formats() -> None:
    assert fmt_amount(750) == "750 g"
    assert fmt_amount(1500) == "1,5 kg"
    assert fmt_amount(500, True) == "500 ml"
    assert fmt_amount(2000, True) == "2 l"
    assert fmt_units(1, "paquetes") == "1 paquete"
    assert fmt_units(2, "paquetes") == "2 paquetes"
    assert fmt_units(1, "uds") == "1 ud"
    assert fmt_units(1, "unidades") == "1 unidad"
    assert fmt_units(3) == "3 uds"


def test_match_pantry_item() -> None:
    items = [
        {"id": "1", "name": "Tomates", "stock": 3},
        {"id": "2", "name": "Atún en lata", "stock": 2},
        {"id": "3", "name": "Queso curado", "stock": 0},
        {"id": "4", "name": "Queso rallado", "stock": 1},
        {"id": "5", "name": "Leche", "stock": 4},
    ]
    assert match_item("tomate", items)["id"] == "1"
    assert match_item("Atún", items)["id"] == "2"
    assert match_item("Queso", items)["id"] == "4"  # el que hay
    assert match_item("Leche entera", items)["id"] == "5"
    assert match_item("Garbanzos", items) is None


def _line(name, qty, unit="g", recipe="R"):
    return {"name": name, "qty": qty, "unit": unit, "recipe_id": recipe, "recipe": recipe, "day": 0, "meal": "lunch"}


def test_check_units() -> None:
    items = [
        {"id": "pasta", "name": "Pasta", "stock": 1, "unit": "", "icon": "🍝", "department": "despensa"},
        {"id": "patatas", "name": "Patatas", "stock": 1, "unit": "kg", "icon": "🥔", "department": "fruta_verdura"},
        {"id": "huevos", "name": "Huevos", "stock": 2, "unit": "", "icon": "🥚", "department": "lacteos"},
        {"id": "salmon", "name": "Salmón", "stock": 1, "unit": "bandejas", "icon": "🐟", "department": "pescado"},
        {"id": "leche", "name": "Leche", "stock": 0, "unit": "bricks", "icon": "🥛", "department": "lacteos"},
        {"id": "pimienta", "name": "Pimienta", "stock": 0, "unit": "", "icon": "🧂", "department": "despensa"},
    ]
    lines = [
        _line("Espaguetis", 300), _line("Macarrones", 400),  # no son "Pasta": van aparte
        _line("Pasta", 750),  # 1 paquete = 500 g → falta 1
        _line("Patatas", 4, "ud"),  # 4 x 200 g = 800 g ≤ 1 kg
        _line("Patatas", 300),  # 1100 g > 1 kg → falta 1 kg
        _line("Huevos", 6, "ud"),  # 6 > 2 → faltan 4
        _line("Salmón", 400),  # no se sabe lo que pesa una bandeja → se da por bueno
        _line("Leche", 200, "ml"),
        _line("Pimienta", None, "gusto"),  # controlada en la despensa y agotada → falta
        _line("Sal", None, "gusto"),  # básico sin controlar → se da por bueno
        _line("Tomate triturado", 600),  # no está: 2 latas de 400 g
        _line("Agua", 1, "l"),  # el agua no cuenta
    ]
    result = {r["name"]: r for r in check(lines, items, set(), {})}
    assert "Agua" not in result
    assert result["Pasta"]["status"] == "missing" and result["Pasta"]["note"] == "1 paquete"
    assert result["Pasta"]["need_text"] == "750 g"
    assert result["Pasta"]["have_text"] == "1 ud (≈ 500 g)"
    assert result["Patatas"]["status"] == "missing" and result["Patatas"]["note"] == "1 kg"
    assert result["Patatas"]["need_text"] == "1,1 kg"
    assert result["Huevos"]["missing"] == 4 and result["Huevos"]["note"] == "4 uds"
    assert result["Salmón"]["status"] == "unsure"
    assert result["Leche"]["note"] == "1 brick" and result["Leche"]["need_text"] == "200 ml"
    assert result["Pimienta"]["status"] == "missing"
    assert result["Sal"]["status"] == "untracked"
    assert result["Tomate triturado"]["note"] == "2 latas"
    assert result["Espaguetis"]["status"] == "missing"

    # Con la equivalencia puesta, el salmón ya se puede comprobar
    eq = {"salmon": {"name": "Salmón", "grams": 250, "volume": False}}
    salmon = next(r for r in check(lines, items, set(), eq) if r["name"] == "Salmón")
    assert salmon["status"] == "missing" and salmon["missing"] == 1 and salmon["note"] == "1 ud"

    # Ya en la Cesta
    in_cesta = {"tomat triturado"}
    tomato = next(r for r in check(lines, items, in_cesta, {}) if r["name"] == "Tomate triturado")
    assert tomato["status"] == "in_cesta"

    # Sin Despensa todo lo que no es básico falta
    no_pantry = {r["name"]: r["status"] for r in check(lines, None, set(), {})}
    assert no_pantry["Huevos"] == "missing" and no_pantry["Sal"] == "untracked"


# ------------------------------------------------------------- planificador
def _example_context(seed=1, history=None, settings=None):
    recipes = [{**r, "id": f"r{i}", "servings": 4} for i, r in enumerate(EXAMPLES)]
    infos = {r["id"]: analyze(r) for r in recipes}
    settings = {"people": 2, "kcal_day": 2000, "batch": True, "prefer_pantry": False, **(settings or {})}
    return recipes, Context(recipes, infos, settings, history or {}, {}, seed)


def test_planner_is_balanced() -> None:
    for seed in range(1, 6):
        recipes, ctx = _example_context(seed)
        week = ctx.generate([None] * SLOTS)
        assert all(week), "todos los huecos rellenos"
        for i, cand in enumerate(week):
            assert ("lunch" if i % 2 == 0 else "dinner") in cand.meals
        counts = Counter()
        for cand in week:
            for key, value in cand.counts.items():
                counts[key] += value
        assert counts["legumbre"] >= 4
        assert counts["pescado"] >= 3
        assert counts["carne"] <= 3
        assert counts["verdura"] >= 1
        # sin repetir el mismo plato el mismo día ni dos platos iguales seguidos
        for d in range(7):
            assert week[2 * d].id != week[2 * d + 1].id
        assert len({c.id for c in week}) >= 12


def test_planner_is_deterministic_and_varied() -> None:
    _, a = _example_context(7)
    _, b = _example_context(7)
    _, c = _example_context(8)
    wa = [x.id for x in a.generate([None] * SLOTS)]
    assert wa == [x.id for x in b.generate([None] * SLOTS)]
    assert wa != [x.id for x in c.generate([None] * SLOTS)]


def test_planner_prefers_high_ratings() -> None:
    picks = Counter()
    for seed in range(1, 13):
        recipes, ctx = _example_context(seed)
        for cand in ctx.generate([None] * SLOTS):
            picks[cand.rating] += 1
    per_recipe = {
        rating: picks[rating] / sum(1 for r in EXAMPLES if r["rating"] == rating) for rating in (2, 3, 4, 5)
    }
    assert per_recipe[5] > per_recipe[3] > per_recipe[2]


def test_planner_avoids_last_week() -> None:
    recipes, ctx = _example_context(3)
    first = ctx.generate([None] * SLOTS)
    history = {c.id: 1 for c in first}
    _, ctx2 = _example_context(3, history)
    second = ctx2.generate([None] * SLOTS)
    repeated = {c.id for c in first} & {c.id for c in second}
    assert len(repeated) <= 7


def test_planner_batch_cooking() -> None:
    """Platos distintos que comparten elaboración (el cuscús y la boloñesa con carne picada)."""

    def shared_bases(week):
        groups: dict[str, set] = {}
        for i, cand in enumerate(week):
            for base in cand.bases:
                groups.setdefault(base, set()).add((cand.id, i // 2))
        return {b for b, uses in groups.items() if len({r for r, _ in uses}) >= 2 and len({d for _, d in uses}) >= 2}

    on = off = 0
    minced_on = minced_off = 0
    for seed in range(1, 21):
        _, ctx = _example_context(seed)
        bases = shared_bases(ctx.generate([None] * SLOTS))
        on += len(bases)
        minced_on += "carne picada" in bases
        _, ctx = _example_context(seed, settings={"batch": False})
        bases = shared_bases(ctx.generate([None] * SLOTS))
        off += len(bases)
        minced_off += "carne picada" in bases
    assert on > off
    assert minced_on > minced_off

    # Dos comidas y cuatro platos de carne: con batch cooking se eligen los que comparten carne picada
    recipes = [
        {**_recipe("Cuscús con carne picada", ingredients=[("Cuscús", 160, "g"), ("Carne picada", 200, "g"), ("Calabacín", 1, "ud")]), "id": "cus", "category": "carne"},
        {**_recipe("Espaguetis a la boloñesa", ingredients=[("Espaguetis", 160, "g"), ("Carne picada", 200, "g"), ("Tomate triturado", 200, "g")]), "id": "bol", "category": "cereal"},
        {**_recipe("Lomo con pimientos", ingredients=[("Lomo de cerdo", 200, "g"), ("Arroz", 160, "g"), ("Pimiento", 1, "ud")]), "id": "lom", "category": "carne"},
        {**_recipe("Ternera guisada", ingredients=[("Ternera", 200, "g"), ("Patatas", 2, "ud"), ("Zanahorias", 1, "ud")]), "id": "ter", "category": "carne"},
    ]
    infos = {r["id"]: analyze(r) for r in recipes}
    fixed = [None, "free", None] + ["free"] * 11  # comida del lunes y del martes
    pairs = {True: 0, False: 0}
    for batch in (True, False):
        for seed in range(1, 11):
            ctx = Context(recipes, infos, {"kcal_day": 2000, "batch": batch}, {}, {}, seed)
            pairs[batch] += {c.id for c in ctx.generate(fixed) if c} == {"cus", "bol"}
    assert pairs[True] > pairs[False]


def test_planner_change_prefers_similar() -> None:
    recipes, ctx = _example_context(5)
    week = [c.id for c in ctx.generate([None] * SLOTS)]
    by_id = {r["id"]: r for r in recipes}
    seen = {week[0]}
    for _ in range(4):
        cand, _restarted = ctx.change(week, 0, list(seen))
        assert cand.id not in seen and "lunch" in cand.meals
        seen.add(cand.id)
    cand, _ = ctx.change(week, 0, [week[0]])
    assert cand.cat == by_id[week[0]]["category"] or cand.cat in ("legumbre", "pescado", "carne", "cereal", "verdura", "huevo")


# -------------------------------------------------------------- alta / baja
async def test_config_flow(hass: HomeAssistant) -> None:
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    assert result["type"] is FlowResultType.FORM
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    assert result["type"] is FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "single_instance_allowed"


async def test_setup_and_unload(hass: HomeAssistant, setup_menu: MockConfigEntry, hass_client) -> None:
    panel = hass.data[frontend.DATA_PANELS]["menu-semanal"]
    assert panel.sidebar_title == "Menú Semanal"
    assert panel.sidebar_icon == "mdi:calendar-week"
    module_url = panel.config["_panel_custom"]["module_url"]
    assert module_url.startswith("/menu_semanal_static/menu-semanal.js?v=")
    assert module_url in hass.data[frontend.DATA_EXTRA_MODULE_URL].urls

    client = await hass_client()
    resp = await client.get("/menu_semanal_static/menu-semanal.js")
    assert resp.status == 200

    assert hass.states.get("sensor.menu_semanal_comida_de_hoy").state == "Sin planificar"
    assert hass.states.get("sensor.menu_semanal_cena_de_hoy").state == "Sin planificar"
    snap = _manager(hass).snapshot()
    assert snap["despensa"]["available"] is False
    assert snap["cesta"]["available"] is False

    assert await hass.config_entries.async_unload(setup_menu.entry_id)
    await hass.async_block_till_done()
    assert setup_menu.state is ConfigEntryState.NOT_LOADED
    assert "menu-semanal" not in hass.data.get(frontend.DATA_PANELS, {})
    assert DOMAIN not in hass.data


# ------------------------------------------------------------------ recetas
async def test_recipes_via_websocket(hass: HomeAssistant, setup_menu, hass_ws_client) -> None:
    client = await hass_ws_client(hass)
    await _ok(client, type="menu_semanal/subscribe")
    first = await client.receive_json()
    assert first["event"]["recipes"] == []
    assert first["event"]["categories"][0] == {"id": "carne", "name": "Carne", "icon": "🥩", "color": "#795548"}
    assert first["event"]["current_week"] in first["event"]["weeks"]

    saved = await _ok(
        client,
        type="menu_semanal/recipe/save",
        **_recipe(
            "  lentejas con chorizo ",
            meals=["lunch"],
            rating=5,
            servings=4,
            ingredients=[("Lentejas", 300, "g"), ("Chorizo", 100, "g"), ("Zanahorias", "2", "ud"), ("Sal", 5, "gusto"), ("", 1, "g")],
        ),
    )
    recipe = saved["recipe"]
    assert recipe["name"] == "Lentejas con chorizo"
    assert recipe["category"] == "legumbre"  # deducida de los ingredientes
    assert recipe["icon"] == "🫘"
    assert recipe["ingredients"][2] == {"name": "Zanahorias", "qty": 2, "unit": "ud"}
    assert recipe["ingredients"][3] == {"name": "Sal", "qty": None, "unit": "gusto"}
    assert len(recipe["ingredients"]) == 4
    assert saved["info"]["kcal"] > 300

    # El panel recibe el cambio
    assert _last_event(client)["recipes"][0]["info"]["portions"]["legumbre"] is True

    dup = await _ws(client, type="menu_semanal/recipe/save", **_recipe("Lentejas con CHORIZO", meals=["dinner"]))
    assert dup["error"]["code"] == "duplicate"
    no_meal = await _ws(client, type="menu_semanal/recipe/save", **_recipe("Otra", meals=[]))
    assert no_meal["error"]["code"] == "meals_required"

    updated = await _ok(
        client,
        type="menu_semanal/recipe/save",
        recipe_id=recipe["id"],
        **_recipe("Lentejas con chorizo", meals=["lunch", "dinner"], rating=2, category="carne", ingredients=[("Lentejas", 300, "g")]),
    )
    assert updated["recipe"]["id"] == recipe["id"]
    assert updated["recipe"]["rating"] == 2 and updated["recipe"]["category"] == "carne"
    assert updated["recipe"]["created_at"] == recipe["created_at"]

    estimate = await _ok(
        client, type="menu_semanal/recipe/estimate", servings=2, ingredients=[{"name": "Huevos", "qty": 4, "unit": "ud"}]
    )
    assert estimate["kcal"] == pytest.approx(159.5, abs=0.1)
    assert estimate["suggested_category"] == "huevo"

    await _ok(client, type="menu_semanal/recipe/delete", recipe_id=recipe["id"])
    assert _manager(hass).recipes == []
    await _ok(client, type="menu_semanal/recipe/restore", recipe_id=recipe["id"])
    assert [r["name"] for r in _manager(hass).recipes] == ["Lentejas con chorizo"]

    added = await _ok(client, type="menu_semanal/recipes/examples")
    assert added["added"] == len(EXAMPLES)
    assert (await _ok(client, type="menu_semanal/recipes/examples"))["added"] == 0


# ------------------------------------------------------------------ semanas
async def test_generate_change_and_slots(sunday, hass: HomeAssistant, setup_menu, hass_ws_client) -> None:
    client = await hass_ws_client(hass)
    no_recipes = await _ws(client, type="menu_semanal/week/generate", week=NEXT)
    assert no_recipes["error"]["code"] == "no_recipes"
    await _ok(client, type="menu_semanal/recipes/examples")
    manager = _manager(hass)
    tortilla = manager.find_recipe("Tortilla de patatas con ensalada")

    # Fijar un plato y dejar un hueco libre antes de generar
    await _ok(client, type="menu_semanal/slot/set", week=NEXT, slot=1, recipe_id=tortilla["id"])
    await _ok(client, type="menu_semanal/slot/set", week=NEXT, slot=13, free=True)
    wrong = await _ws(client, type="menu_semanal/slot/set", week=NEXT, slot=0, recipe_id=tortilla["id"])
    assert wrong["error"]["code"] == "wrong_meal"

    result = await _ok(client, type="menu_semanal/week/generate", week=NEXT, seed=11)
    slots = manager.slots(NEXT)
    assert slots[1]["recipe_id"] == tortilla["id"] and slots[1]["locked"] is True
    assert slots[13]["free"] is True and slots[13]["recipe_id"] is None
    assert all(s["recipe_id"] for i, s in enumerate(slots) if i != 13)
    assert result["previous"][1]["recipe_id"] == tortilla["id"]

    # Misma semilla, mismo menú
    again = await _ok(client, type="menu_semanal/week/generate", week=NEXT, seed=11)
    assert [s["recipe_id"] for s in again["slots"]] == [s["recipe_id"] for s in slots]

    summary = manager.week_snapshot(NEXT)["summary"]
    assert summary["planned"] == 13
    assert len(summary["days"]) == 7
    assert summary["days"][6]["meals"] == 1
    assert summary["days"][0]["kcal"] > 600
    weekly = {w["id"]: w for w in summary["weekly"]}
    assert weekly["legumbre"]["min"] == 4 and weekly["legumbre"]["count"] >= 3

    # CAMBIO: otra receta para la comida del lunes, que también sea de comida
    before = slots[0]["recipe_id"]
    changed = await _ok(client, type="menu_semanal/slot/change", week=NEXT, slot=0)
    after = manager.slots(NEXT)[0]
    assert after["recipe_id"] != before
    assert "lunch" in manager.get_recipe(after["recipe_id"])["meals"]
    assert changed["previous"]["recipe_id"] == before
    # Pulsar CAMBIO otra vez no vuelve a la primera
    await _ok(client, type="menu_semanal/slot/change", week=NEXT, slot=0)
    third = manager.slots(NEXT)[0]
    assert third["recipe_id"] not in (before, after["recipe_id"])
    assert set(third["rejected"]) >= {before, after["recipe_id"]}

    # Deshacer
    await _ok(client, type="menu_semanal/week/restore", week=NEXT, slots=result["previous"])
    assert manager.slots(NEXT)[0]["recipe_id"] is None
    assert manager.slots(NEXT)[1]["recipe_id"] == tortilla["id"]

    # Fijar / soltar
    await _ok(client, type="menu_semanal/week/generate", week=NEXT)
    await _ok(client, type="menu_semanal/slot/lock", week=NEXT, slot=1, locked=False)
    assert manager.slots(NEXT)[1]["locked"] is False
    empty = await _ws(client, type="menu_semanal/slot/lock", week=NEXT, slot=13, locked=True)
    assert empty["error"]["code"] == "empty_slot"

    # Borrar una receta la quita del menú
    rid = manager.slots(NEXT)[2]["recipe_id"]
    await _ok(client, type="menu_semanal/recipe/delete", recipe_id=rid)
    assert all(s["recipe_id"] != rid for s in manager.slots(NEXT))
    await _ok(client, type="menu_semanal/recipe/restore", recipe_id=rid)
    assert manager.slots(NEXT)[2]["recipe_id"] == rid

    cleared = await _ok(client, type="menu_semanal/week/clear", week=NEXT)
    assert len(cleared["previous"]) == SLOTS
    assert all(s["recipe_id"] is None for s in manager.slots(NEXT))


async def test_generation_avoids_previous_week(sunday, hass: HomeAssistant, setup_menu) -> None:
    manager = _manager(hass)
    manager.load_examples()
    await manager.async_generate(CURRENT, seed=1)
    await manager.async_generate(NEXT, seed=1)
    first = {s["recipe_id"] for s in manager.slots(CURRENT)}
    second = {s["recipe_id"] for s in manager.slots(NEXT)}
    assert len(first & second) <= 7


async def test_settings_colors_and_equivalences(hass: HomeAssistant, setup_menu, hass_ws_client) -> None:
    client = await hass_ws_client(hass)
    await _ok(client, type="menu_semanal/settings/set", people=4, kcal_day=1800, batch=False)
    settings = _manager(hass).settings
    assert settings["people"] == 4 and settings["kcal_day"] == 1800 and settings["batch"] is False
    bad = await _ws(client, type="menu_semanal/settings/set", people=40)
    assert bad["success"] is False

    await _ok(client, type="menu_semanal/category/color", category="verdura", color="#00ff00")
    assert next(c for c in _manager(hass).categories if c["id"] == "verdura")["color"] == "#00ff00"
    await _ok(client, type="menu_semanal/category/color", category="verdura", color=None)
    assert next(c for c in _manager(hass).categories if c["id"] == "verdura")["color"] == "#43A047"
    bad_color = await _ws(client, type="menu_semanal/category/color", category="verdura", color="verde")
    assert bad_color["error"]["code"] == "invalid_color"

    await _ok(client, type="menu_semanal/equivalence/set", name="Salmón", grams=250)
    assert _manager(hass).snapshot()["equivalences"] == [{"name": "Salmón", "grams": 250.0, "volume": False}]
    await _ok(client, type="menu_semanal/equivalence/set", name="salmon", grams=None)
    assert _manager(hass).snapshot()["equivalences"] == []


async def test_services_and_sensors(sunday, hass: HomeAssistant, setup_menu) -> None:
    manager = _manager(hass)
    manager.load_examples()
    tortilla = manager.find_recipe("Tortilla de patatas con ensalada")
    manager.set_slot(CURRENT, 13, tortilla["id"])  # domingo, cena
    manager.set_slot(CURRENT, 12, None, free=True)  # domingo, comida: fuera
    await hass.async_block_till_done()
    assert hass.states.get("sensor.menu_semanal_cena_de_hoy").state == "Tortilla de patatas con ensalada"
    state = hass.states.get("sensor.menu_semanal_cena_de_hoy")
    assert state.attributes["icono"] == "🍳"
    assert "Huevos: 4 ud" in state.attributes["ingredientes"]
    assert hass.states.get("sensor.menu_semanal_comida_de_hoy").state == "Libre"

    menu = await hass.services.async_call(DOMAIN, "generate", {"week": "next"}, blocking=True, return_response=True)
    assert menu["week"] == NEXT
    assert len(menu["days"]) == 7 and menu["days"][0]["comida"]
    assert menu["text"].startswith("Lunes. Comida: ")

    today = await hass.services.async_call(DOMAIN, "get_menu", {"day": "hoy"}, blocking=True, return_response=True)
    assert today["days"] == [{"day": "Domingo", "date": "2026-10-04", "comida": "Libre", "cena": "Tortilla de patatas con ensalada", "kcal": today["days"][0]["kcal"]}]
    tomorrow = await hass.services.async_call(DOMAIN, "get_menu", {"day": "mañana"}, blocking=True, return_response=True)
    assert tomorrow["week"] == NEXT and tomorrow["days"][0]["day"] == "Lunes"

    check_result = await hass.services.async_call(
        DOMAIN, "check_ingredients", {"week": "next"}, blocking=True, return_response=True
    )
    assert check_result["count"] > 5  # sin Despensa, falta todo lo que no es básico
    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(
            DOMAIN, "check_ingredients", {"week": "next", "add_to_cesta": True}, blocking=True, return_response=True
        )
    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(DOMAIN, "generate", {"week": "la semana de los tres jueves"}, blocking=True)


# ------------------------------------------------- con Despensa y con Cesta
@needs_siblings
async def test_check_and_add_to_cesta(sunday, hass: HomeAssistant, setup_all, hass_ws_client) -> None:
    client = await hass_ws_client(hass)
    manager = _manager(hass)
    despensa = hass.data["despensa"]
    cesta = hass.data["cesta"]
    await hass.async_block_till_done()
    assert manager.snapshot()["despensa"]["available"] is True
    assert manager.snapshot()["cesta"]["available"] is True

    await _ok(client, type="menu_semanal/settings/set", people=4)
    cuscus = manager.save_recipe(
        _recipe("Cuscús con carne picada", ingredients=[("Cuscús", 160, "g"), ("Carne picada", 250, "g"), ("Cebolla", 1, "ud"), ("Sal", None, "gusto")])
    )
    bolo = manager.save_recipe(
        _recipe("Espaguetis a la boloñesa", ingredients=[("Espaguetis", 160, "g"), ("Carne picada", 250, "g"), ("Tomate triturado", 200, "g"), ("Aceite de oliva", 2, "cda")])
    )
    manager.set_slot(NEXT, 0, cuscus["id"])  # lunes
    manager.set_slot(NEXT, 4, bolo["id"])  # miércoles

    despensa.create_item("Carne picada", stock=0)
    despensa.create_item("Cuscús", stock=1)
    despensa.create_item("Espaguetis", stock=1)
    despensa.create_item("Cebollas", stock=3)
    await hass.async_block_till_done()

    # El panel ve las bases compartidas (batch cooking)
    batch = manager.week_snapshot(NEXT)["summary"]["batch"]
    assert [g["name"] for g in batch] == ["Carne picada"]
    assert batch[0]["amount"] == {"grams": 1000}

    result = await _ok(client, type="menu_semanal/check", week=NEXT)
    assert result["despensa"] is True and result["cesta"] is True and result["from_day"] == 0
    by_name = {r["name"]: r for r in result["items"]}
    assert by_name["Carne picada"]["status"] == "missing"
    assert by_name["Carne picada"]["need_text"] == "1 kg"
    assert by_name["Carne picada"]["note"] == "2 paquetes"
    assert by_name["Tomate triturado"]["status"] == "missing" and by_name["Tomate triturado"]["note"] == "1 lata"
    assert by_name["Cuscús"]["status"] == "ok"  # 320 g ≤ 1 paquete de 500 g
    assert by_name["Espaguetis"]["status"] == "ok"
    assert by_name["Cebollas"]["status"] == "ok"  # 2 de 3
    assert by_name["Sal"]["status"] == "untracked"
    assert by_name["Aceite de oliva"]["status"] == "untracked"
    assert result["missing"] == 2

    missing = [r for r in result["items"] if r["status"] == "missing"]
    added = await _ok(
        client,
        type="menu_semanal/cesta/add",
        items=[{k: r[k] for k in ("name", "note", "icon", "department")} for r in missing],
    )
    assert sorted(added["added"]) == ["Carne picada", "Tomate triturado"]
    in_list = {i["name"]: i for i in cesta.data["items"]}
    assert in_list["Carne picada"]["note"] == "2 paquetes"
    assert in_list["Tomate triturado"]["note"] == "1 lata"
    assert in_list["Carne picada"]["department"] == "carne"

    # Ahora salen como "ya en la Cesta" y no se vuelven a añadir
    again = await _ok(client, type="menu_semanal/check", week=NEXT)
    assert {r["name"]: r["status"] for r in again["items"]}["Carne picada"] == "in_cesta"
    assert (await _ok(client, type="menu_semanal/cesta/add", items=[{"name": "Carne picada"}]))["added"] == []

    # Comprado en la Cesta → la Despensa suma 2 paquetes → ya no falta nada
    for item in list(cesta.data["items"]):
        cesta.purchase_item(item["id"])
    await hass.async_block_till_done()
    assert despensa.find_by_name("Carne picada")["stock"] == 2
    final = await _ok(client, type="menu_semanal/check", week=NEXT)
    assert final["missing"] == 0

    # En la semana en curso (domingo) solo cuenta desde hoy
    manager.set_slot(CURRENT, 0, cuscus["id"])
    current = await _ok(client, type="menu_semanal/check", week=CURRENT)
    assert current["from_day"] == 6 and current["items"] == []

    # La Despensa da preferencia a recetas con lo que hay (y el panel recibe sus productos)
    snap = manager.snapshot()
    assert {i["name"] for i in snap["despensa"]["items"]} >= {"Carne picada", "Cuscús"}


@needs_siblings
async def test_service_adds_missing_to_cesta(sunday, hass: HomeAssistant, setup_all) -> None:
    manager = _manager(hass)
    recipe = manager.save_recipe(_recipe("Huevos rotos", ingredients=[("Huevos", 4, "ud"), ("Patatas", 2, "ud")]))
    manager.set_slot(NEXT, 0, recipe["id"])
    hass.data["despensa"].create_item("Huevos", stock=1)
    result = await hass.services.async_call(
        DOMAIN, "check_ingredients", {"week": "next", "add_to_cesta": True}, blocking=True, return_response=True
    )
    assert result["count"] == 2
    assert sorted(result["added"]) == ["Huevos", "Patatas"]
    notes = {i["name"]: i["note"] for i in hass.data["cesta"].data["items"]}
    assert notes == {"Huevos": "3 uds", "Patatas": "2 uds"}
    assert "Huevos" in result["text"]
