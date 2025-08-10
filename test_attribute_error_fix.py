#!/usr/bin/env python3
"""
Test script to verify that the AttributeError is resolved
"""

import sys
import os

def test_socketio_availability():
    """Test if Socket.IO is available and working."""
    try:
        print("Testing Socket.IO availability...")
        
        # Test basic import
        import socketio
        print("✅ socketio imported successfully")
        
        # Test client creation (same as in main.py)
        client = socketio.Client(
            ssl_verify=False,
            engineio_logger=False,
            logger=False
        )
        print("✅ Socket.IO client created successfully")
        
        # Test if the client has the required methods
        required_methods = ['on', 'connect', 'emit', 'disconnect', 'wait']
        for method in required_methods:
            if hasattr(client, method):
                print(f"✅ Socket.IO client has '{method}' method")
            else:
                print(f"❌ Socket.IO client missing '{method}' method")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error during Socket.IO test: {e}")
        return False

def test_webrtc_availability():
    """Test if WebRTC is available and working."""
    try:
        print("\nTesting WebRTC availability...")
        
        # Test aiortc import
        import aiortc
        from aiortc import RTCPeerConnection, MediaStreamTrack, RTCSessionDescription
        print("✅ aiortc imported successfully")
        
        # Test aiohttp import
        import aiohttp
        print("✅ aiohttp imported successfully")
        
        # Test av import
        import av
        print("✅ av imported successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during WebRTC test: {e}")
        return False

def test_main_py_content():
    """Test if the main.py content has the expected fixes."""
    try:
        print("\nTesting main.py content fixes...")
        
        # Read main.py and check for key fixes
        with open('main.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if @sio.on decorators are removed
        if '@sio.on(' in content:
            print("❌ Found @sio.on decorators - fix not complete")
            return False
        else:
            print("✅ No @sio.on decorators found")
        
        # Check if register_socketio_handlers function exists
        if 'def register_socketio_handlers():' in content:
            print("✅ register_socketio_handlers function found")
        else:
            print("❌ register_socketio_handlers function not found")
            return False
        
        # Check if early return checks are in place
        if 'if not SOCKETIO_AVAILABLE or sio is None:' in content:
            print("✅ Early return checks found")
        else:
            print("❌ Early return checks not found")
            return False
        
        # Check if the function call is added in agent_main
        if 'register_socketio_handlers()' in content:
            print("✅ register_socketio_handlers() call found")
        else:
            print("❌ register_socketio_handlers() call not found")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error during content test: {e}")
        return False

def main():
    """Main test function."""
    print("🔧 AttributeError Fix Verification Test")
    print("=" * 50)
    
    # Test Socket.IO availability
    socketio_ok = test_socketio_availability()
    
    # Test WebRTC availability
    webrtc_ok = test_webrtc_availability()
    
    # Test main.py content fixes
    content_ok = test_main_py_content()
    
    print("\n" + "=" * 50)
    if socketio_ok and webrtc_ok and content_ok:
        print("🎉 All tests passed! The AttributeError should be resolved.")
        print("\nSummary of fixes applied:")
        print("- ✅ Removed all @sio.on decorators")
        print("- ✅ Added register_socketio_handlers() function")
        print("- ✅ Added early return checks in handler functions")
        print("- ✅ Added call to register_socketio_handlers() in agent_main")
        print("- ✅ Socket.IO and WebRTC dependencies are working")
        print("\nYou should now be able to run main.py without the AttributeError!")
    else:
        print("❌ Some tests failed. Please check the output above.")
    
    return socketio_ok and webrtc_ok and content_ok

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)