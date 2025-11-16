# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files
import os
try:
    import rapidocr_onnxruntime as _rapid_pkg
except Exception:
    _rapid_pkg = None


rapidocr_data = collect_data_files('rapidocr_onnxruntime')
if _rapid_pkg is not None:
    _cfg = os.path.join(os.path.dirname(_rapid_pkg.__file__), 'config.yaml')
    if os.path.exists(_cfg):
        rapidocr_data.append((_cfg, 'rapidocr_onnxruntime/config.yaml'))

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=rapidocr_data,
    hiddenimports=['rapidocr_onnxruntime'],
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
    name='main',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
