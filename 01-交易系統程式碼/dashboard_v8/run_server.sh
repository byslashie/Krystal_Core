#!/bin/bash
# Dashboard v8 Flask Server Startup Script

cd "$(dirname "$0")"

# Kill any existing Flask processes on ports 9000-9001
pkill -f "python3.*app.py" 2>/dev/null || true
sleep 2

# Start Flask server
echo "Starting Dashboard v8 Flask Server..."
echo "Access: http://localhost:9000"
python3 -u app.py 2>&1
