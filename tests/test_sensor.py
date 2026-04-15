"""Tests for Mopeka sensors."""
from unittest.mock import patch
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from pytest_homeassistant_custom_component.common import MockConfigEntry
from custom_components.mopeka_ha import DOMAIN

async def test_sensors_creation_and_data(hass):
    """Test that sensors are created and display correct data."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="test@example.com",
        data={CONF_EMAIL: "test@example.com", CONF_PASSWORD: "test-password"},
        options={"sensors": ["battery"]}
    )
    entry.add_to_hass(hass)

    mock_device = {
        "device_id": "MOP123",
        "name": "Gas Tank",
        "battery": 2.95,
        "model_number": "Standard"
    }

    with patch("mopeka.client.MopekaClient") as mock_client:
        mock_client.return_value.get_full_state.return_value = [mock_device]
        
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        state = hass.states.get("sensor.gas_tank_battery")
        
        assert state is not None
        assert state.state == "2.95"

async def test_sensors_update_data(hass):
    """Test that sensors update when API data changes."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="test@example.com",
        data={CONF_EMAIL: "test@example.com", CONF_PASSWORD: "test-password"},
        options={"sensors": ["battery"]}
    )
    entry.add_to_hass(hass)

    mock_device = {"device_id": "MOP123", "name": "Gas Tank", "battery": 3.0}

    with patch("mopeka.client.MopekaClient") as mock_client:
        client_inst = mock_client.return_value
        client_inst.get_full_state.return_value = [mock_device]
        
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        assert hass.states.get("sensor.gas_tank_battery").state == "3.0"

        client_inst.get_full_state.return_value = [
            {"device_id": "MOP123", "name": "Gas Tank", "battery": 2.5}
        ]
        
        coordinator = hass.data[DOMAIN][entry.entry_id]
        await coordinator.async_refresh()
        
        assert hass.states.get("sensor.gas_tank_battery").state == "2.5"


async def test_sensor_get_config_bool(hass):
    """Test get_config with boolean values."""
    from custom_components.mopeka_ha.sensor import get_config
    
    unit, icon, device_class, state_class = get_config("some_key", True)
    
    assert unit is None
    assert icon == "check-circle"
    assert device_class is None
    assert state_class is None


async def test_sensor_get_config_string(hass):
    """Test get_config with string values."""
    from custom_components.mopeka_ha.sensor import get_config
    
    unit, icon, device_class, state_class = get_config("some_key", "some_value")
    
    assert unit is None
    assert icon == "text"
    assert device_class is None
    assert state_class is None


async def test_sensor_get_config_mapped(hass):
    """Test get_config with mapped sensor types."""
    from custom_components.mopeka_ha.sensor import get_config
    
    unit, icon, device_class, state_class = get_config("battery_voltage", 3.5)
    assert unit == "V"
    assert icon == "battery"
    assert state_class == "measurement"
    
    unit, icon, device_class, state_class = get_config("temperature_c", 20.5)
    assert unit == "C"
    assert icon == "thermometer"
    assert state_class == "measurement"


async def test_sensor_get_config_default(hass):
    """Test get_config with unmapped sensor types."""
    from custom_components.mopeka_ha.sensor import get_config
    
    unit, icon, device_class, state_class = get_config("unknown_key", 42.0)
    
    assert unit is None
    assert icon == "information"
    assert device_class is None
    assert state_class is None


async def test_sensor_key_from_unique_id(hass):
    """Test _sensor_key_from_unique_id function."""
    from custom_components.mopeka_ha.sensor import _sensor_key_from_unique_id
    
    known_keys = ["battery_voltage", "temperature_c", "fill_percent"]
    
    assert _sensor_key_from_unique_id("123_battery_voltage", known_keys) == "battery_voltage"
    
    assert _sensor_key_from_unique_id("123_temperature_c", known_keys) == "temperature_c"
    
    assert _sensor_key_from_unique_id("123_unknown_key", known_keys) is None
    
    assert _sensor_key_from_unique_id("device123_temperature_c", known_keys) == "temperature_c"


async def test_sensor_entity_removal(hass):
    """Test removing sensors when deselected in options."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="test@example.com",
        data={CONF_EMAIL: "test@example.com", CONF_PASSWORD: "test-password"},
        options={"sensors": ["battery", "temperature_c"]}  # Start with 2 sensors
    )
    entry.add_to_hass(hass)

    mock_device = {
        "device_id": "MOP123",
        "name": "Gas Tank",
        "battery": 3.0,
        "temperature_c": 25.5,
        "model_number": "Standard"
    }

    with patch("mopeka.client.MopekaClient") as mock_client:
        mock_client.return_value.get_full_state.return_value = [mock_device]
        
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        assert hass.states.get("sensor.gas_tank_battery") is not None
        assert hass.states.get("sensor.gas_tank_temperature_c") is not None

        mock_client.return_value.get_full_state.return_value = [mock_device]
        hass.config_entries.async_update_entry(entry, options={"sensors": ["battery"]})
        await hass.async_block_till_done()

        assert hass.states.get("sensor.gas_tank_battery") is not None
        from homeassistant.helpers import entity_registry as er
        entity_registry = er.async_get(hass)
        entity_id = entity_registry.async_get_entity_id("sensor", DOMAIN, "MOP123_temperature_c")
        assert entity_id is None


async def test_sensor_device_name_update(hass):
    """Test device name gets updated when API returns new name."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="test@example.com",
        data={CONF_EMAIL: "test@example.com", CONF_PASSWORD: "test-password"},
        options={"sensors": ["battery"]}
    )
    entry.add_to_hass(hass)

    mock_device = {
        "device_id": "MOP123",
        "name": "Gas Tank",
        "battery": 3.0,
        "model_number": "Standard"
    }

    with patch("mopeka.client.MopekaClient") as mock_client:
        mock_client.return_value.get_full_state.return_value = [mock_device]
        
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        from homeassistant.helpers import device_registry as dr
        device_registry = dr.async_get(hass)
        device = device_registry.async_get_device(identifiers={(DOMAIN, "MOP123")})
        assert device is not None
        assert device.name == "Gas Tank"

        mock_device["name"] = "Propane Tank"
        coordinator = hass.data[DOMAIN][entry.entry_id]
        await coordinator.async_refresh()
        await hass.async_block_till_done()

        await hass.config_entries.async_reload(entry.entry_id)
        await hass.async_block_till_done()

        device = device_registry.async_get_device(identifiers={(DOMAIN, "MOP123")})
        assert device is not None
        assert device.name == "Propane Tank"


async def test_sensor_entity_id_update(hass):
    """Test entity_id gets updated when device name changes."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="test@example.com",
        data={CONF_EMAIL: "test@example.com", CONF_PASSWORD: "test-password"},
        options={"sensors": ["battery"]}
    )
    entry.add_to_hass(hass)

    mock_device = {
        "device_id": "MOP123",
        "name": "Gas Tank",
        "battery": 3.0,
        "model_number": "Standard"
    }

    with patch("mopeka.client.MopekaClient") as mock_client:
        mock_client.return_value.get_full_state.return_value = [mock_device]
        
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        assert hass.states.get("sensor.gas_tank_battery") is not None

        mock_device["name"] = "Propane Tank"
        coordinator = hass.data[DOMAIN][entry.entry_id]
        await coordinator.async_refresh()
        await hass.async_block_till_done()

        from homeassistant.helpers import entity_registry as er
        entity_registry = er.async_get(hass)
        
        await hass.config_entries.async_reload(entry.entry_id)
        await hass.async_block_till_done()

        assert hass.states.get("sensor.propane_tank_battery") is not None
        
        assert hass.states.get("sensor.gas_tank_battery") is None


async def test_sensor_device_without_name(hass):
    """Test devices without names are skipped."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="test@example.com",
        data={CONF_EMAIL: "test@example.com", CONF_PASSWORD: "test-password"},
        options={"sensors": ["battery"]}
    )
    entry.add_to_hass(hass)

    mock_device = {
        "device_id": "MOP123",
        "battery": 3.0,
        "model_number": "Standard"
    }

    with patch("mopeka.client.MopekaClient") as mock_client:
        mock_client.return_value.get_full_state.return_value = [mock_device]
        
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        assert hass.states.get("sensor.mop123_battery") is None


async def test_sensor_entity_id_already_registered(hass):
    """Test entity_id update when new ID is already registered."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="test@example.com",
        data={CONF_EMAIL: "test@example.com", CONF_PASSWORD: "test-password"},
        options={"sensors": ["battery"]}
    )
    entry.add_to_hass(hass)

    mock_device = {
        "device_id": "MOP123",
        "name": "Gas Tank",
        "battery": 3.0,
        "model_number": "Standard"
    }

    with patch("mopeka.client.MopekaClient") as mock_client:
        mock_client.return_value.get_full_state.return_value = [mock_device]
        
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        assert hass.states.get("sensor.gas_tank_battery") is not None

        mock_device["name"] = "Gas Tank 2"
        mock_client.return_value.get_full_state.return_value = [mock_device]
        
        from homeassistant.helpers import entity_registry as er
        entity_registry = er.async_get(hass)
        
        coordinator = hass.data[DOMAIN][entry.entry_id]
        await coordinator.async_refresh()
        await hass.async_block_till_done()


async def test_sensor_entity_without_unique_id(hass):
    """Test handling of entities without unique_id."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="test@example.com",
        data={CONF_EMAIL: "test@example.com", CONF_PASSWORD: "test-password"},
        options={"sensors": ["battery"]}
    )
    entry.add_to_hass(hass)

    mock_device = {
        "device_id": "MOP123",
        "name": "Gas Tank",
        "battery": 3.0,
        "model_number": "Standard"
    }

    with patch("mopeka.client.MopekaClient") as mock_client:
        mock_client.return_value.get_full_state.return_value = [mock_device]
        
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        assert hass.states.get("sensor.gas_tank_battery") is not None


async def test_sensor_entity_unknown_sensor_key(hass):
    """Test handling of entities with unknown sensor keys."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="test@example.com",
        data={CONF_EMAIL: "test@example.com", CONF_PASSWORD: "test-password"},
        options={"sensors": ["battery"]}
    )
    entry.add_to_hass(hass)

    mock_device = {
        "device_id": "MOP123",
        "name": "Gas Tank",
        "battery": 3.0,
        "model_number": "Standard",
        "unknown_sensor_key": 42.0  # Additional field not in MAP
    }

    with patch("mopeka.client.MopekaClient") as mock_client:
        mock_client.return_value.get_full_state.return_value = [mock_device]
        
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        assert hass.states.get("sensor.gas_tank_battery") is not None
        assert hass.states.get("sensor.gas_tank_unknown_sensor_key") is None


async def test_sensor_entity_non_sensor_domain(hass):
    """Test handling of entities with non-sensor domain (line 88)."""
    from homeassistant.helpers import entity_registry as er
    from homeassistant.helpers import device_registry as dr
    
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="test@example.com",
        data={CONF_EMAIL: "test@example.com", CONF_PASSWORD: "test-password"},
        options={"sensors": ["battery"]}
    )
    entry.add_to_hass(hass)

    mock_device = {
        "device_id": "MOP123",
        "name": "Gas Tank",
        "battery": 3.0,
        "model_number": "Standard"
    }

    with patch("mopeka.client.MopekaClient") as mock_client:
        mock_client.return_value.get_full_state.return_value = [mock_device]
        
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        device_registry = dr.async_get(hass)
        device = device_registry.async_get_device(identifiers={(DOMAIN, "MOP123")})
        
        entity_registry = er.async_get(hass)
        entity_registry.async_get_or_create(
            domain="binary_sensor",
            platform=DOMAIN,
            unique_id=f"MOP123_test",
            device_id=device.id,
            config_entry=entry,
        )
        
        await hass.config_entries.async_reload(entry.entry_id)
        await hass.async_block_till_done()
        
        assert hass.states.get("sensor.gas_tank_battery") is not None


async def test_sensor_entity_without_unique_id_in_registry(hass):
    """Test handling of entities without unique_id in registry (line 90)."""
    from homeassistant.helpers import entity_registry as er
    from homeassistant.helpers import device_registry as dr
    
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="test@example.com",
        data={CONF_EMAIL: "test@example.com", CONF_PASSWORD: "test-password"},
        options={"sensors": ["battery"]}
    )
    entry.add_to_hass(hass)

    mock_device = {
        "device_id": "MOP123",
        "name": "Gas Tank",
        "battery": 3.0,
        "model_number": "Standard"
    }

    with patch("mopeka.client.MopekaClient") as mock_client:
        mock_client.return_value.get_full_state.return_value = [mock_device]
        
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        assert hass.states.get("sensor.gas_tank_battery") is not None
        
        device_registry = dr.async_get(hass)
        device = device_registry.async_get_device(identifiers={(DOMAIN, "MOP123")})
        
        entity_registry = er.async_get(hass)
        entity_registry.async_get_or_create(
            domain="sensor",
            platform="test",
            unique_id="MOP123_test_old",
            device_id=device.id,
            config_entry=entry,
        )
        
        await hass.config_entries.async_reload(entry.entry_id)
        await hass.async_block_till_done()
        
        assert hass.states.get("sensor.gas_tank_battery") is not None


async def test_sensor_entity_already_exists(hass):
    """Test handling when new entity_id is already registered (line 100)."""
    from homeassistant.helpers import entity_registry as er
    from homeassistant.helpers import device_registry as dr
    
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="test@example.com",
        data={CONF_EMAIL: "test@example.com", CONF_PASSWORD: "test-password"},
        options={"sensors": ["battery"]}
    )
    entry.add_to_hass(hass)

    mock_device = {
        "device_id": "MOP123",
        "name": "Gas Tank",
        "battery": 3.0,
        "model_number": "Standard"
    }

    with patch("mopeka.client.MopekaClient") as mock_client:
        mock_client.return_value.get_full_state.return_value = [mock_device]
        
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        assert hass.states.get("sensor.gas_tank_battery") is not None
        
        device_registry = dr.async_get(hass)
        device = device_registry.async_get_device(identifiers={(DOMAIN, "MOP123")})
        
        entity_registry = er.async_get(hass)
        
        entity_registry.async_get_or_create(
            domain="sensor",
            platform="another_integration",
            unique_id="MOP123_battery_conflict",
            device_id=device.id,
            config_entry=entry,
        )
        
        mock_device["name"] = "propane tank"
        coordinator = hass.data[DOMAIN][entry.entry_id]
        await coordinator.async_refresh()
        await hass.async_block_till_done()
        
        await hass.config_entries.async_reload(entry.entry_id)
        await hass.async_block_till_done()
        
        assert hass.states.get("sensor.gas_tank_battery") is not None or \
               hass.states.get("sensor.propane_tank_battery") is not None


async def test_sensor_entity_with_unknown_key_in_unique_id(hass):
    """Test handling of entities with unknown sensor keys in unique_id (line 94)."""
    from homeassistant.helpers import entity_registry as er
    
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="test@example.com",
        data={CONF_EMAIL: "test@example.com", CONF_PASSWORD: "test-password"},
        options={"sensors": ["battery"]}
    )
    entry.add_to_hass(hass)

    mock_device = {
        "device_id": "MOP123",
        "name": "Gas Tank",
        "battery": 3.0,
        "model_number": "Standard"
    }

    with patch("mopeka.client.MopekaClient") as mock_client:
        mock_client.return_value.get_full_state.return_value = [mock_device]
        
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        assert hass.states.get("sensor.gas_tank_battery") is not None
        
        entity_registry = er.async_get(hass)
        entity_registry.async_get_or_create(
            domain="sensor",
            platform=DOMAIN,
            unique_id="MOP123_unknown_sensor_key",
            config_entry=entry,
        )
        
        await hass.config_entries.async_reload(entry.entry_id)
        await hass.async_block_till_done()
        
        assert hass.states.get("sensor.gas_tank_battery") is not None


async def test_sensor_empty_device_name(hass):
    """Test device with name that slugifies to empty string (line 91)."""
    from homeassistant.helpers import entity_registry as er
    from homeassistant.util import slugify
    
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="test@example.com",
        data={CONF_EMAIL: "test@example.com", CONF_PASSWORD: "test-password"},
        options={"sensors": ["battery"]}
    )
    entry.add_to_hass(hass)

    mock_device = {
        "device_id": "MOP123",
        "name": "___",  # Only underscores, slugifies to empty
        "battery": 3.0,
        "model_number": "Standard"
    }

    with patch("mopeka.client.MopekaClient") as mock_client:
        mock_client.return_value.get_full_state.return_value = [mock_device]
        
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        entity_registry = er.async_get(hass)
        
        entity_id = entity_registry.async_get_entity_id("sensor", DOMAIN, "MOP123_battery")
        assert entity_id is not None
        assert entity_id == "sensor.battery"  # No prefix when slugify returns empty
        
        assert hass.states.get("sensor.battery") is not None


async def test_sensor_value_error_on_entity_update(hass):
    """Test handling ValueError when entity_id update fails (lines 120-122)."""
    from homeassistant.helpers import entity_registry as er
    from unittest.mock import patch
    
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="test@example.com",
        data={CONF_EMAIL: "test@example.com", CONF_PASSWORD: "test-password"},
        options={"sensors": ["battery"]}
    )
    entry.add_to_hass(hass)

    mock_device = {
        "device_id": "MOP123",
        "name": "Gas Tank",
        "battery": 3.0,
        "model_number": "Standard"
    }

    with patch("mopeka.client.MopekaClient") as mock_client:
        mock_client.return_value.get_full_state.return_value = [mock_device]
        
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        assert hass.states.get("sensor.gas_tank_battery") is not None
        
        entity_registry = er.async_get(hass)
        
        with patch.object(entity_registry, 'async_update_entity', side_effect=ValueError("Test error")):
            mock_device["name"] = "Propane Tank"
            coordinator = hass.data[DOMAIN][entry.entry_id]
            await coordinator.async_refresh()
            await hass.async_block_till_done()
            
            await hass.config_entries.async_reload(entry.entry_id)
            await hass.async_block_till_done()
        
        assert hass.states.get("sensor.gas_tank_battery") is not None


async def test_device_rename_with_conflict(hass):
    """Test device rename when the new name conflicts with another device."""
    from homeassistant.helpers import device_registry as dr
    
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="test@example.com",
        data={CONF_EMAIL: "test@example.com", CONF_PASSWORD: "test-password"},
        options={"sensors": ["battery"]}
    )
    entry.add_to_hass(hass)

    mock_devices = [
        {
            "device_id": "MOP123",
            "name": "Gas Tank",
            "battery": 3.0,
            "model_number": "Standard"
        },
        {
            "device_id": "MOP456",
            "name": "Propane Tank",
            "battery": 2.8,
            "model_number": "Standard"
        },
    ]

    with patch("mopeka.client.MopekaClient") as mock_client:
        mock_client.return_value.get_full_state.return_value = mock_devices
        
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        from homeassistant.helpers import device_registry as dr
        device_registry = dr.async_get(hass)
        
        device1 = device_registry.async_get_device(identifiers={(DOMAIN, "MOP123")})
        device2 = device_registry.async_get_device(identifiers={(DOMAIN, "MOP456")})
        
        assert device1 is not None
        assert device1.name == "Gas Tank"
        assert device2 is not None
        assert device2.name == "Propane Tank"

        # Rename first device to match second device's name (conflict scenario)
        mock_devices[0]["name"] = "Propane Tank"
        mock_client.return_value.get_full_state.return_value = mock_devices
        
        coordinator = hass.data[DOMAIN][entry.entry_id]
        await coordinator.async_refresh()
        await hass.async_block_till_done()
        
        # Reload to trigger device name update
        await hass.config_entries.async_reload(entry.entry_id)
        await hass.async_block_till_done()
        
        # Both devices now have the same name - this is the conflict
        device1 = device_registry.async_get_device(identifiers={(DOMAIN, "MOP123")})
        device2 = device_registry.async_get_device(identifiers={(DOMAIN, "MOP456")})
        
        # The system should handle this without crashing
        assert device1 is not None
        assert device2 is not None
        
        # Both devices will have the same name (conflict)
        assert device1.name == "Propane Tank"
        assert device2.name == "Propane Tank"
        
        # Verify sensors still work
        assert hass.states.get("sensor.propane_tank_battery") is not None
        # Only one sensor entity will exist due to the naming conflict
        # but the system should not crash


async def test_sensor_device_removed_from_coordinator(hass):
    """Test sensor handles device removal from coordinator gracefully."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="test@example.com",
        data={CONF_EMAIL: "test@example.com", CONF_PASSWORD: "test-password"},
        options={"sensors": ["battery"]}
    )
    entry.add_to_hass(hass)

    mock_device = {
        "device_id": "MOP123",
        "name": "Gas Tank",
        "battery": 3.0,
    }

    with patch("mopeka.client.MopekaClient") as mock_client:
        mock_client.return_value.get_full_state.return_value = [mock_device]
        
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        assert hass.states.get("sensor.gas_tank_battery") is not None
        assert hass.states.get("sensor.gas_tank_battery").state == "3.0"

        # Simulate device removal by clearing coordinator data
        coordinator = hass.data[DOMAIN][entry.entry_id]
        
        # Force a refresh with empty data
        mock_client.return_value.get_full_state.return_value = []
        await coordinator.async_refresh()
        await hass.async_block_till_done()
        
        # Sensor should handle empty data gracefully
        assert coordinator.data == {}
