@echo off
REM Build and Test Script for Popup Notification Fix (Windows)

echo ==================================================
echo 🔧 Building Frontend with Popup Notification Fix
echo ==================================================
echo.

REM Navigate to frontend directory
cd "agent-controller ui v2.1-modified"

REM Install dependencies
echo 📦 Installing dependencies...
call npm install

REM Build the frontend
echo.
echo 🏗️  Building frontend...
call npm run build

REM Check if build succeeded
if %ERRORLEVEL% EQU 0 (
    echo.
    echo ✅ Build successful!
    echo.
    echo 📁 Build output:
    dir build
    echo.
    echo ==================================================
    echo 🎉 Frontend built successfully!
    echo ==================================================
    echo.
    echo Next steps:
    echo 1. Test locally: python controller.py
    echo 2. Open: http://localhost:8080
    echo 3. Run: python test_notifications.py
    echo 4. Deploy: git add . ^&^& git commit -m "Fix popup notifications" ^&^& git push
    echo.
) else (
    echo.
    echo ❌ Build failed! Check errors above.
    exit /b 1
)

cd ..
