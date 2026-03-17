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
# WARNING: collect_submodules('ultralytics') crashes on Raspberry Pi because the
# isolated subprocess it spawns imports torch, exhausting limited RAM.
# Instead, list the ultralytics submodules that are actually used by the app.
hiddenimports += [
    'ultralytics.models',
    'ultralytics.models.yolo',
    'ultralytics.models.yolo.detect',
    'ultralytics.models.yolo.detect.predict',
    'ultralytics.models.yolo.detect.train',
    'ultralytics.models.yolo.detect.val',
    'ultralytics.engine',
    'ultralytics.engine.model',
    'ultralytics.engine.predictor',
    'ultralytics.engine.results',
    'ultralytics.nn',
    'ultralytics.nn.modules',
    'ultralytics.nn.modules.block',
    'ultralytics.nn.modules.conv',
    'ultralytics.nn.modules.head',
    'ultralytics.nn.tasks',
    'ultralytics.utils',
    'ultralytics.utils.checks',
    'ultralytics.utils.downloads',
    'ultralytics.utils.files',
    'ultralytics.utils.ops',
    'ultralytics.utils.plotting',
    'ultralytics.utils.torch_utils',
    'ultralytics.data',
    'ultralytics.data.augment',
    'ultralytics.data.utils',
    'ultralytics.cfg',
]

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
