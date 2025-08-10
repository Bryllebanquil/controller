# Windows 11 Oracle VM Setup Script for WebRTC Agent
# Run as Administrator for best results
# Execution Policy: Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

param(
    [switch]$Force,
    [switch]$SkipTests
)

# Check if running as Administrator
function Test-Administrator {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

if (-not (Test-Administrator)) {
    Write-Warning "Not running as Administrator. Some features may not work properly."
    Write-Host "Consider running PowerShell as Administrator for best results." -ForegroundColor Yellow
    if (-not $Force) {
        $response = Read-Host "Continue anyway? (y/N)"
        if ($response -ne "y" -and $response -ne "Y") {
            exit 1
        }
    }
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "    WebRTC Agent Setup for Windows 11" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Function to write colored output
function Write-Step {
    param([string]$Message, [string]$Status = "INFO")
    $color = switch ($Status) {
        "OK" { "Green" }
        "ERROR" { "Red" }
        "WARNING" { "Yellow" }
        default { "White" }
    }
    Write-Host "[$Status] $Message" -ForegroundColor $color
}

# Step 1: Check Python installation
Write-Step "Checking Python installation..." "INFO"
try {
    $pythonVersion = python --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Step "Python is installed: $pythonVersion" "OK"
    } else {
        throw "Python not found"
    }
} catch {
    Write-Step "Python not found! Please install Python 3.7+ from https://python.org" "ERROR"
    Write-Step "Make sure to check 'Add Python to PATH' during installation" "ERROR"
    Read-Host "Press Enter to exit"
    exit 1
}

# Step 2: Check pip installation
Write-Step "Checking pip installation..." "INFO"
try {
    $pipVersion = pip --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Step "pip is installed: $pipVersion" "OK"
    } else {
        throw "pip not found"
    }
} catch {
    Write-Step "pip not found! Please reinstall Python with pip included" "ERROR"
    Read-Host "Press Enter to exit"
    exit 1
}

# Step 3: Upgrade pip
Write-Step "Upgrading pip..." "INFO"
python -m pip install --upgrade pip
if ($LASTEXITCODE -eq 0) {
    Write-Step "pip upgraded successfully" "OK"
} else {
    Write-Step "pip upgrade failed, continuing anyway..." "WARNING"
}

# Step 4: Create virtual environment
Write-Step "Creating virtual environment..." "INFO"
if (Test-Path "webrtc-env") {
    Write-Step "Virtual environment already exists, removing..." "INFO"
    Remove-Item -Recurse -Force "webrtc-env"
}

python -m venv webrtc-env
if ($LASTEXITCODE -eq 0) {
    Write-Step "Virtual environment created successfully" "OK"
} else {
    Write-Step "Failed to create virtual environment" "ERROR"
    Read-Host "Press Enter to exit"
    exit 1
}

# Step 5: Activate virtual environment and install dependencies
Write-Step "Activating virtual environment and installing dependencies..." "INFO"
$activateScript = "webrtc-env\Scripts\Activate.ps1"
if (Test-Path $activateScript) {
    & $activateScript
    pip install --upgrade pip
    pip install -r requirements-windows.txt
    
    if ($LASTEXITCODE -eq 0) {
        Write-Step "Dependencies installed successfully" "OK"
    } else {
        Write-Step "Some dependencies failed to install" "WARNING"
    }
} else {
    Write-Step "Virtual environment activation script not found" "ERROR"
    Read-Host "Press Enter to exit"
    exit 1
}

# Step 6: Create startup scripts
Write-Step "Creating startup scripts..." "INFO"

# PowerShell startup script
$psStartScript = @"
# PowerShell startup script for WebRTC Agent
Write-Host "Starting WebRTC Agent..." -ForegroundColor Green
Set-Location `$PSScriptRoot
& "webrtc-env\Scripts\Activate.ps1"
python main.py
Read-Host "Press Enter to exit"
"@
Set-Content -Path "start-agent.ps1" -Value $psStartScript

# Batch startup script
$batchStartScript = @"
@echo off
echo Starting WebRTC Agent...
cd /d "%~dp0"
call webrtc-env\Scripts\activate.bat
python main.py
pause
"@
Set-Content -Path "start-agent.bat" -Value $batchStartScript

# Admin batch startup script
$adminBatchScript = @"
@echo off
echo Starting WebRTC Agent as Administrator...
cd /d "%~dp0"
call webrtc-env\Scripts\activate.bat
python main.py --admin
pause
"@
Set-Content -Path "start-agent-admin.bat" -Value $adminBatchScript

# Test dependencies script
$testScript = @"
@echo off
echo Testing WebRTC Agent Dependencies...
cd /d "%~dp0"
call webrtc-env\Scripts\activate.bat
echo Testing imports...
python -c "import aiortc; print('WebRTC: OK')"
python -c "import pyaudio; print('Audio: OK')"
python -c "import mss; print('Screen Capture: OK')"
python -c "import cv2; print('OpenCV: OK')"
echo All tests completed!
pause
"@
Set-Content -Path "test-dependencies.bat" -Value $testScript

Write-Step "Startup scripts created successfully" "OK"

# Step 7: Test dependencies (optional)
if (-not $SkipTests) {
    Write-Step "Testing dependencies..." "INFO"
    & $activateScript
    Write-Host "Testing WebRTC..." -ForegroundColor Cyan
    python -c "import aiortc; print('✅ WebRTC: OK')" 2>$null
    Write-Host "Testing Audio..." -ForegroundColor Cyan
    python -c "import pyaudio; print('✅ Audio: OK')" 2>$null
    Write-Host "Testing Screen Capture..." -ForegroundColor Cyan
    python -c "import mss; print('✅ Screen Capture: OK')" 2>$null
    Write-Host "Testing OpenCV..." -ForegroundColor Cyan
    python -c "import cv2; print('✅ OpenCV: OK')" 2>$null
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "           Setup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

Write-Host "[NEXT STEPS]" -ForegroundColor Yellow
Write-Host "1. Edit main.py and update CONTROLLER_HOST to your controller IP"
Write-Host "2. Test dependencies: run test-dependencies.bat"
Write-Host "3. Start the agent: run start-agent.ps1 or start-agent.bat"
Write-Host ""

Write-Host "[TROUBLESHOOTING]" -ForegroundColor Yellow
Write-Host "- If you get permission errors, run start-agent-admin.bat"
Write-Host "- Check Windows Defender isn't blocking Python"
Write-Host "- Ensure your VM has internet access"
Write-Host ""

Write-Host "[FILES CREATED]" -ForegroundColor Yellow
Write-Host "- webrtc-env\ (Python virtual environment)"
Write-Host "- start-agent.ps1 (PowerShell startup)"
Write-Host "- start-agent.bat (Batch startup)"
Write-Host "- start-agent-admin.bat (Administrator startup)"
Write-Host "- test-dependencies.bat (Dependency testing)"
Write-Host ""

Write-Host "[POWERSHELL USAGE]" -ForegroundColor Cyan
Write-Host "To run PowerShell scripts, you may need to set execution policy:"
Write-Host "Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser"
Write-Host ""

Read-Host "Press Enter to exit"