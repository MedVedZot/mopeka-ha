# Mopeka HA Integration

<p align="left">
  <a href="https://buymeacoffee.com/MedVedZot">
    <img src="https://img.buymeacoffee.com/button-api/?text=Buy%20me%20a%20coffee&slug=MedVedZot&button_colour=FFDD00&font_colour=000000&font_family=Arial&outline_colour=000000&coffee_colour=ffffff" />
  </a>
</p>
No subscriptions. Just support if you find value.
<br/><br/>

Home Assistant custom integration for Mopeka ultrasonic propane tank sensors via Mopeka Cloud API.

![Version](https://img.shields.io/badge/version-1.2.5-blue)
![Home Assistant](https://img.shields.io/badge/HA-2024.1.0%2B-green)
![License](https://img.shields.io/badge/license-MIT-orange)

## Features

- 📊 **Dynamic Sensor Creation** - Automatically discovers available sensors from API
- ☁️ **Cloud API Integration** - Works with Mopeka WiFi gateways (Bluetooth not required)
- 🔐 **Secure Authentication** - Uses your Mopeka account credentials
- 🔄 **Automatic Updates** - Data refreshes every 1 minute
- 📱 **Multiple Sensors** - Choose which sensors to create for each tank
- 📈 **Historical Data** - State class MEASUREMENT for history graphs
- 🎛️ **Customizable** - Add/remove sensors anytime via Options Flow
- 👥 **Multiple Accounts** - Add multiple Mopeka accounts simultaneously

## Requirements

- Home Assistant 2024.1.0 or newer
- Mopeka account with at least one sensor connected via WiFi gateway
- Network access to Mopeka Cloud API

## Installation

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=MedVedZot&repository=mopeka-ha&category=integration)

### Via HACS (Recommended)

1. Open HACS in Home Assistant
2. Go to **Integrations**
3. Click the **three dots menu** → **Custom repositories**
4. Add this repository: `https://github.com/MedVedZot/mopeka-ha.git`
5. Select category: **Integration**
6. Click **Add**
7. Go to **Integrations** and search for "Mopeka HA"
8. Click **Install**
9. Restart Home Assistant

### Manual Installation

1. Copy the `custom_components/mopeka_ha` folder to your Home Assistant `custom_components` directory
2. Install the required dependency:
   ```bash
   pip install mopeka-api==1.0.2
   ```
3. Restart Home Assistant
4. Go to **Settings** → **Devices & Services** → **Add Integration**
5. Search for "Mopeka HA"

## Multiple Accounts

This integration supports adding multiple Mopeka accounts simultaneously. This is useful for:

- Managing sensors at different locations
- Sharing access between different users
- Separating business and personal accounts

### Adding Another Account

To add a second (or third) Mopeka account:

1. Go to **Settings** → **Devices & Services**
2. Click **Add Integration**
3. Search for "Mopeka HA"
4. Enter the credentials for the new account
5. Select sensors for the new account
6. Click **Submit**

Each account will create separate devices and sensors with their own configuration.

### Managing Multiple Accounts

- Each account is independent with its own settings
- You can have different sensor selections for each account
- Each account uses its own update interval
- Removing one account won't affect others

## Configuration

### Step 1: Add Integration

1. After adding the integration, you'll be prompted to enter your Mopeka credentials:
   - **Email**: Your Mopeka account email
   - **Password**: Your Mopeka account password

### Step 2: Select Sensors

2. The integration will automatically:
   - Authenticate with Mopeka Cloud API
   - Discover all sensors available from the API
   - Show you a list of available sensors to create

3. **Select the sensors you want** (at least one must be selected):
   - ✅ `fill_percent` - Tank level in percentage
   - ✅ `temperature_c` - Temperature in Celsius
   - ✅ `temperature_f` - Temperature in Fahrenheit
   - ✅ `battery_voltage` - Battery voltage
   - ✅ `level_cm` - Liquid level in centimeters
   - ✅ `level_inches` - Liquid level in inches
   - ✅ `volume_liters` - Volume in liters
   - ✅ `volume_gallons_us` - Volume in US gallons
   - ✅ `volume_original_unit` - Original volume unit
   - ✅ `tank_type` - Tank type (e.g., "500L")
   - ✅ `tank_height` - Tank height in meters
   - ✅ `vertical` - Tank orientation (true/false)
   - ✅ `propaneButaneRatio` - Propane to butane ratio
   - ✅ `signal_quality` - Signal quality in percentage
   - ✅ `updated_human_readable` - Last update time

4. Click **Submit** to create the integration

### Step 3: Sensors Created

The integration will automatically create sensor entities for each selected field on each tank:

**Example entity names** (for a tank named "Main Propane Tank"):
- `sensor.main_propane_tank_fill_percent`
- `sensor.main_propane_tank_temperature_c`
- `sensor.main_propane_tank_battery_voltage`
- `sensor.main_propane_tank_volume_liters`

## Modifying Sensor Selection

You can add or remove sensors at any time without reinstalling the integration:

1. Go to **Settings** → **Devices & Services**
2. Find **Mopeka HA** integration
3. Click **Configure** (three dots → Configure)
4. Select/deselect sensors as needed
5. Optionally, change the **Update Interval** (in minutes)
6. Optionally, update your **Mopeka password** if it has changed
7. Click **Submit**
8. The integration will automatically add/remove sensor entities

### Changing Credentials

You can update your Mopeka account credentials at any time:

1. Go to **Settings** → **Devices & Services**
2. Find **Mopeka HA** integration
3. Click **Configure** (three dots → Configure)
4. Enter your new **Email** and **Password**
5. Click **Submit**
6. The integration will verify the new credentials and continue working

### Reconfigure Flow

Alternatively, use the Reconfigure option:

1. Go to **Settings** → **Devices & Services**
2. Find **Mopeka HA** integration
3. Click **Reconfigure** (three dots → Reconfigure)
4. Update your email and password
5. Click **Submit**
6. The integration will recreate with the same unique ID but new credentials

**Note**: The sensor selection form displays current sensor values from the API (shown in parentheses), helping you identify which sensors to select.

## Available Sensors

### Sensor Types

The integration automatically determines the sensor type based on the field name and value:

- **Temperature Sensors** - For fields containing "temp" (auto-detects °C or °F)
- **Voltage Sensors** - For fields containing "voltage"
- **Volume Sensors** - For fields containing "volume", "gallon", or "liter"
- **Distance Sensors** - For fields containing "level" or "height"
- **Percentage Sensors** - For fields containing "percent" or values 0-100
- **Text Sensors** - For other fields (shows as text)

### Device Information

The following fields are used for **device identification** and **metadata** (not created as sensors):

These are technical fields that identify and describe the physical device itself:

**Identification Fields:**
- `device_id` - Technical device identifier (also used as serial_number)
- `wifi_gate_id` - WiFi gateway ID (also used as hardware version)
- `brand` - Sensor brand ("tankcheck", used as manufacturer)
- `model_number` - Sensor model number (used as device model)

**Device Metadata:**
- `name` - Device name (displayed in Home Assistant, also used for entity ID prefix)
- `timestamp_iso` - Last update timestamp in ISO format
- `history_start_date` - Historical data start date
- `history_depth_days` - Historical data retention period

**Note**: These fields are automatically populated into the device's information:
- `serial_number` = `device_id`
- `hw_version` = `wifi_gate_id`
- `manufacturer` = `brand`
- `model` = `model_number`

**Important**: These fields are separate from sensor data fields (like `battery_voltage`, `temperature_c`, etc.) which represent measurements and state data. Device identification fields are used to uniquely identify and describe the physical sensor device itself.

### Entity Naming

Sensor entities use a hierarchical naming scheme for better organization:

**Device Name + Sensor Type**

The integration uses `has_entity_name = True`, which means:

- **Device name** = Name you give your tank in the Mopeka app (e.g., "Gas Tank")
- **Sensor name** = Automatically formatted from the sensor key (e.g., "Battery Voltage")
- **Entity name** = Combined: "Gas Tank Battery Voltage"

**Examples:**

| Device Name | Sensor Key | Entity Name | Entity ID |
|-------------|-------------|--------------|------------|
| Gas Tank | `battery_voltage` | Gas Tank Battery Voltage | `sensor.gas_tank_battery_voltage` |
| Propane Tank | `fill_percent` | Propane Tank Fill Percent | `sensor.propanetank_fill_percent` |
| BBQ Grill | `temperature_c` | BBQ Grill Temperature C | `sensor.bbqgrill_temperature_c` |

**Key Benefits:**
- Easy to identify which sensor belongs to which tank
- Consistent naming across all entities
- Automatic formatting of sensor names (camelCase → readable text)
- Entity ID uses `slugify()` for safe identifiers

## Troubleshooting

### Integration Not Connecting

1. Verify your Mopeka credentials are correct
2. Ensure your sensors are connected via WiFi gateway (not just Bluetooth)
3. Check network connectivity to Mopeka Cloud API
4. Review Home Assistant logs for error messages

### No Sensors Found

- Make sure you have at least one Mopeka sensor linked to your account
- Verify your sensors are connected via WiFi gateway
- Check that your sensors are configured in the Mopeka app

### Data Not Updating

- Default update interval is 1 minute
- Check Home Assistant logs for API errors
- Verify your Mopeka account is active

### Sensor Not Created

- Ensure the sensor field was selected during configuration
- Check that the field exists in the API response for your device
- Review Home Assistant logs for errors

### Entity ID Not Updated After Renaming

If you rename a device in the Mopeka app but the entity ID doesn't change:

- **Normal behavior**: Entity ID updates occur during integration reload
- **Conflict detected**: If the new entity ID is already used, the update is skipped
- **Empty name**: If the device name contains only special characters, no prefix is added (e.g., `sensor.battery`)
- Check Home Assistant logs for debug messages about entity ID updates

### Integration Shows "Cannot Connect"

This error typically indicates:

- Incorrect Mopeka credentials
- Network connectivity issues to Mopeka Cloud API
- Your sensors are not connected via WiFi gateway (Bluetooth-only sensors won't work)
- Mopeka API service is temporarily unavailable

### Errors in Home Assistant Logs

Look for these specific error messages:

- `"API Error: ..."` - General API communication issue
- `"invalid_auth"` - Wrong username or password
- `"cannot_connect"` - Network or API connectivity issue
- `"no_sensors_selected"` - Must select at least one sensor

## Advanced Configuration

### Update Interval

The update interval can be changed in two ways:

**Via UI (Recommended):**
1. Go to **Settings** → **Devices & Services**
2. Find **Mopeka HA** integration
3. Click **Configure** (three dots → Configure)
4. Change the **Update Interval** value (in minutes)
5. Click **Submit**

**Via Code:**
To change the default interval, modify `custom_components/mopeka_ha/__init__.py`:

```python
DEFAULT_INTERVAL = 1  # Change this value (in minutes)
```

### API Configuration

The integration uses hardcoded Mopeka API credentials. These are configured automatically and should not need modification.

## Dynamic Sensor System

This integration uses a dynamic sensor system that automatically adapts to changes in the Mopeka API:

- **New fields** in API → automatically appear in sensor selection
- **Removed fields** in API → automatically removed from options
- **No hardcoding** → all sensors discovered from actual API data
- **User control** → you choose which sensors to create

### Entity ID Management

The integration automatically manages entity IDs when device names change:

- **Automatic updates**: If you rename a device in the Mopeka app, entity IDs are automatically updated
  - Example: `sensor.gas_tank_battery` → `sensor.propane_tank_battery`
- **Safe identifiers**: Uses `slugify()` to create valid entity IDs
- **Conflict handling**: Automatically skips updates if the new entity ID is already registered
- **Graceful fallback**: If an error occurs during entity ID update, it's logged without breaking the integration

### Sensor Lifecycle

- **Removal**: When you deselect a sensor in options, the corresponding entity is automatically removed from Home Assistant
- **Preservation**: Selected sensors maintain their data and configuration even when other sensors are added/removed

This ensures the integration stays compatible with future Mopeka API updates without code changes.

## Technical Details

### Integration Type

- **Type**: Hub-based integration (`integration_type: "hub"`)
- **IoT Class**: Cloud Polling (`iot_class: "cloud_polling"`)
- **API Region**: AWS us-east-1
- **API Timeout**: 20 seconds

### Performance Characteristics

- **Default Update Interval**: 1 minute (60 seconds)
- **Minimum Interval**: 1 minute
- **Recommended Interval**: 1-5 minutes depending on your needs
- **Connection Timeout**: 20 seconds
- **API Calls**: One call per account per interval

### Dependencies

- **mopeka-api**: 1.0.2 (Python library for Mopeka Cloud API)
- **Home Assistant**: 2024.1.0 or newer

## Architecture

### Component Structure

```
custom_components/mopeka_ha/
├── __init__.py          # Main integration setup and coordinator
├── config_flow.py        # Configuration UI flow
├── sensor.py            # Sensor entity definitions
├── manifest.json         # Integration metadata
└── translations/         # Localization strings
```

### Data Flow

```
┌─────────────────┐
│   User Input    │  Credentials, sensor selection
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Config Flow    │  Validates credentials, discovers sensors
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Coordinator   │  Polls Mopeka API periodically
│  (Polling)      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Mopeka Cloud   │  Returns sensor data
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Sensors       │  Display data in Home Assistant
│  (Entities)     │
└─────────────────┘
```

### Key Patterns

**Coordinator Pattern:**
- Centralized data fetching from Mopeka API
- Automatic retry logic with error handling
- Configurable update interval
- State management for all sensors

**Entity Management:**
- Dynamic sensor creation based on API data
- Automatic entity ID updates on device rename
- Graceful cleanup of deselected sensors
- Conflict detection and resolution

**Device Registry:**
- Automatic device creation for each sensor
- Device name synchronization with Mopeka API
- Manufacturer, model, and serial number mapping

### State Management

1. **Initialization**: Config flow authenticates and discovers sensors
2. **Setup**: Coordinator starts periodic polling (default: 1 minute)
3. **Updates**: All sensors refresh simultaneously on coordinator update
4. **Changes**: Device renames trigger entity ID updates
5. **Cleanup**: Deselected sensors are removed automatically

## Development

This integration uses the [mopeka-api](https://github.com/MedVedZot/mopeka-api) Python library to communicate with the Mopeka Cloud.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Disclaimer

This project is not affiliated with or endorsed by Mopeka IoT. Use it with your own Mopeka account and devices only.

## License

MIT License - see [LICENSE](LICENSE) for details.

## Support

- 📋 [Issues](https://github.com/MedVedZot/mopeka-ha/issues)
- 💬 [Discussions](https://github.com/MedVedZot/mopeka-ha/discussions)
- ☕ [Buy me a coffee](https://buymeacoffee.com/MedVedZot)