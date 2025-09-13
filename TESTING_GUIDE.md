# Neural Control Hub Testing Guide

This guide shows you how to test the complete system: Frontend UI ↔ Controller ↔ Client Agent.

## Quick Testing Steps

### 1. Verify Setup First
```bash
./verify-setup.sh
```
This checks if all required files and dependencies are in place.

### 2. Start the Complete System
```bash
./start-dev.sh
```
This will start all three components:
- Backend server (controller.py) on port 8080
- Frontend UI on port 3000  
- Agent client connecting to controller

### 3. Test Connections
```bash
python3 test-connection.py
```
This tests API endpoints, CORS, and client connectivity.

## Detailed Testing Process

### Step 1: Environment Check
```bash
# Check if all required files exist
ls -la controller.py client.py "agent-controller ui/package.json"

# Check Python dependencies
python3 -c "import flask, flask_cors, flask_socketio; print('✅ Python deps OK')"

# Check Node.js dependencies
cd "agent-controller ui" && npm list --depth=0
```

### Step 2: Manual Component Testing

#### Test Backend Only
```bash
# Terminal 1 - Start controller
python3 controller.py

# Terminal 2 - Test API endpoints
curl http://localhost:8080/api/auth/status
curl http://localhost:8080/api/system/stats
curl http://localhost:8080/api/agents
```

#### Test Frontend Only
```bash
# Terminal 1 - Start controller (if not running)
python3 controller.py

# Terminal 2 - Start frontend
cd "agent-controller ui"
npm run dev

# Open browser: http://localhost:3000
# Should show login page
```

#### Test Client Only
```bash
# Terminal 1 - Start controller (if not running)
python3 controller.py

# Terminal 2 - Start client
export $(cat client.env | grep -v '^#' | xargs)
python3 client.py --mode agent --no-ssl

# Should see connection messages
```

### Step 3: Full System Testing

#### Start All Components
```bash
./start-dev.sh
```

#### Expected Output:
```
🚀 Starting Neural Control Hub Development Environment
==================================================
📦 Installing Python dependencies...
📦 Installing Node.js dependencies...
🔧 Starting Backend Server (Port 8080)...
🎨 Starting Frontend Development Server (Port 3000)...
🤖 Starting Agent Client...

✅ Development Environment Started!
==================================
🌐 Backend API: http://localhost:8080
🎨 Frontend UI: http://localhost:3000
🤖 Agent Client: Connected to controller
```

### Step 4: Browser Testing

1. **Open Frontend**: http://localhost:3000
2. **Login**: Use default password (check controller.py for ADMIN_PASSWORD)
3. **Check Agent**: Should see the client agent in the agents list
4. **Test Features**:
   - View agent status
   - Send commands
   - Monitor system stats
   - Check activity feed

### Step 5: API Testing

```bash
# Test authentication
curl -X POST http://localhost:8080/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"password": "q"}'

# Test agent list (after login)
curl http://localhost:8080/api/agents \
  -H "Cookie: session=your_session_cookie"

# Test system stats
curl http://localhost:8080/api/system/stats
```

## Troubleshooting Tests

### If Backend Won't Start
```bash
# Check port availability
netstat -tuln | grep :8080

# Check Python dependencies
pip3 install -r requirements.txt

# Check for errors
python3 controller.py --help
```

### If Frontend Won't Start
```bash
# Check Node.js
node --version
npm --version

# Install dependencies
cd "agent-controller ui"
npm install

# Check for errors
npm run dev
```

### If Client Won't Connect
```bash
# Check environment
cat client.env

# Test connection manually
python3 -c "
import requests
try:
    response = requests.get('http://localhost:8080', timeout=5)
    print(f'✅ Controller reachable: HTTP {response.status_code}')
except Exception as e:
    print(f'❌ Controller not reachable: {e}')
"

# Check client logs
python3 client.py --mode agent --no-ssl
```

## Expected Test Results

### ✅ Successful Test Results:

1. **Backend API**: All endpoints return 200 OK
2. **Frontend**: Loads at http://localhost:3000 with login page
3. **Client**: Connects and shows "Connected to server successfully!"
4. **Browser**: Can login and see agent in the interface
5. **Real-time**: Agent status updates in frontend

### ❌ Common Issues:

1. **Port conflicts**: Change ports in configuration
2. **Missing dependencies**: Run install commands
3. **CORS errors**: Check allowed origins in controller.py
4. **Client connection fails**: Verify controller is running
5. **Frontend can't reach backend**: Check proxy configuration

## Advanced Testing

### Load Testing
```bash
# Test multiple clients
for i in {1..5}; do
  python3 client.py --mode agent --no-ssl &
done
```

### Network Testing
```bash
# Test from different machine
curl http://YOUR_IP:8080/api/system/stats
```

### Performance Testing
```bash
# Monitor system resources
htop
# or
top
```

## Test Checklist

- [ ] Backend starts without errors
- [ ] Frontend loads in browser
- [ ] Client connects to controller
- [ ] Can login to frontend
- [ ] Agent appears in frontend
- [ ] Commands can be sent
- [ ] Real-time updates work
- [ ] No console errors
- [ ] All API endpoints respond
- [ ] WebSocket connections stable

## Getting Help

If tests fail:
1. Check the troubleshooting section above
2. Look at console output for error messages
3. Verify all dependencies are installed
4. Check port availability
5. Review configuration files

The system should work end-to-end once all components are properly configured and running!