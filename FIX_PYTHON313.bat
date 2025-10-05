@echo off
echo ================================================================================
echo   PYTHON 3.13 COMPATIBILITY FIX
echo ================================================================================
echo.
echo This will install Python 3.13 compatible versions of:
echo   - eventlet ^>= 0.35.0 (Python 3.13 compatible)
echo   - python-engineio ^>= 4.8.0
echo   - python-socketio ^>= 5.12.0 (compatible with flask-socketio)
echo.
pause

echo.
echo [1/3] Uninstalling old versions...
pip uninstall -y python-socketio python-engineio eventlet

echo.
echo [2/3] Installing Python 3.13 compatible versions...
pip install eventlet>=0.35.0 python-engineio>=4.8.0 python-socketio>=5.12.0

echo.
echo [3/3] Installing other dependencies...
pip install pywin32 numpy opencv-python pygame aiohttp

echo.
echo ================================================================================
echo   INSTALLATION COMPLETE!
echo ================================================================================
echo.
echo Now running the agent...
echo.
python client.py
