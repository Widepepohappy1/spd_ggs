import logging

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import GGSDataCoordinator, GGSDevice
from .const import DOMAIN, MQTT_CMD_TOPIC

_LOGGER = logging.getLogger(__name__)

CLIMATE_MODULES = [
    ("blower", "Blower"),
    ("fan", "Fan"),
    ("heater", "Heater"),
    ("humidifier", "Humidifier"),
    ("dehumidifier", "Dehumidifier"),
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: GGSDataCoordinator = hass.data[DOMAIN][entry.entry_id]

    new_entities = []

    for device in coordinator.get_all_devices():
        for outlet_key in device.outlets:
            new_entities.append(GGSOutletSwitch(coordinator, device, outlet_key))

        for module_key, module_name in CLIMATE_MODULES:
            new_entities.append(
                GGSClimateSwitch(coordinator, device, module_key, module_name)
            )

    if new_entities:
        async_add_entities(new_entities)


class GGSOutletSwitch(SwitchEntity):
    _attr_should_poll = False

    def __init__(
        self,
        coordinator: GGSDataCoordinator,
        device: GGSDevice,
        outlet_key: str,
    ):
        self.coordinator = coordinator
        self.device = device
        self.outlet_key = outlet_key
        self._attr_name = f"Outlet {outlet_key}"
        self._attr_unique_id = f"{device.unique_id}_outlet_{outlet_key}"
        self._attr_has_entity_name = True

        self._attr_device_info = {
            "identifiers": {(DOMAIN, device.identifier)},
            "name": device.name,
            "manufacturer": "Spider Farmer",
            "model": device.device_type.upper(),
            "sw_version": device.firmware_version,
        }

    @property
    def available(self) -> bool:
        return self.device.connected

    @property
    def is_on(self) -> bool:
        outlet_data = self.device.outlets.get(self.outlet_key)
        if not outlet_data:
            return False
        return outlet_data.get("mOnOff", 0) == 1

    async def async_turn_on(self, **kwargs):
        await self._send_command({
            "method": "setConfigField",
            "params": {
                "field": f"{self.outlet_key}_onoff",
                "value": 1,
            },
        })
        outlet_data = self.device.outlets.setdefault(self.outlet_key, {})
        outlet_data["mOnOff"] = 1
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        await self._send_command({
            "method": "setConfigField",
            "params": {
                "field": f"{self.outlet_key}_onoff",
                "value": 0,
            },
        })
        outlet_data = self.device.outlets.setdefault(self.outlet_key, {})
        outlet_data["mOnOff"] = 0
        self.async_write_ha_state()

    async def _send_command(self, payload: dict):
        topic = MQTT_CMD_TOPIC.format(
            device_type=self.device.device_type,
            mac=self.device.mac,
        )
        await self.coordinator.publish_command(topic, payload)


class GGSClimateSwitch(SwitchEntity):
    _attr_should_poll = False
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(
        self,
        coordinator: GGSDataCoordinator,
        device: GGSDevice,
        module_key: str,
        module_name: str,
    ):
        self.coordinator = coordinator
        self.device = device
        self.module_key = module_key
        self._attr_name = module_name
        self._attr_unique_id = f"{device.unique_id}_{module_key}"
        self._attr_has_entity_name = True

        self._attr_device_info = {
            "identifiers": {(DOMAIN, device.identifier)},
            "name": device.name,
            "manufacturer": "Spider Farmer",
            "model": device.device_type.upper(),
            "sw_version": device.firmware_version,
        }

    @property
    def available(self) -> bool:
        return self.device.connected

    @property
    def is_on(self) -> bool:
        module_data = getattr(self.device, self.module_key)
        if not module_data:
            return False
        return module_data.get("mOnOff", 0) == 1

    async def async_turn_on(self, **kwargs):
        await self._send_command({
            "method": "setConfigField",
            "params": {
                "field": f"{self.module_key}_onoff",
                "value": 1,
            },
        })
        module_data = getattr(self.device, self.module_key) or {}
        module_data["mOnOff"] = 1
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        await self._send_command({
            "method": "setConfigField",
            "params": {
                "field": f"{self.module_key}_onoff",
                "value": 0,
            },
        })
        module_data = getattr(self.device, self.module_key) or {}
        module_data["mOnOff"] = 0
        self.async_write_ha_state()

    async def _send_command(self, payload: dict):
        topic = MQTT_CMD_TOPIC.format(
            device_type=self.device.device_type,
            mac=self.device.mac,
        )
        await self.coordinator.publish_command(topic, payload)
