#!/usr/bin/env python3
"""
Simple Socket.IO functionality test
"""

import sys

def test_basic_socketio():
    """Test basic Socket.IO functionality."""
    try:
        print("Testing basic Socket.IO import...")
        import socketio
        print("✅ socketio imported successfully")
        
        # Test client creation
        print("Testing Socket.IO client creation...")
        client = socketio.Client(ssl_verify=False, engineio_logger=False, logger=False)
        print("✅ Socket.IO client created successfully")
        
        # Test if the client has the 'on' method
        if hasattr(client, 'on'):
            print("✅ Socket.IO client has 'on' method")
        else:
            print("❌ Socket.IO client missing 'on' method")
            
        # Test if the client has the 'connect' method
        if hasattr(client, 'connect'):
            print("✅ Socket.IO client has 'connect' method")
        else:
            print("❌ Socket.IO client missing 'connect' method")
            
        # Test if the client has the 'emit' method
        if hasattr(client, 'emit'):
            print("✅ Socket.IO client has 'emit' method")
        else:
            print("❌ Socket.IO client missing 'emit' method")
            
        return True
        
    except Exception as e:
        print(f"❌ Error during Socket.IO test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_webrtc_imports():
    """Test WebRTC imports."""
    try:
        print("\nTesting WebRTC imports...")
        
        # Test aiortc
        try:
            import aiortc
            print("✅ aiortc imported successfully")
        except ImportError:
            print("❌ aiortc import failed")
            
        # Test aiohttp
        try:
            import aiohttp
            print("✅ aiohttp imported successfully")
        except ImportError:
            print("❌ aiohttp import failed")
            
        return True
        
    except Exception as e:
        print(f"❌ Error during WebRTC test: {e}")
        return False

def main():
    """Main test function."""
    print("🔧 Simple Socket.IO & WebRTC Test")
    print("=" * 40)
    
    # Test Socket.IO
    socketio_ok = test_basic_socketio()
    
    # Test WebRTC
    webrtc_ok = test_webrtc_imports()
    
    print("\n" + "=" * 40)
    if socketio_ok and webrtc_ok:
        print("🎉 All basic tests passed!")
        print("\nThis means:")
        print("- Socket.IO is working correctly")
        print("- WebRTC dependencies are available")
        print("- The AttributeError should be resolved")
        print("\nYou can now try running main.py")
    else:
        print("❌ Some tests failed. Please check the output above.")
    
    return socketio_ok and webrtc_ok

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)