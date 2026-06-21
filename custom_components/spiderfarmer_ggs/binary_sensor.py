import logging

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import GGSDataCoordinator, GGSDevice
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: GGSDataCoordinator = hass.data[DOMAIN][entry.entry_id]

    new_entities = []

    for device in coordinator.get_all_devices():
        new_entities.append(
            GGSConnectivitySensor(coordinator, device)
        )

    if new_entities:
        async_add_entities(new_entities)


class GGSConnectivitySensor(BinarySensorEntity):
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_should_poll = False

    def __init__(
        self,
        coordinator: GGSDataCoordinator,
        device: GGSDevice,
    ):
        self.coordinator = coordinator
        self.device = device
        self._attr_name = "Connectivity"
        self._attr_unique_id = f"{device.unique_id}_connectivity"
        self._attr_has_entity_name = True

        self._attr_device_info = {
            "identifiers": {(DOMAIN, device.identifier)},
            "name": device.name,
            "manufacturer": "Spider Farmer",
            "model": device.device_type.upper(),
            "sw_version": device.firmware_version,
        }

    @property
    def is_on(self) -> bool:
        return self.device.connected
