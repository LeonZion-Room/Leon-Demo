# -*- mode: python ; coding: utf-8 -*-

import os
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# 获取当前虚拟环境路径
sys.path.append('/home/lz-studio/Desktop/Leon-Codings/Leon-Demo/Gradio-Demo/.venv/lib/python3.12/site-packages')

# 收集Gradio的所有数据文件和子模块
gradio_datas = collect_data_files('gradio')
gradio_hiddenimports = collect_submodules('gradio')

# 添加safehttpx和groovy的数据文件
safehttpx_version = os.path.join('/home/lz-studio/Desktop/Leon-Codings/Leon-Demo/Gradio-Demo/.venv/lib/python3.12/site-packages/safehttpx', 'version.txt')
groovy_version = os.path.join('/home/lz-studio/Desktop/Leon-Codings/Leon-Demo/Gradio-Demo/.venv/lib/python3.12/site-packages/groovy', 'version.txt')

# 合并所有数据文件
all_datas = gradio_datas + [
    (safehttpx_version, 'safehttpx'),
    (groovy_version, 'groovy')
]

# 合并所有隐藏导入
all_hiddenimports = gradio_hiddenimports + [
    'safehttpx',
    'groovy'
]

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=all_datas,
    hiddenimports=all_hiddenimports,
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
    name='gradio_demo',
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