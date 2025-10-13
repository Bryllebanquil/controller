#!/usr/bin/env python3
"""
Fix Import Issues - Comprehensive Solution
This script fixes Python 3.13 + eventlet import compatibility issues
"""

import subprocess
import sys

def run_command(cmd):
    """Run a command and return success status"""
    try:
        subprocess.check_call(cmd, shell=True)
        return True
    except:
        return False

def main():
    print("=" * 80)
    print("  FIXING IMPORT ISSUES - Python 3.13 + eventlet Compatibility")
    print("=" * 80)
    print("\nThis will reinstall all packages with --force-reinstall to fix import issues.\n")
    
    packages = [
        ("pywin32", "Windows API access"),
        ("python-socketio", "Controller communication - CRITICAL"),
        ("python-engineio", "Socket.IO dependency"),
        ("numpy", "Array operations"),
        ("opencv-python", "Video processing"),
        ("pygame", "GUI features"),
        ("aiohttp", "WebRTC support"),
    ]
    
    print("Packages to reinstall:\n")
    for pkg, desc in packages:
        print(f"  • {pkg:20} - {desc}")
    
    print("\n" + "=" * 80)
    input("\nPress ENTER to continue...")
    
    print("\n" + "=" * 80)
    print("  UNINSTALLING OLD VERSIONS")
    print("=" * 80 + "\n")
    
    # First, uninstall all packages
    for pkg, desc in packages:
        print(f"[*] Uninstalling {pkg}...")
        run_command(f"{sys.executable} -m pip uninstall -y {pkg}")
    
    print("\n" + "=" * 80)
    print("  INSTALLING FRESH VERSIONS")
    print("=" * 80 + "\n")
    
    # Then install fresh versions
    success_count = 0
    failed_packages = []
    
    for pkg, desc in packages:
        print(f"\n[*] Installing {pkg} ({desc})...")
        print("-" * 80)
        
        cmd = f"{sys.executable} -m pip install --no-cache-dir {pkg}"
        if run_command(cmd):
            print(f"[✅] {pkg} installed successfully!")
            success_count += 1
        else:
            print(f"[❌] {pkg} installation FAILED!")
            failed_packages.append(pkg)
    
    print("\n" + "=" * 80)
    print("  INSTALLATION COMPLETE")
    print("=" * 80 + "\n")
    
    print(f"✅ Successfully installed: {success_count}/{len(packages)} packages\n")
    
    if failed_packages:
        print(f"❌ Failed to install: {', '.join(failed_packages)}\n")
        print("Try installing these manually:")
        for pkg in failed_packages:
            print(f"  pip install {pkg}")
    else:
        print("🎉 ALL PACKAGES INSTALLED SUCCESSFULLY!\n")
        print("Now run: python client.py\n")
    
    print("=" * 80)
    input("\nPress ENTER to exit...")

if __name__ == "__main__":
    main()
