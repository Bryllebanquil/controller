================================================================================
                    RESTORE.BAT - SYSTEM RESTORATION TOOL
================================================================================

PURPOSE:
    Remove ALL traces of client.py from your Windows system
    Restore your computer to its original state

QUICK START:
    1. Right-click restore.bat
    2. Select "Run as administrator"
    3. Press any key to confirm
    4. Restart your computer

WHAT IT REMOVES:
    ✓ Registry keys (30+ entries)
    ✓ Scheduled tasks (4 tasks)
    ✓ Windows services (2 services)
    ✓ Deployed files (10+ files)
    ✓ Startup folder entries
    ✓ Notification settings (restored)
    ✓ Windows Defender (re-enabled)

FILES INCLUDED:
    restore.bat              - Main cleanup script
    FOOTPRINT_ANALYSIS.md   - Complete list of modifications
    RESTORE_GUIDE.md        - Detailed usage instructions
    RESTORE_README.txt      - This file

IMPORTANT:
    ⚠ Must run as Administrator
    ⚠ Restart computer after running
    ⚠ Safe to run multiple times

VERIFICATION:
    After restore + restart, check:
    1. Task Manager → No svchost32.exe
    2. Task Manager → Startup tab → No client.py entries
    3. Services (services.msc) → No WindowsSecurityService
    4. Scheduled Tasks (taskschd.msc) → No WindowsSecurityUpdate
    5. Registry Run keys → Clean
    6. Windows Defender → Enabled
    7. Notifications (Win+A) → Working

FOR DETAILED INSTRUCTIONS:
    Open RESTORE_GUIDE.md

FOR COMPLETE ANALYSIS:
    Open FOOTPRINT_ANALYSIS.md

MANUAL CLEANUP (if needed):
    See "Advanced Cleanup" section in RESTORE_GUIDE.md

SAFETY:
    ✓ Script is safe to run
    ✓ Only removes client.py modifications
    ✓ Does not delete your personal files
    ✓ Does not affect Windows system files
    ✓ Can be run multiple times

SUPPORT:
    1. Read RESTORE_GUIDE.md for troubleshooting
    2. Check FOOTPRINT_ANALYSIS.md for details
    3. Run Windows Defender scan after restore

================================================================================
                        RESTORE YOUR SYSTEM NOW!
================================================================================

Right-click restore.bat → Run as administrator → Press any key → Restart

Your computer will be restored to its original state!

================================================================================
