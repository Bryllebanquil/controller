@echo off
echo ========================================
echo WebRTC Optimized Setup for Windows 11 VM
echo ========================================
echo.
echo This script will install all dependencies needed for
echo SMOOTH, LOW-LATENCY WebRTC streaming (<1 second delay)
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

echo ✅ Python found:
python --version

REM Check if pip is available
pip --version >nul 2>&1
if errorlevel 1 (
    echo ❌ ERROR: pip is not available
    echo Please ensure pip is installed with Python
    pause
    exit /b 1
)

echo ✅ pip found:
pip --version

echo.
echo ========================================
echo Installing WebRTC Dependencies...
echo ========================================

REM Upgrade pip first
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install core WebRTC dependencies (CRITICAL for smooth streaming)
echo.
echo Installing core WebRTC libraries...
pip install aiortc>=0.9.0
pip install aiohttp>=3.8.0
pip install python-socketio[client]>=5.7.0

REM Install media capture libraries (CRITICAL for smooth video)
echo.
echo Installing media capture libraries...
pip install mss>=6.1.0
pip install opencv-python>=4.5.0
pip install PyAudio>=0.2.11
pip install numpy>=1.21.0
pip install Pillow>=8.3.0

REM Install alternative capture backends
echo.
echo Installing alternative capture backends...
pip install dxcam>=1.0.0
pip install pyautogui>=0.9.53

REM Install performance optimization libraries
echo.
echo Installing performance optimization libraries...
pip install psutil>=5.8.0
pip install asyncio-mqtt>=0.11.0

REM Install input control libraries
echo.
echo Installing input control libraries...
pip install pynput>=1.7.0
pip install keyboard>=0.13.5

REM Install networking and security
echo.
echo Installing networking and security libraries...
pip install websockets>=10.0
pip install requests>=2.25.0
pip install cryptography>=3.4.0

REM Install Windows-specific libraries
echo.
echo Installing Windows-specific libraries...
pip install pywin32>=300
pip install wmi>=1.5.1

echo.
echo ========================================
echo Verifying WebRTC Installation...
echo ========================================

REM Test if aiortc is properly installed
python -c "import aiortc; print('✅ aiortc imported successfully')" 2>nul
if errorlevel 1 (
    echo ❌ ERROR: aiortc failed to import
    echo WebRTC streaming will NOT work properly
    echo.
    echo Troubleshooting:
    echo 1. Check if you have Visual C++ redistributable installed
    echo 2. Try: pip install --upgrade aiortc
    echo 3. Restart your terminal/command prompt
) else (
    echo ✅ aiortc is working correctly
)

REM Test other critical dependencies
python -c "import cv2; print('✅ OpenCV imported successfully')" 2>nul
python -c "import mss; print('✅ MSS screen capture imported successfully')" 2>nul
python -c "import pyaudio; print('✅ PyAudio imported successfully')" 2>nul

echo.
echo ========================================
echo Creating Startup Scripts...
echo ========================================

REM Create optimized startup script
echo @echo off > start-webrtc-optimized.bat
echo echo Starting WebRTC Agent with Optimized Settings... >> start-webrtc-optimized.bat
echo echo. >> start-webrtc-optimized.bat
echo echo WebRTC Configuration: >> start-webrtc-optimized.bat
echo echo - Target FPS: 30 >> start-webrtc-optimized.bat
echo echo - Ultra-low latency mode: Enabled >> start-webrtc-optimized.bat
echo echo - Hardware acceleration: Enabled >> start-webrtc-optimized.bat
echo echo - Adaptive bitrate: Enabled >> start-webrtc-optimized.bat
echo echo. >> start-webrtc-optimized.bat
echo python main.py --webrtc-optimized --ultra-low-latency >> start-webrtc-optimized.bat
echo pause >> start-webrtc-optimized.bat

REM Create test script
echo @echo off > test-webrtc.bat
echo echo Testing WebRTC Installation... >> test-webrtc.bat
echo echo. >> test-webrtc.bat
echo python -c "import aiortc; print('WebRTC: OK'); import cv2; print('OpenCV: OK'); import mss; print('MSS: OK'); import pyaudio; print('PyAudio: OK'); print('All dependencies ready for smooth streaming!')" >> test-webrtc.bat
echo echo. >> test-webrtc.bat
echo pause >> test-webrtc.bat

echo ✅ Created startup scripts:
echo   - start-webrtc-optimized.bat (for production use)
echo   - test-webrtc.bat (to verify installation)

echo.
echo ========================================
echo WebRTC Setup Complete!
echo ========================================
echo.
echo To test your setup:
echo   1. Run: test-webrtc.bat
echo   2. If all tests pass, run: start-webrtc-optimized.bat
echo.
echo Expected performance:
echo   - Screen capture: 30 FPS
echo   - Latency: <1 second
echo   - Smooth streaming with adaptive quality
echo.
echo If you experience issues:
echo   1. Check Windows Defender isn't blocking Python
echo   2. Ensure you have Visual C++ redistributable
echo   3. Try running as Administrator
echo.
pause