"""IP-address setup flow for QSYNC433FM."""
from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback

from .const import DOMAIN
from .vendor.gateway import Gateway


class QMotionConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Configure a QSYNC433FM gateway."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            host = user_input["host"].strip()
            await self.async_set_unique_id(host.lower())
            self._abort_if_unique_id_configured()
            try:
                await self.hass.async_add_executor_job(Gateway(host).list_groups)
            except (OSError, ValueError):
                errors["base"] = "cannot_connect"
            else:
                return self.async_create_entry(title=f"QSync FM ({host})", data={"host": host})

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required("host"): str}),
            errors=errors,
        )
