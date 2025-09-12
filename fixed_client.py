#!/usr/bin/env python3

import os
import sys
import time
import uuid
import platform
import threading
import socketio
import requests
import json

# Configuration
BACKEND_URL = "https://agent-controller-backend.onrender.com"
FRONTEND_URL = "https://agent-controller-dashboard.onrender.com"
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

def test_backend_connection():
    """Test connection to backend"""
    log_message(f"Testing backend connection: {BACKEND_URL}")
    try:
        response = requests.get(f"{BACKEND_URL}/login", timeout=10)
        log_message(f"✓ Backend accessible: {response.status_code}")
        return True
    except Exception as e:
        log_message(f"✗ Backend connection failed: {e}")
        return False

def test_frontend_connection():
    """Test connection to frontend"""
    log_message(f"Testing frontend connection: {FRONTEND_URL}")
    try:
        response = requests.get(FRONTEND_URL, timeout=10)
        log_message(f"✓ Frontend accessible: {response.status_code}")
        return True
    except Exception as e:
        log_message(f"✗ Frontend connection failed: {e}")
        return False

def main():
    """Main function"""
    log_message("=" * 60)
    log_message("Fixed Agent Client")
    log_message("Starting up...")
    log_message("=" * 60)
    
    # Test connections
    if not test_backend_connection():
        log_message("Cannot connect to backend. Exiting.")
        return
    
    test_frontend_connection()
    
    # Get agent ID
    agent_id = get_or_create_agent_id()
    log_message(f"Agent ID: {agent_id}")
    
    # Create Socket.IO client
    sio = socketio.Client()
    
    @sio.event
    def connect():
        log_message("✓ Connected to backend controller!")
        log_message("Registering agent with controller...")
        
        # Register agent
        sio.emit('agent_connect', {'agent_id': agent_id})
        log_message(f"✓ Agent {agent_id} registration sent")
        
        # Send system info
        system_info = {
            'agent_id': agent_id,
            'name': f'Agent-{agent_id[:8]}',
            'platform': platform.system(),
            'hostname': platform.node(),
            'python_version': platform.python_version(),
            'ip': '127.0.0.1',  # This would be the actual IP in a real scenario
            'capabilities': {
                'screen_capture': False,
                'camera': False,
                'audio': False,
                'input_control': False,
                'webrtc': False,
                'file_transfer': True,
                'commands': True
            },
            'cpu_usage': 0,
            'memory_usage': 0,
            'network_usage': 0,
            'system_info': {
                'os': platform.system(),
                'version': platform.version(),
                'machine': platform.machine(),
                'processor': platform.processor()
            },
            'uptime': 0
        }
        
        # Send system info
        sio.emit('system_info', system_info)
        log_message("✓ System info sent to controller")
        
        # Send heartbeat periodically
        def send_heartbeat():
            while True:
                time.sleep(30)  # Send heartbeat every 30 seconds
                if sio.connected:
                    sio.emit('agent_heartbeat', {
                        'agent_id': agent_id,
                        'timestamp': time.time()
                    })
                    log_message("Heartbeat sent")
        
        heartbeat_thread = threading.Thread(target=send_heartbeat, daemon=True)
        heartbeat_thread.start()
        log_message("✓ Heartbeat thread started")
    
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
        elif command == 'status':
            sio.emit('command_result', {'agent_id': agent_id, 'result': 'Agent is running and healthy'})
            log_message("Responded to status command")
    
    @sio.on('execute_command')
    def on_execute_command(data):
        log_message(f"Received execute command: {data}")
        command = data.get('command', '')
        log_message(f"Executing command: {command}")
        
        # Simple command handling
        if command == 'ping':
            result = 'pong'
        elif command == 'status':
            result = 'Agent is running and healthy'
        elif command == 'info':
            result = f"Agent ID: {agent_id}, Platform: {platform.system()}, Hostname: {platform.node()}"
        else:
            result = f"Command '{command}' received but not implemented"
        
        sio.emit('command_output', {
            'agent_id': agent_id,
            'output': result
        })
        log_message(f"Command result: {result}")
    
    # Connect to backend
    try:
        log_message(f"Connecting to backend: {BACKEND_URL}")
        sio.connect(BACKEND_URL, wait_timeout=10)
        
        # Keep running
        log_message("Agent is running and connected to backend.")
        log_message("Check the frontend dashboard to see this agent.")
        log_message("Press Ctrl+C to stop.")
        
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