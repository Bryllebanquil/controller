#!/usr/bin/env python3

import socketio
import time
import uuid
import platform
import threading
import requests

def test_complete_solution():
    """Test the complete solution with proper frontend configuration"""
    print("🔧 COMPLETE SOLUTION TEST")
    print("=" * 60)
    
    # Test 1: Verify backend is accessible
    print("1. Testing backend accessibility...")
    try:
        response = requests.get("https://agent-controller-backend.onrender.com", timeout=10)
        print(f"   ✓ Backend accessible: {response.status_code}")
    except Exception as e:
        print(f"   ✗ Backend error: {e}")
        return
    
    # Test 2: Connect agent to backend
    print("2. Connecting agent to backend...")
    sio = socketio.Client()
    agent_id = str(uuid.uuid4())
    
    @sio.event
    def connect():
        print("   ✓ Agent connected to backend!")
        
        # Register agent
        sio.emit('agent_connect', {
            'agent_id': agent_id,
            'name': f'TestAgent-{agent_id[:8]}',
            'platform': platform.system(),
            'hostname': platform.node(),
            'ip': '127.0.0.1',
            'capabilities': ['commands', 'file_transfer'],
            'cpu_usage': 0,
            'memory_usage': 0,
            'network_usage': 0
        })
        print("   ✓ Agent registered with backend")
        
        # Send heartbeat
        def heartbeat():
            while sio.connected:
                time.sleep(5)
                sio.emit('agent_heartbeat', {
                    'agent_id': agent_id,
                    'timestamp': time.time()
                })
        
        threading.Thread(target=heartbeat, daemon=True).start()
        print("   ✓ Heartbeat started")
        
        # Keep running
        time.sleep(30)
    
    @sio.event
    def connect_error(data):
        print(f"   ✗ Connection error: {data}")
    
    @sio.event
    def disconnect():
        print("   Disconnected from backend")
    
    try:
        sio.connect('https://agent-controller-backend.onrender.com', wait_timeout=15)
    except Exception as e:
        print(f"Connection failed: {e}")
    finally:
        if sio.connected:
            sio.disconnect()

if __name__ == "__main__":
    test_complete_solution()