# Client.py Bypasses Analysis - Complete Feature Extraction

## Overview
This document contains a comprehensive analysis of all bypasses functionality in client.py that needs to be mirrored in the bypasses module and registry system.

## Core Bypass Categories

### 1. UAC Bypass System
**Location**: Lines ~1000-2000, ~18000-19000

**Key Functions**:
- `UACBypassBase` - Base class for all UAC bypass methods
- `attempt_uac_bypass()` - Main UAC bypass dispatcher
- `bypass_uac_fodhelper_protocol()` - Fodhelper.exe bypass
- `bypass_uac_eventvwr()` - Event viewer bypass
- `bypass_uac_silentcleanup()` - Silent cleanup bypass
- `bypass_uac_compmgmtlauncher()` - Computer management bypass
- `bypass_uac_sdclt()` - SDCLT bypass
- `bypass_uac_slui()` - Software licensing bypass
- `bootstrap_uac_disable_no_admin()` - Aggressive UAC disable
- `silent_disable_uac_method4()` - Registry-based UAC disable
- `run_uac_bypass_test()` - Testing framework for UAC methods

**Registry Operations**:
- Registry key manipulation for protocol handlers
- Environment variable hijacking
- COM interface exploitation (ICMLuaUtil)
- Process token duplication

### 2. Windows Defender Disable System
**Location**: Lines ~2000-3000

**Key Functions**:
- `disable_defender()` - Main defender disable function
- `disable_defender_registry()` - Registry-based disable
- `disable_defender_powershell()` - PowerShell-based disable
- `disable_defender_services()` - Service manipulation
- `disable_windows_notifications()` - Notification system disable

**Registry Paths**:
- `HKLM\SOFTWARE\Policies\Microsoft\Windows Defender`
- `HKLM\SOFTWARE\Microsoft\Windows Defender`
- `HKLM\SYSTEM\CurrentControlSet\Services\WinDefend`

### 3. Persistence Mechanisms
**Location**: Lines ~17000-18000

**Key Functions**:
- `establish_persistence()` - Main persistence setup
- `add_to_startup()` - Startup folder persistence
- `add_registry_startup()` - Registry Run key persistence
- `setup_advanced_persistence()` - Advanced persistence methods
- `check_registry_persistence()` - Persistence verification

**Registry Locations**:
- `HKCU\Software\Microsoft\Windows\CurrentVersion\Run`
- `HKLM\Software\Microsoft\Windows\CurrentVersion\Run`
- `HKCU\Software\Microsoft\Windows\CurrentVersion\RunOnce`

**File System Locations**:
- `%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup`
- `%LOCALAPPDATA%\Microsoft\Windows\svchost32.exe` (stealth location)

### 4. Process Management & Stealth
**Location**: Lines ~3000-5000, ~15000-16000

**Key Functions**:
- `hide_process()` - Process hiding techniques
- `add_firewall_exception()` - Firewall manipulation
- `disable_wsl_routing()` - WSL routing disable
- `terminate_process_admin()` - Admin-level process termination
- `kill_task_manager()` - Task Manager protection

**Windows APIs Used**:
- `NtTerminateProcess` via ctypes
- `SetWindowDisplayAffinity`
- Process token manipulation
- Debug privilege escalation

### 5. System Configuration Bypasses
**Location**: Lines ~18400-18600

**Key Functions**:
- `verify_uac_status()` - UAC status verification
- `is_admin()` - Admin privilege detection
- `get_debug_privilege()` - Debug privilege acquisition
- `run_as_admin_with_limited_attempts()` - UAC prompt handling

### 6. Anti-Analysis Techniques
**Location**: Lines ~5000-6000

**Key Functions**:
- `detect_vm()` - Virtual machine detection
- `sleep_random_non_blocking()` - Stealth timing delays
- String obfuscation in registry operations
- Random delay insertion in critical paths

## Command Execution Integration

### UAC Test Commands
**Location**: Lines ~15800-16200

**Command Format**: `uac-test-{method_name}`

**Available Tests**:
- `uac-test-fodhelper` - Test fodhelper bypass
- `uac-test-eventvwr` - Test event viewer bypass
- `uac-test-silentcleanup` - Test silent cleanup bypass
- `uac-test-compmgmtlauncher` - Test computer management bypass
- `uac-test-sdclt` - Test SDCLT bypass
- `uac-test-slui` - Test SLUI bypass

### System Configuration Commands
**Location**: Lines ~16000-16200

**Available Commands**:
- `security-scan` - Run comprehensive security scan
- `collect-logs` - Collect system logs and security info
- `update-agent` - Agent update mechanism placeholder

## Registry System Architecture

### Registry Manipulation Patterns
1. **Silent Import**: Use `regedit.exe /s` for silent registry imports
2. **Direct API**: Use `winreg` module for direct registry access
3. **PowerShell**: Use PowerShell for complex registry operations
4. **Backup/Restore**: Registry key backup before modification

### Key Registry Operations
- **UAC Disable**: Modify `EnableLUA` and `ConsentPromptBehaviorAdmin`
- **Defender Disable**: Modify various Defender policy keys
- **Persistence**: Add entries to Run keys
- **Protocol Hijacking**: Modify protocol handler associations

## Error Handling Patterns

### Common Error Handling
1. **Graceful Degradation**: Continue operation if bypass fails
2. **Fallback Methods**: Try multiple bypass techniques
3. **Silent Failures**: Log errors but don't interrupt main flow
4. **Retry Logic**: Attempt bypasses multiple times with delays

### Logging Integration
- Use `log_message()` for all bypass operations
- Include bypass method names in log messages
- Log success/failure status for each operation
- Include error details for debugging

## Security Validation Requirements

### Input Validation
- Validate all registry paths before access
- Check admin privileges before attempting bypasses
- Verify system compatibility (Windows version checks)

### Safety Mechanisms
- Registry backup before modifications
- Ability to restore original settings
- Verification of bypass success
- Rollback capabilities

## Performance Characteristics

### Threading Model
- Use daemon threads for bypass operations
- Non-blocking execution for main agent loop
- Background monitoring for persistence

### Resource Usage
- Minimal CPU usage during idle periods
- Efficient registry access patterns
- Memory cleanup after operations

## Integration Points

### Socket.IO Events
- `agent_privilege_update` - Notify controller of privilege changes
- `security_notification` - Send security-related notifications
- `command_result` - Return bypass test results

### Command Integration
- Bypass commands integrated into `on_execute_command`
- System info commands in `on_command`
- Real-time status updates via Socket.IO

This analysis covers all bypasses functionality that needs to be mirrored in the bypasses module and registry system implementation.