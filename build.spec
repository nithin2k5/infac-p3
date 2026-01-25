# -*- mode: python ; coding: utf-8 -*-
# Build Configuration for Cable Marker Detection System
# Works for both desktop and Raspberry Pi

import sys
import os

a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'customtkinter',
        'PIL._tkinter_finder',
        'cv2',
        'numpy',
        'requests',
        'roboflow',
        'RPi.GPIO',  # Raspberry Pi GPIO support
        'threading',
        'platform',
        'time',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'torch',  # Not used, exclude to reduce size
        'torchvision',  # Not used
        'ultralytics',  # Not used
        'scikit-image',  # Not used
        'matplotlib',  # Not used
        'pandas',  # Not used
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
    name='cable_marker_detector',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,  # Strip symbols for smaller size
    upx=False,  # UPX can cause issues on Raspberry Pi
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Keep console for debugging on Raspberry Pi
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)


