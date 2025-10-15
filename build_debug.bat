@echo off
REM ========================================
REM Build client.py in DEBUG mode
REM (Shows console for troubleshooting)
REM ========================================

echo.
echo ╔══════════════════════════════════════════════════════════════════════════════╗
echo ║                    DEBUG BUILD - WITH CONSOLE WINDOW                         ║
echo ╚══════════════════════════════════════════════════════════════════════════════╝
echo.

echo Building in DEBUG mode...
echo This will create an .exe WITH a console window for error messages.
echo.

pyinstaller ^
  --onefile ^
  --console ^
  --debug=all ^
  --name "WindowsSecurityUpdate_DEBUG" ^
  --hidden-import=socketio ^
  --hidden-import=engineio ^
  --collect-all socketio ^
  --collect-all engineio ^
  client.py

if errorlevel 1 (
    echo.
    echo [ERROR] Debug build failed!
    pause
    exit /b 1
)

echo.
echo ╔══════════════════════════════════════════════════════════════════════════════╗
echo ║                       DEBUG BUILD COMPLETE! ✅                               ║
echo ╚══════════════════════════════════════════════════════════════════════════════╝
echo.
echo Debug executable: dist\WindowsSecurityUpdate_DEBUG.exe
echo.
echo Run this .exe to see console output and error messages.
echo.

pause
