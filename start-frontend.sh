#!/bin/bash

# Neural Control Hub - Frontend Startup Script
echo "🚀 Starting Neural Control Hub Frontend..."
echo "========================================"

# Check if we're in the right directory
if [ ! -d "agent-controller ui" ]; then
    echo "❌ Error: 'agent-controller ui' directory not found!"
    echo "Please run this script from the workspace root directory."
    exit 1
fi

# Navigate to frontend directory
cd "agent-controller ui"

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    npm install
    if [ $? -ne 0 ]; then
        echo "❌ Failed to install dependencies!"
        exit 1
    fi
fi

echo "🌐 Starting frontend development server..."
echo "Frontend will be available at: http://localhost:3000"
echo "Backend should be running at: http://localhost:8080"
echo ""
echo "Press Ctrl+C to stop the frontend server"
echo "========================================"

# Start the development server
npm run dev