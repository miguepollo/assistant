import os
import struct
import sys
import wave
import math
import json
import requests
import subprocess
import time
from datetime import datetime

# Import the client created earlier
from rkllm_client import RKLLMClient

# Audio Configuration
# On Orange Pi, ensure to install: sudo apt install portaudio19-dev
# pip install pyaudio vosk
import pyaudio
from vosk import Model as VoskModel, KaldiRecognizer

# Piper TTS Configuration
# Assuming you have the 'piper' binary and an .onnx model downloaded
# Path to Piper binary and model (adjust this on the Orange Pi)
PIPER_BINARY = "./piper/piper" 
PIPER_MODEL = "./piper/es_ES-sharvard-medium.onnx"

# Wake Word Configuration using Vosk
# Vosk-based wake word detection works perfectly on ARM devices like Orange Pi
# You can use any Spanish phrase as wake word
WAKE_WORD_PHRASE = "hola"  # Change to: "oye asistente", "hola ordenador", "hey kubic", etc.
# Cooldown period after wake word detection (seconds)
WAKE_WORD_COOLDOWN = 2.0

# VOSK Configuration (STT)
# Download a lightweight Spanish model: https://alphacephei.com/vosk/models
# Example: vosk-model-small-es-0.42
VOSK_MODEL_PATH = "vosk-model-small-es-0.42"

# Command Listening Timeout (seconds)
# If no command is detected after wake word, return to wake word detection
COMMAND_TIMEOUT = 5.0

CONFIG_FILE = "config.json"

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {}

def get_audio_output_flag():
    config = load_config()
    card_id = config.get('audio_output')
    if card_id is not None:
        # Use plughw for better compatibility and add buffer parameters
        return f"-D plughw:{card_id},0 -B 500000"
    return "-B 500000"

def create_beep_wav(filename="beep.wav"):
    if not os.path.exists(filename):
        print(f"Generating {filename}...")
        duration = 0.2  # seconds
        frequency = 880.0  # Hz
        volume = 0.5
        sample_rate = 44100
        n_samples = int(sample_rate * duration)
        
        try:
            with wave.open(filename, 'w') as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(sample_rate)
                
                for i in range(n_samples):
                    t = float(i) / sample_rate
                    val = volume * math.sin(2.0 * math.pi * frequency * t)
                    data = struct.pack('<h', int(val * 32767.0))
                    wav_file.writeframes(data)
        except Exception as e:
            print(f"Error creating beep file: {e}")

def speak(text):
    """Generate audio with Piper TTS and play it (blocking)"""
    print(f"Assistant: {text}")
    # Clean text
    clean_text = text.replace('"', '').replace("'", "").replace('\n', ' ').replace('`', '')
    
    output_flag = get_audio_output_flag()
    
    # Command to generate streaming audio (piping stdout to aplay)
    # -output_file - sends audio to stdout
    cmd = f'echo "{clean_text}" | {PIPER_BINARY} --model {PIPER_MODEL} --output_file - | aplay -r 22050 -f S16_LE -t raw {output_flag} - 2>/dev/null'
    
    result = os.system(cmd)
    if result != 0:
        print(f"[Warning: Audio playback failed with code {result >> 8}]")
    
    # Small delay to ensure audio device is released
    time.sleep(0.2)

def speak_stream(text_iterator):
    """Generate audio with Piper TTS from a text stream and play it via streaming"""
    print("Assistant (streaming): ", end="")
    
    output_flag = get_audio_output_flag()
    
    # Construct the pipeline: Piper -> Aplay with stderr suppression
    piper_cmd = f'{PIPER_BINARY} --model {PIPER_MODEL} --output_file - 2>/dev/null | aplay -r 22050 -f S16_LE -t raw {output_flag} - 2>/dev/null'
    
    process = None
    pipe_broken = False
    
    try:
        # Start the process with stdin pipe
        process = subprocess.Popen(piper_cmd, shell=True, stdin=subprocess.PIPE, 
                                   stderr=subprocess.DEVNULL, bufsize=0)
        
        for chunk in text_iterator:
            if chunk and not pipe_broken:
                # Print chunk to console as it arrives
                print(chunk, end="", flush=True)
                
                # Clean chunk for TTS
                clean_chunk = chunk.replace('"', '').replace("'", "").replace('`', '')
                
                # Write to Piper
                try:
                    if process.poll() is None:  # Check if process is still running
                        process.stdin.write(clean_chunk.encode('utf-8'))
                        process.stdin.flush()
                    else:
                        pipe_broken = True
                except (BrokenPipeError, OSError):
                    pipe_broken = True
                    break
        
        print("")  # Newline after streaming
        
        # Close stdin to signal EOF to Piper
        if process.stdin and not pipe_broken:
            try:
                process.stdin.close()
            except:
                pass
        
        # Wait for audio to finish playing
        try:
            return_code = process.wait(timeout=30)
            if return_code != 0 and not pipe_broken:
                print(f"[Warning: Audio process exited with code {return_code}]")
        except subprocess.TimeoutExpired:
            process.kill()
            print("[Warning: Audio process timeout]")
        
        # Delay to ensure audio device is released
        time.sleep(0.3)
        
    except Exception as e:
        print(f"\n[Error in speak_stream: {e}]")
    finally:
        # Ensure process is properly terminated
        if process and process.poll() is None:
            try:
                process.terminate()
                process.wait(timeout=1.0)
            except subprocess.TimeoutExpired:
                process.kill()
            except:
                pass

def play_audio(filename):
    if os.path.exists(filename):
        output_flag = get_audio_output_flag()
        result = os.system(f'aplay {output_flag} {filename} 2>/dev/null')
        if result != 0:
            print(f"[Warning: Could not play {filename}]")
        time.sleep(0.1)  # Brief delay to ensure audio device is released

def get_weather_info(config):
    api_key = config.get('openweathermap_key')
    city = config.get('location_city')
    
    if not api_key or not city:
        return "I need the API key and city configured to check the weather."
    
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric&lang=es"
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            temp = data['main']['temp']
            desc = data['weather'][0]['description']
            return f"The weather in {city} is {desc} with a temperature of {temp} degrees Celsius."
        else:
            return "I couldn't get the weather information right now."
    except Exception as e:
        print(f"Error getting weather: {e}")
        return "An error occurred while checking the weather."

def get_current_time():
    now = datetime.now()
    return f"It is {now.strftime('%H:%M')}."

def process_local_intents(text):
    """
    Check if the text matches local intents (time, weather).
    Returns the response string if matched, else None.
    """
    text_lower = text.lower()
    config = load_config()
    
    # Simple keyword matching for intents
    # Time
    if "hora" in text_lower or "time" in text_lower:
        return get_current_time()
    
    # Weather
    if "tiempo" in text_lower or "weather" in text_lower or "clima" in text_lower:
        return get_weather_info(config)
        
    return None

def get_system_prompt():
    """
    Get the system prompt based on configured language.
    This is sent only once at the start of the conversation.
    """
    config = load_config()
    language = config.get('language', 'es')
    
    if language == 'en':
        return "Always respond in English. Keep responses brief and concise. Use plain text only, no formatting, no lists, no markdown. If asked who you are, you are Kubic, an AI assistant."
    else:  # Spanish is default
        return "Siempre responde en español. Respuestas breves y concisas. Solo texto plano, sin formato, sin listas, sin markdown. Si te pregunto quien eres, eres Kubic, un asistente de IA."

def main():
    config = load_config()
    
    # Initialize LLM client with system prompt
    system_prompt = get_system_prompt()
    llm_client = RKLLMClient(system_prompt=system_prompt)

    # Ensure beep sound exists
    create_beep_wav("beep.wav")

    print(f"Wake word detector ready. Listening for: '{WAKE_WORD_PHRASE}'")

    # Initialize Vosk (STT)
    if not os.path.exists(VOSK_MODEL_PATH):
        print(f"Error: Could not find Vosk model at {VOSK_MODEL_PATH}")
        print("Download it from https://alphacephei.com/vosk/models and unzip it here.")
        sys.exit(1)
        
    print("Loading STT model (Vosk)...")
    vosk_model = VoskModel(VOSK_MODEL_PATH)
    rec = KaldiRecognizer(vosk_model, 16000)

    # Initialize Microphone for Vosk (STT)
    p = pyaudio.PyAudio()
    
    input_device_index = None
    if config.get('audio_input'):
        try:
            input_device_index = int(config.get('audio_input'))
            print(f"Using input device index: {input_device_index}")
        except ValueError:
            pass

    # Stream for command recognition (Vosk)
    stream = p.open(format=pyaudio.paInt16,
                    channels=1,
                    rate=16000,
                    input=True,
                    input_device_index=input_device_index,
                    frames_per_buffer=2048)

    print(f"Listening... Say '{WAKE_WORD_PHRASE}' to activate.")
    
    # Play beep sound to indicate the assistant is ready
    play_audio("beep.wav")

    # State machine: 'idle', 'listening_command', 'processing'
    state = 'idle'
    command_start_time = 0
    last_wake_word_time = 0  # Track last wake word detection
    wake_word_rec = KaldiRecognizer(vosk_model, 16000)
    wake_word_rec.SetWords(True)
    
    try:
        while True:
            # Read audio from mic
            data = stream.read(2048, exception_on_overflow=False)
            
            # State: IDLE - Detect Wake Word
            if state == 'idle':
                # Use Vosk to detect wake word
                if wake_word_rec.AcceptWaveform(data):
                    result = json.loads(wake_word_rec.Result())
                    text = result.get("text", "").lower().strip()
                    
                    # Check cooldown period to avoid immediate re-triggering
                    time_since_last_wake = time.time() - last_wake_word_time
                    
                    # Check if wake word phrase is in the recognized text
                    if WAKE_WORD_PHRASE.lower() in text and time_since_last_wake >= WAKE_WORD_COOLDOWN:
                        print(f"Wake Word '{WAKE_WORD_PHRASE}' detected!")
                        last_wake_word_time = time.time()
                        play_audio("beep.wav") 
                        state = 'listening_command'
                        command_start_time = time.time()
                        rec.Reset()  # Reset STT recognizer
                        wake_word_rec.Reset()  # Reset wake word recognizer
                        print("Listening for your command...")
            
            # State: LISTENING_COMMAND - Capture speech to text
            elif state == 'listening_command':
                # Check for timeout
                elapsed = time.time() - command_start_time
                if elapsed > COMMAND_TIMEOUT:
                    print("Command timeout. Returning to wake word detection.")
                    state = 'idle'
                    continue
                
                if rec.AcceptWaveform(data):
                    result = rec.Result()
                    result_json = json.loads(result)
                    text = result_json.get("text", "").strip()
                    
                    if text:
                        print(f"Command received: {text}")
                        state = 'processing'
                        
                        # Process the command
                        speak("Thinking...")
                        
                        # Check for local intents first
                        local_response = process_local_intents(text)
                        
                        if local_response:
                            # If local intent matched, speak response directly
                            speak(local_response)
                        else:
                            # Process with LLM (streaming)
                            # System prompt is already set in the client, just send the user's text
                            response_generator = llm_client.chat_stream(text)
                            speak_stream(response_generator)
                        
                        # Return to idle state after processing
                        print(f"\nWaiting for '{WAKE_WORD_PHRASE}'...")
                        wake_word_rec.Reset()  # Reset wake word recognizer
                        state = 'idle'
                else:
                    # Vosk is processing partial results
                    # Check partial to give user feedback
                    partial = rec.PartialResult()
                    partial_json = json.loads(partial)
                    partial_text = partial_json.get("partial", "")
                    if partial_text:
                        # User is speaking, reset timeout
                        command_start_time = time.time()

    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()

if __name__ == "__main__":
    main()
