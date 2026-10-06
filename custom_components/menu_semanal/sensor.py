"""Sensores "Comida de hoy" y "Cena de hoy": el plato que toca, para paneles y avisos."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_time_change

from .const import DOMAIN, MEAL_NAMES, NAME, VERSION
from .manager import MenuManager


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    manager: MenuManager = hass.data[DOMAIN]
    async_add_entities([MealTodaySensor(manager, entry, meal) for meal in ("lunch", "dinner")])


class MealTodaySensor(SensorEntity):
    """El plato de hoy (comida o cena)."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, manager: MenuManager, entry: ConfigEntry, meal: str) -> None:
        self._manager = manager
        self._meal = meal
        self._attr_name = f"{MEAL_NAMES[meal]} de hoy"
        self._attr_icon = "mdi:silverware-fork-knife" if meal == "lunch" else "mdi:weather-night"
        self._attr_unique_id = f"{entry.entry_id}_{meal}_today"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=NAME,
            manufacturer=NAME,
            model="Planificador de menús",
            sw_version=VERSION,
            entry_type=DeviceEntryType.SERVICE,
        )

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(self._manager.async_add_listener(self._handle_change))
        # A medianoche cambia el día
        self.async_on_remove(async_track_time_change(self.hass, self._midnight, hour=0, minute=0, second=5))

    @callback
    def _handle_change(self) -> None:
        self.async_write_ha_state()

    @callback
    def _midnight(self, _now: Any) -> None:
        self.async_write_ha_state()

    @property
    def native_value(self) -> str:
        recipe, slot = self._manager.meal_today(self._meal)
        if slot.get("free"):
            return "Libre"
        if recipe is None:
            return "Sin planificar"
        return recipe["name"]

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        recipe, slot = self._manager.meal_today(self._meal)
        if recipe is None:
            return {"libre": bool(slot.get("free"))}
        info = self._manager.info(recipe["id"])
        people = int(self._manager.settings.get("people") or 2)
        factor = people / max(1, int(recipe.get("servings") or 1))
        ingredients = []
        for ing in recipe["ingredients"]:
            if ing.get("unit") == "gusto" or ing.get("qty") is None:
                ingredients.append(f"{ing['name']} (al gusto)")
            else:
                qty = round(float(ing["qty"]) * factor, 1)
                qty_text = str(int(qty)) if qty == int(qty) else str(qty).replace(".", ",")
                ingredients.append(f"{ing['name']}: {qty_text} {ing['unit']}")
        return {
            "icono": recipe["icon"],
            "tipo": recipe["category"],
            "valoracion": recipe["rating"],
            "kcal_por_racion": info.get("kcal"),
            "comensales": people,
            "ingredientes": ingredients,
            "receta_id": recipe["id"],
            "fijado": bool(slot.get("locked")),
        }
