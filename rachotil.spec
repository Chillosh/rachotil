# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['src\\rachotil\\main.py'],
    pathex=['src'],
    binaries=[],
    datas=[('src/rachotil/frontend/components/styles', 'rachotil/frontend/components/styles'), ('src/rachotil/backend/storage/dashboard_config.json', 'rachotil/backend/storage'), ('src/rachotil/backend/storage/default_blocks.json', 'rachotil/backend/storage'), ('src/rachotil/backend/storage/keybinds_config.json', 'rachotil/backend/storage'), ('src/rachotil/backend/storage/management_sections.json', 'rachotil/backend/storage')],
    hiddenimports=[],
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
    name='rachotil',
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
    icon=['src\\rachotil\\frontend\\icon.ico'],
)
