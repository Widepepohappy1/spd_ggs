import logging

from homeassistant.components.light import (
    LightEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import GGSDataCoordinator, GGSDevice
from .const import DOMAIN, MQTT_CMD_TOPIC

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: GGSDataCoordinator = hass.data[DOMAIN][entry.entry_id]

    new_entities = []

    for device in coordinator.get_all_devices():
        for light_id in device.lights:
            new_entities.append(GGSLight(coordinator, device, light_id))

        if not device.lights:
            new_entities.append(GGSLight(coordinator, device, "light"))

    if new_entities:
        async_add_entities(new_entities)


class GGSLight(LightEntity):
    _attr_should_poll = False

    def __init__(
        self,
        coordinator: GGSDataCoordinator,
        device: GGSDevice,
        light_id: str,
    ):
        self.coordinator = coordinator
        self.device = device
        self.light_id = light_id

        name = "Light" if light_id == "light" else f"Light {light_id}"
        self._attr_name = name
        self._attr_unique_id = f"{device.unique_id}_light_{light_id}"
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
        light_data = self.device.lights.get(self.light_id)
        if not light_data:
            return False
        level = light_data.get("level", light_data.get("mLevel", 0))
        on_off = light_data.get("mOnOff", 0)
        return on_off == 1 or level > 0

    @property
    def brightness(self) -> int | None:
        light_data = self.device.lights.get(self.light_id)
        if not light_data:
            return None
        level = light_data.get("level", light_data.get("mLevel", 0))
        if level is None:
            return None
        try:
            level_float = float(level)
        except (ValueError, TypeError):
            return None
        if level_float > 100:
            return min(255, int(level_float))
        return min(255, int(level_float * 255 / 100))

    async def async_turn_on(self, **kwargs):
        brightness = kwargs.get("brightness")
        if brightness is None:
            light_data = self.device.lights.get(self.light_id)
            if light_data:
                brightness = self._level_to_brightness(
                    light_data.get("level", light_data.get("mLevel", 100))
                )
            if brightness is None:
                brightness = 255

        level = int(brightness * 100 / 255)

        await self._send_command({
            "method": "setConfigField",
            "params": {
                "field": f"{self.light_id}_mode",
                "value": "manual",
            },
        })
        await self._send_command({
            "method": "setConfigField",
            "params": {
                "field": f"{self.light_id}_level",
                "value": level,
            },
        })

        light_data = self.device.lights.setdefault(self.light_id, {})
        light_data["level"] = level
        light_data["mOnOff"] = 1
        light_data["modeType"] = 0

        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        await self._send_command({
            "method": "setConfigField",
            "params": {
                "field": f"{self.light_id}_level",
                "value": 0,
            },
        })

        light_data = self.device.lights.setdefault(self.light_id, {})
        light_data["level"] = 0
        light_data["mOnOff"] = 0

        self.async_write_ha_state()

    async def _send_command(self, payload: dict):
        topic = MQTT_CMD_TOPIC.format(
            device_type=self.device.device_type,
            mac=self.device.mac,
        )
        await self.coordinator.publish_command(topic, payload)
        _LOGGER.debug("Light command to %s: %s", self.light_id, payload)

    @staticmethod
    def _level_to_brightness(level) -> int:
        if level is None:
            return 255
        try:
            level_float = float(level)
        except (ValueError, TypeError):
            return 255
        if level_float > 100:
            return min(255, int(level_float))
        return min(255, int(level_float * 255 / 100))
