# Neural Control Hub - Frontend & Backend Setup

🚀 **Complete setup guide for running the Neural Control Hub with separate frontend and backend components.**

## 📋 Overview

This setup separates the Neural Control Hub into two components:

- **Backend**: `controller.py` - Python Flask/SocketIO server providing REST API and WebSocket communication
- **Frontend**: `agent-controller ui/` - React/TypeScript web application with modern UI

## 🛠️ Prerequisites

### Backend Requirements
- **Python 3.8+** 
- **pip** (Python package manager)

### Frontend Requirements
- **Node.js 18+**
- **npm** (Node package manager)

## 🚀 Quick Start

### Option 1: Automated Startup (Recommended)

1. **Start Backend** (Terminal 1):
   ```bash
   ./start-backend.sh
   ```

2. **Start Frontend** (Terminal 2):
   ```bash
   ./start-frontend.sh
   ```

### Option 2: Manual Startup

#### Backend Setup
```bash
# Install backend dependencies
pip3 install -r backend-requirements.txt

# Start backend server
python3 start-backend.py
```

#### Frontend Setup
```bash
# Navigate to frontend directory
cd "agent-controller ui"

# Install frontend dependencies
npm install

# Start frontend development server
npm run dev
```

## 🌐 Access URLs

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8080/api/
- **Backend WebSocket**: ws://localhost:8080/socket.io/

## 🔐 Default Credentials

- **Admin Password**: `q`

## 📁 Project Structure

```
workspace/
├── controller.py                 # Backend server
├── start-backend.py             # Backend startup script
├── backend-requirements.txt     # Backend dependencies
├── start-backend.sh             # Backend startup script (bash)
├── start-frontend.sh            # Frontend startup script (bash)
├── agent-controller ui/         # Frontend application
│   ├── src/
│   │   ├── services/
│   │   │   ├── api.ts           # API client
│   │   │   └── websocket.ts     # WebSocket client
│   │   ├── components/
│   │   │   ├── Login.tsx        # Login component
│   │   │   └── SocketProvider-new.tsx  # Updated socket provider
│   │   └── ...
│   ├── .env.development         # Development environment config
│   ├── .env.production          # Production environment config
│   └── package.json             # Frontend dependencies
└── README-SETUP.md              # This file
```

## 🔧 Configuration

### Backend Configuration

Environment variables (optional):
```bash
export ADMIN_PASSWORD="your-secure-password"
export HOST="0.0.0.0"
export PORT="8080"
export SESSION_TIMEOUT="3600"
```

### Frontend Configuration

Edit `.env.development` or `.env.production`:
```env
VITE_API_URL=http://localhost:8080
VITE_WS_URL=http://localhost:8080
```

## 🚀 Features

### Backend API Endpoints

#### Authentication
- `POST /api/auth/login` - Login with password
- `POST /api/auth/logout` - Logout
- `GET /api/auth/status` - Check auth status

#### Agent Management
- `GET /api/agents` - List all agents
- `GET /api/agents/<id>` - Get agent details
- `GET /api/agents/search` - Search/filter agents

#### Streaming Control
- `POST /api/agents/<id>/stream/<type>/start` - Start stream
- `POST /api/agents/<id>/stream/<type>/stop` - Stop stream

#### Command Execution
- `POST /api/agents/<id>/execute` - Execute command
- `GET /api/agents/<id>/commands/history` - Command history

#### File Management
- `GET /api/agents/<id>/files` - Browse files
- `POST /api/agents/<id>/files/download` - Download file
- `POST /api/agents/<id>/files/upload` - Upload file

#### System Monitoring
- `GET /api/system/stats` - System statistics
- `GET /api/system/info` - Server information

### Real-time WebSocket Events

- `agent_connect/disconnect` - Agent connection status
- `performance_update` - Real-time performance metrics
- `command_result` - Command execution results
- `stream_status_update` - Stream status changes
- `file_operation_result` - File operation outcomes
- `system_alert` - System alerts
- `activity_update` - Real-time activity feed

### Frontend Features

- **🔐 Secure Authentication** - Login with password protection
- **📊 Real-time Dashboard** - Live agent monitoring
- **🖥️ Agent Management** - View and control connected agents
- **🎥 Stream Viewer** - Screen, camera, and audio streaming
- **💻 Command Panel** - Execute commands with history
- **📁 File Manager** - Browse, upload, download files
- **📈 System Monitor** - Performance metrics and stats
- **📋 Activity Feed** - Real-time activity logging
- **⚡ Quick Actions** - Bulk operations on multiple agents
- **🔍 Search & Filter** - Advanced agent filtering
- **⚙️ Settings** - System configuration management

## 🔒 Security Features

- **Session Management** - Secure session handling with timeouts
- **IP-based Rate Limiting** - Protection against brute force attacks
- **CORS Protection** - Cross-origin request security
- **Password Hashing** - PBKDF2 with salt for password security
- **WebSocket Authentication** - Secure real-time communication

## 🐛 Troubleshooting

### Backend Issues

1. **Import Errors**:
   ```bash
   pip3 install flask flask-socketio flask-cors eventlet psutil
   ```

2. **Port Already in Use**:
   ```bash
   export PORT=8081  # Use different port
   ```

3. **Permission Errors**:
   ```bash
   sudo python3 start-backend.py  # Run with elevated permissions
   ```

### Frontend Issues

1. **Node Module Errors**:
   ```bash
   cd "agent-controller ui"
   rm -rf node_modules package-lock.json
   npm install
   ```

2. **Build Errors**:
   ```bash
   npm run build  # Check for build issues
   ```

3. **Connection Issues**:
   - Verify backend is running on port 8080
   - Check `.env.development` configuration
   - Ensure CORS is properly configured

### Common Issues

1. **CORS Errors**: Backend CORS is configured for localhost:3000. Update if using different ports.

2. **WebSocket Connection Failed**: Ensure backend is running and accessible.

3. **Authentication Issues**: Default password is 'q'. Check console for detailed error messages.

## 📝 Development

### Adding New Features

1. **Backend**: Add new routes in `controller.py`
2. **Frontend**: Add API calls in `src/services/api.ts`
3. **Real-time**: Add WebSocket events in `src/services/websocket.ts`

### Testing

```bash
# Backend
python3 -m pytest tests/

# Frontend
cd "agent-controller ui"
npm test
```

## 🚀 Production Deployment

1. **Backend**: Use production WSGI server (gunicorn, uwsgi)
2. **Frontend**: Build and serve static files
3. **Security**: Use HTTPS, secure passwords, firewall rules
4. **Monitoring**: Set up logging and monitoring

## 📞 Support

For issues or questions:
1. Check the troubleshooting section
2. Review console logs for detailed error messages
3. Ensure all dependencies are properly installed
4. Verify network connectivity between frontend and backend

---

**🎉 Enjoy using Neural Control Hub!**