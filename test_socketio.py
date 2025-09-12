#!/usr/bin/env python3

import socketio
import time

def test_socketio_connection():
    """Test Socket.IO connection to backend"""
    print("Testing Socket.IO connection...")
    
    sio = socketio.Client()
    
    @sio.event
    def connect():
        print("✓ Connected to Socket.IO server!")
        sio.emit('test', {'message': 'Hello from test client'})
    
    @sio.event
    def connect_error(data):
        print(f"✗ Connection error: {data}")
    
    @sio.event
    def disconnect():
        print("Disconnected from Socket.IO server")
    
    try:
        print("Attempting to connect...")
        sio.connect('https://agent-controller-backend.onrender.com', wait_timeout=15)
        time.sleep(2)
        sio.disconnect()
        print("Test completed successfully")
    except Exception as e:
        print(f"Test failed: {e}")

if __name__ == "__main__":
    test_socketio_connection()