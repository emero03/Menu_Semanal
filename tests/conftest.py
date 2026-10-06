"""Fixtures comunes.

Las pruebas de enlace con Despensa y Cesta necesitan una copia de cada una
(https://github.com/emero03/ha-despensa y https://github.com/emero03/ha-cesta).
Se buscan en ../ha-despensa y ../ha-cesta, o en las rutas de DESPENSA_REPO y CESTA_REPO;
si no están, esas pruebas se saltan.
"""

import os
from pathlib import Path
import sys

import pytest

from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component
from pytest_homeassistant_custom_component.common import MockConfigEntry

ROOT = Path(__file__).resolve().parent.parent
DESPENSA_REPO = Path(os.environ.get("DESPENSA_REPO", ROOT.parent / "ha-despensa"))
CESTA_REPO = Path(os.environ.get("CESTA_REPO", ROOT.parent / "ha-cesta"))
HAS_DESPENSA = (DESPENSA_REPO / "custom_components" / "despensa" / "manifest.json").is_file()
HAS_CESTA = (CESTA_REPO / "custom_components" / "cesta" / "manifest.json").is_file()
# custom_components es un paquete de espacio de nombres: se juntan los repositorios.
for repo, present in ((DESPENSA_REPO, HAS_DESPENSA), (CESTA_REPO, HAS_CESTA)):
    if present:
        sys.path.insert(0, str(repo))

from custom_components.menu_semanal.const import DOMAIN  # noqa: E402

pytest_plugins = "pytest_homeassistant_custom_component"


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Permite cargar custom_components en los tests."""
    yield


async def _add(hass: HomeAssistant, domain: str, title: str) -> MockConfigEntry:
    entry = MockConfigEntry(domain=domain, title=title, data={})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    return entry


@pytest.fixture
async def setup_menu(hass: HomeAssistant) -> MockConfigEntry:
    """Configura solo Menú Semanal."""
    hass.config.language = "es"
    await hass.config.async_set_time_zone("Europe/Madrid")
    assert await async_setup_component(hass, "http", {})
    entry = await _add(hass, DOMAIN, "Menú Semanal")
    await hass.async_block_till_done()
    return entry


@pytest.fixture
async def setup_all(hass: HomeAssistant) -> MockConfigEntry:
    """Configura Cesta, Despensa y Menú Semanal, como en casa."""
    if not (HAS_DESPENSA and HAS_CESTA):
        pytest.skip("Despensa o Cesta no están disponibles (define DESPENSA_REPO y CESTA_REPO)")
    hass.config.language = "es"
    await hass.config.async_set_time_zone("Europe/Madrid")
    assert await async_setup_component(hass, "http", {})
    await _add(hass, "cesta", "Cesta")
    await _add(hass, "despensa", "Despensa")
    entry = await _add(hass, DOMAIN, "Menú Semanal")
    await hass.async_block_till_done()
    return entry
