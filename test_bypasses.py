"""
Unit tests for bypasses and registry modules
Tests all functional paths as specified in requirements
"""

import unittest
import unittest.mock
import platform
import subprocess
import os
import sys
import ctypes
from unittest.mock import patch, MagicMock

# Import the modules we're testing
import bypasses
import registry

class TestBypassesModule(unittest.TestCase):
    """Test cases for bypasses.py module"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.original_platform = platform.system
        self.original_shell32 = None
        if hasattr(ctypes, 'windll'):
            self.original_shell32 = getattr(ctypes.windll, 'shell32', None)
    
    def tearDown(self):
        """Clean up after tests"""
        platform.system = self.original_platform
        if self.original_shell32 and hasattr(ctypes.windll, 'shell32'):
            ctypes.windll.shell32 = self.original_shell32
    
    def test_is_admin_windows_non_admin(self):
        """Test is_admin() on Windows when not admin"""
        with patch('platform.system', return_value='Windows'):
            with patch('ctypes.windll.shell32.IsUserAnAdmin', return_value=0):
                result = bypasses.is_admin()
                self.assertFalse(result)
    
    def test_is_admin_windows_admin(self):
        """Test is_admin() on Windows when admin"""
        with patch('platform.system', return_value='Windows'):
            with patch('ctypes.windll.shell32.IsUserAnAdmin', return_value=1):
                result = bypasses.is_admin()
                self.assertTrue(result)
    
    def test_is_admin_non_windows(self):
        """Test is_admin() on non-Windows systems"""
        with patch('platform.system', return_value='Linux'):
            result = bypasses.is_admin()
            self.assertFalse(result)
    
    def test_is_admin_exception(self):
        """Test is_admin() when exception occurs"""
        with patch('platform.system', return_value='Windows'):
            with patch('ctypes.windll.shell32.IsUserAnAdmin', side_effect=Exception("Test error")):
                result = bypasses.is_admin()
                self.assertFalse(result)
    
    def test_uac_bypass_non_windows(self):
        """Test uac_bypass() on non-Windows systems"""
        with patch('platform.system', return_value='Linux'):
            result = bypasses.uac_bypass()
            self.assertEqual(result['status'], 'failed')
    
    @patch('subprocess.run')
    @patch('time.sleep')
    def test_uac_bypass_windows_success(self, mock_sleep, mock_subprocess):
        """Test uac_bypass() success on Windows"""
        with patch('platform.system', return_value='Windows'):
            # Mock winreg
            mock_key = MagicMock()
            mock_key.__enter__ = MagicMock(return_value=mock_key)
            mock_key.__exit__ = MagicMock(return_value=None)
            
            mock_winreg = MagicMock()
            mock_winreg.CreateKey.return_value = mock_key
            mock_winreg.HKEY_CURRENT_USER = 'HKEY_CURRENT_USER'
            mock_winreg.REG_SZ = 1
            
            with patch.dict('sys.modules', {'winreg': mock_winreg}):
                result = bypasses.uac_bypass()
                self.assertEqual(result['status'], 'success')
                mock_subprocess.assert_called_once()
    
    def test_uac_bypass_windows_import_error(self):
        """Test uac_bypass() when winreg import fails"""
        with patch('platform.system', return_value='Windows'):
            with patch.dict('sys.modules', {'winreg': None}):
                result = bypasses.uac_bypass()
                self.assertEqual(result['status'], 'failed')
    
    def test_sleep_random_non_blocking(self):
        """Test sleep_random_non_blocking()"""
        with patch('time.sleep') as mock_sleep:
            bypasses.sleep_random_non_blocking()
            mock_sleep.assert_called_once()
            # Check that sleep was called with a value between 0.1 and 2.0
            sleep_call = mock_sleep.call_args[0][0]
            self.assertGreaterEqual(sleep_call, 0.1)
            self.assertLessEqual(sleep_call, 2.0)

class TestRegistryModule(unittest.TestCase):
    """Test cases for registry.py module"""
    
    def test_is_admin_windows_non_admin(self):
        """Test is_admin() on Windows when not admin"""
        with patch('platform.system', return_value='Windows'):
            with patch('ctypes.windll.shell32.IsUserAnAdmin', return_value=0):
                result = registry.is_admin()
                self.assertFalse(result)
    
    def test_is_admin_non_windows(self):
        """Test is_admin() on non-Windows systems"""
        with patch('platform.system', return_value='Linux'):
            result = registry.is_admin()
            self.assertFalse(result)
    
    def test_uac_bypass_non_windows(self):
        """Test uac_bypass() on non-Windows systems"""
        with patch('platform.system', return_value='Linux'):
            result = registry.uac_bypass()
            self.assertEqual(result['status'], 'failed')
            self.assertIn('Windows required', result['error'])
    
    @patch('subprocess.run')
    @patch('time.sleep')
    def test_uac_bypass_windows_success(self, mock_sleep, mock_subprocess):
        """Test uac_bypass() success on Windows"""
        with patch('platform.system', return_value='Windows'):
            mock_key = MagicMock()
            mock_key.__enter__ = MagicMock(return_value=mock_key)
            mock_key.__exit__ = MagicMock(return_value=None)
            
            mock_winreg = MagicMock()
            mock_winreg.CreateKey.return_value = mock_key
            mock_winreg.HKEY_CURRENT_USER = 'HKEY_CURRENT_USER'
            mock_winreg.REG_SZ = 1
            
            with patch.dict('sys.modules', {'winreg': mock_winreg}):
                result = registry.uac_bypass()
                self.assertEqual(result['status'], 'success')
                mock_subprocess.assert_called_once()
    
    def test_disable_defender_non_windows(self):
        """Test disable_defender() on non-Windows systems"""
        with patch('platform.system', return_value='Linux'):
            result = registry.disable_defender()
            self.assertEqual(result['status'], 'failed')
            self.assertIn('Windows required', result['error'])

class TestIntegration(unittest.TestCase):
    """Integration tests for bypasses and registry modules"""
    
    def test_admin_check_consistency(self):
        """Test that both modules return consistent admin status"""
        with patch('platform.system', return_value='Linux'):
            bypasses_result = bypasses.is_admin()
            registry_result = registry.is_admin()
            self.assertEqual(bypasses_result, registry_result)
    
    def test_uac_bypass_consistency(self):
        """Test that both modules handle UAC bypass consistently"""
        with patch('platform.system', return_value='Linux'):
            bypasses_result = bypasses.uac_bypass()
            registry_result = registry.uac_bypass()
            
            self.assertEqual(bypasses_result['status'], registry_result['status'])
            self.assertIn('failed', bypasses_result['status'])

class TestErrorHandling(unittest.TestCase):
    """Test error handling and edge cases"""
    
    def test_uac_bypass_exception_handling(self):
        """Test UAC bypass exception handling"""
        with patch('platform.system', return_value='Windows'):
            with patch('builtins.__import__', side_effect=ImportError("No module named 'winreg'")):
                result = bypasses.uac_bypass()
                self.assertEqual(result['status'], 'failed')
    
    def test_is_admin_exception_handling(self):
        """Test is_admin exception handling"""
        with patch('platform.system', return_value='Windows'):
            with patch('ctypes.windll.shell32.IsUserAnAdmin', side_effect=Exception("Test error")):
                result = bypasses.is_admin()
                self.assertFalse(result)
    
    def test_sleep_random_exception_handling(self):
        """Test sleep_random_non_blocking exception handling"""
        with patch('time.sleep', side_effect=Exception("Sleep error")):
            # Should not raise exception
            bypasses.sleep_random_non_blocking()

if __name__ == '__main__':
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTests(loader.loadTestsFromTestCase(TestBypassesModule))
    suite.addTests(loader.loadTestsFromTestCase(TestRegistryModule))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestErrorHandling))
    
    # Run tests with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"Test Summary:")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success: {result.wasSuccessful()}")
    print(f"{'='*60}")
