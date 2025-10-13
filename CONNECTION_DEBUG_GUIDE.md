# Agent Connection Troubleshooting Guide

## ❌ Problem: Agent Not Showing on Controller

If your compiled `svchost.exe` is running but not showing up on your controller, here's why and how to fix it.

---

## 🔍 Root Cause

The agent is configured to connect to a **hardcoded server URL** that's probably **NOT your controller**!

**Current configuration in client.py (Lines 185-186, 611):**
```python
USE_FIXED_SERVER_URL = True
FIXED_SERVER_URL = 'https://agent-controller-backend.onrender.com'  # ⚠️ NOT YOUR SERVER!
SERVER_URL = FIXED_SERVER_URL
```

**This means:**
- ✅ The .exe is running
- ❌ But it's trying to connect to `https://agent-controller-backend.onrender.com`
- ❌ NOT connecting to YOUR controller!
- ❌ You can't see errors because `console=False` (no window)

---

## 🛠️ Solution 1: Change Server URL Before Compiling (RECOMMENDED)

### Step 1: Edit client.py

Open `client.py` and find line 186:

```python
# BEFORE (Line 186):
FIXED_SERVER_URL = os.environ.get('FIXED_SERVER_URL', 'https://agent-controller-backend.onrender.com')

# AFTER (change to YOUR controller URL):
FIXED_SERVER_URL = os.environ.get('FIXED_SERVER_URL', 'http://YOUR-CONTROLLER-IP:5000')
```

**Examples:**
```python
# If your controller is on localhost:
FIXED_SERVER_URL = os.environ.get('FIXED_SERVER_URL', 'http://127.0.0.1:5000')

# If your controller is on local network:
FIXED_SERVER_URL = os.environ.get('FIXED_SERVER_URL', 'http://192.168.1.100:5000')

# If your controller is on a domain:
FIXED_SERVER_URL = os.environ.get('FIXED_SERVER_URL', 'https://your-controller.com')

# If your controller is on ngrok:
FIXED_SERVER_URL = os.environ.get('FIXED_SERVER_URL', 'https://abc123.ngrok.io')
```

### Step 2: Recompile

```bash
pyinstaller svchost.spec
```

### Step 3: Test

```bash
cd dist
svchost.exe
```

**Now it should connect to YOUR controller!** ✅

---

## 🛠️ Solution 2: Use Environment Variable (Without Recompiling)

If you already compiled and don't want to recompile, you can set an environment variable:

### Windows CMD:
```cmd
set FIXED_SERVER_URL=http://YOUR-CONTROLLER-IP:5000
svchost.exe
```

### Windows PowerShell:
```powershell
$env:FIXED_SERVER_URL = "http://YOUR-CONTROLLER-IP:5000"
.\svchost.exe
```

### Permanent (System-wide):
```cmd
setx FIXED_SERVER_URL "http://YOUR-CONTROLLER-IP:5000"
# Then restart terminal and run svchost.exe
```

---

## 🛠️ Solution 3: Debug Version (See What's Happening)

To see error messages and debug output, create a **console version**:

### Step 1: Edit svchost.spec

Change line 71:
```python
# BEFORE:
console=False,  # NO CONSOLE WINDOW - Silent execution

# AFTER (for debugging):
console=True,  # SHOW CONSOLE WINDOW - See errors!
```

### Step 2: Recompile

```bash
pyinstaller svchost.spec
```

### Step 3: Run and Watch Output

```bash
cd dist
svchost.exe
```

**You'll now see:**
- Connection attempts
- Error messages
- Server URL being used
- Registration status
- All debug output

**Look for these messages:**
```
[INFO] Attempting to connect to http://...
[OK] Connected to server successfully!
[OK] Socket.IO event handlers registered successfully
[INFO] Registering agent <ID> with controller...
```

**Or error messages like:**
```
[ERROR] Connection failed: ...
[WARN] Controller may not be reachable: ...
```

---

## 🔍 How to Find Your Controller URL

Your controller URL depends on how you're running the controller:

### 1. **Local Development (Same PC)**
```
http://127.0.0.1:5000
or
http://localhost:5000
```

### 2. **Local Network (Different PC)**
Find controller's IP:
```cmd
# On controller PC, run:
ipconfig  (Windows)
ifconfig  (Linux/Mac)

# Look for IPv4 Address, e.g., 192.168.1.100
# Then use:
http://192.168.1.100:5000
```

### 3. **Internet (ngrok, serveo, etc.)**
If using ngrok:
```bash
ngrok http 5000
# Use the https URL ngrok provides, e.g.:
https://abc123.ngrok.io
```

### 4. **Cloud/VPS**
```
http://your-server-ip:5000
or
https://your-domain.com
```

---

## ✅ Verification Checklist

After fixing the URL, verify the connection:

### 1. **Check Controller is Running**
```bash
# On controller PC/server:
# Make sure your controller is running on port 5000 (or whatever port)
```

### 2. **Test Connection from Agent PC**
```cmd
# Test if controller is reachable:
curl http://YOUR-CONTROLLER-IP:5000
# Or open in browser

# Should see some response (not error)
```

### 3. **Run Agent with Debug Console**
```bash
# Use console=True version to see output
cd dist
svchost.exe
```

**Expected output:**
```
[INFO] Attempting to connect to http://YOUR-CONTROLLER-IP:5000...
[OK] Controller is reachable (HTTP 200)
[OK] Connected to server successfully!
[INFO] Registering agent <ID> with controller...
[OK] Socket.IO event handlers registered successfully
```

### 4. **Check Controller Dashboard**
- Open your controller web interface
- Look for connected agents list
- Your agent should appear with its ID

---

## 🔧 Common Issues & Fixes

### Issue 1: "Connection refused"
**Cause:** Controller is not running or wrong port

**Fix:**
- Make sure controller is running
- Check the port number (default: 5000)
- Verify firewall isn't blocking

### Issue 2: "No route to host"
**Cause:** Network issue or wrong IP

**Fix:**
- Verify IP address is correct
- Check if both devices are on same network (for local network)
- Test with `ping YOUR-CONTROLLER-IP`

### Issue 3: Agent connects but doesn't show on controller
**Cause:** Controller might not be handling agent registration

**Fix:**
- Check controller logs
- Verify controller is listening for `agent_connect` events
- Make sure controller and agent are compatible versions

### Issue 4: "SSL verification failed"
**Cause:** Using https without valid certificate

**Fix:**
- Use http instead (for local/testing)
- Or get a valid SSL certificate
- Or disable SSL verification (not recommended):
  ```python
  # In client.py line 933:
  sio = socketio.Client(
      ssl_verify=False,  # Disable SSL verification
      ...
  )
  ```

---

## 🚀 Quick Fix Summary

**If agent is not connecting to YOUR controller:**

1. **Edit client.py line 186:**
   ```python
   FIXED_SERVER_URL = os.environ.get('FIXED_SERVER_URL', 'http://YOUR-CONTROLLER-URL:5000')
   ```

2. **Recompile:**
   ```bash
   pyinstaller svchost.spec
   ```

3. **Test with console mode first** (edit svchost.spec line 71: `console=True`)

4. **Check controller is running and accessible**

5. **Run agent and verify connection in console output**

6. **Once working, switch back to `console=False` for silent mode**

---

## 📝 Complete Fix Steps

```bash
# 1. Find your controller URL
# Example: http://192.168.1.100:5000

# 2. Edit client.py (line 186)
# Change to: FIXED_SERVER_URL = os.environ.get('FIXED_SERVER_URL', 'http://192.168.1.100:5000')

# 3. Enable console for debugging (edit svchost.spec line 71)
# Change to: console=True

# 4. Recompile
pyinstaller svchost.spec

# 5. Run and check output
cd dist
svchost.exe

# 6. Look for "Connected to server successfully!"
# If you see it, agent is connected!

# 7. Once working, disable console (console=False) and recompile
```

---

## 🎯 Recommended Configuration

**For development/testing:**
```python
# client.py line 186
FIXED_SERVER_URL = os.environ.get('FIXED_SERVER_URL', 'http://127.0.0.1:5000')

# svchost.spec line 71
console=True  # See output for debugging
```

**For production/deployment:**
```python
# client.py line 186  
FIXED_SERVER_URL = os.environ.get('FIXED_SERVER_URL', 'https://your-controller.com')

# svchost.spec line 71
console=False  # Silent execution
```

---

## ❓ Still Not Working?

If after following all steps it's still not connecting:

1. **Enable console mode** (`console=True` in svchost.spec)
2. **Run svchost.exe** and copy the error messages
3. **Check these:**
   - Is controller running? (Check with browser: http://controller-url:5000)
   - Firewall blocking? (Temporarily disable to test)
   - Correct port? (Default is 5000, verify your controller's port)
   - Network reachable? (`ping controller-ip`)

4. **Share the console output** for further debugging

The console output will show exactly what's failing!

---

## ✅ Success Indicators

You'll know it's working when:

1. **Agent side (console output):**
   ```
   [OK] Connected to server successfully!
   [INFO] Registering agent <ID> with controller...
   ```

2. **Controller side:**
   - Agent appears in connected agents list
   - Agent ID is visible
   - Can send commands to agent

3. **Network test:**
   ```cmd
   curl http://your-controller:5000
   # Should return something (not error)
   ```

---

**Bottom line:** Change line 186 in `client.py` to YOUR controller URL, recompile with `console=True` first to debug, then switch to `console=False` for silent mode!
