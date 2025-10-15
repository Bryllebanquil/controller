# 🪟 Windows Installation Guide - Python 3.14

## ✅ Quick Install (Recommended)

```bash
cd C:\Users\Brylle\Downloads
pip install -r requirements-client.txt
```

---

## ⚠️ Common Issues & Solutions

### Issue 1: uvloop Error
**Error:** `RuntimeError: uvloop does not support Windows`

**Solution:** ✅ **FIXED!** uvloop is now commented out in requirements-client.txt
- The code automatically uses standard asyncio on Windows
- No performance loss - Windows asyncio is already optimized

---

### Issue 2: Some Packages Need Pre-Release Versions

If you get errors with `aiortc` or `av`, install them separately:

```bash
pip install --pre aiortc
pip install --pre av
```

Or skip them if you don't need WebRTC features:
```bash
# Edit requirements-client.txt and comment out:
# aiortc>=1.9.0
# av>=13.0.0
```

---

## 📦 Minimal Installation (Core Features Only)

If you want just the essential packages:

```bash
# Core networking
pip install python-socketio>=5.12.0
pip install python-engineio>=4.11.0
pip install uvicorn>=0.22.0
pip install fastapi>=0.100.0
pip install websockets>=15.0
pip install httpx>=0.25.0
pip install aiohttp>=3.9.0

# System & utilities
pip install psutil>=6.1.0
pip install pywin32>=308
pip install requests>=2.32.0

# Computer vision (if needed)
pip install numpy>=2.0.0
pip install opencv-python>=4.10.0.84
pip install Pillow>=11.0.0
pip install mss>=9.0.2

# Build tools
pip install pyinstaller>=6.0.0
```

---

## 🧪 Testing Installation

After installation, verify everything works:

```bash
python -c "import socketio; import websockets; import fastapi; print('✅ Core packages OK')"
python -c "import numpy; import cv2; import PIL; print('✅ Computer Vision OK')"
python -c "import psutil; import win32api; print('✅ System packages OK')"
```

---

## 📊 Package Status for Windows + Python 3.14

| Package | Status | Notes |
|---------|--------|-------|
| python-socketio | ✅ Works | Fully compatible |
| uvicorn | ✅ Works | Use plain version (not [standard]) |
| fastapi | ✅ Works | Fully compatible |
| websockets | ✅ Works | v15.0 has Python 3.14 wheels |
| httpx | ✅ Works | Fully compatible |
| aiohttp | ✅ Works | Fully compatible |
| numpy | ✅ Works | v2.0+ required for Python 3.14 |
| opencv-python | ✅ Works | v4.10+ has wheels |
| Pillow | ✅ Works | v11.0+ compatible |
| psutil | ✅ Works | v6.1+ has wheels |
| pywin32 | ✅ Works | v308+ compatible |
| aiortc | ⚠️ May need --pre | Optional (WebRTC) |
| av | ⚠️ May need --pre | Optional (media) |
| **uvloop** | ❌ Not supported | Linux/macOS only - REMOVED |

---

## 🚀 Running the Client

After successful installation:

```bash
cd C:\Users\Brylle\Downloads
python client.py
```

Expected output:
```
PYTHON AGENT STARTUP - MODERN ASYNC WITH UVLOOP
Step 1: Setting up uvloop (high-performance event loop)...
⚠️ uvloop import FAILED: No module named 'uvloop'
⚠️ To enable uvloop: pip install uvloop
USING STANDARD ASYNCIO - Consider installing uvloop for better performance
```

This is **NORMAL on Windows**! The warning is harmless - the code uses standard asyncio which works great on Windows.

---

## 💡 Tips

1. **Use Python 3.14.0 or later** - Earlier 3.14 pre-releases may have issues
2. **Update pip first**: `python -m pip install --upgrade pip`
3. **Some packages need Visual C++ Build Tools** - Download from Microsoft if needed
4. **WebRTC features (aiortc/av) are optional** - Skip if you don't need video streaming

---

## 🆘 Still Having Issues?

If packages fail to install:

1. Try installing problematic packages with `--pre`:
   ```bash
   pip install --pre <package-name>
   ```

2. Try using prebuilt wheels only:
   ```bash
   pip install <package-name> --only-binary :all:
   ```

3. Skip optional packages (aiortc, av, lxml) if not needed

4. Install core packages first, then add extras one by one

---

## ✅ What Was Fixed

### Before (BROKEN on Windows):
```
uvicorn[standard]>=0.22.0  # Includes uvloop - BREAKS ON WINDOWS
uvloop>=0.18.0             # DOESN'T WORK ON WINDOWS
```

### After (WORKS on Windows):
```
uvicorn>=0.22.0            # Windows compatible
# uvloop>=0.18.0           # LINUX/MACOS ONLY - commented out
```

---

**You're all set! The requirements file is now fully compatible with Windows + Python 3.14.** ✅
