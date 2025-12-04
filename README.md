# Voice Assistant for Orange Pi

A fully-featured voice assistant designed to run on Orange Pi (or similar ARM devices) with wake word detection, speech-to-text, LLM integration, and text-to-speech capabilities.

## Features

- **Wake Word Detection**: Uses OpenWakeWord for hands-free activation
- **Speech Recognition**: Vosk-based offline speech-to-text in Spanish
- **LLM Integration**: Connects to RKLLM server for intelligent responses
- **Text-to-Speech**: Piper TTS for natural voice synthesis
- **Local Intents**: Quick responses for time and weather queries
- **Web Configuration Interface**: Easy setup through a browser
- **Streaming Audio**: Real-time TTS generation and playback
- **Configurable Audio Devices**: Select input/output devices via web UI

## Hardware Requirements

- Orange Pi (or similar ARM-based SBC)
- USB Microphone or audio input device
- Speaker or audio output device
- Internet connection (for initial setup and weather API)

## Software Requirements

### System Dependencies

```bash
# Audio libraries
sudo nala install portaudio19-dev alsa-utils

# Python 3
sudo nala install python3 python3-pip python3-venv

# Network management (for WiFi configuration)
sudo nala install network-manager
```

### Python Dependencies

All Python dependencies are listed in `requirements.txt`:

```bash
pip install -r requirements.txt
```

Required packages:
- `pyaudio` - Audio input/output
- `openwakeword` - Wake word detection
- `vosk` - Speech-to-text
- `requests` - HTTP requests for weather API
- `flask` - Web configuration interface
- `gradio_client` - LLM server communication

### External Components

1. **Piper TTS**
   - Download from: https://github.com/rhasspy/piper
   - Extract to `./piper/piper` (binary)
   - Download a voice model (e.g., `es_ES-sharvard-medium.onnx`)
   - Place model at `./piper/es_ES-sharvard-medium.onnx`

2. **Vosk Model**
   - Download Spanish model from: https://alphacephei.com/vosk/models
   - Recommended: `vosk-model-small-es-0.42`
   - Extract to project root: `./vosk-model-small-es-0.42/`

3. **RKLLM Server**
   - Must be running and accessible via Gradio
   - Configure in `rkllm_client.py` if needed

## Installation

### 1. Clone or Download the Project

```bash
cd ~/Dev
git clone <your-repo-url> assistant
cd assistant
```

### 2. Create Virtual Environment (Recommended)

A virtual environment isolates Python dependencies for this project.

**Create the virtual environment:**

```bash
python3 -m venv venv
```

**Activate the virtual environment:**

On Linux/Mac:
```bash
source venv/bin/activate
```

On Windows:
```bash
venv\Scripts\activate
```

You should see `(venv)` in your terminal prompt when activated.

**To deactivate later:**

```bash
deactivate
```

**Important**: Always activate the virtual environment before running the assistant or installing dependencies.

### 3. Install Python Dependencies

Make sure your virtual environment is activated, then install dependencies:

```bash
pip install -r requirements.txt
```

### 4. Download Piper TTS

```bash
# Create piper directory
mkdir -p piper

# Download Piper for ARM64 (adjust URL for your architecture)
wget https://github.com/rhasspy/piper/releases/latest/download/piper_arm64.tar.gz
tar -xzf piper_arm64.tar.gz -C piper/
rm piper_arm64.tar.gz

# Download Spanish voice model
cd piper
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_ES/sharvard/medium/es_ES-sharvard-medium.onnx
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_ES/sharvard/medium/es_ES-sharvard-medium.onnx.json
cd ..
```

### 5. Download Vosk Model

```bash
# Download and extract Spanish model
wget https://alphacephei.com/vosk/models/vosk-model-small-es-0.42.zip
unzip vosk-model-small-es-0.42.zip
rm vosk-model-small-es-0.42.zip
```

### 6. Make Scripts Executable

```bash
chmod +x run_and_config_assistant.sh
chmod +x configure_assistant.sh
chmod +x sync_to_pi.sh
```

## Configuration

### Quick Start Configuration

Simply run the launcher script:

```bash
./run_and_config_assistant.sh
```

If `config.json` doesn't exist, it will automatically start the web configuration interface.

### Manual Configuration

1. Start the configuration web server:

```bash
python3 config_app.py
```

2. Open your browser and navigate to:
   - From the same device: `http://localhost:5000`
   - From another device on the network: `http://<orange-pi-ip>:5000`

3. Configure the following settings:

   **WiFi Settings**
   - Select your WiFi network from the scan
   - Enter password to connect

   **Audio Settings**
   - Select microphone input device
   - Select speaker output device

   **Weather API** (Optional)
   - Get API key from: https://openweathermap.org/api
   - Enter your city name
   
   **Language Settings**
   - Choose between Spanish (es) or English (en)

4. Click "Save Configuration" - **The assistant will restart automatically!**

### Configuration File

All settings are stored in `config.json`:

```json
{
    "wifi_ssid": "YourNetwork",
    "audio_input": 2,
    "audio_output": 2,
    "openweathermap_key": "your-api-key-here",
    "location_city": "Madrid",
    "language": "es"
}
```

**Note**: Device IDs are stored as integers. On Orange Pi, both input and output typically use card 2 (ES8388 codec).

### Reconfiguration

To change settings after initial setup:

```bash
# Stop the assistant (Ctrl+C if running)
./run_and_config_assistant.sh --config
```

This opens the web interface with your current settings. After saving, the assistant restarts automatically.

## Usage

### Running the Assistant

```bash
./run_and_config_assistant.sh
```

The script will:
1. Check if configuration exists
2. If not configured: start web interface for configuration
3. If configured: 
   - Setup audio (enable speaker on Orange Pi)
   - Start the voice assistant

**Note**: On Orange Pi, the script automatically enables the speaker hardware switch to ensure audio output works correctly.

### Voice Commands Flow

1. **Wake Word**: Say "Alexa" (or configured wake word)
2. **Beep Sound**: Indicates the assistant is listening
3. **Speak Command**: Say your question or command
4. **Response**: Assistant processes and responds with audio

### Supported Commands

**Local Intents** (Fast, no LLM needed):
- Time queries: "What time is it?" / "Que hora es?"
- Weather queries: "What's the weather?" / "Que tiempo hace?"

**General Questions** (Processed by LLM):
- Any other questions or commands
- Conversational interactions

### Example Interaction

```
User: "Alexa"
[Beep sound]
User: "What time is it?"
Assistant: "It is 15:30."

User: "Alexa"
[Beep sound]
User: "What's the weather?"
Assistant: "The weather in Madrid is clear sky with a temperature of 22 degrees Celsius."

User: "Alexa"
[Beep sound]
User: "Tell me a joke"
Assistant: [Streams response from LLM]
```

## Project Structure

```
assistant/
├── main_assistant.py           # Main voice assistant application
├── config_app.py              # Flask web configuration interface
├── rkllm_client.py            # Client for RKLLM Gradio server
├── run_and_config_assistant.sh # Launcher script
├── configure_assistant.sh      # Configuration helper script
├── sync_to_pi.sh              # Deployment script for remote Orange Pi
├── requirements.txt           # Python dependencies
├── config.json                # Configuration file (created after setup)
├── beep.wav                   # Wake word confirmation sound (auto-generated)
├── piper/                     # Piper TTS directory
│   ├── piper                  # Piper binary
│   └── es_ES-sharvard-medium.onnx  # Spanish voice model
├── vosk-model-small-es-0.42/  # Vosk STT model
├── templates/
│   └── index.html            # Web configuration UI
└── static/                   # Static assets for web UI
```

## Advanced Configuration

### Changing Wake Word

Edit `main_assistant.py`:

```python
WAKE_WORD_MODEL = "alexa"  # Options: "alexa", "hey_jarvis", etc.
WAKE_WORD_THRESHOLD = 0.5  # Sensitivity (0-1)
```

### Changing Voice Models

**Different Language**:
1. Download a Piper model from: https://huggingface.co/rhasspy/piper-voices
2. Update `PIPER_MODEL` in `main_assistant.py`
3. Download corresponding Vosk model
4. Update `VOSK_MODEL_PATH` in `main_assistant.py`

**Different Voice**:
- Download alternative voice from Piper voices repository
- Update `PIPER_MODEL` path

### Audio Device Configuration

**List Audio Inputs**:
```bash
python3 -c "import pyaudio; p = pyaudio.PyAudio(); [print(f'{i}: {p.get_device_info_by_index(i)[\"name\"]}') for i in range(p.get_device_count())]"
```

**List Audio Outputs**:
```bash
aplay -l
```

### LLM Server Configuration

Edit `rkllm_client.py` to configure your LLM server endpoint:

```python
def __init__(self, gradio_url="http://localhost:7860"):
    # Change URL to your RKLLM server
```

## Troubleshooting

### No Audio Output

**On Orange Pi**: The speaker hardware switch may be disabled. Enable it with:
```bash
amixer -c 2 sset "spk switch" on
```

Or use the test script:
```bash
./test_audio.sh
```

The `run_and_config_assistant.sh` script enables this automatically, but it may reset after reboot.

**General troubleshooting:**

1. Check audio device configuration:
```bash
aplay -l  # List available cards
aplay -D plughw:2,0 /usr/share/sounds/alsa/Front_Center.wav  # Test output
```

2. Verify `audio_output` in `config.json` matches your card ID (usually 2 for Orange Pi ES8388 codec)

### Microphone Not Working

1. Test microphone:
```bash
arecord -l  # List devices
arecord -D plughw:0,0 -f S16_LE -r 16000 -d 3 test.wav  # Record test
aplay test.wav  # Play back
```

2. Check `audio_input` in `config.json`

### Wake Word Not Detected

1. Verify microphone is working (see above)
2. Adjust `WAKE_WORD_THRESHOLD` in `main_assistant.py`:
   - Default: 0.7
   - Lower = more sensitive (0.5-0.6) but more false positives
   - Higher = less sensitive (0.8-0.9) but may miss activations
3. Try speaking louder or closer to microphone
4. Check available wake words: Models are downloaded automatically by OpenWakeWord

### Wake Word Too Sensitive (False Positives)

If the wake word activates too frequently:

1. Increase `WAKE_WORD_THRESHOLD` in `main_assistant.py` (e.g., 0.8 or 0.9)
2. Increase `WAKE_WORD_COOLDOWN` (e.g., 3.0 or 5.0 seconds)
3. Reduce background noise near the microphone

### Vosk Model Not Found

```bash
# Download and extract
wget https://alphacephei.com/vosk/models/vosk-model-small-es-0.42.zip
unzip vosk-model-small-es-0.42.zip
```

### Piper TTS Not Working

1. Verify binary has execute permissions:
```bash
chmod +x piper/piper
```

2. Test Piper directly:
```bash
echo "Hello world" | ./piper/piper --model ./piper/es_ES-sharvard-medium.onnx --output_file - | aplay -r 22050 -f S16_LE -t raw
```

### LLM Connection Issues

1. Verify RKLLM server is running
2. Check `rkllm_client.py` has correct URL
3. Test connection manually

### WiFi Not Connecting

1. Ensure NetworkManager is running:
```bash
sudo systemctl status NetworkManager
```

2. Manual WiFi connection:
```bash
nmcli dev wifi connect "SSID" password "PASSWORD"
```

## Development

### Testing Configuration Interface

```bash
python3 config_app.py
# Open http://localhost:5000
```

### Testing Main Assistant (Without Audio)

Comment out audio-related code and test with print statements.

### Remote Deployment

Use the sync script to deploy to Orange Pi:

```bash
./sync_to_pi.sh
```

Edit the script to configure your Orange Pi's IP and user.

## Performance Optimization

### Reduce Memory Usage

- Use smaller Vosk model (vosk-model-small-*)
- Reduce audio buffer sizes if experiencing lag
- Close unnecessary services

### Improve Response Time

- Use faster LLM model
- Optimize wake word sensitivity
- Use lightweight Piper voice model

### CPU Usage

Monitor with:
```bash
top
htop
```

## Security Considerations

- API keys are stored in `config.json` - protect this file
- WiFi passwords are not saved (only used for connection)
- Web interface runs on all interfaces (0.0.0.0) - consider firewall rules
- Consider running web config only when needed

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Test on actual hardware if possible
4. Submit a pull request

## License

[Your License Here]

## Acknowledgments

- **Piper TTS**: https://github.com/rhasspy/piper
- **Vosk**: https://alphacephei.com/vosk/
- **OpenWakeWord**: https://github.com/dscripka/openWakeWord
- **RKLLM**: Rockchip LLM inference engine
- **OpenWeatherMap**: https://openweathermap.org/

## Support

For issues, questions, or contributions:
- Open an issue on GitHub
- Check existing issues for solutions
- Review troubleshooting section above

## Changelog

### Version 1.0.0
- Initial release
- Wake word detection
- Speech-to-text (Spanish)
- LLM integration with streaming
- Text-to-speech
- Web configuration interface
- Local intents (time, weather)
- Automated launcher script

## Roadmap

- [ ] Multi-language support
- [ ] More local intents (smart home control, etc.)
- [ ] Voice command history
- [ ] Wake word customization in web UI
- [ ] Mobile app for configuration
- [ ] Docker container support
- [ ] Conversation context memory
- [ ] Plugin system for extensibility

