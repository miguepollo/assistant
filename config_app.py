import os
import json
import subprocess
import sys
import signal
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Required for flash messages
CONFIG_FILE = 'config.json'

# Flag to request restart after saving config
restart_requested = False

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {}

def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)

def get_audio_inputs():
    inputs = []
    try:
        import pyaudio
        p = pyaudio.PyAudio()
        info = p.get_host_api_info_by_index(0)
        numdevices = info.get('deviceCount')
        for i in range(0, numdevices):
            if (p.get_device_info_by_host_api_device_index(0, i).get('maxInputChannels')) > 0:
                name = p.get_device_info_by_host_api_device_index(0, i).get('name')
                inputs.append({'index': i, 'name': name})
        p.terminate()
    except Exception as e:
        print(f"Error getting audio inputs: {e}")
        inputs.append({'index': 0, 'name': 'Default Device'})
    return inputs

def get_audio_outputs():
    outputs = []
    # Using aplay -l to list hardware cards
    try:
        result = subprocess.run(['aplay', '-l'], capture_output=True, text=True)
        lines = result.stdout.split('\n')
        for line in lines:
            if line.startswith('card'):
                # Format: card 0: Codec [H3 Audio Codec], device 0: H3 Audio Codec [H3 Audio Codec]
                parts = line.split(':')
                card_id = parts[0].split()[1]
                name = parts[1].strip()
                # Extract more descriptive name if possible
                full_name = f"Card {card_id}: {name}"
                outputs.append({'card_id': card_id, 'name': full_name})
    except Exception as e:
        print(f"Error getting audio outputs: {e}")
        outputs.append({'card_id': '0', 'name': 'Default Card 0'})
    return outputs

def get_wifi_interfaces():
    interfaces = []
    try:
        # Using nmcli to list devices
        result = subprocess.run(['nmcli', '-t', '-f', 'DEVICE,TYPE', 'device'], capture_output=True, text=True)
        if result.returncode == 0:
            for line in result.stdout.split('\n'):
                if line.strip():
                    parts = line.split(':')
                    if len(parts) >= 2 and parts[1] == 'wifi':
                        interfaces.append(parts[0])
    except Exception as e:
        print(f"Error getting wifi interfaces: {e}")
    
    return interfaces

def scan_wifi_networks(interface=None):
    networks = []
    try:
        # Using nmcli to scan
        cmd = ['nmcli', '-t', '-f', 'SSID', 'dev', 'wifi', 'list']
        if interface:
            cmd.extend(['ifname', interface])

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            # Filter empty SSIDs and duplicates
            ssids = set()
            for line in result.stdout.split('\n'):
                ssid = line.strip()
                # nmcli -t format might escape colons, but SSID is the only field requested so it should be fine.
                # Sometimes \\: is used.
                ssid = ssid.replace('\\:', ':')
                if ssid and ssid not in ssids:
                    ssids.add(ssid)
                    networks.append(ssid)
        else:
            # Fallback for testing or if nmcli fails (simulated)
            print("nmcli failed, maybe not installed or no permissions")
    except Exception as e:
        print(f"Error scanning wifi: {e}")
    
    return sorted(list(networks))

def connect_wifi(ssid, password):
    if not ssid:
        return False, "No SSID provided"
    
    try:
        cmd = ['nmcli', 'dev', 'wifi', 'connect', ssid, 'password', password]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            return True, "Connected successfully"
        else:
            return False, f"Connection failed: {result.stderr}"
    except Exception as e:
        return False, str(e)

@app.route('/')
def index():
    config = load_config()
    input_devices = get_audio_inputs()
    output_cards = get_audio_outputs()
    wifi_interfaces = get_wifi_interfaces()
    return render_template('index.html', 
                         config=config, 
                         input_devices=input_devices,
                         output_cards=output_cards,
                         wifi_interfaces=wifi_interfaces)

@app.route('/save', methods=['POST'])
def save():
    global restart_requested
    config = load_config()
    
    # Update config with form data
    config['wifi_ssid'] = request.form.get('wifi_ssid')
    wifi_password = request.form.get('wifi_password') # Don't save password to file for security, just use it once
    
    # Convert audio device IDs to integers if they're numeric
    audio_input = request.form.get('audio_input')
    audio_output = request.form.get('audio_output')
    
    try:
        config['audio_input'] = int(audio_input) if audio_input and audio_input.isdigit() else audio_input
    except (ValueError, AttributeError):
        config['audio_input'] = audio_input
    
    try:
        config['audio_output'] = int(audio_output) if audio_output and audio_output.isdigit() else audio_output
    except (ValueError, AttributeError):
        config['audio_output'] = audio_output
    
    config['openweathermap_key'] = request.form.get('openweathermap_key')
    config['location_city'] = request.form.get('location_city')
    config['language'] = request.form.get('language', 'es')
    
    save_config(config)
    
    # Handle WiFi connection if password provided
    wifi_message = None
    if config['wifi_ssid'] and wifi_password:
        success, message = connect_wifi(config['wifi_ssid'], wifi_password)
        if success:
            wifi_message = f'WiFi connected to {config["wifi_ssid"]}'
        else:
            wifi_message = f'WiFi connection failed: {message}'
            flash(wifi_message, 'danger')
            return redirect(url_for('index'))
    
    # Configuration saved successfully - request restart
    restart_requested = True
    flash('Configuration saved successfully. Restarting assistant...', 'success')
    
    # Schedule server shutdown to trigger restart
    import threading
    def shutdown_server():
        import time
        time.sleep(2)  # Give time for the response to be sent
        print("\n" + "="*50)
        print("Configuration saved. Shutting down web server...")
        print("The assistant will restart automatically.")
        print("="*50 + "\n")
        os.kill(os.getpid(), signal.SIGTERM)
    
    threading.Thread(target=shutdown_server, daemon=True).start()
    
    return redirect(url_for('shutdown_page'))

@app.route('/scan_wifi')
def scan_wifi():
    interface = request.args.get('interface')
    networks = scan_wifi_networks(interface)
    return jsonify({'networks': networks})

@app.route('/shutdown')
def shutdown_page():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Restarting Assistant</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {
                font-family: Arial, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                margin: 0;
                color: white;
            }
            .container {
                text-align: center;
                padding: 40px;
                background: rgba(255, 255, 255, 0.1);
                border-radius: 20px;
                backdrop-filter: blur(10px);
            }
            .spinner {
                border: 4px solid rgba(255, 255, 255, 0.3);
                border-radius: 50%;
                border-top: 4px solid white;
                width: 60px;
                height: 60px;
                animation: spin 1s linear infinite;
                margin: 20px auto;
            }
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
            h1 { margin-bottom: 10px; }
            p { font-size: 18px; opacity: 0.9; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Configuration Saved!</h1>
            <div class="spinner"></div>
            <p>Starting voice assistant...</p>
            <p style="font-size: 14px; margin-top: 20px;">You can close this window now.</p>
        </div>
    </body>
    </html>
    '''

if __name__ == '__main__':
    print("Starting Config Interface on port 5000...")
    app.run(host='0.0.0.0', port=5000, debug=True)

