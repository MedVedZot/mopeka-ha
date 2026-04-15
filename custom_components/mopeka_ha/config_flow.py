"""Config flow for Mopeka HA."""
import asyncio
import voluptuous as vol
import homeassistant.helpers.config_validation as cv
from homeassistant import config_entries
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.data_entry_flow import AbortFlow

from . import API_DEFAULTS, CONF_INTERVAL, DEFAULT_INTERVAL, DOMAIN

STATIC_SENSORS = [
    "battery_voltage",
    "fill_percent",
    "level_cm",
    "level_inches",
    "propaneButaneRatio",
    "signal_quality",
    "tank_height",
    "tank_type",
    "temperature_c",
    "temperature_f",
    "updated_human_readable",
    "vertical",
    "volume_gallons_us",
    "volume_liters",
    "volume_original_unit"
]

def _get_client(data):
    from mopeka.client import MopekaClient
    return MopekaClient({"username": data[CONF_EMAIL], "password": data[CONF_PASSWORD], **API_DEFAULTS})

async def validate_auth(data):
    def _validate():
        return _get_client(data).get_full_state()
    return await asyncio.to_thread(_validate)

def _get_combined_states(states_list):
    combined = {}
    for device in states_list:
        for key in STATIC_SENSORS:
            if key in device and device[key] is not None:
                if key not in combined or combined[key] == "n/a":
                    combined[key] = device[key]
    return combined

class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    @staticmethod
    def async_get_options_flow(config_entry):
        return OptionsFlowHandler(config_entry)

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input:
            try:
                await validate_auth(user_input)
                await self.async_set_unique_id(user_input[CONF_EMAIL].lower())
                self._abort_if_unique_id_configured()
                self._data = user_input
                return await self.async_step_sensors()
            except AbortFlow:
                raise
            except Exception as err:
                if "401" in str(err) or "unauthorized" in str(err).lower():
                    errors["base"] = "invalid_auth"
                else:
                    errors["base"] = "cannot_connect"
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required(CONF_EMAIL): str, vol.Required(CONF_PASSWORD): str}),
            errors=errors
        )

    async def async_step_reconfigure(self, user_input=None):
        errors = {}
        entry = self.hass.config_entries.async_get_entry(self.context["entry_id"])
        if user_input:
            try:
                await validate_auth(user_input)
                return self.async_update_reload_and_abort(entry, data={**entry.data, **user_input})
            except AbortFlow:
                raise
            except Exception as err:
                if "401" in str(err) or "unauthorized" in str(err).lower():
                    errors["base"] = "invalid_auth"
                else:
                    errors["base"] = "cannot_connect"
        return self.async_show_form(
            step_id="reconfigure",
            data_schema=vol.Schema({
                vol.Required(CONF_EMAIL, default=entry.data[CONF_EMAIL]): str,
                vol.Required(CONF_PASSWORD): str
            }),
            errors=errors
        )

    async def async_step_sensors(self, user_input=None):
        errors = {}
        try:
            states = await asyncio.to_thread(lambda: _get_client(self._data).get_full_state())
            display_data = _get_combined_states(states)
        except Exception:
            display_data = {}

        if user_input is not None:
            selected = []
            for k, v in user_input.items():
                if v:
                    if "(" in k:
                        sensor_key = k.split(" (")[0]
                    else:
                        sensor_key = k
                    selected.append(sensor_key)
            
            if not selected:
                errors["base"] = "no_sensors_selected"
            else:
                return self.async_create_entry(
                    title=self._data[CONF_EMAIL],
                    data=self._data,
                    options={"sensors": selected, CONF_INTERVAL: DEFAULT_INTERVAL}
                )

        schema_dict = {}
        for s in sorted(STATIC_SENSORS):
            val = display_data.get(s, "n/a")
            display_label = f"{s} ({val})"
            schema_dict[vol.Optional(display_label, default=False)] = bool

        return self.async_show_form(step_id="sensors", data_schema=vol.Schema(schema_dict), errors=errors)

class OptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, entry):
        self.entry = entry

    async def async_step_init(self, user_input=None):
        errors = {}
        if user_input is not None:
            new_data = dict(self.entry.data)
            new_options = dict(self.entry.options)
            
            pwd = user_input.get(CONF_PASSWORD) or self.entry.data[CONF_PASSWORD]
            check_data = {CONF_EMAIL: self.entry.data[CONF_EMAIL], CONF_PASSWORD: pwd}
            
            selected = []
            for k, v in user_input.items():
                if v:
                    if "(" in k:
                        sensor_key = k.split(" (")[0]
                    else:
                        sensor_key = k
                    selected.append(sensor_key)
            
            if not selected:
                errors["base"] = "no_sensors_selected"
            else:
                try:
                    await validate_auth(check_data)
                    if user_input.get(CONF_PASSWORD):
                        new_data[CONF_PASSWORD] = user_input.pop(CONF_PASSWORD)
                    else:
                        user_input.pop(CONF_PASSWORD, None)

                    new_options[CONF_INTERVAL] = user_input.pop(CONF_INTERVAL)
                    new_options["sensors"] = selected

                    self.hass.config_entries.async_update_entry(self.entry, data=new_data)
                    return self.async_create_entry(title="", data=new_options)
                except Exception as err:
                    if "401" in str(err) or "unauthorized" in str(err).lower():
                        errors["base"] = "invalid_auth"
                    else:
                        errors["base"] = "cannot_connect"

        coordinator = self.hass.data.get(DOMAIN, {}).get(self.entry.entry_id)
        current_sensors = self.entry.options.get("sensors", [])
        current_interval = self.entry.options.get(CONF_INTERVAL, DEFAULT_INTERVAL)

        schema_dict = {
            vol.Optional(CONF_PASSWORD): str,
            vol.Required(CONF_INTERVAL, default=current_interval): cv.positive_int,
        }

        display_data = {}
        try:
            if coordinator and hasattr(coordinator, 'data') and coordinator.data:
                device_values = list(coordinator.data.values())
                if device_values:
                    display_data = _get_combined_states(device_values)
        except Exception:
            display_data = {}

        for s in sorted(STATIC_SENSORS):
            val = display_data.get(s, "n/a")
            display_label = f"{s} ({val})"
            schema_dict[vol.Optional(display_label, default=s in current_sensors)] = bool

        return self.async_show_form(step_id="init", data_schema=vol.Schema(schema_dict), errors=errors)