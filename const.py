DOMAIN = "spiderfarmer_ggs"
DATA = "spiderfarmer_ggs"
DATA_KEY = "spiderfarmer_ggs"

CONF_MQTT_BROKER = "mqtt_broker"
CONF_MQTT_PORT = "mqtt_port"
CONF_MQTT_USERNAME = "mqtt_username"
CONF_MQTT_PASSWORD = "mqtt_password"
CONF_SCAN_INTERVAL = "scan_interval"

DEFAULT_MQTT_BROKER = "127.0.0.1"
DEFAULT_MQTT_PORT = 1883
DEFAULT_SCAN_INTERVAL = 30

MQTT_TOPIC_PREFIX = "ggs"
MQTT_STATUS_TOPIC = "ggs/+/+/status"
MQTT_SENSORS_TOPIC = "ggs/+/+/sensors"
MQTT_SYSTEM_TOPIC = "ggs/+/+/system"
MQTT_CMD_TOPIC = "ggs/{device_type}/{mac}/cmd"

DEVICE_TYPES = ["ps5", "lc", "cb", "ps3", "t8"]

ENV_SENSOR_FIELDS = {
    "temp": {"name": "Temperature", "unit": "°C", "device_class": "temperature"},
    "humi": {"name": "Humidity", "unit": "%", "device_class": "humidity"},
    "vpd": {"name": "VPD", "unit": "kPa", "device_class": "pressure"},
    "co2": {"name": "CO2", "unit": "ppm", "device_class": "carbon_dioxide"},
    "ppfd": {"name": "PPFD", "unit": "μmol/m²/s", "device_class": "illuminance"},
}

SOIL_SENSOR_FIELDS = {
    "tempSoil": {"name": "Soil Temperature", "unit": "°C", "device_class": "temperature"},
    "humiSoil": {"name": "Soil Moisture", "unit": "%", "device_class": "moisture"},
    "ECSoil": {"name": "Soil EC", "unit": "mS/cm", "device_class": "conductivity"},
}

SYSTEM_FIELDS = {
    "ver": {"name": "Firmware Version", "unit": None, "device_class": None},
    "wifi_rssi": {"name": "WiFi Signal", "unit": "dBm", "device_class": "signal_strength"},
    "upTime": {"name": "Uptime", "unit": "s", "device_class": "duration"},
    "mem_free": {"name": "Free Memory", "unit": "MB", "device_class": None},
}

SERVICE_SEND_COMMAND = "send_command"
SERVICE_GET_CONFIG = "get_config"
SERVICE_SET_CONFIG = "set_config"

ATTR_DEVICE_TYPE = "device_type"
ATTR_MAC = "mac"
ATTR_METHOD = "method"
ATTR_FIELD = "field"
ATTR_VALUE = "value"
ATTR_LIGHT_ID = "light_id"
ATTR_LEVEL = "level"
ATTR_OUTLET = "outlet"

DEVICE_NAME_MAP = {
    "ps5": "Spider Farmer PS5",
    "ps3": "Spider Farmer PS3",
    "t8": "Spider Farmer T8",
    "lc": "Spider Farmer Light Controller",
    "cb": "Spider Farmer CB Controller",
}
