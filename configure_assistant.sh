#!/bin/bash

# configure_assistant.sh
# All-in-one script to configure the assistant on Orange Pi 5
# Run with: ./configure_assistant.sh
# To start the web configuration interface: ./configure_assistant.sh --web-config

set -e # Stop script on error

# Check for web-config flag
if [ "$1" == "--web-config" ]; then
    echo "--- Starting Web Configuration Interface ---"
    # Ensure dependencies are installed for root (since we use sudo)
    if ! sudo python3 -c "import flask" &> /dev/null; then
        echo "Flask not installed for root, installing..."
        sudo apt install -y python3-flask || sudo pip3 install flask
    fi
    
    # Start the web app
    echo "Starting web server at http://0.0.0.0:5000"
    sudo python3 config_app.py
    exit 0
fi

echo "--- 1. Updating system and installing system dependencies ---"
# Dependencies for audio (PortAudio, ALSA), utilities and NetworkManager
sudo apt update
sudo apt install -y portaudio19-dev python3-pyaudio libasound2-plugins wget unzip tar python3-pip git build-essential network-manager

echo "--- 2. Installing Python libraries ---"
# Install from requirements.txt if exists, else install basics
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
else
    echo "requirements.txt not found, installing packages manually..."
    pip install requests gradio_client pyaudio openwakeword vosk numpy Flask
fi

echo "--- 3. Configuring Piper TTS (Text to Speech) ---"
mkdir -p piper
cd piper

# Define architecture and version
ARCH="aarch64" # Orange Pi 5 is ARM64
PIPER_VERSION="2023.11.14-2"

# Download Piper binary if not exists
if [ ! -f "piper" ]; then
    echo "Downloading Piper..."
    wget -O piper.tar.gz "https://github.com/rhasspy/piper/releases/download/${PIPER_VERSION}/piper_linux_${ARCH}.tar.gz"
    echo "Extracting Piper..."
    # Extract removing root 'piper/' folder to avoid conflicts
    tar -xvf piper.tar.gz --strip-components=1
    rm piper.tar.gz
    echo "Piper installed."
else
    echo "Piper already installed."
fi

# Download Voice Model (Spanish - Sharvard Medium)
VOICE_NAME="es_ES-sharvard-medium"
if [ ! -f "${VOICE_NAME}.onnx" ]; then
    echo "Downloading voice model: ${VOICE_NAME}..."
    wget -O "${VOICE_NAME}.onnx" "https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_ES/sharvard/medium/${VOICE_NAME}.onnx"
    wget -O "${VOICE_NAME}.onnx.json" "https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_ES/sharvard/medium/${VOICE_NAME}.onnx.json"
fi
cd ..

echo "--- 4. Configuring Vosk (Offline Speech Recognition) ---"
VOSK_MODEL="vosk-model-small-es-0.42"
if [ ! -d "${VOSK_MODEL}" ]; then
    echo "Downloading Vosk model..."
    wget "https://alphacephei.com/vosk/models/${VOSK_MODEL}.zip"
    echo "Unzipping model..."
    unzip "${VOSK_MODEL}.zip"
    rm "${VOSK_MODEL}.zip"
    echo "Vosk model installed."
else
    echo "Vosk model already exists."
fi

echo "--- Configuration completed successfully ---"
echo "To run the assistant:"
echo "  python main_assistant.py"
echo ""
echo "To configure WiFi, Audio and Location via web:"
echo "  ./configure_assistant.sh --web-config"
