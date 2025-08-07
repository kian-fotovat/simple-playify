# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

binaries = [
    ('bin/ffmpeg.exe', '.'),
    ('bin/libopus-0.x64.dll', '.')
]


datas = [
    ('assets', 'assets') 
]

hiddenimports = [
    'playify_bot',      
    'pystray._win32',   
    'PIL.Image'         
]


a = Analysis(
    ['app.py'], 
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
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
    name='Playify',
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
    icon='assets/images/playify.ico', 
)


coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Playify', 
)
