# -*- mode: python ; coding: utf-8 -*-

import os
import shutil
import importlib
from PyInstaller.utils.hooks import collect_dynamic_libs, collect_data_files

# 1) 收集运行时所需的动态库（onnxruntime 等）
_binaries = []
try:
    _binaries += collect_dynamic_libs('onnxruntime')
except Exception:
    pass
try:
    _binaries += collect_dynamic_libs('rapidocr_onnxruntime')
except Exception:
    pass

# 2) 收集 RapidOCR 包中的数据文件（特别是 config.yaml）
_datas = []
try:
    _datas += collect_data_files('rapidocr_onnxruntime')
except Exception:
    pass
# 显式添加 rapidocr_onnxruntime/config.yaml（某些版本下自动收集可能遗漏）
try:
    rapidocr_pkg = importlib.import_module('rapidocr_onnxruntime')
    rapidocr_dir = os.path.dirname(rapidocr_pkg.__file__)
    cfg = os.path.join(rapidocr_dir, 'config.yaml')
    if os.path.exists(cfg):
        _datas.append((cfg, 'rapidocr_onnxruntime'))
except Exception:
    pass

# 3) 打包项目根目录的 rapidocr_models / rapidocr_modelsa 全部文件
for folder in ('rapidocr_models', 'rapidocr_modelsa'):
    try:
        if os.path.isdir(folder):
            for _root, _dirs, _files in os.walk(folder):
                for _f in _files:
                    _src = os.path.join(_root, _f)
                    _rel = os.path.relpath(_src, folder)
                    _dst = os.path.join(folder, os.path.dirname(_rel))
                    _datas.append((_src, _dst))
    except Exception:
        pass

# 4) 额外隐藏导入（此处保持为空，按需补充）
_hiddenimports = []

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=_binaries,
    datas=_datas,
    hiddenimports=_hiddenimports,
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
    icon=['logo.ico'],
)

# 5) 构建后将资源目录复制到 dist，便于按 exe 相对路径加载
try:
    _base = os.path.abspath(os.getcwd())
    _dist = os.path.join(_base, 'dist')
    os.makedirs(_dist, exist_ok=True)
    for folder in ('rapidocr_models', 'rapidocr_modelsa'):
        _src = os.path.join(_base, folder)
        _dst = os.path.join(_dist, folder)
        if os.path.isdir(_src):
            if os.path.exists(_dst):
                shutil.rmtree(_dst)
            shutil.copytree(_src, _dst)
            print(f"[spec] info: copied {folder} to dist successfully")
except Exception as _e:
    print(f"[spec] warning: copy resources failed: {_e}")
