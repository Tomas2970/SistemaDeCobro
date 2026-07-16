#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import logging
logging.basicConfig(level=logging.CRITICAL)
from app.database import DB
from app.database.backend_adapter import BackendAdapter
backend = BackendAdapter()

print("=== USUARIOS EN LA BD ===")
usuarios = backend.obtener_usuarios_con_rol()
for u in usuarios:
    print(f"ID={u.get('id_usuario')}, nombre='{u.get('nombre')}', rol={u.get('rol_nombre')}, activo={u.get('activo')}")

print("\n=== TEST DE CREDENCIALES ===")
# Probar cada credencial demo
creds = [
    ("lucia", "lucia123"),
    ("martin", "martin123"),
    ("sofia", "sofia123"),
    ("supervisor", "super123"),
    ("admin", "admin123"),
]
for user, pwd in creds:
    # Primero limpiar token
    usr_obj = next((u for u in usuarios if u.get("nombre") == user), None)
    if usr_obj:
        backend.cerrar_sesion_usuario(usr_obj["id_usuario"])
    result = backend.verificar_contraseña(user, pwd)
    print(f"  {user}/{pwd} => {result}")

print("\n=== TEST VENDEDOR CREAR PRODUCTO ===")
# Ver qué hace exactamente el backend cuando id_usuario=2 (vendedor)
vendedor_id = next((u["id_usuario"] for u in usuarios if u.get("rol_nombre") == "vendedor" and u.get("activo")), None)
print(f"ID del vendedor activo: {vendedor_id}")

if vendedor_id:
    try:
        from app.database.backend_adapter import BackendAdapter
        backend2 = BackendAdapter()
        pid = backend2.crear_producto_completo(
            nombre="ProdTestVendedor",
            categoria_id=1,
            codigo_barras=None,
            precio=100.0,
            stock_inicial=10,
            stock_minimo=2,
            id_usuario=vendedor_id
        )
        print(f"  RESULTADO: ID={pid} (NO deberia haberse creado!)")
    except PermissionError as pe:
        print(f"  CORRECTO: PermissionError -> {pe}")
    except Exception as e:
        print(f"  OTRA EXCEPCION: {type(e).__name__}: {e}")

print("\n=== PROVEEDORES - ERROR 'id' ===")
proveedores = backend.obtener_proveedores()
print(f"Total proveedores: {len(proveedores)}")
if proveedores:
    print(f"Primer proveedor keys: {list(proveedores[0].keys())}")
    print(f"Primer proveedor: {proveedores[0]}")
