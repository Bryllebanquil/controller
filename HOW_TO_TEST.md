# How to Test the Neural Control Hub System

## ✅ Quick Verification (What We Just Did)

The basic system test passed! Here's what we verified:
- ✅ Backend server starts successfully
- ✅ API endpoints are responding
- ✅ Frontend builds without errors
- ✅ Client dependencies are available

## 🚀 Full System Testing

### Method 1: Automated Test (Recommended)

```bash
# Run the complete system test
./start-dev.sh
```

This will start all three components:
1. **Backend server** (controller.py) on port 8080
2. **Frontend UI** (React app) on port 3000
3. **Agent client** (client.py) connecting to controller

### Method 2: Manual Step-by-Step Testing

#### Step 1: Start Backend Server
```bash
# Terminal 1
python3 controller.py
```
Expected output:
```
Starting Neural Control Hub with Socket.IO + WebRTC support...
Admin password: q
Server will be available at: http://0.0.0.0:8080
* Running on http://127.0.0.1:8080
```

#### Step 2: Start Frontend
```bash
# Terminal 2
cd "agent-controller ui"
npm run dev
```
Expected output:
```
  VITE v6.3.5  ready in 1234 ms

  ➜  Local:   http://localhost:3000/
  ➜  Network: use --host to expose
```

#### Step 3: Start Agent Client
```bash
# Terminal 3
export $(cat client.env | grep -v '^#' | xargs)
python3 client.py --mode agent --no-ssl
```
Expected output:
```
Attempting to connect to http://localhost:8080...
[OK] Connected to server successfully!
```

## 🌐 Browser Testing

### 1. Open the Frontend
- Go to: http://localhost:3000
- You should see the Neural Control Hub login page

### 2. Login
- Default password: `q` (as shown in backend startup)
- Click "Login" button

### 3. Verify Dashboard
After login, you should see:
- ✅ System overview with stats
- ✅ Agent list (should show your client agent)
- ✅ Navigation tabs (Overview, Agents, Streaming, etc.)

### 4. Test Agent Interaction
- Click on your agent in the agents list
- Try sending a command (e.g., `whoami` or `pwd`)
- Check if the command executes and returns output

## 🔧 API Testing

### Test Authentication
```bash
curl -X POST http://localhost:8080/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"password": "q"}'
```

### Test Agent List
```bash
curl http://localhost:8080/api/agents \
  -H "Cookie: session=your_session_cookie"
```

### Test System Stats
```bash
curl http://localhost:8080/api/system/stats
```

## 🐛 Troubleshooting

### If Backend Won't Start
```bash
# Check if port 8080 is in use
netstat -tuln | grep :8080

# Kill any process using port 8080
sudo lsof -ti:8080 | xargs kill -9
```

### If Frontend Won't Load
```bash
# Check if port 3000 is available
netstat -tuln | grep :3000

# Reinstall dependencies
cd "agent-controller ui"
rm -rf node_modules package-lock.json
npm install
```

### If Client Won't Connect
```bash
# Check environment variables
cat client.env

# Test connection manually
curl http://localhost:8080
```

## 📊 Expected Test Results

### ✅ Successful Test Indicators:

1. **Backend Console**:
   ```
   Client connected: [session_id]
   Agent connected: [agent_id]
   ```

2. **Frontend Browser**:
   - Login page loads
   - Dashboard shows system stats
   - Agent appears in agents list
   - Commands can be sent and executed

3. **Client Console**:
   ```
   [OK] Connected to server successfully!
   Received command: [command]
   Command executed successfully
   ```

### ❌ Common Issues:

1. **"Connection refused"** → Backend not running
2. **"CORS error"** → Frontend/backend URL mismatch
3. **"Agent not visible"** → Client not connected
4. **"Command timeout"** → Network/performance issue

## 🎯 Test Checklist

- [ ] Backend server starts without errors
- [ ] Frontend loads at http://localhost:3000
- [ ] Can login with password `q`
- [ ] Dashboard shows system statistics
- [ ] Agent client connects successfully
- [ ] Agent appears in the agents list
- [ ] Can select and interact with agent
- [ ] Commands can be sent and executed
- [ ] Real-time updates work (status changes)
- [ ] No console errors in browser or terminals

## 🚀 Next Steps After Testing

Once everything is working:

1. **Explore Features**:
   - Try different commands
   - Test file operations
   - Check streaming capabilities
   - Monitor system performance

2. **Customize Configuration**:
   - Update passwords in `controller.py`
   - Modify client settings in `client.env`
   - Adjust frontend settings in `.env` files

3. **Deploy to Production**:
   - Update production environment variables
   - Configure SSL certificates
   - Set up proper hosting

## 📞 Getting Help

If tests fail:
1. Check the troubleshooting section above
2. Look at console output for specific error messages
3. Verify all dependencies are installed
4. Ensure ports are available
5. Check configuration files for typos

The system should work end-to-end once all components are properly configured and running!