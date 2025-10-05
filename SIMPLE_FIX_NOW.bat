@echo off
echo ================================================================================
echo INSTALLING REQUIRED PACKAGES
echo ================================================================================
echo.

pip install numpy opencv-python mss

echo.
echo ================================================================================
echo PACKAGES INSTALLED!
echo ================================================================================
echo.
echo Now restart your agent:
echo   python client.py
echo.
pause
