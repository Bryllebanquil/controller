#!/usr/bin/env python3

import os
import sys
import time

# Add current directory to path
sys.path.insert(0, '.')

try:
    # Test basic imports
    print("Testing imports...")
    import requests
    print("✓ requests imported")
    
    # Test server URL
    SERVER_URL = "https://agent-controller-backend.onrender.com"
    print(f"Testing connection to: {SERVER_URL}")
    
    # Test HTTP connection
    try:
        response = requests.get(SERVER_URL, timeout=10)
        print(f"✓ HTTP connection successful: {response.status_code}")
    except Exception as e:
        print(f"✗ HTTP connection failed: {e}")
    
    # Test Socket.IO connection
    try:
        import socketio
        print("✓ socketio imported")
        
        sio = socketio.Client()
        
        @sio.event
        def connect():
            print("✓ Socket.IO connected successfully!")
            sio.disconnect()
        
        @sio.event
        def connect_error(data):
            print(f"✗ Socket.IO connection error: {data}")
        
        print("Attempting Socket.IO connection...")
        sio.connect(SERVER_URL, wait_timeout=10)
        
    except ImportError:
        print("✗ socketio not available")
    except Exception as e:
        print(f"✗ Socket.IO connection failed: {e}")
        
except Exception as e:
    print(f"✗ Test failed: {e}")