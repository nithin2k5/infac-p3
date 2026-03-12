# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for macOS (Intel & Apple Silicon)
# Usage: pyinstaller mac.spec --clean

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
    excludes=[
        'RPi',
        'RPi.GPIO',
        'rpi_lgpio',
        'lgpio',
    ],
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
    upx=False,          # UPX can break things on macOS
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,      # No terminal window on macOS
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,   # None = native arch; use 'universal2' for fat binary
    codesign_identity=None,
    entitlements_file=None,
)

# macOS app bundle
app = BUNDLE(
    exe,
    name='CableMarkerDetector.app',
    icon=None,
    bundle_identifier='com.cablemarker.detector',
    info_plist={
        'NSCameraUsageDescription': 'Camera access required for live cable marker detection.',
        'NSHighResolutionCapable': True,
    },
)
