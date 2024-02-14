# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['guiVSdebugger.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('view/images/*.ico', 'view/images/'),
        ('langs/*.qm', 'langs/'),
        ('scripts', 'scripts/'),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='VSdebugger',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='view/images/vsjitdebugger_VSJITDEBUGGER.ICO.ico',
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='VSdebugger',
)
