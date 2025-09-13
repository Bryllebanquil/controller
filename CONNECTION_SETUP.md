# Complete System Connection Setup

This document explains how the frontend UI, controller.py backend, and client.py agent are connected in the Neural Control Hub.

## Architecture Overview

```
┌─────────────────┐    HTTP/WebSocket    ┌─────────────────┐    Socket.IO    ┌─────────────────┐
│   Frontend UI   │ ←─────────────────→ │  Controller.py  │ ←──────────────→ │   Client.py     │
│  (React + Vite) │                     │  (Flask Server) │                  │  (Agent Client) │
│   Port: 3000    │                     │   Port: 8080    │                  │  (Connects to)  │
└─────────────────┘                     └─────────────────┘                  └─────────────────┘
```

### Component Roles:
- **Frontend UI**: Web interface for operators to monitor and control agents
- **Controller.py**: Central server that manages agents and provides API endpoints
- **Client.py**: Agent that runs on target systems and connects to the controller

## Connection Configuration

### Frontend Configuration

**Environment Variables** (`.env` files):
- `VITE_API_URL`: Backend API base URL (default: `http://localhost:8080`)
- `VITE_WS_URL`: WebSocket URL for real-time communication (default: `http://localhost:8080`)

**API Service** (`src/services/api.ts`):
- Configured to use environment variables for API endpoints
- Handles authentication, agent management, streaming, file operations
- Includes proper error handling and response typing

**WebSocket Service** (`src/services/websocket.ts`):
- Real-time communication via Socket.IO
- Handles agent updates, command results, stream status, system alerts
- Automatic reconnection and error handling

**Vite Proxy** (`vite.config.ts`):
- Development proxy configuration for seamless local development
- Routes `/api/*` and `/socket.io/*` to backend server

### Backend Configuration

**CORS Setup** (`controller.py`):
```python
allowed_origins = [
    "http://localhost:3000", 
    "http://localhost:5173", 
    "http://127.0.0.1:3000", 
    "http://127.0.0.1:5173",
    "https://neural-control-hub-frontend.onrender.com",
    "https://*.onrender.com"
]

CORS(app, origins=allowed_origins, 
     supports_credentials=True, 
     allow_headers=["Content-Type", "Authorization", "X-Requested-With"])
```

**API Endpoints**:
- `/api/auth/*` - Authentication endpoints
- `/api/agents/*` - Agent management
- `/api/system/*` - System information
- `/api/activity` - Activity feed
- `/api/settings/*` - Configuration management

**WebSocket Events**:
- `operator_connect` - Frontend operator connection
- `agent_list_update` - Real-time agent status updates
- `command_result` - Command execution results
- `stream_status_update` - Streaming status changes
- `activity_update` - System activity notifications

### Client Configuration

**Connection Setup** (`client.py`):
```python
FIXED_SERVER_URL = os.environ.get('FIXED_SERVER_URL', 'http://localhost:8080')
```

**Environment Variables** (`client.env`):
- `FIXED_SERVER_URL` - Controller server URL (default: `http://localhost:8080`)
- `RUN_MODE` - Client mode: `agent` (connects to controller)
- `SILENT_MODE` - Enable/disable console output
- `DEBUG_MODE` - Enable debug logging

**Client Features**:
- Real-time communication via Socket.IO
- Screen/audio/camera streaming
- File transfer capabilities
- Command execution
- System monitoring
- Anti-detection mechanisms

## Development Setup

### Quick Start

1. **Start Complete Development Environment**:
   ```bash
   ./start-dev.sh
   ```
   This script will:
   - Install Python dependencies
   - Install Node.js dependencies
   - Start backend server on port 8080
   - Start frontend development server on port 3000
   - Start agent client connected to controller

2. **Manual Setup**:
   ```bash
   # Terminal 1 - Backend
   python3 controller.py
   
   # Terminal 2 - Frontend
   cd "agent-controller ui"
   npm install
   npm run dev
   
   # Terminal 3 - Agent Client
   export $(cat client.env | grep -v '^#' | xargs)
   python3 client.py --mode agent --no-ssl
   ```

### Testing Connection

Run the connection test script:
```bash
python3 test-connection.py
```

This will test:
- Backend API endpoints
- CORS configuration
- Client connection capability
- Complete system connectivity

## Production Deployment

### Environment Configuration

**Backend**:
- Set `HOST` and `PORT` environment variables
- Configure `SECRET_KEY` for session management
- Set `ADMIN_PASSWORD` for authentication

**Frontend**:
- Update `.env.production` with production URLs
- Build with `npm run build`
- Serve static files or deploy to CDN

### Deployment Checklist

- [ ] Backend server running and accessible
- [ ] CORS origins configured for production domains
- [ ] SSL certificates configured (for HTTPS)
- [ ] Environment variables set correctly
- [ ] Frontend built and deployed
- [ ] WebSocket connections working
- [ ] API endpoints responding correctly

## Troubleshooting

### Common Issues

1. **CORS Errors**:
   - Check `allowed_origins` in `controller.py`
   - Verify frontend URL is included in CORS configuration
   - Ensure `supports_credentials=True` for authenticated requests

2. **Connection Refused**:
   - Verify backend server is running on correct port
   - Check firewall settings
   - Ensure no port conflicts

3. **WebSocket Connection Issues**:
   - Check Socket.IO configuration
   - Verify WebSocket transport is enabled
   - Check for proxy/firewall WebSocket blocking

4. **API Endpoint Not Found**:
   - Verify route definitions in `controller.py`
   - Check URL paths match exactly
   - Ensure HTTP methods match (GET/POST)

### Debug Mode

Enable debug logging:
```bash
# Frontend
export VITE_LOG_LEVEL=debug

# Backend
export FLASK_DEBUG=1
```

## Security Considerations

- Use HTTPS in production
- Implement proper authentication
- Validate all API inputs
- Use secure session management
- Regular security updates
- Monitor for suspicious activity

## API Documentation

The backend provides comprehensive API endpoints documented in `controller.py`. Key endpoints include:

- **Authentication**: `/api/auth/login`, `/api/auth/logout`, `/api/auth/status`
- **Agents**: `/api/agents`, `/api/agents/{id}`, `/api/agents/{id}/execute`
- **Streaming**: `/api/agents/{id}/stream/{type}/start`, `/api/agents/{id}/stream/{type}/stop`
- **Files**: `/api/agents/{id}/files`, `/api/agents/{id}/files/upload`, `/api/agents/{id}/files/download`
- **System**: `/api/system/stats`, `/api/activity`, `/api/settings`

All endpoints return JSON responses with consistent error handling and status codes.