#!/usr/bin/env python3
"""
Test different screen capture methods to see which one causes cursor flicker.
This will help identify if it's DXGI, MSS, or something else.
"""

import time
import sys

def test_dxgi_only():
    """Test with DXGI capture only."""
    print("\n" + "=" * 80)
    print("TEST 1: DXGI SCREEN CAPTURE ONLY (No encoding)")
    print("=" * 80)
    
    try:
        from dxgi_implementation import DXGIScreenCapture
        print("Initializing DXGI capture...")
        cap = DXGIScreenCapture()
        
        if not cap.initialized:
            print("DXGI not available.")
            return False
        
        print("DXGI initialized. Capturing frames for 10 seconds...")
        print("Observe cursor - does it flicker?")
        print()
        
        start = time.time()
        frame_count = 0
        while time.time() - start < 10:
            try:
                frame = cap.get_frame_with_cursor()
                if frame is not None:
                    frame_count += 1
                    if frame_count % 5 == 0:
                        print(f"Captured {frame_count} frames...")
                time.sleep(0.001)  # Minimal sleep
            except Exception as e:
                print(f"Error: {e}")
                break
        
        print(f"\nTest complete. Captured {frame_count} frames.")
        return True
        
    except Exception as e:
        print(f"Test error: {e}")
        return False

def test_mss_only():
    """Test with MSS capture only."""
    print("\n" + "=" * 80)
    print("TEST 2: MSS SCREEN CAPTURE ONLY (No encoding)")
    print("=" * 80)
    
    try:
        import mss
        print("Initializing MSS capture...")
        
        with mss.mss() as sct:
            print("MSS initialized. Capturing frames for 10 seconds...")
            print("Observe cursor - does it flicker?")
            print()
            
            start = time.time()
            frame_count = 0
            while time.time() - start < 10:
                try:
                    frame = sct.grab(sct.monitors[1])  # Primary monitor
                    frame_count += 1
                    if frame_count % 5 == 0:
                        print(f"Captured {frame_count} frames...")
                    time.sleep(0.001)  # Minimal sleep
                except Exception as e:
                    print(f"Error: {e}")
                    break
            
            print(f"\nTest complete. Captured {frame_count} frames.")
        return True
        
    except Exception as e:
        print(f"Test error: {e}")
        return False

def test_with_sleep():
    """Test with 50ms sleep between captures."""
    print("\n" + "=" * 80)
    print("TEST 3: DXGI + 50MS SLEEP (Extreme spacing)")
    print("=" * 80)
    
    try:
        from dxgi_implementation import DXGIScreenCapture
        print("Initializing DXGI capture...")
        cap = DXGIScreenCapture()
        
        if not cap.initialized:
            print("DXGI not available.")
            return False
        
        print("DXGI initialized. Capturing frames with 50ms delays...")
        print("Observe cursor - is it smoother now?")
        print()
        
        start = time.time()
        frame_count = 0
        while time.time() - start < 10:
            try:
                frame = cap.get_frame_with_cursor()
                if frame is not None:
                    frame_count += 1
                    if frame_count % 2 == 0:
                        print(f"Captured {frame_count} frames...")
                time.sleep(0.05)  # 50ms sleep - MUCH longer
            except Exception as e:
                print(f"Error: {e}")
                break
        
        print(f"\nTest complete. Captured {frame_count} frames.")
        return True
        
    except Exception as e:
        print(f"Test error: {e}")
        return False

if __name__ == '__main__':
    print("PC1 CURSOR FLICKER - CAPTURE METHOD TESTS")
    print()
    print("This will test different screen capture methods.")
    print("For each test, move your mouse and observe if cursor flickers.")
    print()
    
    print("Starting tests in 3 seconds...")
    time.sleep(3)
    
    try:
        test_dxgi_only()
        time.sleep(2)
        
        test_mss_only()
        time.sleep(2)
        
        test_with_sleep()
        
        print("\n" + "=" * 80)
        print("ALL TESTS COMPLETE")
        print("=" * 80)
        print()
        print("Results Summary:")
        print("- Which test had the smoothest cursor?")
        print("- Did cursor flicker with 50ms sleep?")
        print("- This identifies the root cause.")
        
    except KeyboardInterrupt:
        print("\n\nTests interrupted.")
