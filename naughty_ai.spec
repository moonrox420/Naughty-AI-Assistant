# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_submodules, collect_data_files

block_cipher = None

hidden_imports = [
    'uvicorn',
    'uvicorn.logging',
    'uvicorn.loops',
    'uvicorn.loops.auto',
    'uvicorn.protocols',
    'uvicorn.protocols.http',
    'uvicorn.protocols.http.auto',
    'uvicorn.protocols.http.h11_impl',
    'uvicorn.protocols.websockets',
    'uvicorn.protocols.websockets.auto',
    'uvicorn.protocols.websockets.websockets_impl',
    'uvicorn.lifespan',
    'uvicorn.lifespan.on',
    'websockets',
    'websockets.legacy',
    'websockets.legacy.server',
    'aiosqlite',
    'sqlite3',
    'httpx',
    'pydantic',
    'pydantic_settings',
    'fastapi',
    'starlette',
    'starlette.staticfiles',
    'starlette.routing',
    'starlette.middleware',
    'starlette.middleware.cors',
    'starlette.responses',
    'multipart',
    'src.config',
    'src.main',
    'src.api.routes',
    'src.api.websocket',
    'src.cards.parser',
    'src.cards.presets',
    'src.db.database',
    'src.db.repository',
    'src.image.client',
    'src.image.launcher',
    'src.image.gpu_lock',
    'src.llm.client',
    'src.llm.detector',
    'src.llm.models',
    'src.memory.extractor',
    'src.memory.manager',
]

datas = [
    ('static', 'static'),
    ('src/db/schema.sql', 'src/db'),
]

a = Analysis(
    ['run.py'],
    pathex=['.'],
    binaries=[],
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'scipy', 'numpy'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='NaughtyAI',
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
