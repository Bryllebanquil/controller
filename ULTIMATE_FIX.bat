@echo off
echo ================================================================================
echo   ULTIMATE FIX - Fix ALL Import Issues
echo ================================================================================
echo.
echo This will fix Python 3.13 + eventlet + socketio compatibility issues
echo.
pause

echo.
echo [STEP 1] Uninstalling incompatible versions...
echo ================================================================================
python -m pip uninstall -y python-socketio python-engineio eventlet

echo.
echo [STEP 2] Installing compatible versions...
echo ================================================================================
python -m pip install eventlet==0.33.3
python -m pip install python-engineio==4.8.0
python -m pip install python-socketio==5.7.0

echo.
echo [STEP 3] Installing other dependencies...
echo ================================================================================
python -m pip install pywin32
python -m pip install numpy
python -m pip install opencv-python
python -m pip install pygame
python -m pip install aiohttp

echo.
echo ================================================================================
echo   INSTALLATION COMPLETE!
echo ================================================================================
echo.
echo Testing imports...
python test_imports.py

echo.
echo ================================================================================
echo   ALL DONE!
echo ================================================================================
echo.
echo You can now run: python client.py
echo.
pause
