#!/usr/bin/env python3

import os
import sys
import time
import uuid
import platform
import threading
import socketio
import requests

# Configuration
SERVER_URL = "https://agent-controller-backend.onrender.com"
SILENT_MODE = False
DEBUG_MODE = True

def log_message(message, level="info"):
    """Log message with proper output handling"""
    if not SILENT_MODE:
        print(f"[{level.upper()}] {message}")

def get_or_create_agent_id():
    """Get or create a unique agent ID"""
    config_path = os.path.expanduser('~/.config')
    os.makedirs(config_path, exist_ok=True)
    id_file_path = os.path.join(config_path, 'agent_id.txt')
    
    if os.path.exists(id_file_path):
        with open(id_file_path, 'r') as f:
            return f.read().strip()
    else:
        agent_id = str(uuid.uuid4())
        with open(id_file_path, 'w') as f:
            f.write(agent_id)
        return agent_id

def main():
    """Main function"""
    log_message("=" * 60)
    log_message("Simple Agent Client")
    log_message("Starting up...")
    log_message("=" * 60)
    
    # Get agent ID
    agent_id = get_or_create_agent_id()
    log_message(f"Agent ID: {agent_id}")
    
    # Test server connection
    log_message(f"Testing connection to: {SERVER_URL}")
    try:
        response = requests.get(SERVER_URL, timeout=10)
        log_message(f"✓ HTTP connection successful: {response.status_code}")
    except Exception as e:
        log_message(f"✗ HTTP connection failed: {e}")
        return
    
    # Create Socket.IO client
    sio = socketio.Client()
    
    @sio.event
    def connect():
        log_message("✓ Connected to controller!")
        sio.emit('agent_connect', {'agent_id': agent_id})
        log_message(f"✓ Agent {agent_id} registered with controller")
        
        # Send system info
        system_info = {
            'agent_id': agent_id,
            'platform': platform.system(),
            'hostname': platform.node(),
            'python_version': platform.python_version(),
            'capabilities': {
                'screen_capture': False,
                'camera': False,
                'audio': False,
                'input_control': False,
                'webrtc': False
            }
        }
        sio.emit('system_info', system_info)
        log_message("✓ System info sent to controller")
    
    @sio.event
    def connect_error(data):
        log_message(f"✗ Connection error: {data}")
    
    @sio.event
    def disconnect():
        log_message("Disconnected from controller")
    
    @sio.on('command')
    def on_command(data):
        log_message(f"Received command: {data}")
        command = data.get('command', '')
        if command == 'ping':
            sio.emit('command_result', {'agent_id': agent_id, 'result': 'pong'})
            log_message("Responded to ping with pong")
    
    # Connect to server
    try:
        log_message("Connecting to controller...")
        sio.connect(SERVER_URL, wait_timeout=10)
        
        # Keep running
        log_message("Agent is running. Press Ctrl+C to stop.")
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        log_message("Shutting down...")
    except Exception as e:
        log_message(f"Error: {e}")
    finally:
        if sio.connected:
            sio.disconnect()

if __name__ == "__main__":
    main()