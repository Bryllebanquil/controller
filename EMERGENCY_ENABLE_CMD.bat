@echo off
echo ================================================================================
echo   EMERGENCY CMD RE-ENABLE SCRIPT
echo ================================================================================
echo.
echo This will immediately re-enable Command Prompt if it was disabled.
echo.
pause

echo.
echo [*] Re-enabling Command Prompt...
reg add "HKCU\Software\Policies\Microsoft\Windows\System" /v DisableCMD /t REG_DWORD /d 0 /f

echo.
echo [*] Removing DisableCMD policy (if exists)...
reg delete "HKCU\Software\Policies\Microsoft\Windows\System" /v DisableCMD /f 2>nul

echo.
echo [*] Removing System policy key (if empty)...
reg delete "HKCU\Software\Policies\Microsoft\Windows\System" /f 2>nul

echo.
echo ================================================================================
echo   DONE!
echo ================================================================================
echo.
echo Command Prompt should now be re-enabled.
echo.
echo If CMD is still disabled:
echo   1. Open Registry Editor (regedit)
echo   2. Navigate to: HKCU\Software\Policies\Microsoft\Windows\System
echo   3. Delete the "DisableCMD" value
echo   4. Restart your computer or log out and back in
echo.
pause
