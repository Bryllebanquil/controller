#!/bin/bash

# VM Setup Script for WebRTC Agent
# This script installs all necessary dependencies for main.py
# Run with: sudo bash setup-vm.sh

set -e  # Exit on any error

echo "🚀 Setting up VM for WebRTC Agent..."

# Update system packages
echo "📦 Updating system packages..."
apt-get update

# Install system dependencies
echo "🔧 Installing system dependencies..."
apt-get install -y \
    python3 \
    python3-pip \
    python3-dev \
    python3-venv \
    build-essential \
    cmake \
    pkg-config \
    libasound2-dev \
    portaudio19-dev \
    libportaudio2 \
    libportaudiocpp0 \
    ffmpeg \
    libavcodec-dev \
    libavformat-dev \
    libswscale-dev \
    libgtk-3-dev \
    libcanberra-gtk3-module \
    libx11-dev \
    libxrandr-dev \
    libxinerama-dev \
    libxcursor-dev \
    libgstreamer1.0-dev \
    libgstreamer-plugins-base1.0-dev \
    libgstreamer-plugins-bad1.0-dev \
    gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-bad \
    gstreamer1.0-plugins-ugly \
    gstreamer1.0-libav \
    gstreamer1.0-tools \
    gstreamer1.0-x \
    gstreamer1.0-alsa \
    gstreamer1.0-gl \
    gstreamer1.0-gtk3 \
    gstreamer1.0-qt5 \
    gstreamer1.0-pulseaudio

# Create Python virtual environment
echo "🐍 Creating Python virtual environment..."
python3 -m venv webrtc-env
source webrtc-env/bin/activate

# Upgrade pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip

# Install Python dependencies
echo "📚 Installing Python dependencies..."
pip install -r requirements-simple.txt

# Install additional dependencies that might be needed
echo "🔧 Installing additional dependencies..."
pip install \
    av>=9.0.0 \
    aioice>=0.7.0 \
    pyee>=9.0.0

# Create startup script
echo "📝 Creating startup script..."
cat > start-agent.sh << 'EOF'
#!/bin/bash
# Startup script for WebRTC Agent
cd "$(dirname "$0")"
source webrtc-env/bin/activate
python3 main.py
EOF

chmod +x start-agent.sh

# Create systemd service (optional)
echo "🔧 Creating systemd service..."
cat > /etc/systemd/system/webrtc-agent.service << EOF
[Unit]
Description=WebRTC Agent Service
After=network.target

[Service]
Type=simple
User=$SUDO_USER
WorkingDirectory=$(pwd)
ExecStart=$(pwd)/start-agent.sh
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
systemctl daemon-reload
systemctl enable webrtc-agent.service

echo "✅ VM setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Configure your controller IP in main.py"
echo "2. Start the agent: ./start-agent.sh"
echo "3. Or use systemd: sudo systemctl start webrtc-agent"
echo "4. Check status: sudo systemctl status webrtc-agent"
echo ""
echo "🔍 Troubleshooting:"
echo "- Check logs: sudo journalctl -u webrtc-agent -f"
echo "- Test WebRTC: python3 -c 'import aiortc; print(\"WebRTC OK\")'"
echo "- Test audio: python3 -c 'import pyaudio; print(\"Audio OK\")'"
echo ""
echo "🌐 WebRTC Agent is ready to run!"