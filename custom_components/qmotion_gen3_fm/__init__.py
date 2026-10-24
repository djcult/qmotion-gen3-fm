"""QMotion QSync FM local integration."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import DOMAIN
from .vendor.gateway import Gateway

PLATFORMS = ["cover"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    gateway = Gateway(entry.data["host"])
    try:
        groups = await hass.async_add_executor_job(gateway.list_groups)
    except (OSError, ValueError) as err:
        raise ConfigEntryNotReady(f"Could not read QSync groups: {err}") from err

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "gateway": gateway,
        "groups": groups,
    }
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    result = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if result:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return result
