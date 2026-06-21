import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONCENTRATION_PARTS_PER_MILLION,
    PERCENTAGE,
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    UnitOfTemperature,
    UnitOfTime,
    UnitOfPressure,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import GGSDataCoordinator, GGSDevice
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

ENV_SENSOR_CONFIG = {
    "temp": {
        "name": "Temperature",
        "native_unit_of_measurement": UnitOfTemperature.CELSIUS,
        "device_class": SensorDeviceClass.TEMPERATURE,
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "humi": {
        "name": "Humidity",
        "native_unit_of_measurement": PERCENTAGE,
        "device_class": SensorDeviceClass.HUMIDITY,
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "vpd": {
        "name": "VPD",
        "native_unit_of_measurement": UnitOfPressure.KPA,
        "device_class": SensorDeviceClass.PRESSURE,
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "co2": {
        "name": "CO2",
        "native_unit_of_measurement": CONCENTRATION_PARTS_PER_MILLION,
        "device_class": SensorDeviceClass.CO2,
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "ppfd": {
        "name": "PPFD",
        "native_unit_of_measurement": "μmol/m2/s",
        "device_class": SensorDeviceClass.ILLUMINANCE,
        "state_class": SensorStateClass.MEASUREMENT,
    },
}

SOIL_SENSOR_CONFIG = {
    "tempSoil": {
        "name": "Temperature",
        "native_unit_of_measurement": UnitOfTemperature.CELSIUS,
        "device_class": SensorDeviceClass.TEMPERATURE,
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "humiSoil": {
        "name": "Moisture",
        "native_unit_of_measurement": PERCENTAGE,
        "device_class": SensorDeviceClass.MOISTURE,
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "ECSoil": {
        "name": "EC",
        "native_unit_of_measurement": "mS/cm",
        "device_class": SensorDeviceClass.CONDUCTIVITY,
        "state_class": SensorStateClass.MEASUREMENT,
    },
}

SYSTEM_SENSOR_CONFIG = {
    "wifi_rssi": {
        "name": "WiFi Signal",
        "native_unit_of_measurement": SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
        "device_class": SensorDeviceClass.SIGNAL_STRENGTH,
        "state_class": SensorStateClass.MEASUREMENT,
        "entity_category": EntityCategory.DIAGNOSTIC,
    },
    "upTime": {
        "name": "Uptime",
        "native_unit_of_measurement": UnitOfTime.SECONDS,
        "device_class": SensorDeviceClass.DURATION,
        "state_class": SensorStateClass.TOTAL_INCREASING,
        "entity_category": EntityCategory.DIAGNOSTIC,
    },
    "mem_free": {
        "name": "Free Memory",
        "native_unit_of_measurement": "MB",
        "state_class": SensorStateClass.MEASUREMENT,
        "entity_category": EntityCategory.DIAGNOSTIC,
    },
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: GGSDataCoordinator = hass.data[DOMAIN][entry.entry_id]

    new_entities = []

    for device in coordinator.get_all_devices():
        new_entities.extend(_create_env_sensors(device))
        new_entities.extend(_create_soil_sensors(device))
        new_entities.extend(_create_system_sensors(device))

    if new_entities:
        async_add_entities(new_entities)


def _create_env_sensors(device: GGSDevice) -> list:
    sensors = []
    for key, config in ENV_SENSOR_CONFIG.items():
        sensors.append(
            GGSEnvironmentSensor(device, key, config["name"], config)
        )
    return sensors


def _create_soil_sensors(device: GGSDevice) -> list:
    sensors = []
    soil_ids = list(device.soil_sensors.keys()) if device.soil_sensors else ["1", "2", "3", "4"]

    for soil_id in soil_ids:
        for key, config in SOIL_SENSOR_CONFIG.items():
            sensors.append(
                GGSSoilSensor(device, soil_id, key, config["name"], config)
            )
    return sensors


def _create_system_sensors(device: GGSDevice) -> list:
    sensors = []
    for key, config in SYSTEM_SENSOR_CONFIG.items():
        sensors.append(
            GGSSystemSensor(device, key, config["name"], config)
        )
    return sensors


class GGSBaseSensor(SensorEntity):
    def __init__(
        self,
        device: GGSDevice,
        sensor_key: str,
        name: str,
        config: dict,
    ):
        self.device = device
        self.sensor_key = sensor_key
        self._attr_name = name
        self._attr_unique_id = f"{device.unique_id}_{sensor_key}"
        self._attr_native_unit_of_measurement = config.get("native_unit_of_measurement")
        self._attr_device_class = config.get("device_class")
        self._attr_state_class = config.get("state_class")
        self._attr_entity_category = config.get("entity_category")
        self._attr_has_entity_name = True
        self._attr_should_poll = False

        self._attr_device_info = {
            "identifiers": {(DOMAIN, device.identifier)},
            "name": device.name,
            "manufacturer": "Spider Farmer",
            "model": device.device_type.upper(),
            "sw_version": device.firmware_version,
            "entry_type": DeviceEntryType.SERVICE,
        }

    @property
    def available(self) -> bool:
        return self.device.connected

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            "mac": self.device.mac,
            "device_type": self.device.device_type,
            "last_seen": self.device.last_seen.isoformat() if self.device.last_seen else None,
        }


class GGSEnvironmentSensor(GGSBaseSensor):
    def __init__(self, device: GGSDevice, sensor_key: str, name: str, config: dict):
        super().__init__(device, f"env_{sensor_key}", name, config)

    @property
    def native_value(self) -> float | None:
        value = self.device.environment.get(self.sensor_key)
        if value is None:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None


class GGSSoilSensor(GGSBaseSensor):
    def __init__(self, device: GGSDevice, soil_id: str, sensor_key: str, name: str, config: dict):
        self.soil_id = soil_id
        super().__init__(
            device,
            f"soil_{soil_id}_{sensor_key}",
            f"Soil {soil_id} {name}",
            config,
        )

    @property
    def native_value(self) -> float | None:
        sensor_data = self.device.soil_sensors.get(self.soil_id)
        if not sensor_data:
            return None
        value = sensor_data.get(self.sensor_key)
        if value is None:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    @property
    def available(self) -> bool:
        if not self.device.connected:
            return False
        sensor_data = self.device.soil_sensors.get(self.soil_id)
        if not sensor_data:
            return False
        value = sensor_data.get(self.sensor_key)
        if value is None:
            return False
        return True


class GGSSystemSensor(GGSBaseSensor):
    def __init__(self, device: GGSDevice, sensor_key: str, name: str, config: dict):
        super().__init__(device, f"sys_{sensor_key}", name, config)

    @property
    def native_value(self) -> float | int | str | None:
        value = self.device.system.get(self.sensor_key)
        if value is None:
            return None
        if self.sensor_key == "ver":
            return str(value)
        try:
            return float(value)
        except (ValueError, TypeError):
            return value
