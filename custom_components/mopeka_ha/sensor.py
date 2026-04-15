"""Mopeka HA Sensors."""
import logging
import re

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import slugify

from . import DOMAIN

_LOGGER = logging.getLogger(__name__)

DEVICE_INFO_FIELDS = {"device_id", "wifi_gate_id", "brand", "model_number", "name", "timestamp_iso", "history_start_date", "history_depth_days"}

MAP = {
    "tank_height": ("m", "ruler", None),
    "temperature_c": ("C", "thermometer", None),
    "temperature_f": ("F", "thermometer", None),
    "battery_voltage": ("V", "battery", SensorDeviceClass.VOLTAGE),
    "signal_quality": ("%", "signal", None),
    "level_cm": ("cm", "ruler", None),
    "level_inches": ("in", "ruler", None),
    "fill_percent": ("%", "percent", None),
    "volume_liters": ("L", "water", None),
    "volume_gallons_us": ("gal", "water", None),
}

def get_config(key, val):
    if isinstance(val, bool):
        return None, "check-circle", None, None
    if isinstance(val, str):
        return None, "text", None, None
    if key in MAP:
        unit, icon, device_class = MAP[key]
        return unit, icon, device_class, SensorStateClass.MEASUREMENT if unit else None
    return None, "information", None, None

def _sensor_key_from_unique_id(unique_id, known_sensor_keys):
    for sensor_key in sorted(known_sensor_keys, key=len, reverse=True):
        suffix = f"_{sensor_key}"
        if unique_id.endswith(suffix):
            return sensor_key
    return None

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    selected = entry.options.get("sensors", [])
    device_registry = dr.async_get(hass)
    entity_registry = er.async_get(hass)

    existing_entries = er.async_entries_for_config_entry(entity_registry, entry.entry_id)
    existing_entries = er.async_entries_for_config_entry(entity_registry, entry.entry_id)
    
    all_possible_keys = set(MAP.keys()) | {
        "updated_human_readable", "vertical", "propaneButaneRatio", 
        "tank_type", "volume_original_unit", "tank_height"
    }
    
    for ent in existing_entries:
        s_key = _sensor_key_from_unique_id(ent.unique_id, all_possible_keys)
        if s_key and s_key not in selected:
            entity_registry.async_remove(ent.entity_id)

    for device_id, data in coordinator.data.items():
        api_name = data.get("name")
        if not api_name:
            continue

        device = device_registry.async_get_device(identifiers={(DOMAIN, device_id)})
        if device and device.name != api_name:
            device_registry.async_update_device(device.id, name=api_name)

        if not device:
            continue

        known_sensor_keys = set(selected)
        known_sensor_keys.update(k for k in data if k not in DEVICE_INFO_FIELDS)

        new_prefix = slugify(api_name)
        if not new_prefix:
            continue
            
        entity_entries = er.async_entries_for_device(entity_registry, device.id, include_disabled_entities=True)

        for entity_entry in entity_entries:
            if entity_entry.domain != "sensor":
                continue
            if not entity_entry.unique_id:
                continue

            sensor_key = _sensor_key_from_unique_id(entity_entry.unique_id, known_sensor_keys)
            if not sensor_key:
                continue
            
            if sensor_key not in selected:
                continue

            safe_sensor_key = slugify(sensor_key)
            expected_entity_id = f"sensor.{new_prefix}_{safe_sensor_key}"
            
            if entity_entry.entity_id == expected_entity_id:
                continue
            if entity_registry.async_is_registered(expected_entity_id):
                continue

            try:
                entity_registry.async_update_entity(entity_entry.entity_id, new_entity_id=expected_entity_id)
            except ValueError as e:
                _LOGGER.debug("Could not update entity ID %s to %s: %s", entity_entry.entity_id, expected_entity_id, e)

    entities = []
    for device_id, device_data in coordinator.data.items():
        for sensor_key in selected:
            if sensor_key in device_data:
                entities.append(MopekaSensor(coordinator, device_id, sensor_key))
    async_add_entities(entities)

class MopekaSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, device_id, sensor_key):
        super().__init__(coordinator)
        self._dev_id = device_id
        self._key = sensor_key
        unit, icon, device_class, state_class = get_config(sensor_key, coordinator.data[device_id].get(sensor_key))
        self._attr_unique_id = f"{device_id}_{sensor_key}"
        self._attr_native_unit_of_measurement = unit
        self._attr_device_class = device_class
        self._attr_state_class = state_class
        self._attr_icon = f"mdi:{icon}"
        self._attr_has_entity_name = True

    @property
    def name(self):
        return re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", self._key).replace("_", " ").title()

    @property
    def device_info(self):
        data = self.coordinator.data[self._dev_id]
        return DeviceInfo(
            identifiers={(DOMAIN, self._dev_id)},
            name=data.get("name"),
            manufacturer=data.get("brand"),
            model=str(data.get("model_number")),
            serial_number=data.get("device_id"),
            hw_version=data.get("wifi_gate_id"),
        )

    @property
    def native_value(self):
        return self.coordinator.data[self._dev_id].get(self._key)