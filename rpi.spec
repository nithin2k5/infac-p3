# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for Raspberry Pi (Linux aarch64)
# Usage: pyinstaller rpi.spec --clean

import sys
import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# ── Collect customtkinter and ultralytics assets ──────────────────────────────
datas = []
datas += collect_data_files('customtkinter')
datas += collect_data_files('ultralytics')

# Bundle the YOLO weights file alongside the app
datas += [('weights-5.pt', '.')]

# ── Hidden imports ────────────────────────────────────────────────────────────
hiddenimports = [
    # GUI
    'customtkinter',
    'PIL._tkinter_finder',
    'PIL.Image',
    'PIL.ImageTk',
    # Vision / ML
    'cv2',
    'numpy',
    'ultralytics',
    'ultralytics.nn',
    'ultralytics.nn.modules',
    'ultralytics.utils',
    'ultralytics.utils.torch_utils',
    'torch',
    'torchvision',
    # GPIO (Raspberry Pi)
    'RPi',
    'RPi.GPIO',
    'rpi_lgpio',
    'lgpio',
    # stdlib
    'threading',
    'platform',
    'time',
    'concurrent.futures',
    'multiprocessing',
    'multiprocessing.pool',
    'queue',
    'hashlib',
]
hiddenimports += collect_submodules('ultralytics')

# ── Analysis ──────────────────────────────────────────────────────────────────
a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],        # Don't exclude ultralytics — the code uses it!
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
    name='cable_marker',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,          # UPX causes issues on Raspberry Pi ARM
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,       # Keep terminal visible on RPi for error messages
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
