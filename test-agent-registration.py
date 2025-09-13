#!/usr/bin/env python3
"""
Test Agent Registration
======================

This script tests the agent registration process step by step
to see where the issue might be.
"""

import socketio
import time
import sys
import json

# Configuration
CONTROLLER_URL = 'https://agent-controller-backend.onrender.com'
AGENT_ID = f"test-agent-{int(time.time())}"

def test_agent_registration():
    print("🧪 Testing Agent Registration Process")
    print("=" * 50)
    print(f"Controller URL: {CONTROLLER_URL}")
    print(f"Agent ID: {AGENT_ID}")
    print("=" * 50)
    
    # Create Socket.IO client
    sio = socketio.Client(
        ssl_verify=False,
        engineio_logger=True,  # Enable logging to see what's happening
        logger=True
    )
    
    # Event handlers
    @sio.event
    def connect():
        print("✅ Connected to controller")
        
        # Test 1: Send agent registration
        print("\n📝 Test 1: Sending agent registration...")
        registration_data = {
            'agent_id': AGENT_ID,
            'platform': sys.platform,
            'python_version': sys.version,
            'timestamp': time.time()
        }
        print(f"Registration data: {json.dumps(registration_data, indent=2)}")
        sio.emit('agent_register', registration_data)
    
    @sio.event
    def agent_registered(data):
        print(f"✅ Registration confirmed: {data}")
    
    @sio.event
    def agent_list_update(data):
        print(f"📋 Agent list update received:")
        print(f"   Total agents: {len(data)}")
        for agent_id, agent_data in data.items():
            print(f"   - {agent_id}: {agent_data}")
    
    @sio.event
    def registration_error(data):
        print(f"❌ Registration error: {data}")
    
    @sio.event
    def disconnect():
        print("❌ Disconnected from controller")
    
    @sio.event
    def connect_error(data):
        print(f"❌ Connection error: {data}")
    
    # Connect and test
    try:
        print("🔌 Connecting to controller...")
        sio.connect(CONTROLLER_URL, wait_timeout=30)
        
        # Wait for registration to complete
        print("\n⏳ Waiting for registration to complete...")
        time.sleep(5)
        
        # Test 2: Send ping to test heartbeat
        print("\n📝 Test 2: Sending ping...")
        sio.emit('ping', {
            'agent_id': AGENT_ID,
            'timestamp': time.time(),
            'uptime': 5
        })
        
        # Wait for pong
        time.sleep(2)
        
        # Test 3: Check if we're in the agent list
        print("\n📝 Test 3: Checking agent list...")
        # We can't directly query the agent list, but we should have received updates
        
        print("\n✅ Test completed. Check the output above for any issues.")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
    finally:
        if sio.connected:
            sio.disconnect()
            print("🔌 Disconnected")

if __name__ == "__main__":
    test_agent_registration()