"""Puente con Despensa (https://github.com/emero03/ha-despensa) y Cesta (https://github.com/emero03/ha-cesta).

No modifica ninguna de las dos:

- De la Despensa lee el inventario (nombre, stock, unidad, icono y balda) a través de su
  gestor, el mismo que usan su panel y su sensor, y se entera de cada cambio.
- De la Cesta lee qué hay ya en la lista, y para añadir usa su acción pública
  `cesta.add_item` con un detalle tipo "2 paquetes", que la Despensa entiende al
  marcarlo como comprado (suma 2).
"""

from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.const import EVENT_COMPONENT_LOADED
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers.event import async_track_time_interval

from .catalog import _stems
from .const import CESTA_DOMAIN, DESPENSA_DOMAIN

_LOGGER = logging.getLogger(__name__)

CHECK_INTERVAL = timedelta(seconds=30)


def _manager_with_items(obj: Any) -> bool:
    data = getattr(obj, "data", None)
    return (
        obj is not None
        and callable(getattr(obj, "async_add_listener", None))
        and isinstance(data, dict)
        and isinstance(data.get("items"), list)
    )


class Siblings:
    """Mantiene el enlace con la Despensa y la Cesta (si están instaladas)."""

    def __init__(self, hass: HomeAssistant, manager: Any) -> None:
        self.hass = hass
        self.manager = manager
        self._despensa: Any = None
        self._cesta: Any = None
        self._unsub_despensa: Any = None
        self._unsub_cesta: Any = None
        self._unsubs: list[Any] = []
        self._cesta_service = False

    # ------------------------------------------------------------ ciclo de vida
    @callback
    def async_start(self) -> None:
        self._unsubs.append(async_track_time_interval(self.hass, self._tick, CHECK_INTERVAL))
        self._unsubs.append(self.hass.bus.async_listen(EVENT_COMPONENT_LOADED, self._on_loaded))
        self._attach()

    @callback
    def async_stop(self) -> None:
        for unsub in self._unsubs:
            unsub()
        self._unsubs.clear()
        self._detach_despensa()
        self._detach_cesta()

    @callback
    def _on_loaded(self, event: Event) -> None:
        if event.data.get("component") in (DESPENSA_DOMAIN, CESTA_DOMAIN):
            self._attach()

    @callback
    def _tick(self, _now: Any = None) -> None:
        self._attach()

    @callback
    def _attach(self) -> None:
        """Se engancha (o se vuelve a enganchar si se han recargado) a la Despensa y la Cesta."""
        changed = False
        despensa = self.hass.data.get(DESPENSA_DOMAIN)
        if not _manager_with_items(despensa):
            despensa = None
        if despensa is not self._despensa:
            self._detach_despensa()
            if despensa is not None:
                self._despensa = despensa
                self._unsub_despensa = despensa.async_add_listener(self._on_change)
                _LOGGER.debug("Conectado con Despensa")
            changed = True

        cesta = self.hass.data.get(CESTA_DOMAIN)
        if not _manager_with_items(cesta):
            cesta = None
        if cesta is not self._cesta:
            self._detach_cesta()
            if cesta is not None:
                self._cesta = cesta
                self._unsub_cesta = cesta.async_add_listener(self._on_change)
                _LOGGER.debug("Conectado con Cesta")
            changed = True

        service = self.hass.services.has_service(CESTA_DOMAIN, "add_item")
        if service != self._cesta_service:
            self._cesta_service = service
            changed = True
        if changed:
            self.manager.siblings_changed()

    @callback
    def _detach_despensa(self) -> None:
        if self._unsub_despensa is not None:
            self._unsub_despensa()
        self._unsub_despensa = None
        self._despensa = None

    @callback
    def _detach_cesta(self) -> None:
        if self._unsub_cesta is not None:
            self._unsub_cesta()
        self._unsub_cesta = None
        self._cesta = None

    @callback
    def _on_change(self) -> None:
        self.manager.siblings_changed()

    # ------------------------------------------------------------------ lectura
    def despensa_items(self) -> list[dict[str, Any]] | None:
        """Productos de la Despensa, o None si no está instalada."""
        if self._despensa is None:
            return None
        items = []
        for item in self._despensa.data.get("items", []):
            if not isinstance(item, dict) or not item.get("name"):
                continue
            items.append(
                {
                    "id": str(item.get("id") or item["name"]),
                    "name": item["name"],
                    "icon": item.get("icon") or "",
                    "unit": item.get("unit") or "",
                    "stock": item.get("stock") or 0,
                    "department": item.get("department") or "otros",
                }
            )
        return items

    @property
    def cesta_available(self) -> bool:
        return self.hass.services.has_service(CESTA_DOMAIN, "add_item")

    def cesta_names(self) -> set[str]:
        """Lo que ya está en la lista de la Cesta (nombres normalizados)."""
        if self._cesta is None:
            return set()
        return {" ".join(_stems(i.get("name", ""))) for i in self._cesta.data.get("items", []) if isinstance(i, dict)}

    # ----------------------------------------------------------------- escritura
    async def async_add_to_cesta(self, entries: list[dict[str, Any]]) -> list[str]:
        """Añade a la lista de la Cesta. Devuelve los nombres añadidos (sin los que ya estaban)."""
        present = self.cesta_names()
        added: list[str] = []
        for entry in entries:
            name = str(entry.get("name") or "").strip()
            if not name:
                continue
            key = " ".join(_stems(name))
            if key in present:
                continue
            data: dict[str, Any] = {"name": name}
            for field in ("note", "icon", "department"):
                if entry.get(field):
                    data[field] = str(entry[field])
            await self.hass.services.async_call(CESTA_DOMAIN, "add_item", data, blocking=True)
            present.add(key)
            added.append(name)
        return added
