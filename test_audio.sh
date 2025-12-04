#!/bin/bash

echo "=== Audio Device Test ==="
echo ""

echo "Listing audio playback devices:"
aplay -l
echo ""

echo "Listing audio capture devices:"
arecord -l
echo ""

echo "Testing playback on default device:"
if [ -f "beep.wav" ]; then
    aplay beep.wav 2>&1
else
    speaker-test -t sine -f 1000 -l 1 2>&1
fi
echo ""

echo "Testing playback on plughw:2,0 (from config):"
if [ -f "beep.wav" ]; then
    aplay -D plughw:2,0 beep.wav 2>&1
else
    echo "beep.wav not found, skipping"
fi
echo ""

echo "Testing recording on device 0 (from config):"
echo "Recording 3 seconds..."
arecord -D plughw:0,0 -d 3 -f S16_LE -r 16000 -c 1 test_recording.wav 2>&1
if [ -f "test_recording.wav" ]; then
    echo "Playing back recording..."
    aplay -D plughw:2,0 test_recording.wav 2>&1
    rm test_recording.wav
fi
echo ""

echo "Test complete!"

