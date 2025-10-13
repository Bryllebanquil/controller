#!/bin/bash

# Neural Control Hub - Backend Startup Script
echo "🔧 Starting Neural Control Hub Backend..."
echo "========================================"

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is not installed or not in PATH!"
    exit 1
fi

# Check if requirements file exists
if [ ! -f "backend-requirements.txt" ]; then
    echo "❌ Error: backend-requirements.txt not found!"
    exit 1
fi

# Install backend dependencies if needed
echo "📦 Checking backend dependencies..."
pip3 install -r backend-requirements.txt

if [ $? -ne 0 ]; then
    echo "❌ Failed to install backend dependencies!"
    echo "You may need to run: pip3 install -r backend-requirements.txt"
    exit 1
fi

echo "🔧 Starting backend server..."
echo "Backend will be available at: http://localhost:8080"
echo "API endpoints: http://localhost:8080/api/"
echo "WebSocket: ws://localhost:8080/socket.io/"
echo ""
echo "Default admin password: q"
echo "Press Ctrl+C to stop the backend server"
echo "========================================"

# Start the backend server
python3 start-backend.py