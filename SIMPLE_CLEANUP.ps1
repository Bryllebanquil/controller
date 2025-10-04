<#
.SYNOPSIS
    COMPLETE Client.py Malware Cleanup and System Restore
.DESCRIPTION
    Removes ALL persistence, registry changes, hidden files, and restores
    UAC, Windows Defender, and Notifications to default state.
.PARAMETER PerformCleanup
    If supplied, performs destructive actions. Default is Dry-Run.
.NOTES
    - Run as Administrator
    - Use -PerformCleanup to actually remove artifacts
#>

[CmdletBinding()]
param(
    [switch]$PerformCleanup = $false
)

# Setup logging
$timestamp = (Get-Date).ToString("yyyyMMdd_HHmmss")
$baseLogDir = Join-Path -Path $env:LOCALAPPDATA -ChildPath "MalwareCleanup\$timestamp"
New-Item -Path $baseLogDir -ItemType Directory -Force | Out-Null
$logFile = Join-Path -Path $baseLogDir -ChildPath "cleanup.log"

function Log {
    param([string]$msg, [string]$level = "INFO")
    $line = "{0} [{1}] {2}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $level, $msg
    $color = "Green"
    if ($level -eq "ERROR") { $color = "Red" }
    elseif ($level -eq "WARNING") { $color = "Yellow" }
    Write-Host $line -ForegroundColor $color
    $line | Out-File -FilePath $logFile -Append -Encoding utf8
}

Log "=============================================================="
Log "  COMPLETE CLIENT.PY CLEANUP AND SYSTEM RESTORE"
Log "=============================================================="
Log "PerformCleanup = $($PerformCleanup.IsPresent)"
if ($PerformCleanup) {
    Log "Mode: DESTRUCTIVE - WILL MAKE CHANGES"
} else {
    Log "Mode: DRY-RUN - NO CHANGES"
}
Log "=============================================================="

Start-Transcript -Path (Join-Path $baseLogDir "transcript.txt") -Force | Out-Null

# Helper function
function DoAction {
    param(
        [string]$Description,
        [scriptblock]$Action
    )
    Log $Description
    if ($PerformCleanup) {
        try {
            & $Action
            Log "  [OK] SUCCESS: $Description"
        } catch {
            Log "  [FAIL] $Description -> $($_.Exception.Message)" "ERROR"
        }
    } else {
        Log "  [DRY-RUN] Would perform: $Description"
    }
}

# ==============================================================
# STEP 1: PROCESS TERMINATION
# ==============================================================

Log ""
Log "[STEP 1] Terminating Suspicious Processes..."
Log "--------------------------------------------------------------"

$processIndicators = @('python.exe','pythonw.exe','svchost32.exe')
$cmdlineIndicators = @('svchost32','client.py','SystemService','WindowsSecurityUpdate','fake.msc','agent','pure_agent')

function Stop-SuspiciousProcesses {
    Log "Scanning for suspicious processes..."
    
    # Python processes with suspicious command lines
    $candidateProcs = Get-CimInstance Win32_Process -Filter "Name='python.exe' OR Name='pythonw.exe'" -ErrorAction SilentlyContinue | Where-Object {
        $match = $false
        if ($_.CommandLine) {
            foreach ($k in $cmdlineIndicators) {
                if ($_.CommandLine.ToLower().Contains($k.ToLower())) { 
                    $match = $true
                    break 
                }
            }
        }
        $match
    }

    if (-not $candidateProcs) {
        Log "  [OK] No suspicious python processes found"
    } else {
        foreach ($p in $candidateProcs) {
            $desc = "Kill process: ID=$($p.ProcessId) Name=$($p.Name)"
            DoAction -Description $desc -Action {
                if (Get-Process -Id $p.ProcessId -ErrorAction SilentlyContinue) {
                    Stop-Process -Id $p.ProcessId -Force -ErrorAction Stop
                }
            }
        }
    }

    # svchost32.exe (malicious fake svchost)
    Get-Process -Name "svchost32" -ErrorAction SilentlyContinue | ForEach-Object {
        DoAction -Description "Kill fake svchost32.exe (PID $($_.Id))" -Action {
            Stop-Process -Id $_.Id -Force
        }
    }

    # Collect network connections
    try {
        netstat -ano | Out-File -FilePath (Join-Path $baseLogDir "netstat.txt") -Encoding utf8
        Log "  [OK] Network connections snapshot saved"
    } catch {
        Log "  [WARN] Could not run netstat: $($_.Exception.Message)" "WARNING"
    }
}

Stop-SuspiciousProcesses

# ==============================================================
# STEP 2: FILE CLEANUP
# ==============================================================

Log ""
Log "[STEP 2] Removing Malicious Files..."
Log "--------------------------------------------------------------"

$searchPaths = @(
    "$env:APPDATA",
    "$env:LOCALAPPDATA",
    "$env:TEMP",
    "$env:SystemRoot\Temp",
    (Join-Path "$env:APPDATA" "Microsoft\Windows\Start Menu\Programs\Startup"),
    (Join-Path "$env:LOCALAPPDATA" "Microsoft\Windows")
)

$fileCandidates = @(
    "*svchost32*",
    "*SystemService*",
    "*WindowsSecurityUpdate*",
    "*WindowsSecurityService*",
    "*client.py*",
    "*client.exe*",
    "*pure_agent*",
    "*agent_id.txt*",
    "*fake.msc*",
    "*tamper_protection*",
    "*watchdog*"
)

function Remove-MaliciousFiles {
    Log "Searching for malicious files..."
    
    foreach ($basePath in $searchPaths) {
        if (-not (Test-Path $basePath)) { continue }
        
        foreach ($pattern in $fileCandidates) {
            $found = Get-ChildItem -Path $basePath -Filter $pattern -Recurse -ErrorAction SilentlyContinue -Force
            
            foreach ($f in $found) {
                # Skip signed system files
                $sys32 = Join-Path $env:SystemRoot "System32"
                if ($f.FullName.ToLower().StartsWith($sys32.ToLower())) {
                    $sig = Get-AuthenticodeSignature -FilePath $f.FullName -ErrorAction SilentlyContinue
                    if ($sig -and $sig.Status -eq 'Valid') {
                        Log "  [SKIP] Signed system file: $($f.FullName)"
                        continue
                    }
                }
                
                $desc = "Delete: $($f.FullName)"
                DoAction -Description $desc -Action {
                    if (Test-Path $f.FullName) {
                        attrib -h -s "$($f.FullName)" 2>$null
                        Remove-Item -LiteralPath $f.FullName -Force -Recurse -ErrorAction Stop
                    }
                }
            }
        }
    }
}

Remove-MaliciousFiles

# ==============================================================
# STEP 3: RESTORE UAC (CRITICAL!)
# ==============================================================

Log ""
Log "[STEP 3] Restoring UAC to Default State..."
Log "--------------------------------------------------------------"

function Restore-UAC {
    $uacPath = "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System"
    
    DoAction -Description "Restore EnableLUA = 1 (re-enable UAC)" -Action {
        Set-ItemProperty -Path $uacPath -Name "EnableLUA" -Value 1 -Type DWord -Force
    }
    
    DoAction -Description "Restore ConsentPromptBehaviorAdmin = 5 (default prompt)" -Action {
        Set-ItemProperty -Path $uacPath -Name "ConsentPromptBehaviorAdmin" -Value 5 -Type DWord -Force
    }
    
    DoAction -Description "Restore PromptOnSecureDesktop = 1 (secure desktop)" -Action {
        Set-ItemProperty -Path $uacPath -Name "PromptOnSecureDesktop" -Value 1 -Type DWord -Force
    }
    
    Log "  [OK] UAC restored (requires restart to take effect)"
}

Restore-UAC

# ==============================================================
# STEP 4: RESTORE WINDOWS DEFENDER (CRITICAL!)
# ==============================================================

Log ""
Log "[STEP 4] Restoring Windows Defender..."
Log "--------------------------------------------------------------"

function Restore-Defender {
    # Remove malicious Defender disable keys
    $defenderPaths = @(
        "HKLM:\SOFTWARE\Policies\Microsoft\Windows Defender",
        "HKLM:\SOFTWARE\Policies\Microsoft\Windows Defender\Real-Time Protection"
    )
    
    foreach ($path in $defenderPaths) {
        DoAction -Description "Remove malicious Defender policy: $path" -Action {
            if (Test-Path $path) {
                Remove-Item -Path $path -Recurse -Force -ErrorAction Stop
            }
        }
    }
    
    # Re-enable Defender via PowerShell
    DoAction -Description "Enable Defender Real-Time Monitoring" -Action {
        if (Get-Command Set-MpPreference -ErrorAction SilentlyContinue) {
            Set-MpPreference -DisableRealtimeMonitoring $false -Force
            Set-MpPreference -DisableBehaviorMonitoring $false -Force
            Set-MpPreference -DisableBlockAtFirstSeen $false -Force
            Set-MpPreference -DisableIOAVProtection $false -Force
            Set-MpPreference -DisableIntrusionPreventionSystem $false -Force
            Set-MpPreference -DisableScriptScanning $false -Force
        }
    }
    
    # Start Defender service
    DoAction -Description "Start Windows Defender service" -Action {
        if (Get-Service -Name WinDefend -ErrorAction SilentlyContinue) {
            Set-Service -Name WinDefend -StartupType Automatic
            Start-Service -Name WinDefend -ErrorAction SilentlyContinue
        }
    }
    
    Log "  [OK] Windows Defender restored"
}

Restore-Defender

# ==============================================================
# STEP 5: RESTORE NOTIFICATIONS
# ==============================================================

Log ""
Log "[STEP 5] Restoring Windows Notifications..."
Log "--------------------------------------------------------------"

function Restore-Notifications {
    $notificationKeys = @(
        @{Path="HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\PushNotifications"; Name="ToastEnabled"; Value=1},
        @{Path="HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Notifications\Settings"; Name="NOC_GLOBAL_SETTING_ALLOW_NOTIFICATION_SOUND"; Value=1},
        @{Path="HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Notifications\Settings"; Name="NOC_GLOBAL_SETTING_ALLOW_TOASTS_ABOVE_LOCK"; Value=1},
        @{Path="HKCU:\SOFTWARE\Policies\Microsoft\Windows\Explorer"; Name="DisableNotificationCenter"; Value=0}
    )
    
    foreach ($key in $notificationKeys) {
        DoAction -Description "Restore notification: $($key.Name)" -Action {
            if (-not (Test-Path $key.Path)) {
                New-Item -Path $key.Path -Force | Out-Null
            }
            Set-ItemProperty -Path $key.Path -Name $key.Name -Value $key.Value -Type DWord -Force
        }
    }
    
    Log "  [OK] Notifications restored"
}

Restore-Notifications

# ==============================================================
# STEP 6: REGISTRY CLEANUP
# ==============================================================

Log ""
Log "[STEP 6] Cleaning Registry Persistence and Hijacks..."
Log "--------------------------------------------------------------"

$regKeysToDelete = @(
    "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run\WindowsSecurityUpdate",
    "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run\svchost32",
    "HKLM:\Software\Microsoft\Windows\CurrentVersion\Run\WindowsSecurityUpdate",
    "HKCU:\Software\Classes\ms-settings\Shell\Open\command",
    "HKCU:\Software\Classes\mscfile\shell\open\command",
    "HKCU:\Software\Classes\exefile\shell\open\command",
    "HKCU:\Software\Classes\Folder\shell\open\command",
    "HKCU:\Software\Classes\CLSID\{11111111-1111-1111-1111-111111111111}",
    "HKCU:\Software\Classes\CLSID\{11111111-2222-3333-4444-555555555555}",
    "HKCU:\Software\Microsoft\Windows\CurrentVersion\App Paths\control.exe",
    "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Image File Execution Options\taskmgr.exe",
    "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Image File Execution Options\regedit.exe"
)

function Remove-RegistryKeys {
    foreach ($k in $regKeysToDelete) {
        DoAction -Description "Remove registry: $k" -Action {
            if (Test-Path $k) {
                Remove-Item -Path $k -Recurse -Force -ErrorAction Stop
            }
        }
    }
    
    # Remove malicious environment variables
    DoAction -Description "Remove HKCU Environment windir hijack" -Action {
        if (Get-ItemProperty -Path "HKCU:\Environment" -Name "windir" -ErrorAction SilentlyContinue) {
            Remove-ItemProperty -Path "HKCU:\Environment" -Name windir -ErrorAction Stop
        }
    }
    
    # Restore system tools
    DoAction -Description "Re-enable Task Manager" -Action {
        if (Test-Path "HKCU:\Software\Microsoft\Windows\CurrentVersion\Policies\System") {
            Remove-ItemProperty -Path "HKCU:\Software\Microsoft\Windows\CurrentVersion\Policies\System" -Name "DisableTaskMgr" -ErrorAction SilentlyContinue
        }
    }
    
    DoAction -Description "Re-enable Registry Editor" -Action {
        if (Test-Path "HKCU:\Software\Microsoft\Windows\CurrentVersion\Policies\System") {
            Remove-ItemProperty -Path "HKCU:\Software\Microsoft\Windows\CurrentVersion\Policies\System" -Name "DisableRegistryTools" -ErrorAction SilentlyContinue
        }
    }
    
    DoAction -Description "Re-enable Command Prompt" -Action {
        if (Test-Path "HKCU:\Software\Policies\Microsoft\Windows\System") {
            Remove-ItemProperty -Path "HKCU:\Software\Policies\Microsoft\Windows\System" -Name "DisableCMD" -ErrorAction SilentlyContinue
        }
    }
    
    Log "  [OK] Registry cleaned"
}

Remove-RegistryKeys

# ==============================================================
# STEP 7: SCHEDULED TASKS
# ==============================================================

Log ""
Log "[STEP 7] Removing Scheduled Tasks..."
Log "--------------------------------------------------------------"

$scheduledTasks = @(
    "\WindowsSecurityUpdate",
    "\WindowsSecurityUpdateTask",
    "\SystemService"
)

function Remove-ScheduledTasks {
    foreach ($t in $scheduledTasks) {
        DoAction -Description "Delete scheduled task: $t" -Action {
            $exists = schtasks /Query /TN $t 2>$null
            if ($LASTEXITCODE -eq 0) {
                schtasks /Delete /TN $t /F | Out-Null
            }
        }
    }
    Log "  [OK] Scheduled tasks cleaned"
}

Remove-ScheduledTasks

# ==============================================================
# STEP 8: SERVICES
# ==============================================================

Log ""
Log "[STEP 8] Removing Malicious Services..."
Log "--------------------------------------------------------------"

$serviceNames = @("WindowsSecurityService", "SystemService", "svchost32")

function Remove-Services {
    foreach ($s in $serviceNames) {
        DoAction -Description "Stop and delete service: $s" -Action {
            $svc = Get-Service -Name $s -ErrorAction SilentlyContinue
            if ($svc) {
                Stop-Service -Name $s -Force -ErrorAction SilentlyContinue
                sc.exe delete $s 2>$null
            }
        }
    }
    Log "  [OK] Services cleaned"
}

Remove-Services

# ==============================================================
# STEP 9: WMI PERSISTENCE
# ==============================================================

Log ""
Log "[STEP 9] Removing WMI Persistence..."
Log "--------------------------------------------------------------"

function Remove-WMIpersist {
    DoAction -Description "Remove WMI event filters" -Action {
        Get-WmiObject -Namespace root\subscription -Class __EventFilter -ErrorAction SilentlyContinue | 
            Where-Object { $_.Name -match "WindowsSecurity|SystemService" } | 
            ForEach-Object { $_.Delete() }
    }
    
    DoAction -Description "Remove WMI event consumers" -Action {
        Get-WmiObject -Namespace root\subscription -Class CommandLineEventConsumer -ErrorAction SilentlyContinue | 
            Where-Object { $_.Name -match "WindowsSecurity|SystemService" } | 
            ForEach-Object { $_.Delete() }
    }
    
    Log "  [OK] WMI persistence removed"
}

Remove-WMIpersist

# ==============================================================
# STEP 10: FIREWALL RESET
# ==============================================================

Log ""
Log "[STEP 10] Resetting Firewall..."
Log "--------------------------------------------------------------"

function Reset-Firewall {
    DoAction -Description "Reset Windows Firewall to defaults" -Action {
        netsh advfirewall reset | Out-Null
    }
    Log "  [OK] Firewall reset"
}

Reset-Firewall

# ==============================================================
# STEP 11: SYSTEM INTEGRITY
# ==============================================================

Log ""
Log "[STEP 11] Running System Integrity Checks..."
Log "--------------------------------------------------------------"

function Run-IntegrityChecks {
    DoAction -Description "Run SFC /scannow" -Action {
        $sfcOutput = Join-Path $baseLogDir "sfc.txt"
        sfc /scannow | Out-File $sfcOutput
        Log "  SFC output saved to: $sfcOutput"
    }
    
    DoAction -Description "Run DISM RestoreHealth" -Action {
        $dismOutput = Join-Path $baseLogDir "dism.txt"
        DISM /Online /Cleanup-Image /RestoreHealth | Out-File $dismOutput
        Log "  DISM output saved to: $dismOutput"
    }
    
    Log "  [OK] System integrity checks complete"
}

Run-IntegrityChecks

# ==============================================================
# STEP 12: DEFENDER SCAN
# ==============================================================

Log ""
Log "[STEP 12] Running Windows Defender Full Scan..."
Log "--------------------------------------------------------------"

function Run-DefenderScan {
    DoAction -Description "Update Defender signatures" -Action {
        if (Get-Command Update-MpSignature -ErrorAction SilentlyContinue) {
            Update-MpSignature
        }
    }
    
    DoAction -Description "Start Defender Full Scan" -Action {
        if (Get-Command Start-MpScan -ErrorAction SilentlyContinue) {
            Start-MpScan -ScanType FullScan -AsJob
            Log "  Defender scan started in background"
        }
    }
    
    Log "  [OK] Defender scan initiated"
}

Run-DefenderScan

# ==============================================================
# STEP 13: COLLECT ARTIFACTS
# ==============================================================

Log ""
Log "[STEP 13] Collecting System State Artifacts..."
Log "--------------------------------------------------------------"

function Collect-Artifacts {
    try {
        Get-ItemProperty "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run" -ErrorAction SilentlyContinue | 
            Out-File (Join-Path $baseLogDir "run_keys.txt")
        
        Get-CimInstance Win32_Service | Select-Object Name,State,StartMode,PathName | 
            Out-File (Join-Path $baseLogDir "services.txt")
        
        schtasks /Query /FO LIST /V | Out-File (Join-Path $baseLogDir "tasks.txt")
        
        Get-Process | Select-Object Id,Name,Path | 
            Out-File (Join-Path $baseLogDir "processes.txt")
        
        Log "  [OK] Artifacts collected in: $baseLogDir"
    } catch {
        Log "  [WARN] Error collecting artifacts: $($_.Exception.Message)" "WARNING"
    }
}

Collect-Artifacts

# ==============================================================
# FINAL SUMMARY
# ==============================================================

Log ""
Log "=============================================================="
Log "  CLEANUP COMPLETE!"
Log "=============================================================="
Log ""
Log "Log files saved to: $baseLogDir"
Log "Main log: $logFile"
Log ""

if ($PerformCleanup) {
    Log "[OK] CHANGES WERE APPLIED"
    Log ""
    Log "[!] CRITICAL: RESTART YOUR PC NOW!"
    Log ""
    Log "After restart:"
    Log "  1. UAC will be re-enabled"
    Log "  2. Windows Defender will be active"
    Log "  3. Notifications will work"
    Log "  4. All system tools will work"
    Log ""
    Log "Verify by:"
    Log "  - Open Task Manager (Ctrl+Shift+Esc)"
    Log "  - Open Registry Editor (Win+R, type regedit)"
    Log "  - Check Defender status in Windows Security"
    Log "  - Try running an admin app (should see UAC prompt)"
} else {
    Log "[INFO] DRY-RUN MODE - NO CHANGES MADE"
    Log ""
    Log "To perform actual cleanup, run:"
    Log "  .\SIMPLE_CLEANUP.ps1 -PerformCleanup"
}

Log "=============================================================="

Stop-Transcript | Out-Null

# Ask for restart if changes were made
if ($PerformCleanup) {
    Write-Host ""
    $restart = Read-Host "Restart computer now? (Y/N)"
    if ($restart -eq 'Y' -or $restart -eq 'y') {
        Log "Restarting computer now"
        Restart-Computer -Force
    }
}
