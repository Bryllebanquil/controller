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

# Set other default environment variables if not set
if [ -z "$SECRET_KEY" ]; then
    echo "Using auto-generated secret key"
fi

if [ -z "$SESSION_TIMEOUT" ]; then
    export SESSION_TIMEOUT="3600"
    echo "Session timeout: 1 hour"
fi

if [ -z "$MAX_LOGIN_ATTEMPTS" ]; then
    export MAX_LOGIN_ATTEMPTS="5"
    echo "Max login attempts: 5"
fi

if [ -z "$LOGIN_TIMEOUT" ]; then
    export LOGIN_TIMEOUT="300"
    echo "Login lockout timeout: 5 minutes"
fi

# Start the application
echo "Starting server..."
python3 controller.py