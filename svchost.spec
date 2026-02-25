# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.win32.versioninfo import (VSVersionInfo, FixedFileInfo, StringFileInfo, StringTable, StringStruct, VarFileInfo, VarStruct)

ver = VSVersionInfo(
    ffi=FixedFileInfo(
        filevers=(1, 0, 0, 0),
        prodvers=(1, 0, 0, 0),
        mask=0x3f,
        flags=0x0,
        OS=0x40004,
        fileType=0x1,
        subtype=0x0,
        date=(0, 0)
    ),
    kids=[
        StringFileInfo([
            StringTable(
                '040904B0',
                [
                    StringStruct('CompanyName', 'Neural Control Hub'),
                    StringStruct('FileDescription', 'Neural Control Hub Agent'),
                    StringStruct('FileVersion', '1.0.0.0'),
                    StringStruct('InternalName', 'NeuralAgent.exe'),
                    StringStruct('OriginalFilename', 'NeuralAgent.exe'),
                    StringStruct('ProductName', 'Neural Control Hub'),
                    StringStruct('ProductVersion', '1.0.0.0'),
                ]
            )
        ]),
        VarFileInfo([VarStruct('Translation', [1033, 1200])])
    ]
)

a = Analysis(
    ['c:\\Users\\Brylle\\controller\\client.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='NeuralAgent',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    version=ver,
    icon='svchost.ico',
)
