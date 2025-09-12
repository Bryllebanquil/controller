#!/usr/bin/env python3

import socketio
import time
import uuid
import platform
import threading

def test_complete_flow():
    """Test the complete agent-controller-frontend flow"""
    print("🔍 COMPREHENSIVE FLOW TEST")
    print("=" * 60)
    
    # Test 1: Connect to backend
    print("1. Testing backend connection...")
    sio = socketio.Client()
    
    agent_id = str(uuid.uuid4())
    print(f"   Agent ID: {agent_id}")
    
    @sio.event
    def connect():
        print("   ✓ Connected to backend!")
        
        # Test 2: Register as agent
        print("2. Registering as agent...")
        sio.emit('agent_connect', {'agent_id': agent_id})
        print("   ✓ Agent registration sent")
        
        # Test 3: Send system info
        print("3. Sending system info...")
        system_info = {
            'agent_id': agent_id,
            'name': f'TestAgent-{agent_id[:8]}',
            'platform': platform.system(),
            'hostname': platform.node(),
            'python_version': platform.python_version(),
            'ip': '127.0.0.1',
            'capabilities': ['commands', 'file_transfer'],
            'cpu_usage': 0,
            'memory_usage': 0,
            'network_usage': 0,
            'system_info': {
                'os': platform.system(),
                'version': platform.version(),
                'machine': platform.machine()
            },
            'uptime': 0
        }
        sio.emit('system_info', system_info)
        print("   ✓ System info sent")
        
        # Test 4: Send heartbeat
        print("4. Starting heartbeat...")
        def send_heartbeat():
            while True:
                time.sleep(5)  # Send heartbeat every 5 seconds
                if sio.connected:
                    sio.emit('agent_heartbeat', {
                        'agent_id': agent_id,
                        'timestamp': time.time()
                    })
                    print("   ✓ Heartbeat sent")
        
        heartbeat_thread = threading.Thread(target=send_heartbeat, daemon=True)
        heartbeat_thread.start()
        
        # Test 5: Simulate operator connection
        print("5. Simulating operator connection...")
        time.sleep(2)
        sio.emit('operator_connect')
        print("   ✓ Operator connect sent")
        
        print("\n✅ ALL TESTS COMPLETED")
        print("Agent should now be visible in frontend if frontend is connected to backend")
        print("Check the frontend dashboard to see if the agent appears")
        
        # Keep running for 30 seconds
        time.sleep(30)
    
    @sio.event
    def connect_error(data):
        print(f"   ✗ Connection error: {data}")
    
    @sio.event
    def disconnect():
        print("   Disconnected from backend")
    
    # Listen for agent_list_update (this should be sent to operators)
    @sio.on('agent_list_update')
    def on_agent_list_update(data):
        print(f"   📡 Received agent_list_update: {len(data)} agents")
        for agent_id, agent_data in data.items():
            print(f"      - {agent_id}: {agent_data.get('name', 'Unknown')}")
    
    try:
        print("Connecting to backend...")
        sio.connect('https://agent-controller-backend.onrender.com', wait_timeout=15)
    except Exception as e:
        print(f"Connection failed: {e}")
    finally:
        if sio.connected:
            sio.disconnect()

if __name__ == "__main__":
    test_complete_flow()