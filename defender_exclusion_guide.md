# Windows Defender Exclusion Manager

This tool allows administrators to programmatically manage Windows Defender exclusions and real-time protection settings. It ensures that exclusions are applied persistently and provides logging for audit purposes.

## 📋 Features

*   **Add Exclusions**: Support for Paths (Directories/Files), Processes, and Extensions.
*   **Remove Exclusions**: Clean up rules when no longer needed.
*   **Verification**: Check if a rule is currently active.
*   **Real-time Protection Toggle**: Temporarily disable/enable protection.
*   **Auto-Elevation**: Automatically requests Administrator privileges if run as a standard user.
*   **Logging**: All operations are logged to `defender_manager.log`.

## 🚀 Installation & Usage

1.  Download `defender_exclusion_manager.ps1`.
2.  Open PowerShell.
3.  Run the script with the desired parameters.

### Syntax

```powershell
.\defender_exclusion_manager.ps1 -Action <Action> [-Type <Type>] [-Value <Value>]
```

### Parameters

*   **Action**: `Add`, `Remove`, `Verify`, `DisableRealTime`, `EnableRealTime`
*   **Type**: `Path`, `Process`, `Extension` (Required for Add/Remove/Verify)
*   **Value**: The specific path, process name, or extension (e.g., "C:\App", "app.exe", ".log")

### Examples

**1. Exclude a specific folder:**
```powershell
.\defender_exclusion_manager.ps1 -Action Add -Type Path -Value "C:\MyDevelopmentFolder"
```

**2. Exclude a process:**
```powershell
.\defender_exclusion_manager.ps1 -Action Add -Type Process -Value "debug_tool.exe"
```

**3. Verify an exclusion:**
```powershell
.\defender_exclusion_manager.ps1 -Action Verify -Type Path -Value "C:\MyDevelopmentFolder"
```

**4. Temporarily Disable Real-time Protection:**
```powershell
.\defender_exclusion_manager.ps1 -Action DisableRealTime
```

## 🧪 Test Cases

| ID | Test Scenario | Command | Expected Result |
| :--- | :--- | :--- | :--- |
| TC01 | Add Directory Exclusion | `.\defender_exclusion_manager.ps1 -Action Add -Type Path -Value "C:\TempTest"` | Log shows "SUCCESS", Get-MpPreference shows path. |
| TC02 | Verify Exclusion | `.\defender_exclusion_manager.ps1 -Action Verify -Type Path -Value "C:\TempTest"` | Output "Verification: Exclusion exists". |
| TC03 | Remove Exclusion | `.\defender_exclusion_manager.ps1 -Action Remove -Type Path -Value "C:\TempTest"` | Log shows "SUCCESS", path removed from Defender. |
| TC04 | Add Process Exclusion | `.\defender_exclusion_manager.ps1 -Action Add -Type Process -Value "test_proc.exe"` | Log shows "SUCCESS". |
| TC05 | Disable Protection | `.\defender_exclusion_manager.ps1 -Action DisableRealTime` | Real-time protection disabled. |

## ⚠️ Compatibility & Security

*   **OS Support**: Windows 10 (1709+), Windows 11, Windows Server 2016+.
*   **PowerShell**: Version 5.1 or newer.
*   **Security**: This script requires Administrator privileges. Only use this for legitimate development and testing purposes. modifying security settings can expose the system to threats.
