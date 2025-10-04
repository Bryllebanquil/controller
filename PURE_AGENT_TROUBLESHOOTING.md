# Pure Agent Troubleshooting - Not Appearing in Dashboard

## 🔍 Problem

You're running `pure_agent.py` but it's **not appearing** in the controller dashboard at:
```
https://agent-controller-backend.onrender.com/dashboard
```

---

## ✅ Solution - Use Debug Version

I've created **`pure_agent_debug.py`** that shows ALL Socket.IO events.

### Step 1: Run Debug Version

```bash
python pure_agent_debug.py
```

### Step 2: Check Output

You should see:

```
======================================================================
PURE AGENT - DEBUG MODE
======================================================================
Agent ID: abc12345-6789-...
Server: https://agent-controller-backend.onrender.com
======================================================================

[INFO] Starting Pure Agent (DEBUG MODE)
[INFO] All Socket.IO events will be logged

[INFO] 🔌 Connecting to https://agent-controller-backend.onrender.com...
[INFO] 🎉 CONNECTED TO CONTROLLER!
[INFO] Socket ID: xyz123...
[INFO] 📤 SENDING agent_connect event...
[INFO] Data: {...}
[INFO] ✅ agent_connect event sent!
[INFO] 📤 SENDING agent_register event...
[INFO] ✅ agent_register event sent!
[INFO] ✅ Connection established!
[INFO] Waiting for commands...

[INFO] 💓 Sending heartbeat...
[INFO] ✅ Heartbeat sent
```

### Step 3: Look for Events

Check if you see these events:

```
✅ GOOD - Should See:
[INFO] 🎉 CONNECTED TO CONTROLLER!
[INFO] 📤 SENDING agent_connect event...
[INFO] ✅ agent_connect event sent!
[INFO] 📥 EVENT RECEIVED: 'agent_registered'
[INFO] 📥 EVENT RECEIVED: 'agent_list_update'

❌ BAD - If You See:
[ERROR] Connection error
[ERROR] Authentication failed
[ERROR] Connection refused
```

---

## 🐛 Common Issues

### Issue 1: Connection Fails

**Symptoms:**
```
❌ CONNECTION ERROR: ...
Connection refused
```

**Solutions:**

**A. Check if Render controller is running:**
- Visit: https://agent-controller-backend.onrender.com
- Should show login page or dashboard
- If it shows error, controller is down

**B. Try local controller:**
Edit `pure_agent_debug.py` line 17:
```python
SERVER_URL = "http://localhost:5000"
```

**C. Check internet connection:**
```bash
ping agent-controller-backend.onrender.com
```

---

### Issue 2: Connects but Not Registered

**Symptoms:**
```
✅ CONNECTED TO CONTROLLER!
✅ agent_connect event sent!
(no agent_registered confirmation)
```

**Possible causes:**

**A. Wrong event format:**
- Controller might expect different data structure
- Check debug logs for errors

**B. Controller not accepting connection:**
- Controller might require authentication
- Check controller logs on Render

**C. Agent ID conflict:**
- Try generating new ID (restart agent)

---

### Issue 3: No Events Received

**Symptoms:**
```
✅ agent_connect event sent!
(never receives any events back)
```

**Solutions:**

**A. Check Socket.IO transport:**
```python
# In pure_agent_debug.py, check connection:
sio.connect(SERVER_URL, transports=['websocket'])  # Try websocket only
# or
sio.connect(SERVER_URL, transports=['polling'])    # Try polling only
```

**B. Check firewall/proxy:**
- WebSocket might be blocked
- Try different network

---

### Issue 4: Dashboard Shows Old Agents Only

**Symptoms:**
- Dashboard shows client.py agents
- But not pure_agent.py

**Possible causes:**

**A. Different registration format:**
- Check what dashboard expects
- Compare with client.py registration

**B. Dashboard filtering:**
- Dashboard might filter by capability
- Check if 'commands' capability is enough

---

## 🔧 Fixes Applied

### Fix 1: Correct Registration Event

Updated to use `agent_connect` (what controller.py expects):

```python
sio.emit('agent_connect', {
    'agent_id': AGENT_ID,
    'name': f'Pure-Agent-{hostname}',
    'platform': f'{os} {version}',
    'capabilities': ['commands', 'system_info'],
    'cpu_usage': cpu,
    'memory_usage': memory,
    # ... more fields
})
```

### Fix 2: Added Heartbeat

```python
sio.emit('agent_heartbeat', {
    'agent_id': AGENT_ID,
    'timestamp': time.time()
})

sio.emit('ping', {
    'agent_id': AGENT_ID,
    'uptime': uptime
})
```

### Fix 3: Added Event Listeners

```python
@sio.on('agent_registered')   # Controller confirms registration
@sio.on('agent_list_update')  # Controller sends agent list
@sio.on('command')            # Controller sends command
@sio.on('pong')               # Controller responds to ping
```

---

## 📊 Expected Flow

### Successful Registration:

```
1. Agent connects to controller
   ↓
2. Agent emits 'agent_connect' with data
   ↓
3. Controller receives and stores agent
   ↓
4. Controller emits 'agent_list_update' to all operators
   ↓
5. Dashboard receives update and shows agent
   ↓
6. Agent appears in dashboard!
```

### Debug Output Should Show:

```
[INFO] 🔌 Connecting to https://...
[INFO] 🎉 CONNECTED TO CONTROLLER!
[INFO] Socket ID: xyz123
[INFO] 📤 SENDING agent_connect event...
[INFO] ✅ agent_connect event sent!
[INFO] 📥 EVENT RECEIVED: 'agent_list_update'
[INFO] 📋 Agent list update received - X agents
[INFO] 💓 Sending heartbeat...
[INFO] 📥 EVENT RECEIVED: 'pong'
[INFO] ✅ Received pong from controller - Connection alive
```

---

## 🎯 Testing Steps

### Step 1: Run Debug Agent

```bash
python pure_agent_debug.py
```

### Step 2: Watch Output

Look for:
- ✅ "CONNECTED TO CONTROLLER"
- ✅ "agent_connect event sent"
- ✅ "EVENT RECEIVED: 'agent_list_update'"

### Step 3: Check Dashboard

Open: https://agent-controller-backend.onrender.com/dashboard

Look for your agent in the list.

### Step 4: Send Test Command

If agent appears:
- Click on agent
- Type: `whoami`
- Press Enter
- Should see result in terminal

---

## 📋 Checklist

- [ ] Dependencies installed: `pip install python-socketio psutil websockets requests`
- [ ] Controller is running (visit URL, should load)
- [ ] Debug agent shows "CONNECTED TO CONTROLLER"
- [ ] Debug agent shows "agent_connect event sent"
- [ ] Debug agent receives events back
- [ ] Dashboard refreshed (Ctrl+F5)
- [ ] Agent appears in dashboard agent list

---

## 🔍 Advanced Debugging

### Check Controller Logs (Render):

1. Go to Render dashboard
2. Click on your controller service
3. Click "Logs" tab
4. Look for:
```
Agent abc12345... connected with SID xyz...
Agent registration successful
```

If you DON'T see this, the controller isn't receiving the registration.

### Check Network Traffic:

1. Open browser DevTools (F12)
2. Go to Network tab
3. Filter: WS (WebSocket)
4. Look for WebSocket connection
5. Check messages sent/received

---

## 🎯 If Still Not Working

### Option 1: Match Original Client Registration

Check how `client.py` registers and copy the exact format:

```bash
# Search for agent_connect in client.py
grep -n "emit.*agent_connect" client.py
```

### Option 2: Check Dashboard Code

The dashboard might be filtering agents. Check if it only shows agents with specific capabilities.

### Option 3: Use Local Controller First

Test with local controller.py:

```bash
# Terminal 1:
python controller.py

# Terminal 2:
# Edit pure_agent_debug.py:
SERVER_URL = "http://localhost:5000"

# Run:
python pure_agent_debug.py

# Browser:
http://localhost:5000/dashboard
```

This eliminates network/Render issues.

---

## 📞 Debug Report

After running `pure_agent_debug.py`, report back with:

1. **Connection status:**
   - Did it connect? (Look for "CONNECTED TO CONTROLLER")

2. **Events sent:**
   - Did it send agent_connect? (Look for "agent_connect event sent")

3. **Events received:**
   - Did it receive any events? (Look for "EVENT RECEIVED")

4. **Controller logs (if available):**
   - What does Render logs show?

5. **Dashboard status:**
   - Does dashboard show any agents?
   - Does it show old client.py agents?

---

## 🎉 Expected Success Output

```
======================================================================
PURE AGENT - DEBUG MODE
======================================================================
Agent ID: d487be0a-16f5-4716-a025-afa35e8c56b8
Server: https://agent-controller-backend.onrender.com
======================================================================

[2025-10-03 12:00:00] Starting Pure Agent (DEBUG MODE)
[2025-10-03 12:00:00] All Socket.IO events will be logged

[2025-10-03 12:00:01] 🔌 Connecting to https://...
[2025-10-03 12:00:02] 🎉 CONNECTED TO CONTROLLER!
[2025-10-03 12:00:02] Socket ID: abc123xyz
[2025-10-03 12:00:02] 📤 SENDING agent_connect event...
[2025-10-03 12:00:02] Data: {'agent_id': 'd487be0a...', 'name': 'Pure-Agent-DESKTOP', ...}
[2025-10-03 12:00:02] ✅ agent_connect event sent!
[2025-10-03 12:00:02] 📤 SENDING agent_register event...
[2025-10-03 12:00:02] ✅ agent_register event sent!
[2025-10-03 12:00:02] ✅ Connection established!
[2025-10-03 12:00:02] Waiting for commands...

[2025-10-03 12:00:03] 📥 EVENT RECEIVED: 'agent_list_update' | Data: {...}
[2025-10-03 12:00:03] 📋 Agent list update received - 1 agents

[2025-10-03 12:00:32] 💓 Sending heartbeat...
[2025-10-03 12:00:32] ✅ Heartbeat sent
[2025-10-03 12:00:33] 📥 EVENT RECEIVED: 'pong' | Data: {...}
[2025-10-03 12:00:33] ✅ Received pong from controller - Connection alive
```

---

## 📁 Files to Use

### For Debugging:
1. **`pure_agent_debug.py`** ← Use this to see all events
2. **`CHECK_STATUS.bat`** - Check system status

### For Production:
1. **`pure_agent.py`** ← Use after debugging works

### Documentation:
1. **`PURE_AGENT_TROUBLESHOOTING.md`** ← This file

---

## 🚀 Next Steps

1. **Run debug version:**
   ```bash
   python pure_agent_debug.py
   ```

2. **Copy the output** and send it to me

3. **Check dashboard** - Does agent appear?

4. **Send me:**
   - Debug output (all logs)
   - Controller Render logs (if available)
   - Dashboard screenshot

**This will show us exactly what's happening!** 🔍
