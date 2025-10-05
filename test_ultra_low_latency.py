#!/usr/bin/env python3
"""
Quick test to verify ultra_low_latency module is working
"""

import sys
import os

print("=" * 60)
print("Ultra-Low Latency Module Test")
print("=" * 60)

# Show current directory
print(f"Current directory: {os.getcwd()}")
print(f"Script location: {os.path.abspath(__file__)}")
print(f"Python path: {sys.path[:3]}")

# Try to import the module
try:
    print("\n1. Testing module import...")
    import ultra_low_latency
    print("   ✅ ultra_low_latency module imported successfully")
except ImportError as e:
    print(f"   ❌ Failed to import: {e}")
    sys.exit(1)

# Try to import the class
try:
    print("\n2. Testing class import...")
    from ultra_low_latency import PreInitializedStreamingSystem
    print("   ✅ PreInitializedStreamingSystem class imported successfully")
except ImportError as e:
    print(f"   ❌ Failed to import class: {e}")
    sys.exit(1)

# Try to create an instance (just for testing)
try:
    print("\n3. Testing class instantiation...")
    print("   (This will initialize the streaming system)")
    system = PreInitializedStreamingSystem()
    print("   ✅ PreInitializedStreamingSystem instance created")
    
    # Wait a moment for background initialization
    import time
    time.sleep(2)
    
    if system.is_ready:
        print("   ✅ System is ready!")
    else:
        print("   ⚠️  System is still initializing (this is normal)")
    
except Exception as e:
    print(f"   ❌ Failed to create instance: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("✅ All tests passed! Ultra-low latency module is working!")
print("=" * 60)
print("\nYou can now run client.py and it will use the ultra-low latency system.")
