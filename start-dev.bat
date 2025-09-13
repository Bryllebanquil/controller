@echo off
REM Windows Development startup script for Neural Control Hub
REM This script starts both the backend and frontend in development mode

echo 🚀 Starting Neural Control Hub Development Environment
echo ==================================================

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Check if Node.js is available
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Node.js is not installed or not in PATH
    pause
    exit /b 1
)

echo 📦 Installing Python dependencies...
pip install -r requirements.txt

echo 📦 Installing Node.js dependencies...
cd "agent-controller ui v2.1"
npm install
cd ..

echo 🔧 Starting Backend Server (Port 8080)...
start "Backend Server" cmd /k "python controller.py"

REM Wait a moment for backend to start
timeout /t 5 /nobreak >nul

echo 🎨 Starting Frontend Development Server (Port 3000)...
cd "agent-controller ui v2.1"
start "Frontend Server" cmd /k "npm run dev"
cd ..

echo 🤖 Starting Agent Client...
REM Load client environment variables
if exist "client.env" (
    for /f "usebackq tokens=1,2 delims==" %%a in ("client.env") do set %%a=%%b
)
start "Agent Client" cmd /k "python client.py --mode agent --no-ssl"

echo.
echo ✅ Development Environment Started!
echo ==================================
echo 🌐 Backend API: http://localhost:8080
echo 🎨 Frontend UI: http://localhost:3000
echo 🤖 Agent Client: Connected to controller
echo.
echo Press any key to exit this script (servers will continue running)
pause >nul