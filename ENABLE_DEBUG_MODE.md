# Quick Guide: Enable Debug Mode to See Errors

## Problem
Your agent is running but you can't see what's happening because `console=False` (no window).

---

## Solution: Enable Console Mode

### Step 1: Edit svchost.spec

Open `svchost.spec` and find **line 71**:

```python
# BEFORE (Line 71):
console=False,  # NO CONSOLE WINDOW - Silent execution

# AFTER (for debugging):
console=True,  # SHOW CONSOLE WINDOW - See all messages!
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

**Now you'll see:**
- Connection attempts
- Success/error messages
- Registration status
- Everything the agent is doing!

---

## What You'll See

### If Working Correctly:
```
[INFO] Attempting to connect to https://agent-controller-backend.onrender.com...
[OK] Controller is reachable (HTTP 200)
[OK] Connected to server successfully!
[INFO] Registering agent <ID> with controller...
[OK] Socket.IO event handlers registered successfully
```
**→ Agent connected! Check controller dashboard.**

### If SSL Error:
```
[ERROR] SSL: CERTIFICATE_VERIFY_FAILED
[ERROR] Failed to connect to server
```
**→ Fix: Disable SSL verification (see below)**

### If Connection Timeout:
```
[INFO] Attempting to connect to https://agent-controller-backend.onrender.com...
[ERROR] Connection timeout
```
**→ Fix: Controller might be sleeping (Render free tier) - wake it up first!**

### If Connection Refused:
```
[ERROR] Connection refused
[ERROR] Failed to connect to server
```
**→ Fix: Controller might be down - check Render dashboard**

---

## Common Fixes

### Fix 1: Disable SSL Verification (if SSL error)

Edit `client.py` around **line 933**:

```python
# BEFORE:
sio = socketio.Client(
    ssl_verify=True,
    engineio_logger=False,
    logger=False
)

# AFTER:
sio = socketio.Client(
    ssl_verify=False,  # Disable SSL verification
    engineio_logger=False,
    logger=False
)
```

Then recompile: `pyinstaller svchost.spec`

### Fix 2: Wake Up Controller (Render Free Tier Sleeps!)

**Render.com free tier apps sleep after 15 minutes of inactivity.**

Before running agent:
1. Open in browser: `https://agent-controller-backend.onrender.com`
2. Wait 30-60 seconds for it to wake up
3. THEN run your agent

---

## Quick Test

```bash
# 1. Enable console
# Edit svchost.spec line 71: console=True

# 2. Recompile
pyinstaller svchost.spec

# 3. Wake controller
# Open in browser: https://agent-controller-backend.onrender.com
# Wait until it loads

# 4. Run agent and watch output
cd dist
svchost.exe

# 5. Look for "[OK] Connected to server successfully!"
```

---

## After It Works

Once you confirm it's working:

1. **Disable console for silent mode:**
   - Edit `svchost.spec` line 71: `console=False`
   - Recompile: `pyinstaller svchost.spec`

2. **Your agent will run silently** ✅

---

## Share Console Output

If it's still not working, **run with console=True** and share:
- What messages you see
- Any error messages
- Last few lines of output

This will tell us exactly what's wrong!
