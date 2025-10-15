@echo off
echo ============================================================================
echo Python Agent - Dependency Installation Script
echo ============================================================================
echo.

:: Check Python version
python --version
echo.

echo [STEP 1] Installing CRITICAL packages (required for basic operation)...
echo.
python -m pip install --upgrade pip
python -m pip install python-socketio python-engineio requests urllib3 certifi websocket-client

echo.
echo [STEP 2] Installing Windows-specific packages...
echo.
python -m pip install pywin32 psutil

echo.
echo [STEP 3] Installing screen capture and automation packages...
echo.
python -m pip install mss Pillow numpy pynput pyautogui pygame

echo.
echo [STEP 4] Installing optional packages (may fail on Python 3.14)...
echo.
python -m pip install opencv-python aiortc Flask Flask-SocketIO aiohttp

echo.
echo ============================================================================
echo Installation complete!
echo ============================================================================
echo.
echo If any packages failed to install, that's OK - the agent will still work
echo with reduced functionality.
echo.
echo Now run: python client.py
echo.
pause
