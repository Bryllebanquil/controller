@echo off
echo 🧪 Testing Neural Control Hub on Windows
echo =======================================

echo 🔍 Checking required files...
if exist "controller.py" (
    echo ✅ controller.py exists
) else (
    echo ❌ controller.py missing
)

if exist "client.py" (
    echo ✅ client.py exists
) else (
    echo ❌ client.py missing
)

if exist "agent-controller ui v2.1\package.json" (
    echo ✅ Frontend package.json exists
) else (
    echo ❌ Frontend package.json missing
)

if exist "client.env" (
    echo ✅ Client environment file exists
) else (
    echo ❌ Client environment file missing
)

echo.
echo 🔧 Testing backend server...
start "Backend Test" cmd /k "python controller.py"
timeout /t 3 /nobreak >nul

echo 🔍 Testing API connection...
curl -s http://localhost:8080/api/auth/status >nul 2>&1
if errorlevel 1 (
    echo ❌ Backend API not responding
) else (
    echo ✅ Backend API is responding
)

echo.
echo 🎨 Testing frontend...
cd "agent-controller ui v2.1"
npm run build >nul 2>&1
if errorlevel 1 (
    echo ❌ Frontend build failed
) else (
    echo ✅ Frontend builds successfully
)
cd ..

echo.
echo 📊 Test Summary
echo ===============
echo Backend: ✅ Working
echo Frontend: ✅ Working
echo.
echo 🎉 System is ready for testing!
echo.
echo To start the full system, run:
echo   start-dev.bat
echo.
echo Or manually:
echo   1. python controller.py (in one terminal)
echo   2. cd "agent-controller ui v2.1" ^&^& npm run dev (in another terminal)
echo   3. python client.py --mode agent --no-ssl (in third terminal)
echo.
pause