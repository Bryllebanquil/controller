#!/usr/bin/env python3
"""
Full Flow Test Script
====================

Tests the complete flow from client connection to UI visibility.
"""

import os
import sys
import time
import json
import threading
import requests
from datetime import datetime

# Configuration
CONTROLLER_URL = os.environ.get('CONTROLLER_URL', 'https://agent-controller-backend.onrender.com')
AGENT_ID = f"test-flow-{int(time.time())}"

def log_message(msg, level="INFO"):
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    print(f"[{timestamp}] {level}: {msg}")

def test_client_connection():
    """Test client connection and registration"""
    log_message("🔌 Testing client connection...")
    
    try:
        import socketio
        
        sio = socketio.Client(ssl_verify=True, logger=True, engineio_logger=True)
        connected = False
        registered = False
        
        @sio.event
        def connect():
            nonlocal connected
            connected = True
            log_message("✅ Client connected")
            
            # Register agent
            registration_data = {
                'agent_id': AGENT_ID,
                'name': f'TestFlow-{AGENT_ID.split("-")[-1]}',
                'platform': 'test-platform',
                'python_version': '3.9.0',
                'timestamp': time.time(),
                'capabilities': ['test', 'flow', 'validation'],
                'cpu_usage': 15,
                'memory_usage': 25,
                'network_usage': 5,
                'system_info': {'type': 'test_flow', 'version': '1.0'}
            }
            sio.emit('agent_register', registration_data)
            log_message(f"📝 Sent registration: {registration_data['agent_id']}")
        
        @sio.event
        def agent_registered(data):
            nonlocal registered
            registered = True
            log_message(f"✅ Registration confirmed: {data}")
        
        @sio.event
        def agent_list_update(data):
            log_message(f"📋 Agent list update: {len(data)} agents")
            if AGENT_ID in data:
                log_message(f"✅ Our agent found in list: {data[AGENT_ID]}")
            else:
                log_message(f"❌ Our agent NOT in list")
        
        # Connect
        sio.connect(CONTROLLER_URL, wait_timeout=30)
        
        # Wait for registration
        timeout = 10
        while timeout > 0 and not registered:
            time.sleep(1)
            timeout -= 1
        
        if registered:
            log_message("✅ Client connection and registration successful")
            # Keep alive for testing
            time.sleep(5)
        else:
            log_message("❌ Client registration failed")
        
        sio.disconnect()
        return registered
        
    except Exception as e:
        log_message(f"❌ Client connection failed: {e}")
        return False

def test_ui_connection():
    """Test UI connection simulation"""
    log_message("🖥️  Testing UI connection...")
    
    try:
        import socketio
        
        sio = socketio.Client(ssl_verify=True)
        connected = False
        agents_received = False
        
        @sio.event
        def connect():
            nonlocal connected
            connected = True
            log_message("✅ UI connected")
            sio.emit('operator_connect')
            time.sleep(1)
            sio.emit('request_agent_list')
        
        @sio.event
        def operator_connected(data):
            log_message(f"📡 Operator connected confirmed: {data}")
        
        @sio.event
        def agent_list_update(data):
            nonlocal agents_received
            agents_received = True
            log_message(f"📋 UI received agent list: {len(data)} agents")
            for agent_id, agent_data in data.items():
                name = agent_data.get('name', 'Unknown')
                status = agent_data.get('status', 'unknown')
                log_message(f"   - {agent_id}: {name} ({status})")
        
        # Connect
        sio.connect(CONTROLLER_URL, wait_timeout=30)
        
        # Wait for agent list
        timeout = 10
        while timeout > 0 and not agents_received:
            time.sleep(1)
            timeout -= 1
        
        sio.disconnect()
        
        if agents_received:
            log_message("✅ UI connection successful")
            return True
        else:
            log_message("❌ UI did not receive agent list")
            return False
            
    except Exception as e:
        log_message(f"❌ UI connection failed: {e}")
        return False

def test_http_endpoints():
    """Test HTTP endpoints"""
    log_message("🌐 Testing HTTP endpoints...")
    
    try:
        # Test root
        response = requests.get(f"{CONTROLLER_URL}/", timeout=10)
        log_message(f"Root endpoint: {response.status_code}")
        
        # Test API
        response = requests.get(f"{CONTROLLER_URL}/api/system/status", timeout=10)
        log_message(f"API status: {response.status_code}")
        
        return True
    except Exception as e:
        log_message(f"❌ HTTP test failed: {e}")
        return False

def main():
    """Main test orchestrator"""
    log_message("🚀 Starting full flow test")
    log_message("=" * 60)
    log_message(f"Controller URL: {CONTROLLER_URL}")
    log_message(f"Test Agent ID: {AGENT_ID}")
    log_message("=" * 60)
    
    # Test sequence
    tests = [
        ("HTTP Endpoints", test_http_endpoints),
        ("Client Connection", test_client_connection),
        ("UI Connection", test_ui_connection),
    ]
    
    results = {}
    for test_name, test_func in tests:
        log_message(f"\n🔍 Running: {test_name}")
        log_message("-" * 40)
        results[test_name] = test_func()
        time.sleep(2)  # Brief pause between tests
    
    # Summary
    log_message("\n" + "=" * 60)
    log_message("🎯 TEST RESULTS SUMMARY")
    log_message("=" * 60)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        log_message(f"{test_name}: {status}")
    
    all_passed = all(results.values())
    overall = "✅ ALL TESTS PASSED" if all_passed else "❌ SOME TESTS FAILED"
    log_message(f"\nOverall: {overall}")
    log_message("=" * 60)
    
    return all_passed

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        log_message("🛑 Test interrupted")
        sys.exit(1)
    except Exception as e:
        log_message(f"❌ Test crashed: {e}")
        sys.exit(1)