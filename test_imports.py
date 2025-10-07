#!/usr/bin/env python3
"""
Test Import Script - Diagnose import issues
"""

import sys

print("=" * 80)
print("  TESTING PACKAGE IMPORTS")
print("=" * 80)
print(f"\nPython: {sys.version}")
print(f"Executable: {sys.executable}")
print("\n" + "=" * 80)

packages_to_test = [
    'win32api',
    'win32con',
    'socketio',
    'socketio.client',
    'numpy',
    'cv2',
    'pygame',
    'aiohttp',
    'pywin32',
]

print("\nTesting imports...\n")

for pkg in packages_to_test:
    try:
        exec(f"import {pkg}")
        print(f"✅ {pkg:20} - SUCCESS")
    except ImportError as e:
        print(f"❌ {pkg:20} - FAILED: {e}")
    except Exception as e:
        print(f"⚠️  {pkg:20} - ERROR: {e}")

print("\n" + "=" * 80)
print("  CHECKING PACKAGE INSTALLATION")
print("=" * 80 + "\n")

import subprocess

packages = [
    'pywin32',
    'python-socketio',
    'numpy',
    'opencv-python',
    'pygame',
    'aiohttp',
]

for pkg in packages:
    result = subprocess.run(
        [sys.executable, "-m", "pip", "show", pkg],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        # Package is installed
        for line in result.stdout.split('\n'):
            if line.startswith('Version:') or line.startswith('Location:'):
                print(f"✅ {pkg:20} - {line.strip()}")
                break
    else:
        print(f"❌ {pkg:20} - NOT INSTALLED")

print("\n" + "=" * 80)
print("DONE!")
print("=" * 80)
