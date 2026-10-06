"""API websocket de Menú Semanal (la usan el panel y la tarjeta)."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from functools import wraps
from typing import Any

import voluptuous as vol

from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant, callback

from .catalog import CATALOG
from .const import CATEGORY_IDS, DOMAIN, MAX_INGREDIENTS, SLOTS, UNITS
from .manager import MenuError, MenuManager
from .nutrition import FOODS

_WEEK = vol.All(str, vol.Match(r"^\d{4}-W\d{2}$"))
_SLOT = vol.All(vol.Coerce(int), vol.Range(min=0, max=SLOTS - 1))
_INGREDIENT = vol.Schema(
    {
        vol.Required("name"): vol.All(str, vol.Length(max=80)),
        vol.Optional("qty"): vol.Any(None, vol.Coerce(float), str),
        vol.Optional("unit"): vol.In(list(UNITS)),
    },
    extra=vol.REMOVE_EXTRA,
)
# "id" es el número del mensaje websocket: la receta va en "recipe_id"
_RECIPE = {
    vol.Optional("recipe_id"): vol.Any(None, str),
    vol.Optional("name"): vol.All(str, vol.Length(max=120)),
    vol.Optional("icon"): vol.All(str, vol.Length(max=16)),
    vol.Optional("meals"): [vol.In(["lunch", "dinner"])],
    vol.Optional("category"): vol.Any(None, vol.In(list(CATEGORY_IDS))),
    vol.Optional("rating"): vol.All(vol.Coerce(int), vol.Range(min=1, max=5)),
    vol.Optional("servings"): vol.All(vol.Coerce(int), vol.Range(min=1, max=20)),
    vol.Optional("ingredients"): vol.All([_INGREDIENT], vol.Length(max=MAX_INGREDIENTS)),
    vol.Optional("base"): vol.Any(None, vol.All(str, vol.Length(max=60))),
    vol.Optional("kcal"): vol.Any(None, vol.Coerce(float), str),
    vol.Optional("notes"): vol.Any(None, vol.All(str, vol.Length(max=4000))),
}


def _manager(hass: HomeAssistant) -> MenuManager | None:
    return hass.data.get(DOMAIN)


def _with_manager(
    func: Callable[[HomeAssistant, websocket_api.ActiveConnection, dict[str, Any], MenuManager], None],
) -> Callable[[HomeAssistant, websocket_api.ActiveConnection, dict[str, Any]], None]:
    """Inyecta el gestor y convierte los errores en respuestas websocket."""

    @wraps(func)
    def wrapper(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
        manager = _manager(hass)
        if manager is None:
            connection.send_error(msg["id"], "not_loaded", "Menú Semanal no está configurado")
            return
        try:
            func(hass, connection, msg, manager)
        except MenuError as err:
            connection.send_error(msg["id"], err.code, str(err))

    return wrapper


def _with_manager_async(
    func: Callable[[HomeAssistant, websocket_api.ActiveConnection, dict[str, Any], MenuManager], Awaitable[None]],
) -> Callable[[HomeAssistant, websocket_api.ActiveConnection, dict[str, Any]], Awaitable[None]]:
    @wraps(func)
    async def wrapper(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
        manager = _manager(hass)
        if manager is None:
            connection.send_error(msg["id"], "not_loaded", "Menú Semanal no está configurado")
            return
        try:
            await func(hass, connection, msg, manager)
        except MenuError as err:
            connection.send_error(msg["id"], err.code, str(err))

    return wrapper


@callback
def async_register_websocket_api(hass: HomeAssistant) -> None:
    for command in (
        ws_subscribe,
        ws_catalog,
        ws_recipe_save,
        ws_recipe_delete,
        ws_recipe_restore,
        ws_recipe_estimate,
        ws_examples,
        ws_generate,
        ws_change,
        ws_slot_set,
        ws_slot_lock,
        ws_week_restore,
        ws_week_clear,
        ws_check,
        ws_cesta_add,
        ws_settings,
        ws_color,
        ws_equivalence,
    ):
        websocket_api.async_register_command(hass, command)


@websocket_api.websocket_command({vol.Required("type"): "menu_semanal/subscribe"})
@callback
@_with_manager
def ws_subscribe(hass, connection, msg, manager: MenuManager) -> None:
    """Envía el estado completo ahora y cada vez que cambie."""
    msg_id = msg["id"]

    @callback
    def forward() -> None:
        connection.send_message(websocket_api.event_message(msg_id, manager.snapshot()))

    connection.subscriptions[msg_id] = manager.async_add_listener(forward)
    connection.send_result(msg_id)
    forward()


@websocket_api.websocket_command({vol.Required("type"): "menu_semanal/catalog"})
@callback
def ws_catalog(hass, connection, msg) -> None:
    """Sugerencias de ingredientes: el catálogo de Cesta/Despensa y la tabla de alimentos."""
    foods = [{"name": e[0][0], "group": e[5]} for e in FOODS]
    connection.send_result(msg["id"], {"catalog": CATALOG, "foods": foods, "units": UNITS})


@websocket_api.websocket_command({vol.Required("type"): "menu_semanal/recipe/save", **_RECIPE})
@callback
@_with_manager
def ws_recipe_save(hass, connection, msg, manager: MenuManager) -> None:
    payload = {k: v for k, v in msg.items() if k not in ("type", "id", "recipe_id")}
    if msg.get("recipe_id"):
        payload["id"] = msg["recipe_id"]
    recipe = manager.save_recipe(payload)
    connection.send_result(msg["id"], {"recipe": recipe, "info": manager.info(recipe["id"])})


@websocket_api.websocket_command({vol.Required("type"): "menu_semanal/recipe/delete", vol.Required("recipe_id"): str})
@callback
@_with_manager
def ws_recipe_delete(hass, connection, msg, manager: MenuManager) -> None:
    connection.send_result(msg["id"], {"recipe": manager.delete_recipe(msg["recipe_id"])})


@websocket_api.websocket_command({vol.Required("type"): "menu_semanal/recipe/restore", vol.Required("recipe_id"): str})
@callback
@_with_manager
def ws_recipe_restore(hass, connection, msg, manager: MenuManager) -> None:
    connection.send_result(msg["id"], {"recipe": manager.restore_recipe(msg["recipe_id"])})


@websocket_api.websocket_command({vol.Required("type"): "menu_semanal/recipe/estimate", **_RECIPE})
@callback
@_with_manager
def ws_recipe_estimate(hass, connection, msg, manager: MenuManager) -> None:
    connection.send_result(msg["id"], manager.estimate(msg))


@websocket_api.websocket_command({vol.Required("type"): "menu_semanal/recipes/examples"})
@callback
@_with_manager
def ws_examples(hass, connection, msg, manager: MenuManager) -> None:
    connection.send_result(msg["id"], {"added": manager.load_examples()})


@websocket_api.websocket_command(
    {vol.Required("type"): "menu_semanal/week/generate", vol.Required("week"): _WEEK, vol.Optional("seed"): int}
)
@websocket_api.async_response
@_with_manager_async
async def ws_generate(hass, connection, msg, manager: MenuManager) -> None:
    connection.send_result(msg["id"], await manager.async_generate(msg["week"], msg.get("seed")))


@websocket_api.websocket_command(
    {vol.Required("type"): "menu_semanal/slot/change", vol.Required("week"): _WEEK, vol.Required("slot"): _SLOT}
)
@websocket_api.async_response
@_with_manager_async
async def ws_change(hass, connection, msg, manager: MenuManager) -> None:
    connection.send_result(msg["id"], await manager.async_change(msg["week"], msg["slot"]))


@websocket_api.websocket_command(
    {
        vol.Required("type"): "menu_semanal/slot/set",
        vol.Required("week"): _WEEK,
        vol.Required("slot"): _SLOT,
        vol.Optional("recipe_id"): vol.Any(None, str),
        vol.Optional("free", default=False): bool,
    }
)
@callback
@_with_manager
def ws_slot_set(hass, connection, msg, manager: MenuManager) -> None:
    previous = manager.set_slot(msg["week"], msg["slot"], msg.get("recipe_id"), msg["free"])
    connection.send_result(msg["id"], {"previous": previous})


@websocket_api.websocket_command(
    {
        vol.Required("type"): "menu_semanal/slot/lock",
        vol.Required("week"): _WEEK,
        vol.Required("slot"): _SLOT,
        vol.Required("locked"): bool,
    }
)
@callback
@_with_manager
def ws_slot_lock(hass, connection, msg, manager: MenuManager) -> None:
    manager.lock_slot(msg["week"], msg["slot"], msg["locked"])
    connection.send_result(msg["id"])


@websocket_api.websocket_command(
    {
        vol.Required("type"): "menu_semanal/week/restore",
        vol.Required("week"): _WEEK,
        vol.Required("slots"): [dict],
    }
)
@callback
@_with_manager
def ws_week_restore(hass, connection, msg, manager: MenuManager) -> None:
    manager.restore_week(msg["week"], msg["slots"])
    connection.send_result(msg["id"])


@websocket_api.websocket_command({vol.Required("type"): "menu_semanal/week/clear", vol.Required("week"): _WEEK})
@callback
@_with_manager
def ws_week_clear(hass, connection, msg, manager: MenuManager) -> None:
    connection.send_result(msg["id"], {"previous": manager.clear_week(msg["week"])})


@websocket_api.websocket_command({vol.Required("type"): "menu_semanal/check", vol.Required("week"): _WEEK})
@callback
@_with_manager
def ws_check(hass, connection, msg, manager: MenuManager) -> None:
    connection.send_result(msg["id"], manager.check(msg["week"]))


@websocket_api.websocket_command(
    {
        vol.Required("type"): "menu_semanal/cesta/add",
        vol.Required("items"): [
            vol.Schema(
                {
                    vol.Required("name"): vol.All(str, vol.Length(min=1, max=120)),
                    vol.Optional("note"): vol.All(str, vol.Length(max=60)),
                    vol.Optional("icon"): vol.All(str, vol.Length(max=16)),
                    vol.Optional("department"): vol.All(str, vol.Length(max=60)),
                },
                extra=vol.REMOVE_EXTRA,
            )
        ],
    }
)
@websocket_api.async_response
@_with_manager_async
async def ws_cesta_add(hass, connection, msg, manager: MenuManager) -> None:
    connection.send_result(msg["id"], {"added": await manager.async_add_to_cesta(msg["items"])})


@websocket_api.websocket_command(
    {
        vol.Required("type"): "menu_semanal/settings/set",
        vol.Optional("people"): vol.All(vol.Coerce(int), vol.Range(min=1, max=12)),
        vol.Optional("kcal_day"): vol.All(vol.Coerce(int), vol.Range(min=1000, max=4500)),
        vol.Optional("batch"): bool,
        vol.Optional("prefer_pantry"): bool,
    }
)
@callback
@_with_manager
def ws_settings(hass, connection, msg, manager: MenuManager) -> None:
    manager.set_settings(**{k: v for k, v in msg.items() if k not in ("type", "id")})
    connection.send_result(msg["id"])


@websocket_api.websocket_command(
    {
        vol.Required("type"): "menu_semanal/category/color",
        vol.Required("category"): vol.In(list(CATEGORY_IDS)),
        vol.Optional("color"): vol.Any(None, str),
    }
)
@callback
@_with_manager
def ws_color(hass, connection, msg, manager: MenuManager) -> None:
    manager.set_color(msg["category"], msg.get("color"))
    connection.send_result(msg["id"])


@websocket_api.websocket_command(
    {
        vol.Required("type"): "menu_semanal/equivalence/set",
        vol.Required("name"): vol.All(str, vol.Length(min=1, max=120)),
        vol.Optional("grams"): vol.Any(None, vol.All(vol.Coerce(float), vol.Range(min=0, max=100000))),
        vol.Optional("volume", default=False): bool,
    }
)
@callback
@_with_manager
def ws_equivalence(hass, connection, msg, manager: MenuManager) -> None:
    manager.set_equivalence(msg["name"], msg.get("grams"), msg["volume"])
    connection.send_result(msg["id"])
