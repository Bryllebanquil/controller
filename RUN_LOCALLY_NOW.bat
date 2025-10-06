@echo off
REM ========================================================================
REM QUICK FIX: Run Controller Locally (2 Minutes)
REM ========================================================================

echo.
echo ========================================================================
echo   STOPPING CURRENT CLIENT (if running)
echo ========================================================================
echo.
echo Press Ctrl+C in the client.py window to stop it first!
echo.
pause

echo.
echo ========================================================================
echo   STARTING LOCAL CONTROLLER (with updated frontend)
echo ========================================================================
echo.

REM Set admin password
set ADMIN_PASSWORD=Admin123

REM Start controller
echo Starting controller at http://localhost:8080...
echo.
python controller.py

REM If controller stops, pause to see error
pause
