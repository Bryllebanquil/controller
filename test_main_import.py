#!/usr/bin/env python3
"""
Test script to verify main.py can be imported without AttributeError
"""

import sys
import os

def test_main_import():
    """Test if main.py can be imported without crashing."""
    try:
        print("Testing main.py import...")
        
        # Add current directory to Python path
        sys.path.insert(0, os.getcwd())
        
        # Try to import main module
        import main
        print("✅ main.py imported successfully!")
        
        # Check if the key variables are properly initialized
        if hasattr(main, 'SOCKETIO_AVAILABLE'):
            print(f"✅ SOCKETIO_AVAILABLE: {main.SOCKETIO_AVAILABLE}")
        else:
            print("❌ SOCKETIO_AVAILABLE not found")
            
        if hasattr(main, 'AIORTC_AVAILABLE'):
            print(f"✅ AIORTC_AVAILABLE: {main.AIORTC_AVAILABLE}")
        else:
            print("❌ AIORTC_AVAILABLE not found")
            
        if hasattr(main, 'sio'):
            print(f"✅ sio object: {type(main.sio)}")
        else:
            print("❌ sio object not found")
            
        # Check if the register_socketio_handlers function exists
        if hasattr(main, 'register_socketio_handlers'):
            print("✅ register_socketio_handlers function found")
        else:
            print("❌ register_socketio_handlers function not found")
            
        return True
        
    except Exception as e:
        print(f"❌ Error importing main.py: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function."""
    print("🔧 Main.py Import Test")
    print("=" * 40)
    
    success = test_main_import()
    
    print("\n" + "=" * 40)
    if success:
        print("🎉 Main.py import test passed!")
        print("The AttributeError should be resolved.")
    else:
        print("❌ Main.py import test failed.")
        print("Check the error details above.")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)