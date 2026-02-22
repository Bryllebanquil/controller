<#
.SYNOPSIS
    Windows Defender Exclusion Manager
.DESCRIPTION
    Manages Windows Defender exclusions for files, directories, extensions, and processes.
    Ensures exclusions are persistent and provides logging and verification.
.PARAMETER Action
    The action to perform: Add, Remove, Verify, DisableRealTime, EnableRealTime.
.PARAMETER Type
    The type of exclusion: Path, Process, Extension.
.PARAMETER Value
    The value to exclude (e.g., "C:\Temp", "test.exe", ".log").
.EXAMPLE
    .\defender_exclusion_manager.ps1 -Action Add -Type Path -Value "C:\MyApp"
.EXAMPLE
    .\defender_exclusion_manager.ps1 -Action DisableRealTime
#>

param (
    [Parameter(Mandatory=$true)]
    [ValidateSet("Add", "Remove", "Verify", "DisableRealTime", "EnableRealTime")]
    [string]$Action,

    [Parameter(Mandatory=$false)]
    [ValidateSet("Path", "Process", "Extension")]
    [string]$Type,

    [Parameter(Mandatory=$false)]
    [string]$Value
)

# Configuration
$LogFile = "$PSScriptRoot\defender_manager.log"

# Functions

function Log-Activity {
    param ([string]$Message, [string]$Level = "INFO")
    $Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $LogEntry = "[$Timestamp] [$Level] $Message"
    Write-Output $LogEntry
    Add-Content -Path $LogFile -Value $LogEntry -ErrorAction SilentlyContinue
}

function Check-Admin {
    $currentPrincipal = [Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()
    return $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Add-Exclusion {
    param ([string]$Type, [string]$Value)
    
    try {
        Log-Activity "Attempting to add exclusion: Type=$Type, Value=$Value"
        
        switch ($Type) {
            "Path" { Add-MpPreference -ExclusionPath $Value -ErrorAction Stop }
            "Process" { Add-MpPreference -ExclusionProcess $Value -ErrorAction Stop }
            "Extension" { Add-MpPreference -ExclusionExtension $Value -ErrorAction Stop }
        }
        
        # Verify
        if (Verify-Exclusion -Type $Type -Value $Value) {
            Log-Activity "Successfully added exclusion: $Value" "SUCCESS"
        } else {
            throw "Exclusion verification failed after addition."
        }
    } catch {
        Log-Activity "Failed to add exclusion: $_" "ERROR"
        throw $_
    }
}

function Remove-Exclusion {
    param ([string]$Type, [string]$Value)
    
    try {
        Log-Activity "Attempting to remove exclusion: Type=$Type, Value=$Value"
        
        switch ($Type) {
            "Path" { Remove-MpPreference -ExclusionPath $Value -ErrorAction Stop }
            "Process" { Remove-MpPreference -ExclusionProcess $Value -ErrorAction Stop }
            "Extension" { Remove-MpPreference -ExclusionExtension $Value -ErrorAction Stop }
        }
        
        Log-Activity "Successfully removed exclusion: $Value" "SUCCESS"
    } catch {
        Log-Activity "Failed to remove exclusion: $_" "ERROR"
        throw $_
    }
}

function Verify-Exclusion {
    param ([string]$Type, [string]$Value)
    
    $Prefs = Get-MpPreference
    $Exists = $false
    
    switch ($Type) {
        "Path" { $Exists = $Prefs.ExclusionPath -contains $Value }
        "Process" { $Exists = $Prefs.ExclusionProcess -contains $Value }
        "Extension" { $Exists = $Prefs.ExclusionExtension -contains $Value }
    }
    
    if ($Exists) {
        Log-Activity "Verification: Exclusion '$Value' exists." "INFO"
    } else {
        Log-Activity "Verification: Exclusion '$Value' NOT found." "WARN"
    }
    
    return $Exists
}

function Toggle-RealTimeProtection {
    param ([bool]$Enable)
    
    try {
        $State = if ($Enable) { "Enable" } else { "Disable" }
        Log-Activity "Attempting to $State Real-time Protection"
        
        Set-MpPreference -DisableRealtimeMonitoring (!$Enable) -ErrorAction Stop
        
        $CurrentState = (Get-MpPreference).DisableRealtimeMonitoring
        if ($CurrentState -eq (!$Enable)) {
            Log-Activity "Real-time Protection successfully set to: $State" "SUCCESS"
        } else {
            throw "Failed to verify Real-time Protection state change."
        }
    } catch {
        Log-Activity "Failed to change Real-time Protection: $_" "ERROR"
        throw $_
    }
}

# Main Execution

if (-not (Check-Admin)) {
    Write-Warning "This script requires Administrator privileges. Attempting to elevate..."
    Start-Process powershell.exe -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`" -Action $Action -Type $Type -Value `"$Value`"" -Verb RunAs
    exit
}

try {
    Log-Activity "Starting Defender Exclusion Manager..."
    
    switch ($Action) {
        "Add" {
            if (-not $Value) { throw "Value is required for Add action." }
            Add-Exclusion -Type $Type -Value $Value
        }
        "Remove" {
            if (-not $Value) { throw "Value is required for Remove action." }
            Remove-Exclusion -Type $Type -Value $Value
        }
        "Verify" {
            if (-not $Value) { throw "Value is required for Verify action." }
            Verify-Exclusion -Type $Type -Value $Value
        }
        "DisableRealTime" {
            Toggle-RealTimeProtection -Enable $false
        }
        "EnableRealTime" {
            Toggle-RealTimeProtection -Enable $true
        }
    }
    
    Log-Activity "Operation completed successfully." "SUCCESS"
} catch {
    Log-Activity "Critical Error: $_" "CRITICAL"
    exit 1
}
