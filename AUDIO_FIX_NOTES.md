# Audio and Wake Word Fixes

## Changes Made

### 1. Wake Word Sensitivity (False Positives)

**Problem**: Wake word was triggering too frequently due to low threshold.

**Solution**:
- Increased `WAKE_WORD_THRESHOLD` from 0.5 to 0.7 (higher = less sensitive)
- Added `WAKE_WORD_COOLDOWN` of 2 seconds to prevent immediate re-triggering
- Implemented cooldown logic in main loop to track last detection time

### 2. Audio Output Issues (No Sound)

**Problem**: Audio playback was failing - no sound output.

**Root Cause**: The speaker hardware switch (`spk switch`) on card 2 was OFF.

**Solutions Applied**:
- Fixed config.json: Changed audio_input from 0 to 2 (only card 2 has capture)
- Created `setup_audio.sh` script to enable speaker switch automatically
- Created `run_assistant.sh` wrapper script that sets up audio before starting
- Added buffer parameter `-B 500000` to aplay commands for better buffering
- Added stderr redirection `2>/dev/null` to suppress ALSA warnings
- Improved error handling in all audio functions
- Added delays after audio playback to ensure device release
- Better pipe error detection in streaming mode

## Running the Assistant

### Recommended Method

```bash
./run_and_config_assistant.sh
```

This script will:
1. Check if configuration exists, if not, start web config interface
2. Enable the speaker hardware switch automatically
3. Start the assistant

### Manual Method

If you need to run directly:

```bash
# Enable audio first
amixer -c 2 sset "spk switch" on

# Then run the assistant
python3 main_assistant.py
```

## Testing

### Run Audio Device Test

```bash
./test_audio.sh
```

This will:
- List all available audio devices
- Test playback on default and configured devices
- Test recording and playback

### Verify Device Configuration

Check which devices are available:

```bash
# List playback devices
aplay -l

# List capture devices
arecord -l
```

Your Orange Pi configuration:
- `audio_output`: 2 (ES8388 codec - speakers)
- `audio_input`: 2 (ES8388 codec - microphone)

### Check Speaker Status

If audio stops working after reboot:

```bash
# Check if speaker switch is on
amixer -c 2 sget "spk switch"

# Enable it if off
amixer -c 2 sset "spk switch" on
```

### Adjust Wake Word Sensitivity

If still getting false positives, edit `main_assistant.py`:

```python
WAKE_WORD_THRESHOLD = 0.8  # Even less sensitive (range: 0.5-0.9)
WAKE_WORD_COOLDOWN = 3.0   # Longer cooldown period
```

If wake word is not detected at all, lower the threshold:

```python
WAKE_WORD_THRESHOLD = 0.6  # More sensitive
```

## Common Issues

### Issue: Audio still not working

1. Check if the audio device is correct:
   ```bash
   aplay -l  # Note the card and device numbers
   ```

2. Test direct playback:
   ```bash
   aplay -D plughw:2,0 beep.wav
   ```

3. If different card needed, update config.json

### Issue: Wake word not detecting

- Lower threshold in main_assistant.py
- Check microphone input level
- Verify correct input device in config.json

### Issue: Too many false wake word triggers

- Increase threshold in main_assistant.py
- Increase cooldown period
- Check for background noise interfering

## Additional Recommendations

1. **Audio Device Selection**: If plughw:2,0 doesn't work, try:
   - Default device: Remove or comment out audio_output in config.json
   - Different card: Change number in config.json

2. **Microphone Quality**: Ensure good microphone placement and minimal background noise

3. **System Audio**: Make sure no other applications are using the audio devices

