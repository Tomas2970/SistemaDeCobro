# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_submodules

block_cipher = None

hidden = []
hidden += collect_submodules('bcrypt')   # asegura todo bcrypt
hidden += [
    '_cffi_backend',
    'PIL._tkinter_finder',
    # FRONTEND pantallas (importadas directa o indirectamente)
    'app.frontend.interfaz_menu_principal',
    'app.frontend.interfaz_venta',
    'app.frontend.interfaz_inventario',
    'app.frontend.interfaz_compra',
    # BACKEND
    'app.database.DB',
    'app.database.backend_adapter',
    'app.database.permisos',
    # TOOLS utilitarias
    'app.tools.seed_initial_data',
    'app.tools.logger_config',
    # Otros usados
    'mysql.connector',
    'dotenv',
    'tkinter',     # (hook de _tkinter incluye tcl/tk)
    'PIL',
]

a = Analysis(
    ['app/main.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        # Solo archivos de datos/recursos, NO .py
        ('app/frontend/Don atilio.png', 'app/frontend'),
        ('app/database/schema.sql', 'app/database'),
    ],
    hiddenimports=hidden,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    name='SistemaCobrosDonAtilio',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,   # GUI (sin consola)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='logo.ico',
)
