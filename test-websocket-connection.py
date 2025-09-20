#!/usr/bin/env python3
"""
Test script to verify WebSocket connection and command result broadcasting
"""
import socketio
import time
import json

# Create a SocketIO client to simulate the UI
sio = socketio.Client()

@sio.event
def connect():
    print("✅ Connected to server")
    print(f"Socket ID: {sio.sid}")
    
    # Join operators room like the UI does
    print("📡 Emitting operator_connect...")
    sio.emit('operator_connect')
    
    print("📡 Emitting join_room 'operators'...")
    sio.emit('join_room', 'operators')

@sio.event
def disconnect():
    print("❌ Disconnected from server")

@sio.event
def joined_room(room):
    print(f"✅ Successfully joined room: {room}")

@sio.event
def command_result(data):
    print("🎉 COMMAND RESULT RECEIVED!")
    print(f"Agent ID: {data.get('agent_id')}")
    print(f"Command: {data.get('command')}")
    print(f"Output length: {len(data.get('output', ''))}")
    print(f"Success: {data.get('success')}")
    print("---")
    print("First 200 chars of output:")
    print(data.get('output', '')[:200])
    print("---")

@sio.event
def agent_list_update(data):
    print(f"📋 Agent list update received: {len(data)} agents")
    for agent_id, agent_info in data.items():
        print(f"  - {agent_id}: {agent_info.get('name', 'Unknown')}")

def test_connection():
    try:
        # Connect to the server
        print("🔌 Connecting to server...")
        sio.connect('http://localhost:8080')
        
        # Wait for events
        print("⏳ Waiting for events... (Press Ctrl+C to exit)")
        sio.wait()
        
    except KeyboardInterrupt:
        print("\n👋 Disconnecting...")
        sio.disconnect()
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_connection()