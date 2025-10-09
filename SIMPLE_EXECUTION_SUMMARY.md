# Simple Summary: What Happens When You Run svc.exe

## 🎯 Quick Answer

When you run `svc.exe` (compiled client.py), it:

1. **Tries to gain admin privileges** (using UAC bypass - no password needed)
2. **Disables UAC permanently** (so no more admin password prompts)
3. **Disables Windows Defender** (turns off antivirus)
4. **Installs itself** to run on every boot
5. **Connects to remote server** and waits for commands
6. **Hides itself** and pretends to be a Windows system service

**Bottom line:** Full remote access to your computer with persistence.

---

## 📊 Simple Visual Flow

```
YOU RUN svc.exe
       ↓
  [Startup Check]
       ↓
  Is Admin? ──No──→ [UAC BYPASS] ──→ Try Fodhelper
       ↓                   ↓            Try EventVwr
      Yes                  ↓            Try AppInfo (VBS) ← NEW
       ↓                   ↓            Try Others...
       ↓              Success? ──Yes──→ [ELEVATE]
       ↓                   ↓
       ↓                   No
       ↓                   ↓
       └───────────────────┘
                ↓
        [System Modifications]
                ↓
        Disable UAC ────────→ Registry: EnableLUA = 0
        Disable Defender ───→ Registry: DisableAntiSpyware = 1
        Disable Notifications → Registry: ToastEnabled = 0
                ↓
        [Install Persistence]
                ↓
        Copy to AppData ────→ C:\Users\...\svchost32.exe
        Registry Run Key ───→ HKCU\...\Run\svchost32
        Startup Folder ─────→ SystemService.bat
        Scheduled Task ─────→ Runs every hour
                ↓
        [Network Connection]
                ↓
        Connect to Server ──→ agent-controller-backend.onrender.com
        Register Agent ─────→ Send hostname, IP, capabilities
                ↓
        [Start Monitoring]
                ↓
        Keylogger Thread ───→ Log keystrokes
        Screen Thread ──────→ Capture screenshots
        Clipboard Thread ───→ Monitor clipboard
        Telemetry Thread ───→ Send CPU/RAM stats
                ↓
        [Wait for Commands]
                ↓
        Server can now:
        • Execute any command
        • View your screen
        • Access files
        • Control your PC
```

---

## 🔴 What Gets Changed on Your PC

### 1. **UAC (User Account Control)**
- **Before:** Admin password required for programs
- **After:** NO password required (UAC completely disabled)
- **How:** Registry key `EnableLUA = 0`

### 2. **Windows Defender**
- **Before:** Antivirus protecting your system
- **After:** Antivirus DISABLED
- **How:** Registry changes + service disabled

### 3. **File System**
- **New file:** `C:\Users\<you>\AppData\Local\Microsoft\Windows\svchost32.exe`
- **New file:** `%APPDATA%\...\Startup\SystemService.bat`
- **Attributes:** Hidden + System (won't show in normal file browser)

### 4. **Registry**
- **Added:** `HKCU\Software\Microsoft\Windows\CurrentVersion\Run\svchost32`
- **Modified:** `HKLM\...\Policies\System\EnableLUA = 0`
- **Modified:** Various Defender keys

### 5. **Network**
- **New connection:** Persistent to `agent-controller-backend.onrender.com`
- **Always connected** (like always-on remote desktop)

---

## ⏱️ Timeline (What Happens When)

| Time | What Happens | You See |
|------|-------------|---------|
| **0-5 sec** | Startup checks | Console: "Python Agent Starting..." |
| **5-10 sec** | UAC bypass attempts | Console: "Attempting UAC bypass..." |
| **10-15 sec** | System modifications | Console: "UAC DISABLED SUCCESSFULLY!" |
| **15-20 sec** | Defender disable | Console: "Windows Defender disabled" |
| **20-25 sec** | Persistence install | Files copied to AppData |
| **25-30 sec** | Server connection | Console: "Connected to server" |
| **30+ sec** | Active monitoring | Nothing visible (runs in background) |

---

## 🎭 How It Hides

### Disguise Techniques:
1. **Process name:** `svchost32.exe` (looks like Windows system file)
2. **Fake service name:** "System Update Service" or "Windows Security Service"
3. **Hidden files:** Uses `attrib +h +s` to hide
4. **No console window:** Runs silently in background
5. **VBS execution:** Uses Windows Script Host (looks normal)

### What Task Manager Shows:
```
Name: svchost32.exe
Location: C:\Users\John\AppData\Local\Microsoft\Windows\
User: John (or SYSTEM)
CPU: 0-5%
```

**Looks like:** Legitimate Windows service  
**Actually is:** Remote access tool

---

## 🌐 What the Server Can Do

Once connected, the remote server can:

### Basic Commands:
- ✅ Run any CMD/PowerShell command
- ✅ Upload/download files
- ✅ Browse all your files
- ✅ Delete/modify files

### Monitoring:
- ✅ See your screen in real-time
- ✅ Access your webcam
- ✅ Record your microphone
- ✅ Log every keystroke
- ✅ See what you copy/paste

### Control:
- ✅ Shutdown/restart your PC
- ✅ Lock your screen
- ✅ Run programs
- ✅ Modify system settings

**Basically:** Complete remote control of your computer.

---

## 🔍 How to Detect It

### Check File System:
```cmd
dir /a %LOCALAPPDATA%\Microsoft\Windows\svchost32.exe
dir /a %APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\SystemService.bat
```

### Check Registry:
```cmd
reg query HKCU\Software\Microsoft\Windows\CurrentVersion\Run /v svchost32
reg query HKLM\SOFTWARE\Policies\Microsoft\Windows Defender /v DisableAntiSpyware
reg query HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System /v EnableLUA
```

### Check Network:
```cmd
netstat -ano | findstr "443"
```
Look for: `agent-controller-backend.onrender.com`

### Check Processes:
```cmd
tasklist | findstr "svchost32"
```
If found in AppData (not System32) → It's the agent

---

## 🛡️ What to Do If You Find It

### Immediate Actions:
1. **Disconnect network** (unplug ethernet/disable WiFi)
2. **Kill the process** (Task Manager → svchost32.exe → End Task)
3. **Delete the files**:
   - `%LOCALAPPDATA%\Microsoft\Windows\svchost32.exe`
   - `%APPDATA%\...\Startup\SystemService.bat`
4. **Remove registry keys**:
   - `HKCU\...\Run\svchost32`
5. **Re-enable UAC**:
   - `reg add "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System" /v EnableLUA /t REG_DWORD /d 1 /f`
6. **Re-enable Defender**
7. **Restart your PC**

### Full Cleanup:
1. Run antivirus scan (after re-enabling Defender)
2. Check scheduled tasks for "SystemService"
3. Change all passwords (from a different device)
4. Consider full system reinstall if used for sensitive work

---

## ❓ FAQ

**Q: Will I see a UAC prompt?**  
A: NO - it uses bypass techniques that don't show prompts

**Q: Will Defender detect it?**  
A: Unlikely - it tries to disable Defender immediately

**Q: Can I just delete the .exe?**  
A: No - it has multiple persistence methods and will restore itself

**Q: Will it work without admin?**  
A: Partially - most features work, but UAC disable and Defender disable need admin

**Q: Does it work on Windows 11?**  
A: Some UAC bypasses are patched in Windows 11, but many still work

**Q: Can it survive a restart?**  
A: YES - that's the whole point of persistence

**Q: Will firewall block it?**  
A: Usually NO - uses HTTPS (port 443) which is almost never blocked

---

## 📝 Summary for Non-Technical Users

**In plain English:**

Running `svc.exe` is like giving a stranger the keys to your house and letting them live there secretly. They can:
- See everything you do
- Use your computer without you knowing
- Access all your files
- Spy on you through webcam/microphone
- Install themselves so they come back even after you try to remove them

The program tricks Windows into thinking it's a legitimate system service, turns off your antivirus, and makes it so no one needs a password to run programs on your computer.

**It's a full remote access tool with stealth and persistence.**

---

## 🎯 Key Takeaways

1. **Stealthy:** Hides as Windows system service
2. **Persistent:** Survives restarts, runs on boot
3. **Powerful:** Full system control + monitoring
4. **Destructive:** Disables UAC and Defender
5. **Remote:** Connects to external server
6. **Hard to Remove:** Multiple persistence mechanisms

**Bottom Line:** This is serious malware/RAT (Remote Access Tool) that gives complete control of your PC to whoever controls the server.
