#!/bin/bash
# Stop continuous improvement gracefully

echo "🛑 Stopping continuous improvement..."

# Find and stop the process
if pgrep -f "continuous_improvement.py" > /dev/null; then
    pkill -SIGTERM -f "continuous_improvement.py"
    echo "✅ Stop signal sent"
    
    # Wait for graceful shutdown
    sleep 5
    
    # Force kill if still running
    if pgrep -f "continuous_improvement.py" > /dev/null; then
        pkill -SIGKILL -f "continuous_improvement.py"
        echo "⚡ Force stopped"
    else
        echo "✅ Stopped gracefully"
    fi
else
    echo "ℹ️ No continuous improvement process running"
fi