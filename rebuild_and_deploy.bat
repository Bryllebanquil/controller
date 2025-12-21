@echo off
echo ========================================
echo REBUILD UI AND DEPLOY TO RENDER
echo ========================================
echo.

echo Step 1/5: Navigating to UI directory...
cd "agent-controller ui v2.1"
if errorlevel 1 (
    echo ERROR: Failed to navigate to UI directory!
    pause
    exit /b 1
)

echo Step 2/5: Installing dependencies...
call npm install
if errorlevel 1 (
    echo ERROR: npm install failed!
    pause
    exit /b 1
)

echo Step 3/5: Building production UI...
call npm run build
if errorlevel 1 (
    echo ERROR: npm run build failed!
    pause
    exit /b 1
)

echo Step 4/5: Navigating back to root...
cd ..

echo Step 5/5: Committing and pushing to Git...
git add -A
git commit -m "Fix file manager: add total_size and rebuild UI with download handling"
git push origin main

if errorlevel 1 (
    echo.
    echo WARNING: Git push may have failed.
    echo Please check your Git credentials and internet connection.
    echo.
) else (
    echo.
    echo ========================================
    echo SUCCESS! Deployment triggered!
    echo ========================================
    echo.
    echo Next steps:
    echo 1. Go to Render dashboard
    echo 2. Wait for deployment to complete
    echo 3. Restart your agent: python client.py
    echo 4. Test upload/download in browser!
    echo.
)

pause
