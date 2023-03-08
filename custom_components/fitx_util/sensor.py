"""Sensor"""
import logging
from typing import Any
from .const import DATA_COORDINATOR, DOMAIN
from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ID, PERCENTAGE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

_LOGGER = logging.getLogger(__name__)
# _LOGGER.setLevel("DEBUG")


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Setup all entities"""
    coordinator: DataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id][
        DATA_COORDINATOR
    ]
    unique_id = entry.data[CONF_ID]
    entities = []

    entities.append(
        GymUtilizationSensor(
            coordinator,
            unique_id,
            "utilization",
            "Gym Utilization",
            PERCENTAGE,
            None,
            None,
            SensorStateClass.MEASUREMENT,
            True,
        )
    )

    async_add_entities(entities)


class GymUtilizationSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Gym util Sensor."""

    def __init__(
        self,
        coordinator,
        unique_id,
        sensor_type,
        name,
        unit,
        icon,
        device_class,
        state_class,
        enabled_default: bool = True,
    ) -> None:
        """Initialize a Utilization sensor."""
        super().__init__(coordinator)

        self._unique_id = unique_id
        self._type = sensor_type
        self._device_class = device_class
        self._state_class = state_class
        self._enabled_default = enabled_default

        self._attr_name = name
        self._attr_device_class = self._device_class
        self._attr_icon = icon
        self._attr_native_unit_of_measurement = unit
        self._attr_unique_id = f"{self._unique_id}_{self._type}"
        self._attr_state_class = state_class

    @property
    def native_value(self) -> None | int:
        """Return the state of the sensor."""
        if not self.coordinator.data or not self.coordinator.data["utilization"]:
            _LOGGER.debug("native value not found in coordinator!")
            return None

        for item in self.coordinator.data["utilization"]:
            if not item["current"]:
                continue

            # _LOGGER.debug("returning native value %d", item["percentage"])
            return item["percentage"]

        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return attributes for sensor."""
        if not self.coordinator.data:
            return {}

        attributes = {
            #    "last_synced": self.coordinator.data["lastSync"],
        }

        return attributes

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return {
            "identifiers": {(DOMAIN, self._unique_id)},
            "name": "Gym Utilization",
        }

    @property
    def entity_registry_enabled_default(self) -> bool:
        """Return if the entity should be enabled when first added to the entity registry."""
        return self._enabled_default

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return (
            super().available
            and self.coordinator.data
            and "utilization" in self.coordinator.data
        )
