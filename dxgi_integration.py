"""
Integration code for DXGI screen capture in client.py

This replaces the MSS-based screen_capture_worker with DXGI.
Copy the new screen_capture_worker() function into client.py
to replace the existing implementation.
"""

import time
import threading
import queue
import cv2
import numpy as np
from dxgi_implementation import DXGIScreenCapture
import ctypes

# Configuration - these should match client.py values
TARGET_FPS = 30
CAPTURE_QUEUE_SIZE = 10
STREAMING_ENABLED = False

# Global DXGI capture instance
_dxgi_capture = None
_dxgi_lock = threading.Lock()

def initialize_dxgi_capture():
    """Initialize DXGI capture system."""
    global _dxgi_capture
    try:
        _dxgi_capture = DXGIScreenCapture(target_fps=TARGET_FPS, quality=85)
        if _dxgi_capture.initialized:
            print("[DXGI] Screen capture system initialized")
            return True
        else:
            print("[DXGI] Failed to initialize, falling back to MSS")
            return False
    except Exception as e:
        print(f"[DXGI] Initialization error: {e}, falling back to MSS")
        return False

def screen_capture_worker_dxgi(agent_id):
    """
    DXGI-based screen capture worker (replaces MSS).
    
    KEY IMPROVEMENTS:
    - Cursor position from frame metadata (synchronized!)
    - No separate cursor call (eliminates race condition)
    - Dirty region tracking for bandwidth
    - Professional cursor rendering
    - Native DirectX performance
    
    This function replaces screen_capture_worker() in client.py
    """
    global STREAMING_ENABLED, capture_queue, _dxgi_capture
    
    if not _dxgi_capture or not _dxgi_capture.initialized:
        print("[DXGI] Capture not initialized, starting fallback")
        # Fall back to MSS if DXGI failed
        return screen_capture_worker_fallback(agent_id)
    
    print("[DXGI] Screen capture worker starting")
    frame_time = 1.0 / TARGET_FPS
    frame_count = 0
    last_stats_time = time.time()
    
    try:
        while STREAMING_ENABLED:
            try:
                start = time.time()
                
                # ACQUIRE FRAME WITH SYNCHRONIZED METADATA
                # This is the KEY advantage - cursor comes with frame!
                frame = _dxgi_capture.get_frame_with_cursor()
                
                if frame is None:
                    # Timeout, try again
                    time.sleep(0.001)
                    continue
                
                # Frame is now already composite with cursor!
                # The cursor is guaranteed to be in sync because:
                # 1. Position comes from DXGI_OUTDUPL_FRAME_INFO
                # 2. Info is captured AT frame capture time
                # 3. No separate call = no race condition
                
                # Resize if needed
                width, height = _dxgi_capture.frame_width, _dxgi_capture.frame_height
                if width > 1280:
                    scale = 1280 / width
                    width = int(width * scale)
                    height = int(height * scale)
                    frame = cv2.resize(frame, (width, height), interpolation=cv2.INTER_AREA)
                
                # Queue frame for encoding
                queue_size = capture_queue.qsize()
                if queue_size < CAPTURE_QUEUE_SIZE:
                    try:
                        capture_queue.put_nowait(frame)
                        frame_count += 1
                    except queue.Full:
                        pass
                else:
                    # Queue full, drop frame
                    pass
                
                # Maintain target FPS
                elapsed = time.time() - start
                sleep_time = max(0, frame_time - elapsed)
                if sleep_time > 0:
                    time.sleep(sleep_time)
                
                # Log stats
                now = time.time()
                if now - last_stats_time >= 5:
                    fps = frame_count / (now - last_stats_time)
                    print(f"[DXGI] Capture FPS: {fps:.1f}, Queue: {queue_size}")
                    frame_count = 0
                    last_stats_time = now
            
            except KeyboardInterrupt:
                print("[DXGI] Capture interrupted")
                break
            except Exception as e:
                print(f"[DXGI] Frame capture error: {e}")
                time.sleep(0.01)
    
    except KeyboardInterrupt:
        print("[DXGI] Capture worker interrupted")
    finally:
        print("[DXGI] Screen capture stopped")
        if _dxgi_capture:
            _dxgi_capture.release()

def screen_capture_worker_fallback(agent_id):
    """
    Fallback to MSS if DXGI fails.
    This is the old implementation.
    """
    global STREAMING_ENABLED, capture_queue, SELECTED_MONITOR_INDEX
    
    print("[Fallback] Using MSS screen capture")
    # ... (existing MSS-based implementation)
    # This would be your current screen_capture_worker code

# ============ INTEGRATION INSTRUCTIONS ============
"""
TO USE THIS IN client.py:

1. Import at top of client.py:
   from dxgi_implementation import DXGIScreenCapture

2. In your main initialization (around line where threads start):
   # Initialize DXGI (or fallback to MSS)
   dxgi_ready = initialize_dxgi_capture()
   if dxgi_ready:
       print("Using DXGI screen capture")
       capture_thread = threading.Thread(
           target=screen_capture_worker_dxgi,
           args=(agent_id,),
           daemon=True
       )
   else:
       print("Using MSS screen capture")
       capture_thread = threading.Thread(
           target=screen_capture_worker,  # Keep old name for fallback
           args=(agent_id,),
           daemon=True
       )

3. Replace screen_capture_worker definition with:
   def screen_capture_worker(agent_id):
       global STREAMING_ENABLED, capture_queue, _dxgi_capture
       
       # Try DXGI first
       if _dxgi_capture and _dxgi_capture.initialized:
           screen_capture_worker_dxgi(agent_id)
       else:
           # Fallback code (existing implementation)
           screen_capture_worker_fallback(agent_id)

BENEFITS:
✓ Cursor always synchronized to frame (from metadata)
✓ No separate cursor call = no race condition
✓ Bandwidth optimized (dirty region tracking)
✓ Professional-grade performance
✓ Native Windows integration
✓ Actual cursor shapes supported

COMPATIBILITY:
- Requires: Windows 8+, DirectX 11
- Fallback: Automatic to MSS if DXGI unavailable
"""

# ============ SIMPLE INTEGRATION VERSION ============

def get_screen_capture_functions():
    """
    Returns dict with capture functions.
    Use this to swap implementations dynamically.
    """
    return {
        'dxgi': screen_capture_worker_dxgi,
        'mss': screen_capture_worker_fallback,
    }

def screen_capture_worker_adaptive(agent_id):
    """
    Adaptive capture that tries DXGI, falls back to MSS.
    This is the safest approach.
    """
    global STREAMING_ENABLED, capture_queue, _dxgi_capture
    
    # Try DXGI first
    if _dxgi_capture and _dxgi_capture.initialized:
        try:
            screen_capture_worker_dxgi(agent_id)
        except Exception as e:
            print(f"[DXGI] Error, falling back: {e}")
            _dxgi_capture = None
            screen_capture_worker_fallback(agent_id)
    else:
        # Use MSS fallback
        screen_capture_worker_fallback(agent_id)
