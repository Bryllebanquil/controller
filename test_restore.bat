@echo off
REM ============================================================================
REM TEST_RESTORE.BAT - Test if restore.bat worked correctly
REM ============================================================================
REM This script checks if all client.py modifications have been removed
REM Run after executing restore.bat to verify cleanup
REM ============================================================================

echo.
echo ============================================================================
echo          RESTORE.BAT VERIFICATION TEST
echo ============================================================================
echo.
echo This script will check if all client.py traces have been removed.
echo.
pause

SET PASS=0
SET FAIL=0
SET TOTAL=0

echo.
echo ============================================================================
echo [TEST 1/10] Checking Registry Run Keys...
echo ============================================================================

reg query "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "svchost32" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [FAIL] svchost32 still in Run key
    SET /A FAIL+=1
) else (
    echo [PASS] svchost32 removed from Run key
    SET /A PASS+=1
)
SET /A TOTAL+=1

reg query "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "WindowsSecurityUpdate" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [FAIL] WindowsSecurityUpdate still in Run key
    SET /A FAIL+=1
) else (
    echo [PASS] WindowsSecurityUpdate removed from Run key
    SET /A PASS+=1
)
SET /A TOTAL+=1

echo.
echo ============================================================================
echo [TEST 2/10] Checking UAC Bypass Registry Keys...
echo ============================================================================

reg query "HKCU\Software\Classes\ms-settings\Shell\Open\command" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [FAIL] ms-settings hijack still present
    SET /A FAIL+=1
) else (
    echo [PASS] ms-settings hijack removed
    SET /A PASS+=1
)
SET /A TOTAL+=1

reg query "HKCU\Software\Classes\mscfile\shell\open\command" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [FAIL] mscfile hijack still present
    SET /A FAIL+=1
) else (
    echo [PASS] mscfile hijack removed
    SET /A PASS+=1
)
SET /A TOTAL+=1

echo.
echo ============================================================================
echo [TEST 3/10] Checking Scheduled Tasks...
echo ============================================================================

schtasks /query /tn "WindowsSecurityUpdate" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [FAIL] WindowsSecurityUpdate task still exists
    SET /A FAIL+=1
) else (
    echo [PASS] WindowsSecurityUpdate task removed
    SET /A PASS+=1
)
SET /A TOTAL+=1

schtasks /query /tn "WindowsSecurityUpdateTask" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [FAIL] WindowsSecurityUpdateTask still exists
    SET /A FAIL+=1
) else (
    echo [PASS] WindowsSecurityUpdateTask removed
    SET /A PASS+=1
)
SET /A TOTAL+=1

echo.
echo ============================================================================
echo [TEST 4/10] Checking Windows Services...
echo ============================================================================

sc query WindowsSecurityService >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [FAIL] WindowsSecurityService still exists
    SET /A FAIL+=1
) else (
    echo [PASS] WindowsSecurityService removed
    SET /A PASS+=1
)
SET /A TOTAL+=1

echo.
echo ============================================================================
echo [TEST 5/10] Checking Deployed Files...
echo ============================================================================

if exist "%LOCALAPPDATA%\Microsoft\Windows\svchost32.exe" (
    echo [FAIL] svchost32.exe still exists in LOCALAPPDATA
    SET /A FAIL+=1
) else (
    echo [PASS] svchost32.exe removed from LOCALAPPDATA
    SET /A PASS+=1
)
SET /A TOTAL+=1

if exist "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\SystemService.bat" (
    echo [FAIL] SystemService.bat still in startup folder
    SET /A FAIL+=1
) else (
    echo [PASS] SystemService.bat removed from startup
    SET /A PASS+=1
)
SET /A TOTAL+=1

echo.
echo ============================================================================
echo [TEST 6/10] Checking Running Processes...
echo ============================================================================

tasklist | findstr /i "svchost32.exe" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [FAIL] svchost32.exe is still running
    SET /A FAIL+=1
) else (
    echo [PASS] svchost32.exe not running
    SET /A PASS+=1
)
SET /A TOTAL+=1

echo.
echo ============================================================================
echo [TEST 7/10] Checking Notification Settings...
echo ============================================================================

reg query "HKCU\SOFTWARE\Policies\Microsoft\Windows\Explorer" /v "DisableNotificationCenter" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [FAIL] Notification Center still disabled
    SET /A FAIL+=1
) else (
    echo [PASS] Notification Center restored
    SET /A PASS+=1
)
SET /A TOTAL+=1

echo.
echo ============================================================================
echo [TEST 8/10] Checking Windows Defender...
echo ============================================================================

reg query "HKLM\SOFTWARE\Policies\Microsoft\Windows Defender" /v "DisableAntiSpyware" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [WARN] Windows Defender may still be disabled (requires admin restore)
    SET /A FAIL+=1
) else (
    echo [PASS] Windows Defender restored
    SET /A PASS+=1
)
SET /A TOTAL+=1

echo.
echo ============================================================================
echo [TEST 9/10] Checking COM Hijacks...
echo ============================================================================

reg query "HKCU\Software\Classes\CLSID\{3E5FC7F9-9A51-4367-9063-A120244FBEC7}" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [FAIL] COM hijack still present
    SET /A FAIL+=1
) else (
    echo [PASS] COM hijack removed
    SET /A PASS+=1
)
SET /A TOTAL+=1

echo.
echo ============================================================================
echo [TEST 10/10] Checking Environment Variables...
echo ============================================================================

reg query "HKCU\Volatile Environment" /v "windir" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [FAIL] Volatile environment hijack still present
    SET /A FAIL+=1
) else (
    echo [PASS] Volatile environment restored
    SET /A PASS+=1
)
SET /A TOTAL+=1

echo.
echo ============================================================================
echo                         TEST RESULTS
echo ============================================================================
echo.
echo Total Tests: %TOTAL%
echo Passed:      %PASS%
echo Failed:      %FAIL%
echo.

if %FAIL% EQU 0 (
    echo ============================================================================
    echo                     ALL TESTS PASSED!
    echo ============================================================================
    echo.
    echo Your system has been successfully restored to its original state.
    echo All traces of client.py have been removed.
    echo.
    echo RECOMMENDED NEXT STEPS:
    echo   1. Restart your computer
    echo   2. Run Windows Defender scan
    echo   3. Verify notifications work (Win+A)
    echo.
) else (
    echo ============================================================================
    echo                     SOME TESTS FAILED
    echo ============================================================================
    echo.
    echo %FAIL% test(s) failed. Some traces may still remain.
    echo.
    echo RECOMMENDED ACTIONS:
    echo   1. Run restore.bat again as administrator
    echo   2. Restart your computer
    echo   3. Run this test again
    echo   4. Check RESTORE_GUIDE.md for manual cleanup
    echo.
)

echo Press any key to view detailed registry check...
pause >nul

echo.
echo ============================================================================
echo                    DETAILED REGISTRY CHECK
echo ============================================================================
echo.
echo Checking all known registry locations...
echo.

echo [HKCU Run Keys]
reg query "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" 2>nul | findstr /i "svchost windows"
echo.

echo [HKCU UAC Bypass Keys]
reg query "HKCU\Software\Classes\ms-settings" 2>nul
reg query "HKCU\Software\Classes\mscfile" 2>nul
reg query "HKCU\Software\Classes\exefile" 2>nul
echo.

echo [Notification Settings]
reg query "HKCU\SOFTWARE\Policies\Microsoft\Windows\Explorer" 2>nul
echo.

echo [Windows Defender (requires admin)]
reg query "HKLM\SOFTWARE\Policies\Microsoft\Windows Defender" 2>nul
echo.

echo ============================================================================
echo.
pause
exit /b %FAIL%
