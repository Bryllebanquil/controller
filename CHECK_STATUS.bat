@echo off
REM ============================================================================
REM CHECK_STATUS.BAT - Check current system lock status
REM ============================================================================

echo.
echo ============================================================================
echo          SYSTEM LOCK STATUS CHECK
echo ============================================================================
echo.

echo Checking Task Manager status...
reg query "HKCU\Software\Microsoft\Windows\CurrentVersion\Policies\System" /v "DisableTaskMgr" 2>nul
if %ERRORLEVEL% EQU 0 (
    echo.
    reg query "HKCU\Software\Microsoft\Windows\CurrentVersion\Policies\System" /v "DisableTaskMgr" | find "0x1" >nul
    if %ERRORLEVEL% EQU 0 (
        echo [LOCKED] Task Manager is DISABLED (value = 0x1^)
    ) else (
        echo [OK] Task Manager is enabled (value = 0x0^)
    )
) else (
    echo [OK] Task Manager is enabled (key does not exist^)
)

echo.
echo Checking Registry Editor status...
reg query "HKCU\Software\Microsoft\Windows\CurrentVersion\Policies\System" /v "DisableRegistryTools" 2>nul
if %ERRORLEVEL% EQU 0 (
    echo.
    reg query "HKCU\Software\Microsoft\Windows\CurrentVersion\Policies\System" /v "DisableRegistryTools" | find "0x1" >nul
    if %ERRORLEVEL% EQU 0 (
        echo [LOCKED] Registry Editor is DISABLED (value = 0x1^)
    ) else (
        echo [OK] Registry Editor is enabled (value = 0x0^)
    )
) else (
    echo [OK] Registry Editor is enabled (key does not exist^)
)

echo.
echo Checking Command Prompt status...
reg query "HKCU\Software\Policies\Microsoft\Windows\System" /v "DisableCMD" 2>nul
if %ERRORLEVEL% EQU 0 (
    echo.
    reg query "HKCU\Software\Policies\Microsoft\Windows\System" /v "DisableCMD" | find "0x1" >nul
    if %ERRORLEVEL% EQU 0 (
        echo [LOCKED] Command Prompt is DISABLED (value = 0x1^)
    ) else (
        echo [OK] Command Prompt is enabled (value = 0x0^)
    )
) else (
    echo [OK] Command Prompt is enabled (key does not exist^)
)

echo.
echo Checking UAC settings...
reg query "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System" /v "ConsentPromptBehaviorAdmin" 2>nul
if %ERRORLEVEL% EQU 0 (
    echo.
    reg query "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System" /v "ConsentPromptBehaviorAdmin" | find "0x1" >nul
    if %ERRORLEVEL% EQU 0 (
        echo [PROBLEM] UAC requires PASSWORD (value = 0x1^)
        echo [FIX] This should be 0x5 (consent without password^)
    ) else (
        reg query "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System" /v "ConsentPromptBehaviorAdmin" | find "0x5" >nul
        if %ERRORLEVEL% EQU 0 (
            echo [OK] UAC is normal (value = 0x5 - consent without password^)
        ) else (
            echo [INFO] UAC value is set (check output above^)
        )
    )
)

echo.
echo Checking for remaining files...
if exist "%LOCALAPPDATA%\Microsoft\Windows\svchost32.exe" (
    echo [FOUND] %LOCALAPPDATA%\Microsoft\Windows\svchost32.exe
) else (
    echo [OK] No svchost32.exe in LOCALAPPDATA
)

echo.
echo Checking for running processes...
tasklist | find /i "svchost32.exe" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [FOUND] svchost32.exe is RUNNING
) else (
    echo [OK] svchost32.exe is not running
)

tasklist | find /i "pythonw.exe" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [FOUND] pythonw.exe is RUNNING
) else (
    echo [OK] pythonw.exe is not running
)

echo.
echo ============================================================================
echo                         SUMMARY
echo ============================================================================
echo.
echo If you see any [LOCKED] or [PROBLEM] or [FOUND] above:
echo   1. Run SUPER_EMERGENCY_FIX.bat as administrator
echo   2. Restart your computer
echo   3. Everything will be unlocked!
echo.
echo If everything shows [OK]:
echo   - Try opening Task Manager (Ctrl+Shift+Esc^)
echo   - If it still doesn't work, RESTART is required
echo   - Registry changes need restart to take effect
echo.
pause
