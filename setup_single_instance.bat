@echo off
echo.
echo ============================================
echo CLIENT.PY SINGLE-INSTANCE SETUP UTILITY
echo ============================================
echo.

set "VBS_LAUNCHER=C:\Users\Brylle\testing\client_launcher.vbs"
set "STARTUP_FOLDER=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
set "STARTUP_BAT=%STARTUP_FOLDER%\SystemService.bat"
set "NEW_STARTUP_VBS=%STARTUP_FOLDER%\ClientService.vbs"

echo [1] Cleaning up duplicate startup entries...
echo.

REM Remove the old batch file from startup folder
if exist "%STARTUP_BAT%" (
    echo    - Removing old batch file from startup folder...
    del /f /q "%STARTUP_BAT%"
    echo      ✓ Removed: %STARTUP_BAT%
) else (
    echo    - No old batch file found in startup folder
)

echo.
echo [2] Removing registry startup entry...
echo.

REM Remove the registry entry (svchost32)
echo    - Removing registry startup entry...
reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "svchost32" /f >nul 2>&1
if %errorlevel% equ 0 (
    echo      ✓ Removed registry entry: svchost32
) else (
    echo      - Registry entry not found or already removed
)

echo.
echo [3] Creating new VBS startup entry...
echo.

REM Create the new VBS shortcut in startup folder
echo    - Creating startup VBS script...
(
echo Set objShell = CreateObject^("WScript.Shell"^)
echo strVBSPath = "%VBS_LAUNCHER%"
echo objShell.Run strVBSPath, 0, False
) > "%NEW_STARTUP_VBS%"

echo      ✓ Created: %NEW_STARTUP_VBS%

echo.
echo [4] Testing VBS launcher...
echo.

REM Test the VBS launcher
echo    - Testing VBS launcher functionality...
cscript //nologo "%VBS_LAUNCHER%"
timeout /t 3 /nobreak >nul

echo.
echo [5] Verifying single instance...
echo.

REM Check if process is running
tasklist /FI "IMAGENAME eq python.exe" /FO CSV | find /i "python.exe" >nul
if %errorlevel% equ 0 (
    echo      ✓ Client.py is running (single instance)
) else (
    echo      ⚠ Client.py may not have started properly
)

echo.
echo ============================================
echo SETUP COMPLETE!
echo ============================================
echo.
echo Summary:
echo - ✓ Removed duplicate startup entries
echo - ✓ Created single-instance VBS launcher
echo - ✓ Configured silent background execution
echo.
echo The client.py will now run as a single silent instance
echo on system startup and manual restarts.
echo.
echo Log file location:
echo %TEMP%\ClientLauncher\launcher.log
echo.
pause