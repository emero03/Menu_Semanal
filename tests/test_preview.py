"""La vista previa usa una copia en JavaScript del planificador: debe dar exactamente lo mismo.

Se salta si no hay Node.js instalado.
"""

from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess

import pytest

from custom_components.menu_semanal.examples import EXAMPLES
from custom_components.menu_semanal.nutrition import analyze
from custom_components.menu_semanal.pantry import check
from custom_components.menu_semanal.planner import SLOTS, Context, summarize

ROOT = Path(__file__).resolve().parent.parent
NODE = shutil.which("node")
pytestmark = pytest.mark.skipif(NODE is None, reason="Node.js no está instalado")

SETTINGS = {"people": 2, "kcal_day": 2000, "batch": True, "prefer_pantry": True}
PANTRY = [
    {"id": "1", "name": "Lentejas", "stock": 1, "unit": "", "icon": "🫘", "department": "despensa"},
    {"id": "2", "name": "Carne picada", "stock": 0, "unit": "", "icon": "🥩", "department": "carne"},
    {"id": "3", "name": "Patatas", "stock": 1, "unit": "kg", "icon": "🥔", "department": "fruta_verdura"},
    {"id": "4", "name": "Huevos", "stock": 3, "unit": "", "icon": "🥚", "department": "lacteos"},
    {"id": "5", "name": "Salmón", "stock": 1, "unit": "bandejas", "icon": "🐟", "department": "pescado"},
    {"id": "6", "name": "Tomate triturado", "stock": 1, "unit": "latas", "icon": "🥫", "department": "despensa"},
]

NODE_SCRIPT = r"""
const fs = require("fs");
const [dataPath, mockPath, casesPath] = process.argv.slice(2);
globalThis.MENU_DATA = JSON.parse(fs.readFileSync(dataPath, "utf8"));
eval(fs.readFileSync(mockPath, "utf8"));
const { analyze, Context, summarize, checkPantry } = globalThis.MenuDemo._internals;
const cases = JSON.parse(fs.readFileSync(casesPath, "utf8"));
const recipes = cases.recipes;
const infos = {};
for (const r of recipes) infos[r.id] = analyze(r);
const out = { infos, weeks: [], changes: [], summary: null, check: null };
for (const c of cases.generate) {
  const ctx = new Context(recipes, infos, cases.settings, c.history, c.pantry, c.seed);
  out.weeks.push(ctx.generate(c.fixed).map((x) => (x ? x.id : null)));
}
for (const c of cases.changes) {
  const ctx = new Context(recipes, infos, cases.settings, {}, {}, c.seed);
  const [cand, restarted] = ctx.change(c.week, c.slot, c.rejected);
  out.changes.push([cand ? cand.id : null, restarted]);
}
const byId = new Map(recipes.map((r) => [r.id, r]));
out.summary = summarize(cases.slots, byId, infos, cases.settings, {});
out.check = checkPantry(cases.lines, cases.pantry_items, new Set(cases.in_cesta), {});
process.stdout.write(JSON.stringify(out));
"""


def _data() -> dict:
    out = subprocess.run(
        ["python3", str(ROOT / "tools" / "build_preview.py"), "--data"], capture_output=True, text=True, check=True
    )
    return json.loads(out.stdout)


def test_javascript_planner_matches_python(tmp_path) -> None:
    recipes = [{**r, "id": f"r{i}", "servings": 4} for i, r in enumerate(EXAMPLES)]
    infos = {r["id"]: analyze(r) for r in recipes}
    pantry = {r["id"]: (i % 5) / 4 for i, r in enumerate(recipes)}
    generate_cases = [
        {"seed": seed, "fixed": [None] * SLOTS, "history": {}, "pantry": {}} for seed in (1, 7, 42, 2026)
    ] + [
        {"seed": 5, "fixed": ["free", "r22"] + [None] * 12, "history": {"r0": 1, "r11": 2, "r17": 1}, "pantry": pantry},
    ]
    change_week = [r["id"] for r in recipes[:14]]
    change_cases = [{"seed": s, "week": change_week, "slot": s % 14, "rejected": [change_week[s % 14]]} for s in (3, 4, 9)]
    slots = [{"recipe_id": f"r{i}", "free": False} for i in range(14)]
    slots[5] = {"recipe_id": None, "free": True}
    lines = [
        {"name": "Lentejas", "qty": 600, "unit": "g", "recipe_id": "a", "recipe": "A", "day": 0, "meal": "lunch"},
        {"name": "Carne picada", "qty": 800, "unit": "g", "recipe_id": "b", "recipe": "B", "day": 1, "meal": "lunch"},
        {"name": "Patatas", "qty": 6, "unit": "ud", "recipe_id": "b", "recipe": "B", "day": 1, "meal": "lunch"},
        {"name": "Huevos", "qty": 4, "unit": "ud", "recipe_id": "c", "recipe": "C", "day": 2, "meal": "dinner"},
        {"name": "Salmón", "qty": 250, "unit": "g", "recipe_id": "c", "recipe": "C", "day": 2, "meal": "dinner"},
        {"name": "Tomate triturado", "qty": 700, "unit": "g", "recipe_id": "a", "recipe": "A", "day": 0, "meal": "lunch"},
        {"name": "Leche", "qty": 300, "unit": "ml", "recipe_id": "c", "recipe": "C", "day": 2, "meal": "dinner"},
        {"name": "Sal", "qty": None, "unit": "gusto", "recipe_id": "c", "recipe": "C", "day": 2, "meal": "dinner"},
        {"name": "Garbanzos cocidos", "qty": 500, "unit": "g", "recipe_id": "c", "recipe": "C", "day": 2, "meal": "dinner"},
    ]
    cases = {
        "recipes": recipes,
        "settings": SETTINGS,
        "generate": generate_cases,
        "changes": change_cases,
        "slots": slots,
        "lines": lines,
        "pantry_items": PANTRY,
        "in_cesta": ["lech"],
    }
    (tmp_path / "data.json").write_text(json.dumps(_data(), ensure_ascii=False), encoding="utf-8")
    (tmp_path / "cases.json").write_text(json.dumps(cases, ensure_ascii=False), encoding="utf-8")
    (tmp_path / "run.js").write_text(NODE_SCRIPT, encoding="utf-8")
    result = subprocess.run(
        [NODE, str(tmp_path / "run.js"), str(tmp_path / "data.json"), str(ROOT / "preview" / "mock-backend.js"), str(tmp_path / "cases.json")],
        capture_output=True,
        text=True,
        check=True,
    )
    js = json.loads(result.stdout)

    # Misma estimación nutricional
    for rid, info in infos.items():
        assert js["infos"][rid] == json.loads(json.dumps(info)), rid

    # Mismo menú con la misma semilla
    for case, js_week in zip(generate_cases, js["weeks"], strict=True):
        ctx = Context(recipes, infos, SETTINGS, case["history"], case["pantry"], case["seed"])
        assert [c.id if c else None for c in ctx.generate(case["fixed"])] == js_week, case["seed"]

    # Mismo CAMBIO
    for case, (js_id, js_restarted) in zip(change_cases, js["changes"], strict=True):
        ctx = Context(recipes, infos, SETTINGS, {}, {}, case["seed"])
        cand, restarted = ctx.change(case["week"], case["slot"], case["rejected"])
        assert (cand.id, restarted) == (js_id, js_restarted)

    # Mismo resumen y misma comprobación de la despensa
    summary = summarize(slots, {r["id"]: r for r in recipes}, infos, SETTINGS, {})
    assert js["summary"] == json.loads(json.dumps(summary))
    py_check = check(lines, PANTRY, {"lech"}, {})
    assert js["check"] == json.loads(json.dumps(py_check))
