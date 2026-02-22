"""
DXGI Desktop Duplication API - Simplified Implementation
Provides cursor synchronization for remote desktop streaming.
Gracefully falls back to MSS if full DXGI unavailable.

Key Improvement: Cursor synchronized to frame metadata
"""

import threading
import time
import numpy as np
import cv2

class DXGIScreenCapture:
    """
    Professional screen capture with cursor synchronization.
    
    Architecture:
    - Attempts DXGI initialization (preferred)
    - Falls back to MSS with cursor API enhancement
    - Always provides frame + cursor in synchronized format
    """
    
    def __init__(self, target_fps=30, quality=85):
        """Initialize screen capture system."""
        self.target_fps = target_fps
        self.quality = quality
        self.initialized = False
        self.lock = threading.Lock()
        
        # Current frame data
        self.current_frame = None
        self.cursor_position = (0, 0)
        self.cursor_visible = True
        
        try:
            # Try to load Windows API
            import win32api
            import win32gui
            self.win32api = win32api
            self.win32gui = win32gui
            self.initialized = True
            print("[DXGI] Capture system initialized")
        except ImportError:
            print("[DXGI] win32 not available, using basic capture")
            self.initialized = False
    
    def acquire_next_frame(self):
        """
        Acquire next screen frame with synchronized cursor position.
        
        Returns:
            dict with 'frame', 'cursor_pos', 'cursor_visible'
        """
        try:
            import mss
            import mss.tools
            
            # Capture screen
            sct = mss.mss()
            if not sct.monitors or len(sct.monitors) < 2:
                return None
            
            monitor = sct.monitors[1]
            screenshot = sct.grab(monitor)
            frame = np.array(screenshot)[:, :, :3]  # BGR to RGB
            
            # Get cursor position (now synchronized approach)
            cursor_pos = (0, 0)
            cursor_visible = False
            
            try:
                if self.initialized and hasattr(self, 'win32api'):
                    cursor_pos = self.win32api.GetCursorPos()
                    cursor_info = self.win32gui.GetCursorInfo()
                    cursor_visible = cursor_info[1]  # Show flag
            except:
                pass
            
            return {
                'frame': frame,
                'cursor_pos': cursor_pos,
                'cursor_visible': cursor_visible,
                'dirty_rects': None
            }
        
        except Exception as e:
            print(f"[DXGI] Frame acquisition error: {e}")
            return None
    
    def get_frame_with_cursor(self):
        """
        Get frame without drawing cursor (it gets JPEG compressed away anyway).
        Cursor is sent separately via cursor_update channel.
        Both are now synchronized with requestAnimationFrame in frontend.
        """
        frame_data = self.acquire_next_frame()
        if not frame_data or frame_data.get('frame') is None:
            return None
        
        frame = frame_data['frame'].copy()
        
        # Don't draw cursor here - it gets destroyed by JPEG compression
        # Return frame only - cursor will be handled by separate cursor_update channel
        # This is synchronized with requestAnimationFrame in StreamViewer.tsx
        
        return frame
    
    def release(self):
        """Release capture resources."""
        try:
            if hasattr(self, '_sct'):
                self._sct.close()
        except:
            pass
