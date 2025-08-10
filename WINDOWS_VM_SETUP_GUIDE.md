# Windows 11 Oracle VM Setup Guide for WebRTC Agent

## 🚀 Quick Start for Windows 11 Oracle VM

### 1. Download Required Files
Make sure you have these files in your VM:
- `main.py` - The WebRTC agent
- `requirements-windows.txt` - Windows-specific dependencies
- `setup-windows.bat` - Automated setup script

### 2. Run Setup Script
```cmd
# Right-click setup-windows.bat and "Run as Administrator"
# OR open Command Prompt as Administrator and run:
setup-windows.bat
```

### 3. Start the Agent
```cmd
# Option 1: Normal startup
start-agent.bat

# Option 2: Administrator startup (if you get permission errors)
start-agent-admin.bat
```

## 📋 Prerequisites

### System Requirements
- **OS**: Windows 11 (Oracle VM)
- **RAM**: Minimum 4GB, Recommended 8GB+
- **Storage**: Minimum 20GB free space
- **Python**: 3.7+ (automatically checked by setup script)

### Oracle VM Specific
- **VirtualBox Guest Additions**: Install for better performance
- **Shared Folders**: Enable if transferring files from host
- **Network**: Bridge adapter recommended for better connectivity

## 🔧 Manual Installation (Alternative)

If the automated script doesn't work:

### 1. Install Python
1. Download Python 3.7+ from [python.org](https://python.org)
2. **IMPORTANT**: Check "Add Python to PATH" during installation
3. **IMPORTANT**: Check "Install pip" during installation

### 2. Open Command Prompt as Administrator
```cmd
# Press Win + X, then "Windows Terminal (Admin)" or "Command Prompt (Admin)"
```

### 3. Create Virtual Environment
```cmd
cd /d "C:\path\to\your\agent\folder"
python -m venv webrtc-env
webrtc-env\Scripts\activate.bat
```

### 4. Install Dependencies
```cmd
pip install --upgrade pip
pip install -r requirements-windows.txt
```

## ⚙️ Configuration

### 1. Edit main.py
```python
# Find and update these lines:
CONTROLLER_HOST = "YOUR_CONTROLLER_IP"  # Change to your controller IP
CONTROLLER_PORT = 8080                   # Change if needed
```

### 2. Windows-Specific Settings
```python
# In main.py, ensure these Windows-specific features are enabled:
WINDOWS_SPECIFIC_FEATURES = True
ADMIN_PRIVILEGES_REQUIRED = False  # Set to True if you need admin features
```

## 🧪 Testing

### 1. Test Dependencies
```cmd
# Run the test script created by setup
test-dependencies.bat

# Or test manually:
webrtc-env\Scripts\activate.bat
python -c "import aiortc; print('✅ WebRTC OK')"
python -c "import pyaudio; print('✅ Audio OK')"
python -c "import mss; print('✅ Screen Capture OK')"
python -c "import cv2; print('✅ OpenCV OK')"
```

### 2. Test WebRTC Connection
```cmd
# Start the agent and check for connection messages
start-agent.bat
```

## 🚨 Troubleshooting

### Common Windows Issues

#### 1. Python Not Found
```cmd
# Check if Python is in PATH
python --version

# If not found, reinstall Python and check "Add to PATH"
# Or manually add Python to PATH:
setx PATH "%PATH%;C:\Python39;C:\Python39\Scripts"
```

#### 2. Permission Errors
```cmd
# Run Command Prompt as Administrator
# Right-click Command Prompt → "Run as Administrator"

# Or use the admin startup script:
start-agent-admin.bat
```

#### 3. Windows Defender Blocking
1. Open Windows Security
2. Go to "Virus & threat protection"
3. Click "Manage settings"
4. Add your agent folder to exclusions

#### 4. PyAudio Installation Failed
```cmd
# Try installing from wheel:
pip install pipwin
pipwin install pyaudio

# Or download pre-compiled wheel from:
# https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio
```

#### 5. Virtual Environment Issues
```cmd
# Remove and recreate virtual environment:
rmdir /s webrtc-env
python -m venv webrtc-env
webrtc-env\Scripts\activate.bat
pip install -r requirements-windows.txt
```

### Oracle VM Specific Issues

#### 1. Poor Performance
- Install VirtualBox Guest Additions
- Allocate more RAM/CPU cores to VM
- Enable hardware acceleration in VM settings

#### 2. Network Issues
- Set network adapter to "Bridge Adapter"
- Ensure host firewall allows VM traffic
- Check VM network settings

#### 3. File Transfer Issues
- Enable shared folders in VM settings
- Use drag-and-drop if enabled
- Copy files through shared clipboard

## 🔄 Updates

### Update Dependencies
```cmd
webrtc-env\Scripts\activate.bat
pip install --upgrade -r requirements-windows.txt
```

### Update Code
```cmd
# Stop the agent (Ctrl+C)
# Update main.py
# Restart: start-agent.bat
```

## 📊 Monitoring

### Check Process Status
```cmd
# Task Manager
taskmgr

# Or Command Prompt
tasklist | findstr python
```

### View Logs
```cmd
# Check console output in the agent window
# Or redirect output to file:
start-agent.bat > agent.log 2>&1
```

### Performance Monitoring
```cmd
# Resource Monitor
resmon

# Or Task Manager → Performance tab
```

## 🛡️ Security Considerations

### Windows Security
1. **Windows Defender**: May need exclusions for Python scripts
2. **User Account Control**: Run as Administrator if needed
3. **Firewall**: Allow Python through Windows Firewall

### VM Security
1. **Guest Additions**: Keep updated for security patches
2. **Network Isolation**: Use bridge adapter for better control
3. **Shared Resources**: Limit shared folders and clipboard

## 🎯 Oracle VM Optimization

### 1. VM Settings
- **RAM**: Allocate at least 4GB (8GB recommended)
- **CPU**: Allocate 2+ cores
- **Storage**: Use SSD if possible, allocate 20GB+
- **Network**: Bridge adapter for best connectivity

### 2. Guest Additions
```cmd
# Install VirtualBox Guest Additions
# This improves performance and integration
```

### 3. Performance Tips
- Enable hardware acceleration in VM settings
- Allocate more video memory
- Use bridged networking for better performance

## 📚 Additional Resources

### Windows-Specific
- [Python on Windows](https://docs.python.org/3/using/windows.html)
- [Windows Subsystem for Linux (WSL)](https://docs.microsoft.com/en-us/windows/wsl/)
- [Windows Terminal](https://docs.microsoft.com/en-us/windows/terminal/)

### WebRTC
- [aiortc Documentation](https://aiortc.readthedocs.io/)
- [WebRTC API](https://developer.mozilla.org/en-US/docs/Web/API/WebRTC_API)

## 🎯 Next Steps

After successful installation:

1. **Test Connection**: Verify agent connects to controller
2. **Test WebRTC**: Start streaming and verify quality
3. **Monitor Performance**: Use the new optimization features
4. **Scale Up**: Plan for production deployment

## 📞 Support

If you encounter issues:

1. **Check this guide** for common solutions
2. **Run test-dependencies.bat** to verify installation
3. **Check Windows Event Viewer** for system errors
4. **Verify VM network settings** and connectivity
5. **Ensure Windows Defender** isn't blocking Python

---

**Happy Streaming on Windows 11! 🎥✨**