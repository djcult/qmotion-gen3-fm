"""Cover entities for one-way QMotion FM groups."""
from __future__ import annotations

from homeassistant.components.cover import CoverEntity, CoverEntityFeature, ATTR_POSITION
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.exceptions import HomeAssistantError

from .const import DOMAIN
from .position import ha_to_qsync, qsync_to_ha


async def async_setup_entry(hass, entry, async_add_entities):
    state = hass.data[DOMAIN][entry.entry_id]
    gateway = state["gateway"]
    async_add_entities(
        QMotionCover(gateway, group, entry.entry_id, entry.data["host"])
        for group in state["groups"]
    )


class QMotionCover(CoverEntity):
    """A cover reporting last commanded position, never physical motor feedback."""

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
        # Byte 30 in the 60-byte FM record is the gateway's stored command
        # position. It may be stale if the blind was moved using the remote.
        self._last_commanded_position = qsync_to_ha(group.raw[30])
        self._position_source = (
            "gateway_record" if self._last_commanded_position is not None else "unknown"
        )

    @property
    def current_cover_position(self):
        return self._last_commanded_position

    @property
    def is_closed(self):
        if self._last_commanded_position is None:
            return None
        return self._last_commanded_position == 0

    @property
    def extra_state_attributes(self):
        return {"position_source": self._position_source}

    async def _send(self, hass_position: int) -> None:
        qsync_position = ha_to_qsync(hass_position)
        try:
            await self.hass.async_add_executor_job(
                self._gateway.set_position, self._channel, qsync_position
            )
        except (OSError, ValueError) as err:
            raise HomeAssistantError(f"QSync command failed: {err}") from err
        # Transport completion is not an acknowledgement from the FM motor.
        self._last_commanded_position = hass_position
        self._position_source = "home_assistant_command"
        self.async_write_ha_state()

    async def async_open_cover(self, **kwargs):
        await self._send(100)

    async def async_close_cover(self, **kwargs):
        await self._send(0)

    async def async_set_cover_position(self, **kwargs):
        await self._send(kwargs[ATTR_POSITION])
