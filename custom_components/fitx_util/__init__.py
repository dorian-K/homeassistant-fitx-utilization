"""The FitX Utilization integration."""
from __future__ import annotations
import logging

from aionanoleaf import ClientConnectionError
from .fitx import FitXApi

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DATA_COORDINATOR, DEFAULT_UPDATE_INTERVAL, DOMAIN

PLATFORMS: list[Platform] = [Platform.SENSOR]
_LOGGER = logging.getLogger(__name__)
# _LOGGER.setLevel("DEBUG")


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up FitX Utilization from a config entry."""

    hass.data.setdefault(DOMAIN, {})

    coordinator = FitXDataUpdateCoordinator(hass, entry=entry)

    if not await coordinator.async_login():
        return False

    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = {
        DATA_COORDINATOR: coordinator,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


class FitXDataUpdateCoordinator(DataUpdateCoordinator):
    """FitX Data Update Coordinator"""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.entry = entry
        self.hass = hass

        self._api = FitXApi(entry.data["studio_id"], entry.data["brand"])
        self.entry = entry
        self.disable_session = False

        super().__init__(
            hass, _LOGGER, name=DOMAIN, update_interval=DEFAULT_UPDATE_INTERVAL
        )

    async def async_login(self) -> bool:
        """Login to FitX"""
        try:
            await self._api.init()
        except ClientConnectionError:
            _LOGGER.exception()
            return False
        if (
            not self.disable_session
            and "session" in self.entry.data
            and len(self.entry.data["session"]) > 1
        ):
            _LOGGER.debug("setting session %s", {self.entry.data["session"]})
            self._api.set_session(self.entry.data["session"])
        else:
            try:
                await self._api.login(
                    self.entry.data["email"], self.entry.data["password"]
                )
            except ClientConnectionError:
                _LOGGER.exception()
                return False
        return True

    async def _async_update_data(self) -> dict:
        try:
            util = await self._api.get_utilv2()
        except ClientConnectionError as error:
            _LOGGER.debug("Trying to relogin to FitX", exc_info=1)
            self.disable_session = True
            if not await self.async_login():
                raise UpdateFailed(error) from error
            try:
                util = await self._api.get_utilv2()
            except ClientConnectionError as error2:
                raise UpdateFailed(error2) from error2
        return {"utilization": util}
