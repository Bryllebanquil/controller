#!/usr/bin/env python3
"""
Automatic Dependency Installer for Python Agent
Installs all required packages for the agent to work properly
"""

import subprocess
import sys

def print_header(message):
    """Print a formatted header"""
    print("\n" + "=" * 80)
    print(f"  {message}")
    print("=" * 80 + "\n")

def install_package(package_name, description):
    """Install a single package"""
    print(f"[*] Installing {package_name} ({description})...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
        print(f"[✅] {package_name} installed successfully!\n")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[❌] Failed to install {package_name}: {e}\n")
        return False

def main():
    print_header("PYTHON AGENT - DEPENDENCY INSTALLER")
    
    print("This script will install all required dependencies for the Python Agent.")
    print("The following packages will be installed:\n")
    
    packages = [
        ("pywin32", "Windows API access"),
        ("python-socketio", "Controller communication - FIXES OFFLINE MODE"),
        ("numpy", "Array operations"),
        ("opencv-python", "Video processing"),
        ("pygame", "GUI features"),
        ("aiohttp", "WebRTC support"),
    ]
    
    for pkg, desc in packages:
        print(f"  • {pkg:20} - {desc}")
    
    print("\n")
    
    input("Press ENTER to continue with installation...")
    
    print_header("STARTING INSTALLATION")
    
    success_count = 0
    failed_packages = []
    
    for i, (package, description) in enumerate(packages, 1):
        print(f"\n[{i}/{len(packages)}] Installing {package}...")
        print("-" * 80)
        
        if install_package(package, description):
            success_count += 1
        else:
            failed_packages.append(package)
    
    print_header("INSTALLATION COMPLETE")
    
    print(f"✅ Successfully installed: {success_count}/{len(packages)} packages\n")
    
    if failed_packages:
        print(f"❌ Failed to install: {', '.join(failed_packages)}\n")
        print("Please install these manually using:")
        for pkg in failed_packages:
            print(f"  pip install {pkg}")
        print("\n")
    else:
        print("🎉 ALL PACKAGES INSTALLED SUCCESSFULLY!\n")
        print("You can now run the agent:")
        print("  python client.py\n")
    
    print("=" * 80)
    input("\nPress ENTER to exit...")

if __name__ == "__main__":
    main()
