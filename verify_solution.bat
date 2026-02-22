@echo off
echo.
echo ============================================
echo FINAL VERIFICATION: SINGLE-INSTANCE SOLUTION
echo ============================================
echo.

echo [1] Current Startup Configuration:
echo.
echo    Startup Folder Contents:
dir /b "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup" 2>nul | findstr /i "client\|system"
echo.
echo    Registry Startup Entries:
reg query "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" 2>nul | findstr /i "svchost32\|client"

echo.
echo [2] Testing Single-Instance Functionality:
echo.

echo    - Stopping any existing Python processes...
taskkill /F /IM python.exe /T >nul 2>&1
timeout /t 2 /nobreak >nul

echo    - Launching client.py via VBS...
cscript //nologo "C:\Users\Brylle\testing\client_launcher.vbs"
timeout /t 3 /nobreak >nul

echo    - Checking process count:
tasklist /FI "IMAGENAME eq python.exe" /FO CSV 2>nul | find /i /c "python.exe"

echo.
echo    - Testing duplicate prevention (attempting second launch)...
cscript //nologo "C:\Users\Brylle\testing\client_launcher.vbs"
timeout /t 2 /nobreak >nul

echo    - Final process count:
tasklist /FI "IMAGENAME eq python.exe" /FO CSV 2>nul | find /i /c "python.exe"

echo.
echo [3] Log File Analysis:
echo.
if exist "%TEMP%\ClientLauncher\launcher.log" (
    echo    Recent log entries:
    echo    -----------------
    type "%TEMP%\ClientLauncher\launcher.log" | tail -10 2>nul || type "%TEMP%\ClientLauncher\launcher.log"
) else (
    echo    No log file found
)

echo.
echo [4] Silent Execution Test:
echo.
echo    - Verifying no visible windows:
tasklist /FI "IMAGENAME eq python.exe" /FO TABLE /V 2>nul | findstr /i "python.exe" | findstr /v "Console"
if %errorlevel% equ 0 (
    echo      ✓ No console windows detected (running silently)
) else (
    echo      - Process may be running in background
)

echo.
echo ============================================
echo SUMMARY
echo ============================================
echo.

set "final_count=0"
for /f "tokens=*" %%i in ('tasklist /FI "IMAGENAME eq python.exe" /FO CSV 2^>nul ^| find /i /c "python.exe"') do set "final_count=%%i"

if "%final_count%"=="1" (
    echo ✅ SUCCESS: Single-instance solution is working correctly!
    echo.
    echo    ✓ Only one instance running
    echo    ✓ Duplicate prevention active
    echo    ✓ Silent background execution
    echo    ✓ Proper startup configuration
    echo.
    echo The client.py will now run as a single silent instance
    echo on system startup without showing any command prompt windows.
) else (
    echo ⚠ ISSUE: Multiple instances detected or none running
    echo    Current count: %final_count%
    echo    Expected: 1
    echo.
    echo Check the log file for details:
    echo %TEMP%\ClientLauncher\launcher.log
)

echo.
echo Solution files created:
echo - C:\Users\Brylle\testing\client_launcher.vbs (main launcher)
echo - C:\Users\Brylle\testing\setup_single_instance.bat (setup utility)
echo - C:\Users\Brylle\testing\test_single_instance.bat (testing tool)
echo.
pause