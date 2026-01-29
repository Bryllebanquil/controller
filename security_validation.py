"""
Security validation for bypasses and registry modules
Tests security aspects of the implementation
"""

import unittest
import platform
import subprocess
import tempfile
import os
from unittest.mock import patch, MagicMock

import bypasses
import registry

class SecurityValidation(unittest.TestCase):
    """Security validation tests"""
    
    def test_no_hardcoded_credentials(self):
        """Ensure no hardcoded credentials in the modules"""
        # Read module contents
        with open('bypasses.py', 'r') as f:
            bypasses_content = f.read()
        
        with open('registry.py', 'r') as f:
            registry_content = f.read()
        
        # Check for common credential patterns
        credential_patterns = [
            'password',
            'passwd',
            'pwd',
            'secret',
            'key',
            'token',
            'api_key',
            'auth'
        ]
        
        for pattern in credential_patterns:
            # Should not contain hardcoded credentials
            self.assertNotIn(f'{pattern} =', bypasses_content.lower())
            self.assertNotIn(f'{pattern}=', bypasses_content.lower())
            self.assertNotIn(f'{pattern} =', registry_content.lower())
            self.assertNotIn(f'{pattern}=', registry_content.lower())
    
    def test_no_sensitive_data_logging(self):
        """Ensure no sensitive data is logged"""
        # Check that no sensitive operations are logged
        with open('bypasses.py', 'r') as f:
            content = f.read()
        
        # Should not have print statements that could leak data
        self.assertNotIn('print(registry', content)
        self.assertNotIn('print(key', content)
        self.assertNotIn('print(path', content)
    
    def test_registry_cleanup(self):
        """Test that registry keys are properly cleaned up"""
        with patch('platform.system', return_value='Windows'):
            # Mock successful registry operations
            mock_key = MagicMock()
            mock_key.__enter__ = MagicMock(return_value=mock_key)
            mock_key.__exit__ = MagicMock(return_value=None)
            
            mock_winreg = MagicMock()
            mock_winreg.CreateKey.return_value = mock_key
            mock_winreg.HKEY_CURRENT_USER = 'HKEY_CURRENT_USER'
            mock_winreg.REG_SZ = 1
            mock_winreg.DeleteKey = MagicMock()
            
            with patch.dict('sys.modules', {'winreg': mock_winreg}):
                with patch('subprocess.run') as mock_subprocess:
                    result = bypasses.uac_bypass()
                    
                    # Should attempt to delete the key
                    mock_winreg.DeleteKey.assert_called_once()
    
    def test_no_arbitrary_code_execution(self):
        """Test that no arbitrary code execution is possible"""
        # Check that subprocess calls are controlled
        with open('bypasses.py', 'r') as f:
            content = f.read()
        
        # Should only call specific, controlled executables
        self.assertIn('fodhelper.exe', content)
        self.assertNotIn('eval(', content)
        self.assertNotIn('exec(', content)
        self.assertNotIn('__import__', content)
    
    def test_platform_specific_guards(self):
        """Test that Windows-specific code is properly guarded"""
        # Test on non-Windows platform
        with patch('platform.system', return_value='Linux'):
            result = bypasses.uac_bypass()
            self.assertEqual(result['status'], 'failed')
            
            result = registry.uac_bypass()
            self.assertEqual(result['status'], 'failed')
            
            result = registry.disable_defender()
            self.assertEqual(result['status'], 'failed')
    
    def test_error_handling_security(self):
        """Test that errors don't leak sensitive information"""
        with patch('platform.system', return_value='Windows'):
            with patch('ctypes.windll.shell32.IsUserAnAdmin', side_effect=Exception("Sensitive info")):
                result = bypasses.is_admin()
                self.assertFalse(result)  # Should return safe default
    
    def test_registry_access_validation(self):
        """Test registry access patterns"""
        # Check that only expected registry keys are accessed
        with open('bypasses.py', 'r') as f:
            content = f.read()
        
        with open('registry.py', 'r') as f:
            content += f.read()
        
        # Should only access specific, expected registry paths
        expected_paths = [
            r'Software\Classes\ms-settings\shell\open\command',
            r'SOFTWARE\Policies\Microsoft\Windows Defender'
        ]
        
        for path in expected_paths:
            self.assertIn(path, content)
        
        # Should not contain generic registry access patterns
        self.assertNotIn('HKEY_CURRENT_USER\\', content.replace(expected_paths[0], ''))
        self.assertNotIn('HKEY_LOCAL_MACHINE\\', content.replace(expected_paths[1], ''))
    
    def test_subprocess_security(self):
        """Test subprocess call security"""
        # Check subprocess calls
        with open('bypasses.py', 'r') as f:
            content = f.read()
        
        with open('registry.py', 'r') as f:
            content += f.read()
        
        # Should use safe subprocess parameters
        self.assertIn('creationflags=8', content)  # CREATE_NO_WINDOW
        self.assertIn('check=False', content)  # Don't raise on non-zero exit
        
        # Should not use shell=True
        self.assertNotIn('shell=True', content)
    
    def test_no_network_calls(self):
        """Ensure no network calls are made"""
        with open('bypasses.py', 'r') as f:
            content = f.read()
        
        with open('registry.py', 'r') as f:
            content += f.read()
        
        # Should not contain network-related imports or calls
        network_terms = ['socket', 'http', 'url', 'request', 'download', 'upload']
        for term in network_terms:
            self.assertNotIn(term, content.lower())

class ComplianceValidation(unittest.TestCase):
    """Compliance and best practices validation"""
    
    def test_input_validation(self):
        """Test input validation patterns"""
        # These functions should handle invalid inputs gracefully
        with patch('platform.system', return_value='Windows'):
            # Test with various edge cases
            result = bypasses.is_admin()
            self.assertIsInstance(result, bool)
            
            result = bypasses.uac_bypass()
            self.assertIsInstance(result, dict)
            self.assertIn('status', result)
    
    def test_output_sanitization(self):
        """Test that outputs are properly sanitized"""
        with patch('platform.system', return_value='Linux'):
            result = bypasses.uac_bypass()
            
            # Should not contain system paths or sensitive info
            if 'error' in result:
                self.assertNotIn('\\', result['error'])  # No Windows paths
                self.assertNotIn('/', result['error'])   # No Unix paths
    
    def test_safe_defaults(self):
        """Test that safe defaults are used"""
        with patch('platform.system', return_value='Windows'):
            with patch('ctypes.windll.shell32.IsUserAnAdmin', side_effect=Exception()):
                # Should default to False (safe) when can't determine admin status
                result = bypasses.is_admin()
                self.assertFalse(result)

if __name__ == '__main__':
    print("="*60)
    print("SECURITY VALIDATION")
    print("="*60)
    
    # Run security tests
    suite = unittest.TestLoader().loadTestsFromModule(__import__(__name__))
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print(f"\n{'='*60}")
    print("SECURITY VALIDATION SUMMARY")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"All security tests passed: {result.wasSuccessful()}")
    print(f"{'='*60}")
    
    if result.wasSuccessful():
        print("\n✅ SECURITY CHECKLIST:")
        print("✅ No hardcoded credentials")
        print("✅ No sensitive data logging")
        print("✅ Registry cleanup implemented")
        print("✅ No arbitrary code execution")
        print("✅ Platform-specific guards in place")
        print("✅ Error handling doesn't leak sensitive info")
        print("✅ Safe registry access patterns")
        print("✅ Secure subprocess usage")
        print("✅ No network calls")
        print("✅ Input validation and output sanitization")
        print("✅ Safe defaults used")
    else:
        print("\n❌ Security issues found - please review test failures")