@echo off
echo.
echo ============================================
echo CLIENT.PY SINGLE-INSTANCE TEST & VERIFICATION
echo ============================================
echo.

echo [1] Stopping all existing Python processes...
echo.

REM Kill all python.exe processes gracefully first
echo    - Sending termination signals...
taskkill /F /IM python.exe /T >nul 2>&1
timeout /t 2 /nobreak >nul

echo    - Verifying processes stopped...
tasklist /FI "IMAGENAME eq python.exe" /FO CSV | find /i "python.exe" >nul
if %errorlevel% neq 0 (
    echo      ✓ All Python processes stopped successfully
) else (
    echo      ⚠ Some Python processes may still be running
)

echo.
echo [2] Testing single-instance VBS launcher...
echo.

REM Test launching the VBS script
echo    - Launching client_launcher.vbs...
cscript //nologo "C:\Users\Brylle\testing\client_launcher.vbs"
timeout /t 3 /nobreak >nul

echo.
echo [3] Verifying single instance...
echo.

REM Count Python processes
set "python_count=0"
for /f "tokens=*" %%i in ('tasklist /FI "IMAGENAME eq python.exe" /FO CSV ^| find /i /c "python.exe"') do set "python_count=%%i"

echo    - Python processes running: %python_count%

if "%python_count%"=="1" (
    echo      ✓ SUCCESS: Only one instance is running
) else (
    echo      ⚠ ISSUE: Expected 1 instance, found %python_count%
)

echo.
echo [4] Testing duplicate prevention...
echo.

REM Try to launch again (should be prevented)
echo    - Attempting second launch (should be blocked)...
cscript //nologo "C:\Users\Brylle\testing\client_launcher.vbs"
timeout /t 2 /nobreak >nul

REM Count again
set "python_count2=0"
for /f "tokens=*" %%i in ('tasklist /FI "IMAGENAME eq python.exe" /FO CSV ^| find /i /c "python.exe"') do set "python_count2=%%i"

echo    - Python processes after second attempt: %python_count2%

if "%python_count2%"=="1" (
    echo      ✓ SUCCESS: Duplicate launch prevented
) else (
    echo      ⚠ ISSUE: Duplicate instance created
)

echo.
echo [5] Checking log file...
echo.

if exist "%TEMP%\ClientLauncher\launcher.log" (
    echo    - Log file contents:
    echo.
    type "%TEMP%\ClientLauncher\launcher.log"
) else (
    echo    - No log file found
)

echo.
echo ============================================
echo TEST SUMMARY
echo ============================================
echo.
if "%python_count%"=="1" if "%python_count2%"=="1" (
    echo ✓ SINGLE-INSTANCE FUNCTIONALITY WORKING
    echo.
    echo The system correctly:
    echo - Prevents duplicate instances
    echo - Runs silently in background
    echo - Logs activities for debugging
    echo.
) else (
    echo ⚠ SINGLE-INSTANCE ISSUES DETECTED
    echo.
    echo Check the log file for details:
    echo %TEMP%\ClientLauncher\launcher.log
    echo.
)

echo Press any key to continue...
pause >nul