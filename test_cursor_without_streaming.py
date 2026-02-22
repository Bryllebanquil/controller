#!/usr/bin/env python3
"""
Test if cursor flickers WITHOUT any screen capture/streaming active.
If cursor is smooth here, the problem IS screen capture.
If cursor still flickers, it's something else (system, display driver, etc).
"""

import time
import sys

print("=" * 80)
print("PC1 CURSOR FLICKER TEST - NO STREAMING")
print("=" * 80)
print()
print("This test runs WITHOUT any screen capture or streaming.")
print("Move your mouse around and observe if the cursor flickers.")
print()
print("- If cursor is SMOOTH: The flicker is caused by screen capture")
print("- If cursor STILL FLICKERS: The problem is elsewhere (drivers, system, etc)")
print()
print("Running for 30 seconds... Move mouse around.")
print()

try:
    start_time = time.time()
    while time.time() - start_time < 30:
        # Do absolutely nothing - let OS handle cursor rendering
        time.sleep(0.01)
        sys.stdout.write('.')
        sys.stdout.flush()
    
    print("\n\nTest complete.")
    print("Did the cursor flicker during this 30-second test?")

except KeyboardInterrupt:
    print("\n\nTest interrupted.")
