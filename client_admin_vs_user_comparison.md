# client.py Admin vs. Standard User Capabilities — Comprehensive Comparison

## Overview
- This document compares what client.py can do when run as Administrator versus as a standard (non-admin) user.
- Focus areas include registry operations, Group Policy, UAC configuration, Windows Defender changes, notifications control, scheduled tasks, services, startup persistence, environment hijacks, COM/IFEO techniques, and file system actions.
- Use this to understand which actions require elevation and which are per-user only.

## Privilege Impact Summary
- Administrator
  - Full write to HKLM and HKLM\SOFTWARE\Policies registry hives
  - Modify Group Policy-backed settings and UAC policy (EnableLUA, ConsentPromptBehaviorAdmin, PromptOnSecureDesktop)
  - Create/modify/delete services and system scheduled tasks
  - Write to protected locations (System32/SysWOW64), stop protected processes, alter Windows Defender enforcement
- Standard User
  - Write to HKCU and HKCU\Software\Classes (per-user associations and protocol handlers)
  - Create per-user scheduled tasks and startup entries
  - Attempt protocol/association-based elevation paths (effect depends on OS build and UAC settings)
  - Cannot change HKLM or Group Policy-backed settings; cannot create system services; cannot write to protected directories

## Capability Matrix
| Area | Admin | Standard User |
|------|------|---------------|
| HKLM policy keys (UAC, Defender) | Allowed | Not allowed |
| HKCU keys (Run, protocol handlers) | Allowed | Allowed |
| Group Policy registry (HKLM\SOFTWARE\Policies\...) | Allowed | Not allowed |
| UAC policy (EnableLUA, ConsentPromptBehaviorAdmin, PromptOnSecureDesktop) | Allowed | Not allowed |
| Windows Defender policy (DisableRealtimeMonitoring, etc.) | Allowed | Not allowed |
| Windows Defender runtime prefs (Set-MpPreference) | Allowed | Often blocked; requires elevation |
| Scheduled tasks (system) | Create/Run/Delete | Query only; cannot modify system tasks |
| Services (create/delete/stop) | Allowed | Not allowed |
| Startup persistence (HKCU Run/RunOnce) | Allowed | Allowed |
| Notifications suppression (HKCU) | Allowed | Allowed |
| Notifications suppression (HKLM\Policies) | Allowed | Not allowed |
| COM CLSID hijacks under HKCU | Allowed | Allowed |
| IFEO hooks (HKLM Image File Execution Options) | Allowed | Not allowed |
| Environment hijack (HKCU windir) | Allowed | Allowed |
| System directory writes (System32/SysWOW64) | Allowed | Not allowed |
| Killing protected processes | Allowed (with care) | Not allowed |

## Registry and Group Policy
- Administrator
  - UAC policy: HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System
    - EnableLUA, ConsentPromptBehaviorAdmin, PromptOnSecureDesktop
  - Group Policy-backed nodes:
    - HKLM\SOFTWARE\Policies\Microsoft\Windows Defender (and subkeys)
    - HKLM\SOFTWARE\Policies\Microsoft\Windows Defender Security Center (Notifications, Systray)
    - HKLM\SOFTWARE\Policies\Microsoft\Windows\Explorer (DisableNotificationCenter)
  - IFEO (Image File Execution Options):
    - HKLM\SOFTWARE\...\Image File Execution Options\<process>.exe
- Standard User
  - Per-user nodes:
    - HKCU\Software\Microsoft\Windows\CurrentVersion\Run / RunOnce
    - HKCU\Software\Classes\ms-settings, mscfile, exefile, Folder, AppX... (protocol/association hijacks)
    - HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\PushNotifications (ToastEnabled)
    - HKCU\SOFTWARE\Microsoft\Windows Defender\UX Configuration (Notification_Suppress)
    - HKCU\Environment / HKCU\Volatile Environment (windir)
  - Cannot write to HKLM or HKLM\SOFTWARE\Policies

## UAC Configuration and Bypass Attempts
- Administrator
  - Can directly set UAC policy values to suppress prompts
  - Can run system-level bypass helpers and write HKLM keys as part of flows
- Standard User
  - Can set HKCU\Software\Classes protocol/association entries (e.g., ms-settings, mscfile, exefile, Folder, AppX WSReset)
  - Bypass success depends on Windows version, UAC level, and mitigation state; no guarantee of elevation
  - Cannot persist UAC policy changes in HKLM

## Windows Defender and Tamper Protection
- Administrator
  - Registry: HKLM\SOFTWARE\Policies\Microsoft\Windows Defender\Real-Time Protection (DisableRealtimeMonitoring, DisableBehaviorMonitoring, etc.)
  - PowerShell: Set-MpPreference to re-enable/disable runtime protections
  - Tamper Protection: HKLM\SOFTWARE\Microsoft\Windows Defender\Features (may affect ability to write Defender policies)
- Standard User
  - Limited to HKCU notification UX settings; cannot alter Defender enforcement or policies

## Notifications and UX
- Administrator
  - Can set HKLM policy flags (DisableNotificationCenter) and Defender Security Center systray/notifications
- Standard User
  - Can toggle HKCU PushNotifications.ToastEnabled and Defender UX Notification_Suppress
  - Changes affect current user only; do not enforce system-wide behavior

## Scheduled Tasks and Services
- Administrator
  - schtasks: create/delete/run system tasks (e.g., WindowsSecurityUpdate*)
  - sc.exe: stop/delete/create services (WindowsSecurityService, WindowsSecurityUpdate, SystemUpdateService)
- Standard User
  - schtasks query: view tasks; cannot modify system tasks
  - No service control rights

## Startup and Persistence
- Administrator
  - HKCU Run/RunOnce (per-user)
  - HKLM Run/RunOnce (all users), if used
  - Startup folder entries in per-user and common locations
- Standard User
  - HKCU Run/RunOnce only and per-user Startup folder entries

## Environment and COM/IFEO Techniques
- Administrator
  - IFEO under HKLM for process interception
  - COM hijacks may be combined with HKLM writes
- Standard User
  - COM CLSID hijacks and AppX protocol hijacks in HKCU\Software\Classes
  - windir environment override in HKCU for certain task flows; success depends on OS mitigations

## File System Actions
- Administrator
  - Write/delete in protected paths (System32, SysWOW64), deploy binaries broadly
  - Kill protected processes and write to program locations under Program Files
- Standard User
  - Write within %APPDATA%, %LOCALAPPDATA%, %TEMP%; cannot write to protected directories

## Risks and Side Effects
- HKCU association/protocol changes can disrupt shell handling for the current user if left in place
- HKLM policy changes affect all users and can degrade system security posture
- Service/task modifications can cause startup errors or system instability if misconfigured
- Defender policy changes may trigger security product alerts or be blocked under Tamper Protection

## Testing and Verification
- Use uac_bypass_tester.py audit mode to snapshot current state without modifying the system:
  - python uac_bypass_tester.py
  - Select “4. Audit registry and policies”
  - Outputs JSON report of UAC policy, notifications, bypass keys, IFEO, COM hijacks, environment, tasks, services, startup entries, and suspicious files
- For cleanup, use:
  - restore.ps1 for comprehensive removal of artifacts, including Malwarebytes detections

## References
- client.py
  - UAC policy handling and registry writes: [client.py](file:///c:/Users/vboxuser_sphinx/testing/testing/client.py)
  - Notifications and Defender policy changes: [client.py](file:///c:/Users/vboxuser_sphinx/testing/testing/client.py)
  - Protocol/association and environment hijacks (ms-settings, mscfile, exefile, Folder, AppX; windir): [client.py](file:///c:/Users/vboxuser_sphinx/testing/testing/client.py)
- uac_bypass_tester.py
  - Audit mode and report: [uac_bypass_tester.py](file:///c:/Users/vboxuser_sphinx/testing/testing/uac_bypass_tester.py)
- restore.ps1
  - System restore and malware artifacts cleanup: [restore.ps1](file:///c:/Users/vboxuser_sphinx/testing/testing/restore.ps1)

