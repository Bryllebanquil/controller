# Fix: Eventlet Import Error

## ❌ Problem Found!

Your agent is **failing to import eventlet** and exiting immediately:

```
[DEBUG] ❌ eventlet import FAILED: No module named 'eventlet.hubs.epolls'
[DEBUG] Installing eventlet: pip install eventlet
```

Then the script exits at line 33 of client.py.

---

## 🔍 Root Cause

**PyInstaller is not bundling eventlet correctly!**

The error `No module named 'eventlet.hubs.epolls'` happens because:
- eventlet has platform-specific modules
- `epolls` is Linux-specific (uses epoll)
- On Windows, eventlet should use different modules
- PyInstaller isn't detecting/bundling all eventlet dependencies

---

## ✅ Solution 1: Add Eventlet to Hidden Imports (RECOMMENDED)

### Step 1: Edit svchost.spec

Add eventlet modules to hidden imports (around line 12-28):

```python
# BEFORE:
hiddenimports = [
    'engineio.async_drivers.threading',
    'dns',
    'dns.resolver',
    'win32timezone',
    'pywintypes',
    'pythoncom',
    'win32api',
    'win32con',
    'win32file',
    'win32gui',
    'win32process',
    'win32security',
    'win32service',
    'win32com.client',
    'comtypes.client',
    'winreg',
    'shutil',
    'threading',
    'time',
]

# AFTER (add eventlet modules):
hiddenimports = [
    'engineio.async_drivers.threading',
    'dns',
    'dns.resolver',
    'win32timezone',
    'pywintypes',
    'pythoncom',
    'win32api',
    'win32con',
    'win32file',
    'win32gui',
    'win32process',
    'win32security',
    'win32service',
    'win32com.client',
    'comtypes.client',
    'winreg',
    'shutil',
    'threading',
    'time',
    # Eventlet modules (CRITICAL!)
    'eventlet',
    'eventlet.hubs',
    'eventlet.hubs.hub',
    'eventlet.hubs.poll',
    'eventlet.hubs.selects',
    'eventlet.greenthread',
    'eventlet.greenpool',
    'eventlet.queue',
    'eventlet.timeout',
    'eventlet.wsgi',
    'eventlet.green',
    'eventlet.green.socket',
    'eventlet.green.threading',
    'eventlet.green.select',
    'eventlet.green.ssl',
]
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

**Should now work!** ✅

---

## ✅ Solution 2: Make Eventlet Optional (FASTER FIX)

If eventlet is not critical for basic agent functionality, make it optional:

### Edit client.py (Lines 27-33)

```python
# BEFORE:
try:
    import eventlet
    debug_print("✅ eventlet imported successfully")
except ImportError as e:
    debug_print(f"❌ eventlet import FAILED: {e}")
    debug_print("Installing eventlet: pip install eventlet")
    sys.exit(1)  # ← EXITS HERE!

# AFTER (make it optional):
try:
    import eventlet
    debug_print("✅ eventlet imported successfully")
    EVENTLET_AVAILABLE = True
except ImportError as e:
    debug_print(f"⚠️ eventlet import FAILED: {e}")
    debug_print("⚠️ Continuing without eventlet (some features may not work)")
    EVENTLET_AVAILABLE = False
    eventlet = None  # Set to None instead of exiting
```

### Also edit the monkey_patch section (Lines 35-45):

```python
# BEFORE:
debug_print("Step 2: Running eventlet.monkey_patch()...")
try:
    # ... monkey patch code ...
    eventlet.monkey_patch()
    debug_print("✅ eventlet.monkey_patch() completed successfully")
except Exception as e:
    debug_print(f"❌ eventlet.monkey_patch() FAILED: {e}")
    sys.exit(1)  # ← EXITS HERE!

# AFTER (make it optional):
if EVENTLET_AVAILABLE:
    debug_print("Step 2: Running eventlet.monkey_patch()...")
    try:
        # ... monkey patch code ...
        eventlet.monkey_patch()
        debug_print("✅ eventlet.monkey_patch() completed successfully")
    except Exception as e:
        debug_print(f"⚠️ eventlet.monkey_patch() FAILED: {e}")
        debug_print("⚠️ Continuing without monkey patching")
else:
    debug_print("Step 2: Skipping eventlet.monkey_patch() (eventlet not available)")
```

### Recompile

```bash
pyinstaller svchost.spec
```

This allows the agent to run without eventlet (though some async features might not work).

---

## ✅ Solution 3: Install Eventlet Before Compiling

Maybe eventlet isn't installed in your Python environment:

```bash
# Install/reinstall eventlet
pip uninstall eventlet -y
pip install eventlet

# Verify it works
python -c "import eventlet; print('OK')"

# Then recompile
pyinstaller svchost.spec
```

---

## 🎯 Recommended Fix (Quickest)

**Use Solution 1 (Add to hidden imports):**

1. **Edit `svchost.spec`** - Add eventlet modules to `hiddenimports` list
2. **Recompile:** `pyinstaller svchost.spec`
3. **Test:** `cd dist && svchost.exe`

This ensures all eventlet dependencies are bundled.

---

## 📊 After Fix - What You Should See

```
[DEBUG] ==============================================================
[DEBUG] PYTHON AGENT STARTUP - UAC PRIVILEGE DEBUGGER ENABLED
[DEBUG] ==============================================================
[DEBUG] Python version: 3.13.6 ...
[DEBUG] Platform: win32
[DEBUG] ==============================================================
[DEBUG] Step 1: Importing eventlet...
[DEBUG] ✅ eventlet imported successfully  ← SHOULD SEE THIS!
[DEBUG] Step 2: Running eventlet.monkey_patch()...
[DEBUG] ✅ eventlet.monkey_patch() completed successfully
[DEBUG] ==============================================================
[DEBUG] EVENTLET SETUP COMPLETE - NOW IMPORTING OTHER MODULES
[DEBUG] ==============================================================
[INFO] Attempting to connect to https://agent-controller-backend.onrender.com...
[OK] Connected to server successfully!  ← THEN THIS!
```

---

## 🔧 Complete Fix Code

**svchost.spec (add to hiddenimports):**

```python
hiddenimports = [
    'engineio.async_drivers.threading',
    'dns',
    'dns.resolver',
    'win32timezone',
    'pywintypes',
    'pythoncom',
    'win32api',
    'win32con',
    'win32file',
    'win32gui',
    'win32process',
    'win32security',
    'win32service',
    'win32com.client',
    'comtypes.client',
    'winreg',
    'shutil',
    'threading',
    'time',
    # ADD THESE FOR EVENTLET:
    'eventlet',
    'eventlet.hubs',
    'eventlet.hubs.hub',
    'eventlet.hubs.poll',
    'eventlet.hubs.selects',
    'eventlet.greenthread',
    'eventlet.greenpool',
    'eventlet.queue',
    'eventlet.timeout',
]
```

**Then:**
```bash
pyinstaller svchost.spec
cd dist
svchost.exe
```

---

## ✅ Success Indicator

After the fix, you should see:
- ✅ `eventlet imported successfully`
- ✅ `eventlet.monkey_patch() completed successfully`
- ✅ Agent continues to connect to controller
- ✅ No more immediate exit!

---

**The problem is PyInstaller not bundling eventlet properly. Add it to hidden imports and it will work!** 🚀
