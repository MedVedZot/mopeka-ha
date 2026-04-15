"""Tests for Mopeka integration initialization."""
from unittest.mock import patch
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from pytest_homeassistant_custom_component.common import MockConfigEntry
from custom_components.mopeka_ha import DOMAIN

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
    entry1.add_to_hass(hass)
    entry2.add_to_hass(hass)

    mock_device1 = {"device_id": "MOP123", "name": "Gas Tank 1", "battery": 3.0}
    mock_device2 = {"device_id": "MOP456", "name": "Gas Tank 2", "battery": 2.5}

    with patch("mopeka.client.MopekaClient") as mock_client:
        mock_client.return_value.get_full_state.return_value = [mock_device1]
        
        assert await hass.config_entries.async_setup(entry1.entry_id)
        await hass.async_block_till_done()

        mock_client.return_value.get_full_state.return_value = [mock_device2]
        assert await hass.config_entries.async_setup(entry2.entry_id)
        await hass.async_block_till_done()

        assert hass.states.get("sensor.gas_tank_1_battery") is not None
        assert hass.states.get("sensor.gas_tank_2_battery") is not None

        assert hass.states.get("sensor.gas_tank_1_battery").state == "3.0"
        assert hass.states.get("sensor.gas_tank_2_battery").state == "2.5"

        coordinator1 = hass.data[DOMAIN][entry1.entry_id]
        coordinator2 = hass.data[DOMAIN][entry2.entry_id]
        assert coordinator1 is not coordinator2
        assert coordinator1.data.keys() != coordinator2.data.keys()

        assert entry.state is ConfigEntryState.NOT_LOADED


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
