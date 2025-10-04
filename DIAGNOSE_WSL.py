#!/usr/bin/env python3
"""
Diagnose why client.py has WSL issues but simple-client.py works
"""

import subprocess
import platform
import os

print("="*70)
print("  WSL DIAGNOSTIC TOOL")
print("="*70)
print()

# Test 1: Check platform
print("[TEST 1] Platform Check:")
print(f"  System: {platform.system()}")
print(f"  Platform: {platform.platform()}")
print(f"  Machine: {platform.machine()}")
print()

# Test 2: Test PowerShell directly
print("[TEST 2] Testing PowerShell directly:")
try:
    result = subprocess.run(
        ["powershell.exe", "-NoProfile", "-Command", "echo 'PowerShell works'"],
        capture_output=True,
        text=True,
        timeout=5,
        creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
    )
    print(f"  Output: {result.stdout.strip()}")
    print(f"  Error: {result.stderr.strip()}")
    if "PowerShell works" in result.stdout:
        print("  ✅ PowerShell execution WORKS")
    else:
        print("  ❌ PowerShell execution FAILED")
except Exception as e:
    print(f"  ❌ PowerShell error: {e}")
print()

# Test 3: Test PowerShell without full path
print("[TEST 3] Testing PowerShell (no full path):")
try:
    result = subprocess.run(
        ["powershell", "-Command", "Get-Date"],
        capture_output=True,
        text=True,
        timeout=5
    )
    print(f"  Output: {result.stdout.strip()[:100]}")
    if "WSL" in result.stderr or "Linux" in result.stderr:
        print("  ❌ PowerShell is aliased to WSL!")
    else:
        print("  ✅ PowerShell works normally")
except Exception as e:
    print(f"  ❌ Error: {e}")
print()

# Test 4: Test CMD
print("[TEST 4] Testing CMD (cmd.exe):")
try:
    result = subprocess.run(
        ["cmd.exe", "/c", "echo CMD works"],
        capture_output=True,
        text=True,
        timeout=5
    )
    print(f"  Output: {result.stdout.strip()}")
    if "CMD works" in result.stdout:
        print("  ✅ CMD execution WORKS")
    else:
        print("  ❌ CMD execution FAILED")
except Exception as e:
    print(f"  ❌ CMD error: {e}")
print()

# Test 5: Test full path CMD
print("[TEST 5] Testing CMD (full path):")
try:
    result = subprocess.run(
        ["C:\\Windows\\System32\\cmd.exe", "/c", "echo Full path CMD works"],
        capture_output=True,
        text=True,
        timeout=5
    )
    print(f"  Output: {result.stdout.strip()}")
    if "Full path CMD works" in result.stdout:
        print("  ✅ Full path CMD WORKS")
    else:
        print("  ❌ Full path CMD FAILED")
except Exception as e:
    print(f"  ❌ Error: {e}")
print()

# Test 6: Check WSL status
print("[TEST 6] Checking WSL status:")
try:
    result = subprocess.run(
        ["wsl.exe", "--status"],
        capture_output=True,
        text=True,
        timeout=5
    )
    if "no installed distributions" in result.stdout.lower() or "no installed distributions" in result.stderr.lower():
        print("  ❌ WSL is installed but has NO distributions")
        print("  ⚠️ This is causing the problem!")
    elif result.returncode == 0:
        print("  ✅ WSL is installed and configured")
        print(f"  Output: {result.stdout.strip()[:200]}")
    else:
        print("  ℹ️ WSL check inconclusive")
except FileNotFoundError:
    print("  ✅ WSL is NOT installed (good!)")
except Exception as e:
    print(f"  ℹ️ WSL check error: {e}")
print()

# Test 7: Check which powershell is being used
print("[TEST 7] Checking PowerShell location:")
try:
    result = subprocess.run(
        ["where", "powershell"],
        capture_output=True,
        text=True,
        timeout=5
    )
    paths = result.stdout.strip().split('\n')
    for p in paths:
        print(f"  - {p}")
        if "wsl" in p.lower() or "linux" in p.lower():
            print("    ⚠️ This is a WSL alias!")
except Exception as e:
    print(f"  Error: {e}")
print()

# Recommendation
print("="*70)
print("  RECOMMENDATION")
print("="*70)
print()

print("Based on diagnostics, the best fix is:")
print()
print("Option 1: Use the working simple-client.py execute_command:")
print("  1. Copy the execute_command function from simple-client.py")
print("  2. Replace it in client.py")
print("  3. This should work since simple-client.py works for you")
print()
print("Option 2: Disable WSL:")
print("  1. Run as Administrator:")
print("     dism.exe /online /disable-feature /featurename:Microsoft-Windows-Subsystem-Linux")
print("  2. Restart PC")
print()
print("Option 3: Install a WSL distribution:")
print("  1. wsl --install Ubuntu")
print("  2. This will satisfy WSL but might slow down commands")
print()
print("RECOMMENDED: Option 1 (use simple-client.py's execute_command)")
print()
print("="*70)
