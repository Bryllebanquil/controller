#!/usr/bin/env python3
"""
Test screen capture with streaming enabled but ONLY video, no audio/camera.
This isolates screen capture to identify if other streams are causing flicker.
"""

import os
import sys
import time

# Set minimal configuration
os.environ['STREAMING_ENABLED'] = '1'
os.environ['AUDIO_STREAMING_ENABLED'] = '0'
os.environ['CAMERA_STREAMING_ENABLED'] = '0'

print("=" * 80)
print("PC1 CURSOR FLICKER TEST - VIDEO ONLY (NO AUDIO/CAMERA)")
print("=" * 80)
print()
print("Starting client.py with ONLY screen capture streaming...")
print("No audio or camera streams will be active.")
print()
print("Move your mouse and observe cursor smoothness:")
print("- Smooth = screen capture only is working correctly")
print("- Flickering = something else is interfering")
print()
print("Running for 30 seconds...")
print()

try:
    # Import after environment setup
    import client
    
    # Start screen streaming ONLY
    print("Starting screen streaming...")
    
    try:
        # Try to start streaming
        client.STREAMING_ENABLED = True
        client.AUDIO_STREAMING_ENABLED = False
        client.CAMERA_STREAMING_ENABLED = False
        
        # Give it time to start
        time.sleep(2)
        
        print("Streaming started. Move mouse for 30 seconds...")
        start = time.time()
        frame_count = 0
        
        while time.time() - start < 30:
            try:
                # Monitor frame queue to see if capturing
                if hasattr(client, 'capture_queue') and client.capture_queue:
                    queue_size = client.capture_queue.qsize() if hasattr(client.capture_queue, 'qsize') else 0
                    if queue_size > 0:
                        frame_count += 1
                        if frame_count % 5 == 0:
                            print(f"Frames captured: {frame_count}, Queue size: {queue_size}")
                
                time.sleep(0.1)
            except Exception as e:
                print(f"Monitor error: {e}")
                time.sleep(0.1)
        
        print(f"\nTest complete. Total frames: {frame_count}")
        
        # Stop streaming
        print("Stopping streaming...")
        client.STREAMING_ENABLED = False
        time.sleep(1)
        
        print("\nDid cursor flicker during this test?")
        
    except Exception as e:
        print(f"Error during test: {e}")
        import traceback
        traceback.print_exc()

except KeyboardInterrupt:
    print("\n\nTest interrupted.")
    sys.exit(0)
