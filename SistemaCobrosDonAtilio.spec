# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['app\\main.py'],
    pathex=[],
    binaries=[],
    datas=[('app', 'app')],
    hiddenimports=['app.frontend.interfaz_gestion_proveedores', 'app.frontend.interfaz_crear_proveedor', 'app.frontend.interfaz_asignar_productos', 'app.frontend.interfaz_categorias', 'app.frontend.interfaz_gestion_usuarios', 'app.frontend.interfaz_crear_usuario', 'app.frontend.interfaz_gestion_clientes', 'app.frontend.interfaz_crear_cliente', 'app.frontend.interfaz_inventario', 'app.frontend.interfaz_productos', 'app.frontend.interfaz_venta', 'app.frontend.interfaz_reportes', 'app.frontend.interfaz_cuenta_corriente', 'app.frontend.interfaz_compra', 'app.frontend.interfaz_historiales', 'mysql.connector.plugins.caching_sha2_password', 'bcrypt', 'mysql.connector', 'dotenv'],
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
    name='SistemaCobrosDonAtilio',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['logo.ico'],
)
