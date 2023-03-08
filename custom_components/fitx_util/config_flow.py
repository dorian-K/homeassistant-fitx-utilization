"""Config flow for FitX Utilization integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from .fitx import FitXApi
from homeassistant.const import CONF_ID
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)
# _LOGGER.setLevel("DEBUG")

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Optional("brand", default="fitx"): str,
        vol.Required("studio_id"): str,
        vol.Required("email"): str,
        vol.Required("password"): str,
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """
    api = FitXApi(data["studio_id"], data["brand"])
    try:
        await api.init()
    except Exception as exc:
        await api.close()
        _LOGGER.debug("api.init failed", exc_info=1)

        raise CannotConnect() from exc
    try:
        await api.login(data["email"], data["password"])
    except Exception as exc:
        await api.close()
        _LOGGER.debug("api.login failed", exc_info=1)

        raise InvalidAuth() from exc
    await api.close()
    # Return info that you want to store in the config entry.
    uid = data["brand"] + ":" + data["studio_id"] + ":" + data["email"]
    # api_session = api.get_session()
    # _LOGGER.debug(f"{api_session.coded_value}")
    return {
        "title": data["brand"] + "(" + data["email"] + ")",
        CONF_ID: uid,
        "session": api.get_session().value,
        **data,
    }


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for FitX Utilization."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(info[CONF_ID])
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title=info["title"], data=info)

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
