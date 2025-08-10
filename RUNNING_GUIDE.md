# Complete Guide to Run `main.py`

## 🚀 Quick Start

### 1. Install Dependencies
```bash
# Install all required packages
pip install -r requirements.txt

# Or install individually for specific needs
pip install aiortc aiohttp python-socketio[client] opencv-python mss PyAudio
```

### 2. Basic Usage
```bash
# Run as agent (default)
python main.py

# Run as controller
python main.py --mode controller

# Run both agent and controller
python main.py --mode both
```

## 📋 Prerequisites

### System Requirements
- **Python**: 3.8 or higher
- **OS**: Windows 10/11, Linux (Ubuntu 18.04+), macOS 10.15+
- **RAM**: Minimum 4GB, Recommended 8GB+
- **Storage**: 2GB free space
- **Network**: Internet connection for Socket.IO

### Windows-Specific Requirements
- Visual C++ Redistributable 2015-2022
- Windows SDK (for some packages)
- Administrator privileges (for full functionality)

### Linux-Specific Requirements
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y python3-dev python3-pip
sudo apt-get install -y libasound2-dev portaudio19-dev
sudo apt-get install -y ffmpeg libavcodec-dev libavformat-dev
sudo apt-get install -y libgtk-3-dev libcanberra-gtk3-module

# CentOS/RHEL
sudo yum install -y python3-devel python3-pip
sudo yum install -y alsa-lib-devel portaudio-devel
sudo yum install -y ffmpeg-devel
```

## 🔧 Installation Steps

### Step 1: Python Environment
```bash
# Check Python version
python --version

# Create virtual environment (recommended)
python -m venv webrtc_env
source webrtc_env/bin/activate  # Linux/macOS
webrtc_env\Scripts\activate     # Windows
```

### Step 2: Install Dependencies
```bash
# Upgrade pip
pip install --upgrade pip

# Install requirements
pip install -r requirements.txt

# Verify installation
python -c "import aiortc, opencv, mss, pyaudio; print('All modules imported successfully!')"
```

### Step 3: Test Installation
```bash
# Test basic functionality
python -c "import main; print('main.py imports successfully')"

# Check WebRTC availability
python -c "from main import AIORTC_AVAILABLE; print(f'WebRTC available: {AIORTC_AVAILABLE}')"
```

## 🎯 Running Modes

### Agent Mode (Default)
```bash
python main.py
```
**What it does:**
- Connects to Socket.IO server
- Waits for remote commands
- Can stream screen, audio, camera
- Supports WebRTC for low-latency streaming

**Use case:** Remote control agent, monitoring, automation

### Controller Mode
```bash
python main.py --mode controller
python main.py --mode controller --port 9000
python main.py --mode controller --no-ssl
```
**What it does:**
- Starts web server (HTTP/HTTPS)
- Provides dashboard interface
- Controls connected agents
- Available at `http://localhost:8080`

**Use case:** Control panel, monitoring dashboard, remote management

### Both Mode
```bash
python main.py --mode both
```
**What it does:**
- Runs controller in background thread
- Runs agent in main thread
- Self-contained operation

**Use case:** Standalone system, testing, development

## 🌐 Network Configuration

### Socket.IO Server Connection
The agent connects to a Socket.IO server. You need to configure:

1. **Server URL** in the code
2. **Authentication** if required
3. **Firewall rules** for the connection

### WebRTC Configuration
For optimal WebRTC performance:

1. **STUN/TURN servers** for NAT traversal
2. **ICE candidates** for connection establishment
3. **Bandwidth estimation** for adaptive quality

## 📊 Performance Optimization

### WebRTC Settings
```python
# In main.py, these settings control performance:
WEBRTC_CONFIG = {
    'quality_levels': ['low', 'medium', 'high', 'ultra'],
    'performance_tuning': {
        'ultra_low_latency': True,
        'hardware_acceleration': True,
        'adaptive_bitrate': True,
        'frame_dropping': True
    }
}
```

### System Optimization
- **CPU Priority**: Run with higher priority
- **Memory**: Ensure sufficient RAM
- **Network**: Use wired connection when possible
- **Storage**: SSD for better I/O performance

## 🚨 Troubleshooting

### Common Issues

#### 1. Import Errors
```bash
# Error: No module named 'aiortc'
pip install aiortc

# Error: No module named 'cv2'
pip install opencv-python

# Error: No module named 'mss'
pip install mss
```

#### 2. Permission Errors
```bash
# Windows: Run as Administrator
# Linux: Use sudo or proper permissions
sudo python main.py

# macOS: Grant accessibility permissions
```

#### 3. Audio/Video Issues
```bash
# PyAudio issues on Linux
sudo apt-get install portaudio19-dev
pip install --global-option='build_ext' PyAudio

# OpenCV issues
pip install opencv-python-headless  # For headless environments
```

#### 4. Network Issues
```bash
# Check firewall settings
# Verify Socket.IO server is accessible
# Check STUN/TURN server configuration
```

### Debug Mode
```bash
# Enable verbose logging
export PYTHONPATH=.
python main.py --debug

# Check logs for detailed information
```

## 🔒 Security Considerations

### Production Deployment
1. **Use HTTPS** (SSL enabled by default)
2. **Implement authentication**
3. **Configure firewall rules**
4. **Monitor access logs**
5. **Regular security updates**

### Network Security
- **Firewall configuration**
- **VPN usage** for remote access
- **STUN/TURN server security**
- **Encrypted communication**

## 📈 Monitoring and Maintenance

### Performance Metrics
- **Latency**: Target <1 second
- **FPS**: Target 30 FPS
- **Bandwidth**: Monitor usage
- **CPU/Memory**: System resources

### Logging
```bash
# Check application logs
# Monitor system resources
# Track connection quality
# Monitor WebRTC statistics
```

### Updates
```bash
# Update dependencies regularly
pip install --upgrade -r requirements.txt

# Check for security updates
# Monitor for new features
```

## 🎮 Advanced Usage

### Custom Configuration
```python
# Modify WEBRTC_CONFIG in main.py
# Adjust performance settings
# Configure custom STUN/TURN servers
# Set quality preferences
```

### Integration
- **API endpoints** for external control
- **Webhook support** for notifications
- **Database integration** for logging
- **Monitoring systems** integration

### Scaling
- **Load balancing** for multiple agents
- **Database clustering** for high availability
- **CDN integration** for global access
- **Microservices architecture**

## 📚 Additional Resources

### Documentation
- [aiortc Documentation](https://aiortc.readthedocs.io/)
- [Socket.IO Documentation](https://socket.io/docs/)
- [OpenCV Documentation](https://docs.opencv.org/)

### Community
- GitHub Issues for bug reports
- Stack Overflow for questions
- Discord/Slack communities

### Support
- Check logs for error details
- Verify system requirements
- Test with minimal configuration
- Use debug mode for troubleshooting

## ✅ Success Checklist

- [ ] Python 3.8+ installed
- [ ] Dependencies installed successfully
- [ ] No import errors
- [ ] Network connectivity verified
- [ ] Permissions configured correctly
- [ ] Firewall rules updated
- [ ] SSL certificates configured (if needed)
- [ ] Performance optimized
- [ ] Security measures implemented
- [ ] Monitoring configured
- [ ] Backup strategy in place

## 🆘 Emergency Procedures

### If main.py crashes:
1. Check error logs
2. Verify dependencies
3. Test with minimal configuration
4. Restart the application
5. Check system resources

### If WebRTC fails:
1. Verify network connectivity
2. Check STUN/TURN servers
3. Verify firewall settings
4. Test with different browsers
5. Check browser console for errors

### If performance degrades:
1. Monitor system resources
2. Check network quality
3. Adjust quality settings
4. Restart the application
5. Consider hardware upgrades

---

**Remember**: This is a powerful tool. Use responsibly and ensure proper security measures are in place for production deployments.