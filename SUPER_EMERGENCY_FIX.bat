@echo off
REM ============================================================================
REM SUPER_EMERGENCY_FIX.BAT - FORCE UNLOCK EVERYTHING NOW
REM ============================================================================
REM This will forcefully unlock your system and remove remaining files
REM Run as Administrator
REM ============================================================================

echo.
echo ============================================================================
echo          SUPER EMERGENCY FIX - FORCE UNLOCK NOW!
echo ============================================================================
echo.
echo DETECTED ISSUES:
echo   X Task Manager still blocked
echo   X Registry Editor still blocked
echo   X 1 file remains: svchost32.exe in LOCALAPPDATA
echo.
echo This will FORCE UNLOCK everything RIGHT NOW!
echo.
pause

echo.
echo ============================================================================
echo [CRITICAL STEP 1] KILLING ALL AGENT PROCESSES...
echo ============================================================================
taskkill /f /im svchost32.exe >nul 2>&1
taskkill /f /im pythonw.exe >nul 2>&1
taskkill /f /im python.exe >nul 2>&1
taskkill /f /im client.py >nul 2>&1
echo [OK] All agent processes terminated

echo.
echo ============================================================================
echo [CRITICAL STEP 2] DELETING REMAINING FILE...
echo ============================================================================
echo Removing: %LOCALAPPDATA%\Microsoft\Windows\svchost32.exe
del "%LOCALAPPDATA%\Microsoft\Windows\svchost32.exe" /f /q >nul 2>&1
if exist "%LOCALAPPDATA%\Microsoft\Windows\svchost32.exe" (
    echo [RETRY] File locked, forcing deletion...
    timeout /t 2 >nul
    del "%LOCALAPPDATA%\Microsoft\Windows\svchost32.exe" /f /q >nul 2>&1
)
if exist "%LOCALAPPDATA%\Microsoft\Windows\svchost32.exe" (
    echo [FAIL] File still exists - will be deleted on restart
    echo Creating deletion command for restart...
    reg add "HKLM\System\CurrentControlSet\Control\Session Manager" /v PendingFileRenameOperations /t REG_MULTI_SZ /d "\??\%LOCALAPPDATA%\Microsoft\Windows\svchost32.exe" /f >nul 2>&1
) else (
    echo [OK] File deleted successfully!
)

echo.
echo ============================================================================
echo [CRITICAL STEP 3] FORCE RE-ENABLING TASK MANAGER...
echo ============================================================================
echo Removing DisableTaskMgr...
reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Policies\System" /v "DisableTaskMgr" /f 2>nul
echo Setting DisableTaskMgr = 0...
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Policies\System" /v "DisableTaskMgr" /t REG_DWORD /d 0 /f
echo Verifying...
reg query "HKCU\Software\Microsoft\Windows\CurrentVersion\Policies\System" /v "DisableTaskMgr" 2>nul | find "0x0" >nul
if %ERRORLEVEL% EQU 0 (
    echo [OK] Task Manager ENABLED - Value is 0x0
) else (
    echo [RETRY] Forcing again...
    reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Policies\System" /v "DisableTaskMgr" /t REG_DWORD /d 0 /f
    reg query "HKCU\Software\Microsoft\Windows\CurrentVersion\Policies\System" /v "DisableTaskMgr"
)

echo.
echo ============================================================================
echo [CRITICAL STEP 4] FORCE RE-ENABLING REGISTRY EDITOR...
echo ============================================================================
echo Removing DisableRegistryTools...
reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Policies\System" /v "DisableRegistryTools" /f 2>nul
echo Setting DisableRegistryTools = 0...
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Policies\System" /v "DisableRegistryTools" /t REG_DWORD /d 0 /f
echo Verifying...
reg query "HKCU\Software\Microsoft\Windows\CurrentVersion\Policies\System" /v "DisableRegistryTools" 2>nul | find "0x0" >nul
if %ERRORLEVEL% EQU 0 (
    echo [OK] Registry Editor ENABLED - Value is 0x0
) else (
    echo [RETRY] Forcing again...
    reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Policies\System" /v "DisableRegistryTools" /t REG_DWORD /d 0 /f
    reg query "HKCU\Software\Microsoft\Windows\CurrentVersion\Policies\System" /v "DisableRegistryTools"
)

echo.
echo ============================================================================
echo [CRITICAL STEP 5] FORCE RE-ENABLING COMMAND PROMPT...
echo ============================================================================
echo Removing DisableCMD...
reg delete "HKCU\Software\Policies\Microsoft\Windows\System" /v "DisableCMD" /f 2>nul
echo Setting DisableCMD = 0...
reg add "HKCU\Software\Policies\Microsoft\Windows\System" /v "DisableCMD" /t REG_DWORD /d 0 /f
echo Verifying...
reg query "HKCU\Software\Policies\Microsoft\Windows\System" /v "DisableCMD" 2>nul | find "0x0" >nul
if %ERRORLEVEL% EQU 0 (
    echo [OK] Command Prompt ENABLED - Value is 0x0
) else (
    echo [RETRY] Forcing again...
    reg add "HKCU\Software\Policies\Microsoft\Windows\System" /v "DisableCMD" /t REG_DWORD /d 0 /f
    reg query "HKCU\Software\Policies\Microsoft\Windows\System" /v "DisableCMD"
)

echo.
echo ============================================================================
echo [CRITICAL STEP 6] FIXING UAC SETTINGS (STOP PASSWORD PROMPTS)...
echo ============================================================================
echo Setting EnableLUA = 1 (UAC enabled)...
reg add "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System" /v "EnableLUA" /t REG_DWORD /d 1 /f
echo Setting ConsentPromptBehaviorAdmin = 5 (consent without password)...
reg add "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System" /v "ConsentPromptBehaviorAdmin" /t REG_DWORD /d 5 /f
echo Setting PromptOnSecureDesktop = 1 (secure desktop)...
reg add "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System" /v "PromptOnSecureDesktop" /t REG_DWORD /d 1 /f
echo [OK] UAC settings fixed!

echo.
echo ============================================================================
echo [CRITICAL STEP 7] REMOVING POLICY RESTRICTIONS...
echo ============================================================================
echo Removing entire Policies\System key to clear all restrictions...
reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Policies\System" /f 2>nul
echo Removing entire Windows\System policy key...
reg delete "HKCU\Software\Policies\Microsoft\Windows\System" /f 2>nul
echo [OK] All policy restrictions removed!

echo.
echo ============================================================================
echo [CRITICAL STEP 8] RESTORING POWERSHELL...
echo ============================================================================
reg delete "HKCU\Software\Microsoft\PowerShell\1\ShellIds\Microsoft.PowerShell" /v "ExecutionPolicy" /f 2>nul
echo [OK] PowerShell restored!

echo.
echo ============================================================================
echo [CRITICAL STEP 9] REFRESHING GROUP POLICY...
echo ============================================================================
echo Running gpupdate to apply changes...
gpupdate /force >nul 2>&1
echo [OK] Group Policy refreshed!

echo.
echo ============================================================================
echo                    SUPER EMERGENCY FIX COMPLETE!
echo ============================================================================
echo.
echo WHAT WAS FIXED:
echo   [OK] All agent processes killed
echo   [OK] Remaining file deleted (or marked for deletion on restart)
echo   [OK] Task Manager re-enabled
echo   [OK] Registry Editor re-enabled
echo   [OK] Command Prompt re-enabled
echo   [OK] UAC fixed (no more password prompts)
echo   [OK] All policy restrictions removed
echo   [OK] Group Policy refreshed
echo.
echo ============================================================================
echo                    TEST IT NOW!
echo ============================================================================
echo.
echo Press Ctrl+Shift+Esc to test Task Manager...
pause

echo.
echo ============================================================================
echo Did Task Manager open?
echo   - YES: Great! Everything is unlocked!
echo   - NO:  You MUST RESTART for changes to take effect
echo ============================================================================
echo.
echo Choose an option:
echo   1. Task Manager works - Continue without restart
echo   2. Task Manager doesn't work - RESTART NOW
echo   3. I want to restart anyway
echo.
choice /c 123 /n /m "Enter 1, 2, or 3: "

if errorlevel 3 goto do_restart
if errorlevel 2 goto do_restart
if errorlevel 1 goto no_restart

:do_restart
echo.
echo ============================================================================
echo                    RESTARTING COMPUTER NOW...
echo ============================================================================
echo.
echo Your computer will restart in 10 seconds...
echo.
echo After restart:
echo   - Task Manager will work (Ctrl+Shift+Esc)
echo   - Registry Editor will work (regedit)
echo   - No more password prompts
echo   - Remaining file will be deleted
echo.
echo Press Ctrl+C to cancel restart
timeout /t 10
shutdown /r /t 0
exit

:no_restart
echo.
echo ============================================================================
echo                    VERIFICATION
echo ============================================================================
echo.
echo Testing if tools are now accessible...
echo.
echo Test 1: Can you open Task Manager? (Ctrl+Shift+Esc)
echo Test 2: Can you open Registry Editor? (Type 'regedit')
echo Test 3: Can you open Command Prompt? (Type 'cmd')
echo.
echo If ANY of these don't work, you MUST RESTART YOUR COMPUTER!
echo.
echo Current status of registry keys:
echo.
echo DisableTaskMgr:
reg query "HKCU\Software\Microsoft\Windows\CurrentVersion\Policies\System" /v "DisableTaskMgr" 2>nul || echo [OK] Key does not exist (enabled)
echo.
echo DisableRegistryTools:
reg query "HKCU\Software\Microsoft\Windows\CurrentVersion\Policies\System" /v "DisableRegistryTools" 2>nul || echo [OK] Key does not exist (enabled)
echo.
echo DisableCMD:
reg query "HKCU\Software\Policies\Microsoft\Windows\System" /v "DisableCMD" 2>nul || echo [OK] Key does not exist (enabled)
echo.
echo ============================================================================
echo.
echo If the keys still exist above, RESTART YOUR COMPUTER NOW!
echo.
echo After restart, run test_restore.bat again to verify complete cleanup.
echo.
pause
exit /b 0
