# Spider Farmer GGS Home Assistant Integration

[![Home Assistant Custom Integration](https://img.shields.io/badge/Home%20Assistant-Custom%20Integration-blue)](https://www.home-assistant.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Version](https://img.shields.io/badge/Version-1.0.0-green)]()

A custom Home Assistant integration for **Spider Farmer GGS** (Grow Gear System) controllers. Communicates with Spider Farmer smart grow systems via **MQTT** to monitor and control lights, climate modules, outlets, and environmental sensors.

---

## 📋 Table of Contents

- [Supported Devices](#-supported-devices)
- [Features](#-features)
- [Prerequisites](#-prerequisites)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [MQTT Topics](#-mqtt-topics)
- [Entities](#-entities)
- [Services](#-services)
- [Troubleshooting](#-troubleshooting)
- [License](#-license)

---

## 🖥️ Supported Devices

| Device Type | Description |
|------------|-------------|
| `ps5` | Spider Farmer PS5 Controller |
| `ps3` | Spider Farmer PS3 Controller |
| `t8` | Spider Farmer T8 Controller |
| `lc` | Spider Farmer Light Controller (LC) |
| `cb` | Spider Farmer CB Controller |

---

## ✨ Features

- **Automatic device discovery** via MQTT topic subscriptions
- **Light control** — on/off with brightness (0–255)
- **Switch control** — outlets and climate modules (blower, fan, heater, humidifier, dehumidifier)
- **Environmental sensors** — temperature, humidity, VPD, CO₂, PPFD
- **Soil sensors** — temperature, moisture, EC (up to 4 soil probes)
- **System diagnostics** — WiFi signal strength, uptime, free memory
- **Connectivity monitoring** — binary sensor for device online/offline status
- **Custom services** — advanced MQTT command control (`send_command`, `get_config`, `set_config`)

---

## 📦 Prerequisites

1. **Home Assistant** (Core, Container, or OS)
2. **MQTT integration** configured and running in Home Assistant
3. A **Spider Farmer GGS-compatible device** publishing to MQTT topics in the format `ggs/{device_type}/{mac}/{message_type}`

---

## 🔧 Installation

### Option 1: Manual Install

1. Copy the entire integration folder into your Home Assistant config directory:
   ```
   <config>/custom_components/spiderfarmer_ggs/
   ```
2. Restart Home Assistant.
3. Go to **Settings → Devices & Services → Add Integration** and search for **"Spider Farmer GGS"**.

### Option 2: HACS (if available)

1. Open **HACS** in Home Assistant.
2. Click **+** → search for **"Spider Farmer GGS"**.
3. Click **Download**.
4. Restart Home Assistant.

---

## ⚙️ Configuration

During setup you'll be asked for:

| Field | Description | Default |
|-------|-------------|---------|
| **Host** | MQTT broker address | `127.0.0.1` |
| **Port** | MQTT broker port | `1883` |
| **Scan Interval** | Polling interval in seconds (fallback mode) | `30` |

> **Note:** The integration primarily uses **MQTT subscriptions** for real-time updates. The scan interval is only used as a fallback when MQTT is unavailable.

---

## 📡 MQTT Topics

### Subscribed Topics (Incoming)

| Topic | Purpose |
|-------|---------|
| `ggs/+/+/status` | Device status: lights, outlets, climate modules |
| `ggs/+/+/sensors` | Sensor data: environment, soil |
| `ggs/+/+/system` | System info: firmware, WiFi, uptime |

### Published Topics (Outgoing)

| Topic | Purpose |
|-------|---------|
| `ggs/{device_type}/{mac}/cmd` | Send commands to the device |

### Topic Format

```
ggs/{device_type}/{mac}/{message_type}
```

**Example:**
```
ggs/ps5/AABBCCDDEEFF/status
ggs/ps5/AABBCCDDEEFF/sensors
ggs/ps5/AABBCCDDEEFF/system
```

---

## 📊 Entities

### Sensors

| Sensor | Unit | Device Class |
|--------|------|-------------|
| Temperature | °C | `temperature` |
| Humidity | % | `humidity` |
| VPD | kPa | `pressure` |
| CO₂ | ppm | `carbon_dioxide` |
| PPFD | μmol/m²/s | `illuminance` |
| Soil Temperature | °C | `temperature` |
| Soil Moisture | % | `moisture` |
| Soil EC | mS/cm | `conductivity` |
| WiFi Signal | dBm | `signal_strength` |
| Uptime | s | `duration` |
| Free Memory | MB | — |

### Lights

| Entity | Description |
|--------|-------------|
| Light | Main light channel (brightness 0–255) |
| Light 2 | Secondary light channel (if available) |

### Switches

| Switch | Description |
|--------|-------------|
| Outlet O1–O4 | Relay outlet control |
| Blower | Climate blower module |
| Fan | Climate fan module |
| Heater | Climate heater module |
| Humidifier | Climate humidifier module |
| Dehumidifier | Climate dehumidifier module |

### Binary Sensors

| Sensor | Description |
|--------|-------------|
| Connectivity | Device online/offline status |

---

## 🔌 Services

### `spiderfarmer_ggs.send_command`

Send a raw command to a device.

| Field | Required | Description |
|-------|----------|-------------|
| `device_type` | ✅ | Device type: `ps5`, `ps3`, `t8`, `lc`, `cb` |
| `mac` | ✅ | MAC address of the device |
| `method` | ✅ | Command method (`getConfigField`, `setConfigField`, `getDevSta`, `getSysSta`) |
| `field` | ❌ | Config field name |
| `value` | ❌ | Value to set |

**Example (YAML):**
```yaml
service: spiderfarmer_ggs.send_command
data:
  device_type: ps5
  mac: AABBCCDDEEFF
  method: getConfigField
  field: light_mode
```

### `spiderfarmer_ggs.get_config`

Get a configuration field from a device.

| Field | Required | Description |
|-------|----------|-------------|
| `device_type` | ✅ | Device type |
| `mac` | ✅ | MAC address |
| `field` | ❌ | Config field name (leave empty for all fields) |

### `spiderfarmer_ggs.set_config`

Set a configuration field on a device.

| Field | Required | Description |
|-------|----------|-------------|
| `device_type` | ✅ | Device type |
| `mac` | ✅ | MAC address |
| `field` | ✅ | Config field name |
| `value` | ✅ | Value to set |

---

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| No devices discovered | Verify your device is publishing to `ggs/{device_type}/{mac}/{type}` MQTT topics |
| MQTT not available | Ensure the MQTT integration is set up and connected in Home Assistant |
| Entities show unavailable | Check that the device is online and sending data periodically |
| Commands not working | Verify the MQTT broker allows publishing to `ggs/{device_type}/{mac}/cmd` |
| Logs | Check Home Assistant logs under `custom_components.spiderfarmer_ggs` |

---

## 📜 License

This project is licensed under the [MIT License](LICENSE).

---

## 🙏 Credits

- Built for the **Home Assistant** community
- Designed for **Spider Farmer** GGS grow systems
