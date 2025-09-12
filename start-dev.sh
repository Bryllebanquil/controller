#!/bin/bash

# Development startup script for Neural Control Hub
# This script starts both the backend and frontend in development mode

echo "🚀 Starting Neural Control Hub Development Environment"
echo "=================================================="

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 is not installed or not in PATH"
    exit 1
fi

# Check if Node.js is available
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed or not in PATH"
    exit 1
fi

# Function to kill background processes on exit
cleanup() {
    echo "🛑 Shutting down development servers..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

echo "📦 Installing Python dependencies..."
if [ -f "requirements.txt" ]; then
    pip3 install -r requirements.txt
else
    echo "⚠️  requirements.txt not found, skipping Python dependencies"
fi

echo "📦 Installing Node.js dependencies..."
if [ -d "agent-controller ui" ]; then
    cd "agent-controller ui"
    npm install
    cd ..
else
    echo "⚠️  Frontend directory not found"
fi

echo "🔧 Starting Backend Server (Port 8080)..."
python3 controller.py &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 3

echo "🎨 Starting Frontend Development Server (Port 3000)..."
cd "agent-controller ui"
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "✅ Development Environment Started!"
echo "=================================="
echo "🌐 Backend API: http://localhost:8080"
echo "🎨 Frontend UI: http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop all servers"
echo ""

# Wait for background processes
wait $BACKEND_PID $FRONTEND_PID