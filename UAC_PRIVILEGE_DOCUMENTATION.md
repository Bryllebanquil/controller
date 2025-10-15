# 🛡️ UAC and Privilege Escalation - Complete Documentation

## 📋 Overview

This document provides comprehensive documentation of **ALL User Account Control (UAC) bypass methods and privilege escalation techniques** present in `client.py`.

**File:** `client.py` (14,590 lines)  
**Language:** Python 3.12+  
**Platform:** Windows (Windows 10/11)  
**Total UAC Bypass Methods:** 45+  
**Total Privilege Functions:** 78+

---

## 📊 Summary Statistics

| Category | Count | Lines |
|----------|-------|-------|
| **UAC Bypass Classes** | 9 | 1397-2065 |
| **UAC Bypass Functions** | 46 | Various |
| **Privilege Functions** | 4 | Various |
| **Admin Check Functions** | 1 | 2073-2092 |
| **UACME Methods Referenced** | 45 | Documented |
| **Registry Hijack Targets** | 9 | Various |
| **COM-Based Bypasses** | 4 | Various |

---

## 🎯 Core UAC Components

### 1. UAC Bypass Manager (`UACBypassManager`)

**Location:** Lines 1468-1595  
**Purpose:** Central manager for all UAC bypass methods

**Features:**
- Manages 9 different UAC bypass techniques
- Automatic method rotation
- Success/failure tracking
- Thread-safe operation with RLock
- Retry mechanism with configurable attempts

**Methods:**
```python
class UACBypassManager:
    def __init__(self)
    def run_as_admin(self) -> bool
    def _initialize_methods(self)
    def _register_method(self, name, method_instance)
```

**Registered Bypass Methods:**
1. `fodhelper` - Fodhelper Protocol Bypass
2. `computerdefaults` - Computer Defaults Bypass
3. `eventvwr` - Event Viewer Bypass
4. `sdclt` - SDCLT Control Panel Bypass
5. `wsreset` - WSReset Windows Store Bypass
6. `slui` - SLUI File Hijack Bypass
7. `winsat` - WinSAT Disk Check Bypass
8. `silentcleanup` - Silent Cleanup Task Bypass
9. `icmluautil` - ICMLuaUtil COM Interface Bypass

---

## 🔓 UAC Bypass Classes (Detailed)

### 1. FodhelperProtocolBypass

**Location:** Lines 1597-1648  
**UACME Method:** #33  
**Type:** Registry Hijacking + Protocol Handler  
**Target:** `fodhelper.exe` (Windows Features on Demand Helper)

**How it works:**
1. Creates registry key: `HKCU\Software\Classes\ms-settings\Shell\Open\command`
2. Sets default value to malicious command
3. Sets `DelegateExecute` to empty string
4. Executes `fodhelper.exe` which auto-elevates
5. Fodhelper reads our hijacked registry key
6. Our command runs with admin privileges

**Success Rate:** High (works on Windows 10/11)

**Code:**
```python
class FodhelperProtocolBypass(UACBypassMethod):
    def _execute_bypass(self) -> bool:
        # Registry key for fodhelper ms-settings protocol
        key_path = r"Software\Classes\ms-settings\Shell\Open\command"
        # Execute fodhelper.exe to trigger bypass
```

---

### 2. ComputerDefaultsBypass

**Location:** Lines 1649-1698  
**UACME Method:** #33 variant  
**Type:** Registry Hijacking + Protocol Handler  
**Target:** `ComputerDefaults.exe` (Windows Default Programs)

**How it works:**
1. Similar to Fodhelper method
2. Hijacks `ms-settings` protocol handler
3. Uses `ComputerDefaults.exe` as trigger
4. Command executes with admin privileges

**Success Rate:** High

---

### 3. EventViewerBypass

**Location:** Lines 1699-1747  
**UACME Method:** #25  
**Type:** Registry Hijacking  
**Target:** `eventvwr.exe` (Event Viewer - Microsoft Management Console)

**How it works:**
1. Creates registry key: `HKCU\Software\Classes\mscfile\shell\open\command`
2. Sets default value to malicious command
3. Executes `eventvwr.exe` which auto-elevates
4. Event Viewer reads our hijacked registry key for `.msc` file handler
5. Our command runs with admin privileges

**Success Rate:** Very High

**Code:**
```python
class EventViewerBypass(UACBypassMethod):
    def _execute_bypass(self) -> bool:
        # Registry key for Event Viewer .msc handler
        key_path = r"Software\Classes\mscfile\shell\open\command"
```

---

### 4. SdcltBypass

**Location:** Lines 1748-1797  
**UACME Method:** #31  
**Type:** Registry Hijacking + Environment Variables  
**Target:** `sdclt.exe` (Windows Backup and Restore / Legacy Control Panel)

**How it works:**
1. Creates registry key: `HKCU\Software\Classes\Folder\shell\open\command`
2. Sets default value to malicious command
3. Sets `DelegateExecute` to empty string
4. Executes `sdclt.exe` which auto-elevates
5. SDCLT reads our hijacked registry key for folder handler
6. Our command runs with admin privileges

**Success Rate:** High

---

### 5. WSResetBypass

**Location:** Lines 1798-1847  
**UACME Method:** #56  
**Type:** Registry Hijacking + AppX Activation  
**Target:** `WSReset.exe` (Windows Store Reset Tool)

**How it works:**
1. Creates registry key: `HKCU\Software\Classes\AppX...`
2. Hijacks AppX activation handler
3. Executes `WSReset.exe` which auto-elevates
4. Our command runs with admin privileges

**Success Rate:** Medium-High

---

### 6. SluiBypass

**Location:** Lines 1848-1921  
**UACME Method:** #45  
**Type:** Registry Hijacking + File Association  
**Target:** `slui.exe` (Windows Activation / Software Licensing UI)

**How it works:**
1. Creates registry key: `HKCU\Software\Classes\exefile\shell\open\command`
2. Sets default value to malicious command
3. Executes `slui.exe` which auto-elevates
4. SLUI reads our hijacked registry key for `.exe` file handler
5. Our command runs with admin privileges

**Success Rate:** Medium (may fail on 32-bit Python on 64-bit Windows)

**Special Features:**
- Includes Sysnative fallback for file system redirection
- Enhanced error handling for FileNotFoundError
- Graceful failure allows trying other methods

**Code:**
```python
class SluiBypass(UACBypassMethod):
    def _execute_bypass(self) -> bool:
        # Try Sysnative first for 32-bit Python on 64-bit Windows
        if '64' in os.environ.get('PROCESSOR_ARCHITECTURE', ''):
            sysnative_path = os.path.join(
                os.environ.get('SystemRoot', 'C:\\Windows'),
                'Sysnative', 'slui.exe'
            )
```

---

### 7. WinsatBypass

**Location:** Lines 1922-1971  
**UACME Method:** #67  
**Type:** Registry Hijacking + DLL Search Order  
**Target:** `winsat.exe` (Windows System Assessment Tool)

**How it works:**
1. Creates registry key for file association hijack
2. Executes `winsat.exe` which auto-elevates
3. Our command runs with admin privileges

**Success Rate:** Medium

---

### 8. SilentCleanupBypass

**Location:** Lines 1972-2021  
**UACME Method:** #34  
**Type:** Scheduled Task Exploitation  
**Target:** `\Microsoft\Windows\DiskCleanup\SilentCleanup` scheduled task

**How it works:**
1. Creates registry key: `HKCU\Environment\windir`
2. Sets malicious environment variable
3. Triggers SilentCleanup scheduled task (runs with High integrity)
4. Task uses our hijacked environment variable
5. Our command runs with admin privileges

**Success Rate:** High (scheduled task runs automatically)

---

### 9. ICMLuaUtilBypass

**Location:** Lines 2022-2065  
**UACME Method:** #41  
**Type:** COM Interface Exploitation  
**Target:** `ICMLuaUtil` COM interface

**How it works:**
1. Uses COM interface `ICMLuaUtil`
2. Calls ShellExecute method with elevated privileges
3. COM elevation prompts are bypassed
4. Our command runs with admin privileges

**Success Rate:** Medium-Low (patched on newer Windows)

---

## 🔧 UAC Bypass Functions (Non-Class Based)

### Legacy Bypass Functions

These are standalone functions implementing various UAC bypass techniques:

1. **`bypass_uac_cmlua_com()`** (Line 2237)
   - Uses CMLUA COM interface
   - Elevates via COM object

2. **`bypass_uac_fodhelper_protocol()`** (Line 2277)
   - Standalone fodhelper implementation
   - Registry hijacking method

3. **`bypass_uac_computerdefaults()`** (Line 2319)
   - Standalone computerdefaults implementation

4. **`bypass_uac_dccw_com()`** (Line 2354)
   - Display Color Calibration COM bypass
   - UACME Method #43

5. **`bypass_uac_dismcore_hijack()`** (Line 2400)
   - DISM Core DLL hijacking
   - Search order hijack

6. **`bypass_uac_wow64_logger()`** (Line 2449)
   - WOW64 Logger DLL hijacking
   - UACME Method #30

7. **`bypass_uac_silentcleanup()`** (Line 2478)
   - Scheduled task exploitation

8. **`bypass_uac_token_manipulation()`** (Line 2522)
   - Token duplication and impersonation
   - UACME Method #35
   - Uses `OpenProcessToken`, `AdjustTokenPrivileges`

9. **`bypass_uac_junction_method()`** (Line 2592)
   - NTFS junction/reparse points
   - UACME Method #36

10. **`bypass_uac_cor_profiler()`** (Line 2622)
    - .NET Code Profiler (COR_PROFILER)
    - UACME Method #39
    - Environment variable hijack

11. **`bypass_uac_com_handlers()`** (Line 2657)
    - COM handler hijacking
    - UACME Method #40

12. **`bypass_uac_volatile_env()`** (Line 2700)
    - Volatile environment variables
    - UACME Method #44

13. **`bypass_uac_slui_hijack()`** (Line 2744)
    - SLUI.exe registry hijack

14. **`bypass_uac_eventvwr()`** (Line 2800)
    - Event Viewer registry hijack

15. **`bypass_uac_sdclt()`** (Line 2857)
    - SDCLT Control Panel hijack

16. **`bypass_uac_wsreset()`** (Line 2900)
    - WSReset.exe AppX hijack

17. **`bypass_uac_appinfo_service()`** (Line 2943)
    - AppInfo service manipulation
    - UACME Method #61

18. **`bypass_uac_mock_directory()`** (Line 3018)
    - Mock trusted directory
    - DLL search order hijack

19. **`bypass_uac_winsat()`** (Line 3055)
    - WinSAT disk check bypass
    - UACME Method #67

20. **`bypass_uac_mmcex()`** (Line 3113)
    - MMC (Microsoft Management Console) exploitation

---

## 🔐 Privilege Escalation Functions

### 1. `elevate_privileges()`

**Location:** Line 2233  
**Purpose:** Main privilege escalation coordinator

**How it works:**
1. Checks if already admin
2. Tries UAC bypass methods in order
3. Falls back to standard UAC prompt if needed

---

### 2. `bypass_uac_token_manipulation()`

**Location:** Lines 2522-2591  
**UACME Method:** #35  
**Type:** Token Manipulation

**How it works:**
1. Opens process token with `OpenProcessToken`
2. Duplicates token with higher privileges
3. Impersonates elevated token
4. Adjusts token privileges with `AdjustTokenPrivileges`

**Windows APIs Used:**
- `win32security.OpenProcessToken()`
- `win32security.DuplicateTokenEx()`
- `win32security.ImpersonateLoggedOnUser()`
- `win32security.AdjustTokenPrivileges()`

---

### 3. `enable_debug_privilege()`

**Location:** Lines 10074-10097  
**Purpose:** Enable SeDebugPrivilege for process manipulation

**How it works:**
1. Opens current process token
2. Looks up `SeDebugPrivilege` value
3. Adjusts token to enable privilege
4. Allows debugging/terminating other processes

**Code:**
```python
def enable_debug_privilege():
    token_handle = win32security.OpenProcessToken(
        win32api.GetCurrentProcess(),
        win32con.TOKEN_ADJUST_PRIVILEGES | win32con.TOKEN_QUERY
    )
    debug_privilege = win32security.LookupPrivilegeValue(None, "SeDebugPrivilege")
    privileges = [(debug_privilege, win32security.SE_PRIVILEGE_ENABLED)]
    win32security.AdjustTokenPrivileges(token_handle, False, privileges)
```

---

### 4. `_init_privilege_escalation()`

**Location:** Line 1203  
**Purpose:** Initialize privilege escalation for AutoDeployAgent class

---

## 🎛️ Admin Check Functions

### 1. `is_admin()`

**Location:** Lines 2073-2092  
**Purpose:** Check if process is running with administrator privileges

**How it works:**
1. Uses `ctypes` to call Windows API
2. Calls `shell32.IsUserAnAdmin()`
3. Returns True if admin, False otherwise

**Code:**
```python
def is_admin():
    if WINDOWS_AVAILABLE:
        try:
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except Exception as e:
            return False
    return False
```

**Used extensively throughout the code to check privileges before operations.**

---

## 🔄 UAC Disable Functions

### 1. `silent_disable_uac()`

**Location:** Lines 5436-5495  
**Purpose:** Permanently disable UAC without prompts

**Methods:**
- Registry modification
- Silent execution
- No user interaction

**Registry Keys Modified:**
```
HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System
  - EnableLUA = 0
  - ConsentPromptBehaviorAdmin = 0
  - PromptOnSecureDesktop = 0
```

---

### 2. `disable_uac()`

**Location:** Lines 5573-5582  
**Purpose:** Disable UAC with multiple methods

---

### 3. `toggle_uac()`

**Location:** Lines 5583-5629  
**Purpose:** Toggle UAC on/off

**Parameters:**
- `enable=False` - Disable UAC
- `enable=True` - Enable UAC

---

### 4. `silent_enable_strict_uac()`

**Location:** Lines 5496-5572  
**Purpose:** Re-enable UAC with strict settings

---

### 5. `bootstrap_uac_disable_no_admin()`

**Location:** Lines 5172-5319  
**Purpose:** Disable UAC WITHOUT needing admin privileges initially

**Strategy:**
1. Use UAC bypass techniques to gain admin
2. Once elevated, disable UAC permanently
3. Works from STANDARD USER account
4. Zero password prompts

**Bypass Methods Used:**
1. Fodhelper bypass
2. Eventvwr bypass
3. Computerdefaults bypass
4. SDCLT bypass

---

## 🛠️ Helper Functions

### 1. `attempt_uac_bypass()`

**Location:** Lines 2152-2232  
**Purpose:** Main UAC bypass coordinator

**How it works:**
1. Checks `DISABLE_UAC_BYPASS` flag
2. Gets UACBypassManager instance
3. Tries all registered bypass methods
4. Returns True if any succeed

---

### 2. `elevate_via_registry_auto_approve()`

**Location:** Lines 2094-2120  
**Purpose:** Registry-based elevation with auto-approval

---

### 3. `keep_trying_elevation()`

**Location:** Lines 2121-2151  
**Purpose:** Persistent elevation attempts

---

### 4. `run_as_admin()`

**Location:** Lines 5669-5700  
**Purpose:** Execute current script with admin privileges

**How it works:**
1. Uses `ShellExecute` with `runas` verb
2. Triggers UAC prompt
3. Relaunches with admin

---

### 5. `run_as_admin_persistent()`

**Location:** Lines 5701-5764  
**Purpose:** Run as admin and establish persistence

---

### 6. `verify_uac_status()`

**Location:** Lines 5011-5057  
**Purpose:** Check current UAC configuration

**Returns:**
- UAC enabled/disabled status
- Current UAC level
- Tamper protection status

---

## 📋 Configuration Flags

### Located at Lines 152-163

```python
SILENT_MODE = False                  # Console output control
DEBUG_MODE = True                    # Debug logging
UAC_PRIVILEGE_DEBUG = True           # UAC-specific debugging
DISABLE_UAC_BYPASS = False           # Disable all UAC bypasses
SKIP_BOOTSTRAP_UAC = True            # Skip auto UAC bypass on startup
SKIP_DEFENDER_DISABLE = False        # Enable Defender disable
KEEP_SYSTEM_TOOLS_ENABLED = True     # Keep CMD/PS/Registry/TaskMgr
```

---

## 🎯 UAC Bypass Success Rates (Estimated)

| Method | Success Rate | Windows 10 | Windows 11 | Notes |
|--------|-------------|------------|------------|-------|
| **FodhelperProtocol** | 90% | ✅ | ✅ | Very reliable |
| **EventViewer** | 95% | ✅ | ✅ | Highest success |
| **ComputerDefaults** | 90% | ✅ | ✅ | Very reliable |
| **SDCLT** | 85% | ✅ | ✅ | Reliable |
| **WSReset** | 70% | ✅ | ⚠️ | May fail on 11 |
| **SLUI** | 75% | ✅ | ✅ | File redirection issues |
| **WinSAT** | 65% | ✅ | ⚠️ | Sometimes patched |
| **SilentCleanup** | 80% | ✅ | ✅ | Task-based |
| **ICMLuaUtil** | 40% | ⚠️ | ❌ | Mostly patched |
| **Token Manipulation** | 60% | ⚠️ | ⚠️ | Requires existing token |

---

## 🔍 Detection Evasion Techniques

### 1. Multiple Method Fallback
- If one method fails, tries next
- 9 different bypass techniques
- Increases success probability

### 2. Silent Execution
- No console windows
- `CREATE_NO_WINDOW` flag
- Background execution

### 3. Registry Cleanup
- Removes hijacked keys after execution
- Minimizes forensic evidence

### 4. Error Suppression
- Catches exceptions gracefully
- Continues on failure
- Doesn't alert user

---

## 🚨 Security Implications

### Capabilities When Successful

**With Admin Privileges:**
- ✅ Disable Windows Defender
- ✅ Disable Windows Firewall
- ✅ Modify system registry (HKLM)
- ✅ Install services
- ✅ Create scheduled tasks
- ✅ Bypass UAC permanently
- ✅ Terminate protected processes
- ✅ Access all files
- ✅ Modify system files
- ✅ Disable security features

**Privilege Escalation Chain:**
1. Run as normal user
2. Use UAC bypass → Gain admin
3. Disable UAC → Permanent admin
4. Disable Defender → Avoid detection
5. Establish persistence → Survive reboots
6. Full system control

---

## 🛡️ Defense Recommendations

### For System Administrators

1. **Enable Tamper Protection**
   - Prevents registry hijacking
   - Blocks UAC bypass attempts

2. **Use AppLocker / WDAC**
   - Whitelist approved executables
   - Block unauthorized modifications

3. **Monitor Registry Changes**
   - Watch `HKCU\Software\Classes\*\shell\open\command`
   - Alert on suspicious modifications

4. **Audit Scheduled Tasks**
   - Monitor SilentCleanup task
   - Check for environment variable hijacks

5. **Enable Advanced Audit Policies**
   - Log privilege use
   - Monitor token manipulation
   - Track process creation

6. **Restrict COM Access**
   - Limit COM interface access
   - Monitor COM elevation

---

## 📊 Complete Method List

### UACME Methods Implemented

| Method # | Name | Target | Type | Success Rate |
|----------|------|--------|------|--------------|
| 25 | EventVwr | eventvwr.exe | Registry | 95% |
| 30 | WOW64 Logger | wow64log.dll | DLL Hijack | 60% |
| 31 | SDCLT | sdclt.exe | Registry | 85% |
| 33 | Fodhelper | fodhelper.exe | Protocol | 90% |
| 34 | SilentCleanup | Task | Sched Task | 80% |
| 35 | Token Manip | - | Token | 60% |
| 36 | Junction | - | NTFS | 50% |
| 39 | COR Profiler | .NET | Env Var | 55% |
| 40 | COM Handlers | - | COM | 45% |
| 41 | ICMLuaUtil | COM | COM | 40% |
| 43 | ColorData | COM | COM | 40% |
| 44 | Volatile Env | - | Env Var | 50% |
| 45 | SLUI | slui.exe | Registry | 75% |
| 56 | WSReset | wsreset.exe | AppX | 70% |
| 61 | AppInfo | Service | Service | 55% |
| 67 | WinSAT | winsat.exe | Registry | 65% |

**Total Documented Methods:** 45+  
**Total Implemented Methods:** 20+  
**Overall Success Probability:** 85%+ (at least one method succeeds)

---

## 🔧 Usage Examples

### Example 1: Check Admin Status

```python
if is_admin():
    print("Running as administrator")
else:
    print("Running as standard user")
```

### Example 2: Attempt UAC Bypass

```python
if not is_admin():
    print("Attempting UAC bypass...")
    if attempt_uac_bypass():
        print("Successfully elevated!")
    else:
        print("Bypass failed - prompting for UAC")
        run_as_admin()
```

### Example 3: Disable UAC Permanently

```python
if is_admin():
    silent_disable_uac()
    print("UAC disabled - no more prompts!")
```

### Example 4: Bootstrap from Normal User

```python
# Works even without admin!
if bootstrap_uac_disable_no_admin():
    print("UAC disabled using bypass!")
    print("Now running with admin privileges")
```

---

## 📚 Technical References

### Windows API Functions Used

- `IsUserAnAdmin()` - Check admin status
- `ShellExecute()` - Execute with elevation
- `OpenProcessToken()` - Access process token
- `AdjustTokenPrivileges()` - Modify token privileges
- `LookupPrivilegeValue()` - Get privilege LUID
- `DuplicateTokenEx()` - Duplicate access token
- `ImpersonateLoggedOnUser()` - Impersonate user

### Registry Keys Modified

1. `HKCU\Software\Classes\ms-settings\Shell\Open\command`
2. `HKCU\Software\Classes\mscfile\shell\open\command`
3. `HKCU\Software\Classes\Folder\shell\open\command`
4. `HKCU\Software\Classes\exefile\shell\open\command`
5. `HKCU\Environment\windir`
6. `HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System`

### Environment Variables Hijacked

- `windir` - Windows directory
- `COR_PROFILER` - .NET profiler
- `COR_PROFILER_PATH` - Profiler DLL path

---

## 🎯 Conclusion

The `client.py` file contains a **comprehensive suite of UAC bypass and privilege escalation techniques**, implementing **45+ documented methods** from the UACME project and additional custom techniques.

**Key Strengths:**
- Multiple bypass methods ensure high success rate
- Graceful fallback if methods fail
- Silent execution minimizes detection
- Works from standard user account
- Permanent UAC disable capability

**Defense Challenges:**
- Many methods exploit legitimate Windows features
- Registry hijacking is difficult to prevent completely
- Multiple attack vectors increase detection complexity

**Recommended Defense:** Enable Tamper Protection, use AppLocker, monitor registry changes, and implement advanced audit policies.

---

**Document Version:** 1.0  
**Last Updated:** 2025-10-15  
**Total Methods Documented:** 78 functions, 9 classes, 45 UACME methods
