# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec file for Starbase HOTAS Bridge
# Run: pyinstaller StarbaseHOTASBridge.spec

import os
from pathlib import Path

block_cipher = None

a = Analysis(
    ['starbase_hotas.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('hotas_profiles', 'hotas_profiles'),  # bundle default profiles
    ],
    hiddenimports=[
        'pygame',
        'pynput',
        'pynput.keyboard',
        'pynput.mouse',
        'PyQt6',
        'PyQt6.QtWidgets',
        'PyQt6.QtCore',
        'PyQt6.QtGui',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'unittest', 'email', 'html', 'http', 'xml'],
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
    name='StarbaseHOTASBridge',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,          # no black console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico' if os.path.exists('icon.ico') else None,
)
