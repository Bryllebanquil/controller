# 🚀 Client Installation Guide

## 📋 Overview

The client (`client.py`) requires various dependencies depending on the features you want to use. This guide provides different installation options based on your needs.

## 🎯 Installation Options

### **Option 1: Full Installation (Recommended)**
Install all dependencies for complete functionality:

```bash
pip install -r requirements-client.txt
```

### **Option 2: Minimal Installation**
Install only core dependencies for basic functionality:

```bash
pip install -r requirements-client-minimal.txt
```

### **Option 3: Manual Installation**
Install dependencies one by one as needed.

## 🖥️ Platform-Specific Instructions

### **Windows Installation**

#### **Prerequisites:**
```bash
# Install Visual C++ Build Tools (if not already installed)
# Download from: https://visualstudio.microsoft.com/visual-cpp-build-tools/

# Or install Visual Studio Community with C++ workload
```

#### **Install Dependencies:**
```bash
# Full installation
pip install -r requirements-client.txt

# Or minimal installation
pip install -r requirements-client-minimal.txt
```

#### **Windows-Specific Features:**
- ✅ **dxcam**: High-performance screen capture
- ✅ **pyaudio**: Audio capture
- ✅ **pywin32**: Windows API access
- ✅ **keyboard**: Global hotkey support

### **Linux Installation (Ubuntu/Debian)**

#### **Prerequisites:**
```bash
# Install system packages
sudo apt-get update
sudo apt-get install -y \
    portaudio19-dev \
    python3-pyaudio \
    libasound2-dev \
    libportaudio2 \
    libportaudiocpp0 \
    portaudio19-dev \
    python3-dev \
    build-essential
```

#### **Install Dependencies:**
```bash
# Full installation
pip install -r requirements-client.txt

# Or minimal installation
pip install -r requirements-client-minimal.txt
```

### **macOS Installation**

#### **Prerequisites:**
```bash
# Install Homebrew (if not already installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install system packages
brew install portaudio
```

#### **Install Dependencies:**
```bash
# Full installation
pip install -r requirements-client.txt

# Or minimal installation
pip install -r requirements-client-minimal.txt
```

## 🔧 Feature-Specific Dependencies

### **Core Features (Always Required):**
```bash
pip install python-socketio requests psutil cryptography
```

### **Screen Capture:**
```bash
pip install mss
# Windows only: pip install dxcam
```

### **Audio Features:**
```bash
# Windows
pip install pyaudio

# Linux/macOS
pip install sounddevice
```

### **Input Control:**
```bash
pip install pynput keyboard pyautogui
```

### **Image Processing:**
```bash
pip install pillow numpy opencv-python
```

### **WebRTC Streaming:**
```bash
pip install aiortc
```

### **Performance Optimization:**
```bash
pip install msgpack lz4 zstandard xxhash
# Linux/macOS only: pip install uvloop
```

## 🚨 Troubleshooting

### **Common Issues:**

#### **1. PyAudio Installation Fails (Windows):**
```bash
# Download pre-compiled wheel from:
# https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio

# Then install:
pip install PyAudio-0.2.11-cp39-cp39-win_amd64.whl
```

#### **2. PortAudio Issues (Linux):**
```bash
sudo apt-get install portaudio19-dev
pip install pyaudio
```

#### **3. OpenCV Installation Issues:**
```bash
# Try different installation methods:
pip install opencv-python-headless
# or
pip install opencv-contrib-python
```

#### **4. Permission Issues (Linux/macOS):**
```bash
# For audio access:
sudo usermod -a -G audio $USER
# Then logout and login again
```

## ✅ Verification

### **Test Installation:**
```bash
python3 -c "
import socketio
import requests
import mss
import psutil
print('✅ Core dependencies installed successfully!')
"
```

### **Test Client Connection:**
```bash
python3 client.py
```

## 📊 Dependency Categories

| Category | Dependencies | Required |
|----------|-------------|----------|
| **Communication** | python-socketio, requests | ✅ Yes |
| **Screen Capture** | mss, dxcam (Windows) | ✅ Yes |
| **System Monitoring** | psutil | ✅ Yes |
| **Security** | cryptography | ✅ Yes |
| **Audio** | pyaudio, sounddevice | 🔶 Optional |
| **Input Control** | pynput, keyboard, pyautogui | 🔶 Optional |
| **Image Processing** | pillow, numpy, opencv-python | 🔶 Optional |
| **WebRTC** | aiortc | 🔶 Optional |
| **Performance** | msgpack, lz4, zstandard, xxhash | 🔶 Optional |

## 🎯 Quick Start

### **For Basic Functionality:**
```bash
pip install python-socketio requests mss psutil cryptography
python3 client.py
```

### **For Full Features:**
```bash
pip install -r requirements-client.txt
python3 client.py
```

## 📝 Notes

- **Core dependencies** are required for basic client functionality
- **Optional dependencies** enable additional features but the client will work without them
- **Platform-specific packages** are automatically handled by pip
- **System packages** may be required on Linux/macOS for audio support

The client is designed to gracefully handle missing dependencies and will log warnings for unavailable features.