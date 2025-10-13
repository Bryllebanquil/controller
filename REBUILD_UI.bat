@echo off
echo ====================================================================
echo Rebuilding Agent Controller UI v2.1
echo ====================================================================
echo.

cd "agent-controller ui v2.1"

echo [1/3] Installing dependencies...
call npm install
if errorlevel 1 (
    echo ERROR: npm install failed!
    pause
    exit /b 1
)

echo.
echo [2/3] Building production bundle...
call npm run build
if errorlevel 1 (
    echo ERROR: npm build failed!
    pause
    exit /b 1
)

echo.
echo [3/3] Build complete!
echo.
echo ====================================================================
echo SUCCESS! UI has been rebuilt.
echo ====================================================================
echo.
echo Next steps:
echo 1. Restart the controller (Ctrl+C then run: python controller.py)
echo 2. Hard refresh your browser (Ctrl+Shift+R)
echo 3. Test with: ls
echo.
echo The output should now display properly formatted with line breaks!
echo ====================================================================
pause
