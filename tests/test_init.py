"""Tests for Mopeka integration initialization."""
from unittest.mock import patch
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from pytest_homeassistant_custom_component.common import MockConfigEntry
from custom_components.mopeka_ha import DOMAIN, CONF_INTERVAL

async def test_setup_and_unload_entry(hass):
    """Test setting up and unloading the integration."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="test@example.com",
        data={CONF_EMAIL: "test@example.com", CONF_PASSWORD: "test-password"},
        options={"sensors": ["battery"]}
    )
    entry.add_to_hass(hass)

    with patch("mopeka.client.MopekaClient") as mock_client:
        mock_client.return_value.get_full_state.return_value = [{"device_id": "123", "battery": 3.0}]
        
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        assert entry.state is ConfigEntryState.LOADED

        assert await hass.config_entries.async_unload(entry.entry_id)
        await hass.async_block_till_done()


async def test_multiple_accounts(hass):
    """Test that multiple Mopeka accounts can be added simultaneously."""
    entry1 = MockConfigEntry(
        domain=DOMAIN,
        title="user1@example.com",
        data={CONF_EMAIL: "user1@example.com", CONF_PASSWORD: "test-pass-1"},
        options={"sensors": ["battery"]}
    )
    entry2 = MockConfigEntry(
        domain=DOMAIN,
        title="user2@example.com",
        data={CONF_EMAIL: "user2@example.com", CONF_PASSWORD: "test-pass-2"},
        options={"sensors": ["battery"]}
    )

    mock_device1 = {"device_id": "MOP123", "name": "Gas Tank 1", "battery": 3.0}
    mock_device2 = {"device_id": "MOP456", "name": "Gas Tank 2", "battery": 2.5}

    with patch("mopeka.client.MopekaClient") as mock_client:
        mock_client.return_value.get_full_state.side_effect = [[mock_device1], [mock_device2]]
        
        entry1.add_to_hass(hass)
        assert await hass.config_entries.async_setup(entry1.entry_id)
        await hass.async_block_till_done()

        entry2.add_to_hass(hass)
        assert await hass.config_entries.async_setup(entry2.entry_id)
        await hass.async_block_till_done()

        assert hass.states.get("sensor.gas_tank_1_battery") is not None
        assert hass.states.get("sensor.gas_tank_2_battery") is not None


async def test_setup_entry_api_error(hass):
    """Test setup entry handles API errors gracefully."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="test@example.com",
        data={CONF_EMAIL: "test@example.com", CONF_PASSWORD: "test-password"},
        options={"sensors": ["battery"]}
    )
    entry.add_to_hass(hass)

    with patch("mopeka.client.MopekaClient") as mock_client:
        mock_client.return_value.get_full_state.side_effect = [
            [{"device_id": "123", "battery": 3.0}],
            Exception("API connection failed")
        ]
        
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        assert entry.state is ConfigEntryState.LOADED

        coordinator = hass.data[DOMAIN][entry.entry_id]
        await coordinator.async_refresh()
        await hass.async_block_till_done()

        assert await hass.config_entries.async_unload(entry.entry_id)
        await hass.async_block_till_done()


async def test_reload_entry(hass):
    """Test reloading the integration when config is updated."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="test@example.com",
        data={CONF_EMAIL: "test@example.com", CONF_PASSWORD: "test-password"},
        options={"sensors": ["battery"]}
    )
    entry.add_to_hass(hass)

    with patch("mopeka.client.MopekaClient") as mock_client:
        mock_client.return_value.get_full_state.return_value = [{"device_id": "123", "battery": 3.0}]
        
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        assert entry.state is ConfigEntryState.LOADED

        from custom_components.mopeka_ha import async_reload_entry
        await async_reload_entry(hass, entry)
        await hass.async_block_till_done()

        assert entry.state is ConfigEntryState.LOADED

        assert await hass.config_entries.async_unload(entry.entry_id)
        await hass.async_block_till_done()


async def test_empty_api_response(hass):
    """Test handling of empty API response."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="test@example.com",
        data={CONF_EMAIL: "test@example.com", CONF_PASSWORD: "test-password"},
        options={"sensors": ["battery"]}
    )
    entry.add_to_hass(hass)

    with patch("mopeka.client.MopekaClient") as mock_client:
        mock_client.return_value.get_full_state.return_value = []
        
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        assert entry.state is ConfigEntryState.LOADED
        assert hass.data[DOMAIN][entry.entry_id].data == {}


async def test_invalid_interval_values(hass):
    """Test handling of invalid interval values."""
    from custom_components.mopeka_ha import DEFAULT_INTERVAL
    
    # Test interval = 0
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="test@example.com",
        data={CONF_EMAIL: "test@example.com", CONF_PASSWORD: "test-password"},
        options={CONF_INTERVAL: 0}
    )
    entry.add_to_hass(hass)

    with patch("mopeka.client.MopekaClient") as mock_client:
        mock_client.return_value.get_full_state.return_value = [{"device_id": "123", "battery": 3.0}]
        
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        # Should use default interval
        coordinator = hass.data[DOMAIN][entry.entry_id]
        assert coordinator.update_interval.total_seconds() == DEFAULT_INTERVAL * 60
    
    # Test interval = -1
    entry2 = MockConfigEntry(
        domain=DOMAIN,
        title="test2@example.com",
        data={CONF_EMAIL: "test2@example.com", CONF_PASSWORD: "test-password"},
        options={CONF_INTERVAL: -1}
    )
    entry2.add_to_hass(hass)

    with patch("mopeka.client.MopekaClient") as mock_client:
        mock_client.return_value.get_full_state.return_value = [{"device_id": "456", "battery": 2.5}]
        
        assert await hass.config_entries.async_setup(entry2.entry_id)
        await hass.async_block_till_done()

        coordinator2 = hass.data[DOMAIN][entry2.entry_id]
        assert coordinator2.update_interval.total_seconds() == DEFAULT_INTERVAL * 60
    
    # Test interval as string
    entry3 = MockConfigEntry(
        domain=DOMAIN,
        title="test3@example.com",
        data={CONF_EMAIL: "test3@example.com", CONF_PASSWORD: "test-password"},
        options={CONF_INTERVAL: "invalid"}
    )
    entry3.add_to_hass(hass)

    with patch("mopeka.client.MopekaClient") as mock_client:
        mock_client.return_value.get_full_state.return_value = [{"device_id": "789", "battery": 2.8}]
        
        assert await hass.config_entries.async_setup(entry3.entry_id)
        await hass.async_block_till_done()

        coordinator3 = hass.data[DOMAIN][entry3.entry_id]
        assert coordinator3.update_interval.total_seconds() == DEFAULT_INTERVAL * 60
