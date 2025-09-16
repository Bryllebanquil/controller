#!/usr/bin/env python3
"""
Quick Test Client
================

Quickly tests agent connection to the deployed controller.
"""

import time
import sys

# Try to import socketio
try:
    import socketio
    print("✅ python-socketio is available")
except ImportError:
    print("❌ python-socketio not available")
    print("This script needs python-socketio to run")
    print("The controller should still work with other clients that have it")
    sys.exit(1)

# Configuration
CONTROLLER_URL = 'https://agent-controller-backend.onrender.com'
AGENT_ID = f"quick-test-{int(time.time())}"

def test_connection():
    print(f"🔌 Testing connection to {CONTROLLER_URL}")
    print(f"🆔 Agent ID: {AGENT_ID}")
    print("-" * 50)
    
    # Create client
    sio = socketio.Client(ssl_verify=True)
    
    @sio.event
    def connect():
        print("✅ Connected to controller!")
        
        # Register as agent
        registration_data = {
            'agent_id': AGENT_ID,
            'name': f'QuickTest-{AGENT_ID.split("-")[-1]}',
            'platform': 'test',
            'python_version': '3.9',
            'timestamp': time.time(),
            'capabilities': ['test'],
            'cpu_usage': 10,
            'memory_usage': 20,
            'network_usage': 1
        }
        
        print("📝 Registering agent...")
        sio.emit('agent_register', registration_data)
    
    @sio.event
    def agent_registered(data):
        print(f"✅ Agent registered: {data}")
    
    @sio.event
    def agent_list_update(data):
        print(f"📋 Agent list update: {len(data)} agents")
        if AGENT_ID in data:
            print(f"✅ Our agent is in the list!")
        else:
            print("❌ Our agent not found in list")
    
    @sio.event
    def disconnect():
        print("❌ Disconnected from controller")
    
    @sio.event
    def connect_error(data):
        print(f"❌ Connection error: {data}")
    
    try:
        # Connect
        print("🔄 Connecting...")
        sio.connect(CONTROLLER_URL, wait_timeout=30)
        
        # Wait a bit
        print("⏳ Waiting for events...")
        time.sleep(10)
        
        # Disconnect
        sio.disconnect()
        print("✅ Test completed")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    test_connection()