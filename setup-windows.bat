@echo off
REM Windows 11 Oracle VM Setup Script for WebRTC Agent
REM Run as Administrator for best results

echo ========================================
echo    WebRTC Agent Setup for Windows 11
echo ========================================
echo.

REM Check if running as Administrator
net session >nul 2>&1
if %errorLevel% == 0 (
    echo [OK] Running as Administrator
) else (
    echo [WARNING] Not running as Administrator
    echo Some features may not work properly
    echo.
    pause
)

echo.
echo [1/6] Checking Python installation...
python --version >nul 2>&1
if %errorLevel% == 0 (
    echo [OK] Python is installed
    python --version
) else (
    echo [ERROR] Python not found!
    echo Please install Python 3.7+ from https://python.org
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

echo.
echo [2/6] Checking pip installation...
pip --version >nul 2>&1
if %errorLevel% == 0 (
    echo [OK] pip is installed
    pip --version
) else (
    echo [ERROR] pip not found!
    echo Please reinstall Python with pip included
    pause
    exit /b 1
)

echo.
echo [3/6] Upgrading pip...
python -m pip install --upgrade pip

echo.
echo [4/6] Creating virtual environment...
if exist "webrtc-env" (
    echo [INFO] Virtual environment already exists, removing...
    rmdir /s /q "webrtc-env"
)
python -m venv webrtc-env

echo.
echo [5/6] Activating virtual environment and installing dependencies...
call webrtc-env\Scripts\activate.bat
pip install --upgrade pip
pip install -r requirements-windows.txt

echo.
echo [6/6] Creating startup scripts...
echo @echo off > start-agent.bat
echo echo Starting WebRTC Agent... >> start-agent.bat
echo cd /d "%~dp0" >> start-agent.bat
echo call webrtc-env\Scripts\activate.bat >> start-agent.bat
echo python main.py >> start-agent.bat
echo pause >> start-agent.bat

echo @echo off > start-agent-admin.bat
echo echo Starting WebRTC Agent as Administrator... >> start-agent-admin.bat
echo cd /d "%~dp0" >> start-agent-admin.bat
echo call webrtc-env\Scripts\activate.bat >> start-agent-admin.bat
echo python main.py --admin >> start-agent-admin.bat
echo pause >> start-agent-admin.bat

echo @echo off > test-dependencies.bat
echo echo Testing WebRTC Agent Dependencies... >> test-dependencies.bat
echo cd /d "%~dp0" >> test-dependencies.bat
echo call webrtc-env\Scripts\activate.bat >> test-dependencies.bat
echo echo Testing imports... >> test-dependencies.bat
echo python -c "import aiortc; print('WebRTC: OK')" >> test-dependencies.bat
echo python -c "import pyaudio; print('Audio: OK')" >> test-dependencies.bat
echo python -c "import mss; print('Screen Capture: OK')" >> test-dependencies.bat
echo python -c "import cv2; print('OpenCV: OK')" >> test-dependencies.bat
echo echo All tests completed! >> test-dependencies.bat
echo pause >> test-dependencies.bat

echo.
echo ========================================
echo           Setup Complete!
echo ========================================
echo.
echo [NEXT STEPS]
echo 1. Edit main.py and update CONTROLLER_HOST to your controller IP
echo 2. Test dependencies: run test-dependencies.bat
echo 3. Start the agent: run start-agent.bat
echo.
echo [TROUBLESHOOTING]
echo - If you get permission errors, run start-agent-admin.bat
echo - Check Windows Defender isn't blocking Python
echo - Ensure your VM has internet access
echo.
echo [FILES CREATED]
echo - webrtc-env\ (Python virtual environment)
echo - start-agent.bat (Normal startup)
echo - start-agent-admin.bat (Administrator startup)
echo - test-dependencies.bat (Dependency testing)
echo.
pause