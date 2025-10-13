# Install Required Dependencies for Streaming

Your logs show these critical errors:

```
[WARNING] numpy not available, some features may not work
[WARNING] opencv-python not available, video processing may not work
```

## Required Packages

For **screen and camera streaming** to work, you MUST install:

### 1. NumPy (Required for image processing)
```bash
pip install numpy
```

### 2. OpenCV (Required for screen capture and camera)
```bash
pip install opencv-python
```

### 3. MSS (Required for screen capture)
```bash
pip install mss
```

## Quick Install (All at Once)

```bash
pip install numpy opencv-python mss
```

## After Installing

1. **Restart your agent**:
```bash
python client.py
```

2. **Check the logs** - you should NO LONGER see:
   - ❌ `numpy not available`
   - ❌ `opencv-python not available`
   
3. **You SHOULD see**:
   - ✅ `Started modern non-blocking video stream at 15 FPS`
   - ✅ Console logs in browser: `📹 Received screen_frame...`

## Why This Matters

Without these packages:
- ❌ No screen capture
- ❌ No camera capture
- ❌ No image encoding
- ❌ No frames sent to UI
- ❌ Stuck on "Waiting for frames..."

With these packages:
- ✅ Screen streaming works
- ✅ Camera streaming works
- ✅ Live video in UI
- ✅ FPS and bandwidth monitoring

## Verification

After installing and restarting, check your console for:

```
[INFO] Started modern non-blocking video stream at 15 FPS.
[INFO] Started smart video streaming (WebRTC preferred, Socket.IO fallback).
```

And in your browser console (F12):
```javascript
📹 SocketProvider: Received screen_frame from agent: 5f92d0f4
```

If you see these, streaming is working! 🎉
