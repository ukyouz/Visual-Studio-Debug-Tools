# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['guiBinView.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('view/images/*.ico', 'view/images/'),
        ('langs/*.qm', 'langs/'),
        ('scripts', 'scripts/'),
        ('libs/*.so', 'libs/'),
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
    name='BinViewer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='view/images/dsquery_153.ico',
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='BinViewer',
)
