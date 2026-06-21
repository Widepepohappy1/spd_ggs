import asyncio
import json
import logging

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_HOST,
    CONF_PORT,
    Platform,
)
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.typing import ConfigType
from homeassistant.util.dt import utcnow

from .const import (
    DOMAIN,
    DATA_KEY,
    MQTT_TOPIC_PREFIX,
    MQTT_STATUS_TOPIC,
    MQTT_SENSORS_TOPIC,
    MQTT_SYSTEM_TOPIC,
    MQTT_CMD_TOPIC,
    DEVICE_NAME_MAP,
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    SERVICE_SEND_COMMAND,
    SERVICE_GET_CONFIG,
    SERVICE_SET_CONFIG,
    ATTR_DEVICE_TYPE,
    ATTR_MAC,
    ATTR_METHOD,
    ATTR_FIELD,
    ATTR_VALUE,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [
    Platform.SENSOR,
    Platform.LIGHT,
    Platform.SWITCH,
    Platform.BINARY_SENSOR,
]

_SEND_COMMAND_SCHEMA = vol.All(
    vol.Schema({
        vol.Required(ATTR_DEVICE_TYPE): str,
        vol.Required(ATTR_MAC): str,
        vol.Required(ATTR_METHOD): str,
        vol.Optional(ATTR_FIELD): str,
        vol.Optional(ATTR_VALUE): object,
    })
)

_GET_CONFIG_SCHEMA = vol.All(
    vol.Schema({
        vol.Required(ATTR_DEVICE_TYPE): str,
        vol.Required(ATTR_MAC): str,
        vol.Optional(ATTR_FIELD): str,
    })
)

_SET_CONFIG_SCHEMA = vol.All(
    vol.Schema({
        vol.Required(ATTR_DEVICE_TYPE): str,
        vol.Required(ATTR_MAC): str,
        vol.Required(ATTR_FIELD): str,
        vol.Required(ATTR_VALUE): object,
    })
)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    if entry.unique_id is None:
        hass.config_entries.async_update_entry(
            entry, unique_id=f"spiderfarmer_ggs_{entry.data[CONF_HOST]}_{entry.data[CONF_PORT]}"
        )

    host = entry.data[CONF_HOST]
    port = entry.data[CONF_PORT]
    scan_interval = entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)

    coordinator = GGSDataCoordinator(hass, host, port, scan_interval)
    await coordinator.async_setup()

    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(async_update_listener))

    _register_services(hass)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    await coordinator.async_teardown()

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
        if not hass.data[DOMAIN]:
            for service in [SERVICE_SEND_COMMAND, SERVICE_GET_CONFIG, SERVICE_SET_CONFIG]:
                if hass.services.has_service(DOMAIN, service):
                    hass.services.async_remove(DOMAIN, service)

    return unload_ok


async def async_update_listener(hass: HomeAssistant, entry: ConfigEntry):
    await hass.config_entries.async_reload(entry.entry_id)


def _register_services(hass: HomeAssistant):
    async def handle_send_command(call: ServiceCall):
        coordinator = None
        for data in hass.data.get(DOMAIN, {}).values():
            coordinator = data
            break

        if not coordinator:
            _LOGGER.error("No Spider Farmer GGS integration configured")
            return

        device_type = call.data[ATTR_DEVICE_TYPE]
        mac = call.data[ATTR_MAC]
        method = call.data[ATTR_METHOD]
        field = call.data.get(ATTR_FIELD)
        value = call.data.get(ATTR_VALUE)

        payload = {"method": method}
        if field is not None:
            payload["params"] = {"field": field}
            if value is not None:
                payload["params"]["value"] = value

        topic = MQTT_CMD_TOPIC.format(device_type=device_type, mac=mac)
        await coordinator.publish_command(topic, payload)
        _LOGGER.info("Sent command to %s: %s", topic, json.dumps(payload))

    async def handle_get_config(call: ServiceCall):
        coordinator = None
        for data in hass.data.get(DOMAIN, {}).values():
            coordinator = data
            break

        if not coordinator:
            _LOGGER.error("No Spider Farmer GGS integration configured")
            return

        device_type = call.data[ATTR_DEVICE_TYPE]
        mac = call.data[ATTR_MAC]
        field = call.data.get(ATTR_FIELD, "")

        payload = {"method": "getConfigField", "params": {"field": field}}
        topic = MQTT_CMD_TOPIC.format(device_type=device_type, mac=mac)
        await coordinator.publish_command(topic, payload)

    async def handle_set_config(call: ServiceCall):
        coordinator = None
        for data in hass.data.get(DOMAIN, {}).values():
            coordinator = data
            break

        if not coordinator:
            _LOGGER.error("No Spider Farmer GGS integration configured")
            return

        device_type = call.data[ATTR_DEVICE_TYPE]
        mac = call.data[ATTR_MAC]
        field = call.data[ATTR_FIELD]
        value = call.data[ATTR_VALUE]

        payload = {
            "method": "setConfigField",
            "params": {"field": field, "value": value}
        }
        topic = MQTT_CMD_TOPIC.format(device_type=device_type, mac=mac)
        await coordinator.publish_command(topic, payload)

    hass.services.async_register(
        DOMAIN,
        SERVICE_SEND_COMMAND,
        handle_send_command,
        schema=_SEND_COMMAND_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_GET_CONFIG,
        handle_get_config,
        schema=_GET_CONFIG_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_CONFIG,
        handle_set_config,
        schema=_SET_CONFIG_SCHEMA,
    )


class GGSDevice:
    def __init__(self, device_type: str, mac: str):
        self.device_type = device_type
        self.mac = mac.upper()
        self.name = DEVICE_NAME_MAP.get(device_type, f"Spider Farmer {device_type.upper()}")
        self.firmware_version = None
        self.last_seen = None
        self.connected = False

        self.environment = {}
        self.soil_sensors = {}
        self.outlets = {}
        self.lights = {}
        self.blower = None
        self.fan = None
        self.heater = None
        self.humidifier = None
        self.dehumidifier = None
        self.system = {}

    @property
    def unique_id(self) -> str:
        return f"spiderfarmer_ggs_{self.device_type}_{self.mac}"

    @property
    def identifier(self) -> str:
        return f"{self.device_type}_{self.mac}"


class GGSDataCoordinator:
    def __init__(self, hass: HomeAssistant, host: str, port: int, scan_interval: int):
        self.hass = hass
        self.host = host
        self.port = port
        self.scan_interval = scan_interval
        self.devices: dict[str, GGSDevice] = {}
        self.mqtt_available = False
        self._mqtt = None
        self._unsubscribe = None
        self._task = None

    async def async_setup(self):
        try:
            self._mqtt = await self.hass.helpers.integration.async_get_integration(self.hass, "mqtt")
            if self._mqtt:
                self.mqtt_available = True
                await self._subscribe_to_topics()
                _LOGGER.info("MQTT integration available, subscribing to GGS topics")
            else:
                _LOGGER.warning("MQTT integration not found, using polling mode")
                self._task = asyncio.create_task(self._poll_loop())
        except Exception as err:
            _LOGGER.error("Failed to setup MQTT: %s", err)

    async def async_teardown(self):
        if self._unsubscribe:
            self._unsubscribe()
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    async def _subscribe_to_topics(self):
        from homeassistant.components import mqtt

        async def _message_received(msg):
            topic = msg.topic
            payload = msg.payload

            await self._handle_message(topic, payload)

        topics = [
            (MQTT_STATUS_TOPIC, 0),
            (MQTT_SENSORS_TOPIC, 0),
            (MQTT_SYSTEM_TOPIC, 0),
        ]

        for topic, qos in topics:
            self._unsubscribe = await mqtt.async_subscribe(
                self.hass, topic, _message_received, qos
            )

        _LOGGER.info("Subscribed to MQTT topics: %s", [t[0] for t in topics])

    async def _handle_message(self, topic: str, payload: str):
        try:
            data = json.loads(payload)
        except json.JSONDecodeError:
            return

        parts = topic.split("/")
        if len(parts) < 4:
            return

        device_type = parts[1]
        mac = parts[2].upper()
        msg_type = parts[3]

        if mac not in self.devices:
            self.devices[mac] = GGSDevice(device_type, mac)
            _LOGGER.info("Discovered new device: %s (%s)", mac, device_type)

        device = self.devices[mac]
        device.last_seen = utcnow()
        device.connected = True

        nested_data = data.get("data", data)

        if msg_type == "status":
            await self._process_status(device, nested_data)
        elif msg_type == "sensors":
            await self._process_sensors(device, data)
        elif msg_type == "system":
            await self._process_system(device, nested_data)

    async def _process_status(self, device: GGSDevice, data: dict):
        if "sensor" in data:
            device.environment.update(data["sensor"])

        if "sensors" in data and isinstance(data["sensors"], list):
            for sensor in data["sensors"]:
                if sensor.get("id") != "avg":
                    device.soil_sensors[sensor.get("id", "unknown")] = sensor

        if "outlet" in data:
            for key, val in data["outlet"].items():
                if key.startswith("O") and isinstance(val, dict):
                    device.outlets[key] = val

        if "light" in data:
            device.lights["light"] = data["light"]
        if "light2" in data:
            device.lights["light2"] = data["light2"]

        if "blower" in data:
            device.blower = data["blower"]
        if "fan" in data:
            device.fan = data["fan"]
        if "heater" in data:
            device.heater = data["heater"]
        if "humidifier" in data:
            device.humidifier = data["humidifier"]
        if "dehumidifier" in data:
            device.dehumidifier = data["dehumidifier"]

        if "brightness" in data and "mode" in data:
            device.lights["light"] = {
                "modeType": data["mode"],
                "level": data["brightness"],
                "mOnOff": 1 if data["brightness"] > 0 else 0,
            }

    async def _process_sensors(self, device: GGSDevice, data: dict):
        if "sensor" in data:
            device.environment.update(data["sensor"])
        else:
            for key in ["temp", "humi", "vpd", "co2", "ppfd"]:
                if key in data:
                    device.environment[key] = data[key]

    async def _process_system(self, device: GGSDevice, data: dict):
        sys_data = data.get("sys", data)
        device.system = sys_data
        device.firmware_version = sys_data.get("ver")

        wifi = sys_data.get("wifi", {})
        if isinstance(wifi, dict):
            device.system["wifi_rssi"] = wifi.get("rssi")

    async def _poll_loop(self):
        while True:
            try:
                await asyncio.sleep(self.scan_interval)
                for mac, device in self.devices.items():
                    device.connected = False
            except asyncio.CancelledError:
                break
            except Exception as err:
                _LOGGER.error("Poll error: %s", err)

    async def publish_command(self, topic: str, payload: dict):
        if not self.mqtt_available:
            _LOGGER.error("Cannot publish: MQTT not available")
            return

        from homeassistant.components import mqtt

        await mqtt.async_publish(
            self.hass,
            topic,
            json.dumps(payload),
            qos=0,
            retain=False,
        )

    def get_device(self, mac: str) -> GGSDevice | None:
        return self.devices.get(mac.upper())

    def get_all_devices(self) -> list[GGSDevice]:
        return list(self.devices.values())
