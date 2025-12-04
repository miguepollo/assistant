#!/bin/bash

# Script to configure and run the voice assistant
# If config.json doesn't exist, it starts the web server for configuration
# Otherwise, it runs the main assistant
#
# Usage:
#   ./run_and_config_assistant.sh         # Normal mode
#   ./run_and_config_assistant.sh --config  # Force configuration mode
#
# To avoid sudo password prompt for CPU/GPU optimization, run once:
#   echo "$USER ALL=(ALL) NOPASSWD: /usr/bin/tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor" | sudo tee /etc/sudoers.d/cpu-governor
#   echo "$USER ALL=(ALL) NOPASSWD: /usr/bin/tee /sys/class/devfreq/*/governor" | sudo tee -a /etc/sudoers.d/cpu-governor
#   sudo chmod 0440 /etc/sudoers.d/cpu-governor

CONFIG_FILE="config.json"
CONFIG_APP="config_app.py"
MAIN_APP="main_assistant.py"

cd "$(dirname "$0")"
# mirar si esta instalado python3-dev portaudio19-dev build-essential network-manager, si no, instalarlos
if ! command -v python3-dev &> /dev/null; then
    sudo apt install python3-dev
fi
if ! command -v portaudio19-dev &> /dev/null; then
    sudo apt install portaudio19-dev
fi
if ! command -v build-essential &> /dev/null; then
    sudo apt install build-essential
fi
if ! command -v nmcli &> /dev/null; then
    sudo apt install network-manager
fi
if ! command -v file &> /dev/null; then
    sudo apt install file
fi
if ! command -v wget &> /dev/null; then
    sudo apt install wget
fi
if ! command -v unzip &> /dev/null; then
    sudo apt install unzip
fi


echo "Voice Assistant Launcher"
echo "========================"
echo ""
##hacer que si no hay venv crearlo en .venv y activarlo
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi
source .venv/bin/activate
pip install -r requirements.txt
# Function to check if config.json exists and has minimal content
check_config() {
    if [ ! -f "$CONFIG_FILE" ]; then
        return 1
    fi
    
    # Check if file is not empty and contains valid JSON
    if [ -s "$CONFIG_FILE" ]; then
        if python3 -c "import json; json.load(open('$CONFIG_FILE'))" 2>/dev/null; then
            return 0
        fi
    fi
    
    return 1
}

# Check for --config flag to force configuration mode
FORCE_CONFIG=false
if [ "$1" == "--config" ] || [ "$1" == "-c" ]; then
    FORCE_CONFIG=true
    echo "Configuration mode requested."
    echo ""
fi

# Check if configuration exists and not forcing config mode
if ! check_config || [ "$FORCE_CONFIG" == "true" ]; then
    if [ "$FORCE_CONFIG" == "true" ]; then
        echo "Opening configuration interface to edit settings..."
    fi
    echo ""
    echo "Please open your browser and go to:"
    echo "  http://localhost:5000"
    echo ""
    echo "Or if you are on another device on the same network:"
    echo "  http://$(hostname -I | awk '{print $1}'):5000"
    echo ""
    echo "After saving your configuration, the assistant will start automatically."
    echo ""
    echo "Press Ctrl+C to exit if you want to cancel."
    echo ""
    
    # Start the configuration web server
    python3 "$CONFIG_APP"
    
    # When the user exits the config server, check if config was created
    echo ""
    if check_config; then
        echo "Configuration completed successfully."
        echo "Restarting to launch the assistant..."
        echo ""
        sleep 2
        exec "$0"
    else
        echo "Configuration was not completed."
        echo "Please run this script again to configure."
        exit 1
    fi
else
    echo "Configuration found. Starting voice assistant..."
    echo ""
    
    # Display current configuration (without sensitive data)
    echo "Current configuration:"
    python3 -c "
import json
with open('$CONFIG_FILE', 'r') as f:
    config = json.load(f)
    for key, value in config.items():
        if 'password' in key.lower() or 'key' in key.lower():
            print(f'  {key}: ****')
        else:
            print(f'  {key}: {value}')
    "
    echo ""
    
    # Setup audio (enable speaker on Orange Pi)
    echo "Setting up audio..."
    if command -v amixer &> /dev/null; then
        # Get audio output card from config
        AUDIO_CARD=$(python3 -c "import json; print(json.load(open('$CONFIG_FILE')).get('audio_output', 2))" 2>/dev/null)
        if [ -z "$AUDIO_CARD" ]; then
            AUDIO_CARD=2
        fi
        
        # Enable speaker switch
        amixer -c "$AUDIO_CARD" sset "spk switch" on &>/dev/null
        if [ $? -eq 0 ]; then
            echo "Audio enabled on card $AUDIO_CARD"
        else
            echo "Warning: Could not enable audio (this is normal if not on Orange Pi)"
        fi
    fi
    echo ""
    
    # Start RKLLM server in background if not already running
    echo "Checking RKLLM server status..."
    if ! pgrep -f "gradio_server.py" > /dev/null; then
        echo "Starting RKLLM server..."
        RKLLM_DIR="/home/orangepi/ezrknn-llm/examples/rkllm_server_demo/rkllm_server"
        RKLLM_MODEL="/home/orangepi/ezrknn-llm/gemma3/gemma-3-1b-it_w8a8_g128_rk3588.rkllm"
        
        if [ -d "$RKLLM_DIR" ] && [ -f "$RKLLM_MODEL" ]; then
            # Try to set performance mode (will fail silently if no sudo)
            echo "Optimizing CPU/GPU performance..."
            for cpu in /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor; do
                [ -f "$cpu" ] && echo performance | sudo tee "$cpu" > /dev/null 2>&1
            done
            for gov in /sys/class/devfreq/*/governor; do
                [ -f "$gov" ] && echo performance | sudo tee "$gov" > /dev/null 2>&1
            done
            
            cd "$RKLLM_DIR"
            
            # Check for missing shared library (common issue)
            # We need to force check again if the existing one is wrong architecture
            if [ ! -f "lib/librkllmrt.so" ] || ! file "lib/librkllmrt.so" | grep -q "64-bit"; then
                if [ -f "lib/librkllmrt.so" ]; then
                    echo "Incorrect library architecture detected. Removing old one..."
                    rm "lib/librkllmrt.so"
                fi
                
                echo "Library lib/librkllmrt.so not found or incorrect in $RKLLM_DIR"
                echo "Attempting to locate correct aarch64 library..."
                mkdir -p lib
                
                # Try to find it in the ezrknn-llm directory, prioritizing aarch64
                # We look for paths containing 'aarch64' or 'arm64' first
                LIB_SOURCE=$(find /home/orangepi/ezrknn-llm -name "librkllmrt.so" | grep "aarch64" | head -n 1)
                
                if [ -z "$LIB_SOURCE" ]; then
                     # Fallback: try to check file type of any found lib
                     echo "Explicit aarch64 path not found, searching all..."
                     ALL_LIBS=$(find /home/orangepi/ezrknn-llm -name "librkllmrt.so")
                     for lib in $ALL_LIBS; do
                        if file "$lib" | grep -q "64-bit"; then
                            LIB_SOURCE=$lib
                            break
                        fi
                     done
                fi

                if [ -n "$LIB_SOURCE" ]; then
                    echo "Found 64-bit library at $LIB_SOURCE"
                    cp "$LIB_SOURCE" lib/
                    echo "Copied library to $(pwd)/lib/"
                else
                    echo "Error: Could not find 64-bit librkllmrt.so in /home/orangepi/ezrknn-llm"
                fi
            fi
            
            # Export library path just in case
            export LD_LIBRARY_PATH=$(pwd)/lib:$LD_LIBRARY_PATH
            
            nohup python3 gradio_server.py --rkllm_model_path "$RKLLM_MODEL" --target_platform rk3588 > /tmp/rkllm_server.log 2>&1 &
            echo "RKLLM server started (PID: $!)"
            echo "Log file: /tmp/rkllm_server.log"
            
            echo "Waiting for RKLLM server to be ready (this may take a minute)..."
            # Wait loop for port 8080
            MAX_RETRIES=60
            COUNT=0
            while [ $COUNT -lt $MAX_RETRIES ]; do
                # Check if port 8080 is open on localhost
                if python3 -c "import socket; s = socket.socket(); s.settimeout(1); result = s.connect_ex(('127.0.0.1', 8080)); s.close(); exit(result)" 2>/dev/null; then
                    echo " RKLLM server is ready!"
                    break
                fi
                echo -n "."
                sleep 2
                COUNT=$((COUNT+1))
            done
            echo ""
            
            if [ $COUNT -eq $MAX_RETRIES ]; then
                echo "Warning: Timed out waiting for RKLLM server to open port 8080."
                echo "It might still be loading the model or failed to start."
                echo "Checking log file tail:"
                tail -n 5 /tmp/rkllm_server.log
            fi
            
            cd - > /dev/null
        else
            echo "Warning: RKLLM server path not found. Continuing anyway..."
        fi
    else
        echo "RKLLM server is already running"
    fi
    echo ""
    
    echo "Starting assistant..."
    echo ""
    
    # Check for Vosk model and download if missing
    VOSK_MODEL_DIR="vosk-model-small-es-0.42"
    if [ ! -d "$VOSK_MODEL_DIR" ]; then
        echo "Vosk model not found. Downloading..."
        wget "https://alphacephei.com/vosk/models/vosk-model-small-es-0.42.zip"
        echo "Unzipping model..."
        unzip "vosk-model-small-es-0.42.zip"
        rm "vosk-model-small-es-0.42.zip"
        echo "Model installed."
    fi

    # Run the main assistant
    python3 "$MAIN_APP"
fi
