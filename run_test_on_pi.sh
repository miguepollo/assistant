#!/bin/bash

# Script to run on the Orange Pi (target device) to test the RKLLM server connection
# Usage: ./test_rkllm_connection.py

cat << 'EOF' > test_rkllm_connection_pi.py
#!/usr/bin/env python3
import sys
import time
from gradio_client import Client
import traceback

# Localhost since we are on the Pi
GRADIO_URL = "http://127.0.0.1:8080/"

def test_connection():
    print("=" * 60)
    print("RKLLM Server Connection Diagnostic Tool (On Device)")
    print(f"Connecting to {GRADIO_URL}")
    print("=" * 60)
    
    try:
        client = Client(GRADIO_URL)
        print("✓ Client initialized")
    except Exception as e:
        print(f"✗ Failed to initialize client: {e}")
        print("Is the gradio_server.py running?")
        return False
    
    print("\n[1] Testing /get_RKLLM_output (Streaming)...")
    
    # Use the format expected by the latest RKLLM Gradio demo
    messages_history = [{
        "role": "user",
        "content": "Hola, ¿quién eres?"
    }]
    
    try:
        print(f"  Sending history: {messages_history}")
        job = client.submit(
            history=messages_history,
            api_name="/get_RKLLM_output"
        )
        
        print("  Receiving stream...")
        chunk_count = 0
        last_output = None
        
        for output in job:
            chunk_count += 1
            last_output = output
            print(".", end="", flush=True)
            
        print(f"\n✓ Streaming finished ({chunk_count} chunks)")
        
        if last_output:
             print(f"\n  Final output: {last_output}")
             if isinstance(last_output, list) and len(last_output) > 0:
                 last_msg = last_output[-1]
                 print(f"  Last message content: {last_msg}")
        else:
             print("  WARNING: No output received!")
        
    except Exception as e:
        print(f"\n✗ Streaming failed: {e}")
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)
EOF

# Run the python script
python3 test_rkllm_connection_pi.py
rm test_rkllm_connection_pi.py

