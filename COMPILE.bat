@echo off
echo ===============================================
echo  Installing packages and compiling svchost.exe
echo ===============================================
echo.

echo [1/5] Installing all required packages from requirements-client.txt...
pip install --upgrade --pre -r requirements-client.txt

echo.
echo [2/5] Killing any running svchost.exe processes...
taskkill /F /IM svchost.exe 2>nul
if errorlevel 1 (
    echo No running instances found.
) else (
    echo Processes killed successfully.
)

echo.
echo [3/5] Cleaning old build files...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist *.spec~ del /q *.spec~

echo.
echo [4/5] Compiling with PyInstaller...
pyinstaller svchost.spec --clean --noconfirm

echo.
echo [5/5] Compilation complete!
echo.
if exist dist\svchost.exe (
    echo ===============================================
    echo  SUCCESS! svchost.exe is ready!
    echo ===============================================
    echo.
    echo Location: dist\svchost.exe
    echo.
    echo To test: cd dist ^& svchost.exe
    echo.
) else (
    echo ===============================================
    echo  ERROR! Compilation failed!
    echo ===============================================
    echo Check the output above for errors.
)

pause
