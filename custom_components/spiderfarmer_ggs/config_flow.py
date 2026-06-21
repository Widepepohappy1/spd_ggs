import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_USERNAME, CONF_PASSWORD
from homeassistant.data_entry_flow import FlowResult

from .const import (
    DOMAIN,
    DEFAULT_MQTT_BROKER,
    DEFAULT_MQTT_PORT,
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
)


class SpiderFarmerGGSConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None) -> FlowResult:
        if user_input is not None:
            return self.async_create_entry(
                title=f"Spider Farmer GGS ({user_input[CONF_HOST]})",
                data=user_input,
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_HOST, default=DEFAULT_MQTT_BROKER): str,
                vol.Required(CONF_PORT, default=DEFAULT_MQTT_PORT): int,
                vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): int,
            }),
            description_placeholders={},
        )

    async def async_step_mqtt(self, discovery_info=None) -> FlowResult:
        await self.async_set_unique_id("mqtt_discovery_spiderfarmer_ggs")
        self._abort_if_unique_id_configured()

        return self.async_create_entry(
            title="Spider Farmer GGS (MQTT Discovery)",
            data={
                CONF_HOST: DEFAULT_MQTT_BROKER,
                CONF_PORT: DEFAULT_MQTT_PORT,
                CONF_SCAN_INTERVAL: DEFAULT_SCAN_INTERVAL,
            },
        )
