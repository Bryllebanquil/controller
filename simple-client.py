#!/usr/bin/env python3
"""
Enhanced Simple Client for Controller Testing
============================================

This is an improved version of simple-client.py that includes:
- Basic Socket.IO connection to controller
- Command execution testing
- Interactive command input
- Real-time command output display
- Connection status monitoring
- Comprehensive logging

Usage:
    python3 simple-client.py [--url CONTROLLER_URL] [--interactive]

Features:
    - Basic Socket.IO connection to controller
    - Command execution and response handling
    - Interactive mode for manual testing
    - Connection status monitoring
    - Heartbeat/ping functionality
    - Comprehensive logging
    - Graceful error handling
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

# Configure enhanced logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Configuration
DEFAULT_CONTROLLER_URL = os.environ.get('CONTROLLER_URL', 'http://localhost:8080')
AGENT_ID = f"simple-client-{int(time.time())}"
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
interactive_mode = False

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    global shutdown_requested
    log_message("🛑 Shutdown signal received, closing connections...")
    shutdown_requested = True

def log_message(message, level="info"):
    """Enhanced logging function with colors"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    colors = {
        "info": "\033[94m",      # Blue
        "success": "\033[92m",   # Green
        "warning": "\033[93m",   # Yellow
        "error": "\033[91m",     # Red
        "reset": "\033[0m"       # Reset
    }
    
    color = colors.get(level, colors["info"])
    reset = colors["reset"]
    print(f"{color}[{timestamp}] {level.upper()}: {message}{reset}")

def execute_command(command):
    """Execute a command and return its output"""
    try:
        log_message(f"Executing command: {command}", "info")
        
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
        
        log_message(f"Command output: {output[:200]}{'...' if len(output) > 200 else ''}", "success")
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

def test_basic_connection():
    """Test basic HTTP connection to controller"""
    try:
        import requests
        log_message(f"Testing HTTP connection to {controller_url}")
        
        response = requests.get(f"{controller_url}/", timeout=10)
        if response.status_code in [200, 302]:  # 302 is redirect to login
            log_message("✅ HTTP connection successful")
            return True
        else:
            log_message(f"❌ HTTP connection failed: {response.status_code}", "error")
            return False
            
    except ImportError:
        log_message("❌ requests library not available", "error")
        return False
    except Exception as e:
        log_message(f"❌ HTTP connection failed: {e}", "error")
        return False

def interactive_command_loop():
    """Interactive command input loop"""
    log_message("🎮 Interactive mode enabled. Type commands to execute on the agent.", "info")
    log_message("Type 'exit' or 'quit' to stop, 'help' for available commands.", "info")
    
    while connected and not shutdown_requested:
        try:
            command = input("\n💻 Enter command: ").strip()
            
            if command.lower() in ['exit', 'quit']:
                log_message("Exiting interactive mode...", "info")
                break
            elif command.lower() == 'help':
                print("\n📋 Available commands:")
                print("  - Any system command (dir, ls, pwd, etc.)")
                print("  - 'status' - Show connection status")
                print("  - 'ping' - Send ping to controller")
                print("  - 'exit' or 'quit' - Exit interactive mode")
                continue
            elif command.lower() == 'status':
                print_connection_status()
                continue
            elif command.lower() == 'ping':
                if sio and connected:
                    sio.emit('ping', {
                        'agent_id': AGENT_ID,
                        'timestamp': time.time(),
                        'uptime': time.time() - connection_start_time if connection_start_time else 0
                    })
                    log_message("Ping sent to controller", "info")
                else:
                    log_message("Not connected to controller", "error")
                continue
            elif not command:
                continue
            
            # Execute command locally and send result to controller
            output = execute_command(command)
            
            # Send command result to controller
            if sio and connected:
                sio.emit('command_result', {
                    'agent_id': AGENT_ID,
                    'command': command,
                    'output': output,
                    'success': True,
                    'timestamp': time.time()
                })
                log_message("Command result sent to controller", "success")
            else:
                log_message("Not connected to controller, result not sent", "warning")
                
        except KeyboardInterrupt:
            log_message("🛑 Interactive mode interrupted", "warning")
            break
        except EOFError:
            log_message("🛑 Input stream closed", "warning")
            break
        except Exception as e:
            log_message(f"❌ Error in interactive mode: {e}", "error")

def print_connection_status():
    """Print current connection status"""
    print("\n" + "="*50)
    print("📊 CONNECTION STATUS")
    print("="*50)
    print(f"Controller URL: {controller_url}")
    print(f"Agent ID: {AGENT_ID}")
    print(f"Connection Status: {'✅ Connected' if connected else '❌ Disconnected'}")
    
    if connection_start_time:
        uptime = time.time() - connection_start_time
        print(f"Connection Duration: {uptime:.1f} seconds")
    
    print(f"Messages Received: {message_count}")
    if last_heartbeat:
        print(f"Last Heartbeat: {time.time() - last_heartbeat:.1f}s ago")
    else:
        print("Last Heartbeat: No heartbeat received")
    print("="*50)

def test_socketio_connection():
    """Test Socket.IO connection to controller with command handling"""
    global sio
    
    try:
        import socketio
        
        log_message("Testing Socket.IO connection...")
        
        # Create Socket.IO client
        sio = socketio.Client(
            ssl_verify=False,  # Disable SSL verification for local testing
            engineio_logger=False,
            logger=False
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
                'name': f'Simple-Client-{AGENT_ID.split("-")[-1]}',
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
            
            # Register with controller
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
            log_message(f"📡 Heartbeat received (message #{message_count})", "info")
        
        @sio.event
        def command(data):
            """Handle command execution requests from controller"""
            global message_count
            message_count += 1
            
            command_text = data.get('command', '')
            execution_id = data.get('execution_id', 'unknown')
            
            log_message(f"📨 Command received: {command_text}", "info")
            log_message(f"📋 Execution ID: {execution_id}", "info")
            
            # Execute the command
            output = execute_command(command_text)
            
            # Send command result back to controller
            sio.emit('command_result', {
                'agent_id': AGENT_ID,
                'execution_id': execution_id,
                'command': command_text,
                'output': output,
                'success': True,
                'execution_time': 0,  # Could measure actual execution time
                'timestamp': time.time()
            })
            
            log_message("📤 Command result sent to controller", "success")
        
        @sio.event
        def agent_registered(data):
            log_message(f"✅ Agent registration confirmed: {data}", "success")
        
        @sio.event
        def agent_list_update(data):
            log_message(f"📋 Agent list updated: {len(data)} agents", "info")
            for agent_id, agent_data in data.items():
                status = agent_data.get('status', 'unknown')
                name = agent_data.get('name', agent_id)
                log_message(f"   - {name} ({agent_id}): {status}", "info")
        
        @sio.event
        def registration_error(data):
            log_message(f"❌ Registration error: {data}", "error")
        
        # Connect to controller
        log_message(f"Connecting to {controller_url}...", "info")
        sio.connect(controller_url, wait_timeout=CONNECTION_TIMEOUT)
        
        # Start interactive mode if requested
        if interactive_mode:
            interactive_command_loop()
        else:
            # Keep connection alive and send heartbeats
            try:
                while connected and not shutdown_requested:
                    time.sleep(HEARTBEAT_INTERVAL)
                    
                    if connected and not shutdown_requested:
                        # Send ping
                        sio.emit('ping', {
                            'agent_id': AGENT_ID,
                            'timestamp': time.time(),
                            'uptime': time.time() - connection_start_time if connection_start_time else 0
                        })
                        
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
    global controller_url, interactive_mode
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Enhanced Simple Client for Controller Testing')
    parser.add_argument('--url', default=DEFAULT_CONTROLLER_URL, 
                       help=f'Controller URL (default: {DEFAULT_CONTROLLER_URL})')
    parser.add_argument('--interactive', '-i', action='store_true',
                       help='Enable interactive command mode')
    
    args = parser.parse_args()
    controller_url = args.url
    interactive_mode = args.interactive
    
    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print("🚀 Enhanced Simple Client - Controller Testing Tool")
    print("=" * 60)
    print(f"Target Controller: {controller_url}")
    print(f"Agent ID: {AGENT_ID}")
    print(f"Interactive Mode: {'✅ Enabled' if interactive_mode else '❌ Disabled'}")
    print("=" * 60)
    
    # Test 1: Basic HTTP connection
    log_message("Starting connection tests...", "info")
    http_success = test_basic_connection()
    
    if not http_success:
        log_message("❌ Basic HTTP connection failed. Check controller URL and network.", "error")
        return False
    
    # Test 2: Socket.IO connection
    log_message("HTTP connection OK, testing Socket.IO...", "info")
    socketio_success = test_socketio_connection()
    
    # Print final summary
    print_connection_status()
    
    if socketio_success and connected:
        log_message("✅ All connection tests passed!", "success")
        return True
    else:
        log_message("❌ Connection tests failed", "error")
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