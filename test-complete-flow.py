#!/usr/bin/env python3
"""
Complete test of the command execution flow:
1. Start a mock agent (simple client)
2. Connect as operator
3. Send command
4. Verify response
"""
import socketio
import threading
import time
import json
import subprocess
import sys
import os

def test_agent_connection():
    """Test agent connection and command execution"""
    print("🤖 Testing agent connection and command execution...")
    
    # Agent socket
    agent_sio = socketio.Client()
    agent_connected = False
    command_received = False
    
    @agent_sio.event
    def connect():
        nonlocal agent_connected
        agent_connected = True
        print("✅ Agent connected")
        
        # Register as agent
        agent_sio.emit('agent_connect', {
            'agent_id': 'test-agent-123',
            'name': 'Test Agent',
            'platform': 'linux',
            'capabilities': ['commands', 'screen']
        })
    
    @agent_sio.event
    def command(data):
        nonlocal command_received
        command_received = True
        command_text = data.get('command', '')
        execution_id = data.get('execution_id', '')
        
        print(f"📝 Agent received command: {command_text}")
        print(f"📝 Execution ID: {execution_id}")
        
        # Simulate command execution
        if command_text == 'test':
            output = "Test command executed successfully!"
        else:
            output = f"Command '{command_text}' executed"
        
        # Send result back
        result = {
            'agent_id': 'test-agent-123',
            'execution_id': execution_id,
            'command': command_text,
            'output': output,
            'success': True,
            'execution_time': 0.1
        }
        
        print(f"📤 Sending command result: {result}")
        agent_sio.emit('command_result', result)
    
    # Connect agent
    try:
        agent_sio.connect('http://localhost:8080')
        time.sleep(2)  # Wait for registration
        
        if not agent_connected:
            print("❌ Agent failed to connect")
            return False
            
        print("✅ Agent registered successfully")
        return agent_sio, command_received
        
    except Exception as e:
        print(f"❌ Agent connection failed: {e}")
        return False

def test_operator_connection_and_command():
    """Test operator connection and command sending"""
    print("👨‍💻 Testing operator connection and command execution...")
    
    # Operator socket
    operator_sio = socketio.Client()
    operator_connected = False
    room_joined = False
    command_result_received = False
    test_message_received = False
    
    @operator_sio.event
    def connect():
        nonlocal operator_connected
        operator_connected = True
        print("✅ Operator connected")
        
        # Join operators room
        operator_sio.emit('operator_connect')
        operator_sio.emit('join_room', 'operators')
    
    @operator_sio.event
    def joined_room(room):
        nonlocal room_joined
        if room == 'operators':
            room_joined = True
            print(f"✅ Operator joined room: {room}")
    
    @operator_sio.event
    def test_message(data):
        nonlocal test_message_received
        test_message_received = True
        print(f"🧪 Test message received: {data}")
    
    @operator_sio.event
    def command_result(data):
        nonlocal command_result_received
        command_result_received = True
        print(f"🎉 COMMAND RESULT RECEIVED!")
        print(f"   Agent: {data.get('agent_id')}")
        print(f"   Command: {data.get('command')}")
        print(f"   Output: {data.get('output')}")
        print(f"   Success: {data.get('success')}")
    
    # Connect operator
    try:
        operator_sio.connect('http://localhost:8080')
        time.sleep(2)  # Wait for room joining
        
        if not operator_connected:
            print("❌ Operator failed to connect")
            return False
        
        if not room_joined:
            print("❌ Operator failed to join operators room")
            return False
        
        if not test_message_received:
            print("⚠️ Test message not received (connection might be weak)")
        
        # Send test command
        print("📡 Sending test command...")
        operator_sio.emit('execute_command', {
            'agent_id': 'test-agent-123',
            'command': 'test'
        })
        
        # Wait for response
        time.sleep(3)
        
        if command_result_received:
            print("✅ Command result received successfully!")
            return True
        else:
            print("❌ Command result not received")
            return False
            
    except Exception as e:
        print(f"❌ Operator connection failed: {e}")
        return False
    finally:
        operator_sio.disconnect()

def main():
    print("🚀 Starting complete command flow test...\n")
    
    # Test 1: Agent connection
    agent_result = test_agent_connection()
    if not agent_result:
        print("❌ Agent test failed")
        return False
    
    agent_sio, command_received = agent_result
    print()
    
    # Test 2: Operator connection and command
    operator_result = test_operator_connection_and_command()
    
    # Cleanup
    agent_sio.disconnect()
    
    if operator_result:
        print("\n✅ ALL TESTS PASSED! Command flow is working correctly.")
        return True
    else:
        print("\n❌ TESTS FAILED! Command flow has issues.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)