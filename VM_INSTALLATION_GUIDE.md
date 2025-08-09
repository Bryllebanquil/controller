# VM Installation Guide for WebRTC Agent

## 🚀 Quick Start

### 1. Clone/Download Files
```bash
# Make sure you have these files in your VM:
# - main.py
# - requirements-simple.txt
# - setup-vm.sh
```

### 2. Run Setup Script
```bash
# Make script executable and run
chmod +x setup-vm.sh
sudo bash setup-vm.sh
```

### 3. Start the Agent
```bash
# Option 1: Direct start
./start-agent.sh

# Option 2: Systemd service
sudo systemctl start webrtc-agent
sudo systemctl status webrtc-agent
```

## 📋 Prerequisites

### System Requirements
- **OS**: Ubuntu 18.04+ or Debian 10+
- **RAM**: Minimum 2GB, Recommended 4GB+
- **Storage**: Minimum 10GB free space
- **Python**: 3.7+ (automatically installed by script)

### Network Requirements
- **Outbound**: HTTP/HTTPS (for controller communication)
- **WebRTC**: STUN/TURN server access (if behind NAT)
- **Ports**: Dynamic (WebRTC uses random ports)

## 🔧 Manual Installation (Alternative)

If you prefer manual installation:

### 1. Install System Dependencies
```bash
sudo apt-get update
sudo apt-get install -y \
    python3 \
    python3-pip \
    python3-dev \
    build-essential \
    libasound2-dev \
    portaudio19-dev \
    ffmpeg \
    libavcodec-dev \
    libavformat-dev \
    libswscale-dev
```

### 2. Create Virtual Environment
```bash
python3 -m venv webrtc-env
source webrtc-env/bin/activate
```

### 3. Install Python Dependencies
```bash
pip install --upgrade pip
pip install -r requirements-simple.txt
```

## ⚙️ Configuration

### 1. Edit main.py
```python
# Find and update these lines:
CONTROLLER_HOST = "YOUR_CONTROLLER_IP"  # Change to your controller IP
CONTROLLER_PORT = 8080                   # Change if needed
```

### 2. Environment Variables (Optional)
```bash
export WEBRTC_ENABLED=true
export CONTROLLER_HOST=YOUR_CONTROLLER_IP
export CONTROLLER_PORT=8080
```

## 🧪 Testing

### 1. Test WebRTC Installation
```bash
source webrtc-env/bin/activate
python3 -c "import aiortc; print('✅ WebRTC OK')"
```

### 2. Test Audio Support
```bash
python3 -c "import pyaudio; print('✅ Audio OK')"
```

### 3. Test Screen Capture
```bash
python3 -c "import mss; print('✅ Screen Capture OK')"
```

## 🚨 Troubleshooting

### Common Issues

#### 1. PyAudio Installation Failed
```bash
# On Ubuntu/Debian
sudo apt-get install -y portaudio19-dev
pip install --global-option='build_ext' --global-option='-I/usr/include/alsa' PyAudio

# Alternative: Use system package
sudo apt-get install -y python3-pyaudio
```

#### 2. OpenCV Issues
```bash
# For headless environments
pip uninstall opencv-python
pip install opencv-python-headless
```

#### 3. WebRTC Connection Issues
```bash
# Check firewall settings
sudo ufw status
sudo ufw allow 8080  # If using specific port

# Check STUN/TURN server access
curl -I stun:stun.l.google.com:19302
```

#### 4. Permission Issues
```bash
# Fix audio permissions
sudo usermod -a -G audio $USER
# Logout and login again
```

### Debug Mode
```bash
# Run with verbose logging
python3 main.py --debug

# Check systemd logs
sudo journalctl -u webrtc-agent -f
```

## 🔄 Updates

### Update Dependencies
```bash
source webrtc-env/bin/activate
pip install --upgrade -r requirements-simple.txt
```

### Update Code
```bash
# Stop service
sudo systemctl stop webrtc-agent

# Update main.py
# Restart service
sudo systemctl start webrtc-agent
```

## 📊 Monitoring

### Check Service Status
```bash
sudo systemctl status webrtc-agent
sudo systemctl is-enabled webrtc-agent
```

### View Logs
```bash
# Real-time logs
sudo journalctl -u webrtc-agent -f

# Recent logs
sudo journalctl -u webrtc-agent -n 100
```

### Performance Monitoring
```bash
# CPU and memory usage
htop

# Network connections
netstat -tulpn | grep python
```

## 🛡️ Security Considerations

### Firewall Configuration
```bash
# Allow only necessary outbound traffic
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw enable
```

### User Permissions
```bash
# Create dedicated user (recommended)
sudo adduser webrtc-agent
sudo usermod -a -G audio,video webrtc-agent
```

### SSL/TLS (if needed)
```bash
# Generate self-signed certificate
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes
```

## 📚 Additional Resources

### Documentation
- [aiortc Documentation](https://aiortc.readthedocs.io/)
- [WebRTC API](https://developer.mozilla.org/en-US/docs/Web/API/WebRTC_API)
- [Socket.IO Python Client](https://python-socketio.readthedocs.io/)

### Community Support
- [aiortc GitHub Issues](https://github.com/aiortc/aiortc/issues)
- [WebRTC Forum](https://groups.google.com/forum/#!forum/discuss-webrtc)

## 🎯 Next Steps

After successful installation:

1. **Test Connection**: Verify agent connects to controller
2. **Test WebRTC**: Start streaming and verify quality
3. **Monitor Performance**: Use the new optimization features
4. **Scale Up**: Plan for production deployment with mediasoup

## 📞 Support

If you encounter issues:
1. Check the troubleshooting section above
2. Review logs: `sudo journalctl -u webrtc-agent -f`
3. Verify network connectivity to controller
4. Test individual components (WebRTC, audio, screen capture)

---

**Happy Streaming! 🎥✨**