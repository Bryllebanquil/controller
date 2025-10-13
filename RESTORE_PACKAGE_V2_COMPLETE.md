# Complete Restore Package v2.0 - Updated Documentation

## 📋 Overview

This restore package has been **completely updated** based on a **line-by-line scan** of `client.py` to identify ALL system modifications.

---

## 📦 Package Contents

### Main Scripts:
1. **`restore.bat`** - Complete system cleanup (v2.0)
2. **`test_restore.bat`** - Verification tool (v2.0)

### Documentation:
3. **`RESTORE_PACKAGE_V2_COMPLETE.md`** - This file
4. **`FOOTPRINT_ANALYSIS.md`** - Original footprint analysis
5. **`RESTORE_GUIDE.md`** - Detailed restore guide

---

## 🆕 What's New in v2.0

### Added Cleanup Targets:

#### 1. **Additional UAC Bypass Methods** ✅
- **EventVwr.exe** (UACME Method 25) - `mscfile` registry hijack
- **sdclt.exe** (UACME Method 31) - `exefile` and `Folder` hijacks
- **WSReset.exe** (UACME Method 56) - `AppX` registry hijack
- **slui.exe** (UACME Method 45) - `.exe` shell hijack

#### 2. **COM Handler Hijacks** ✅
- **ICMLuaUtil** (UACME Method 41) - CLSID `{3E5FC7F9-9A51-4367-9063-A120244FBEC7}`
- **IColorDataProxy** (UACME Method 43) - CLSID `{D2E7041B-2927-42FB-8E9F-7CE93B6DC937}`
- Additional COM hijacks - CLSID `{BCDE0395-E52F-467C-8E3D-C4579291692E}`

#### 3. **Environment Variable Hijacks** ✅
- **windir** variable hijack (UACME Method 44)
- **.NET Profiler** hijacks:
  - `COR_ENABLE_PROFILING`
  - `COR_PROFILER`
  - `COR_PROFILER_PATH`

#### 4. **Temporary Exploit Files** ✅
- `%TEMP%\uac_bypass.reg`
- `%TEMP%\deploy.ps1`
- `%TEMP%\tamper_protection.py`
- `%TEMP%\tamper_protection.exe`
- `%TEMP%\profiler.dll`
- `%TEMP%\DismCore.dll`
- `%TEMP%\wow64log.dll`
- `%TEMP%\fake.msc`

#### 5. **Fake System Directories** ✅
- `%TEMP%\Windows`
- `%TEMP%\System32`
- `%TEMP%\junction_target`
- `%TEMP%\fake_system32`
- `%TEMP%\mock_system32`

#### 6. **Additional Services** ✅
- `WindowsSecurityUpdate` (in addition to `WindowsSecurityService`)

#### 7. **UAC Settings Restoration** ✅
- Restores proper UAC levels:
  - `EnableLUA` = 1
  - `ConsentPromptBehaviorAdmin` = 5
  - `PromptOnSecureDesktop` = 1

#### 8. **Additional Windows Defender Settings** ✅
- `DisableIOAVProtection`
- `DisableOnAccessProtection`
- `DisableIntrusionPreventionSystem`
- `DisableScriptScanning`

#### 9. **System32 Copies** ✅
- `C:\Windows\System32\svchost32.exe`
- `C:\Windows\SysWOW64\svchost32.exe`
- `C:\Windows\System32\drivers\svchost32.exe`

---

## 🎯 Complete List of What Gets Cleaned

### Registry Keys (31 total):

#### HKCU - Run Keys (4):
```
HKCU\Software\Microsoft\Windows\CurrentVersion\Run
  - svchost32
  - WindowsSecurityUpdate
HKCU\Software\Microsoft\Windows\CurrentVersion\RunOnce
  - svchost32
  - WindowsSecurityUpdate
```

#### HKCU - UAC Bypass Keys (5):
```
HKCU\Software\Classes\ms-settings\Shell\Open\command
HKCU\Software\Classes\mscfile\shell\open\command
HKCU\Software\Classes\exefile\shell\open\command
HKCU\Software\Classes\Folder\shell\open\command
HKCU\Software\Classes\.exe\shell\open\command
HKCU\Software\Classes\AppX82a6gwre4fdg3bt635tn5ctqjf8msdd2\Shell\open\command
```

#### HKCU - COM Hijacks (3):
```
HKCU\Software\Classes\CLSID\{3E5FC7F9-9A51-4367-9063-A120244FBEC7}\InprocServer32
HKCU\Software\Classes\CLSID\{D2E7041B-2927-42FB-8E9F-7CE93B6DC937}\InprocServer32
HKCU\Software\Classes\CLSID\{BCDE0395-E52F-467C-8E3D-C4579291692E}\InprocServer32
```

#### HKCU - Environment Variables (4):
```
HKCU\Volatile Environment
  - windir
HKCU\Environment
  - windir
  - COR_ENABLE_PROFILING
  - COR_PROFILER
  - COR_PROFILER_PATH
```

#### HKCU - Notifications (7):
```
HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\PushNotifications
  - ToastEnabled
HKCU\SOFTWARE\Policies\Microsoft\Windows\Explorer
  - DisableNotificationCenter
HKCU\SOFTWARE\Microsoft\Windows Defender\UX Configuration
  - Notification_Suppress
HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Notifications\Settings
  - NOC_GLOBAL_SETTING_ALLOW_TOASTS_ABOVE_LOCK
  - NOC_GLOBAL_SETTING_ALLOW_CRITICAL_TOASTS_ABOVE_LOCK
HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Notifications\Settings\Windows.SystemToast.WindowsUpdate
  - Enabled
HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Notifications\Settings\Windows.SystemToast.SecurityAndMaintenance
  - Enabled
```

#### HKLM - Windows Defender (8):
```
HKLM\SOFTWARE\Policies\Microsoft\Windows Defender
  - DisableAntiSpyware
HKLM\SOFTWARE\Policies\Microsoft\Windows Defender\Real-Time Protection
  - DisableRealtimeMonitoring
  - DisableBehaviorMonitoring
  - DisableOnAccessProtection
  - DisableScanOnRealtimeEnable
  - DisableIOAVProtection
```

#### HKLM - UAC Settings (3):
```
HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System
  - EnableLUA (restored to 1)
  - ConsentPromptBehaviorAdmin (restored to 5)
  - PromptOnSecureDesktop (restored to 1)
```

#### HKLM - Notifications (1):
```
HKLM\SOFTWARE\Policies\Microsoft\Windows\Explorer
  - DisableNotificationCenter
```

---

### Scheduled Tasks (4+):
```
- WindowsSecurityUpdate
- WindowsSecurityUpdateTask
- MicrosoftEdgeUpdateTaskUser
- SystemUpdateTask
```

---

### Windows Services (3):
```
- WindowsSecurityService
- WindowsSecurityUpdate
- SystemUpdateService
```

---

### Files and Directories (40+):

#### Startup Folder (4):
```
%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\
  - SystemService.bat
  - svchost32.bat
  - svchost32.exe
  - WindowsUpdate.bat
```

#### LOCALAPPDATA (3):
```
%LOCALAPPDATA%\Microsoft\Windows\
  - svchost32.exe
  - svchost32.bat
  - svchost32.py
```

#### APPDATA (3):
```
%APPDATA%\Microsoft\Windows\
  - svchost32.exe
  - svchost32.bat
  - svchost32.py
```

#### TEMP Files (10):
```
%TEMP%\
  - svchost32.py
  - svchost32.bat
  - svchost32.exe
  - watchdog.py
  - watchdog.bat
  - deploy.ps1
  - tamper_protection.py
  - tamper_protection.exe
  - uac_bypass.reg
  - fake.msc
```

#### TEMP DLLs (3):
```
%TEMP%\
  - profiler.dll
  - DismCore.dll
  - wow64log.dll
```

#### TEMP Directories (5):
```
%TEMP%\
  - Windows\
  - System32\
  - junction_target\
  - fake_system32\
  - mock_system32\
```

#### System32 (3):
```
C:\Windows\System32\
  - svchost32.exe
C:\Windows\SysWOW64\
  - svchost32.exe
C:\Windows\System32\drivers\
  - svchost32.exe
```

---

### Processes Terminated (3):
```
- svchost32.exe
- client.py
- pythonw.exe
```

---

## 🚀 Usage Instructions

### Step 1: Run restore.bat

```batch
Right-click restore.bat → Run as administrator
```

**What it does:**
- Removes all 31+ registry keys
- Deletes 4 scheduled tasks
- Removes 3 Windows services
- Deletes 40+ files and directories
- Restores Windows Defender settings
- Restores UAC settings
- Restores notification settings
- Terminates running processes

---

### Step 2: Run test_restore.bat

```batch
Right-click test_restore.bat → Run as administrator
```

**What it does:**
- Verifies all 12 cleanup categories
- Counts passed and failed tests
- Shows detailed scan results
- Reports SUCCESS or issues found

---

### Step 3: Restart Computer

```
Restart → Complete cleanup
```

---

## ✅ Verification Checklist

After running both scripts:

- [ ] Registry Run keys removed
- [ ] UAC bypass keys removed
- [ ] COM hijacks removed
- [ ] Environment variables restored
- [ ] Notification settings restored
- [ ] Scheduled tasks removed
- [ ] Windows services removed
- [ ] Files deleted
- [ ] Processes terminated
- [ ] Windows Defender restored
- [ ] UAC settings restored
- [ ] test_restore.bat shows 0 failures

---

## 📊 Expected Output

### restore.bat Success:
```
============================================================================
                         CLEANUP COMPLETE
============================================================================

All traces of client.py have been removed from your system.

RECOMMENDED NEXT STEPS:
  1. RESTART YOUR COMPUTER
  2. Run Windows Defender full scan
  3. Run test_restore.bat
```

### test_restore.bat Success:
```
============================================================================
                         VERIFICATION COMPLETE
============================================================================

RESULTS:
  Tests Passed: 25
  Tests Failed: 0

========================================================================
  ✓✓✓ SUCCESS! ALL TRACES HAVE BEEN REMOVED! ✓✓✓
========================================================================
```

---

## 🐛 Troubleshooting

### Issue: Some tests fail

**Solution:**
1. Restart in Safe Mode
2. Run restore.bat again as admin
3. Use Task Manager to end processes
4. Manually remove remaining entries

### Issue: Access Denied errors

**Solution:**
1. Ensure running as Administrator
2. Take ownership of registry keys:
   ```
   regedit → Right-click key → Permissions → Take Ownership
   ```
3. Disable any security software temporarily

### Issue: Files in use

**Solution:**
1. Restart computer
2. Run restore.bat before other programs start
3. Boot into Safe Mode

---

## 📋 Manual Verification

### Check Registry:
```
regedit

Navigate to:
HKCU\Software\Microsoft\Windows\CurrentVersion\Run
HKCU\Software\Classes\ms-settings
HKCU\Software\Classes\mscfile
HKCU\Software\Classes\CLSID

Verify: No svchost32 or WindowsSecurityUpdate entries
```

### Check Scheduled Tasks:
```
taskschd.msc

Look for:
- WindowsSecurityUpdate
- WindowsSecurityUpdateTask

Verify: Not present
```

### Check Services:
```
services.msc

Look for:
- WindowsSecurityService
- WindowsSecurityUpdate
- SystemUpdateService

Verify: Not present
```

### Check Startup:
```
Task Manager (Ctrl+Shift+Esc) → Startup tab

Look for:
- svchost32
- Any suspicious entries

Verify: None present
```

---

## 🎯 Complete System Restoration

### Before restore.bat:
```
❌ 31+ registry keys modified
❌ 4+ scheduled tasks created
❌ 3 services created
❌ 40+ files deployed
❌ UAC bypasses active
❌ COM hijacks active
❌ Notifications disabled
❌ Defender disabled
```

### After restore.bat + restart:
```
✅ All registry keys removed/restored
✅ All scheduled tasks removed
✅ All services removed
✅ All files deleted
✅ UAC bypasses removed
✅ COM hijacks removed
✅ Notifications enabled
✅ Defender enabled
```

---

## 📞 Support

### If restore fails:

1. **Boot into Safe Mode:**
   ```
   Settings → Update & Security → Recovery → Advanced startup → Restart now
   → Troubleshoot → Advanced options → Startup Settings → Restart
   → Press 4 for Safe Mode
   ```

2. **Run restore.bat in Safe Mode**

3. **Manual cleanup if needed:**
   - Use `regedit` to remove keys
   - Use `taskschd.msc` to remove tasks
   - Use `services.msc` to remove services
   - Use File Explorer to delete files

---

## 🎉 Summary

### restore.bat v2.0 Features:

✅ **12 cleanup steps** (vs 8 in v1.0)
✅ **31+ registry keys** removed (vs 20 in v1.0)
✅ **40+ files/directories** deleted (vs 15 in v1.0)
✅ **UAC settings** restored
✅ **.NET profiler** hijacks removed
✅ **COM handlers** removed
✅ **Environment variables** restored
✅ **Fake directories** removed
✅ **Temporary exploits** removed
✅ **Additional Defender settings** restored

### test_restore.bat v2.0 Features:

✅ **12 test categories** (vs 9 in v1.0)
✅ **25+ individual tests**
✅ **Detailed registry scan**
✅ **Pass/fail count**
✅ **Success/failure reporting**
✅ **Manual verification tips**

---

## 📖 Files in Restore Package v2.0

1. ✅ `restore.bat` - Main cleanup script (v2.0)
2. ✅ `test_restore.bat` - Verification script (v2.0)
3. ✅ `RESTORE_PACKAGE_V2_COMPLETE.md` - This documentation
4. ✅ `FOOTPRINT_ANALYSIS.md` - Detailed footprint analysis
5. ✅ `RESTORE_GUIDE.md` - Step-by-step guide
6. ✅ `RESTORE_README.txt` - Quick reference
7. ✅ `README_RESTORE.md` - Navigation guide

---

**Your system will be completely restored to its original state!** ✅

**Run restore.bat → test_restore.bat → Restart → Clean!** 🎉
