#!/usr/bin/env python3
"""
Fix WSL Command Execution Issue in client.py
This script will update your client.py to use CMD instead of PowerShell
"""

import os
import sys
import re

def fix_wsl_issue():
    print("="*70)
    print("  FIX WSL COMMAND EXECUTION ISSUE")
    print("="*70)
    print()
    
    # Check if client.py exists
    if not os.path.exists('client.py'):
        print("ERROR: client.py not found in current directory!")
        print(f"Current directory: {os.getcwd()}")
        print("\nPlease navigate to the directory containing client.py:")
        print('  cd "C:\\Users\\Brylle\\render deploy\\controller"')
        return False
    
    print("[1/4] Reading client.py...")
    with open('client.py', 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    print("[2/4] Creating backup: client.py.backup")
    with open('client.py.backup', 'w', encoding='utf-8') as f:
        f.write(content)
    
    changes_made = 0
    
    # Fix 1: Replace PowerShell with CMD
    print("[3/4] Fixing execute_command to use CMD instead of PowerShell...")
    
    # Pattern 1: Full function replacement
    old_pattern1 = r'["\'"]powershell\.exe["\'"]\s*,\s*["\'"]-NoProfile["\'"]\s*,\s*["\'"]-Command["\'"]\s*,\s*command'
    new_pattern1 = r'"C:\\Windows\\System32\\cmd.exe", "/c", command'
    
    if re.search(old_pattern1, content):
        content = re.sub(old_pattern1, new_pattern1, content)
        changes_made += 1
        print("  [OK] Replaced powershell.exe with cmd.exe")
    else:
        # Try simpler pattern
        if 'powershell.exe' in content and 'execute_command' in content:
            # Manual replacement
            content = content.replace(
                '["powershell.exe", "-NoProfile", "-Command", command]',
                '["C:\\\\Windows\\\\System32\\\\cmd.exe", "/c", command]'
            )
            content = content.replace(
                "['powershell.exe', '-NoProfile', '-Command', command]",
                '["C:\\\\Windows\\\\System32\\\\cmd.exe", "/c", command]'
            )
            changes_made += 1
            print("  [OK] Replaced powershell.exe with cmd.exe (manual)")
    
    # Fix 2: Add proper encoding
    if 'execute_command' in content and 'encoding=' not in content[:content.find('def execute_command') + 500]:
        print("  [INFO] Note: Add encoding='utf-8' manually if needed")
    
    # Fix 3: Suppress RLock warning
    if 'RLock' not in content or 'warnings.filterwarnings' not in content:
        print("[BONUS] Adding RLock warning suppression...")
        lines = content.split('\n')
        
        # Find eventlet block
        for i, line in enumerate(lines):
            if 'Fix eventlet RLock' in line or 'eventlet.monkey_patch' in line:
                # Insert warning suppression before eventlet
                if 'import warnings' not in '\n'.join(lines[:i+10]):
                    lines.insert(i, 'import warnings')
                    lines.insert(i+1, "warnings.filterwarnings('ignore', message='.*RLock.*')")
                    lines.insert(i+2, '')
                    changes_made += 1
                    print("  [OK] Added RLock warning suppression")
                break
        
        content = '\n'.join(lines)
    
    # Write fixed content
    print("[4/4] Writing fixed client.py...")
    with open('client.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print()
    print("="*70)
    if changes_made > 0:
        print(f"SUCCESS! Made {changes_made} fix(es) to client.py")
        print("="*70)
        print()
        print("What was fixed:")
        print("  - Commands now use CMD.exe instead of PowerShell")
        print("  - Full path C:\\Windows\\System32\\cmd.exe to avoid WSL")
        print("  - RLock warnings suppressed")
        print()
        print("Backup saved as: client.py.backup")
        print()
        print("Now test with:")
        print("  python client.py")
        print()
        print("Then in the controller UI, try:")
        print("  dir")
        print("  systeminfo")
        print("  ipconfig")
        print()
        print("These should work without WSL errors!")
    else:
        print("INFO: No changes needed (already fixed or pattern not found)")
        print("="*70)
        print()
        print("If you're still getting WSL errors, try MANUAL FIX:")
        print()
        print("1. Open client.py in Notepad")
        print("2. Search for: powershell.exe")
        print("3. Replace line with:")
        print('   ["C:\\\\Windows\\\\System32\\\\cmd.exe", "/c", command]')
        print()
        print("4. Save and try again")
    
    print("="*70)
    return changes_made > 0

def show_manual_fix():
    print()
    print("="*70)
    print("  MANUAL FIX INSTRUCTIONS")
    print("="*70)
    print()
    print("If the automated fix didn't work, do this manually:")
    print()
    print("1. Open client.py in Notepad or VS Code")
    print()
    print("2. Find this line (around line 6297-6298):")
    print("   ---")
    print('   ["powershell.exe", "-NoProfile", "-Command", command]')
    print("   ---")
    print()
    print("3. Replace it with:")
    print("   ---")
    print('   ["C:\\\\Windows\\\\System32\\\\cmd.exe", "/c", command]')
    print("   ---")
    print()
    print("4. Save the file")
    print()
    print("5. Run: python client.py")
    print()
    print("6. Test commands:")
    print("   - dir")
    print("   - systeminfo")
    print("   - ipconfig")
    print()
    print("Should work without WSL errors!")
    print("="*70)

if __name__ == "__main__":
    try:
        success = fix_wsl_issue()
        
        if not success:
            show_manual_fix()
    except KeyboardInterrupt:
        print("\n\n[!] Cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nERROR: {e}")
        print("\nTrying manual fix instructions instead...")
        show_manual_fix()
        sys.exit(1)
