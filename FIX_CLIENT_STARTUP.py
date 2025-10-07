#!/usr/bin/env python3
"""
Quick fix for client.py startup errors
Run this script in the same directory as client.py
"""

import os
import sys

def fix_client_py():
    """Fix the two startup errors in client.py"""
    
    client_file = "client.py"
    
    if not os.path.exists(client_file):
        print(f"ERROR: {client_file} not found in current directory!")
        print(f"Current directory: {os.getcwd()}")
        return False
    
    print(f"Reading {client_file}...")
    with open(client_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Backup original
    backup_file = "client.py.backup"
    print(f"Creating backup: {backup_file}")
    with open(backup_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    changes_made = 0
    
    # Fix 1: Remove ssl=True from monkey_patch
    if "ssl=True" in content:
        print("Fixing: Removing ssl=True from eventlet.monkey_patch()...")
        # Replace the entire monkey_patch line
        old_pattern = "eventlet.monkey_patch(all=True, thread=True, time=True, os=True, socket=True, select=True, ssl=True)"
        new_pattern = "eventlet.monkey_patch(all=True, thread=True, time=True, socket=True, select=True)"
        
        if old_pattern in content:
            content = content.replace(old_pattern, new_pattern)
            changes_made += 1
            print("  [OK] Removed ssl=True parameter")
        else:
            # Try alternative format
            content = content.replace("ssl=True)", ")")
            content = content.replace(", ssl=True", "")
            changes_made += 1
            print("  [OK] Removed ssl=True parameter (alternative method)")
    
    # Fix 2: Ensure 'import os' is at the top (after eventlet block)
    lines = content.split('\n')
    
    # Find the eventlet block
    eventlet_end = -1
    for i, line in enumerate(lines):
        if "EVENTLET_PATCHED = False" in line and i < 20:
            eventlet_end = i
            break
    
    if eventlet_end > 0:
        # Check if 'import os' exists before line 105
        has_early_os_import = False
        for i in range(eventlet_end + 1):
            if lines[i].strip().startswith("import os"):
                has_early_os_import = True
                break
        
        if not has_early_os_import:
            print("Fixing: Adding 'import os' at line 3...")
            # Insert after "# This MUST be at the very top..."
            insert_pos = 2  # After the second comment line
            lines.insert(insert_pos, "import os  # Import os FIRST before anything else")
            lines.insert(insert_pos + 1, "")
            changes_made += 1
            print("  [OK] Added 'import os' at top of file")
        else:
            print("  [OK] 'import os' already at top")
    
    # Write fixed content
    if changes_made > 0:
        fixed_content = '\n'.join(lines)
        print(f"\nWriting fixed {client_file}...")
        with open(client_file, 'w', encoding='utf-8') as f:
            f.write(fixed_content)
        
        print(f"\n{'='*60}")
        print(f"SUCCESS! Fixed {changes_made} issue(s) in {client_file}")
        print(f"{'='*60}")
        print(f"Backup saved as: {backup_file}")
        print(f"\nNow try running: python client.py")
        print(f"{'='*60}")
        return True
    else:
        print("\n[INFO] No changes needed - file already looks correct!")
        print("If you're still getting errors, you might be running a different file.")
        return True

if __name__ == "__main__":
    print("="*60)
    print("  CLIENT.PY STARTUP FIX SCRIPT")
    print("="*60)
    print()
    
    success = fix_client_py()
    
    if not success:
        sys.exit(1)
