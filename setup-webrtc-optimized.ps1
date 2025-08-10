#!/usr/bin/env pwsh
<#
.SYNOPSIS
    WebRTC Optimized Setup for Windows 11 VM
    
.DESCRIPTION
    This script installs all dependencies needed for SMOOTH, LOW-LATENCY 
    WebRTC streaming (<1 second delay) with proper error handling and verification.
    
.EXAMPLE
    .\setup-webrtc-optimized.ps1
    
.NOTES
    Run as Administrator for best results
    Requires PowerShell 5.1+ or PowerShell Core 6.0+
#>

# Set execution policy for this session
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process -Force

# Colors for output
$Red = "`e[31m"
$Green = "`e[32m"
$Yellow = "`e[33m"
$Blue = "`e[34m"
$Magenta = "`e[35m"
$Cyan = "`e[36m"
$Reset = "`e[0m"

function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    
    switch ($Color) {
        "Red" { Write-Host $Message -ForegroundColor Red }
        "Green" { Write-Host $Message -ForegroundColor Green }
        "Yellow" { Write-Host $Message -ForegroundColor Yellow }
        "Blue" { Write-Host $Message -ForegroundColor Blue }
        "Magenta" { Write-Host $Message -ForegroundColor Magenta }
        "Cyan" { Write-Host $Message -ForegroundColor Cyan }
        default { Write-Host $Message }
    }
}

function Test-Dependency {
    param(
        [string]$Command,
        [string]$Name,
        [string]$InstallUrl = ""
    )
    
    try {
        $result = & $Command --version 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-ColorOutput "✅ $Name found: $result" "Green"
            return $true
        } else {
            throw "Command failed"
        }
    } catch {
        Write-ColorOutput "❌ ERROR: $Name is not installed or not in PATH" "Red"
        if ($InstallUrl) {
            Write-ColorOutput "   Download from: $InstallUrl" "Yellow"
        }
        return $false
    }
}

function Install-Package {
    param(
        [string]$Package,
        [string]$Description
    )
    
    Write-ColorOutput "Installing $Description..." "Blue"
    try {
        pip install $Package
        if ($LASTEXITCODE -eq 0) {
            Write-ColorOutput "✅ $Description installed successfully" "Green"
            return $true
        } else {
            Write-ColorOutput "❌ Failed to install $Description" "Red"
            return $false
        }
    } catch {
        Write-ColorOutput "❌ Error installing $Description: $_" "Red"
        return $false
    }
}

function Test-Import {
    param(
        [string]$Module,
        [string]$Description
    )
    
    try {
        python -c "import $Module; print('✅ $Description imported successfully')" 2>$null
        if ($LASTEXITCODE -eq 0) {
            return $true
        } else {
            throw "Import failed"
        }
    } catch {
        Write-ColorOutput "❌ ERROR: $Description failed to import" "Red"
        Write-ColorOutput "   WebRTC streaming will NOT work properly" "Yellow"
        return $false
    }
}

# Main script
Write-ColorOutput "========================================" "Cyan"
Write-ColorOutput "WebRTC Optimized Setup for Windows 11 VM" "Cyan"
Write-ColorOutput "========================================" "Cyan"
Write-Host ""

Write-ColorOutput "This script will install all dependencies needed for" "White"
Write-ColorOutput "SMOOTH, LOW-LATENCY WebRTC streaming (<1 second delay)" "White"
Write-Host ""

# Check prerequisites
Write-ColorOutput "Checking Prerequisites..." "Blue"
Write-Host ""

$pythonOk = Test-Dependency "python" "Python" "https://python.org"
$pipOk = Test-Dependency "pip" "pip" "https://pip.pypa.io"

if (-not $pythonOk -or -not $pipOk) {
    Write-ColorOutput "`n❌ Prerequisites not met. Please install missing components." "Red"
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""

# Upgrade pip
Write-ColorOutput "Upgrading pip..." "Blue"
python -m pip install --upgrade pip
if ($LASTEXITCODE -eq 0) {
    Write-ColorOutput "✅ pip upgraded successfully" "Green"
} else {
    Write-ColorOutput "⚠️  pip upgrade failed, continuing..." "Yellow"
}

Write-Host ""

# Install WebRTC dependencies
Write-ColorOutput "========================================" "Cyan"
Write-ColorOutput "Installing WebRTC Dependencies..." "Cyan"
Write-ColorOutput "========================================" "Cyan"

$dependencies = @(
    @{Package="aiortc>=0.9.0"; Description="Core WebRTC library"},
    @{Package="aiohttp>=3.8.0"; Description="Async HTTP for WebRTC"},
    @{Package="python-socketio[client]>=5.7.0"; Description="Real-time communication"},
    @{Package="mss>=6.1.0"; Description="Fast screen capture"},
    @{Package="opencv-python>=4.5.0"; Description="Video processing"},
    @{Package="PyAudio>=0.2.11"; Description="Audio capture"},
    @{Package="numpy>=1.21.0"; Description="Fast array operations"},
    @{Package="Pillow>=8.3.0"; Description="Image processing"},
    @{Package="dxcam>=1.0.0"; Description="Alternative screen capture"},
    @{Package="pyautogui>=0.9.53"; Description="Fallback screen capture"},
    @{Package="psutil>=5.8.0"; Description="System monitoring"},
    @{Package="asyncio-mqtt>=0.11.0"; Description="Async message queuing"},
    @{Package="pynput>=1.7.0"; Description="Input control"},
    @{Package="keyboard>=0.13.5"; Description="Alternative input method"},
    @{Package="websockets>=10.0"; Description="WebSocket support"},
    @{Package="requests>=2.25.0"; Description="HTTP requests"},
    @{Package="cryptography>=3.4.0"; Description="Encryption"},
    @{Package="pywin32>=300"; Description="Windows API access"},
    @{Package="wmi>=1.5.1"; Description="Windows Management"}
)

$failedPackages = @()

foreach ($dep in $dependencies) {
    $success = Install-Package -Package $dep.Package -Description $dep.Description
    if (-not $success) {
        $failedPackages += $dep.Description
    }
    Write-Host ""
}

# Report installation results
if ($failedPackages.Count -gt 0) {
    Write-ColorOutput "⚠️  Some packages failed to install:" "Yellow"
    foreach ($pkg in $failedPackages) {
        Write-ColorOutput "   - $pkg" "Yellow"
    }
    Write-Host ""
} else {
    Write-ColorOutput "✅ All packages installed successfully!" "Green"
    Write-Host ""
}

# Verify WebRTC installation
Write-ColorOutput "========================================" "Cyan"
Write-ColorOutput "Verifying WebRTC Installation..." "Cyan"
Write-ColorOutput "========================================" "Cyan"

$criticalModules = @(
    @{Module="aiortc"; Description="WebRTC core"},
    @{Module="cv2"; Description="OpenCV"},
    @{Module="mss"; Description="Screen capture"},
    @{Module="pyaudio"; Description="Audio capture"}
)

$allModulesOk = $true
foreach ($module in $criticalModules) {
    $ok = Test-Import -Module $module.Module -Description $module.Description
    if (-not $ok) {
        $allModulesOk = $false
    }
}

Write-Host ""

# Create startup scripts
Write-ColorOutput "========================================" "Cyan"
Write-ColorOutput "Creating Startup Scripts..." "Cyan"
Write-ColorOutput "========================================" "Cyan"

# Create optimized startup script
$startupScript = @"
@echo off
echo ========================================
echo WebRTC Agent - Optimized for Low Latency
echo ========================================
echo.
echo WebRTC Configuration:
echo - Target FPS: 30
echo - Ultra-low latency mode: Enabled
echo - Hardware acceleration: Enabled
echo - Adaptive bitrate: Enabled
echo.
echo Starting agent...
python main.py --webrtc-optimized --ultra-low-latency
echo.
echo Agent stopped. Press any key to exit...
pause >nul
"@

$startupScript | Out-File -FilePath "start-webrtc-optimized.bat" -Encoding ASCII

# Create test script
$testScript = @"
@echo off
echo Testing WebRTC Installation...
echo.
python -c "import aiortc; print('WebRTC: OK'); import cv2; print('OpenCV: OK'); import mss; print('MSS: OK'); import pyaudio; print('PyAudio: OK'); print('All dependencies ready for smooth streaming!')"
echo.
echo Test completed. Press any key to exit...
pause >nul
"@

$testScript | Out-File -FilePath "test-webrtc.bat" -Encoding ASCII

Write-ColorOutput "✅ Created startup scripts:" "Green"
Write-ColorOutput "   - start-webrtc-optimized.bat (for production use)" "White"
Write-ColorOutput "   - test-webrtc.bat (to verify installation)" "White"

Write-Host ""

# Final status
Write-ColorOutput "========================================" "Cyan"
Write-ColorOutput "WebRTC Setup Complete!" "Cyan"
Write-ColorOutput "========================================" "Cyan"
Write-Host ""

if ($allModulesOk) {
    Write-ColorOutput "🎉 SUCCESS: All WebRTC dependencies are ready!" "Green"
    Write-Host ""
    Write-ColorOutput "To test your setup:" "White"
    Write-ColorOutput "   1. Run: .\test-webrtc.bat" "Yellow"
    Write-ColorOutput "   2. If all tests pass, run: .\start-webrtc-optimized.bat" "Yellow"
    Write-Host ""
    Write-ColorOutput "Expected performance:" "White"
    Write-ColorOutput "   - Screen capture: 30 FPS" "Cyan"
    Write-ColorOutput "   - Latency: <1 second" "Cyan"
    Write-ColorOutput "   - Smooth streaming with adaptive quality" "Cyan"
} else {
    Write-ColorOutput "⚠️  WARNING: Some critical modules failed to import" "Yellow"
    Write-ColorOutput "   WebRTC streaming may not work properly" "Yellow"
    Write-Host ""
    Write-ColorOutput "Troubleshooting:" "White"
    Write-ColorOutput "   1. Check if Windows Defender is blocking Python" "Yellow"
    Write-ColorOutput "   2. Ensure you have Visual C++ redistributable installed" "Yellow"
    Write-ColorOutput "   3. Try running as Administrator" "Yellow"
    Write-ColorOutput "   4. Restart your terminal/command prompt" "Yellow"
}

Write-Host ""
Write-ColorOutput "If you experience issues:" "White"
Write-ColorOutput "   1. Check Windows Defender isn't blocking Python" "Yellow"
Write-ColorOutput "   2. Ensure you have Visual C++ redistributable" "Yellow"
Write-ColorOutput "   3. Try running as Administrator" "Yellow"
Write-ColorOutput "   4. Check the test-webrtc.bat output for specific errors" "Yellow"

Write-Host ""
Read-Host "Press Enter to exit"