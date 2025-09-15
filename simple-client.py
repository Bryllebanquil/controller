#!/usr/bin/env python3
"""
Simple Client for Controller Connection Test
============================================

This is a minimal version of client.py that only tests the connection
to the controller without any complex features like screen capture,
audio processing, or system monitoring.

Usage:
    python3 simple-client.py

Features:
    - Basic Socket.IO connection to controller
    - Connection status monitoring
    - Simple heartbeat/ping functionality
    - Minimal logging
    - Graceful error handling
"""

import os
import sys
import time
import json
import logging
from datetime import datetime

# Configure simple logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Configuration
CONTROLLER_URL = os.environ.get('CONTROLLER_URL', 'https://agent-controller-backend.onrender.com')
AGENT_ID = f"simple-client-{int(time.time())}"
CONNECTION_TIMEOUT = 30
HEARTBEAT_INTERVAL = 10

# Connection status
connected = False
connection_start_time = None
last_heartbeat = None
message_count = 0

def log_message(message, level="info"):
    """Simple logging function"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {level.upper()}: {message}")

def test_basic_connection():
    """Test basic HTTP connection to controller"""
    try:
        import requests
        log_message(f"Testing HTTP connection to {CONTROLLER_URL}")
        
        response = requests.get(f"{CONTROLLER_URL}/", timeout=10)
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

def test_socketio_connection():
    """Test Socket.IO connection to controller"""
    try:
        import socketio
        
        log_message("Testing Socket.IO connection...")
        
        # Create Socket.IO client
        sio = socketio.Client(
            ssl_verify=True,  # Enable SSL verification for security
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
            log_message("✅ Socket.IO connection established!")
            
            # Send initial agent registration with comprehensive data
            sio.emit('agent_register', {
                'agent_id': AGENT_ID,
                'name': f'SimpleClient-{AGENT_ID.split("-")[-1]}',
                'platform': sys.platform,
                'python_version': sys.version.split()[0],  # Just version number
                'timestamp': time.time(),
                'capabilities': ['basic', 'ping', 'commands'],
                'cpu_usage': 0,
                'memory_usage': 0,
                'network_usage': 0,
                'system_info': {
                    'type': 'simple_client',
                    'version': '1.0'
                }
            })
            log_message("📝 Agent registration sent with comprehensive data")
        
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
            log_message(f"📡 Heartbeat received (message #{message_count})")
        
        @sio.event
        def agent_command(data):
            global message_count
            message_count += 1
            log_message(f"📨 Command received: {data}")
            
            # Send response
            sio.emit('agent_response', {
                'agent_id': AGENT_ID,
                'command_id': data.get('command_id'),
                'response': 'Command received by simple client',
                'timestamp': time.time()
            })
        
        @sio.event
        def agent_registered(data):
            log_message(f"✅ Agent registration confirmed: {data}")
        
        @sio.event
        def agent_list_update(data):
            log_message(f"📋 Agent list updated: {len(data)} agents")
            for agent_id, agent_data in data.items():
                log_message(f"   - {agent_id}: {agent_data.get('status', 'unknown')}")
        
        @sio.event
        def registration_error(data):
            log_message(f"❌ Registration error: {data}", "error")
        
        # Connect to controller
        log_message(f"Connecting to {CONTROLLER_URL}...")
        sio.connect(CONTROLLER_URL, wait_timeout=CONNECTION_TIMEOUT)
        
        # Keep connection alive and send heartbeats
        try:
            while connected:
                time.sleep(HEARTBEAT_INTERVAL)
                
                if connected:
                    # Send ping
                    sio.emit('ping', {
                        'agent_id': AGENT_ID,
                        'timestamp': time.time(),
                        'uptime': time.time() - connection_start_time if connection_start_time else 0
                    })
                    
                    # Check connection health
                    if last_heartbeat and (time.time() - last_heartbeat) > (HEARTBEAT_INTERVAL * 3):
                        log_message("❌ No heartbeat received, connection may be stale", "warning")
                
        except KeyboardInterrupt:
            log_message("🛑 Interrupted by user")
        except Exception as e:
            log_message(f"❌ Connection error: {e}", "error")
        finally:
            if connected:
                sio.disconnect()
                log_message("🔌 Disconnected from controller")
        
        return True
        
    except ImportError:
        log_message("❌ python-socketio library not available", "error")
        log_message("Install with: pip install python-socketio", "info")
        return False
    except Exception as e:
        log_message(f"❌ Socket.IO connection failed: {e}", "error")
        return False

def print_connection_summary():
    """Print connection test summary"""
    print("\n" + "="*60)
    print("🔍 CONNECTION TEST SUMMARY")
    print("="*60)
    print(f"Controller URL: {CONTROLLER_URL}")
    print(f"Agent ID: {AGENT_ID}")
    print(f"Connection Status: {'✅ Connected' if connected else '❌ Disconnected'}")
    
    if connection_start_time:
        uptime = time.time() - connection_start_time
        print(f"Connection Duration: {uptime:.1f} seconds")
    
    print(f"Messages Received: {message_count}")
    print(f"Last Heartbeat: {time.time() - last_heartbeat:.1f}s ago" if last_heartbeat else "No heartbeat received")
    print("="*60)

def main():
    """Main function"""
    print("🚀 Simple Client - Controller Connection Test")
    print("=" * 50)
    print(f"Target Controller: {CONTROLLER_URL}")
    print(f"Agent ID: {AGENT_ID}")
    print("=" * 50)
    
    # Test 1: Basic HTTP connection
    log_message("Starting connection tests...")
    http_success = test_basic_connection()
    
    if not http_success:
        log_message("❌ Basic HTTP connection failed. Check controller URL and network.", "error")
        return False
    
    # Test 2: Socket.IO connection
    log_message("HTTP connection OK, testing Socket.IO...")
    socketio_success = test_socketio_connection()
    
    # Print summary
    print_connection_summary()
    
    if socketio_success and connected:
        log_message("✅ All connection tests passed!")
        return True
    else:
        log_message("❌ Connection tests failed", "error")
        return False

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        log_message("🛑 Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        log_message(f"❌ Unexpected error: {e}", "error")
        sys.exit(1)