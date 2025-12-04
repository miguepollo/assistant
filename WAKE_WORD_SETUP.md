# Wake Word Detection Setup

## How It Works

The assistant now uses **Vosk** for wake word detection. This is the same speech recognition engine used for understanding your commands, which means:

✅ **Perfect ARM Support** - Works flawlessly on Orange Pi 5 Max  
✅ **No API Keys Required** - Completely offline and free  
✅ **Custom Wake Words** - Use any Spanish phrase you want  
✅ **High Accuracy** - Same quality as command recognition  
✅ **Low Latency** - Fast detection and response  
✅ **No Additional Dependencies** - Already using Vosk for STT  

## Configuring Your Wake Word

### Default Wake Word
By default, the assistant listens for **"alexa"**

### Changing the Wake Word

Edit `main_assistant.py` and change the `WAKE_WORD_PHRASE`:

```python
WAKE_WORD_PHRASE = "alexa"  # Change this to your preference
```

### Recommended Wake Words (Spanish)

Since you're using the Spanish Vosk model, here are some suggestions:

- `"alexa"` - Short and distinct
- `"asistente"` - Spanish for assistant
- `"oye asistente"` - Hey assistant
- `"hola ordenador"` - Hello computer
- `"hey kubic"` - Custom name for your assistant
- `"ok asistente"` - OK assistant
- `"hola robot"` - Hello robot

### Tips for Choosing a Wake Word

1. **Length**: 2-3 syllables work best
   - Too short: More false positives
   - Too long: Harder to remember and say

2. **Distinctiveness**: Choose uncommon words
   - Avoid common words used in normal conversation
   - This reduces accidental activations

3. **Clear pronunciation**: Easy to say clearly
   - Avoid similar sounding words
   - Make sure it's easy to pronounce

4. **Language**: Must be in Spanish (or the language of your Vosk model)
   - The model is trained on Spanish
   - English words might work but with lower accuracy

## Adjusting Sensitivity

### Cooldown Period
Prevents the assistant from triggering multiple times in succession:

```python
WAKE_WORD_COOLDOWN = 2.0  # seconds
```

- **Lower values (1.0-1.5)**: More responsive, but may re-trigger quickly
- **Higher values (2.5-3.0)**: Less responsive, but prevents accidental re-triggering
- **Recommended**: 2.0 seconds (default)

## Troubleshooting

### Wake Word Not Detected

1. **Check pronunciation**: Make sure you're saying it clearly
2. **Volume**: Speak loud enough for the microphone
3. **Try a different wake word**: Some words are easier to recognize
4. **Check microphone**: Test with `arecord -d 5 test.wav` and play it back

### Too Many False Positives

1. **Choose a more unique wake word**: Avoid common words
2. **Increase cooldown**: Set `WAKE_WORD_COOLDOWN = 3.0`
3. **Use longer phrases**: "oye asistente" instead of "asistente"

### Wake Word Detection is Slow

This is normal with Vosk-based detection. The assistant needs to:
1. Recognize the audio
2. Process the text
3. Check if it matches the wake word

Typical detection time: 1-2 seconds after you finish saying the wake word.

## Advanced: Using English Wake Words

If you want to use English wake words like "hey jarvis" or "computer":

1. Download an English Vosk model from https://alphacephei.com/vosk/models
2. Extract it to the project directory
3. Edit `main_assistant.py`:

```python
VOSK_MODEL_PATH = "vosk-model-small-en-us-0.15"  # English model
WAKE_WORD_PHRASE = "hey jarvis"
```

## Why Not Porcupine?

Initially, we tried to use Porcupine by Picovoice, but it doesn't support the ARM CPU architecture of the Orange Pi 5 Max (CPU: '0xd05'). Vosk provides a better solution that:

- Works on all ARM architectures
- Doesn't require API keys or internet
- Gives you full control over custom wake words
- Uses the same engine for consistency

## Future Improvements

Possible enhancements for better wake word detection:

1. **Separate wake word model**: Use a small, fast model just for wake word detection
2. **Phonetic matching**: Match phonetic patterns instead of exact text
3. **Confidence scores**: Only trigger on high-confidence detections
4. **Multiple wake words**: Support several wake word options

For now, the Vosk-based solution provides a good balance of accuracy, reliability, and ease of use on your Orange Pi hardware.

