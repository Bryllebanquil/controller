# PowerShell Script to Fix Everything

Write-Host "================================================================================" -ForegroundColor Green
Write-Host "FIXING AGENT - INSTALLING PACKAGES AND COPYING FILES" -ForegroundColor Green
Write-Host "================================================================================" -ForegroundColor Green
Write-Host ""

# Step 1: Install packages
Write-Host "Step 1: Installing required Python packages..." -ForegroundColor Yellow
pip install numpy opencv-python mss

# Step 2: Copy fixed files (if accessible)
Write-Host ""
Write-Host "Step 2: Attempting to copy fixed files..." -ForegroundColor Yellow

$sourceClient = "/workspace/client.py"
$sourceController = "/workspace/controller.py"
$destDir = "C:\Users\Brylle\render deploy\controller"

if (Test-Path $sourceClient) {
    Write-Host "  Copying client.py..." -ForegroundColor Cyan
    Copy-Item $sourceClient "$destDir\client.py" -Force
    Write-Host "  ✓ client.py copied!" -ForegroundColor Green
} else {
    Write-Host "  ✗ Cannot access /workspace/client.py" -ForegroundColor Red
    Write-Host "  You need to manually copy the fixed files from your repository" -ForegroundColor Yellow
}

if (Test-Path $sourceController) {
    Write-Host "  Copying controller.py..." -ForegroundColor Cyan
    Copy-Item $sourceController "$destDir\controller.py" -Force
    Write-Host "  ✓ controller.py copied!" -ForegroundColor Green
} else {
    Write-Host "  ✗ Cannot access /workspace/controller.py" -ForegroundColor Red
}

Write-Host ""
Write-Host "================================================================================" -ForegroundColor Green
Write-Host "DONE!" -ForegroundColor Green
Write-Host "================================================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Now restart your agent:" -ForegroundColor Yellow
Write-Host "  cd 'C:\Users\Brylle\render deploy\controller'" -ForegroundColor Cyan
Write-Host "  python client.py" -ForegroundColor Cyan
Write-Host ""

Read-Host "Press Enter to exit"
