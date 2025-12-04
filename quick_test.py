#!/usr/bin/env python3
from gradio_client import Client

client = Client("http://192.168.1.162:8080/")


def make_message(role, text):
    return {"role": role, "content": [{"text": text, "type": "text"}]}


# Test 1: Empty history
print("Test 1: Empty history")
try:
    result = client.predict(
        user_message="Hola",
        history=[],
        api_name="/get_user_input"
    )
    print(f"Success! Result: {result}")
    print(f"History returned: {result[1]}")
except Exception as e:
    print(f"Failed: {e}")

print("\n" + "="*60 + "\n")

# Test 2: With system message
print("Test 2: With system message")
try:
    result = client.predict(
        user_message="Hola",
        history=[make_message("system", "Eres útil")],
        api_name="/get_user_input"
    )
    print(f"Success! Result: {result}")
except Exception as e:
    print(f"Failed: {e}")

print("\n" + "="*60 + "\n")

# Test 3: With user message in history
print("Test 3: With previous user message")
try:
    result = client.predict(
        user_message="Cómo estás?",
        history=[make_message("user", "Hola")],
        api_name="/get_user_input"
    )
    print(f"Success! Result: {result}")
except Exception as e:
    print(f"Failed: {e}")
