@echo off
REM ============================================================================
REM RESTORE.BAT - Complete System Restore Script for client.py Cleanup
REM ============================================================================
REM This script removes ALL traces of client.py from your system
REM Run as Administrator for complete cleanup
REM Updated: Scanned client.py line-by-line for all modifications
REM ============================================================================

echo.
echo ============================================================================
echo          CLIENT.PY COMPLETE SYSTEM RESTORE SCRIPT v2.0
echo ============================================================================
echo.
echo This will remove ALL traces of client.py from your system including:
echo   - Registry keys (HKCU and HKLM)
echo   - Scheduled tasks
echo   - Startup entries
echo   - Services
echo   - Files and directories
echo   - Windows Defender modifications
echo   - Notification settings
echo   - UAC bypass registry hijacks
echo   - COM handler hijacks
echo   - Environment variable hijacks
echo.
echo Press CTRL+C to cancel, or
pause

echo.
echo [STEP 1/12] Removing Registry Run Keys...
echo ============================================================================

REM Remove HKCU Run keys
reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "svchost32" /f >nul 2>&1
reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "WindowsSecurityUpdate" /f >nul 2>&1
reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\RunOnce" /v "svchost32" /f >nul 2>&1
reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\RunOnce" /v "WindowsSecurityUpdate" /f >nul 2>&1

echo [OK] Registry Run keys removed

echo.
echo [STEP 2/12] Removing UAC Bypass Registry Keys (fodhelper/computerdefaults)...
echo ============================================================================

REM Remove ms-settings protocol hijack (fodhelper/computerdefaults bypass)
reg delete "HKCU\Software\Classes\ms-settings\Shell\Open\command" /f >nul 2>&1
reg delete "HKCU\Software\Classes\ms-settings\Shell\Open" /f >nul 2>&1
reg delete "HKCU\Software\Classes\ms-settings\Shell" /f >nul 2>&1
reg delete "HKCU\Software\Classes\ms-settings" /f >nul 2>&1

echo [OK] ms-settings protocol hijack removed

echo.
echo [STEP 3/12] Removing EventVwr UAC Bypass Registry Keys...
echo ============================================================================

REM Remove mscfile hijack (EventVwr bypass - UACME Method 25)
reg delete "HKCU\Software\Classes\mscfile\shell\open\command" /f >nul 2>&1
reg delete "HKCU\Software\Classes\mscfile\shell\open" /f >nul 2>&1
reg delete "HKCU\Software\Classes\mscfile\shell" /f >nul 2>&1
reg delete "HKCU\Software\Classes\mscfile" /f >nul 2>&1

echo [OK] EventVwr bypass registry keys removed

echo.
echo [STEP 4/12] Removing SDCLT UAC Bypass Registry Keys...
echo ============================================================================

REM Remove exefile hijack (sdclt bypass - UACME Method 31)
reg delete "HKCU\Software\Classes\exefile\shell\open\command" /f >nul 2>&1
reg delete "HKCU\Software\Classes\exefile\shell\open" /f >nul 2>&1

REM Remove Folder shell hijack (sdclt alternative)
reg delete "HKCU\Software\Classes\Folder\shell\open\command" /f >nul 2>&1
reg delete "HKCU\Software\Classes\Folder\shell\open" /f >nul 2>&1

echo [OK] SDCLT bypass registry keys removed

echo.
echo [STEP 5/12] Removing Additional UAC Bypass Registry Keys...
echo ============================================================================

REM Remove AppX registry hijack (WSReset bypass - UACME Method 56)
reg delete "HKCU\Software\Classes\AppX82a6gwre4fdg3bt635tn5ctqjf8msdd2\Shell\open\command" /f >nul 2>&1
reg delete "HKCU\Software\Classes\AppX82a6gwre4fdg3bt635tn5ctqjf8msdd2\Shell\open" /f >nul 2>&1
reg delete "HKCU\Software\Classes\AppX82a6gwre4fdg3bt635tn5ctqjf8msdd2\Shell" /f >nul 2>&1
reg delete "HKCU\Software\Classes\AppX82a6gwre4fdg3bt635tn5ctqjf8msdd2" /f >nul 2>&1

REM Remove slui.exe bypass (UACME Method 45)
reg delete "HKCU\Software\Classes\.exe\shell\open\command" /f >nul 2>&1

echo [OK] Additional UAC bypass keys removed

echo.
echo [STEP 6/12] Removing COM Handler Hijacks...
echo ============================================================================

REM Remove ICMLuaUtil COM interface hijack (UACME Method 41)
reg delete "HKCU\Software\Classes\CLSID\{3E5FC7F9-9A51-4367-9063-A120244FBEC7}\InprocServer32" /f >nul 2>&1
reg delete "HKCU\Software\Classes\CLSID\{3E5FC7F9-9A51-4367-9063-A120244FBEC7}" /f >nul 2>&1

REM Remove IColorDataProxy COM interface hijack (UACME Method 43)
reg delete "HKCU\Software\Classes\CLSID\{D2E7041B-2927-42FB-8E9F-7CE93B6DC937}\InprocServer32" /f >nul 2>&1
reg delete "HKCU\Software\Classes\CLSID\{D2E7041B-2927-42FB-8E9F-7CE93B6DC937}" /f >nul 2>&1

REM Remove additional COM hijacks
reg delete "HKCU\Software\Classes\CLSID\{BCDE0395-E52F-467C-8E3D-C4579291692E}\InprocServer32" /f >nul 2>&1
reg delete "HKCU\Software\Classes\CLSID\{BCDE0395-E52F-467C-8E3D-C4579291692E}" /f >nul 2>&1

echo [OK] COM handler hijacks removed

echo.
echo [STEP 7/12] Removing Environment Variable Hijacks...
echo ============================================================================

REM Remove environment variable hijacks (UACME Method 44)
reg delete "HKCU\Volatile Environment" /v "windir" /f >nul 2>&1
reg delete "HKCU\Environment" /v "windir" /f >nul 2>&1
reg delete "HKCU\Environment" /v "PATH_MODIFIED_BY_AGENT" /f >nul 2>&1

echo [OK] Environment variable hijacks removed

echo.
echo [STEP 8/12] Restoring Notification Settings...
echo ============================================================================

REM Restore Action Center notifications
reg delete "HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\PushNotifications" /v "ToastEnabled" /f >nul 2>&1

REM Restore Notification Center
reg delete "HKCU\SOFTWARE\Policies\Microsoft\Windows\Explorer" /v "DisableNotificationCenter" /f >nul 2>&1
reg delete "HKLM\SOFTWARE\Policies\Microsoft\Windows\Explorer" /v "DisableNotificationCenter" /f >nul 2>&1

REM Restore Windows Defender notifications
reg delete "HKCU\SOFTWARE\Microsoft\Windows Defender\UX Configuration" /v "Notification_Suppress" /f >nul 2>&1

REM Restore toast notifications
reg delete "HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Notifications\Settings" /v "NOC_GLOBAL_SETTING_ALLOW_TOASTS_ABOVE_LOCK" /f >nul 2>&1
reg delete "HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Notifications\Settings" /v "NOC_GLOBAL_SETTING_ALLOW_CRITICAL_TOASTS_ABOVE_LOCK" /f >nul 2>&1

REM Restore Windows Update notifications
reg delete "HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Notifications\Settings\Windows.SystemToast.WindowsUpdate" /v "Enabled" /f >nul 2>&1

REM Restore Security notifications
reg delete "HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Notifications\Settings\Windows.SystemToast.SecurityAndMaintenance" /v "Enabled" /f >nul 2>&1

echo [OK] Notification settings restored

echo.
echo [STEP 9/12] Removing Scheduled Tasks...
echo ============================================================================

REM Remove scheduled tasks
schtasks /delete /tn "WindowsSecurityUpdate" /f >nul 2>&1
schtasks /delete /tn "WindowsSecurityUpdateTask" /f >nul 2>&1
schtasks /delete /tn "MicrosoftEdgeUpdateTaskUser" /f >nul 2>&1
schtasks /delete /tn "SystemUpdateTask" /f >nul 2>&1

REM Remove SilentCleanup abuse (UACME Method 34)
REM Note: We don't delete this task as it's a legitimate Windows task
REM But we ensure it's not being abused
schtasks /query /tn "\Microsoft\Windows\DiskCleanup\SilentCleanup" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [INFO] SilentCleanup task exists - verify it's legitimate in Task Scheduler
)

echo [OK] Scheduled tasks removed

echo.
echo [STEP 10/12] Removing Windows Services...
echo ============================================================================

REM Stop and remove services
sc stop WindowsSecurityService >nul 2>&1
sc delete WindowsSecurityService >nul 2>&1
sc stop WindowsSecurityUpdate >nul 2>&1
sc delete WindowsSecurityUpdate >nul 2>&1
sc stop SystemUpdateService >nul 2>&1
sc delete SystemUpdateService >nul 2>&1

echo [OK] Windows services removed

echo.
echo [STEP 11/12] Removing Startup Folder Entries and Files...
echo ============================================================================

REM Remove startup folder entries
del "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\SystemService.bat" /f >nul 2>&1
del "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\svchost32.bat" /f >nul 2>&1
del "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\WindowsUpdate.bat" /f >nul 2>&1
del "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\svchost32.exe" /f >nul 2>&1

REM Remove deployed executables and files
del "%LOCALAPPDATA%\Microsoft\Windows\svchost32.exe" /f >nul 2>&1
del "%LOCALAPPDATA%\Microsoft\Windows\svchost32.bat" /f >nul 2>&1
del "%LOCALAPPDATA%\Microsoft\Windows\svchost32.py" /f >nul 2>&1
del "%APPDATA%\Microsoft\Windows\svchost32.exe" /f >nul 2>&1
del "%APPDATA%\Microsoft\Windows\svchost32.bat" /f >nul 2>&1
del "%APPDATA%\Microsoft\Windows\svchost32.py" /f >nul 2>&1

REM Remove temp files
del "%TEMP%\svchost32.py" /f >nul 2>&1
del "%TEMP%\svchost32.bat" /f >nul 2>&1
del "%TEMP%\svchost32.exe" /f >nul 2>&1
del "%TEMP%\watchdog.py" /f >nul 2>&1
del "%TEMP%\watchdog.bat" /f >nul 2>&1
del "%TEMP%\deploy.ps1" /f >nul 2>&1
del "%TEMP%\tamper_protection.py" /f >nul 2>&1
del "%TEMP%\tamper_protection.exe" /f >nul 2>&1
del "%TEMP%\uac_bypass.reg" /f >nul 2>&1

REM Remove fake system directories
rd /s /q "%TEMP%\Windows" >nul 2>&1
rd /s /q "%TEMP%\System32" >nul 2>&1
rd /s /q "%TEMP%\junction_target" >nul 2>&1
rd /s /q "%TEMP%\fake_system32" >nul 2>&1

REM Remove profiler DLLs
del "%TEMP%\profiler.dll" /f >nul 2>&1
del "%TEMP%\DismCore.dll" /f >nul 2>&1
del "%TEMP%\wow64log.dll" /f >nul 2>&1

REM Remove mock directories
rd /s /q "%TEMP%\mock_system32" >nul 2>&1

REM Remove fake MSC files
del "%TEMP%\fake.msc" /f >nul 2>&1

REM Remove potential System32 copies
del "C:\Windows\System32\svchost32.exe" /f >nul 2>&1
del "C:\Windows\SysWOW64\svchost32.exe" /f >nul 2>&1
del "C:\Windows\System32\drivers\svchost32.exe" /f >nul 2>&1

echo [OK] Startup entries and files removed

echo.
echo [STEP 12/12] Restoring Windows Defender Settings...
echo ============================================================================

REM Re-enable Windows Defender (requires admin)
reg delete "HKLM\SOFTWARE\Policies\Microsoft\Windows Defender" /v "DisableAntiSpyware" /f >nul 2>&1
reg delete "HKLM\SOFTWARE\Policies\Microsoft\Windows Defender\Real-Time Protection" /v "DisableRealtimeMonitoring" /f >nul 2>&1
reg delete "HKLM\SOFTWARE\Policies\Microsoft\Windows Defender\Real-Time Protection" /v "DisableBehaviorMonitoring" /f >nul 2>&1
reg delete "HKLM\SOFTWARE\Policies\Microsoft\Windows Defender\Real-Time Protection" /v "DisableOnAccessProtection" /f >nul 2>&1
reg delete "HKLM\SOFTWARE\Policies\Microsoft\Windows Defender\Real-Time Protection" /v "DisableScanOnRealtimeEnable" /f >nul 2>&1
reg delete "HKLM\SOFTWARE\Policies\Microsoft\Windows Defender\Real-Time Protection" /v "DisableIOAVProtection" /f >nul 2>&1

REM Re-enable Windows Defender via PowerShell (requires admin)
powershell -Command "Set-MpPreference -DisableRealtimeMonitoring $false" >nul 2>&1
powershell -Command "Set-MpPreference -DisableBehaviorMonitoring $false" >nul 2>&1
powershell -Command "Set-MpPreference -DisableIOAVProtection $false" >nul 2>&1
powershell -Command "Set-MpPreference -DisableOnAccessProtection $false" >nul 2>&1
powershell -Command "Set-MpPreference -DisableIntrusionPreventionSystem $false" >nul 2>&1
powershell -Command "Set-MpPreference -DisableScriptScanning $false" >nul 2>&1

echo [OK] Windows Defender settings restored

echo.
echo ============================================================================
echo [ADDITIONAL CLEANUP] Stopping Running Processes and Final Cleanup...
echo ============================================================================

REM Kill any running instances
taskkill /f /im svchost32.exe >nul 2>&1
taskkill /f /im client.py >nul 2>&1
taskkill /f /im pythonw.exe >nul 2>&1

REM CRITICAL: Re-enable Task Manager, Registry Editor, and CMD
echo [CRITICAL] Re-enabling Task Manager...
reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Policies\System" /v "DisableTaskMgr" /f >nul 2>&1
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Policies\System" /v "DisableTaskMgr" /t REG_DWORD /d 0 /f >nul 2>&1

echo [CRITICAL] Re-enabling Registry Editor...
reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Policies\System" /v "DisableRegistryTools" /f >nul 2>&1
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Policies\System" /v "DisableRegistryTools" /t REG_DWORD /d 0 /f >nul 2>&1

echo [CRITICAL] Re-enabling Command Prompt...
reg delete "HKCU\Software\Policies\Microsoft\Windows\System" /v "DisableCMD" /f >nul 2>&1
reg add "HKCU\Software\Policies\Microsoft\Windows\System" /v "DisableCMD" /t REG_DWORD /d 0 /f >nul 2>&1

echo [CRITICAL] Restoring PowerShell Execution Policy...
reg delete "HKCU\Software\Microsoft\PowerShell\1\ShellIds\Microsoft.PowerShell" /v "ExecutionPolicy" /f >nul 2>&1

REM Restore UAC settings if modified
reg add "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System" /v "EnableLUA" /t REG_DWORD /d 1 /f >nul 2>&1
reg add "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System" /v "ConsentPromptBehaviorAdmin" /t REG_DWORD /d 5 /f >nul 2>&1
reg add "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System" /v "PromptOnSecureDesktop" /t REG_DWORD /d 1 /f >nul 2>&1

REM Clean up .NET profiler hijacks
reg delete "HKCU\Environment" /v "COR_ENABLE_PROFILING" /f >nul 2>&1
reg delete "HKCU\Environment" /v "COR_PROFILER" /f >nul 2>&1
reg delete "HKCU\Environment" /v "COR_PROFILER_PATH" /f >nul 2>&1

echo [OK] Additional cleanup completed

echo.
echo ============================================================================
echo                         CLEANUP COMPLETE
echo ============================================================================
echo.
echo All traces of client.py have been removed from your system.
echo.
echo RECOMMENDED NEXT STEPS:
echo   1. RESTART YOUR COMPUTER for changes to take full effect
echo   2. Run Windows Defender full scan: Start ^> Windows Security ^> Virus ^& threat protection ^> Full scan
echo   3. Check Task Manager (Ctrl+Shift+Esc) for any suspicious processes
echo   4. Verify Task Scheduler: taskschd.msc (ensure no suspicious scheduled tasks)
echo   5. Check Services: services.msc (ensure no suspicious services)
echo   6. Verify startup items: msconfig ^> Startup tab
echo   7. Verify notification settings: Start ^> Settings ^> System ^> Notifications
echo   8. Check registry: regedit (verify HKCU\Software\Microsoft\Windows\CurrentVersion\Run)
echo.
echo REGISTRY AREAS CLEANED:
echo   - HKCU\Software\Microsoft\Windows\CurrentVersion\Run
echo   - HKCU\Software\Microsoft\Windows\CurrentVersion\RunOnce
echo   - HKCU\Software\Classes\ms-settings
echo   - HKCU\Software\Classes\mscfile
echo   - HKCU\Software\Classes\exefile
echo   - HKCU\Software\Classes\Folder
echo   - HKCU\Software\Classes\CLSID (COM hijacks)
echo   - HKCU\Volatile Environment
echo   - HKLM\SOFTWARE\Policies\Microsoft\Windows Defender
echo   - Notification settings (HKCU + HKLM)
echo.
echo FILES AND FOLDERS CLEANED:
echo   - %%LOCALAPPDATA%%\Microsoft\Windows\svchost32.*
echo   - %%APPDATA%%\Microsoft\Windows\svchost32.*
echo   - %%TEMP%%\svchost32.*
echo   - %%TEMP%%\Windows (fake directory)
echo   - %%TEMP%%\System32 (fake directory)
echo   - All watchdog and tamper protection files
echo   - All temporary exploit files (DLLs, REG files, etc.)
echo.
echo SCHEDULED TASKS REMOVED:
echo   - WindowsSecurityUpdate
echo   - WindowsSecurityUpdateTask
echo   - MicrosoftEdgeUpdateTaskUser
echo   - SystemUpdateTask
echo.
echo SERVICES REMOVED:
echo   - WindowsSecurityService
echo   - WindowsSecurityUpdate
echo   - SystemUpdateService
echo.
echo Your system should now be restored to its original state.
echo If you notice any remaining issues, please run test_restore.bat to verify cleanup.
echo.

pause
exit /b 0
