# PowerShell script to unblock and run svchost.exe properly
# This fixes the "Windows cannot access" error

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Unblock and Run svchost.exe" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if running as admin
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "ERROR: Not running as Administrator!" -ForegroundColor Red
    Write-Host "Please right-click this script and select 'Run as Administrator'" -ForegroundColor Yellow
    Write-Host ""
    pause
    exit 1
}

# Locate the executable
$exePath = Join-Path $PSScriptRoot "dist\svchost.exe"

if (-not (Test-Path $exePath)) {
    Write-Host "ERROR: svchost.exe not found at: $exePath" -ForegroundColor Red
    Write-Host "Please build it first using REBUILD_SVCHOST.bat" -ForegroundColor Yellow
    Write-Host ""
    pause
    exit 1
}

Write-Host "[1/4] Found executable at: $exePath" -ForegroundColor Green
Write-Host ""

# Unblock the file
Write-Host "[2/4] Unblocking the executable..." -ForegroundColor Yellow
try {
    Unblock-File -Path $exePath -ErrorAction Stop
    Write-Host "✓ File unblocked successfully!" -ForegroundColor Green
} catch {
    Write-Host "⚠ Could not unblock: $($_.Exception.Message)" -ForegroundColor Yellow
}
Write-Host ""

# Add Windows Defender exclusion
Write-Host "[3/4] Adding Windows Defender exclusion..." -ForegroundColor Yellow
try {
    Add-MpPreference -ExclusionPath $exePath -ErrorAction Stop
    Write-Host "✓ Windows Defender exclusion added!" -ForegroundColor Green
} catch {
    Write-Host "⚠ Could not add exclusion: $($_.Exception.Message)" -ForegroundColor Yellow
    Write-Host "You may need to add it manually in Windows Security" -ForegroundColor Yellow
}
Write-Host ""

# Run the executable
Write-Host "[4/4] Starting svchost.exe..." -ForegroundColor Yellow
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Launching executable..." -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

try {
    Start-Process -FilePath $exePath -Verb RunAs -ErrorAction Stop
    Write-Host "✓ Successfully launched!" -ForegroundColor Green
    Write-Host "Check if the UAC prompt appears and click 'Yes'" -ForegroundColor Yellow
} catch {
    Write-Host "✗ Failed to launch: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
    Write-Host "Try these steps manually:" -ForegroundColor Yellow
    Write-Host "1. Go to: $exePath" -ForegroundColor White
    Write-Host "2. Right-click → Properties" -ForegroundColor White
    Write-Host "3. Check 'Unblock' at the bottom → Apply" -ForegroundColor White
    Write-Host "4. Right-click → 'Run as administrator'" -ForegroundColor White
}

Write-Host ""
Write-Host "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
