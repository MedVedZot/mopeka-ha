"""Tests for the Mopeka config flow."""
from unittest.mock import MagicMock, patch

from homeassistant import config_entries, data_entry_flow
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.mopeka_ha import DOMAIN, CONF_INTERVAL

async def test_form_user_success(hass):
    """Test we get the form and handle a successful user auth."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["step_id"] == "user"

    mock_devices = [{"device_id": "12345", "name": "Propane Tank", "battery_voltage": 3.0}]

    with patch("custom_components.mopeka_ha.config_flow._get_client") as mock_client:
        mock_client.return_value.get_full_state.return_value = mock_devices
        
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_EMAIL: "test@example.com", CONF_PASSWORD: "test-password"},
        )

        assert result2["type"] == data_entry_flow.FlowResultType.FORM
        assert result2["step_id"] == "sensors"
        assert result2["errors"] == {}

        with patch("custom_components.mopeka_ha.async_setup_entry", return_value=True):
            result3 = await hass.config_entries.flow.async_configure(
                result2["flow_id"],
                user_input={"battery_voltage (3.0)": True},
            )

    assert result3["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result3["title"] == "test@example.com"
    assert result3["data"][CONF_EMAIL] == "test@example.com"
    assert result3["data"][CONF_PASSWORD] == "test-password"
    assert "battery_voltage" in result3["options"]["sensors"]

async def test_form_user_cannot_connect(hass):
    """Test we handle cannot connect error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch("custom_components.mopeka_ha.config_flow._get_client") as mock_client:
        mock_client.return_value.get_full_state.side_effect = Exception("Connection drop")
        
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_EMAIL: "test@example.com", CONF_PASSWORD: "test-password"},
        )

    assert result2["type"] == data_entry_flow.FlowResultType.FORM
    assert result2["step_id"] == "user"
    assert result2["errors"] == {"base": "cannot_connect"}

async def test_form_user_invalid_auth(hass):
    """Test handling of invalid authentication."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch("custom_components.mopeka_ha.config_flow._get_client") as mock_client:
        mock_client.return_value.get_full_state.side_effect = Exception("401 Unauthorized")

        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_EMAIL: "test@example.com", CONF_PASSWORD: "wrong-password"},
        )

    assert result2["type"] == data_entry_flow.FlowResultType.FORM
    assert result2["errors"] == {"base": "invalid_auth"}

async def test_step_reconfigure(hass):
    """Test the reconfigure step."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_EMAIL: "test@example.com", CONF_PASSWORD: "old-password"},
        entry_id="mock_id",
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_RECONFIGURE, "entry_id": entry.entry_id},
    )
    assert result["step_id"] == "reconfigure"

    with patch("custom_components.mopeka_ha.config_flow._get_client") as mock_client:
        mock_client.return_value.get_full_state.return_value = []

        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_EMAIL: "test@example.com", CONF_PASSWORD: "new-password"},
        )

    assert result2["type"] == data_entry_flow.FlowResultType.ABORT
    assert result2["reason"] == "reconfigure_successful"
    assert entry.data[CONF_PASSWORD] == "new-password"

async def test_options_flow(hass):
    """Test the options flow."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_EMAIL: "test@example.com", CONF_PASSWORD: "test-pass"},
        options={"sensors": ["battery_voltage"], CONF_INTERVAL: 60},
    )
    entry.add_to_hass(hass)

    mock_coord = MagicMock()
    mock_coord.data = {"123": {"battery_voltage": 3.0, "fill_percent": 50}}
    hass.data[DOMAIN] = {entry.entry_id: mock_coord}

    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["step_id"] == "init"

    with patch("custom_components.mopeka_ha.config_flow._get_client") as mock_client:
        mock_client.return_value.get_full_state.return_value = []
        
        result2 = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={
                CONF_INTERVAL: 120,
                "battery_voltage (3.0)": True,
                "fill_percent (50)": True,
                CONF_PASSWORD: "new-secret-pass",
            },
        )

    assert result2["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert entry.options[CONF_INTERVAL] == 120
    assert "fill_percent" in entry.options["sensors"]
    assert entry.data[CONF_PASSWORD] == "new-secret-pass"


async def test_form_user_abort_flow(hass):
    """Test we handle flow abortion during setup."""
    from homeassistant.data_entry_flow import AbortFlow
    
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch("custom_components.mopeka_ha.config_flow._get_client") as mock_client:
        mock_client.return_value.get_full_state.side_effect = AbortFlow("test_abort")
        
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_EMAIL: "test@example.com", CONF_PASSWORD: "test-password"},
        )

    assert result2["type"] == data_entry_flow.FlowResultType.ABORT
    assert result2["reason"] == "test_abort"


async def test_form_user_no_sensors_selected(hass):
    """Test we handle no sensors selected."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch("custom_components.mopeka_ha.config_flow._get_client") as mock_client:
        mock_client.return_value.get_full_state.return_value = [{"device_id": "123", "name": "Tank"}]
        
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_EMAIL: "test@example.com", CONF_PASSWORD: "test-password"},
        )

        assert result2["type"] == data_entry_flow.FlowResultType.FORM
        assert result2["step_id"] == "sensors"

        result3 = await hass.config_entries.flow.async_configure(
            result2["flow_id"],
            user_input={},  # No sensors selected
        )

    assert result3["type"] == data_entry_flow.FlowResultType.FORM
    assert result3["step_id"] == "sensors"
    assert result3["errors"] == {"base": "no_sensors_selected"}


async def test_form_sensors_api_error(hass):
    """Test sensors step handles API errors gracefully."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch("custom_components.mopeka_ha.config_flow._get_client") as mock_client:
        mock_client.return_value.get_full_state.return_value = [{"device_id": "123", "name": "Tank", "battery_voltage": 3.0}]
        
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_EMAIL: "test@example.com", CONF_PASSWORD: "test-password"},
        )

        assert result2["type"] == data_entry_flow.FlowResultType.FORM
        assert result2["step_id"] == "sensors"

        with patch("custom_components.mopeka_ha.async_setup_entry", return_value=True):
            result3 = await hass.config_entries.flow.async_configure(
                result2["flow_id"],
                user_input={"battery_voltage (3.0)": True},
            )

    assert result3["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY


async def test_reconfigure_invalid_auth(hass):
    """Test reconfigure with invalid authentication."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_EMAIL: "test@example.com", CONF_PASSWORD: "old-password"},
        entry_id="mock_id",
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_RECONFIGURE, "entry_id": entry.entry_id},
    )
    assert result["step_id"] == "reconfigure"

    with patch("custom_components.mopeka_ha.config_flow._get_client") as mock_client:
        mock_client.return_value.get_full_state.side_effect = Exception("401 Unauthorized")

        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_EMAIL: "test@example.com", CONF_PASSWORD: "wrong-password"},
        )

    assert result2["type"] == data_entry_flow.FlowResultType.FORM
    assert result2["errors"] == {"base": "invalid_auth"}


async def test_reconfigure_cannot_connect(hass):
    """Test reconfigure with connection error."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_EMAIL: "test@example.com", CONF_PASSWORD: "old-password"},
        entry_id="mock_id",
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_RECONFIGURE, "entry_id": entry.entry_id},
    )
    assert result["step_id"] == "reconfigure"

    with patch("custom_components.mopeka_ha.config_flow._get_client") as mock_client:
        mock_client.return_value.get_full_state.side_effect = Exception("Connection failed")

        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_EMAIL: "test@example.com", CONF_PASSWORD: "test-password"},
        )

    assert result2["type"] == data_entry_flow.FlowResultType.FORM
    assert result2["errors"] == {"base": "cannot_connect"}


async def test_get_client_function(hass):
    """Test _get_client function creates MopekaClient with correct parameters."""
    from unittest.mock import patch
    from custom_components.mopeka_ha import API_DEFAULTS
    from custom_components.mopeka_ha.config_flow import _get_client
    
    test_data = {
        CONF_EMAIL: "test@example.com",
        CONF_PASSWORD: "test-password"
    }
    
    with patch("mopeka.client.MopekaClient") as mock_mopeka_client:
        client = _get_client(test_data)
        
        mock_mopeka_client.assert_called_once_with({
            "username": "test@example.com",
            "password": "test-password",
            **API_DEFAULTS
        })
        
        assert client is not None


async def test_options_flow_no_password_change(hass):
    """Test options flow without changing password."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_EMAIL: "test@example.com", CONF_PASSWORD: "test-pass"},
        options={"sensors": ["battery_voltage"], CONF_INTERVAL: 60},
    )
    entry.add_to_hass(hass)

    mock_coord = MagicMock()
    mock_coord.data = {"123": {"battery_voltage": 3.0}}
    hass.data[DOMAIN] = {entry.entry_id: mock_coord}

    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] == data_entry_flow.FlowResultType.FORM

    with patch("custom_components.mopeka_ha.config_flow._get_client") as mock_client:
        mock_client.return_value.get_full_state.return_value = []
        
        result2 = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={
                CONF_INTERVAL: 120,
                "battery_voltage (3.0)": True,
            },
        )

    assert result2["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert entry.options[CONF_INTERVAL] == 120
    assert entry.data[CONF_PASSWORD] == "test-pass"  # Password unchanged


async def test_reconfigure_abort_flow(hass):
    """Test reconfigure with flow abortion."""
    from homeassistant.data_entry_flow import AbortFlow
    
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_EMAIL: "test@example.com", CONF_PASSWORD: "old-password"},
        entry_id="mock_id",
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_RECONFIGURE, "entry_id": entry.entry_id},
    )
    assert result["step_id"] == "reconfigure"

    with patch("custom_components.mopeka_ha.config_flow._get_client") as mock_client:
        mock_client.return_value.get_full_state.side_effect = AbortFlow("test_abort")

        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_EMAIL: "test@example.com", CONF_PASSWORD: "test-password"},
        )

    assert result2["type"] == data_entry_flow.FlowResultType.ABORT
    assert result2["reason"] == "test_abort"


async def test_form_sensors_api_error_on_refresh(hass):
    """Test sensors step handles API errors gracefully on refresh."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch("custom_components.mopeka_ha.config_flow._get_client") as mock_client:
        mock_client.return_value.get_full_state.return_value = [{"device_id": "123", "name": "Tank", "battery_voltage": 3.0}]
        
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_EMAIL: "test@example.com", CONF_PASSWORD: "test-password"},
        )

        assert result2["type"] == data_entry_flow.FlowResultType.FORM
        assert result2["step_id"] == "sensors"

        mock_client.return_value.get_full_state.side_effect = Exception("API error")
        
        with patch("custom_components.mopeka_ha.async_setup_entry", return_value=True):
            result3 = await hass.config_entries.flow.async_configure(
                result2["flow_id"],
                user_input={"battery_voltage (3.0)": True},
            )

    assert result3["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY


async def test_form_sensors_empty_data(hass):
    """Test sensors step with empty device data."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch("custom_components.mopeka_ha.config_flow._get_client") as mock_client:
        mock_client.return_value.get_full_state.return_value = []
        
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_EMAIL: "test@example.com", CONF_PASSWORD: "test-password"},
        )

        assert result2["type"] == data_entry_flow.FlowResultType.FORM
        assert result2["step_id"] == "sensors"

        result3 = await hass.config_entries.flow.async_configure(
            result2["flow_id"],
            user_input={},
        )

    assert result3["type"] == data_entry_flow.FlowResultType.FORM
    assert result3["errors"] == {"base": "no_sensors_selected"}


async def test_options_flow_invalid_auth(hass):
    """Test options flow with invalid authentication."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_EMAIL: "test@example.com", CONF_PASSWORD: "test-pass"},
        options={"sensors": ["battery_voltage"], CONF_INTERVAL: 60},
    )
    entry.add_to_hass(hass)

    mock_coord = MagicMock()
    mock_coord.data = {"123": {"battery_voltage": 3.0}}
    hass.data[DOMAIN] = {entry.entry_id: mock_coord}

    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] == data_entry_flow.FlowResultType.FORM

    with patch("custom_components.mopeka_ha.config_flow._get_client") as mock_client:
        mock_client.return_value.get_full_state.side_effect = Exception("401 Unauthorized")
        
        result2 = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={
                CONF_INTERVAL: 120,
                "battery_voltage (3.0)": True,
                CONF_PASSWORD: "new-pass",
            },
        )

    assert result2["type"] == data_entry_flow.FlowResultType.FORM
    assert result2["errors"] == {"base": "invalid_auth"}


async def test_options_flow_cannot_connect(hass):
    """Test options flow with connection error."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_EMAIL: "test@example.com", CONF_PASSWORD: "test-pass"},
        options={"sensors": ["battery_voltage"], CONF_INTERVAL: 60},
    )
    entry.add_to_hass(hass)

    mock_coord = MagicMock()
    mock_coord.data = {"123": {"battery_voltage": 3.0}}
    hass.data[DOMAIN] = {entry.entry_id: mock_coord}

    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] == data_entry_flow.FlowResultType.FORM

    with patch("custom_components.mopeka_ha.config_flow._get_client") as mock_client:
        mock_client.return_value.get_full_state.side_effect = Exception("Connection failed")
        
        result2 = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={
                CONF_INTERVAL: 120,
                "battery_voltage (3.0)": True,
                CONF_PASSWORD: "new-pass",
            },
        )

    assert result2["type"] == data_entry_flow.FlowResultType.FORM
    assert result2["errors"] == {"base": "cannot_connect"}


async def test_options_flow_coordinator_data_empty(hass):
    """Test options flow when coordinator data is empty."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_EMAIL: "test@example.com", CONF_PASSWORD: "test-pass"},
        options={"sensors": ["battery_voltage"], CONF_INTERVAL: 60},
    )
    entry.add_to_hass(hass)

    mock_coord = MagicMock()
    mock_coord.data = {}  # Empty data
    hass.data[DOMAIN] = {entry.entry_id: mock_coord}

    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] == data_entry_flow.FlowResultType.FORM

    # Should not crash, just show form with n/a values - must select at least one sensor
    with patch("custom_components.mopeka_ha.config_flow._get_client") as mock_client:
        mock_client.return_value.get_full_state.return_value = []
        
        result2 = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={
                CONF_INTERVAL: 120,
                CONF_PASSWORD: "new-pass",
                "battery_voltage (n/a)": True,  # Select at least one sensor
            },
        )

    assert result2["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY


async def test_get_combined_states():
    """Test _get_combined_states function."""
    from custom_components.mopeka_ha.config_flow import _get_combined_states

    states_list = [
        {"device_id": "123", "battery_voltage": 3.0, "fill_percent": 50},
        {"device_id": "456", "battery_voltage": 2.8},
        {"device_id": "789", "fill_percent": 75, "temperature_c": 20.5},
    ]

    combined = _get_combined_states(states_list)

    assert combined["battery_voltage"] == 3.0
    assert combined["fill_percent"] == 50
    assert combined["temperature_c"] == 20.5

    states_list[1]["battery_voltage"] = "n/a"
    combined = _get_combined_states(states_list)

    assert combined["battery_voltage"] == 3.0

    states_list[0]["battery_voltage"] = None
    combined = _get_combined_states(states_list)

    assert "battery_voltage" not in combined or combined["battery_voltage"] == "n/a"


async def test_get_combined_states_empty_list():
    """Test _get_combined_states with empty states list."""
    from custom_components.mopeka_ha.config_flow import _get_combined_states

    states_list = []
    combined = _get_combined_states(states_list)

    assert combined == {}


async def test_get_combined_states_all_none():
    """Test _get_combined_states when all devices have None values."""
    from custom_components.mopeka_ha.config_flow import _get_combined_states

    states_list = [
        {"device_id": "123", "battery_voltage": None, "fill_percent": None},
        {"device_id": "456", "battery_voltage": None, "temperature_c": None},
    ]

    combined = _get_combined_states(states_list)

    assert combined == {}


async def test_get_combined_states_all_na():
    """Test _get_combined_states when all devices have n/a values."""
    from custom_components.mopeka_ha.config_flow import _get_combined_states

    states_list = [
        {"device_id": "123", "battery_voltage": "n/a", "fill_percent": "n/a"},
        {"device_id": "456", "battery_voltage": "n/a", "temperature_c": "n/a"},
    ]

    combined = _get_combined_states(states_list)

    # "n/a" values are included when no better value exists
    assert combined["battery_voltage"] == "n/a"
    assert combined["fill_percent"] == "n/a"
    assert combined["temperature_c"] == "n/a"


async def test_get_combined_states_mixed_values():
    """Test _get_combined_states with mix of valid, None, and n/a values."""
    from custom_components.mopeka_ha.config_flow import _get_combined_states

    states_list = [
        {"device_id": "123", "battery_voltage": 3.0, "fill_percent": None},
        {"device_id": "456", "battery_voltage": "n/a", "fill_percent": 50},
        {"device_id": "789", "battery_voltage": 2.5, "fill_percent": "n/a"},
    ]

    combined = _get_combined_states(states_list)

    assert combined["battery_voltage"] == 3.0  # First valid value
    assert combined["fill_percent"] == 50  # First valid value


async def test_get_combined_states_filters_static_sensors():
    """Test _get_combined_states only includes STATIC_SENSORS keys."""
    from custom_components.mopeka_ha.config_flow import _get_combined_states

    states_list = [
        {
            "device_id": "123",
            "battery_voltage": 3.0,
            "fill_percent": 50,
            "custom_field": "value",  # Not in STATIC_SENSORS
            "random_key": 123,  # Not in STATIC_SENSORS
        },
    ]

    combined = _get_combined_states(states_list)

    assert "battery_voltage" in combined
    assert "fill_percent" in combined
    assert "custom_field" not in combined
    assert "random_key" not in combined
