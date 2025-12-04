#!/usr/bin/env python3
"""
Test script to diagnose RKLLM server connection issues
"""

import sys
from gradio_client import Client
import traceback

GRADIO_URL = "http://192.168.1.162:8080/"

def test_connection():
    print("=" * 60)
    print("RKLLM Server Connection Diagnostic Tool")
    print("=" * 60)
    print()
    
    client = Client(GRADIO_URL)
    
    # Step 1: Test /get_user_input (Standard Flow)
    print("[1/3] Testing /get_user_input (User Only, No System Prompt)...")
    try:
        # We do NOT add the message to history manually. 
        # We pass it as user_message argument.
        result = client.predict(
            user_message="Hola",
            history=[],
            api_name="/get_user_input"
        )
        print("✓ /get_user_input success!")
        
        # Result is usually (textbox_val, history_list)
        if isinstance(result, (list, tuple)) and len(result) > 1:
            history_with_user = result[1]
            print(f"  Received history: {str(history_with_user)[:200]}...")
        else:
            print(f"  Unexpected result format: {result}")
            return False
            
    except Exception as e:
        print(f"✗ /get_user_input failed: {e}")
        traceback.print_exc()
        return False

    # Step 2: Test /get_RKLLM_output (Standard Flow)
    print("\n[2/3] Testing /get_RKLLM_output (Streaming)...")
    try:
        job = client.submit(
            history=history_with_user,
            api_name="/get_RKLLM_output"
        )
        
        print("  Receiving stream...")
        chunk_count = 0
        last_output = None
        for output in job:
            chunk_count += 1
            last_output = output
            if chunk_count <= 3:
                print(f"    Chunk {chunk_count}: {str(output)[:100]}...")
        
        print(f"✓ Streaming successful ({chunk_count} chunks received)")
        if last_output:
             print(f"  Final output structure: {type(last_output)}")
             if isinstance(last_output, list) and last_output:
                 print(f"  Last message: {last_output[-1]}")
        
    except Exception as e:
        print(f"✗ Streaming failed: {e}")
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)
