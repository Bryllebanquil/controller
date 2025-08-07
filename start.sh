#!/bin/bash

# Neural Control Hub Startup Script

echo "Starting Neural Control Hub..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies if needed
if [ ! -f "venv/lib/python*/site-packages/flask" ]; then
    echo "Installing dependencies..."
    pip install flask flask-socketio eventlet
fi

# Set default admin password if not set
if [ -z "$ADMIN_PASSWORD" ]; then
    export ADMIN_PASSWORD="admin123"
    echo "Using default admin password: admin123"
    echo "To change password, set ADMIN_PASSWORD environment variable"
fi

# Start the application
echo "Starting server..."
python3 controller.py