@echo off
echo ================================================================================
echo  INSTALLING ALL REQUIRED DEPENDENCIES
echo ================================================================================
echo.
echo This will install all packages needed for the Python Agent
echo.
pause

echo.
echo [1/6] Installing pywin32 (Windows API access)...
pip install pywin32
echo.

echo [2/6] Installing python-socketio (Controller communication)...
pip install python-socketio
echo.

echo [3/6] Installing numpy (Array operations)...
pip install numpy
echo.

echo [4/6] Installing opencv-python (Video processing)...
pip install opencv-python
echo.

echo [5/6] Installing pygame (GUI features)...
pip install pygame
echo.

echo [6/6] Installing aiohttp (WebRTC support)...
pip install aiohttp
echo.

echo ================================================================================
echo  INSTALLATION COMPLETE!
echo ================================================================================
echo.
echo All dependencies have been installed successfully.
echo You can now run: python client.py
echo.
pause
