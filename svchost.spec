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
    'eventlet',
    'eventlet.hubs',
    'eventlet.green',
    'eventlet.queue',
    'eventlet.greenio',
    'eventlet.semaphore',
    'eventlet.timeout',

    # Screen capture & image processing
    'mss',
    'mss._linux',
    'mss._osx',
    'mss._windows',
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
]

# Collect extra data files that some libraries need
datas = []
datas += collect_data_files('cv2')             # OpenCV data / haarcascades / etc
datas += collect_data_files('mss')             # sometimes helps
datas += collect_data_files('dxcam')           # important for dxcam
datas += collect_data_files('numpy')           # .dll & .pyd files
datas += collect_data_files('pynput')

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
    [],
    exclude_binaries=True,
    name='client',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,                     # ← try False if UPX causes crashes
    upx_exclude=['vcruntime140.dll', 'msvcp140.dll', 'cv2*.pyd'],
    console=False,                # ← silent / no console
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,                    # ← add your .ico if you want
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='client',
)