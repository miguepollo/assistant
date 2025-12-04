from gradio_client import Client
import sys
import traceback
import json
import os

# API Configuration
CONFIG_FILE = "config.json"

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {}

class RKLLMClient:
    def __init__(self, url=None, system_prompt=None):
        if url is None:
            config = load_config()
            # Default to localhost if not specified, as we run the server locally
            url = config.get('rkllm_api_url', "http://localhost:8080/")
            
        print(f"Connecting to RKLLM API at: {url}")
        self.client = Client(url)
        self.history = []
        self.system_prompt_sent = False
        self.system_prompt = system_prompt

    def _ensure_content_string(self, content):
        """
        Ensure content is a string.
        """
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            # If it's the complex format [{'text': '...', 'type': 'text'}]
            if len(content) > 0 and isinstance(content[0], dict) and 'text' in content[0]:
                return content[0]['text']
            return " ".join([str(c) for c in content])
        return str(content)

    def _format_history_for_api(self):
        """
        Convert internal history to the message format expected by the API.
        Each message must be: {'role': 'user', 'content': 'string'}
        """
        messages = []
        for item in self.history:
            # If already in dict format with role and content
            if isinstance(item, dict) and 'role' in item and 'content' in item:
                messages.append({
                    "role": item['role'],
                    "content": self._ensure_content_string(item['content'])
                })
            # If in tuple format [user_msg, bot_msg], convert to message dicts
            elif isinstance(item, (list, tuple)) and len(item) >= 2:
                messages.append({
                    "role": "user",
                    "content": str(item[0])
                })
                messages.append({
                    "role": "assistant",
                    "content": str(item[1])
                })
        return messages

    def chat(self, user_message):
        """
        Sends a message to the Gradio API and returns the full response.
        Maintains conversation history in the instance.
        """
        try:
            # Format message properly for chat API
            messages_history = self._format_history_for_api()
            
            # Add system prompt if needed
            if self.system_prompt and not self.system_prompt_sent:
                messages_history.insert(0, {
                    "role": "system",
                    "content": self.system_prompt
                })
                self.system_prompt_sent = True
            
            # Add user message
            messages_history.append({
                "role": "user",
                "content": user_message
            })
            
            # Step 1: Send user input (/get_user_input)
            # We bypass this as it seems to be a UI helper that crashes with API usage
            history_with_user = messages_history
            
            # Step 2: Get model response (/get_RKLLM_output)
            # Returns: history_with_response
            result_step2 = self.client.predict(
                history=history_with_user,
                api_name="/get_RKLLM_output"
            )
            
            # Update our local history
            self.history = result_step2
            
            # Extract the last assistant message
            if self.history:
                last_interaction = self.history[-1]
                # Check if it's in message dict format
                if isinstance(last_interaction, dict) and 'content' in last_interaction:
                    content = last_interaction['content']
                    # If content is a list of objects, extract text
                    if isinstance(content, list) and len(content) > 0:
                        if isinstance(content[0], dict) and 'text' in content[0]:
                            return content[0]['text']
                    # If content is a string (shouldn't happen with new format)
                    elif isinstance(content, str):
                        return content
                # Check if it's in tuple format
                elif isinstance(last_interaction, (list, tuple)) and len(last_interaction) > 1:
                    bot_response = last_interaction[1]
                    return bot_response
                
            return "Error: Could not retrieve response from history."

        except Exception as e:
            return f"Error connecting to Gradio: {str(e)}"

    def chat_stream(self, user_message):
        """
        Sends a message to the Gradio API and yields the response incrementally.
        """
        try:
            # Format message properly for chat API
            messages_history = self._format_history_for_api()
            
            # Add system prompt if needed
            if self.system_prompt and not self.system_prompt_sent:
                messages_history.insert(0, {
                    "role": "system",
                    "content": self.system_prompt
                })
                self.system_prompt_sent = True
            
            # Add user message
            messages_history.append({
                "role": "user",
                "content": user_message
            })
            
            # Step 1: Send user input
            # We bypass this as it seems to be a UI helper that crashes with API usage
            history_with_user = messages_history
            
            # Step 2: Request stream
            try:
                job = self.client.submit(
                    history=history_with_user,
                    api_name="/get_RKLLM_output"
                )
            except Exception as e:
                print(f"[ERROR] Failed to submit job to /get_RKLLM_output: {str(e)}")
                traceback.print_exc()
                yield f"Error submitting request: {str(e)}"
                return
            
            current_full_text = ""
            intermediate_output = None
            error_occurred = False
            
            try:
                for intermediate_output in job:
                    # Debug: trace what we get
                    print(f" DEBUG: Received update type {type(intermediate_output)}")
                    if intermediate_output:
                        print(f" DEBUG: Last interaction: {intermediate_output[-1]}")
                    
                    # intermediate_output is the full history at that point
                    if intermediate_output:
                        last_interaction = intermediate_output[-1]
                        # print(f" DEBUG: Last interaction: {last_interaction}")
                        
                    # Handle dict format (messages with role/content)
                    if isinstance(last_interaction, dict) and 'content' in last_interaction:
                        content = last_interaction['content']
                        # Content is a list of objects with 'text' field
                        if isinstance(content, list) and len(content) > 0:
                            if isinstance(content[0], dict) and 'text' in content[0]:
                                full_text = content[0]['text']
                            else:
                                continue
                        # Fallback for string content (shouldn't happen)
                        elif isinstance(content, str):
                            full_text = content
                        else:
                            continue
                    # Handle tuple format (legacy)
                    elif isinstance(last_interaction, (list, tuple)) and len(last_interaction) > 1:
                        full_text = last_interaction[1]
                    else:
                        continue
                        
                    if full_text is None:
                        continue 
                    
                    # Calculate new chunk
                    if len(full_text) > len(current_full_text):
                        chunk = full_text[len(current_full_text):]
                        current_full_text = full_text
                        yield chunk
            except Exception as e:
                print(f"[ERROR] Error during streaming: {str(e)}")
                traceback.print_exc()
                error_occurred = True
                yield f" [Streaming interrupted: {str(e)}]"
                            
            # Update history at the end (only if no error)
            if not error_occurred and intermediate_output is not None:
                self.history = intermediate_output
            
        except Exception as e:
            print(f"[ERROR] Unexpected error in chat_stream: {str(e)}")
            traceback.print_exc()
            yield f"Error: {str(e)}"

    def clear_history(self):
        self.history = []
        self.system_prompt_sent = False

def chat_with_rkllm(prompt):
    """
    Wrapper function to maintain compatibility or simple usage.
    Instantiates a new client on each call (does not maintain memory between calls to this function).
    """
    client = RKLLMClient()
    return client.chat(prompt)

if __name__ == "__main__":
    # Usage example
    user_input = "Hola, ¿qué tal estás? y quien eres? cuentamelo detallado"
    if len(sys.argv) > 1:
        user_input = " ".join(sys.argv[1:])
        
    print(f"User: {user_input}")
    
    # Instantiate the client
    rkllm = RKLLMClient()
    response = rkllm.chat(user_input)
    
    print(f"RKLLM: {response}")
