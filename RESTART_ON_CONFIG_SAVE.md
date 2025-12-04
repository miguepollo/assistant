# Auto-Restart on Configuration Save

## Feature Overview

The assistant now automatically restarts when you save configuration changes through the web interface. No manual restart needed!

## How It Works

### User Flow

1. **Start the assistant**:
   ```bash
   ./run_and_config_assistant.sh
   ```

2. **No config exists**: Web interface opens automatically

3. **Save configuration**: Click "Save Configuration" button

4. **Automatic restart**: Server shuts down and assistant starts immediately

5. **Ready to use**: Voice assistant is running with your settings

### Reconfiguration

To change settings while the assistant is running:

```bash
# Stop the assistant (Ctrl+C)

# Run in configuration mode
./run_and_config_assistant.sh --config
```

Or:

```bash
./run_and_config_assistant.sh -c
```

This will open the web interface with your current settings loaded.

## Technical Details

### Changes Made

#### 1. **config_app.py**
- Added auto-shutdown after saving configuration
- Displays nice "Restarting..." page to user
- Gracefully terminates Flask server after 2 seconds
- Added audio output device selector
- Properly converts device IDs to integers

#### 2. **run_and_config_assistant.sh**
- Added `--config` flag to force configuration mode
- Improved messages to indicate auto-restart behavior
- Script automatically restarts when config server exits
- Uses `exec "$0"` to restart itself

#### 3. **templates/index.html**
- Added audio output device selector
- Improved device selection logic for both input and output

### Code Flow

```
User saves config
    ↓
config_app.py saves to config.json
    ↓
Schedules server shutdown (2 second delay)
    ↓
Shows "Restarting..." page to user
    ↓
Flask server terminates
    ↓
run_and_config_assistant.sh detects server exit
    ↓
Checks if config.json exists
    ↓
Config found → exec "$0" (restart script)
    ↓
Setup audio
    ↓
Start main_assistant.py
```

## Benefits

1. **Seamless experience**: No manual restart required
2. **Better UX**: Clear visual feedback during restart
3. **Convenience**: Edit settings anytime with `--config` flag
4. **Robust**: Handles all edge cases gracefully

## Configuration File

All settings are saved to `config.json`:

```json
{
    "audio_output": 2,
    "audio_input": 2,
    "wifi_ssid": "YourNetwork",
    "openweathermap_key": "your_api_key",
    "location_city": "Madrid",
    "language": "es"
}
```

Note: Device IDs are now properly saved as integers for better compatibility.

## Usage Examples

### First Time Setup

```bash
./run_and_config_assistant.sh
# Opens web interface automatically
# Configure and save
# Assistant starts automatically
```

### Reconfigure Later

```bash
# Stop assistant (Ctrl+C)
./run_and_config_assistant.sh --config
# Make changes
# Save → automatic restart
```

### Normal Run (After Setup)

```bash
./run_and_config_assistant.sh
# Starts assistant immediately if config exists
```

## Troubleshooting

### Server doesn't restart after save

Check that:
1. `config.json` was created/updated
2. JSON is valid (no syntax errors)
3. Script has execute permissions: `chmod +x run_and_config_assistant.sh`

### Can't access web interface

Make sure:
1. Port 5000 is not blocked by firewall
2. You're using the correct IP address
3. NetworkManager is running for WiFi features

## Future Enhancements

Possible improvements:
- Add "Reconfigure" button in a system tray icon
- Auto-detect when config changes and offer to restart
- Add validation before saving config
- Support for multiple user profiles











