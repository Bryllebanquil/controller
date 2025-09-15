#!/usr/bin/env python3
"""
Comprehensive Connection Debug Script
=====================================

This script tests the full connection flow between client, controller, and UI
to identify why agents aren't appearing in the controller UI.
"""

import os
import sys
import time
import json
import logging
import asyncio
import requests
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('connection_debug.log')
    ]
)
logger = logging.getLogger(__name__)

# Configuration
CONTROLLER_URL = os.environ.get('CONTROLLER_URL', 'https://agent-controller-backend.onrender.com')
AGENT_ID = f"debug-client-{int(time.time())}"

def test_http_endpoint():
    """Test basic HTTP connectivity to controller"""
    logger.info(f"Testing HTTP connection to {CONTROLLER_URL}")
    
    try:
        # Test root endpoint
        response = requests.get(f"{CONTROLLER_URL}/", timeout=10)
        logger.info(f"Root endpoint status: {response.status_code}")
        
        # Test API endpoints
        endpoints = ['/api/system/status', '/api/agents', '/dashboard']
        for endpoint in endpoints:
            try:
                resp = requests.get(f"{CONTROLLER_URL}{endpoint}", timeout=5)
                logger.info(f"Endpoint {endpoint}: {resp.status_code}")
            except Exception as e:
                logger.error(f"Endpoint {endpoint} failed: {e}")
                
        return True
    except Exception as e:
        logger.error(f"HTTP test failed: {e}")
        return False

def test_socketio_connection():
    """Test Socket.IO connection with detailed logging"""
    try:
        import socketio
        
        logger.info("Creating Socket.IO client...")
        sio = socketio.Client(
            ssl_verify=True,
            engineio_logger=True,  # Enable for debugging
            logger=True
        )
        
        events_received = []
        connection_successful = False
        registration_confirmed = False
        
        @sio.event
        def connect():
            nonlocal connection_successful
            connection_successful = True
            logger.info("✅ Socket.IO connection established!")
            events_received.append('connect')
            
            # Send agent registration with full debug data
            registration_data = {
                'agent_id': AGENT_ID,
                'name': f'DebugClient-{AGENT_ID.split("-")[-1]}',
                'platform': sys.platform,
                'python_version': sys.version.split()[0],
                'timestamp': time.time(),
                'capabilities': ['debug', 'testing', 'commands'],
                'cpu_usage': 5,
                'memory_usage': 10,
                'network_usage': 2,
                'system_info': {
                    'type': 'debug_client',
                    'version': '1.0',
                    'test_mode': True
                }
            }
            
            logger.info(f"Sending registration: {json.dumps(registration_data, indent=2)}")
            sio.emit('agent_register', registration_data)
        
        @sio.event
        def disconnect():
            logger.warning("❌ Socket.IO connection lost")
            events_received.append('disconnect')
        
        @sio.event
        def connect_error(data):
            logger.error(f"❌ Socket.IO connection error: {data}")
            events_received.append(f'connect_error: {data}')
        
        @sio.event
        def agent_registered(data):
            nonlocal registration_confirmed
            registration_confirmed = True
            logger.info(f"✅ Agent registration confirmed: {data}")
            events_received.append(f'agent_registered: {data}')
        
        @sio.event
        def registration_error(data):
            logger.error(f"❌ Registration error: {data}")
            events_received.append(f'registration_error: {data}')
        
        @sio.event
        def agent_list_update(data):
            logger.info(f"📋 Agent list update received: {len(data)} agents")
            for agent_id, agent_data in data.items():
                logger.info(f"  - Agent {agent_id}: {agent_data.get('name', 'Unknown')} ({agent_data.get('status', 'unknown')})")
            events_received.append(f'agent_list_update: {len(data)} agents')
        
        @sio.event
        def operator_connected(data):
            logger.info(f"📡 Operator connected event: {data}")
            events_received.append(f'operator_connected: {data}')
        
        @sio.event
        def activity_update(data):
            logger.info(f"📰 Activity update: {data.get('action', 'Unknown')} - {data.get('details', '')}")
            events_received.append(f'activity_update: {data.get("action")}')
        
        @sio.event
        def pong(data):
            logger.info(f"🏓 Pong received: {data}")
            events_received.append('pong')
        
        # Connect to controller
        logger.info(f"Connecting to {CONTROLLER_URL}...")
        sio.connect(CONTROLLER_URL, wait_timeout=30)
        
        # Wait for events and send test data
        logger.info("Waiting for events...")
        time.sleep(5)
        
        # Send ping
        if connection_successful:
            ping_data = {
                'agent_id': AGENT_ID,
                'timestamp': time.time(),
                'uptime': 5
            }
            logger.info(f"Sending ping: {ping_data}")
            sio.emit('ping', ping_data)
        
        # Wait for responses
        time.sleep(5)
        
        # Test operator connect simulation
        logger.info("Simulating operator connect...")
        sio.emit('operator_connect')
        sio.emit('request_agent_list')
        
        time.sleep(3)
        
        # Disconnect
        if sio.connected:
            sio.disconnect()
            logger.info("🔌 Disconnected from controller")
        
        # Summary
        logger.info("\n" + "="*60)
        logger.info("CONNECTION TEST SUMMARY")
        logger.info("="*60)
        logger.info(f"Connection successful: {connection_successful}")
        logger.info(f"Registration confirmed: {registration_confirmed}")
        logger.info(f"Events received: {len(events_received)}")
        for event in events_received:
            logger.info(f"  - {event}")
        logger.info("="*60)
        
        return connection_successful and registration_confirmed
        
    except ImportError:
        logger.error("❌ python-socketio library not available")
        logger.info("Install with: pip install python-socketio requests")
        return False
    except Exception as e:
        logger.error(f"❌ Socket.IO test failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def test_ui_connection():
    """Test if UI can connect to the backend"""
    logger.info("Testing UI connectivity...")
    
    # Check if UI build exists
    ui_build_path = "/workspace/agent-controller ui v2.1/build"
    if os.path.exists(ui_build_path):
        logger.info("✅ UI build directory exists")
        
        # Check if index.html exists
        index_path = os.path.join(ui_build_path, "index.html")
        if os.path.exists(index_path):
            logger.info("✅ UI index.html exists")
            
            # Read and check for socket configuration
            with open(index_path, 'r') as f:
                content = f.read()
                logger.info("UI HTML content preview:")
                logger.info(content[:500] + "...")
        else:
            logger.error("❌ UI index.html not found")
    else:
        logger.error("❌ UI build directory not found")

def check_cors_configuration():
    """Check CORS configuration"""
    logger.info("Checking CORS configuration...")
    
    try:
        # Test OPTIONS request
        response = requests.options(
            f"{CONTROLLER_URL}/socket.io/",
            headers={
                'Origin': 'http://localhost:3000',
                'Access-Control-Request-Method': 'GET',
                'Access-Control-Request-Headers': 'Content-Type'
            },
            timeout=10
        )
        
        logger.info(f"CORS preflight status: {response.status_code}")
        logger.info(f"CORS headers: {dict(response.headers)}")
        
    except Exception as e:
        logger.error(f"CORS test failed: {e}")

def main():
    """Main test function"""
    logger.info("🚀 Starting comprehensive connection debug")
    logger.info("=" * 60)
    logger.info(f"Target Controller: {CONTROLLER_URL}")
    logger.info(f"Debug Agent ID: {AGENT_ID}")
    logger.info("=" * 60)
    
    # Run all tests
    tests = [
        ("HTTP Connectivity", test_http_endpoint),
        ("CORS Configuration", check_cors_configuration),
        ("UI Build Check", test_ui_connection),
        ("Socket.IO Connection", test_socketio_connection),
    ]
    
    results = {}
    for test_name, test_func in tests:
        logger.info(f"\n🔍 Running test: {test_name}")
        logger.info("-" * 40)
        try:
            results[test_name] = test_func()
        except Exception as e:
            logger.error(f"Test {test_name} crashed: {e}")
            results[test_name] = False
    
    # Final summary
    logger.info("\n" + "="*60)
    logger.info("🎯 FINAL TEST RESULTS")
    logger.info("="*60)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{test_name}: {status}")
    
    all_passed = all(results.values())
    logger.info(f"\nOverall Status: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
    logger.info("="*60)
    
    if not all_passed:
        logger.error("\n🔧 TROUBLESHOOTING RECOMMENDATIONS:")
        logger.error("1. Check if controller is deployed and accessible")
        logger.error("2. Verify CORS configuration allows UI origin")
        logger.error("3. Ensure Socket.IO is properly configured")
        logger.error("4. Check network connectivity and firewall settings")
        logger.error("5. Verify agent registration event handlers")
    
    return all_passed

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("🛑 Debug interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)