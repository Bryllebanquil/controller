# 🚀 Agent Controller Deployment Guide

## 📋 Overview

This system consists of:
- **Controller (Backend + UI v2.1)**: Flask server with integrated React UI
- **Client (Agent)**: Python agent that connects to the controller

## 🏃‍♂️ Local Development

### 1. Run the Controller
```bash
# Install dependencies
pip install --break-system-packages flask flask-socketio flask-cors

# Run the controller (serves UI v2.1 at http://localhost:8080)
python3 controller.py
```

### 2. Run the Client
```bash
# The client will connect to the controller automatically
python3 client.py
```

### 3. Access the System
- **Web UI**: http://localhost:8080
- **Login**: Use the default password `q` (or set `ADMIN_PASSWORD` env var)

## 🌐 Render Deployment

### Prerequisites
1. GitHub repository with your code
2. Render account
3. Updated `render.yaml` (already configured)

### Deployment Steps

#### 1. Update Environment Variables
Before deploying, update these in your `render.yaml`:

```yaml
envVars:
  - key: ADMIN_PASSWORD
    value: "your_secure_password_here"  # Change this!
  - key: SECRET_KEY
    value: "your_secret_key_here"       # Generate a secure key
```

#### 2. Deploy to Render
1. Connect your GitHub repository to Render
2. Render will automatically detect the `render.yaml` file
3. The deployment will:
   - Install Python dependencies from `requirements-controller.txt`
   - Start the controller with Gunicorn
   - Serve the integrated UI v2.1

#### 3. Access Your Deployed System
- **URL**: `https://agent-controller-backend.onrender.com`
- **Login**: Use the password you set in `ADMIN_PASSWORD`

### Client Connection
The client (`client.py`) is already configured to connect to:
```
https://agent-controller-backend.onrender.com
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ADMIN_PASSWORD` | Admin login password | `q` |
| `SECRET_KEY` | Flask secret key | Auto-generated |
| `HOST` | Server host | `0.0.0.0` |
| `PORT` | Server port | `8080` |
| `SESSION_TIMEOUT` | Session timeout (seconds) | `3600` |
| `MAX_LOGIN_ATTEMPTS` | Max login attempts | `5` |
| `LOGIN_TIMEOUT` | Login lockout (seconds) | `300` |

### Client Configuration
The client automatically connects to the controller using:
- **Fixed URL**: `https://agent-controller-backend.onrender.com`
- **Protocol**: Socket.IO for real-time communication
- **Streaming**: WebRTC for low-latency video/audio

## 🛠️ Troubleshooting

### Common Issues

1. **Controller won't start**
   ```bash
   # Check dependencies
   pip install --break-system-packages flask flask-socketio flask-cors
   ```

2. **Client can't connect**
   - Verify the controller is running
   - Check firewall settings
   - Ensure the URL in `client.py` matches your deployment

3. **UI not loading**
   - Check if static assets are being served
   - Verify the build directory exists: `agent-controller ui v2.1/build/`

### Logs
- **Controller logs**: Check Render dashboard or console output
- **Client logs**: Check console output when running `python3 client.py`

## 🔒 Security Notes

1. **Change default passwords** before deployment
2. **Use HTTPS** in production (Render provides this automatically)
3. **Set strong SECRET_KEY** for session management
4. **Configure CORS** if needed for custom domains

## 📊 System Architecture

```
┌─────────────────┐    Socket.IO    ┌─────────────────┐
│   Client.py     │◄──────────────►│  Controller.py  │
│   (Agent)       │                 │  (Backend+UI)   │
│                 │                 │                 │
│ • Screen capture│                 │ • Web UI v2.1   │
│ • Audio capture │                 │ • Agent mgmt    │
│ • Command exec  │                 │ • Real-time     │
│ • File ops      │                 │   streaming     │
└─────────────────┘                 └─────────────────┘
```

## 🎯 Next Steps

1. **Deploy to Render** using the updated `render.yaml`
2. **Test the connection** by running a client
3. **Customize the UI** if needed in `agent-controller ui v2.1/src/`
4. **Set up monitoring** and logging as needed

The system is now ready for deployment! 🚀