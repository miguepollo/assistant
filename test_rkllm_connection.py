#!/usr/bin/env python3
"""
Test script to diagnose RKLLM server connection issues
"""

import sys
from gradio_client import Client
import traceback

# Use localhost as default since the assistant runs locally
GRADIO_URL = "http://127.0.0.1:8080/"

def test_connection():
    print("=" * 60)
    print("RKLLM Server Connection Diagnostic Tool")
    print(f"Connecting to {GRADIO_URL}")
    print("=" * 60)
    print()
    
    try:
        client = Client(GRADIO_URL)
        print("✓ Client initialized")
    except Exception as e:
        print(f"✗ Failed to initialize client: {e}")
        return False
    
    # Step 1: Test /get_user_input (Standard Flow)
    print("\n[1/3] Testing /get_user_input...")
    history_with_user = []
    try:
        # Emulate the flow in rkllm_client.py
        # We construct the history manually as we do in the client
        messages_history = [{
            "role": "user",
            "content": "Hola"
        }]
        
        # In rkllm_client.py we skip /get_user_input and go straight to predict/submit
        # But let's try to see if the server responds to a simple predict first
        print("  Skipping /get_user_input (as per rkllm_client.py strategy)")
        history_with_user = messages_history
            
    except Exception as e:
        print(f"✗ Setup failed: {e}")
        traceback.print_exc()
        return False

    # Step 2: Test /get_RKLLM_output (Streaming)
    print("\n[2/3] Testing /get_RKLLM_output (Streaming)...")
    try:
        print(f"  Sending history: {history_with_user}")
        job = client.submit(
            history=history_with_user,
            api_name="/get_RKLLM_output"
        )
        
        print("  Receiving stream...")
        chunk_count = 0
        last_output = None
        
        # This loop corresponds to 'for intermediate_output in job:'
        for output in job:
            chunk_count += 1
            last_output = output
            # Show progress dots
            print(".", end="", flush=True)
            if chunk_count % 10 == 0:
                print(f" ({chunk_count})")
        
        print(f"\n✓ Streaming finished ({chunk_count} chunks received)")
        
        if last_output:
             print(f"  Final output structure type: {type(last_output)}")
             print(f"  Final output content: {last_output}")
        else:
             print("  WARNING: No output received from stream!")
        
    except Exception as e:
        print(f"✗ Streaming failed: {e}")
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)
