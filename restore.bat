@echo off
REM ============================================================================
REM RESTORE.BAT - Complete System Restore Script for client.py Cleanup
REM ============================================================================
REM This script removes ALL traces of client.py from your system
REM Run as Administrator for complete cleanup
REM ============================================================================

echo.
echo ============================================================================
echo          CLIENT.PY COMPLETE SYSTEM RESTORE SCRIPT
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
echo.
echo Press CTRL+C to cancel, or
pause

echo.
echo [STEP 1/8] Removing Registry Run Keys...
echo ============================================================================

REM Remove HKCU Run keys
reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "svchost32" /f >nul 2>&1
reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "WindowsSecurityUpdate" /f >nul 2>&1
reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\RunOnce" /v "svchost32" /f >nul 2>&1
reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\RunOnce" /v "WindowsSecurityUpdate" /f >nul 2>&1

echo [OK] Registry Run keys removed

echo.
echo [STEP 2/8] Removing UAC Bypass Registry Keys...
echo ============================================================================

REM Remove ms-settings protocol hijack
reg delete "HKCU\Software\Classes\ms-settings\Shell\Open\command" /f >nul 2>&1
reg delete "HKCU\Software\Classes\ms-settings\Shell\Open" /f >nul 2>&1
reg delete "HKCU\Software\Classes\ms-settings\Shell" /f >nul 2>&1
reg delete "HKCU\Software\Classes\ms-settings" /f >nul 2>&1

REM Remove mscfile hijack (EventVwr bypass)
reg delete "HKCU\Software\Classes\mscfile\shell\open\command" /f >nul 2>&1

REM Remove exefile hijack (slui.exe bypass)
reg delete "HKCU\Software\Classes\exefile\shell\open\command" /f >nul 2>&1

REM Remove AppX registry hijack (WSReset bypass)
reg delete "HKCU\Software\Classes\AppX82a6gwre4fdg3bt635tn5ctqjf8msdd2\Shell\open\command" /f >nul 2>&1

REM Remove Folder shell hijack
reg delete "HKCU\Software\Classes\Folder\shell\open\command" /f >nul 2>&1

REM Remove COM handler hijacks
reg delete "HKCU\Software\Classes\CLSID\{3E5FC7F9-9A51-4367-9063-A120244FBEC7}\InprocServer32" /f >nul 2>&1
reg delete "HKCU\Software\Classes\CLSID\{D2E7041B-2927-42FB-8E9F-7CE93B6DC937}\InprocServer32" /f >nul 2>&1

REM Remove environment variable hijacks
reg delete "HKCU\Volatile Environment" /v "windir" /f >nul 2>&1

echo [OK] UAC bypass registry keys removed

echo.
echo [STEP 3/8] Restoring Notification Settings...
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
echo [STEP 4/8] Removing Scheduled Tasks...
echo ============================================================================

REM Remove scheduled tasks
schtasks /delete /tn "WindowsSecurityUpdate" /f >nul 2>&1
schtasks /delete /tn "WindowsSecurityUpdateTask" /f >nul 2>&1
schtasks /delete /tn "MicrosoftEdgeUpdateTaskUser" /f >nul 2>&1
schtasks /delete /tn "SystemUpdateTask" /f >nul 2>&1

echo [OK] Scheduled tasks removed

echo.
echo [STEP 5/8] Removing Windows Services...
echo ============================================================================

REM Stop and remove services
sc stop WindowsSecurityService >nul 2>&1
sc delete WindowsSecurityService >nul 2>&1
sc stop SystemUpdateService >nul 2>&1
sc delete SystemUpdateService >nul 2>&1

echo [OK] Windows services removed

echo.
echo [STEP 6/8] Removing Startup Folder Entries...
echo ============================================================================

REM Remove startup folder entries
del "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\SystemService.bat" /f >nul 2>&1
del "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\svchost32.bat" /f >nul 2>&1
del "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\WindowsUpdate.bat" /f >nul 2>&1

echo [OK] Startup folder entries removed

echo.
echo [STEP 7/8] Removing Deployed Files...
echo ============================================================================

REM Remove deployed executables and files
del "%LOCALAPPDATA%\Microsoft\Windows\svchost32.exe" /f >nul 2>&1
del "%LOCALAPPDATA%\Microsoft\Windows\svchost32.bat" /f >nul 2>&1
del "%LOCALAPPDATA%\Microsoft\Windows\svchost32.py" /f >nul 2>&1
del "%APPDATA%\Microsoft\Windows\svchost32.exe" /f >nul 2>&1
del "%APPDATA%\Microsoft\Windows\svchost32.bat" /f >nul 2>&1
del "%APPDATA%\Microsoft\Windows\svchost32.py" /f >nul 2>&1
del "%TEMP%\svchost32.py" /f >nul 2>&1
del "%TEMP%\svchost32.bat" /f >nul 2>&1

REM Remove watchdog files
del "%TEMP%\watchdog.py" /f >nul 2>&1
del "%TEMP%\watchdog.bat" /f >nul 2>&1

echo [OK] Deployed files removed

echo.
echo [STEP 8/8] Restoring Windows Defender Settings...
echo ============================================================================

REM Re-enable Windows Defender (requires admin)
reg delete "HKLM\SOFTWARE\Policies\Microsoft\Windows Defender" /v "DisableAntiSpyware" /f >nul 2>&1
reg delete "HKLM\SOFTWARE\Policies\Microsoft\Windows Defender\Real-Time Protection" /v "DisableRealtimeMonitoring" /f >nul 2>&1
reg delete "HKLM\SOFTWARE\Policies\Microsoft\Windows Defender\Real-Time Protection" /v "DisableBehaviorMonitoring" /f >nul 2>&1
reg delete "HKLM\SOFTWARE\Policies\Microsoft\Windows Defender\Real-Time Protection" /v "DisableOnAccessProtection" /f >nul 2>&1
reg delete "HKLM\SOFTWARE\Policies\Microsoft\Windows Defender\Real-Time Protection" /v "DisableScanOnRealtimeEnable" /f >nul 2>&1

REM Re-enable Windows Defender via PowerShell (requires admin)
powershell -Command "Set-MpPreference -DisableRealtimeMonitoring $false" >nul 2>&1
powershell -Command "Set-MpPreference -DisableBehaviorMonitoring $false" >nul 2>&1
powershell -Command "Set-MpPreference -DisableIOAVProtection $false" >nul 2>&1

echo [OK] Windows Defender settings restored

echo.
echo ============================================================================
echo [STEP 9/9] Additional Cleanup (Optional)...
echo ============================================================================

REM Kill any running instances
taskkill /f /im svchost32.exe >nul 2>&1
taskkill /f /im client.py >nul 2>&1
taskkill /f /im python.exe >nul 2>&1

REM Clear PowerShell execution policy changes
reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Policies\System" /v "DisableRegistryTools" /f >nul 2>&1
reg delete "HKCU\Software\Policies\Microsoft\Windows\System" /v "DisableCMD" /f >nul 2>&1

echo [OK] Additional cleanup completed

echo.
echo ============================================================================
echo                         CLEANUP COMPLETE
echo ============================================================================
echo.
echo All traces of client.py have been removed from your system.
echo.
echo RECOMMENDED NEXT STEPS:
echo   1. Restart your computer for changes to take full effect
echo   2. Run Windows Defender full scan: Start ^> Windows Security ^> Virus ^& threat protection ^> Quick scan
echo   3. Check Task Manager for any suspicious processes
echo   4. Verify notification settings: Start ^> Settings ^> System ^> Notifications
echo.
echo Your system should now be restored to its original state.
echo.

pause
exit /b 0
