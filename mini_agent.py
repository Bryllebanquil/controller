#!/usr/bin/env python3
import os
import time
import socketio
import sys
import platform

SERVER_URL = os.environ.get('SERVER_URL', 'https://agent-controller-backend.onrender.com')
AGENT_ID = os.environ.get('AGENT_ID', f"mini-agent-{int(time.time())}")

sio = socketio.Client(ssl_verify=True, engineio_logger=False, logger=False)

@sio.event
def connect():
    print(f"[mini-agent] Connected. Registering as {AGENT_ID}")
    sio.emit('agent_connect', {
        'agent_id': AGENT_ID,
        'platform': sys.platform,
        'python_version': sys.version,
        'capabilities': ['screen','files','commands']
    })

@sio.event
def disconnect():
    print("[mini-agent] Disconnected")

def main():
    print(f"[mini-agent] Connecting to {SERVER_URL} as {AGENT_ID}")
    sio.connect(SERVER_URL, wait_timeout=15)
    try:
        while True:
            sio.emit('ping', {
                'agent_id': AGENT_ID,
                'timestamp': time.time(),
                'uptime': int(time.time())
            })
            time.sleep(5)
    except KeyboardInterrupt:
        pass
    finally:
        sio.disconnect()

if __name__ == '__main__':
    main()

