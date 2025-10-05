# PowerShell script to run the agent with all dependencies installed

Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "  PYTHON AGENT - STARTUP SCRIPT" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""

# Check if packages are already installed
Write-Host "[1/2] Checking package installation..." -ForegroundColor Yellow
$packagesInstalled = $true

$packages = @(
    "eventlet",
    "python-socketio",
    "pywin32",
    "numpy",
    "opencv-python",
    "pygame",
    "aiohttp"
)

foreach ($pkg in $packages) {
    $result = python -m pip show $pkg 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  ❌ $pkg - NOT INSTALLED" -ForegroundColor Red
        $packagesInstalled = $false
    } else {
        Write-Host "  ✅ $pkg - Installed" -ForegroundColor Green
    }
}

if (-not $packagesInstalled) {
    Write-Host ""
    Write-Host "[2/2] Installing missing packages..." -ForegroundColor Yellow
    Write-Host "================================================================================" -ForegroundColor Cyan
    
    # Uninstall old versions
    python -m pip uninstall -y python-socketio python-engineio eventlet
    
    # Install compatible versions
    python -m pip install eventlet==0.33.3
    python -m pip install python-engineio==4.8.0
    python -m pip install python-socketio==5.7.0
    python -m pip install pywin32 numpy opencv-python pygame aiohttp
    
    Write-Host ""
    Write-Host "✅ Packages installed!" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "✅ All packages already installed!" -ForegroundColor Green
}

Write-Host ""
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "  STARTING PYTHON AGENT" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""

# Run the agent
python client.py
