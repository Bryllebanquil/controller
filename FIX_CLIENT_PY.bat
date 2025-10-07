@echo off
REM Script to fix client.py by pulling the correct version from git

echo ================================================================================
echo FIXING CLIENT.PY - PULLING CORRECT VERSION FROM GIT
echo ================================================================================
echo.

cd "C:\Users\Brylle\render deploy\controller"

echo Current branch:
git branch

echo.
echo Pulling latest version with fixes...
git fetch origin cursor/debug-ui-download-upload-visibility-72a5
git checkout cursor/debug-ui-download-upload-visibility-72a5
git pull origin cursor/debug-ui-download-upload-visibility-72a5

echo.
echo Verifying fix...
findstr /n "def stream_screen_webrtc_or_socketio" client.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo SUCCESS! Function found in client.py
    echo.
    echo Now installing packages...
    pip install numpy opencv-python mss
    echo.
    echo DONE! Now run: python client.py
) else (
    echo.
    echo ERROR: Function still not found. Manual fix needed.
)

pause
