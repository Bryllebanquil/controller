#!/usr/bin/env python3
"""
Test script to verify command execution flow
"""

import socketio
import time
import json

# Test configuration
CONTROLLER_URL = "http://localhost:8080"  # Adjust as needed
AGENT_ID = f"test-agent-{int(time.time())}"

def test_command_flow():
    """Test the complete command execution flow"""
    print("🧪 Testing Command Execution Flow")
    print("=" * 50)
    
    # Create Socket.IO client
    sio = socketio.Client()
    
    # Track test results
    test_results = {
        'connected': False,
        'agent_registered': False,
        'command_sent': False,
        'command_received': False,
        'response_received': False
    }
    
    @sio.event
    def connect():
        print("✅ Connected to controller")
        test_results['connected'] = True
        
        # Register as agent
        agent_data = {
            'agent_id': AGENT_ID,
            'name': f'Test-Agent-{AGENT_ID.split("-")[-1]}',
            'platform': 'Test',
            'hostname': 'test-host',
            'python_version': '3.8',
            'timestamp': time.time(),
            'ip': '127.0.0.1',
            'capabilities': ['commands'],
            'cpu_usage': 0,
            'memory_usage': 0,
            'network_usage': 0
        }
        
        print(f"📝 Registering agent: {AGENT_ID}")
        sio.emit('agent_connect', agent_data)
    
    @sio.event
    def agent_registered(data):
        print("✅ Agent registration confirmed")
        test_results['agent_registered'] = True
    
    @sio.event
    def command(data):
        print(f"📨 Command received: {data}")
        test_results['command_received'] = True
        
        command_text = data.get('command', '')
        execution_id = data.get('execution_id', 'unknown')
        
        # Simulate command execution
        output = f"Test output for command: {command_text}"
        
        # Send result back
        result_data = {
            'agent_id': AGENT_ID,
            'execution_id': execution_id,
            'command': command_text,
            'output': output,
            'success': True,
            'execution_time': 0,
            'timestamp': time.time()
        }
        
        print(f"📤 Sending command result: {result_data}")
        sio.emit('command_result', result_data)
        test_results['response_received'] = True
    
    @sio.event
    def command_result(data):
        print(f"📥 Command result received: {data}")
    
    @sio.event
    def command_output(data):
        print(f"📥 Command output received: {data}")
    
    @sio.event
    def disconnect():
        print("❌ Disconnected from controller")
    
    try:
        # Connect to controller
        print(f"🔌 Connecting to {CONTROLLER_URL}...")
        sio.connect(CONTROLLER_URL)
        
        # Wait for connection and registration
        time.sleep(2)
        
        if test_results['connected'] and test_results['agent_registered']:
            print("✅ Agent is connected and registered")
            
            # Now test as operator
            print("🔌 Connecting as operator...")
            sio.emit('operator_connect')
            time.sleep(1)
            
            # Send test command
            test_command = "echo Hello World"
            print(f"📤 Sending test command: {test_command}")
            sio.emit('execute_command', {
                'agent_id': AGENT_ID,
                'command': test_command
            })
            test_results['command_sent'] = True
            
            # Wait for response
            print("⏳ Waiting for command response...")
            time.sleep(3)
            
        else:
            print("❌ Failed to connect or register agent")
            
    except Exception as e:
        print(f"❌ Error during test: {e}")
    
    finally:
        sio.disconnect()
    
    # Print test results
    print("\n📊 Test Results:")
    print("=" * 30)
    for test, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test}: {status}")
    
    # Overall result
    all_passed = all(test_results.values())
    print(f"\n🎯 Overall Result: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
    
    return all_passed

if __name__ == "__main__":
    test_command_flow()