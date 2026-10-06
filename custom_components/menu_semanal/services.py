"""Acciones de Menú Semanal para automatizaciones y scripts."""

from __future__ import annotations

from datetime import timedelta
from typing import Any

import voluptuous as vol

from homeassistant.core import HomeAssistant, ServiceCall, ServiceResponse, SupportsResponse, callback
from homeassistant.exceptions import ServiceValidationError
import homeassistant.helpers.config_validation as cv

from .catalog import normalize
from .const import (
    ATTR_ADD_TO_CESTA,
    ATTR_DAY,
    ATTR_WEEK,
    DAY_NAMES,
    DAYS,
    DOMAIN,
    MEAL_NAMES,
    MEALS,
    SERVICE_CHECK,
    SERVICE_GENERATE,
    SERVICE_GET_MENU,
)
from .manager import MenuError, MenuManager, resolve_week, today, week_key, week_monday

GENERATE_SCHEMA = vol.Schema({vol.Optional(ATTR_WEEK, default="current"): cv.string})
CHECK_SCHEMA = vol.Schema(
    {vol.Optional(ATTR_WEEK, default="current"): cv.string, vol.Optional(ATTR_ADD_TO_CESTA, default=False): cv.boolean}
)
GET_MENU_SCHEMA = vol.Schema({vol.Optional(ATTR_WEEK): cv.string, vol.Optional(ATTR_DAY): cv.string})


def _manager(hass: HomeAssistant) -> MenuManager:
    manager: MenuManager | None = hass.data.get(DOMAIN)
    if manager is None:
        raise ServiceValidationError(translation_domain=DOMAIN, translation_key="not_loaded")
    return manager


def _week(value: str | None) -> str:
    try:
        return resolve_week(value)
    except MenuError as err:
        raise ServiceValidationError(str(err)) from err


def _day(value: str) -> tuple[str, int]:
    """"today"/"hoy", "tomorrow"/"mañana", un día de la semana o una fecha → (semana, día)."""
    text = normalize(value)
    now = today()
    if text in ("today", "hoy"):
        target = now
    elif text in ("tomorrow", "manana"):
        target = now + timedelta(days=1)
    else:
        names = [normalize(n) for n in DAY_NAMES]
        english = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        if text in names or text in english:
            index = names.index(text) if text in names else english.index(text)
            target = now + timedelta(days=(index - now.weekday()) % 7)
        else:
            try:
                target = now.fromisoformat(value.strip()[:10])
            except ValueError as err:
                raise ServiceValidationError(f"Día no válido: {value}") from err
    return week_key(target), target.weekday()


def _menu_response(manager: MenuManager, key: str, only_day: int | None = None) -> dict[str, Any]:
    snap = manager.week_snapshot(key)
    recipes = {r["id"]: r for r in manager.recipes}
    days = []
    for d in range(DAYS):
        if only_day is not None and d != only_day:
            continue
        entry: dict[str, Any] = {"day": DAY_NAMES[d], "date": (week_monday(key) + timedelta(days=d)).isoformat()}
        for m, meal in enumerate(MEALS):
            slot = snap["slots"][2 * d + m]
            recipe = recipes.get(slot.get("recipe_id") or "")
            entry[MEAL_NAMES[meal].lower()] = (
                "Libre" if slot.get("free") else (recipe["name"] if recipe else None)
            )
        entry["kcal"] = snap["summary"]["days"][d]["kcal"]
        days.append(entry)
    text = manager.day_text(key, only_day) if only_day is not None else manager.menu_text(key)
    return {"week": key, "days": days, "text": text}


@callback
def async_register_services(hass: HomeAssistant) -> None:
    """Registra las acciones menu_semanal.*"""

    async def generate(call: ServiceCall) -> ServiceResponse:
        manager = _manager(hass)
        key = _week(call.data.get(ATTR_WEEK))
        try:
            await manager.async_generate(key)
        except MenuError as err:
            raise ServiceValidationError(str(err)) from err
        return _menu_response(manager, key) if call.return_response else None

    async def check_ingredients(call: ServiceCall) -> ServiceResponse:
        manager = _manager(hass)
        key = _week(call.data.get(ATTR_WEEK))
        result = manager.check(key)
        missing = [r for r in result["items"] if r["status"] == "missing"]
        added: list[str] = []
        if call.data.get(ATTR_ADD_TO_CESTA) and missing:
            try:
                added = await manager.async_add_to_cesta(
                    [{"name": r["name"], "note": r["note"], "icon": r["icon"], "department": r["department"]} for r in missing]
                )
            except MenuError as err:
                raise ServiceValidationError(str(err)) from err
        lines = [f"{r['icon']} {r['name']}" + (f" ({r['note']})" if r["note"] else "") for r in missing]
        if not call.return_response:
            return None
        return {
            "week": key,
            "count": len(missing),
            "missing": [
                {"name": r["name"], "icon": r["icon"], "need": r["need_text"], "have": r["have_text"], "note": r["note"]}
                for r in missing
            ],
            "unsure": [r["name"] for r in result["items"] if r["status"] == "unsure"],
            "in_cesta": [r["name"] for r in result["items"] if r["status"] == "in_cesta"],
            "added": added,
            "text": "\n".join(lines),
        }

    @callback
    def get_menu(call: ServiceCall) -> ServiceResponse:
        manager = _manager(hass)
        if day := call.data.get(ATTR_DAY):
            key, index = _day(day)
            return _menu_response(manager, key, index)
        return _menu_response(manager, _week(call.data.get(ATTR_WEEK)))

    hass.services.async_register(
        DOMAIN, SERVICE_GENERATE, generate, schema=GENERATE_SCHEMA, supports_response=SupportsResponse.OPTIONAL
    )
    hass.services.async_register(
        DOMAIN, SERVICE_CHECK, check_ingredients, schema=CHECK_SCHEMA, supports_response=SupportsResponse.OPTIONAL
    )
    hass.services.async_register(
        DOMAIN, SERVICE_GET_MENU, get_menu, schema=GET_MENU_SCHEMA, supports_response=SupportsResponse.ONLY
    )
