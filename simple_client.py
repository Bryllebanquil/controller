import socketio
import time
import sys
import os
import platform

# Server configuration
SERVER_URL = "http://127.0.0.1:8080"
AGENT_NAME = f"Test-Agent-{platform.node()}"
AGENT_ID = f"test-agent-{os.getpid()}"

print(f"[*] Starting Simple Test Client...")
print(f"[*] Target Server: {SERVER_URL}")
print(f"[*] Agent Name: {AGENT_NAME}")
print(f"[*] Agent ID: {AGENT_ID}")

sio = socketio.Client()

@sio.event
def connect():
    print(f"[+] Connected to server!")
    print(f"[*] Sending agent info...")
    
    # Send basic agent info
    agent_info = {
        'id': AGENT_ID,
        'name': AGENT_NAME,
        'platform': platform.system(),
        'version': '1.0.0',
        'ip': '127.0.0.1',
        'hostname': platform.node(),
        'username': os.getlogin() if hasattr(os, 'getlogin') else 'unknown',
        'status': 'online'
    }
    
    sio.emit('agent_connect', agent_info)
    print(f"[+] Agent connect payload sent.")

@sio.event
def disconnect():
    print("[-] Disconnected from server")

@sio.event
def connect_error(data):
    print(f"[!] Connection failed: {data}")

def main():
    try:
        sio.connect(SERVER_URL)
        print("[*] Connection initiated, waiting for events...")
        sio.wait()
    except Exception as e:
        print(f"[!] Critical Error: {e}")
        time.sleep(5)

if __name__ == '__main__':
    main()
