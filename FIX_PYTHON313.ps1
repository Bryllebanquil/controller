# Python 3.13 Compatibility Fix Script

Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "  PYTHON 3.13 COMPATIBILITY FIX" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "This will install Python 3.13 compatible versions:" -ForegroundColor Yellow
Write-Host "  - eventlet >= 0.35.0 (Python 3.13 compatible)" -ForegroundColor White
Write-Host "  - python-engineio >= 4.8.0" -ForegroundColor White
Write-Host "  - python-socketio >= 5.12.0 (compatible with flask-socketio)" -ForegroundColor White
Write-Host ""

Write-Host "[1/3] Uninstalling old versions..." -ForegroundColor Yellow
python -m pip uninstall -y python-socketio python-engineio eventlet

Write-Host ""
Write-Host "[2/3] Installing Python 3.13 compatible versions..." -ForegroundColor Yellow
python -m pip install "eventlet>=0.35.0" "python-engineio>=4.8.0" "python-socketio>=5.12.0"

Write-Host ""
Write-Host "[3/3] Installing other dependencies..." -ForegroundColor Yellow
python -m pip install pywin32 numpy opencv-python pygame aiohttp

Write-Host ""
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "  INSTALLATION COMPLETE!" -ForegroundColor Green
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Now running the agent..." -ForegroundColor Yellow
Write-Host ""

python client.py
