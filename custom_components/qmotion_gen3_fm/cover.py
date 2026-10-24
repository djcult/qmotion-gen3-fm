"""Cover entities for one-way QMotion FM groups."""
from __future__ import annotations

from homeassistant.components.cover import CoverEntity, CoverEntityFeature, ATTR_POSITION
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.exceptions import HomeAssistantError

from .const import DOMAIN


async def async_setup_entry(hass, entry, async_add_entities):
    state = hass.data[DOMAIN][entry.entry_id]
    gateway = state["gateway"]
    async_add_entities(
        QMotionCover(gateway, group, entry.entry_id, entry.data["host"])
        for group in state["groups"]
    )


class QMotionCover(CoverEntity):
    """A group whose position cannot be read back from the one-way FM motor."""

    _attr_assumed_state = True
    _attr_supported_features = (
        CoverEntityFeature.OPEN | CoverEntityFeature.CLOSE | CoverEntityFeature.SET_POSITION
    )
    _attr_has_entity_name = True

    def __init__(self, gateway, group, entry_id: str, host: str) -> None:
        self._gateway = gateway
        self._channel = group.channel
        self._attr_name = group.name
        self._attr_unique_id = f"{entry_id}_{group.page.hex()}_{group.channel}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry_id)},
            name="QSync FM Gateway",
            manufacturer="QMotion",
            model="QSYNC433FM",
        )
        self._attr_available = True

    @property
    def current_cover_position(self):
        # We deliberately do not report guessed motor state: handheld remote
        # actions cannot be observed by this one-way RF gateway.
        return None

    @property
    def is_closed(self):
        return None

    async def _send(self, hass_position: int) -> None:
        # Home Assistant: 0=closed, 100=open. QSync: 0=open, 100=closed.
        qsync_position = 100 - hass_position
        try:
            await self.hass.async_add_executor_job(
                self._gateway.set_position, self._channel, qsync_position
            )
        except (OSError, ValueError) as err:
            raise HomeAssistantError(f"QSync command failed: {err}") from err

    async def async_open_cover(self, **kwargs):
        await self._send(100)

    async def async_close_cover(self, **kwargs):
        await self._send(0)

    async def async_set_cover_position(self, **kwargs):
        await self._send(kwargs[ATTR_POSITION])
