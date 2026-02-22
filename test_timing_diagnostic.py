#!/usr/bin/env python3
"""
Detailed timing diagnostic - show EXACT time between screen captures
This reveals if screen capture is actually respecting the 100ms minimum sleep.
"""

import time
import threading
from datetime import datetime

def diagnose_capture_timing():
    """Monitor actual capture timing to see if 100ms sleep is working."""
    
    print("=" * 80)
    print("SCREEN CAPTURE TIMING DIAGNOSTIC")
    print("=" * 80)
    print()
    print("This will show EXACT timing between screen captures.")
    print("Target: Minimum 100ms between captures (8 FPS max)")
    print()
    
    try:
        from dxgi_implementation import DXGIScreenCapture
        print("Testing DXGI capture with your current settings...")
        print()
        
        cap = DXGIScreenCapture()
        if not cap.initialized:
            print("DXGI not available")
            return
        
        print("Frame #   | Time (ms) | Status")
        print("-" * 40)
        
        last_capture_time = time.time()
        frame_count = 0
        times_list = []
        
        for i in range(20):  # Capture 20 frames
            start = time.time()
            
            frame = cap.get_frame_with_cursor()
            
            elapsed_ms = (time.time() - start) * 1000
            time_since_last = (time.time() - last_capture_time) * 1000
            
            times_list.append(time_since_last)
            
            if frame is not None:
                frame_count += 1
                status = "✓ OK" if time_since_last >= 100 else f"✗ FAST ({time_since_last:.0f}ms)"
                print(f"{i:3d}      | {time_since_last:7.1f}  | {status}")
            
            last_capture_time = time.time()
            
            # Sleep simulation (what your code does)
            frame_time = 1.0 / 8  # TARGET_FPS = 8
            sleep_time = max(0.1, frame_time - elapsed_ms/1000)  # 100ms minimum
            if sleep_time > 0:
                time.sleep(sleep_time)
        
        print()
        print("=" * 40)
        print("STATISTICS:")
        print(f"Average time between captures: {sum(times_list)/len(times_list):.1f}ms")
        print(f"Min time: {min(times_list):.1f}ms")
        print(f"Max time: {max(times_list):.1f}ms")
        
        if min(times_list) < 100:
            print()
            print("⚠️  WARNING: Some captures happening too fast (<100ms)!")
            print("This WILL cause cursor flicker.")
        else:
            print()
            print("✓ All captures properly spaced (≥100ms)")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    diagnose_capture_timing()
