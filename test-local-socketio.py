#!/usr/bin/env python3
"""
Test Socket.IO server locally to verify it works before deployment
"""
import subprocess
import time
import socketio
import threading
import sys

def test_socketio_server():
    """Test if the Socket.IO server can start and accept connections"""
    print("🧪 Testing Socket.IO server locally...")
    
    # Start the server in a separate thread
    def start_server():
        try:
            subprocess.run([sys.executable, 'controller.py'], 
                          capture_output=True, 
                          timeout=10)
        except subprocess.TimeoutExpired:
            pass  # Expected - server should keep running
        except Exception as e:
            print(f"❌ Server failed to start: {e}")
    
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()
    
    # Wait for server to start
    time.sleep(3)
    
    # Test client connection
    client = socketio.Client()
    connected = False
    test_message_received = False
    
    @client.event
    def connect():
        nonlocal connected
        connected = True
        print("✅ Client connected to server")
        client.emit('operator_connect')
    
    @client.event
    def test_message(data):
        nonlocal test_message_received
        test_message_received = True
        print(f"✅ Test message received: {data}")
    
    @client.event
    def joined_room(room):
        print(f"✅ Joined room: {room}")
    
    try:
        print("🔌 Connecting client to server...")
        client.connect('http://localhost:8080', wait_timeout=5)
        time.sleep(2)
        
        if connected:
            print("✅ Socket.IO server is working correctly!")
            return True
        else:
            print("❌ Failed to connect to Socket.IO server")
            return False
            
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        return False
    finally:
        try:
            client.disconnect()
        except:
            pass

if __name__ == "__main__":
    success = test_socketio_server()
    sys.exit(0 if success else 1)