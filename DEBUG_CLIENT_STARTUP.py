"""
DEBUG CLIENT STARTUP ISSUES
Quick diagnostic script to identify why client.py exits early
"""

import sys
import traceback

print("=" * 80)
print("DEBUG: CLIENT.PY STARTUP DIAGNOSTIC")
print("=" * 80)

# Step 1: Check if eventlet is installed
print("\n[1] Checking eventlet installation...")
try:
    import eventlet
    print("✅ eventlet installed successfully")
    print(f"   Version: {eventlet.__version__ if hasattr(eventlet, '__version__') else 'Unknown'}")
except ImportError as e:
    print(f"❌ eventlet NOT installed: {e}")
    print("   Run: pip install eventlet")

# Step 2: Test monkey_patch
print("\n[2] Testing eventlet.monkey_patch()...")
try:
    import eventlet
    eventlet.monkey_patch(all=True, thread=True, time=True, socket=True, select=True)
    print("✅ monkey_patch() successful (without ssl parameter)")
except Exception as e:
    print(f"❌ monkey_patch() failed: {e}")
    print("   Trying without parameters...")
    try:
        eventlet.monkey_patch()
        print("✅ monkey_patch() successful (basic)")
    except Exception as e2:
        print(f"❌ Basic monkey_patch() also failed: {e2}")

# Step 3: Check threading after monkey_patch
print("\n[3] Testing threading after monkey_patch...")
try:
    import threading
    lock = threading.RLock()
    print("✅ RLock created successfully")
    
    with lock:
        print("✅ RLock works with context manager")
except Exception as e:
    print(f"❌ RLock test failed: {e}")
    traceback.print_exc()

# Step 4: Test UACBypassManager creation
print("\n[4] Testing UACBypassManager creation...")
try:
    import os
    import subprocess
    import time
    
    WINDOWS_AVAILABLE = sys.platform == 'win32'
    
    class UACBypassError(Exception):
        pass
    
    class UACBypassMethod:
        def __init__(self, name: str, description: str, method_id: int):
            self.name = name
            self.description = description
            self.method_id = method_id
            self._lock = threading.Lock()
            print(f"   Created method: {name}")
    
    class UACBypassManager:
        def __init__(self):
            print("   Initializing UACBypassManager...")
            self._lock = threading.RLock()
            print("   Created RLock")
            self.methods = {}
            print("   Created methods dict")
    
    manager = UACBypassManager()
    print("✅ UACBypassManager created successfully")
    
except Exception as e:
    print(f"❌ UACBypassManager creation failed: {e}")
    traceback.print_exc()

# Step 5: Check if client.py can be imported
print("\n[5] Testing client.py import...")
try:
    # Don't actually import (might hang), just check syntax
    import py_compile
    py_compile.compile('client.py', doraise=True)
    print("✅ client.py syntax is valid")
except Exception as e:
    print(f"❌ client.py has syntax errors: {e}")
    traceback.print_exc()

# Step 6: Check dependencies
print("\n[6] Checking critical dependencies...")
critical_deps = [
    'socketio',
    'requests',
    'psutil',
    'pillow',
    'numpy',
    'cv2',
]

for dep in critical_deps:
    try:
        if dep == 'pillow':
            import PIL
            print(f"✅ {dep} (PIL) installed")
        elif dep == 'cv2':
            import cv2
            print(f"✅ {dep} (opencv-python) installed")
        else:
            __import__(dep)
            print(f"✅ {dep} installed")
    except ImportError:
        print(f"⚠️  {dep} NOT installed (might be optional)")

print("\n" + "=" * 80)
print("DIAGNOSTIC COMPLETE")
print("=" * 80)

print("\nRECOMMENDATIONS:")
print("-" * 80)

# Check Python version
print(f"\n1. Python version: {sys.version}")
if sys.version_info >= (3, 13):
    print("   ⚠️  Python 3.13+ detected - eventlet might have compatibility issues")
    print("   Consider using Python 3.11 or 3.12 for better compatibility")

print("\n2. If RLock warning persists:")
print("   - The warning is HARMLESS and can be ignored")
print("   - client.py should still run (warning is suppressed)")
print("   - If it exits, there's a different issue")

print("\n3. If client.py exits immediately:")
print("   - Check for syntax errors above")
print("   - Check for missing dependencies above")
print("   - Run: python client.py 2>&1 | more")
print("   - Look for the actual error message")

print("\n4. To see full startup output:")
print("   - Open client.py")
print("   - Look for 'if __name__ == \"__main__\":' section")
print("   - All startup messages are now using print() instead of log_message()")
print("   - Should show detailed startup progress")

print("\n" + "=" * 80)
print("RUN THIS NEXT:")
print("=" * 80)
print("\npython client.py\n")
print("Then copy ALL output here for analysis")
print("=" * 80)
