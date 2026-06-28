# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller 打包配置。

打包方式：onedir（一个文件夹，启动快）。
引擎文件 engine/ 会被原样复制到 exe 同级目录，由 engine_controller 在运行时定位。
"""

block_cipher = None

a = Analysis(
    ['main_visual.py'],
    pathex=[],
    binaries=[],
    # 将 engine 目录整体打包到输出根目录下的 engine/
    datas=[('engine', 'engine')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='象棋助手',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,  # GUI 程序，不显示控制台黑窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='象棋助手',
)
