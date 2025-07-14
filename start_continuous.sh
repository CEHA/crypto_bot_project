#!/bin/bash
# Start continuous improvement with monitoring

cd /home/user/Source/Binance/crypto_bot_project

# Create logs directory
mkdir -p logs

# Function to start the process
start_process() {
    echo "🚀 Starting continuous improvement..."
    python3 continuous_improvement.py
}

# Function to monitor and restart if needed
monitor_loop() {
    while true; do
        echo "$(date): Starting continuous improvement process"
        start_process
        exit_code=$?
        
        if [ $exit_code -eq 0 ]; then
            echo "$(date): Process exited normally"
            break
        else
            echo "$(date): Process crashed with exit code $exit_code, restarting in 5 seconds..."
            sleep 5
        fi
    done
}

# Handle signals
trap 'echo "Stopping continuous improvement..."; exit 0' SIGINT SIGTERM

# Check if already running
if pgrep -f "continuous_improvement.py" > /dev/null; then
    echo "❌ Continuous improvement already running!"
    echo "Use: pkill -f continuous_improvement.py to stop"
    exit 1
fi

echo "🔄 Starting monitored continuous improvement loop"
echo "Press Ctrl+C to stop gracefully"

# Start monitoring loop
monitor_loop
