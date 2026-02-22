"""
Enhanced Registry Test Suite for UI Toggle Operations
Comprehensive testing for all registry modifications from bypasses & registry tablist
"""

import ctypes
import platform
import winreg
import json
import time
import subprocess
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

try:
    import client
    CLIENT_AVAILABLE = True
except ImportError:
    CLIENT_AVAILABLE = False
    print("Warning: client.py not found. Cannot verify against client definitions.")

class RegistryStatus(Enum):
    ENABLED = "Enabled"
    DISABLED = "Disabled"
    NOT_FOUND = "Not Found"
    ERROR = "Error"

@dataclass
class RegistryTest:
    name: str
    description: str
    registry_path: str
    registry_key: str
    hive: int
    expected_value: any
    value_type: int
    test_type: str  # "enabled_test" or "disabled_test"
    category: str  # UI category for grouping

class EnhancedRegistryUITester:
    """Enhanced test suite for registry operations from UI toggle components"""
    
    def __init__(self):
        self.test_results = []
        self.is_windows = platform.system() == 'Windows'
        self.is_admin = self._check_admin() if self.is_windows else False
        
    def _check_admin(self) -> bool:
        """Check if running with administrator privileges"""
        try:
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except:
            return False
    
    def _get_enhanced_registry_tests(self) -> List[RegistryTest]:
        """Define comprehensive registry tests for all UI components"""
        tests = [
            # === POLICY & NOTIFICATION TESTS ===
            
            # Policy Push Notifications
            RegistryTest(
                name="Policy Push Notifications - Global",
                description="Disable cloud application notifications globally",
                registry_path=r"SOFTWARE\Policies\Microsoft\Windows\PushNotifications-Enabled",
                registry_key="NoCloudApplicationNotification",
                hive=winreg.HKEY_LOCAL_MACHINE,
                expected_value=1,
                value_type=winreg.REG_DWORD,
                test_type="enabled_test",
                category="Policy"
            ),
            
            RegistryTest(
                name="Policy Push Notifications - User",
                description="Disable push notifications for current user",
                registry_path=r"SOFTWARE\Policies\Microsoft\Windows\CurrentVersion\PushNotifications",
                registry_key="NoToastApplicationNotification",
                hive=winreg.HKEY_CURRENT_USER,
                expected_value=1,
                value_type=winreg.REG_DWORD,
                test_type="enabled_test",
                category="Policy"
            ),
            
            # Policy Windows Update
            RegistryTest(
                name="Policy Windows Update - Auto Update",
                description="Disable automatic Windows Updates",
                registry_path=r"SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate\AU",
                registry_key="NoAutoUpdate",
                hive=winreg.HKEY_LOCAL_MACHINE,
                expected_value=1,
                value_type=winreg.REG_DWORD,
                test_type="disabled_test",
                category="Policy"
            ),
            
            RegistryTest(
                name="Policy Windows Update - Disable Access",
                description="Disable Windows Update access",
                registry_path=r"SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate",
                registry_key="DisableWindowsUpdateAccess",
                hive=winreg.HKEY_LOCAL_MACHINE,
                expected_value=1,
                value_type=winreg.REG_DWORD,
                test_type="disabled_test",
                category="Policy"
            ),
            
            # === CONTEXT MENU TESTS ===
            
            # Context Runas Cmd
            RegistryTest(
                name="Context Runas Cmd",
                description="Add 'Run as Administrator' to CMD context menu",
                registry_path=r"SOFTWARE\Classes\cmdfile\shell\runas",
                registry_key="",
                hive=winreg.HKEY_CLASSES_ROOT,
                expected_value="",
                value_type=winreg.REG_SZ,
                test_type="disabled_test",
                category="Context Menu"
            ),
            
            RegistryTest(
                name="Context Runas Cmd - Command",
                description="CMD runas command executable",
                registry_path=r"SOFTWARE\Classes\cmdfile\shell\runas\command",
                registry_key="",
                hive=winreg.HKEY_CLASSES_ROOT,
                expected_value="cmd.exe",
                value_type=winreg.REG_SZ,
                test_type="disabled_test",
                category="Context Menu"
            ),
            
            # Context Powershell Admin
            RegistryTest(
                name="Context Powershell Admin",
                description="Add 'Run as Administrator' to PowerShell context menu",
                registry_path=r"SOFTWARE\Classes\Microsoft.PowerShellScript.1\shell\runas",
                registry_key="",
                hive=winreg.HKEY_CLASSES_ROOT,
                expected_value="",
                value_type=winreg.REG_SZ,
                test_type="disabled_test",
                category="Context Menu"
            ),
            
            RegistryTest(
                name="Context Powershell Admin - Command",
                description="PowerShell runas command executable",
                registry_path=r"SOFTWARE\Classes\Microsoft.PowerShellScript.1\shell\runas\command",
                registry_key="",
                hive=winreg.HKEY_CLASSES_ROOT,
                expected_value="powershell.exe -Command \"Start-Process PowerShell -ArgumentList '-ExecutionPolicy Bypass' -Verb RunAs\"",
                value_type=winreg.REG_SZ,
                test_type="disabled_test",
                category="Context Menu"
            ),
            
            # === NOTIFICATION CENTER TESTS ===
            
            # Notify Center Hkcu
            RegistryTest(
                name="Notify Center Hkcu - Disable Center",
                description="Disable notification center for current user",
                registry_path=r"SOFTWARE\Policies\Microsoft\Windows\Explorer",
                registry_key="DisableNotificationCenter",
                hive=winreg.HKEY_CURRENT_USER,
                expected_value=1,
                value_type=winreg.REG_DWORD,
                test_type="disabled_test",
                category="Notification Center"
            ),
            
            RegistryTest(
                name="Notify Center Hkcu - Disable Toasts",
                description="Disable toast notifications for current user",
                registry_path=r"SOFTWARE\Microsoft\Windows\CurrentVersion\PushNotifications",
                registry_key="ToastEnabled",
                hive=winreg.HKEY_CURRENT_USER,
                expected_value=0,
                value_type=winreg.REG_DWORD,
                test_type="disabled_test",
                category="Notification Center"
            ),
            
            # Notify Center Hklm
            RegistryTest(
                name="Notify Center Hklm - Disable Center",
                description="Disable notification center system-wide",
                registry_path=r"SOFTWARE\Policies\Microsoft\Windows\Explorer",
                registry_key="DisableNotificationCenter",
                hive=winreg.HKEY_LOCAL_MACHINE,
                expected_value=1,
                value_type=winreg.REG_DWORD,
                test_type="disabled_test",
                category="Notification Center"
            ),
            
            RegistryTest(
                name="Notify Center Hklm - Disable Toasts",
                description="Disable toast notifications system-wide",
                registry_path=r"SOFTWARE\Microsoft\Windows\CurrentVersion\PushNotifications",
                registry_key="ToastEnabled",
                hive=winreg.HKEY_LOCAL_MACHINE,
                expected_value=0,
                value_type=winreg.REG_DWORD,
                test_type="disabled_test",
                category="Notification Center"
            ),
            
            # === DEFENDER UX TESTS ===
            
            # Defender Ux Suppress
            RegistryTest(
                name="Defender Ux Suppress - Notifications",
                description="Suppress Windows Defender notifications",
                registry_path=r"SOFTWARE\Policies\Microsoft\Windows Defender\UX Configuration",
                registry_key="Notification_Suppress",
                hive=winreg.HKEY_LOCAL_MACHINE,
                expected_value=1,
                value_type=winreg.REG_DWORD,
                test_type="disabled_test",
                category="Defender UX"
            ),
            
            RegistryTest(
                name="Defender Ux Suppress - Non Critical",
                description="Suppress non-critical Windows Defender notifications",
                registry_path=r"SOFTWARE\Policies\Microsoft\Windows Defender\UX Configuration",
                registry_key="Notification_Suppress_NonCritical",
                hive=winreg.HKEY_LOCAL_MACHINE,
                expected_value=1,
                value_type=winreg.REG_DWORD,
                test_type="disabled_test",
                category="Defender UX"
            ),
            
            # === TOAST NOTIFICATION TESTS ===
            
            # Toast Global Above Lock
            RegistryTest(
                name="Toast Global Above Lock - Disable",
                description="Disable toast notifications above lock screen",
                registry_path=r"SOFTWARE\Policies\Microsoft\Windows\System",
                registry_key="DisableAcrylicBackgroundOnLogon",
                hive=winreg.HKEY_LOCAL_MACHINE,
                expected_value=1,
                value_type=winreg.REG_DWORD,
                test_type="disabled_test",
                category="Toast Notifications"
            ),
            
            # Toast Global Critical Above Lock
            RegistryTest(
                name="Toast Global Critical Above Lock - Disable",
                description="Disable critical toast notifications above lock screen",
                registry_path=r"SOFTWARE\Policies\Microsoft\Windows\System",
                registry_key="DisableLockScreenAppNotifications",
                hive=winreg.HKEY_LOCAL_MACHINE,
                expected_value=1,
                value_type=winreg.REG_DWORD,
                test_type="disabled_test",
                category="Toast Notifications"
            ),
            
            # Toast Windows Update
            RegistryTest(
                name="Toast Windows Update - Disable UX",
                description="Disable Windows Update toast notifications UX",
                registry_path=r"SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate",
                registry_key="SetDisableUXWUAccess",
                hive=winreg.HKEY_LOCAL_MACHINE,
                expected_value=1,
                value_type=winreg.REG_DWORD,
                test_type="disabled_test",
                category="Toast Notifications"
            ),
            
            # Toast Security Maintenance
            RegistryTest(
                name="Toast Security Maintenance - Disable Center",
                description="Disable Security Center maintenance notifications",
                registry_path=r"SOFTWARE\Policies\Microsoft\Windows Defender Security Center",
                registry_key="DisableWindowsSecurityCenterNotifications",
                hive=winreg.HKEY_LOCAL_MACHINE,
                expected_value=1,
                value_type=winreg.REG_DWORD,
                test_type="disabled_test",
                category="Toast Notifications"
            ),
            
            # Toast Windows Security
            RegistryTest(
                name="Toast Windows Security - Disable Center",
                description="Disable Windows Security center notifications",
                registry_path=r"SOFTWARE\Policies\Microsoft\Windows Defender Security Center",
                registry_key="DisableWindowsSecurityCenter",
                hive=winreg.HKEY_LOCAL_MACHINE,
                expected_value=1,
                value_type=winreg.REG_DWORD,
                test_type="disabled_test",
                category="Toast Notifications"
            ),
            
            # Toast Sec Health Ui
            RegistryTest(
                name="Toast Sec Health Ui - Disable Health",
                description="Disable Security Health UI notifications",
                registry_path=r"SOFTWARE\Policies\Microsoft\Windows Defender Security Center",
                registry_key="DisableHealthUI",
                hive=winreg.HKEY_LOCAL_MACHINE,
                expected_value=1,
                value_type=winreg.REG_DWORD,
                test_type="disabled_test",
                category="Toast Notifications"
            ),
            
            # === EXPLORER UI TESTS ===
            
            # Explorer Balloon Tips
            RegistryTest(
                name="Explorer Balloon Tips - Disable",
                description="Disable Explorer balloon tip notifications",
                registry_path=r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Advanced",
                registry_key="EnableBalloonTips",
                hive=winreg.HKEY_CURRENT_USER,
                expected_value=0,
                value_type=winreg.REG_DWORD,
                test_type="disabled_test",
                category="Explorer UI"
            ),
            
            RegistryTest(
                name="Explorer Balloon Tips - Info Tips",
                description="Disable Explorer info tips",
                registry_path=r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Advanced",
                registry_key="ShowInfoTip",
                hive=winreg.HKEY_CURRENT_USER,
                expected_value=0,
                value_type=winreg.REG_DWORD,
                test_type="disabled_test",
                category="Explorer UI"
            ),
            
            # Explorer Info Tip
            RegistryTest(
                name="Explorer Info Tip - Folder Tips",
                description="Disable folder info tips in Explorer",
                registry_path=r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Advanced",
                registry_key="FolderContentsInfoTip",
                hive=winreg.HKEY_CURRENT_USER,
                expected_value=0,
                value_type=winreg.REG_DWORD,
                test_type="disabled_test",
                category="Explorer UI"
            ),
            
            # === DEFENDER REALTIME MONITORING ===
            
            # DisableRealtimeMonitoring
            RegistryTest(
                name="DisableRealtimeMonitoring - Realtime",
                description="Disable Windows Defender real-time monitoring",
                registry_path=r"SOFTWARE\Policies\Microsoft\Windows Defender",
                registry_key="DisableRealtimeMonitoring",
                hive=winreg.HKEY_LOCAL_MACHINE,
                expected_value=1,
                value_type=winreg.REG_DWORD,
                test_type="enabled_test",
                category="Defender Monitoring"
            ),
            
            RegistryTest(
                name="DisableRealtimeMonitoring - Behavior",
                description="Disable Windows Defender behavior monitoring",
                registry_path=r"SOFTWARE\Policies\Microsoft\Windows Defender\Real-Time Protection",
                registry_key="DisableBehaviorMonitoring",
                hive=winreg.HKEY_LOCAL_MACHINE,
                expected_value=1,
                value_type=winreg.REG_DWORD,
                test_type="enabled_test",
                category="Defender Monitoring"
            ),
            
            RegistryTest(
                name="DisableRealtimeMonitoring - On Access",
                description="Disable Windows Defender on-access protection",
                registry_path=r"SOFTWARE\Policies\Microsoft\Windows Defender\Real-Time Protection",
                registry_key="DisableOnAccessProtection",
                hive=winreg.HKEY_LOCAL_MACHINE,
                expected_value=1,
                value_type=winreg.REG_DWORD,
                test_type="enabled_test",
                category="Defender Monitoring"
            )
        ]
        return tests
    
    def check_registry_value(self, test: RegistryTest) -> Dict:
        """Check if a registry value exists and matches expected value"""
        if not self.is_windows:
            return {
                'status': RegistryStatus.ERROR,
                'message': 'Windows required for registry operations',
                'test_name': test.name,
                'test_type': test.test_type,
                'category': test.category
            }
        
        try:
            with winreg.OpenKey(test.hive, test.registry_path, 0, winreg.KEY_READ) as key:
                try:
                    value, value_type = winreg.QueryValueEx(key, test.registry_key)
                    
                    # Check if value matches expected
                    if value == test.expected_value:
                        status = RegistryStatus.ENABLED if test.test_type == "enabled_test" else RegistryStatus.DISABLED
                        message = f"Registry key found with correct value: {value}"
                    else:
                        status = RegistryStatus.ERROR
                        message = f"Registry key found but value mismatch. Expected: {test.expected_value}, Found: {value}"
                    
                    return {
                        'status': status,
                        'message': message,
                        'found_value': value,
                        'expected_value': test.expected_value,
                        'test_name': test.name,
                        'test_type': test.test_type,
                        'category': test.category,
                        'registry_path': f"{test.hive}\\{test.registry_path}\\{test.registry_key}",
                        'value_type': value_type
                    }
                    
                except OSError:
                    return {
                        'status': RegistryStatus.NOT_FOUND,
                        'message': 'Registry key not found',
                        'test_name': test.name,
                        'test_type': test.test_type,
                        'category': test.category,
                        'registry_path': f"{test.hive}\\{test.registry_path}\\{test.registry_key}"
                    }
                    
        except OSError:
            return {
                'status': RegistryStatus.NOT_FOUND,
                'message': 'Registry path not found',
                'test_name': test.name,
                'test_type': test.test_type,
                'category': test.category,
                'registry_path': f"{test.hive}\\{test.registry_path}\\{test.registry_key}"
            }
        except Exception as e:
            return {
                'status': RegistryStatus.ERROR,
                'message': f'Error accessing registry: {str(e)}',
                'test_name': test.name,
                'test_type': test.test_type,
                'category': test.category,
                'registry_path': f"{test.hive}\\{test.registry_path}\\{test.registry_key}"
            }
    
    def set_registry_value(self, test: RegistryTest) -> Dict:
        """Set a registry value for testing purposes"""
        if not self.is_windows:
            return {
                'status': 'failed',
                'message': 'Windows required for registry operations',
                'test_name': test.name
            }
        
        if not self.is_admin:
            return {
                'status': 'failed',
                'message': 'Administrator privileges required for registry modifications',
                'test_name': test.name
            }
        
        try:
            # Create parent keys if they don't exist
            parent_path = test.registry_path
            
            # For context menu items, we need to create the full path structure
            if "runas" in test.registry_path:
                # Create the command subkey for context menus
                command_path = f"{test.registry_path}\\command"
                with winreg.CreateKey(test.hive, command_path) as key:
                    winreg.SetValueEx(key, test.registry_key, 0, test.value_type, test.expected_value)
            else:
                with winreg.CreateKey(test.hive, test.registry_path) as key:
                    winreg.SetValueEx(key, test.registry_key, 0, test.value_type, test.expected_value)
                
                return {
                    'status': 'success',
                    'message': f'Successfully set registry value to {test.expected_value}',
                    'test_name': test.name,
                    'registry_path': f"{test.hive}\\{test.registry_path}\\{test.registry_key}"
                }
                
        except Exception as e:
            return {
                'status': 'failed',
                'message': f'Failed to set registry value: {str(e)}',
                'test_name': test.name,
                'registry_path': f"{test.hive}\\{test.registry_path}\\{test.registry_key}"
            }
    
    def remove_registry_value(self, test: RegistryTest) -> Dict:
        """Remove a registry value for cleanup"""
        if not self.is_windows or not self.is_admin:
            return {
                'status': 'failed',
                'message': 'Windows and admin privileges required for registry cleanup',
                'test_name': test.name
            }
        
        try:
            with winreg.OpenKey(test.hive, test.registry_path, 0, winreg.KEY_WRITE) as key:
                winreg.DeleteValue(key, test.registry_key)
                
                return {
                    'status': 'success',
                    'message': 'Successfully removed registry value',
                    'test_name': test.name,
                    'registry_path': f"{test.hive}\\{test.registry_path}\\{test.registry_key}"
                }
                
        except OSError:
            return {
                'status': 'not_found',
                'message': 'Registry value not found for cleanup',
                'test_name': test.name
            }
        except Exception as e:
            return {
                'status': 'failed',
                'message': f'Failed to remove registry value: {str(e)}',
                'test_name': test.name
            }
    
    def verify_client_registry_items(self) -> Dict:
        """Verify all registry items defined in client.py"""
        if not CLIENT_AVAILABLE:
            return {'status': 'error', 'message': 'client.py not available'}
            
        results = {
            'total': len(client.REGISTRY_MAP),
            'verified': 0,
            'failed': 0,
            'details': []
        }
        
        print(f"\n{'='*80}")
        print(f"VERIFYING CLIENT REGISTRY ITEMS ({len(client.REGISTRY_MAP)} items)")
        print(f"{'='*80}\n")
        
        for name, (hive_str, path, value_name) in client.REGISTRY_MAP.items():
            item_result = {
                'name': name,
                'path': f"{hive_str}\\{path}",
                'value_name': value_name,
                'status': 'unknown',
                'current_value': None,
                'message': ''
            }
            
            try:
                hive = None
                if hive_str == 'HKCU': hive = winreg.HKEY_CURRENT_USER
                elif hive_str == 'HKLM': hive = winreg.HKEY_LOCAL_MACHINE
                elif hive_str == 'HKCR': hive = winreg.HKEY_CLASSES_ROOT
                
                try:
                    with winreg.OpenKey(hive, path, 0, winreg.KEY_READ) as key:
                        if value_name:
                            val, val_type = winreg.QueryValueEx(key, value_name)
                            item_result['current_value'] = val
                            
                            if val in [0, 1]:
                                item_result['status'] = 'verified'
                                item_result['message'] = 'Present and valid boolean'
                                results['verified'] += 1
                                print(f"[OK] {name}: Found = {val}")
                            else:
                                item_result['status'] = 'warning'
                                item_result['message'] = f'Present but non-boolean value: {val}'
                                results['failed'] += 1
                                print(f"[WARN] {name}: Found = {val} (Expected 0/1)")
                        else:
                            item_result['status'] = 'verified'
                            item_result['message'] = 'Key present'
                            results['verified'] += 1
                            print(f"[OK] {name}: Key present")
                            
                except FileNotFoundError:
                    item_result['status'] = 'missing'
                    item_result['message'] = 'Key or value not found'
                    results['failed'] += 1
                    print(f"[MISSING] {name}: Not found")
                        
            except PermissionError:
                item_result['status'] = 'error'
                item_result['message'] = 'Permission denied'
                results['failed'] += 1
                print(f"[ERROR] {name}: Permission denied")
            except Exception as e:
                item_result['status'] = 'error'
                item_result['message'] = str(e)
                results['failed'] += 1
                print(f"[ERROR] {name}: {e}")
                
            results['details'].append(item_result)
            
        return results

    def run_category_tests(self, category: str = None, simulate_enabled: bool = False) -> Dict:
        """Run tests for specific category or all categories"""
        tests = self._get_enhanced_registry_tests()
        
        # Filter by category if specified
        if category:
            tests = [t for t in tests if t.category.lower() == category.lower()]
        
        results = {
            'system_info': {
                'platform': platform.system(),
                'is_windows': self.is_windows,
                'is_admin': self.is_admin,
                'test_timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                'category': category or 'All Categories'
            },
            'tests': [],
            'summary': {
                'total_tests': len(tests),
                'passed': 0,
                'failed': 0,
                'not_found': 0,
                'errors': 0,
                'by_category': {}
            }
        }
        
        print(f"\n{'='*100}")
        print(f"ENHANCED REGISTRY UI TEST SUITE")
        print(f"{'='*100}")
        print(f"Platform: {platform.system()}")
        print(f"Admin Rights: {self.is_admin}")
        print(f"Category: {category or 'All Categories'}")
        print(f"Total Tests: {len(tests)}")
        print(f"{'='*100}\n")
        
        # Group tests by category for better organization
        categories = {}
        for test in tests:
            if test.category not in categories:
                categories[test.category] = []
            categories[test.category].append(test)
        
        for cat_name, cat_tests in categories.items():
            print(f"\n{'='*60}")
            print(f"CATEGORY: {cat_name.upper()}")
            print(f"{'='*60}\n")
            
            for test in cat_tests:
                print(f"Testing: {test.name}")
                print(f"Description: {test.description}")
                print(f"Registry Path: {test.hive}\\{test.registry_path}\\{test.registry_key}")
                
                # If simulating enabled state, set the registry value first
                if simulate_enabled and self.is_windows and self.is_admin:
                    print(f"Simulating enabled state...")
                    set_result = self.set_registry_value(test)
                    if set_result['status'] != 'success':
                        print(f"Warning: Could not set registry value: {set_result['message']}")
                
                # Check the registry value
                result = self.check_registry_value(test)
                results['tests'].append(result)
                
                # Print result
                print(f"Status: {result['status'].value}")
                print(f"Message: {result['message']}")
                if 'found_value' in result:
                    print(f"Found Value: {result['found_value']}")
                    print(f"Expected Value: {result['expected_value']}")
                print(f"{'-'*60}\n")
                
                # Update summary
                if result['status'] == RegistryStatus.ENABLED or result['status'] == RegistryStatus.DISABLED:
                    results['summary']['passed'] += 1
                    if cat_name not in results['summary']['by_category']:
                        results['summary']['by_category'][cat_name] = {'passed': 0, 'failed': 0, 'not_found': 0, 'errors': 0}
                    results['summary']['by_category'][cat_name]['passed'] += 1
                elif result['status'] == RegistryStatus.NOT_FOUND:
                    results['summary']['not_found'] += 1
                    if cat_name not in results['summary']['by_category']:
                        results['summary']['by_category'][cat_name] = {'passed': 0, 'failed': 0, 'not_found': 0, 'errors': 0}
                    results['summary']['by_category'][cat_name]['not_found'] += 1
                else:
                    results['summary']['failed'] += 1
                    if cat_name not in results['summary']['by_category']:
                        results['summary']['by_category'][cat_name] = {'passed': 0, 'failed': 0, 'not_found': 0, 'errors': 0}
                    results['summary']['by_category'][cat_name]['failed'] += 1
        
        # Print summary
        print(f"\n{'='*100}")
        print(f"TEST SUMMARY")
        print(f"{'='*100}")
        print(f"Total Tests: {results['summary']['total_tests']}")
        print(f"Passed: {results['summary']['passed']}")
        print(f"Failed: {results['summary']['failed']}")
        print(f"Not Found: {results['summary']['not_found']}")
        print(f"Success Rate: {(results['summary']['passed'] / results['summary']['total_tests'] * 100):.1f}%")
        
        if results['summary']['by_category']:
            print(f"\nBy Category:")
            for cat, stats in results['summary']['by_category'].items():
                total = sum(stats.values())
                if total > 0:
                    print(f"  {cat}: Passed={stats['passed']}, Failed={stats['failed']}, Not Found={stats['not_found']}")
        
        print(f"{'='*100}")
        
        return results
    
    def cleanup_all_tests(self) -> Dict:
        """Remove all test registry values for cleanup"""
        tests = self._get_enhanced_registry_tests()
        cleanup_results = []
        
        print(f"\n{'='*100}")
        print(f"REGISTRY CLEANUP")
        print(f"{'='*100}\n")
        
        for test in tests:
            print(f"Cleaning up: {test.name}")
            result = self.remove_registry_value(test)
            cleanup_results.append(result)
            print(f"Status: {result['status']}")
            print(f"Message: {result['message']}")
            print(f"{'-'*60}")
        
        return {
            'cleanup_count': len([r for r in cleanup_results if r['status'] == 'success']),
            'results': cleanup_results
        }
    
    def test_specific_ui_toggle(self, toggle_name: str, enable: bool = True) -> Dict:
        """Test a specific UI toggle by name"""
        tests = self._get_enhanced_registry_tests()
        
        # Find the test by name (partial match)
        matching_tests = [t for t in tests if toggle_name.lower() in t.name.lower()]
        
        if not matching_tests:
            return {
                'status': 'error',
                'message': f'No registry tests found matching "{toggle_name}"',
                'available_tests': [t.name for t in tests]
            }
        
        if len(matching_tests) > 1:
            return {
                'status': 'error',
                'message': f'Multiple tests match "{toggle_name}": {[t.name for t in matching_tests]}',
                'available_tests': [t.name for t in tests]
            }
        
        test = matching_tests[0]
        
        if enable and self.is_windows and self.is_admin:
            # Enable the registry setting
            result = self.set_registry_value(test)
            if result['status'] == 'success':
                # Verify it was set correctly
                check_result = self.check_registry_value(test)
                return {
                    'status': 'success',
                    'message': f'Successfully enabled {test.name}',
                    'set_result': result,
                    'verify_result': check_result
                }
            else:
                return result
        else:
            # Just check the current state
            return self.check_registry_value(test)

def main():
    """Main function with enhanced UI"""
    tester = EnhancedRegistryUITester()
    
    print("Enhanced Registry UI Test Suite")
    print("This tool tests registry operations from the bypasses & registry tablist")
    print("\nAvailable UI Components to Test:")
    print("1. Policy Push Notifications")
    print("2. Policy Windows Update") 
    print("3. Context Runas Cmd")
    print("4. Context Powershell Admin")
    print("5. Notify Center Hkcu")
    print("6. Notify Center Hklm")
    print("7. Defender Ux Suppress")
    print("8. Toast Global Above Lock")
    print("9. Toast Global Critical Above Lock")
    print("10. Toast Windows Update")
    print("11. Toast Security Maintenance")
    print("12. Toast Windows Security")
    print("13. Toast Sec Health Ui")
    print("14. Explorer Balloon Tips")
    print("15. Explorer Info Tip")
    print("16. DisableRealtimeMonitoring")
    print("\nAdvanced Options:")
    print("A. Test by Category (Policy, Context Menu, Notification Center, etc.)")
    print("B. Test All Components")
    print("C. Simulate Enabled State (requires admin)")
    print("D. Cleanup Registry")
    print("E. Test Specific Toggle")
    print("F. Verify All Client Registry Items")
    
    try:
        choice = input("\nEnter your choice (1-16, A-F): ").strip().upper()
        
        if choice in ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15", "16"]:
            # Map numbers to toggle names
            toggle_map = {
                "1": "Policy Push Notifications",
                "2": "Policy Windows Update",
                "3": "Context Runas Cmd", 
                "4": "Context Powershell Admin",
                "5": "Notify Center Hkcu",
                "6": "Notify Center Hklm",
                "7": "Defender Ux Suppress",
                "8": "Toast Global Above Lock",
                "9": "Toast Global Critical Above Lock",
                "10": "Toast Windows Update",
                "11": "Toast Security Maintenance",
                "12": "Toast Windows Security",
                "13": "Toast Sec Health Ui",
                "14": "Explorer Balloon Tips",
                "15": "Explorer Info Tip",
                "16": "DisableRealtimeMonitoring"
            }
            
            toggle_name = toggle_map[choice]
            enable = input(f"Enable {toggle_name}? (y/n): ").strip().lower() == 'y'
            result = tester.test_specific_ui_toggle(toggle_name, enable)
            print(f"\nResult: {json.dumps(result, indent=2, default=str)}")
            
        elif choice == "A":
            print("\nCategories:")
            print("1. Policy")
            print("2. Context Menu")
            print("3. Notification Center")
            print("4. Defender UX")
            print("5. Toast Notifications")
            print("6. Explorer UI")
            print("7. Defender Monitoring")
            
            cat_choice = input("Select category (1-7): ").strip()
            cat_map = {
                "1": "Policy",
                "2": "Context Menu",
                "3": "Notification Center",
                "4": "Defender UX",
                "5": "Toast Notifications",
                "6": "Explorer UI",
                "7": "Defender Monitoring"
            }
            
            if cat_choice in cat_map:
                results = tester.run_category_tests(cat_map[cat_choice])
                filename = f"registry_category_test_{cat_map[cat_choice]}_{time.strftime('%Y%m%d_%H%M%S')}.json"
                with open(filename, 'w') as f:
                    json.dump(results, f, indent=2, default=str)
                print(f"\nResults saved to: {filename}")
            else:
                print("Invalid category choice.")
                
        elif choice == "B":
            results = tester.run_category_tests()
            filename = f"registry_all_tests_{time.strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            print(f"\nResults saved to: {filename}")
            
        elif choice == "C":
            if not tester.is_admin:
                print("Administrator privileges required for simulation!")
                return
            
            results = tester.run_category_tests(simulate_enabled=True)
            filename = f"registry_simulation_{time.strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            print(f"\nResults saved to: {filename}")
            
        elif choice == "D":
            cleanup_results = tester.cleanup_all_tests()
            print(f"\nCleanup completed. Removed {cleanup_results['cleanup_count']} registry values.")
            
        elif choice == "E":
            toggle_name = input("Enter toggle name (partial match): ").strip()
            
            # Find matches manually first
            all_tests = tester._get_enhanced_registry_tests()
            matches = [t for t in all_tests if toggle_name.lower() in t.name.lower()]
            
            if not matches:
                 print(f"No tests match '{toggle_name}'")
                 return

            selected_test = None
            if len(matches) > 1:
                print(f"\nMultiple matches found for '{toggle_name}':")
                for i, t in enumerate(matches):
                    print(f"{i+1}. {t.name}")
                
                try:
                    idx = int(input("\nSelect test number: ")) - 1
                    if 0 <= idx < len(matches):
                        selected_test = matches[idx]
                    else:
                        print("Invalid selection.")
                        return
                except ValueError:
                    print("Invalid input.")
                    return
            else:
                selected_test = matches[0]

            enable = input(f"Enable {selected_test.name}? (y/n): ").strip().lower() == 'y'
            result = tester.test_specific_ui_toggle(selected_test.name, enable)
            print(f"\nResult: {json.dumps(result, indent=2, default=str)}")
            
        elif choice == "F":
            results = tester.verify_client_registry_items()
            filename = f"registry_client_verification_{time.strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            print(f"\nResults saved to: {filename}")
            
        else:
            print("Invalid choice. Please run again.")
            return
            
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user.")
    except Exception as e:
        print(f"\nError during testing: {str(e)}")

if __name__ == "__main__":
    main()