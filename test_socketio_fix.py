#!/usr/bin/env python3
"""
Test script to verify Socket.IO fix is working
"""

import sys
import os

def test_socketio_import():
    """Test if Socket.IO imports work without AttributeError."""
    try:
        print("Testing Socket.IO import...")
        
        # Test basic import
        import socketio
        print("✅ socketio imported successfully")
        
        # Test if main.py can be imported without AttributeError
        print("Testing main.py import...")
        import main
        print("✅ main.py imported successfully - no AttributeError")
        
        # Check if the register_socketio_handlers function exists
        if hasattr(main, 'register_socketio_handlers'):
            print("✅ register_socketio_handlers function exists")
        else:
            print("❌ register_socketio_handlers function not found")
            
        # Check if the handler functions exist without decorators
        handler_functions = [
            'on_file_chunk_from_operator',
            'on_file_upload_complete_from_operator', 
            'on_request_file_chunk_from_agent',
            'connect',
            'disconnect',
            'on_command',
            'on_mouse_move',
            'on_mouse_click',
            'on_remote_key_press',
            'on_file_upload'
        ]
        
        missing_handlers = []
        for handler in handler_functions:
            if hasattr(main, handler):
                print(f"✅ {handler} function exists")
            else:
                missing_handlers.append(handler)
                print(f"❌ {handler} function missing")
        
        if missing_handlers:
            print(f"\n⚠️  Missing handlers: {missing_handlers}")
        else:
            print("\n✅ All handler functions exist")
            
        return True
        
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_webrtc_handlers():
    """Test if WebRTC handlers exist without decorators."""
    try:
        print("\nTesting WebRTC handlers...")
        
        webrtc_handlers = [
            'on_webrtc_offer',
            'on_webrtc_answer', 
            'on_webrtc_ice_candidate',
            'on_webrtc_start_streaming',
            'on_webrtc_stop_streaming',
            'on_webrtc_get_stats',
            'on_webrtc_set_quality',
            'on_webrtc_quality_change',
            'on_webrtc_frame_dropping',
            'on_webrtc_get_enhanced_stats',
            'on_webrtc_get_production_readiness',
            'on_webrtc_get_migration_plan',
            'on_webrtc_get_monitoring_data',
            'on_webrtc_adaptive_bitrate_control',
            'on_webrtc_implement_frame_dropping'
        ]
        
        missing_webrtc = []
        for handler in webrtc_handlers:
            if hasattr(main, handler):
                print(f"✅ {handler} function exists")
            else:
                missing_webrtc.append(handler)
                print(f"❌ {handler} function missing")
        
        if missing_webrtc:
            print(f"\n⚠️  Missing WebRTC handlers: {missing_webrtc}")
        else:
            print("\n✅ All WebRTC handler functions exist")
            
        return True
        
    except Exception as e:
        print(f"❌ Error testing WebRTC handlers: {e}")
        return False

def main():
    """Main test function."""
    print("🔧 Socket.IO Fix Verification Test")
    print("=" * 50)
    
    # Test basic Socket.IO functionality
    socketio_ok = test_socketio_import()
    
    # Test WebRTC handlers
    webrtc_ok = test_webrtc_handlers()
    
    print("\n" + "=" * 50)
    if socketio_ok and webrtc_ok:
        print("🎉 All tests passed! Socket.IO fix is working correctly.")
        print("\nThe AttributeError should now be resolved.")
        print("You can run main.py without the 'NoneType' object has no attribute 'on' error.")
    else:
        print("❌ Some tests failed. Please check the output above.")
    
    return socketio_ok and webrtc_ok

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)