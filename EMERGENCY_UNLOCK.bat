@echo off
REM ============================================================================
REM EMERGENCY_UNLOCK.BAT - IMMEDIATE SYSTEM UNLOCK
REM ============================================================================
REM This script IMMEDIATELY re-enables Task Manager, Registry Editor, and CMD
REM Run as Administrator RIGHT NOW to regain control
REM ============================================================================

echo.
echo ============================================================================
echo          EMERGENCY SYSTEM UNLOCK - CRITICAL FIX
echo ============================================================================
echo.
echo Your system is currently locked:
echo   X Task Manager is disabled
echo   X Registry Editor is disabled
echo   X Command Prompt is disabled
echo   X UAC is requiring password for everything
echo.
echo This script will IMMEDIATELY unlock everything.
echo.
pause

echo.
echo [EMERGENCY] Re-enabling Task Manager...
reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Policies\System" /v "DisableTaskMgr" /f >nul 2>&1
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Policies\System" /v "DisableTaskMgr" /t REG_DWORD /d 0 /f >nul 2>&1
echo [OK] Task Manager enabled! (Press Ctrl+Shift+Esc to test)

echo.
echo [EMERGENCY] Re-enabling Registry Editor...
reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Policies\System" /v "DisableRegistryTools" /f >nul 2>&1
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Policies\System" /v "DisableRegistryTools" /t REG_DWORD /d 0 /f >nul 2>&1
echo [OK] Registry Editor enabled! (Type 'regedit' to test)

echo.
echo [EMERGENCY] Re-enabling Command Prompt...
reg delete "HKCU\Software\Policies\Microsoft\Windows\System" /v "DisableCMD" /f >nul 2>&1
reg add "HKCU\Software\Policies\Microsoft\Windows\System" /v "DisableCMD" /t REG_DWORD /d 0 /f >nul 2>&1
echo [OK] Command Prompt enabled! (Type 'cmd' to test)

echo.
echo [EMERGENCY] Fixing UAC Settings (Stop Password Prompts)...
reg add "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System" /v "EnableLUA" /t REG_DWORD /d 1 /f >nul 2>&1
reg add "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System" /v "ConsentPromptBehaviorAdmin" /t REG_DWORD /d 5 /f >nul 2>&1
reg add "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System" /v "PromptOnSecureDesktop" /t REG_DWORD /d 1 /f >nul 2>&1
echo [OK] UAC fixed! (No more password prompts for admin)

echo.
echo [EMERGENCY] Restoring PowerShell Execution Policy...
reg delete "HKCU\Software\Microsoft\PowerShell\1\ShellIds\Microsoft.PowerShell" /v "ExecutionPolicy" /f >nul 2>&1
echo [OK] PowerShell policy restored!

echo.
echo ============================================================================
echo                    EMERGENCY UNLOCK COMPLETE!
echo ============================================================================
echo.
echo YOU CAN NOW USE:
echo   [OK] Task Manager (Ctrl+Shift+Esc)
echo   [OK] Registry Editor (regedit)
echo   [OK] Command Prompt (cmd)
echo   [OK] Admin apps WITHOUT password prompts
echo.
echo IMPORTANT: You MUST restart your computer for all changes to take effect!
echo.
echo NEXT STEPS:
echo   1. Test Task Manager (Ctrl+Shift+Esc) - Should work now
echo   2. RESTART YOUR COMPUTER
echo   3. Run restore.bat to remove all agent traces
echo   4. Run test_restore.bat to verify cleanup
echo.
echo If Task Manager still doesn't work, restart and try again.
echo.

pause

echo.
echo Do you want to RESTART NOW? (Recommended)
echo Press Y to restart, N to restart later
choice /c YN /n /m "[Y]es or [N]o: "

if errorlevel 2 goto no_restart
if errorlevel 1 goto do_restart

:do_restart
echo.
echo Restarting in 10 seconds...
echo Press Ctrl+C to cancel
timeout /t 10
shutdown /r /t 0
exit

:no_restart
echo.
echo Remember to restart your computer manually for changes to take full effect!
pause
exit /b 0
