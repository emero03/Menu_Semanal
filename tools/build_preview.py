"""Genera preview/menu-semanal-preview.html a partir del frontend y de las tablas reales.

Uso: python3 tools/build_preview.py
"""

import importlib.util
import json
from pathlib import Path
import sys
import types

ROOT = Path(__file__).resolve().parent.parent
COMPONENT = ROOT / "custom_components" / "menu_semanal"

# Se cargan los módulos sin Home Assistant: un paquete falso con solo lo que hace falta.
package = types.ModuleType("menu_semanal")
package.__path__ = [str(COMPONENT)]
sys.modules["menu_semanal"] = package


def load(name: str):
    spec = importlib.util.spec_from_file_location(f"menu_semanal.{name}", COMPONENT / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[f"menu_semanal.{name}"] = module
    spec.loader.exec_module(module)
    return module


catalog = load("catalog")
const = load("const")
nutrition = load("nutrition")
pantry = load("pantry")
examples = load("examples")

DEPARTMENTS = [
    {"id": "fruta_verdura", "color": "#43A047"}, {"id": "panaderia", "color": "#C9922E"},
    {"id": "carne", "color": "#E53935"}, {"id": "pescado", "color": "#1E88E5"},
    {"id": "charcuteria", "color": "#FB8C00"}, {"id": "lacteos", "color": "#F9C02D"},
    {"id": "despensa", "color": "#9E9D24"}, {"id": "desayuno", "color": "#EC407A"},
    {"id": "congelados", "color": "#00ACC1"}, {"id": "bebidas", "color": "#8E24AA"},
    {"id": "otros", "color": "#78909C"},
]

data = {
    "catalog": catalog.CATALOG,
    "foods": nutrition.foods_for_js(),
    "examples": examples.EXAMPLES,
    "categories": const.CATEGORIES,
    "packages": [list(p) for p in pantry.PACKAGES],
    "basics": sorted(nutrition.BASICS),
    "units": const.UNITS,
    "settings": const.DEFAULT_SETTINGS,
    "departments": DEPARTMENTS,
}


def build() -> str:
    html = (ROOT / "preview" / "template.html").read_text(encoding="utf-8")
    menu_js = (COMPONENT / "frontend" / "menu-semanal.js").read_text(encoding="utf-8")
    mock_js = (ROOT / "preview" / "mock-backend.js").read_text(encoding="utf-8")
    assert "</script" not in menu_js + mock_js
    dump = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    for marker, value in {"/*MENU_DATA*/": dump, "/*MOCK_JS*/": mock_js, "/*MENU_JS*/": menu_js}.items():
        assert html.count(marker) == 1, marker
        html = html.replace(marker, value)
    return html


def fragment(html: str) -> str:
    """La misma página sin <html>/<head>/<body>, para publicarla donde ya ponen ese esqueleto."""
    head, body = html.split("</head>", 1)
    head = head[head.index("<title>") :]
    body = body.replace("<body>", "", 1).replace("</body>", "").replace("</html>", "")
    return head + body


if __name__ == "__main__":
    out = ROOT / "preview" / "menu-semanal-preview.html"
    if len(sys.argv) > 1 and sys.argv[1] == "--data":
        print(json.dumps(data, ensure_ascii=False))
        sys.exit(0)
    if len(sys.argv) > 2 and sys.argv[1] == "--fragment":
        Path(sys.argv[2]).write_text(fragment(build()), encoding="utf-8")
        print(sys.argv[2])
        sys.exit(0)
    html = build()
    out.write_text(html, encoding="utf-8")
    print(f"{out} ({len(html) // 1024} KB)")
