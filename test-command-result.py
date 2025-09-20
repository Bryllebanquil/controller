#!/usr/bin/env python3
"""
Test Command Result Script
=========================

This script tests if command results are being sent properly from the client to the controller.

Usage:
    python3 test-command-result.py [--url CONTROLLER_URL]
"""

import os
import sys
import time
import json
import subprocess
import platform
import argparse
from datetime import datetime

def log_message(message, level="info"):
    """Simple logging function"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    colors = {
        "info": "\033[94m",
        "success": "\033[92m",
        "warning": "\033[93m",
        "error": "\033[91m",
        "debug": "\033[95m",
        "reset": "\033[0m"
    }
    
    color = colors.get(level, colors["info"])
    reset = colors["reset"]
    print(f"{color}[{timestamp}] {level.upper()}: {message}{reset}")

def test_socketio_connection():
    """Test Socket.IO connection with detailed command result logging"""
    try:
        import socketio
        
        log_message("🔌 Testing Socket.IO connection with command result logging...", "info")
        
        # Create Socket.IO client
        sio = socketio.Client(
            ssl_verify=False,
            engineio_logger=True,
            logger=True
        )
        
        agent_id = f"test-client-{int(time.time())}"
        
        # Connection event handlers
        @sio.event
        def connect():
            log_message("✅ Socket.IO connection established!", "success")
            
            # Send agent registration
            agent_data = {
                'agent_id': agent_id,
                'name': f'Test-Client-{agent_id.split("-")[-1]}',
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
            log_message("❌ Socket.IO connection lost", "warning")
        
        @sio.event
        def connect_error(data):
            log_message(f"❌ Socket.IO connection error: {data}", "error")
        
        @sio.event
        def command(data):
            """Handle command execution requests from controller"""
            log_message(f"📨 Command event received: {json.dumps(data, indent=2)}", "debug")
            
            command_text = data.get('command', '')
            execution_id = data.get('execution_id', 'unknown')
            
            log_message(f"📨 Command received: '{command_text}'", "info")
            log_message(f"📋 Execution ID: {execution_id}", "info")
            
            # Execute the command
            try:
                if platform.system() == "Windows":
                    result = subprocess.run(
                        ["powershell.exe", "-NoProfile", "-Command", command_text],
                        capture_output=True,
                        text=True,
                        timeout=30,
                        creationflags=subprocess.CREATE_NO_WINDOW
                    )
                else:
                    result = subprocess.run(
                        ["bash", "-c", command_text],
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                
                output = result.stdout + result.stderr
                if not output:
                    output = "[No output from command]"
                
                log_message(f"✅ Command executed successfully", "success")
                log_message(f"📄 Output: {output[:200]}{'...' if len(output) > 200 else ''}", "debug")
                
            except Exception as e:
                output = f"Command execution failed: {e}"
                log_message(f"❌ Command execution failed: {e}", "error")
            
            # Prepare command result
            result_data = {
                'agent_id': agent_id,
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
            for agent_id_item, agent_data in data.items():
                status = agent_data.get('status', 'unknown')
                name = agent_data.get('name', agent_id_item)
                log_message(f"   - {name} ({agent_id_item}): {status}", "info")
        
        @sio.event
        def registration_error(data):
            log_message(f"❌ Registration error: {json.dumps(data, indent=2)}", "error")
        
        # Connect to controller
        controller_url = "https://agent-controller-backend.onrender.com"
        log_message(f"🔌 Connecting to {controller_url}...", "info")
        sio.connect(controller_url, wait_timeout=30)
        
        # Keep connection alive
        try:
            while True:
                time.sleep(10)
                log_message("💓 Heartbeat - waiting for commands...", "info")
        except KeyboardInterrupt:
            log_message("🛑 Interrupted by user", "warning")
        except Exception as e:
            log_message(f"❌ Connection error: {e}", "error")
        
        return True
        
    except ImportError:
        log_message("❌ python-socketio library not available", "error")
        return False
    except Exception as e:
        log_message(f"❌ Socket.IO connection failed: {e}", "error")
        return False
    finally:
        if sio:
            sio.disconnect()
            log_message("🔌 Disconnected from controller", "info")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Test Command Result Script')
    parser.add_argument('--url', default='https://agent-controller-backend.onrender.com',
                       help='Controller URL')
    
    args = parser.parse_args()
    
    print("🧪 Test Command Result Script")
    print("=" * 50)
    print(f"Controller URL: {args.url}")
    print("=" * 50)
    
    log_message("🚀 Starting command result test...", "info")
    log_message("📋 Instructions:", "info")
    log_message("1. Open browser to your controller dashboard", "info")
    log_message("2. Login and go to Agents tab", "info")
    log_message("3. Select the test client agent", "info")
    log_message("4. Go to Commands tab and execute a command", "info")
    log_message("5. Check browser console (F12) for debug logs", "info")
    log_message("6. Check this terminal for client-side logs", "info")
    
    # Test Socket.IO connection
    test_socketio_connection()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log_message("🛑 Test interrupted by user", "warning")
    except Exception as e:
        log_message(f"❌ Unexpected error: {e}", "error")