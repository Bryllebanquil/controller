@echo off
REM ============================================================================
REM TEST_RESTORE.BAT - Verification Script for Restore Cleanup
REM ============================================================================
REM This script verifies that all traces of client.py have been removed
REM Run AFTER running restore.bat
REM Updated: Comprehensive verification based on line-by-line scan
REM ============================================================================

echo.
echo ============================================================================
echo          CLIENT.PY RESTORE VERIFICATION SCRIPT v2.0
echo ============================================================================
echo.
echo This script will verify that all traces have been removed.
echo.
pause

echo.
echo [TEST 1/12] Checking Registry Run Keys...
echo ============================================================================

set FAIL_COUNT=0
set PASS_COUNT=0

reg query "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "svchost32" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [FAIL] svchost32 still in Run key
    set /a FAIL_COUNT+=1
) else (
    echo [PASS] svchost32 removed from Run key
    set /a PASS_COUNT+=1
)

reg query "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "WindowsSecurityUpdate" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [FAIL] WindowsSecurityUpdate still in Run key
    set /a FAIL_COUNT+=1
) else (
    echo [PASS] WindowsSecurityUpdate removed from Run key
    set /a PASS_COUNT+=1
)

reg query "HKCU\Software\Microsoft\Windows\CurrentVersion\RunOnce" /v "svchost32" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [FAIL] svchost32 still in RunOnce key
    set /a FAIL_COUNT+=1
) else (
    echo [PASS] svchost32 removed from RunOnce key
    set /a PASS_COUNT+=1
)

echo.
echo [TEST 2/12] Checking UAC Bypass Registry Keys (ms-settings)...
echo ============================================================================

reg query "HKCU\Software\Classes\ms-settings\Shell\Open\command" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [FAIL] ms-settings hijack still exists
    set /a FAIL_COUNT+=1
) else (
    echo [PASS] ms-settings hijack removed
    set /a PASS_COUNT+=1
)

echo.
echo [TEST 3/12] Checking EventVwr Bypass Keys (mscfile)...
echo ============================================================================

reg query "HKCU\Software\Classes\mscfile\shell\open\command" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [FAIL] mscfile hijack still exists
    set /a FAIL_COUNT+=1
) else (
    echo [PASS] mscfile hijack removed
    set /a PASS_COUNT+=1
)

echo.
echo [TEST 4/12] Checking SDCLT Bypass Keys...
echo ============================================================================

reg query "HKCU\Software\Classes\exefile\shell\open\command" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [FAIL] exefile hijack still exists
    set /a FAIL_COUNT+=1
) else (
    echo [PASS] exefile hijack removed
    set /a PASS_COUNT+=1
)

reg query "HKCU\Software\Classes\Folder\shell\open\command" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [FAIL] Folder shell hijack still exists
    set /a FAIL_COUNT+=1
) else (
    echo [PASS] Folder shell hijack removed
    set /a PASS_COUNT+=1
)

echo.
echo [TEST 5/12] Checking COM Handler Hijacks...
echo ============================================================================

reg query "HKCU\Software\Classes\CLSID\{3E5FC7F9-9A51-4367-9063-A120244FBEC7}\InprocServer32" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [FAIL] ICMLuaUtil COM hijack still exists
    set /a FAIL_COUNT+=1
) else (
    echo [PASS] ICMLuaUtil COM hijack removed
    set /a PASS_COUNT+=1
)

reg query "HKCU\Software\Classes\CLSID\{D2E7041B-2927-42FB-8E9F-7CE93B6DC937}\InprocServer32" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [FAIL] IColorDataProxy COM hijack still exists
    set /a FAIL_COUNT+=1
) else (
    echo [PASS] IColorDataProxy COM hijack removed
    set /a PASS_COUNT+=1
)

echo.
echo [TEST 6/12] Checking Environment Variable Hijacks...
echo ============================================================================

reg query "HKCU\Volatile Environment" /v "windir" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [FAIL] windir environment variable hijack still exists
    set /a FAIL_COUNT+=1
) else (
    echo [PASS] windir environment variable hijack removed
    set /a PASS_COUNT+=1
)

reg query "HKCU\Environment" /v "COR_ENABLE_PROFILING" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [FAIL] .NET profiler hijack still exists
    set /a FAIL_COUNT+=1
) else (
    echo [PASS] .NET profiler hijack removed
    set /a PASS_COUNT+=1
)

echo.
echo [TEST 7/12] Checking Notification Settings...
echo ============================================================================

reg query "HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\PushNotifications" /v "ToastEnabled" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [INFO] ToastEnabled setting exists (may be normal)
) else (
    echo [PASS] ToastEnabled setting removed
    set /a PASS_COUNT+=1
)

reg query "HKCU\SOFTWARE\Policies\Microsoft\Windows\Explorer" /v "DisableNotificationCenter" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [FAIL] DisableNotificationCenter still set
    set /a FAIL_COUNT+=1
) else (
    echo [PASS] DisableNotificationCenter removed
    set /a PASS_COUNT+=1
)

echo.
echo [TEST 8/12] Checking Scheduled Tasks...
echo ============================================================================

schtasks /query /tn "WindowsSecurityUpdate" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [FAIL] WindowsSecurityUpdate task still exists
    set /a FAIL_COUNT+=1
) else (
    echo [PASS] WindowsSecurityUpdate task removed
    set /a PASS_COUNT+=1
)

schtasks /query /tn "WindowsSecurityUpdateTask" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [FAIL] WindowsSecurityUpdateTask still exists
    set /a FAIL_COUNT+=1
) else (
    echo [PASS] WindowsSecurityUpdateTask removed
    set /a PASS_COUNT+=1
)

echo.
echo [TEST 9/12] Checking Windows Services...
echo ============================================================================

sc query WindowsSecurityService >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [FAIL] WindowsSecurityService still exists
    set /a FAIL_COUNT+=1
) else (
    echo [PASS] WindowsSecurityService removed
    set /a PASS_COUNT+=1
)

sc query WindowsSecurityUpdate >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [FAIL] WindowsSecurityUpdate service still exists
    set /a FAIL_COUNT+=1
) else (
    echo [PASS] WindowsSecurityUpdate service removed
    set /a PASS_COUNT+=1
)

echo.
echo [TEST 10/12] Checking Deployed Files...
echo ============================================================================

if exist "%LOCALAPPDATA%\Microsoft\Windows\svchost32.exe" (
    echo [FAIL] svchost32.exe still exists in LOCALAPPDATA
    set /a FAIL_COUNT+=1
) else (
    echo [PASS] svchost32.exe removed from LOCALAPPDATA
    set /a PASS_COUNT+=1
)

if exist "%APPDATA%\Microsoft\Windows\svchost32.exe" (
    echo [FAIL] svchost32.exe still exists in APPDATA
    set /a FAIL_COUNT+=1
) else (
    echo [PASS] svchost32.exe removed from APPDATA
    set /a PASS_COUNT+=1
)

if exist "%TEMP%\svchost32.py" (
    echo [FAIL] svchost32.py still exists in TEMP
    set /a FAIL_COUNT+=1
) else (
    echo [PASS] svchost32.py removed from TEMP
    set /a PASS_COUNT+=1
)

if exist "%TEMP%\uac_bypass.reg" (
    echo [FAIL] uac_bypass.reg still exists in TEMP
    set /a FAIL_COUNT+=1
) else (
    echo [PASS] uac_bypass.reg removed from TEMP
    set /a PASS_COUNT+=1
)

if exist "%TEMP%\Windows" (
    echo [FAIL] Fake Windows directory still exists in TEMP
    set /a FAIL_COUNT+=1
) else (
    echo [PASS] Fake Windows directory removed from TEMP
    set /a PASS_COUNT+=1
)

if exist "%TEMP%\profiler.dll" (
    echo [FAIL] profiler.dll still exists in TEMP
    set /a FAIL_COUNT+=1
) else (
    echo [PASS] profiler.dll removed from TEMP
    set /a PASS_COUNT+=1
)

if exist "C:\Windows\System32\svchost32.exe" (
    echo [FAIL] svchost32.exe still exists in System32
    set /a FAIL_COUNT+=1
) else (
    echo [PASS] svchost32.exe removed from System32
    set /a PASS_COUNT+=1
)

echo.
echo [TEST 11/12] Checking Running Processes...
echo ============================================================================

tasklist | find /i "svchost32.exe" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [FAIL] svchost32.exe is still running
    set /a FAIL_COUNT+=1
) else (
    echo [PASS] svchost32.exe is not running
    set /a PASS_COUNT+=1
)

tasklist | find /i "client.py" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [FAIL] client.py is still running
    set /a FAIL_COUNT+=1
) else (
    echo [PASS] client.py is not running
    set /a PASS_COUNT+=1
)

echo.
echo [TEST 12/12] Checking Windows Defender Settings...
echo ============================================================================

reg query "HKLM\SOFTWARE\Policies\Microsoft\Windows Defender" /v "DisableAntiSpyware" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [FAIL] Windows Defender DisableAntiSpyware still set
    set /a FAIL_COUNT+=1
) else (
    echo [PASS] Windows Defender DisableAntiSpyware removed
    set /a PASS_COUNT+=1
)

reg query "HKLM\SOFTWARE\Policies\Microsoft\Windows Defender\Real-Time Protection" /v "DisableRealtimeMonitoring" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [FAIL] DisableRealtimeMonitoring still set
    set /a FAIL_COUNT+=1
) else (
    echo [PASS] DisableRealtimeMonitoring removed
    set /a PASS_COUNT+=1
)

echo.
echo ============================================================================
echo                         VERIFICATION COMPLETE
echo ============================================================================
echo.
echo RESULTS:
echo   Tests Passed: %PASS_COUNT%
echo   Tests Failed: %FAIL_COUNT%
echo.

if %FAIL_COUNT% EQU 0 (
    echo ========================================================================
    echo   ✓✓✓ SUCCESS! ALL TRACES HAVE BEEN REMOVED! ✓✓✓
    echo ========================================================================
    echo.
    echo Your system is clean. All modifications have been successfully removed.
    echo.
    echo FINAL RECOMMENDATIONS:
    echo   1. Restart your computer
    echo   2. Run Windows Defender full scan
    echo   3. Check Task Manager for any unusual processes
    echo   4. Verify your startup items in Task Manager ^> Startup tab
    echo.
) else (
    echo ========================================================================
    echo   ⚠️ WARNING: %FAIL_COUNT% ISSUE(S) FOUND! ⚠️
    echo ========================================================================
    echo.
    echo Some traces were not removed. This may indicate:
    echo   1. restore.bat was not run as Administrator
    echo   2. Files are in use (processes still running)
    echo   3. Registry keys require additional permissions
    echo.
    echo RECOMMENDED ACTIONS:
    echo   1. Restart your computer in Safe Mode
    echo   2. Run restore.bat again as Administrator
    echo   3. Use Task Manager to end any suspicious processes
    echo   4. Manually check and remove any remaining entries
    echo.
    echo If issues persist, you may need to:
    echo   - Use regedit to manually remove registry keys
    echo   - Use Task Scheduler to manually remove tasks
    echo   - Use Services console to manually remove services
    echo.
)

echo.
echo Additional checks you can perform manually:
echo   1. Task Scheduler (taskschd.msc) - Check for suspicious tasks
echo   2. Services (services.msc) - Check for suspicious services
echo   3. Registry Editor (regedit) - Check HKCU\Software\Microsoft\Windows\CurrentVersion\Run
echo   4. Task Manager (Ctrl+Shift+Esc) - Startup tab and Processes tab
echo   5. Windows Security - Check protection history
echo.
echo Press any key to view detailed registry scan...
pause >nul

echo.
echo ============================================================================
echo                    DETAILED REGISTRY SCAN
echo ============================================================================
echo.

echo Scanning HKCU Run keys:
reg query "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" 2>nul | find /i "svchost" && echo [FOUND] Suspicious entry in Run key || echo [CLEAN] No suspicious entries in Run key

echo.
echo Scanning HKCU Classes:
reg query "HKCU\Software\Classes\ms-settings" 2>nul && echo [FOUND] ms-settings key exists || echo [CLEAN] ms-settings key removed
reg query "HKCU\Software\Classes\mscfile" 2>nul && echo [FOUND] mscfile key exists || echo [CLEAN] mscfile key removed
reg query "HKCU\Software\Classes\exefile" 2>nul && echo [FOUND] exefile key exists (check if legitimate) || echo [CLEAN] No exefile hijack

echo.
echo Scanning startup folders:
dir "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup" /b 2>nul | find /i "svchost" && echo [FOUND] Suspicious file in Startup folder || echo [CLEAN] Startup folder clean

echo.
echo Scanning scheduled tasks:
schtasks /query /fo LIST 2>nul | find /i "WindowsSecurityUpdate" && echo [FOUND] Suspicious scheduled task || echo [CLEAN] No suspicious scheduled tasks

echo.
echo Scanning services:
sc query state= all 2>nul | find /i "WindowsSecurity" && echo [FOUND] Suspicious service || echo [CLEAN] No suspicious services

echo.
echo ============================================================================
echo                    SCAN COMPLETE
echo ============================================================================
echo.

pause
exit /b %FAIL_COUNT%
