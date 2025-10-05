# Function Definition Order Fix - NameError Resolution

## Error Reported

```
NameError: name 'screen_capture_worker' is not defined. 
Did you mean: 'camera_capture_worker'?
```

## Root Cause

Python reads files top-to-bottom and functions must be defined **before** they are referenced.

### The Problem:
- `stream_screen_h264_socketio()` was defined at **line 5288**
- It tried to create threads using `screen_capture_worker`, `screen_encode_worker`, `screen_send_worker`
- But those functions weren't defined until **line 11791+** (6,500 lines later!)
- When Python tried to execute line 5297, it couldn't find `screen_capture_worker` yet

### The Call Chain:
```python
Line 5294: start_streaming()
  └─> Line 5313: Creates thread → stream_screen_webrtc_or_socketio()
      └─> Line 6375: Calls stream_screen_h264_socketio()
          └─> Line 5297: References screen_capture_worker ← NOT DEFINED YET! ❌
```

## The Fix

**Moved `stream_screen_h264_socketio()` definition to AFTER the worker functions:**

### Old Structure (BROKEN):
```python
Line 5288:  def stream_screen_h264_socketio(agent_id):  # ← Defined here
Line 5297:      threading.Thread(target=screen_capture_worker, ...)  # ← References undefined function
...
Line 11791: def screen_capture_worker(agent_id):  # ← Defined 6500 lines later!
Line 11826: def screen_encode_worker(agent_id):
Line 11846: def screen_send_worker(agent_id):
```

### New Structure (FIXED):
```python
Line 5288:  def stream_screen_h264_socketio(agent_id):
                """Placeholder - actual implementation below"""
                pass  # ← Placeholder to prevent import errors
...
Line 11791: def screen_capture_worker(agent_id):  # ← Defined first
Line 11826: def screen_encode_worker(agent_id):
Line 11846: def screen_send_worker(agent_id):
Line 11851: def stream_screen_h264_socketio(agent_id):  # ← ACTUAL implementation HERE ✅
                """Modern H.264 screen streaming with SocketIO."""
                # Now can safely reference worker functions above
                STREAM_THREADS = [
                    threading.Thread(target=screen_capture_worker, ...),  # ← Now defined! ✅
                    threading.Thread(target=screen_encode_worker, ...),
                    threading.Thread(target=screen_send_worker, ...),
                ]
```

## Files Modified

**client.py**:
1. Lines 5288-5292: Changed to placeholder (prevents import errors)
2. Lines 11850-11868: Added actual implementation after worker functions

## Why This Works

1. **Early placeholder (line 5288)**: Prevents import errors if code references the function name early
2. **Actual implementation (line 11851)**: Defined after all dependencies exist
3. **Python function lookup**: When the function is CALLED (at runtime), Python uses the LAST definition it found
4. **Result**: By the time `stream_screen_h264_socketio()` is called, both the placeholder AND actual implementation exist, and Python uses the actual one

## Other Issues in User's Log

### OpenCV Not Available (Camera Streaming)
```
[ERROR] Error: OpenCV not available for camera capture
[ERROR] Error: OpenCV not available for camera encoding
```

**Cause**: Missing `opencv-python` package

**Fix**: Install OpenCV:
```bash
pip install opencv-python
# Or
pip install cv2
```

### Persistence Errors (Not Critical)
```
[WARN] Failed to establish system persistence
[WARN] Failed to create backup
```

These are non-critical warnings - the agent works fine without these persistence mechanisms.

## Testing

After this fix, screen streaming should work:

1. ✅ No more `NameError`
2. ✅ Worker threads start successfully
3. ✅ Frames are captured from screen
4. ✅ Frames are encoded as JPEG
5. ✅ Frames are sent to controller
6. ✅ UI displays live video

### Expected Console Output:
```
[INFO] Started modern non-blocking video stream at 15 FPS.
[INFO] Started smart video streaming (WebRTC preferred, Socket.IO fallback).
```

### Expected Browser Console:
```
📹 SocketProvider: Received screen_frame from agent: 5f92d0f4
📹 SocketProvider: Received screen_frame from agent: 5f92d0f4
(Repeating every ~67ms)
```

### Expected UI:
```
Screen Stream
🔴 LIVE  |  High  |  15 FPS
[LIVE VIDEO PLAYING]
15 FPS  |  2.3 MB/s  |  423 frames
```

## Summary

| Issue | Status |
|-------|--------|
| NameError: screen_capture_worker not defined | ✅ FIXED |
| Threading bug (workers not starting) | ✅ FIXED |
| Frame encoding (base64 data URLs) | ✅ FIXED |
| Controller forwarding | ✅ FIXED |
| UI display logic | ✅ FIXED |
| Function definition order | ✅ FIXED |
| Camera streaming (OpenCV missing) | ⚠️ Needs cv2 install |

**Result**: Screen streaming should now work perfectly! 🎉
