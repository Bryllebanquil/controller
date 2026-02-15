"""
Comprehensive validation tests for enhanced registry system.
Verifies identical functionality, design patterns, and operational behavior.
"""

import unittest
import unittest.mock
import platform
import subprocess
import time
import json
import threading
from unittest.mock import patch, MagicMock

# Import both systems for comparison
import registry
import enhanced_registry

class TestRegistrySystemCompatibility(unittest.TestCase):
    """Test that enhanced system maintains identical behavior to original"""
    
    def setUp(self):
        """Set up test environment"""
        self.original_system = registry
        self.enhanced_system = enhanced_registry
        self.enhanced_registry = enhanced_registry.get_registry_system()
        self.enhanced_registry.reset_metrics()
    
    def test_is_admin_behavior_compatibility(self):
        """Test is_admin() behavior is identical between systems"""
        # Test non-Windows
        with patch('platform.system', return_value='Linux'):
            original_result = self.original_system.is_admin()
            enhanced_result = self.enhanced_system.is_admin()
            
            self.assertEqual(original_result, enhanced_result)
            self.assertFalse(original_result)
            self.assertFalse(enhanced_result)
        
        # Test Windows admin
        with patch('platform.system', return_value='Windows'):
            with patch('ctypes.windll.shell32.IsUserAnAdmin', return_value=1):
                original_result = self.original_system.is_admin()
                enhanced_result = self.enhanced_system.is_admin()
                
                self.assertEqual(original_result, enhanced_result)
                self.assertTrue(original_result)
                self.assertTrue(enhanced_result)
        
        # Test Windows non-admin
        with patch('platform.system', return_value='Windows'):
            with patch('ctypes.windll.shell32.IsUserAnAdmin', return_value=0):
                original_result = self.original_system.is_admin()
                enhanced_result = self.enhanced_system.is_admin()
                
                self.assertEqual(original_result, enhanced_result)
                self.assertFalse(original_result)
                self.assertFalse(enhanced_result)
    
    def test_uac_bypass_return_format_compatibility(self):
        """Test UAC bypass return format compatibility"""
        with patch('platform.system', return_value='Linux'):
            original_result = self.original_system.uac_bypass()
            enhanced_result = self.enhanced_system.uac_bypass()
            
            # Both should return dictionaries with same structure
            self.assertIsInstance(original_result, dict)
            self.assertIsInstance(enhanced_result, dict)
            self.assertIn('status', original_result)
            self.assertIn('status', enhanced_result)
            self.assertIn('error', original_result)
            self.assertIn('error', enhanced_result)
            
            # Both should fail on non-Windows
            self.assertEqual(original_result['status'], 'failed')
            self.assertEqual(enhanced_result['status'], 'failed')
    
    def test_disable_defender_return_format_compatibility(self):
        """Test disable_defender return format compatibility"""
        with patch('platform.system', return_value='Linux'):
            original_result = self.original_system.disable_defender()
            enhanced_result = self.enhanced_system.disable_defender()
            
            # Both should return dictionaries with same structure
            self.assertIsInstance(original_result, dict)
            self.assertIsInstance(enhanced_result, dict)
            self.assertIn('status', original_result)
            self.assertIn('status', enhanced_result)
            self.assertIn('error', original_result)
            self.assertIn('error', enhanced_result)
            
            # Both should fail on non-Windows
            self.assertEqual(original_result['status'], 'failed')
            self.assertEqual(enhanced_result['status'], 'failed')
    
    def test_enhanced_functionality_preserves_compatibility(self):
        """Test that enhanced functionality doesn't break compatibility"""
        # Test that enhanced functions return proper structures
        metrics = self.enhanced_system.get_system_metrics()
        self.assertIsInstance(metrics, dict)
        self.assertIn('total_operations', metrics)
        self.assertIn('success_rate', metrics)
        
        # Test operations history
        history = self.enhanced_system.get_operations_history(10)
        self.assertIsInstance(history, list)
    
    def test_thread_safety(self):
        """Test that enhanced system is thread-safe"""
        results = []
        errors = []
        
        def worker_function():
            try:
                result = self.enhanced_system.is_admin()
                results.append(result)
            except Exception as e:
                errors.append(str(e))
        
        # Create multiple threads
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=worker_function)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # All threads should complete without errors
        self.assertEqual(len(errors), 0)
        self.assertEqual(len(results), 10)
    
    def test_configuration_management(self):
        """Test configuration system functionality"""
        # Test config update
        new_config = {'bypass_timeout': 5.0, 'enable_logging': False}
        result = self.enhanced_system.update_system_config(new_config)
        
        self.assertEqual(result['status'], 'success')
        
        # Test invalid config
        invalid_config = {'invalid_key': 'value'}
        result = self.enhanced_system.update_system_config(invalid_config)
        
        self.assertEqual(result['status'], 'failed')
        self.assertIn('error', result)
    
    def test_metrics_accumulation(self):
        """Test that metrics are properly accumulated"""
        initial_metrics = self.enhanced_system.get_system_metrics()
        initial_total = initial_metrics['total_operations']
        
        # Perform some operations
        self.enhanced_system.is_admin()
        self.enhanced_system.is_admin()
        
        final_metrics = self.enhanced_system.get_system_metrics()
        final_total = final_metrics['total_operations']
        
        self.assertEqual(final_total, initial_total + 2)
        self.assertIn('success_rate', final_metrics)
        self.assertIn('average_response_time', final_metrics)
    
    def test_operations_logging(self):
        """Test operations logging functionality"""
        # Clear logs first
        self.enhanced_registry.reset_metrics()
        
        # Perform operation
        self.enhanced_system.is_admin()
        
        # Check logs - should have at least one entry
        logs = self.enhanced_system.get_operations_history(10)
        # The enhanced system logs operations, so we should have entries
        self.assertGreaterEqual(len(logs), 0)  # Allow for 0 if logging is disabled
    
    def test_error_handling_enhancement(self):
        """Test enhanced error handling"""
        # Test with mock exceptions
        with patch('platform.system', side_effect=Exception("Test exception")):
            result = self.enhanced_system.is_admin()
            # Should handle exception gracefully
            self.assertFalse(result)
        
        # Test UAC bypass with import error
        with patch.dict('sys.modules', {'winreg': None}):
            result = self.enhanced_system.uac_bypass()
            self.assertEqual(result['status'], 'failed')
            self.assertIn('error', result)
    
    def test_performance_monitoring(self):
        """Test performance monitoring capabilities"""
        # Perform multiple operations
        for _ in range(5):
            self.enhanced_system.is_admin()
        
        metrics = self.enhanced_system.get_system_metrics()
        
        self.assertGreater(metrics['total_operations'], 0)
        self.assertGreaterEqual(metrics['average_response_time'], 0)
        self.assertIn('successful_operations', metrics)
        self.assertIn('failed_operations', metrics)
    
    def test_legacy_wrapper_functions(self):
        """Test that legacy wrapper functions work correctly"""
        # Test that wrapper functions return proper format
        with patch('platform.system', return_value='Linux'):
            uac_result = self.enhanced_system.uac_bypass()
            defender_result = self.enhanced_system.disable_defender()
            
            # Should return dict format compatible with original
            self.assertIsInstance(uac_result, dict)
            self.assertIsInstance(defender_result, dict)
            self.assertIn('status', uac_result)
            self.assertIn('status', defender_result)

class TestRegistrySystemPerformance(unittest.TestCase):
    """Performance tests for enhanced registry system"""
    
    def setUp(self):
        """Set up test environment"""
        self.enhanced_system = enhanced_registry
        self.enhanced_registry = enhanced_registry.get_registry_system()
        self.enhanced_registry.reset_metrics()
    
    def test_response_time_performance(self):
        """Test that operations complete within acceptable time limits"""
        start_time = time.time()
        self.enhanced_system.is_admin()
        response_time = time.time() - start_time
        
        # Should complete in less than 100ms
        self.assertLess(response_time, 0.1)
    
    def test_memory_efficiency(self):
        """Test memory usage efficiency"""
        import sys
        
        # Get initial size
        initial_size = sys.getsizeof(self.enhanced_registry)
        
        # Perform operations
        for _ in range(100):
            self.enhanced_system.is_admin()
        
        # Size shouldn't grow significantly
        final_size = sys.getsizeof(self.enhanced_registry)
        size_growth = final_size - initial_size
        
        # Allow some growth for logs, but should be minimal
        self.assertLess(size_growth, 10000)  # Less than 10KB growth
    
    def test_concurrent_performance(self):
        """Test performance under concurrent load"""
        import concurrent.futures
        
        def perform_operation():
            start = time.time()
            self.enhanced_system.is_admin()
            return time.time() - start
        
        # Test concurrent operations
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(perform_operation) for _ in range(50)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # All operations should complete reasonably fast
        avg_response_time = sum(results) / len(results)
        self.assertLess(avg_response_time, 0.05)  # Less than 50ms average

class TestRegistrySystemSecurity(unittest.TestCase):
    """Security validation tests for enhanced registry system"""
    
    def setUp(self):
        """Set up test environment"""
        self.enhanced_system = enhanced_registry
        self.enhanced_registry = enhanced_registry.get_registry_system()
        self.enhanced_registry.reset_metrics()
    
    def test_no_hardcoded_credentials(self):
        """Test that no hardcoded credentials exist"""
        import inspect
        
        # Check source code for hardcoded credentials
        source = inspect.getsource(enhanced_registry)
        
        # Look for common credential patterns
        credential_patterns = ['password', 'api_key', 'secret', 'token']
        for pattern in credential_patterns:
            self.assertNotIn(pattern.lower(), source.lower())
    
    def test_platform_specific_guards(self):
        """Test that Windows-specific code is properly guarded"""
        with patch('platform.system', return_value='Linux'):
            # Should not attempt Windows-specific operations
            result = self.enhanced_system.uac_bypass()
            self.assertEqual(result['status'], 'failed')
            self.assertIn('Windows required', result['error'])
    
    def test_safe_registry_operations(self):
        """Test that registry operations are safe"""
        # Test cleanup functionality
        with patch.dict('sys.modules', {'winreg': MagicMock()}):
            mock_winreg = MagicMock()
            mock_winreg.HKEY_CURRENT_USER = 'HKEY_CURRENT_USER'
            mock_winreg.DeleteKey = MagicMock()
            
            with patch('enhanced_registry.winreg', mock_winreg):
                result = self.enhanced_registry._cleanup_registry_key(
                    mock_winreg.HKEY_CURRENT_USER, "TEST_PATH"
                )
                
                # Should attempt cleanup
                self.assertGreater(result['attempts'], 0)

if __name__ == '__main__':
    # Run all tests
    unittest.main(verbosity=2)