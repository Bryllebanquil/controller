# -*- mode: python ; coding: utf-8 -*-
# client.spec - Silent/Windowless PyInstaller spec for client.py

import os
import sys
from PyInstaller.building.api import COLLECT, EXE, PYZ
from PyInstaller.building.build_main import Analysis
import PyInstaller.config

# =============================================================================
# CONFIGURATION
# =============================================================================

block_cipher = None

# Platform-specific adjustments
is_windows = sys.platform == 'win32'
is_linux = sys.platform.startswith('linux')
is_macos = sys.platform == 'darwin'

# =============================================================================
# ANALYSIS - Main analysis for all imports
# =============================================================================

# Additional search paths
additional_paths = []

# Main analysis with simplified hidden imports (removed duplicates)
a = Analysis(
    ['client.py'],
    pathex=additional_paths,
    binaries=[],
    datas=[],
    hiddenimports=[
        # Core imports
        'socketio', 'engineio', 'eventlet', 'eventlet.green',
        'aiohttp', 'aiofiles', 'asyncio', 'websockets',
        'requests', 'urllib3', 'certifi', 'charset_normalizer', 'idna',
        
        # Screen/Media
        'mss', 'cv2', 'numpy', 'pygame', 'PIL', 'PIL.Image',
        
        # Audio
        'speech_recognition',
        'pyaudio' if is_windows else '',
        'sounddevice' if not is_windows else '',
        
        # Input
        'pynput', 'keyboard', 'pyautogui',
        
        # System
        'psutil', 'py_cpuinfo',
        'win32api' if is_windows else '',
        'win32con' if is_windows else '',
        'win32process' if is_windows else '',
        'win32security' if is_windows else '',
        'win32event' if is_windows else '',
        'win32clipboard' if is_windows else '',
        'pythoncom' if is_windows else '',
        'pywintypes' if is_windows else '',
        
        # WebRTC
        'aiortc', 'av',
        
        # Compression
        'msgpack', 'lz4', 'zstandard', 'xxhash',
        'uvloop' if not is_windows else '',
        
        # Security
        'cryptography',
        
        # Utilities
        'pyotp', 'qrcode',
        
        # Built-in modules often missed
        'email.mime.text', 'email.mime.multipart',
        'winreg' if is_windows else '',
        'ctypes.wintypes' if is_windows else '',
        
        # Cython
        'Cython',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=['runtime_hook.py'],  # Add runtime hook for silent operation
    excludes=[
        # Remove unnecessary packages
        'tkinter', 'tcl', 'tk', '_tkinter', 'turtle',
        'matplotlib', 'scipy', 'pandas', 'scikit-learn',
        'test', 'tests', 'unittest', 'pytest',
    ],
    noarchive=False,
    optimize=1,  # Optimize bytecode
    upx=False,  # Disable UPX for stability
)

# =============================================================================
# ADDITIONAL BINARIES AND DATA
# =============================================================================

# Add Windows DLLs if needed
if is_windows:
    # Common Windows DLLs that might be required
    a.binaries += [
        # ('path/to/dll', '.'),
    ]
    
    # Add icon file for Windows executable
    a.datas += [
        # ('icon.ico', 'icon.ico', 'DATA'),
    ]

# =============================================================================
# RUNTIME HOOK FOR SILENT OPERATION
# =============================================================================

# Create runtime hook file
runtime_hook_content = '''
# runtime_hook.py
# Hook to suppress console and handle errors silently

import sys
import os
import traceback

def suppress_stdout_stderr():
    """Redirect stdout and stderr to null."""
    if hasattr(sys, 'frozen'):  # Running as compiled
        try:
            # Open null device
            null_device = open(os.devnull, 'w')
            sys.stdout = null_device
            sys.stderr = null_device
        except:
            pass

# Apply on import
suppress_stdout_stderr()

# Exception handler for silent error handling
def silent_exception_handler(exc_type, exc_value, exc_traceback):
    """Silently handle exceptions."""
    # You could log to file here if needed
    pass

# Install exception handler
sys.excepthook = silent_exception_handler
'''

# Write runtime hook file
with open('runtime_hook.py', 'w') as f:
    f.write(runtime_hook_content)

# =============================================================================
# CREATE PYZ
# =============================================================================

pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher
)

# =============================================================================
# CREATE SILENT EXECUTABLE (NO CONSOLE WINDOW)
# =============================================================================

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='ClientSilent',  # Output executable name
    debug=False,
    bootloader_ignore_signals=True,  # Handle signals gracefully
    strip=True,  # Strip symbols for smaller size
    upx=True,  # Enable compression (may cause issues with some DLLs)
    console=False,  # CRITICAL: NO CONSOLE WINDOW
    disable_windowed_traceback=True,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Optional: 'app.ico' for Windows
    version=None,  # Optional: 'version.txt'
    manifest=None,
    uac_admin=False,  # Don't request admin on launch
    uac_uiaccess=False,
    rt_manifest=None,
    aslr=True,  # ASLR for security
    dpiaware=True,  # DPI aware for modern displays
    sidebyside=False,
    binding_redirects=False,
    com_server=False,
    com_library=False,
    com_typelib=False,
    com_embedding=False,
    com_typelib_embedding=False,
    com_server_embedding=False,
    com_library_embedding=False,
    com_typelib_library=False,
    com_server_library=False,
    com_typelib_server=False,
    com_typelib_library_embedding=False,
    com_server_library_embedding=False,
    com_typelib_server_embedding=False,
)

# =============================================================================
# COLLECT FOR ONE-FILE MODE
# =============================================================================

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=True,
    upx=True,
    upx_exclude=[],  # Exclude specific files from UPX
    name='dist'  # Output directory
)