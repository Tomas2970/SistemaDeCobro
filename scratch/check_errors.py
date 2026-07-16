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

print("=== 1. TEST SESION_ACTIVA ===")
# Limpiar token de sofia
backend.cerrar_sesion_usuario(5)
# Primer login
r1 = backend.verificar_contraseña("sofia", "sofia123")
print(f"Primer login: {r1}")
# Segundo login SIN cerrar sesión
r2 = backend.verificar_contraseña("sofia", "sofia123")
print(f"Segundo login (debería ser SESION_ACTIVA): {r2}")
# Verificar token en BD
conn = DB.conectar()
cur = conn.cursor(dictionary=True)
cur.execute("SELECT id_usuario, nombre, token_sesion, token_timestamp FROM Usuario WHERE nombre='sofia'")
row = cur.fetchone()
print(f"Estado en BD: {row}")
cur.close(); conn.close()
# Limpiar
backend.cerrar_sesion_usuario(5)

print("\n=== 2. TEST FORMATO ITEMS VENTA ===")
# Ver qué formato espera DB.registrar_venta_completa
import inspect
try:
    sig = inspect.signature(DB.registrar_venta_completa)
    print(f"Firma DB.registrar_venta_completa: {sig}")
except Exception as e:
    print(f"Error obteniendo firma: {e}")

# Ver código fuente de la función
import ast
db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'app', 'database', 'DB.py')
with open(db_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Buscar la función registrar_venta_completa
idx = content.find("def registrar_venta_completa(")
if idx >= 0:
    # Obtener las primeras 50 líneas de la función
    lines = content[idx:idx+3000].split('\n')[:50]
    print("Primeras líneas de registrar_venta_completa:")
    for i, line in enumerate(lines):
        print(f"  {i+1}: {line}")

print("\n=== 3. TEST ERROR 'id' EN PROVEEDORES ===")
# Inspeccionar registrar_compra_mixta
idx2 = content.find("def registrar_pago_proveedor(")
if idx2 >= 0:
    lines2 = content[idx2:idx2+2000].split('\n')[:40]
    print("Primeras líneas de registrar_pago_proveedor:")
    for i, line in enumerate(lines2):
        print(f"  {i+1}: {line}")
