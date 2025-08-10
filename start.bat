@echo off
title Main.py Startup Script
color 0A

echo.
echo ========================================
echo    Main.py Startup Script
echo ========================================
echo.

:menu
echo Choose an option:
echo.
echo 1. Run as Agent (default)
echo 2. Run as Controller
echo 3. Run Both (Agent + Controller)
echo 4. Check Dependencies
echo 5. Help
echo 6. Exit
echo.
set /p choice="Enter your choice (1-6): "

if "%choice%"=="1" goto agent
if "%choice%"=="2" goto controller
if "%choice%"=="3" goto both
if "%choice%"=="4" goto check
if "%choice%"=="5" goto help
if "%choice%"=="6" goto exit
goto invalid

:agent
echo.
echo Starting as Agent...
echo.
python main.py
goto end

:controller
echo.
echo Starting as Controller...
echo.
python main.py --mode controller
goto end

:both
echo.
echo Starting Both (Agent + Controller)...
echo.
python main.py --mode both
goto end

:check
echo.
echo Checking dependencies...
echo.
python start.py --check
echo.
pause
goto menu

:help
echo.
echo ========================================
echo              HELP
echo ========================================
echo.
echo Agent Mode:
echo   - Connects to Socket.IO server
echo   - Waits for remote commands
echo   - Can stream screen, audio, camera
echo   - Supports WebRTC for low-latency
echo.
echo Controller Mode:
echo   - Starts web server (HTTP/HTTPS)
echo   - Provides dashboard interface
echo   - Controls connected agents
echo   - Available at http://localhost:8080
echo.
echo Both Mode:
echo   - Runs controller in background
echo   - Runs agent in main thread
echo   - Self-contained operation
echo.
echo Troubleshooting:
echo   - Install dependencies: pip install -r requirements.txt
echo   - Run as Administrator for full functionality
echo   - Check firewall settings
echo   - Verify Python 3.8+ is installed
echo.
pause
goto menu

:invalid
echo.
echo Invalid choice. Please enter 1-6.
echo.
pause
goto menu

:exit
echo.
echo Goodbye!
exit /b 0

:end
echo.
echo Application stopped.
pause
goto menu