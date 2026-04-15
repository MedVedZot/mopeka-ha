"""Mopeka HA Integration."""
import asyncio
import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

_LOGGER = logging.getLogger(__name__)
DOMAIN = "mopeka_ha"
PLATFORMS = [Platform.SENSOR]
CONF_INTERVAL = "update_interval"
DEFAULT_INTERVAL = 1

API_DEFAULTS = {
    "user_pool_id": "us-east-1_sLQ1KlStp",
    "client_id": "7dafulgmkck7u9hiju6v6p1emt",
    "base_url": "https://gateway.mopeka.cloud/app/sensors",
    "timeout": 20,
    "region": "us-east-1"
}

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    config = {"username": entry.data[CONF_EMAIL], "password": entry.data[CONF_PASSWORD], **API_DEFAULTS}
    interval = entry.options.get(CONF_INTERVAL, DEFAULT_INTERVAL)

    async def async_update_data():
        try:
            return await asyncio.to_thread(_fetch_data, config)
        except Exception as err:
            raise UpdateFailed(f"API Error: {err}") from err

    coord = DataUpdateCoordinator(hass, _LOGGER, name=DOMAIN, update_method=async_update_data, update_interval=timedelta(minutes=interval))
    await coord.async_config_entry_first_refresh()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coord
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    return True

def _fetch_data(config: dict) -> dict:
    from mopeka.client import MopekaClient
    return {s["device_id"]: s for s in MopekaClient(config).get_full_state()}

async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        if DOMAIN in hass.data:
            hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok