#!/bin/bash

# Destination Configuration (Orange Pi)
# Change these values to match your Orange Pi
REMOTE_USER="orangepi"  # User on Orange Pi
REMOTE_IP="192.168.1.221" # IP of Orange Pi
REMOTE_DIR="~/assistant" # Destination directory on Orange Pi

echo "Starting continuous synchronization with ${REMOTE_USER}@${REMOTE_IP}:${REMOTE_DIR}"

# Sync function
sync_files() {
    rsync -avz \
        --exclude '.venv' \
        --exclude '__pycache__' \
        --exclude '.git' \
        --exclude 'terminals' \
        --exclude '*.pyc' \
        ./ "${REMOTE_USER}@${REMOTE_IP}:${REMOTE_DIR}"
}

# Check if inotifywait is installed
if command -v inotifywait &> /dev/null; then
    echo "Using inotifywait to detect real-time changes..."
    
    # Initial sync
    sync_files
    
    # Monitoring loop
    # Exclude .venv and .git from monitoring to avoid saturation
    while inotifywait -r -e modify,create,delete,move \
        --exclude '(\.venv|\.git|__pycache__|terminals)' \
        ./; do
            echo "Change detected. Synchronizing..."
            sync_files
            echo "Synchronization completed."
    done
else
    echo "WARNING: 'inotify-tools' is not installed."
    echo "Using simple loop with 2 second wait."
    echo "To improve performance, install inotify-tools: sudo nala install inotify-tools"
    
    while true; do
        sync_files
        sleep 2
    done
fi
