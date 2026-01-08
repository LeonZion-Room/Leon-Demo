# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_data_files
import os

# 添加必要的数据文件
datas = [
    ('ui_palette.json', '.'),
    ('ui_style.py', '.'),
    ('ui_style_nb.py', '.'),
    ('logo.ico', '.'),
]

# 添加所有Python模块文件
python_files = ['fc.py', 'img2pdf.py', 'pdf2docx.py', 'pdf2imagepdf.py', 'pdf2images.py', 'pdf2oneimage.py', 'pdf_merge.py', 'pdf_shrink.py', 'pdf_split.py']
for file in python_files:
    datas.append((file, '.'))

# 移除rapidocr相关配置
a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[],  # 移除rapidocr_onnxruntime
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
    console=False,  # 设置为窗口应用程序，不显示控制台
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['logo.ico'],
    onefile=True,  # 启用单文件打包
)