#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de diagnóstico para encontrar el problema con impresora.py
Ejecuta este archivo desde donde ejecutas normalmente tu app
"""

import os
import sys

print("=" * 60)
print("DIAGNÓSTICO DEL SISTEMA")
print("=" * 60)

# 1. ¿Desde dónde se ejecuta?
print("\n1. DIRECTORIO ACTUAL (desde donde ejecutas):")
print(f"   {os.getcwd()}")

# 2. ¿Dónde está este script?
script_location = os.path.abspath(__file__)
script_dir = os.path.dirname(script_location)
print("\n2. UBICACIÓN DE ESTE SCRIPT:")
print(f"   {script_location}")
print(f"   Directorio: {script_dir}")

# 3. ¿Qué contiene el directorio actual?
print("\n3. ARCHIVOS EN EL DIRECTORIO ACTUAL:")
try:
    archivos = os.listdir(os.getcwd())
    for archivo in sorted(archivos):
        tipo = "📁" if os.path.isdir(archivo) else "📄"
        print(f"   {tipo} {archivo}")
except Exception as e:
    print(f"   ERROR: {e}")

# 4. ¿Existe la carpeta 'app'?
print("\n4. ¿EXISTE LA CARPETA 'app'?")
app_exists = os.path.exists("app")
print(f"   {app_exists}")
if app_exists:
    print("\n   Contenido de 'app/':")
    try:
        for archivo in sorted(os.listdir("app")):
            tipo = "📁" if os.path.isdir(os.path.join("app", archivo)) else "📄"
            print(f"      {tipo} {archivo}")
    except Exception as e:
        print(f"      ERROR: {e}")

# 5. ¿Existe app/impresora.py?
print("\n5. ¿EXISTE app/impresora.py?")
impresora_path = os.path.join("app", "impresora.py")
print(f"   Ruta buscada: {os.path.abspath(impresora_path)}")
print(f"   ¿Existe?: {os.path.exists(impresora_path)}")

# 6. Buscar impresora.py en todo el proyecto
print("\n6. BUSCANDO 'impresora.py' EN TODO EL PROYECTO:")
found_files = []
for root, dirs, files in os.walk("."):
    for file in files:
        if "impresora" in file.lower():
            full_path = os.path.join(root, file)
            found_files.append(full_path)
            print(f"   ✓ Encontrado: {full_path}")

if not found_files:
    print("   ✗ No se encontró ningún archivo 'impresora.py'")

# 7. sys.path actual
print("\n7. RUTAS EN sys.path (donde Python busca módulos):")
for i, path in enumerate(sys.path, 1):
    print(f"   {i}. {path}")

# 8. Intentar importar
print("\n8. INTENTANDO IMPORTAR 'impresora':")
try:
    import impresora
    print("   ✓ ÉXITO: impresora importado correctamente")
    print(f"   Ubicación: {impresora.__file__}")
except ImportError as e:
    print(f"   ✗ ERROR: {e}")

print("\n9. INTENTANDO IMPORTAR 'app.impresora':")
try:
    from app import impresora
    print("   ✓ ÉXITO: app.impresora importado correctamente")
    print(f"   Ubicación: {impresora.__file__}")
except ImportError as e:
    print(f"   ✗ ERROR: {e}")

print("\n" + "=" * 60)
print("FIN DEL DIAGNÓSTICO")
print("=" * 60)
print("\nCopia TODA esta salida y envíamela para ayudarte.")