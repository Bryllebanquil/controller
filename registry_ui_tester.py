"""
Registry Test Suite for UI Toggle Operations
Tests all registry modifications from the bypasses & registry tablist interface
"""

import ctypes
import platform
import winreg
import json
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

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

class RegistryUITester:
    """Test registry operations from UI toggle components"""
    
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
    
    def _get_registry_tests(self) -> List[RegistryTest]:
        """Define all registry tests for UI components"""
        tests = [
            # Policy Push Notifications
            RegistryTest(
                name="Policy Push Notifications",
                description="Test Policy Push Notifications registry setting",
                registry_path=r"SOFTWARE\Policies\Microsoft\Windows\PushNotifications-Enabled",
                registry_key="NoCloudApplicationNotification",
                hive=winreg.HKEY_LOCAL_MACHINE,
                expected_value=1,
                value_type=winreg.REG_DWORD,
                test_type="enabled_test"
            ),
            
            # Policy Windows Update
            RegistryTest(
                name="Policy Windows Update",
                description="Test Windows Update policy registry setting",
                registry_path=r"SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate\AU",
                registry_key="NoAutoUpdate",
                hive=winreg.HKEY_LOCAL_MACHINE,
                expected_value=1,
                value_type=winreg.REG_DWORD,
                test_type="disabled_test"
            ),
            
            # Context Runas Cmd
            RegistryTest(
                name="Context Runas Cmd",
                description="Test context menu Run as Administrator for CMD",
                registry_path=r"SOFTWARE\Classes\cmdfile\shell\runas",
                registry_key="",
                hive=winreg.HKEY_CLASSES_ROOT,
                expected_value="",
                value_type=winreg.REG_SZ,
                test_type="disabled_test"
            ),
            
            # Context Powershell Admin
            RegistryTest(
                name="Context Powershell Admin",
                description="Test context menu Run as Administrator for PowerShell",
                registry_path=r"SOFTWARE\Classes\Microsoft.PowerShellScript.1\shell\runas",
                registry_key="",
                hive=winreg.HKEY_CLASSES_ROOT,
                expected_value="",
                value_type=winreg.REG_SZ,
                test_type="disabled_test"
            ),
            
            # Notify Center Hkcu
            RegistryTest(
                name="Notify Center Hkcu",
                description="Test notification center HKCU settings",
                registry_path=r"SOFTWARE\Policies\Microsoft\Windows\Explorer",
                registry_key="DisableNotificationCenter",
                hive=winreg.HKEY_CURRENT_USER,
                expected_value=1,
                value_type=winreg.REG_DWORD,
                test_type="disabled_test"
            ),
            
            # Notify Center Hklm
            RegistryTest(
                name="Notify Center Hklm",
                description="Test notification center HKLM settings",
                registry_path=r"SOFTWARE\Policies\Microsoft\Windows\Explorer",
                registry_key="DisableNotificationCenter",
                hive=winreg.HKEY_LOCAL_MACHINE,
                expected_value=1,
                value_type=winreg.REG_DWORD,
                test_type="disabled_test"
            ),
            
            # Defender Ux Suppress
            RegistryTest(
                name="Defender Ux Suppress",
                description="Test Windows Defender UX suppression",
                registry_path=r"SOFTWARE\Policies\Microsoft\Windows Defender\UX Configuration",
                registry_key="Notification_Suppress",
                hive=winreg.HKEY_LOCAL_MACHINE,
                expected_value=1,
                value_type=winreg.REG_DWORD,
                test_type="disabled_test"
            ),
            
            # Toast Global Above Lock
            RegistryTest(
                name="Toast Global Above Lock",
                description="Test toast notifications above lock screen",
                registry_path=r"SOFTWARE\Policies\Microsoft\Windows\System",
                registry_key="DisableAcrylicBackgroundOnLogon",
                hive=winreg.HKEY_LOCAL_MACHINE,
                expected_value=1,
                value_type=winreg.REG_DWORD,
                test_type="disabled_test"
            ),
            
            # Toast Global Critical Above Lock
            RegistryTest(
                name="Toast Global Critical Above Lock",
                description="Test critical toast notifications above lock screen",
                registry_path=r"SOFTWARE\Policies\Microsoft\Windows\System",
                registry_key="DisableLockScreenAppNotifications",
                hive=winreg.HKEY_LOCAL_MACHINE,
                expected_value=1,
                value_type=winreg.REG_DWORD,
                test_type="disabled_test"
            ),
            
            # Toast Windows Update
            RegistryTest(
                name="Toast Windows Update",
                description="Test Windows Update toast notifications",
                registry_path=r"SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate",
                registry_key="SetDisableUXWUAccess",
                hive=winreg.HKEY_LOCAL_MACHINE,
                expected_value=1,
                value_type=winreg.REG_DWORD,
                test_type="disabled_test"
            ),
            
            # Toast Security Maintenance
            RegistryTest(
                name="Toast Security Maintenance",
                description="Test Security Maintenance toast notifications",
                registry_path=r"SOFTWARE\Policies\Microsoft\Windows Defender Security Center",
                registry_key="DisableWindowsSecurityCenterNotifications",
                hive=winreg.HKEY_LOCAL_MACHINE,
                expected_value=1,
                value_type=winreg.REG_DWORD,
                test_type="disabled_test"
            ),
            
            # Toast Windows Security
            RegistryTest(
                name="Toast Windows Security",
                description="Test Windows Security toast notifications",
                registry_path=r"SOFTWARE\Policies\Microsoft\Windows Defender Security Center",
                registry_key="DisableWindowsSecurityCenter",
                hive=winreg.HKEY_LOCAL_MACHINE,
                expected_value=1,
                value_type=winreg.REG_DWORD,
                test_type="disabled_test"
            ),
            
            # Toast Sec Health Ui
            RegistryTest(
                name="Toast Sec Health Ui",
                description="Test Security Health UI toast notifications",
                registry_path=r"SOFTWARE\Policies\Microsoft\Windows Defender Security Center",
                registry_key="DisableHealthUI",
                hive=winreg.HKEY_LOCAL_MACHINE,
                expected_value=1,
                value_type=winreg.REG_DWORD,
                test_type="disabled_test"
            ),
            
            # Explorer Balloon Tips
            RegistryTest(
                name="Explorer Balloon Tips",
                description="Test Explorer balloon tip notifications",
                registry_path=r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Advanced",
                registry_key="EnableBalloonTips",
                hive=winreg.HKEY_CURRENT_USER,
                expected_value=0,
                value_type=winreg.REG_DWORD,
                test_type="disabled_test"
            ),
            
            # Explorer Info Tip
            RegistryTest(
                name="Explorer Info Tip",
                description="Test Explorer info tip notifications",
                registry_path=r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Advanced",
                registry_key="ShowInfoTip",
                hive=winreg.HKEY_CURRENT_USER,
                expected_value=0,
                value_type=winreg.REG_DWORD,
                test_type="disabled_test"
            ),
            
            # DisableRealtimeMonitoring
            RegistryTest(
                name="DisableRealtimeMonitoring",
                description="Test Windows Defender real-time monitoring disable",
                registry_path=r"SOFTWARE\Policies\Microsoft\Windows Defender",
                registry_key="DisableRealtimeMonitoring",
                hive=winreg.HKEY_LOCAL_MACHINE,
                expected_value=1,
                value_type=winreg.REG_DWORD,
                test_type="enabled_test"
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
                'test_type': test.test_type
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
                        'registry_path': f"{test.hive}\\{test.registry_path}\\{test.registry_key}"
                    }
                    
                except OSError:
                    return {
                        'status': RegistryStatus.NOT_FOUND,
                        'message': 'Registry key not found',
                        'test_name': test.name,
                        'test_type': test.test_type,
                        'registry_path': f"{test.hive}\\{test.registry_path}\\{test.registry_key}"
                    }
                    
        except OSError:
            return {
                'status': RegistryStatus.NOT_FOUND,
                'message': 'Registry path not found',
                'test_name': test.name,
                'test_type': test.test_type,
                'registry_path': f"{test.hive}\\{test.registry_path}\\{test.registry_key}"
            }
        except Exception as e:
            return {
                'status': RegistryStatus.ERROR,
                'message': f'Error accessing registry: {str(e)}',
                'test_name': test.name,
                'test_type': test.test_type,
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
    
    def run_all_tests(self, simulate_enabled: bool = False) -> Dict:
        """Run all registry tests and return comprehensive results"""
        tests = self._get_registry_tests()
        results = {
            'system_info': {
                'platform': platform.system(),
                'is_windows': self.is_windows,
                'is_admin': self.is_admin,
                'test_timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
            },
            'tests': [],
            'summary': {
                'total_tests': len(tests),
                'passed': 0,
                'failed': 0,
                'not_found': 0,
                'errors': 0
            }
        }
        
        print(f"\n{'='*80}")
        print(f"REGISTRY UI TEST SUITE")
        print(f"{'='*80}")
        print(f"Platform: {platform.system()}")
        print(f"Admin Rights: {self.is_admin}")
        print(f"Total Tests: {len(tests)}")
        print(f"{'='*80}\n")
        
        for test in tests:
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
            elif result['status'] == RegistryStatus.NOT_FOUND:
                results['summary']['not_found'] += 1
            else:
                results['summary']['failed'] += 1
        
        # Print summary
        print(f"{'='*80}")
        print(f"TEST SUMMARY")
        print(f"{'='*80}")
        print(f"Total Tests: {results['summary']['total_tests']}")
        print(f"Passed: {results['summary']['passed']}")
        print(f"Failed: {results['summary']['failed']}")
        print(f"Not Found: {results['summary']['not_found']}")
        print(f"Success Rate: {(results['summary']['passed'] / results['summary']['total_tests'] * 100):.1f}%")
        print(f"{'='*80}")
        
        return results
    
    def cleanup_all_tests(self) -> Dict:
        """Remove all test registry values for cleanup"""
        tests = self._get_registry_tests()
        cleanup_results = []
        
        print(f"\n{'='*80}")
        print(f"REGISTRY CLEANUP")
        print(f"{'='*80}\n")
        
        for test in tests:
            print(f"Cleaning up: {test.name}")
            result = self.remove_registry_value(test)
            cleanup_results.append(result)
            print(f"Status: {result['status']}")
            print(f"Message: {result['message']}")
            print(f"{'-'*40}")
        
        return {
            'cleanup_count': len([r for r in cleanup_results if r['status'] == 'success']),
            'results': cleanup_results
        }

def main():
    """Main function to run registry tests"""
    tester = RegistryUITester()
    
    print("Registry UI Test Suite")
    print("This tool tests registry operations from the bypasses & registry tablist")
    print("\nOptions:")
    print("1. Check current registry state")
    print("2. Simulate enabled state and test")
    print("3. Cleanup registry (remove test values)")
    print("4. Run all tests with detailed output")
    
    try:
        choice = input("\nEnter your choice (1-4): ").strip()
        
        if choice == "1":
            results = tester.run_all_tests(simulate_enabled=False)
            
        elif choice == "2":
            print("\nThis will attempt to set registry values to simulate enabled state")
            print("Administrator privileges required!")
            results = tester.run_all_tests(simulate_enabled=True)
            
        elif choice == "3":
            cleanup_results = tester.cleanup_all_tests()
            print(f"\nCleanup completed. Removed {cleanup_results['cleanup_count']} registry values.")
            return
            
        elif choice == "4":
            results = tester.run_all_tests(simulate_enabled=False)
            
            # Save detailed results to file
            filename = f"registry_test_results_{time.strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            print(f"\nDetailed results saved to: {filename}")
            
        else:
            print("Invalid choice. Please run again.")
            return
            
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user.")
    except Exception as e:
        print(f"\nError during testing: {str(e)}")

if __name__ == "__main__":
    main()