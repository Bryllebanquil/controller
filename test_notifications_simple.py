#!/usr/bin/env python3
"""
Simple Notification Test Script
Quick test to verify notification popup system
"""

import socketio
import time
import uuid

# Configuration
CONTROLLER_URL = "http://localhost:5000"
AGENT_ID = f"test-{uuid.uuid4().hex[:8]}"

# Create Socket.IO client
sio = socketio.Client()

@sio.event
def connect():
    print(f"✅ Connected to controller!")
    print(f"📝 Registering as agent: {AGENT_ID}\n")
    
    # Register as agent
    sio.emit('agent_connect', {
        'agent_id': AGENT_ID,
        'hostname': 'test-host',
        'username': 'test-user',
        'os': 'Windows 10',
        'ip': '127.0.0.1'
    })
    
    time.sleep(1)
    
    # Send test notifications
    print("📤 Sending test notifications...\n")
    
    # Success notification
    print("1️⃣ Success notification (Camera Stream)")
    sio.emit('agent_notification', {
        'agent_id': AGENT_ID,
        'type': 'success',
        'title': 'Camera Stream Started',
        'message': 'Camera streaming started successfully',
        'category': 'agent'
    })
    time.sleep(3)
    
    # Warning notification
    print("2️⃣ Warning notification (Already Active)")
    sio.emit('agent_notification', {
        'agent_id': AGENT_ID,
        'type': 'warning',
        'title': 'Stream Already Active',
        'message': 'Screen streaming is already running',
        'category': 'agent'
    })
    time.sleep(3)
    
    # Error notification
    print("3️⃣ Error notification (File Not Found)")
    sio.emit('agent_notification', {
        'agent_id': AGENT_ID,
        'type': 'error',
        'title': 'File Not Found',
        'message': 'File document.pdf not found on agent',
        'category': 'system'
    })
    time.sleep(3)
    
    # Info notification
    print("4️⃣ Info notification (Download Started)")
    sio.emit('agent_notification', {
        'agent_id': AGENT_ID,
        'type': 'info',
        'title': 'File Download Started',
        'message': 'Starting download of report.xlsx (5.2 MB)',
        'category': 'system'
    })
    time.sleep(3)
    
    # Command notification
    print("5️⃣ Command notification (Executed)")
    sio.emit('agent_notification', {
        'agent_id': AGENT_ID,
        'type': 'success',
        'title': 'Command Executed',
        'message': 'Command "systeminfo" executed successfully',
        'category': 'command'
    })
    time.sleep(3)
    
    print("\n✅ All test notifications sent!")
    print("🔔 Check the dashboard for popup notifications!")
    print("⏳ Waiting 5 seconds before disconnecting...\n")
    time.sleep(5)
    
    sio.disconnect()

@sio.event
def disconnect():
    print("👋 Disconnected from controller\n")

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🧪 SIMPLE NOTIFICATION TEST")
    print("="*60)
    print(f"Controller: {CONTROLLER_URL}")
    print(f"Agent ID: {AGENT_ID}")
    print("="*60 + "\n")
    
    try:
        print("📡 Connecting to controller...")
        sio.connect(CONTROLLER_URL)
        sio.wait()
        
        print("\n" + "="*60)
        print("✅ TEST COMPLETED!")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error: {e}\n")
