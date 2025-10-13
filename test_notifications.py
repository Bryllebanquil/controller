#!/usr/bin/env python3
"""
Notification Popup Test Script
Tests the agent-to-controller-to-UI notification system
"""

import socketio
import time
import uuid
import sys
from datetime import datetime

# Configuration
CONTROLLER_URL = "http://localhost:5000"
AGENT_ID = f"test-agent-{uuid.uuid4().hex[:8]}"

# Create Socket.IO client
sio = socketio.Client(
    reconnection=True,
    reconnection_delay=1,
    reconnection_delay_max=5,
    logger=False,
    engineio_logger=False
)

# Test notification data
TEST_NOTIFICATIONS = [
    # Success notifications
    {
        'type': 'success',
        'category': 'agent',
        'title': 'Camera Stream Started',
        'message': 'Camera streaming started successfully with high quality'
    },
    {
        'type': 'success',
        'category': 'system',
        'title': 'File Saved',
        'message': 'File document.pdf saved successfully (2.5 MB)'
    },
    {
        'type': 'success',
        'category': 'command',
        'title': 'Command Executed',
        'message': 'Command "dir C:\\" executed successfully'
    },
    
    # Warning notifications
    {
        'type': 'warning',
        'category': 'agent',
        'title': 'Stream Already Active',
        'message': 'Screen streaming is already active'
    },
    {
        'type': 'warning',
        'category': 'system',
        'title': 'WebRTC Fallback',
        'message': 'Using Socket.IO streaming (WebRTC not available)'
    },
    {
        'type': 'warning',
        'category': 'agent',
        'title': 'Agent Disconnected',
        'message': 'Lost connection to controller'
    },
    
    # Error notifications
    {
        'type': 'error',
        'category': 'agent',
        'title': 'Camera Stream Failed',
        'message': 'Failed to start camera streaming: No camera device found'
    },
    {
        'type': 'error',
        'category': 'system',
        'title': 'File Not Found',
        'message': 'File important.txt not found on agent'
    },
    {
        'type': 'error',
        'category': 'command',
        'title': 'Command Failed',
        'message': 'Command execution failed: Access denied'
    },
    {
        'type': 'error',
        'category': 'security',
        'title': 'Remote Control Error',
        'message': 'Mouse control failed: Permission denied'
    },
    
    # Info notifications
    {
        'type': 'info',
        'category': 'agent',
        'title': 'Stream Not Active',
        'message': 'Audio streaming is not currently active'
    },
    {
        'type': 'info',
        'category': 'system',
        'title': 'File Download Started',
        'message': 'Starting download of report.xlsx (5.2 MB)'
    },
]

# Connection handlers
@sio.event
def connect():
    print(f"\n{'='*80}")
    print(f"✅ Connected to controller at {CONTROLLER_URL}")
    print(f"{'='*80}\n")
    
    # Register as agent
    print(f"📝 Registering as agent: {AGENT_ID}")
    sio.emit('agent_connect', {
        'agent_id': AGENT_ID,
        'hostname': 'test-agent-hostname',
        'username': 'test-user',
        'os': 'Windows 10',
        'ip': '127.0.0.1'
    })
    time.sleep(1)
    print(f"✅ Agent registered successfully\n")

@sio.event
def connect_error(data):
    print(f"❌ Connection error: {data}")
    sys.exit(1)

@sio.event
def disconnect():
    print(f"\n{'='*80}")
    print(f"❌ Disconnected from controller")
    print(f"{'='*80}\n")

# Notification confirmation handler
@sio.event
def notification_received(data):
    print(f"   📬 Controller confirmed notification receipt")

def send_notification(notification_data):
    """Send a test notification to the controller"""
    notification = {
        'agent_id': AGENT_ID,
        'type': notification_data['type'],
        'title': notification_data['title'],
        'message': notification_data['message'],
        'category': notification_data['category'],
        'timestamp': int(time.time() * 1000)
    }
    
    print(f"\n{'─'*80}")
    print(f"📤 Sending {notification_data['type'].upper()} notification:")
    print(f"   Category: {notification_data['category']}")
    print(f"   Title: {notification_data['title']}")
    print(f"   Message: {notification_data['message']}")
    
    sio.emit('agent_notification', notification)
    print(f"   ✅ Notification sent to controller")
    print(f"   🔔 Popup should appear in dashboard now!")
    print(f"{'─'*80}")

def test_streaming_notifications():
    """Test streaming-related notifications"""
    print(f"\n{'='*80}")
    print(f"🎥 TESTING STREAMING NOTIFICATIONS")
    print(f"{'='*80}")
    
    streaming_tests = [
        {
            'type': 'success',
            'category': 'agent',
            'title': 'Screen Stream Started',
            'message': 'Screen streaming started with high quality'
        },
        {
            'type': 'success',
            'category': 'agent',
            'title': 'Audio Stream Started',
            'message': 'Audio streaming started via WebRTC'
        },
        {
            'type': 'warning',
            'category': 'agent',
            'title': 'Camera Already Active',
            'message': 'Camera streaming is already running'
        },
        {
            'type': 'success',
            'category': 'agent',
            'title': 'Camera Stream Stopped',
            'message': 'Camera streaming stopped successfully'
        },
        {
            'type': 'error',
            'category': 'agent',
            'title': 'Stream Failed',
            'message': 'Failed to start streaming: Display capture error'
        }
    ]
    
    for notification in streaming_tests:
        send_notification(notification)
        time.sleep(2)

def test_file_operations():
    """Test file operation notifications"""
    print(f"\n{'='*80}")
    print(f"📁 TESTING FILE OPERATION NOTIFICATIONS")
    print(f"{'='*80}")
    
    file_tests = [
        {
            'type': 'info',
            'category': 'system',
            'title': 'File Download Started',
            'message': 'Starting download of document.pdf (1.5 MB)'
        },
        {
            'type': 'success',
            'category': 'system',
            'title': 'File Download Complete',
            'message': 'File document.pdf downloaded successfully (1.5 MB)'
        },
        {
            'type': 'success',
            'category': 'system',
            'title': 'File Saved',
            'message': 'File uploaded and saved to C:\\Users\\Admin\\file.txt'
        },
        {
            'type': 'success',
            'category': 'system',
            'title': 'File Deleted',
            'message': 'File temp.txt deleted successfully'
        },
        {
            'type': 'error',
            'category': 'system',
            'title': 'File Not Found',
            'message': 'File important.xlsx not found on agent'
        },
        {
            'type': 'error',
            'category': 'system',
            'title': 'File Save Failed',
            'message': 'Failed to save file: Disk full'
        }
    ]
    
    for notification in file_tests:
        send_notification(notification)
        time.sleep(2)

def test_command_execution():
    """Test command execution notifications"""
    print(f"\n{'='*80}")
    print(f"💻 TESTING COMMAND EXECUTION NOTIFICATIONS")
    print(f"{'='*80}")
    
    command_tests = [
        {
            'type': 'success',
            'category': 'command',
            'title': 'Command Executed',
            'message': 'Command "systeminfo" executed successfully'
        },
        {
            'type': 'success',
            'category': 'command',
            'title': 'Process List Retrieved',
            'message': 'Successfully retrieved 156 processes'
        },
        {
            'type': 'success',
            'category': 'command',
            'title': 'Directory Listed',
            'message': 'Listed 42 items in C:\\Users\\Admin'
        },
        {
            'type': 'error',
            'category': 'command',
            'title': 'Command Failed',
            'message': 'Command execution failed: Access denied'
        },
        {
            'type': 'error',
            'category': 'command',
            'title': 'Process List Failed',
            'message': 'Failed to retrieve process list: Permission error'
        }
    ]
    
    for notification in command_tests:
        send_notification(notification)
        time.sleep(2)

def test_security_notifications():
    """Test security-related notifications"""
    print(f"\n{'='*80}")
    print(f"🔒 TESTING SECURITY NOTIFICATIONS")
    print(f"{'='*80}")
    
    security_tests = [
        {
            'type': 'warning',
            'category': 'security',
            'title': 'UAC Prompt Detected',
            'message': 'User Account Control prompt requires attention'
        },
        {
            'type': 'error',
            'category': 'security',
            'title': 'Privilege Escalation Failed',
            'message': 'Failed to elevate privileges: User denied'
        },
        {
            'type': 'success',
            'category': 'security',
            'title': 'Admin Access Granted',
            'message': 'Successfully obtained administrator privileges'
        },
        {
            'type': 'error',
            'category': 'security',
            'title': 'Remote Control Error',
            'message': 'Mouse control failed: Insufficient permissions'
        }
    ]
    
    for notification in security_tests:
        send_notification(notification)
        time.sleep(2)

def test_connection_notifications():
    """Test connection-related notifications"""
    print(f"\n{'='*80}")
    print(f"🔌 TESTING CONNECTION NOTIFICATIONS")
    print(f"{'='*80}")
    
    connection_tests = [
        {
            'type': 'success',
            'category': 'agent',
            'title': 'Agent Connected',
            'message': f'Successfully connected as agent {AGENT_ID}'
        },
        {
            'type': 'warning',
            'category': 'agent',
            'title': 'Connection Unstable',
            'message': 'Network connection is unstable (high latency)'
        },
        {
            'type': 'error',
            'category': 'agent',
            'title': 'Connection Error',
            'message': 'Failed to establish WebRTC connection'
        }
    ]
    
    for notification in connection_tests:
        send_notification(notification)
        time.sleep(2)

def test_webrtc_notifications():
    """Test WebRTC-related notifications"""
    print(f"\n{'='*80}")
    print(f"🌐 TESTING WEBRTC NOTIFICATIONS")
    print(f"{'='*80}")
    
    webrtc_tests = [
        {
            'type': 'success',
            'category': 'system',
            'title': 'WebRTC Started',
            'message': 'WebRTC streaming started successfully'
        },
        {
            'type': 'warning',
            'category': 'system',
            'title': 'WebRTC Fallback',
            'message': 'WebRTC not available, using Socket.IO streaming'
        },
        {
            'type': 'success',
            'category': 'system',
            'title': 'WebRTC Stopped',
            'message': 'WebRTC streaming stopped successfully'
        },
        {
            'type': 'error',
            'category': 'system',
            'title': 'WebRTC Failed',
            'message': 'WebRTC connection failed: ICE negotiation timeout'
        }
    ]
    
    for notification in webrtc_tests:
        send_notification(notification)
        time.sleep(2)

def run_all_tests():
    """Run all notification tests"""
    try:
        print(f"\n{'='*80}")
        print(f"🧪 NOTIFICATION POPUP TEST SCRIPT")
        print(f"{'='*80}")
        print(f"Controller URL: {CONTROLLER_URL}")
        print(f"Agent ID: {AGENT_ID}")
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*80}\n")
        
        print(f"📡 Connecting to controller...")
        sio.connect(CONTROLLER_URL, transports=['websocket', 'polling'])
        
        # Wait for connection to stabilize
        time.sleep(2)
        
        # Test categories
        print(f"\n{'='*80}")
        print(f"🎯 STARTING TEST SEQUENCE")
        print(f"{'='*80}")
        print(f"Total notifications to send: {len(TEST_NOTIFICATIONS) + 25}")
        print(f"Watch the dashboard for popup notifications!")
        print(f"{'='*80}")
        
        # Run basic tests first
        print(f"\n\n{'#'*80}")
        print(f"# PHASE 1: BASIC NOTIFICATION TYPES")
        print(f"{'#'*80}")
        
        for i, notification in enumerate(TEST_NOTIFICATIONS, 1):
            print(f"\n[{i}/{len(TEST_NOTIFICATIONS)}]", end='')
            send_notification(notification)
            time.sleep(3)  # Wait 3 seconds between notifications
        
        # Run specific feature tests
        print(f"\n\n{'#'*80}")
        print(f"# PHASE 2: FEATURE-SPECIFIC TESTS")
        print(f"{'#'*80}")
        
        test_streaming_notifications()
        time.sleep(2)
        
        test_file_operations()
        time.sleep(2)
        
        test_command_execution()
        time.sleep(2)
        
        test_security_notifications()
        time.sleep(2)
        
        test_connection_notifications()
        time.sleep(2)
        
        test_webrtc_notifications()
        
        # Final summary
        print(f"\n\n{'='*80}")
        print(f"✅ ALL NOTIFICATION TESTS COMPLETED!")
        print(f"{'='*80}")
        print(f"\n📊 Test Summary:")
        print(f"   - Basic notifications: {len(TEST_NOTIFICATIONS)}")
        print(f"   - Streaming tests: 5")
        print(f"   - File operation tests: 6")
        print(f"   - Command execution tests: 5")
        print(f"   - Security tests: 4")
        print(f"   - Connection tests: 3")
        print(f"   - WebRTC tests: 4")
        print(f"   - Total: {len(TEST_NOTIFICATIONS) + 27} notifications sent")
        print(f"\n💡 Check the agent-controller dashboard to verify all popups appeared!")
        print(f"{'='*80}\n")
        
        # Keep connection alive for a bit
        print(f"⏳ Keeping connection alive for 10 seconds...")
        time.sleep(10)
        
        print(f"👋 Disconnecting...")
        sio.disconnect()
        
        print(f"\n{'='*80}")
        print(f"🎉 TEST SCRIPT COMPLETED SUCCESSFULLY!")
        print(f"{'='*80}\n")
        
    except KeyboardInterrupt:
        print(f"\n\n⚠️  Test interrupted by user")
        sio.disconnect()
    except Exception as e:
        print(f"\n\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        sio.disconnect()

if __name__ == "__main__":
    # Check for custom controller URL
    if len(sys.argv) > 1:
        CONTROLLER_URL = sys.argv[1]
        print(f"Using custom controller URL: {CONTROLLER_URL}")
    
    run_all_tests()
