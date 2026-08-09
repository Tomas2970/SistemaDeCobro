#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
=============================================================================
PRUEBA FUNCIONAL COMPLETA - Sistema Don Atilio
=============================================================================
Prueba cada caso de uso directamente via backend/DB.
No requiere interfaz gráfica.
Ejecución: python scratch/test_funcional_completo.py
=============================================================================
"""

import sys
import os
import json
import re
from datetime import date, datetime, timedelta
from typing import Optional

# ── Ajustar PYTHONPATH para importar el paquete app ──────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR   = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, ROOT_DIR)
os.chdir(ROOT_DIR)

# ── Inicializar logging silencioso ────────────────────────────────────────────
import logging
logging.basicConfig(level=logging.CRITICAL)   # Solo errores críticos en consola

# ── Contadores de resultados ──────────────────────────────────────────────────
OK      = 0
FALLA   = 0
PARCIAL = 0
RESULTADOS = []   # (estado, categoria, descripcion, detalle)

# ── Colores para consola ──────────────────────────────────────────────────────
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

def _log(estado: str, categoria: str, descripcion: str, detalle: str = ""):
    global OK, FALLA, PARCIAL
    RESULTADOS.append((estado, categoria, descripcion, detalle))
    if estado == "OK":
        OK += 1
        icono = f"{GREEN}✅ OK{RESET}"
    elif estado == "FALLA":
        FALLA += 1
        icono = f"{RED}❌ FALLA{RESET}"
    else:
        PARCIAL += 1
        icono = f"{YELLOW}⚠️  PARCIAL{RESET}"
    
    print(f"  {icono} [{categoria}] {descripcion}")
    if detalle:
        print(f"        {detalle}")

def seccion(titulo: str):
    print(f"\n{BOLD}{CYAN}{'='*70}{RESET}")
    print(f"{BOLD}{CYAN}  {titulo}{RESET}")
    print(f"{BOLD}{CYAN}{'='*70}{RESET}")

# ─────────────────────────────────────────────────────────────────────────────
# IMPORTAR MÓDULOS DEL SISTEMA
# ─────────────────────────────────────────────────────────────────────────────
try:
    from app.database import DB
    from app.database.backend_adapter import BackendAdapter
    from app.database.permisos import tiene_permiso, PERMISOS, DIAS_HISTORIAL_SUPERVISOR
    from app.frontend.validaciones_ui import ValidadoresVisuales, ValidadorFormulario
    backend = BackendAdapter()
    print(f"\n{GREEN}✓ Módulos importados correctamente{RESET}")
except Exception as e:
    print(f"\n{RED}✗ ERROR CRÍTICO: No se pudieron importar los módulos: {e}{RESET}")
    sys.exit(1)

# ─────────────────────────────────────────────────────────────────────────────
# VARIABLES DE ESTADO GLOBAL (IDs creados durante el test)
# ─────────────────────────────────────────────────────────────────────────────
state = {
    "usuario_vendedor": None,    # dict con id_usuario, nombre, id_rol, token_sesion
    "usuario_supervisor": None,
    "usuario_admin": None,
    "usuario_nuevo_id": None,    # ID del usuario de prueba creado
    "cliente_nuevo_id": None,
    "producto_nuevo_id": None,
    "proveedor_nuevo_id": None,
    "categoria_nueva_id": None,
    "caja_session_id": None,
    "id_venta_prueba": None,
    "id_compra_prueba": None,
    "stock_antes_venta": 0,
    "stock_antes_compra": 0,
}

# ═════════════════════════════════════════════════════════════════════════════
# SECCIÓN 1: AUTENTICACIÓN Y SESIONES
# ═════════════════════════════════════════════════════════════════════════════
seccion("1. AUTENTICACIÓN Y CONTROL DE SESIONES")

# 1.1 Login con contraseña incorrecta
try:
    resultado = backend.verificar_contraseña("lucia", "CONTRASEÑA_INCORRECTA_XYZ_123")
    if resultado is None:
        _log("OK", "Auth", "Login con contraseña incorrecta → rechazado correctamente (None)")
    elif isinstance(resultado, dict) and resultado.get("error") == "SESION_ACTIVA":
        _log("PARCIAL", "Auth", "Login con contraseña incorrecta → detectó sesión activa antes de validar contraseña")
    else:
        _log("FALLA", "Auth", "Login con contraseña incorrecta", f"Debería retornar None, retornó: {resultado}")
except Exception as e:
    _log("FALLA", "Auth", "Login con contraseña incorrecta", f"Excepción: {e}")

# 1.2 Login con usuario inexistente
try:
    resultado = backend.verificar_contraseña("usuario_que_no_existe_xyz99", "cualquierpass")
    if resultado is None:
        _log("OK", "Auth", "Login con usuario inexistente → rechazado correctamente (None)")
    else:
        _log("FALLA", "Auth", "Login con usuario inexistente", f"Debería retornar None, retornó: {resultado}")
except Exception as e:
    _log("FALLA", "Auth", "Login con usuario inexistente", f"Excepción: {e}")

# 1.3 Login correcto como Vendedor
# NOTA: 'lucia' es SUPERVISOR. Los vendedores son: sofia, martin, cajero_demo_1, cajero_demo_2
# Buscar el primer usuario activo con rol vendedor
try:
    usuarios = backend.obtener_usuarios_con_rol()
    # Limpiar tokens de todos los vendedores para evitar SESION_ACTIVA
    vendedores_activos = [u for u in usuarios if u.get("rol_nombre") == "vendedor" and u.get("activo")]
    for v in vendedores_activos:
        backend.cerrar_sesion_usuario(v["id_usuario"])
    
    # sofia tiene contraseña conocida: sofia123
    resultado = backend.verificar_contraseña("sofia", "sofia123")
    if resultado and "id_usuario" in resultado and "error" not in resultado:
        state["usuario_vendedor"] = resultado
        _log("OK", "Auth", f"Login correcto como Vendedor (sofia) → ID={resultado['id_usuario']}, Rol={resultado['id_rol']}")
    else:
        # Intentar con martin
        resultado = backend.verificar_contraseña("martin", "martin123")
        if resultado and "id_usuario" in resultado and "error" not in resultado:
            state["usuario_vendedor"] = resultado
            _log("OK", "Auth", f"Login correcto como Vendedor (martin) → ID={resultado['id_usuario']}, Rol={resultado['id_rol']}")
        else:
            _log("FALLA", "Auth", "Login correcto como Vendedor", f"sofia: None, martin: {resultado} (credenciales incorrectas o usuarios inexistentes)")
except Exception as e:
    _log("FALLA", "Auth", "Login correcto como Vendedor", f"Excepción: {e}")

# 1.4 Segunda instancia con mismo usuario (debe retornar SESION_ACTIVA)
try:
    if state["usuario_vendedor"]:
        nombre_vend = state["usuario_vendedor"]["nombre"]
        pwd_vend = "sofia123" if nombre_vend == "sofia" else "martin123"
        resultado2 = backend.verificar_contraseña(nombre_vend, pwd_vend)
        if isinstance(resultado2, dict) and resultado2.get("error") == "SESION_ACTIVA":
            _log("OK", "Auth", "Segunda instancia mismo usuario → bloqueada con SESION_ACTIVA ✓")
        elif Search_None := (resultado2 is None):
            _log("FALLA", "Auth", "Segunda instancia mismo usuario", 
                 "Debería retornar {'error':'SESION_ACTIVA'} pero retornó None")
        else:
            _log("FALLA", "Auth", "Segunda instancia mismo usuario", f"Resultado inesperado: {resultado2}")
    else:
        _log("FALLA", "Auth", "Segunda instancia mismo usuario", "No hay sesión previa para probar (test anterior falló)")
except Exception as e:
    _log("FALLA", "Auth", "Segunda instancia mismo usuario", f"Excepción: {e}")

# 1.5 Login correcto como Supervisor
# NOTA: los supervisores son lucia (lucia123), supervisor (super123), supervisor_demo
try:
    usuarios = backend.obtener_usuarios_con_rol()
    supervisores_activos = [u for u in usuarios if u.get("rol_nombre") == "supervisor" and u.get("activo")]
    for sv in supervisores_activos:
        backend.cerrar_sesion_usuario(sv["id_usuario"])
    
    # Credenciales conocidas: lucia/lucia123
    resultado = backend.verificar_contraseña("lucia", "lucia123")
    if resultado and "id_usuario" in resultado and "error" not in resultado:
        state["usuario_supervisor"] = resultado
        _log("OK", "Auth", f"Login correcto como Supervisor (lucia) → ID={resultado['id_usuario']}")
    else:
        # Intentar supervisor/super123
        resultado = backend.verificar_contraseña("supervisor", "super123")
        if resultado and "id_usuario" in resultado and "error" not in resultado:
            state["usuario_supervisor"] = resultado
            _log("OK", "Auth", f"Login correcto como Supervisor (supervisor) → ID={resultado['id_usuario']}")
        else:
            _log("FALLA", "Auth", "Login correcto como Supervisor", f"lucia: None, supervisor: {resultado}")
except Exception as e:
    _log("FALLA", "Auth", "Login correcto como Supervisor", f"Excepción: {e}")

# 1.6 Login correcto como Admin
try:
    usuarios = backend.obtener_usuarios_con_rol()
    admin_user = next((u for u in usuarios if u.get("rol_nombre") == "admin"), None)
    if admin_user:
        backend.cerrar_sesion_usuario(admin_user["id_usuario"])
        resultado = backend.verificar_contraseña(admin_user["nombre"], "admin123")
        if resultado and "id_usuario" in resultado and "error" not in resultado:
            state["usuario_admin"] = resultado
            _log("OK", "Auth", f"Login correcto como Admin ({admin_user['nombre']}) → ID={resultado['id_usuario']}")
        else:
            _log("FALLA", "Auth", "Login correcto como Admin", f"Resultado: {resultado}")
    else:
        _log("FALLA", "Auth", "Login correcto como Admin", "No se encontró ningún usuario admin en la BD")
except Exception as e:
    _log("FALLA", "Auth", "Login correcto como Admin", f"Excepción: {e}")

# 1.7 Cierre de sesión → token queda NULL
try:
    if state["usuario_vendedor"]:
        uid = state["usuario_vendedor"]["id_usuario"]
        resultado = backend.cerrar_sesion_usuario(uid)
        # Verificar directamente en BD que el token es NULL
        conn = DB.conectar()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT token_sesion FROM Usuario WHERE id_usuario=%s", (uid,))
        row = cur.fetchone()
        cur.close(); conn.close()
        if row and row.get("token_sesion") is None:
            _log("OK", "Auth", "Cierre de sesión → token_sesion=NULL en BD ✓")
        else:
            _log("FALLA", "Auth", "Cierre de sesión", f"Token no es NULL: {row}")
    else:
        _log("FALLA", "Auth", "Cierre de sesión", "No hay sesión activa para cerrar")
except Exception as e:
    _log("FALLA", "Auth", "Cierre de sesión → verificar token NULL", f"Excepción: {e}")

# ═════════════════════════════════════════════════════════════════════════════
# SECCIÓN 2: PERMISOS POR ROL
# ═════════════════════════════════════════════════════════════════════════════
seccion("2. SISTEMA DE PERMISOS POR ROL")

usuario_vendedor_dict = {"id_rol": 2, "nombre": "lucia"}
usuario_supervisor_dict = {"id_rol": 3, "nombre": "supervisor"}
usuario_admin_dict = {"id_rol": 1, "nombre": "admin"}

permisos_tests = [
    # (usuario_dict, permiso, esperado, descripcion)
    (usuario_vendedor_dict,   "realizar_ventas",       True,  "Vendedor puede realizar_ventas"),
    (usuario_vendedor_dict,   "crear_clientes",        False, "Vendedor NO puede crear_clientes"),
    (usuario_vendedor_dict,   "editar_clientes",       False, "Vendedor NO puede editar_clientes"),
    (usuario_vendedor_dict,   "eliminar_clientes",     False, "Vendedor NO puede eliminar_clientes"),
    (usuario_vendedor_dict,   "eliminar_productos",    False, "Vendedor NO puede eliminar_productos"),
    (usuario_vendedor_dict,   "ajustar_inventario_manual", False, "Vendedor NO puede ajustar_inventario_manual"),
    (usuario_vendedor_dict,   "cancelar_ventas",       False, "Vendedor NO puede cancelar_ventas"),
    (usuario_vendedor_dict,   "abrir_caja",            True,  "Vendedor puede abrir_caja"),
    (usuario_vendedor_dict,   "cerrar_caja",           True,  "Vendedor puede cerrar_caja"),
    (usuario_vendedor_dict,   "ver_caja_todos",        False, "Vendedor NO puede ver_caja_todos"),
    (usuario_supervisor_dict, "crear_clientes",        True,  "Supervisor puede crear_clientes"),
    (usuario_supervisor_dict, "editar_clientes",       True,  "Supervisor puede editar_clientes"),
    (usuario_supervisor_dict, "eliminar_clientes",     False, "Supervisor NO puede eliminar_clientes"),
    (usuario_supervisor_dict, "eliminar_productos",    False, "Supervisor NO puede eliminar_productos"),
    (usuario_supervisor_dict, "cerrar_caja_ajena",     True,  "Supervisor puede cerrar_caja_ajena"),
    (usuario_supervisor_dict, "ver_usuarios",          False, "Supervisor NO puede ver_usuarios"),
    (usuario_admin_dict,      "eliminar_clientes",     True,  "Admin puede eliminar_clientes"),
    (usuario_admin_dict,      "eliminar_productos",    True,  "Admin puede eliminar_productos"),
    (usuario_admin_dict,      "ver_usuarios",          True,  "Admin puede ver_usuarios"),
    (usuario_admin_dict,      "ingreso_extraordinario",True,  "Admin puede ingreso_extraordinario"),
    (usuario_admin_dict,      "ver_auditoria",         True,  "Admin puede ver_auditoria"),
    (usuario_admin_dict,      "broadcast_mensaje",     True,  "Admin puede broadcast_mensaje"),
]

for usr, perm, esperado, desc in permisos_tests:
    try:
        resultado = tiene_permiso(usr, perm)
        if resultado == esperado:
            _log("OK", "Permisos", desc)
        else:
            _log("FALLA", "Permisos", desc, f"Esperado={esperado}, Obtenido={resultado}")
    except Exception as e:
        _log("FALLA", "Permisos", desc, f"Excepción: {e}")

# ═════════════════════════════════════════════════════════════════════════════
# SECCIÓN 3: VALIDACIONES DE FORMULARIOS (UI LAYER)
# ═════════════════════════════════════════════════════════════════════════════
seccion("3. VALIDACIONES DE FORMULARIOS")

vv = ValidadoresVisuales

validacion_tests = [
    # (metodo, input, esperado_valido, descripcion)
    (vv.validar_email, "usuario@ejemplo.com",   True,  "Email válido"),
    (vv.validar_email, "no-es-un-email",        False, "Email sin @ → inválido"),
    (vv.validar_email, "sin@dominio",           False, "Email sin .com → inválido"),
    (vv.validar_email, "",                      True,  "Email vacío → opcional (válido)"),
    (vv.validar_nombre, "Juan",                 True,  "Nombre válido (4 chars)"),
    (vv.validar_nombre, "AB",                   False, "Nombre corto (2 chars) → inválido"),
    (vv.validar_nombre, "123",                  False, "Nombre empieza con número → inválido"),
    (vv.validar_dni,   "12345678",              True,  "DNI válido (8 dígitos)"),
    (vv.validar_dni,   "123456",                False, "DNI corto (6 dígitos) → inválido"),
    (vv.validar_dni,   "123456789",             False, "DNI largo (9 dígitos) → inválido"),
    (vv.validar_dni,   "",                      False, "DNI vacío → obligatorio → inválido"),
    (vv.validar_cuit,  "20123456789",           True,  "CUIT válido (11 dígitos)"),
    (vv.validar_cuit,  "2012345678",            False, "CUIT corto (10 dígitos) → inválido"),
    (vv.validar_cuit,  "",                      True,  "CUIT vacío → opcional (válido)"),
    (vv.validar_telefono, "3513456789",         True,  "Teléfono válido (10 dígitos)"),
    (vv.validar_telefono, "351345678",          False, "Teléfono corto (9 dígitos) → inválido"),
    (vv.validar_telefono, "",                   True,  "Teléfono vacío → opcional (válido)"),
    (vv.validar_monto, "100.50",               True,  "Monto válido"),
    (vv.validar_monto, "0",                    False, "Monto cero → inválido"),
    (vv.validar_monto, "-50",                  False, "Monto negativo → inválido"),
    (vv.validar_monto, "",                     False, "Monto vacío → inválido"),
]

for metodo, inp, esperado, desc in validacion_tests:
    try:
        valido, msg = metodo(inp)
        if valido == esperado:
            _log("OK", "Validaciones", desc)
        else:
            _log("FALLA", "Validaciones", desc, f"Esperado válido={esperado}, Obtenido válido={valido}, Msg='{msg}'")
    except Exception as e:
        _log("FALLA", "Validaciones", desc, f"Excepción: {e}")

# ═════════════════════════════════════════════════════════════════════════════
# SECCIÓN 4: GESTIÓN DE CLIENTES
# ═════════════════════════════════════════════════════════════════════════════
seccion("4. GESTIÓN DE CLIENTES")

id_admin = state["usuario_admin"]["id_usuario"] if state["usuario_admin"] else 1

# 4.1 Listar clientes
try:
    clientes = backend.obtener_clientes()
    if isinstance(clientes, list):
        _log("OK", "Clientes", f"Listar clientes → {len(clientes)} clientes encontrados")
    else:
        _log("FALLA", "Clientes", "Listar clientes", f"No retornó lista: {type(clientes)}")
except Exception as e:
    _log("FALLA", "Clientes", "Listar clientes", f"Excepción: {e}")

# 4.2 Buscar cliente por nombre
try:
    resultados = backend.buscar_cliente_por_nombre("Consum")
    if isinstance(resultados, list):
        _log("OK", "Clientes", f"Buscar cliente por nombre 'Consum' → {len(resultados)} resultados")
    else:
        _log("FALLA", "Clientes", "Buscar cliente por nombre", f"Tipo inesperado: {type(resultados)}")
except Exception as e:
    _log("FALLA", "Clientes", "Buscar cliente por nombre", f"Excepción: {e}")

# 4.3 Crear cliente con email inválido → la validación de UI debe rechazarlo
try:
    valido_email, _ = ValidadoresVisuales.validar_email("email-invalido-sin-arroba")
    if not valido_email:
        _log("OK", "Clientes", "Crear cliente con email inválido → rechazado por validador UI")
    else:
        _log("FALLA", "Clientes", "Crear cliente con email inválido", "El validador aceptó un email sin @")
except Exception as e:
    _log("FALLA", "Clientes", "Validar email inválido", f"Excepción: {e}")

# 4.4 Crear cliente con campos obligatorios vacíos
try:
    ok, msg = ValidadorFormulario.validar_campos({
        "Nombre": ("", "nombre", True),
        "DNI": ("12345678", "dni", True),
    })
    if not ok:
        _log("OK", "Clientes", "Crear cliente con nombre vacío → rechazado por ValidadorFormulario")
    else:
        _log("FALLA", "Clientes", "Crear cliente con nombre vacío", "ValidadorFormulario aceptó nombre vacío")
except Exception as e:
    _log("FALLA", "Clientes", "Validar campos obligatorios vacíos", f"Excepción: {e}")

# 4.5 Crear cliente nuevo (con todos los campos completos)
import time as _time
ts = int(_time.time()) % 100000
nombre_cliente_test = f"Cliente Test {ts}"
try:
    id_nuevo = backend.crear_cliente(
        nombre=nombre_cliente_test,
        dni=f"9{ts:07d}"[:8],
        cuit="",
        direccion="Calle Falsa 123",
        telefono="3513456789",
        email=f"test{ts}@test.com",
        limite_credito=10000.0,
        id_usuario_admin=id_admin
    )
    if id_nuevo and isinstance(id_nuevo, int):
        state["cliente_nuevo_id"] = id_nuevo
        _log("OK", "Clientes", f"Crear cliente nuevo → ID={id_nuevo}, Nombre='{nombre_cliente_test}'")
    else:
        _log("FALLA", "Clientes", "Crear cliente nuevo", f"Retornó: {id_nuevo}")
except ValueError as ve:
    _log("FALLA", "Clientes", "Crear cliente nuevo", f"ValueError: {ve}")
except Exception as e:
    _log("FALLA", "Clientes", "Crear cliente nuevo", f"Excepción: {e}")

# 4.6 Consultar detalle del cliente creado
try:
    if state["cliente_nuevo_id"]:
        detalle = backend.obtener_cliente_completo(state["cliente_nuevo_id"])
        if detalle and detalle.get("nombre") == nombre_cliente_test:
            _log("OK", "Clientes", f"Consultar detalle cliente → nombre='{detalle['nombre']}' ✓")
        else:
            _log("FALLA", "Clientes", "Consultar detalle cliente", f"Detalle: {detalle}")
    else:
        _log("FALLA", "Clientes", "Consultar detalle cliente", "No hay cliente creado")
except Exception as e:
    _log("FALLA", "Clientes", "Consultar detalle cliente", f"Excepción: {e}")

# 4.7 Editar cliente existente
try:
    if state["cliente_nuevo_id"]:
        nombre_editado = f"Cliente Editado {ts}"
        resultado = backend.actualizar_cliente(
            id_cliente=state["cliente_nuevo_id"],
            nombre=nombre_editado,
            dni=f"9{ts:07d}"[:8],
            cuit="",
            direccion="Calle Editada 456",
            telefono="3513456789",
            email=f"editado{ts}@test.com",
            limite_credito=15000.0,
            id_usuario_admin=id_admin
        )
        if resultado:
            # Verificar que el cambio se persistió
            detalle = backend.obtener_cliente_completo(state["cliente_nuevo_id"])
            if detalle and detalle.get("nombre") == nombre_editado:
                _log("OK", "Clientes", f"Editar cliente → nombre actualizado a '{nombre_editado}' ✓")
            else:
                _log("PARCIAL", "Clientes", "Editar cliente", f"actualizar_cliente retornó True pero nombre en BD={detalle.get('nombre') if detalle else 'N/A'}")
        else:
            _log("FALLA", "Clientes", "Editar cliente", "actualizar_cliente retornó False")
    else:
        _log("FALLA", "Clientes", "Editar cliente", "No hay cliente para editar")
except Exception as e:
    _log("FALLA", "Clientes", "Editar cliente", f"Excepción: {e}")

# 4.8 Intentar eliminar cliente como Vendedor → debe estar bloqueado por permisos
try:
    puede_eliminar = tiene_permiso(usuario_vendedor_dict, "eliminar_clientes")
    if not puede_eliminar:
        _log("OK", "Clientes", "Vendedor intentar eliminar cliente → bloqueado por permisos ✓")
    else:
        _log("FALLA", "Clientes", "Vendedor intentar eliminar cliente", "El vendedor tiene permiso eliminar_clientes (no debería)")
except Exception as e:
    _log("FALLA", "Clientes", "Verificar bloqueo eliminación para vendedor", f"Excepción: {e}")

# 4.9 Supervisor intentar eliminar cliente → también bloqueado
try:
    puede_eliminar = tiene_permiso(usuario_supervisor_dict, "eliminar_clientes")
    if not puede_eliminar:
        _log("OK", "Clientes", "Supervisor intentar eliminar cliente → bloqueado por permisos ✓")
    else:
        _log("FALLA", "Clientes", "Supervisor intentar eliminar cliente", "El supervisor tiene permiso eliminar_clientes (no debería)")
except Exception as e:
    _log("FALLA", "Clientes", "Verificar bloqueo eliminación para supervisor", f"Excepción: {e}")

# 4.10 Admin eliminar cliente (lógico)
try:
    if state["cliente_nuevo_id"]:
        resultado = backend.eliminar_cliente_logico(state["cliente_nuevo_id"], id_usuario_admin=id_admin)
        if resultado:
            # Verificar que ya no aparece en listado activo
            clientes_post = backend.obtener_clientes()
            ids_activos = [c["id_cliente"] for c in clientes_post]
            if state["cliente_nuevo_id"] not in ids_activos:
                _log("OK", "Clientes", "Admin eliminar cliente (lógico) → no aparece en listado activo ✓")
            else:
                _log("FALLA", "Clientes", "Admin eliminar cliente", "El cliente sigue apareciendo en listado activo tras eliminación lógica")
        else:
            _log("FALLA", "Clientes", "Admin eliminar cliente", "eliminar_cliente_logico retornó False")
    else:
        _log("FALLA", "Clientes", "Admin eliminar cliente", "No hay cliente para eliminar")
except Exception as e:
    _log("FALLA", "Clientes", "Admin eliminar cliente", f"Excepción: {e}")

# ═════════════════════════════════════════════════════════════════════════════
# SECCIÓN 5: GESTIÓN DE PRODUCTOS Y CATEGORÍAS
# ═════════════════════════════════════════════════════════════════════════════
seccion("5. GESTIÓN DE PRODUCTOS Y CATEGORÍAS")

# 5.1 Listar categorías
try:
    cats = backend.obtener_categorias()
    if isinstance(cats, list) and len(cats) > 0:
        _log("OK", "Productos", f"Listar categorías → {len(cats)} categorías")
        state["categoria_nueva_id"] = cats[0].get("id_categoria")
    else:
        _log("PARCIAL", "Productos", "Listar categorías", f"Lista vacía o tipo incorrecto: {cats}")
except Exception as e:
    _log("FALLA", "Productos", "Listar categorías", f"Excepción: {e}")

# 5.2 Crear categoría nueva
try:
    nombre_cat = f"CatTest{ts}"
    resultado = backend.crear_categoria(nombre_cat, margen=20.0, es_pesable=False)
    if resultado:
        # Buscar el ID de la categoría recién creada
        cats_post = backend.obtener_categorias()
        cat_nueva = next((c for c in cats_post if c.get("nombre") == nombre_cat), None)
        if cat_nueva:
            state["categoria_nueva_id"] = cat_nueva.get("id_categoria")
            _log("OK", "Productos", f"Crear categoría nueva '{nombre_cat}' → ID={state['categoria_nueva_id']}")
        else:
            _log("PARCIAL", "Productos", "Crear categoría nueva", "crear_categoria retornó True pero no se encontró en listado")
    else:
        _log("FALLA", "Productos", "Crear categoría nueva", "crear_categoria retornó False")
except Exception as e:
    _log("FALLA", "Productos", "Crear categoría nueva", f"Excepción: {e}")

# 5.3 Listar productos
try:
    productos = backend.obtener_productos()
    if isinstance(productos, list) and len(productos) > 0:
        _log("OK", "Productos", f"Listar productos → {len(productos)} productos")
    else:
        _log("PARCIAL", "Productos", "Listar productos", "Lista vacía (puede ser que la BD no tiene productos demo)")
except Exception as e:
    _log("FALLA", "Productos", "Listar productos", f"Excepción: {e}")

# 5.4 Crear producto nuevo con todos los campos
try:
    nombre_prod = f"Producto Test {ts}"
    cat_id = state["categoria_nueva_id"]
    id_nuevo_prod = backend.crear_producto_completo(
        nombre=nombre_prod,
        categoria_id=cat_id,
        codigo_barras=f"7790{ts:06d}",
        precio=199.99,
        stock_inicial=50,
        stock_minimo=5,
        es_pesable=False,
        id_usuario=id_admin
    )
    if id_nuevo_prod:
        state["producto_nuevo_id"] = id_nuevo_prod
        _log("OK", "Productos", f"Crear producto '{nombre_prod}' → ID={id_nuevo_prod}")
    else:
        _log("FALLA", "Productos", "Crear producto nuevo", "Retornó None o False")
except Exception as e:
    _log("FALLA", "Productos", "Crear producto nuevo", f"Excepción: {e}")

# 5.5 Crear producto con precio negativo → debe rechazarse
try:
    backend.crear_producto_completo(
        nombre=f"ProdNegativo{ts}",
        categoria_id=state["categoria_nueva_id"],
        codigo_barras=None,
        precio=-100.0,
        stock_inicial=10,
        stock_minimo=2,
        id_usuario=id_admin
    )
    _log("FALLA", "Productos", "Crear producto con precio negativo", "No lanzó ValueError (debería haberlo hecho)")
except ValueError as ve:
    _log("OK", "Productos", "Crear producto con precio negativo → rechazado con ValueError ✓")
except Exception as e:
    _log("FALLA", "Productos", "Crear producto con precio negativo", f"Excepción inesperada: {e}")

# 5.6 Vendedor intenta crear producto → debe ser rechazado
try:
    # Usar el ID del vendedor activo (sofia=5, martin=4)
    # La verificación de rol en backend_adapter usa DB.obtener_usuarios_con_rol()
    usuarios_db = backend.obtener_usuarios_con_rol()
    vendedor_activo_id = next((u["id_usuario"] for u in usuarios_db if u.get("rol_nombre") == "vendedor" and u.get("activo")), None)
    if vendedor_activo_id is None:
        vendedor_activo_id = state["usuario_vendedor"]["id_usuario"] if state["usuario_vendedor"] else 5
    
    backend.crear_producto_completo(
        nombre=f"ProdVendedor{ts}",
        categoria_id=state["categoria_nueva_id"],
        codigo_barras=None,
        precio=100.0,
        stock_inicial=10,
        stock_minimo=2,
        id_usuario=vendedor_activo_id
    )
    _log("FALLA", "Productos", "Vendedor crear producto", f"No lanzó PermissionError (ID vendedor usado: {vendedor_activo_id})")
except PermissionError:
    _log("OK", "Productos", "Vendedor crear producto → rechazado con PermissionError ✓")
except Exception as e:
    _log("FALLA", "Productos", "Vendedor crear producto", f"Excepción inesperada: {e}")

# 5.7 Editar nombre de producto existente
try:
    if state["producto_nuevo_id"]:
        nombre_editado = f"Producto Editado {ts}"
        resultado = backend.actualizar_producto(
            id_producto=state["producto_nuevo_id"],
            nombre=nombre_editado,
            id_usuario=id_admin
        )
        if resultado:
            prod = backend.buscar_producto_por_id(state["producto_nuevo_id"])
            if prod and prod.get("nombre") == nombre_editado:
                _log("OK", "Productos", f"Editar nombre de producto → '{nombre_editado}' ✓")
            else:
                _log("PARCIAL", "Productos", "Editar nombre de producto", f"actualizar retornó True pero nombre en BD: {prod.get('nombre') if prod else 'N/A'}")
        else:
            _log("FALLA", "Productos", "Editar nombre de producto", "actualizar_producto retornó False")
    else:
        _log("FALLA", "Productos", "Editar nombre de producto", "No hay producto creado")
except Exception as e:
    _log("FALLA", "Productos", "Editar nombre de producto", f"Excepción: {e}")

# 5.8 Editar precio de producto
try:
    if state["producto_nuevo_id"]:
        nuevo_precio = 299.99
        resultado = backend.actualizar_producto(
            id_producto=state["producto_nuevo_id"],
            precio=nuevo_precio,
            id_usuario=id_admin
        )
        if resultado:
            prod = backend.buscar_producto_por_id(state["producto_nuevo_id"])
            precio_bd = float(prod.get("precio", 0)) if prod else 0
            if abs(precio_bd - nuevo_precio) < 0.01:
                _log("OK", "Productos", f"Editar precio de producto → ${nuevo_precio} en BD ✓")
            else:
                _log("PARCIAL", "Productos", "Editar precio de producto", f"Precio en BD={precio_bd}, esperado={nuevo_precio}")
        else:
            _log("FALLA", "Productos", "Editar precio de producto", "actualizar_producto retornó False")
    else:
        _log("FALLA", "Productos", "Editar precio de producto", "No hay producto creado")
except Exception as e:
    _log("FALLA", "Productos", "Editar precio de producto", f"Excepción: {e}")

# 5.9 Buscar producto por código de barras
try:
    if state["producto_nuevo_id"]:
        codigo = f"7790{ts:06d}"
        prod = backend.buscar_producto_por_codigo_barras(codigo)
        if prod:
            _log("OK", "Productos", f"Buscar producto por código de barras '{codigo}' → encontrado ✓")
        else:
            _log("PARCIAL", "Productos", "Buscar producto por código de barras", f"No encontró producto con código '{codigo}' (puede ser que el código no se asignó correctamente)")
except Exception as e:
    _log("FALLA", "Productos", "Buscar producto por código de barras", f"Excepción: {e}")

# 5.10 Buscar producto por nombre
try:
    if state["producto_nuevo_id"]:
        resultados = backend.buscar_producto_por_nombre(f"Editado {ts}")
        if resultados and len(resultados) > 0:
            _log("OK", "Productos", f"Buscar producto por nombre → {len(resultados)} resultado(s) ✓")
        else:
            _log("FALLA", "Productos", "Buscar producto por nombre", "No retornó resultados")
except Exception as e:
    _log("FALLA", "Productos", "Buscar producto por nombre", f"Excepción: {e}")

# 5.11 Eliminar producto (solo Admin puede)
try:
    puede_eliminar_supervisor = tiene_permiso(usuario_supervisor_dict, "eliminar_productos")
    if not puede_eliminar_supervisor:
        _log("OK", "Productos", "Supervisor NO puede eliminar productos → bloqueado por permisos ✓")
    else:
        _log("FALLA", "Productos", "Supervisor eliminar producto", "Supervisor tiene permiso eliminar_productos (no debería)")
except Exception as e:
    _log("FALLA", "Productos", "Verificar bloqueo eliminación producto supervisor", f"Excepción: {e}")

# ═════════════════════════════════════════════════════════════════════════════
# SECCIÓN 6: INVENTARIO Y AJUSTE DE STOCK
# ═════════════════════════════════════════════════════════════════════════════
seccion("6. INVENTARIO Y AJUSTE DE STOCK")

# 6.1 Obtener stock de producto
try:
    if state["producto_nuevo_id"]:
        stock = backend.obtener_stock(state["producto_nuevo_id"])
        _log("OK", "Inventario", f"Obtener stock del producto de prueba → {stock} unidades")
    else:
        _log("FALLA", "Inventario", "Obtener stock", "No hay producto creado")
except Exception as e:
    _log("FALLA", "Inventario", "Obtener stock", f"Excepción: {e}")

# 6.2 Ajuste manual de stock hacia arriba
try:
    if state["producto_nuevo_id"]:
        stock_antes = backend.obtener_stock(state["producto_nuevo_id"])
        stock_nuevo = stock_antes + 20
        resultado = backend.actualizar_inventario_absoluto(
            id_producto=state["producto_nuevo_id"],
            stock_abs=stock_nuevo,
            stock_minimo=5,
            id_usuario=id_admin,
            motivo="Ajuste de prueba funcional hacia arriba"
        )
        if resultado:
            stock_post = backend.obtener_stock(state["producto_nuevo_id"])
            if abs(stock_post - stock_nuevo) < 0.01:
                _log("OK", "Inventario", f"Ajuste manual stock ↑ → {stock_antes} → {stock_post} ✓")
            else:
                _log("FALLA", "Inventario", "Ajuste manual stock ↑", f"Stock en BD={stock_post}, esperado={stock_nuevo}")
        else:
            _log("FALLA", "Inventario", "Ajuste manual stock ↑", "actualizar_inventario_absoluto retornó False")
    else:
        _log("FALLA", "Inventario", "Ajuste manual stock ↑", "No hay producto creado")
except Exception as e:
    _log("FALLA", "Inventario", "Ajuste manual stock ↑", f"Excepción: {e}")

# 6.3 Ajuste manual de stock hacia abajo
try:
    if state["producto_nuevo_id"]:
        stock_antes = backend.obtener_stock(state["producto_nuevo_id"])
        stock_nuevo = max(0, stock_antes - 10)
        resultado = backend.actualizar_inventario_absoluto(
            id_producto=state["producto_nuevo_id"],
            stock_abs=stock_nuevo,
            stock_minimo=5,
            id_usuario=id_admin,
            motivo="Ajuste de prueba funcional hacia abajo"
        )
        if resultado:
            stock_post = backend.obtener_stock(state["producto_nuevo_id"])
            if abs(stock_post - stock_nuevo) < 0.01:
                _log("OK", "Inventario", f"Ajuste manual stock ↓ → {stock_antes} → {stock_post} ✓")
            else:
                _log("FALLA", "Inventario", "Ajuste manual stock ↓", f"Stock en BD={stock_post}, esperado={stock_nuevo}")
        else:
            _log("FALLA", "Inventario", "Ajuste manual stock ↓", "actualizar_inventario_absoluto retornó False")
    else:
        _log("FALLA", "Inventario", "Ajuste manual stock ↓", "No hay producto creado")
except Exception as e:
    _log("FALLA", "Inventario", "Ajuste manual stock ↓", f"Excepción: {e}")

# 6.4 Verificar que ajuste sin observación requiere manejo en UI
# (El backend acepta motivo vacío, la validación es en UI)
try:
    # El backend no bloquea el motivo vacío, eso es responsabilidad de la UI
    # Verificamos que el campo motivo se registra en auditoría
    if state["producto_nuevo_id"]:
        bitacora = backend.obtener_bitacora_acciones(
            accion="AJUSTE_STOCK_MANUAL",
            id_usuario=id_admin,
            limit=5
        )
        if bitacora:
            _log("OK", "Inventario", f"Ajuste de stock → registrado en Bitácora ({len(bitacora)} entradas encontradas) ✓")
        else:
            _log("PARCIAL", "Inventario", "Ajuste de stock en Bitácora", "No se encontraron entradas en bitácora para AJUSTE_STOCK_MANUAL")
except Exception as e:
    _log("FALLA", "Inventario", "Verificar ajuste en Bitácora", f"Excepción: {e}")

# 6.5 Ver stock bajo
try:
    bajo_stock = backend.obtener_stock_bajo()
    _log("OK", "Inventario", f"Obtener productos con stock bajo → {len(bajo_stock)} productos")
except Exception as e:
    _log("FALLA", "Inventario", "Obtener stock bajo", f"Excepción: {e}")

# ═════════════════════════════════════════════════════════════════════════════
# SECCIÓN 7: CAJA OPERATIVA
# ═════════════════════════════════════════════════════════════════════════════
seccion("7. CAJA OPERATIVA")

id_vendedor = state["usuario_vendedor"]["id_usuario"] if state["usuario_vendedor"] else None

# 7.1 Verificar que no hay caja abierta para el vendedor
try:
    if id_vendedor:
        caja = backend.obtener_session_abierta(id_vendedor)
        if caja is None:
            _log("OK", "Caja", "Vendedor no tiene caja abierta (estado inicial correcto) ✓")
        else:
            # Cerrar caja abierta previa para poder hacer el test limpio
            _log("PARCIAL", "Caja", "Vendedor ya tiene caja abierta (se limpiará)", f"ID session={caja.get('id_session')}")
            # Cerrar forzado
            backend.cerrar_caja_por_supervisor(caja["id_session"], id_supervisor=id_admin, obs="Limpieza test funcional")
    else:
        _log("FALLA", "Caja", "Verificar caja inicial vendedor", "No hay ID de vendedor")
except Exception as e:
    _log("FALLA", "Caja", "Verificar caja inicial vendedor", f"Excepción: {e}")

# 7.2 Abrir caja con monto inicial
try:
    if id_vendedor:
        resultado = backend.abrir_caja_session(id_vendedor, monto_inicial=1500.0, tipo_caja='turno')
        if resultado:
            caja = backend.obtener_session_abierta(id_vendedor)
            if caja:
                state["caja_session_id"] = caja.get("id_session")
                _log("OK", "Caja", f"Abrir caja con monto inicial $1500 → ID_session={state['caja_session_id']} ✓")
            else:
                _log("FALLA", "Caja", "Abrir caja", "abrir_caja_session retornó True pero no hay caja abierta")
        else:
            _log("FALLA", "Caja", "Abrir caja", "abrir_caja_session retornó False")
    else:
        _log("FALLA", "Caja", "Abrir caja", "No hay ID de vendedor")
except Exception as e:
    _log("FALLA", "Caja", "Abrir caja", f"Excepción: {e}")

# 7.3 Intentar abrir segunda caja estando la primera abierta
try:
    if id_vendedor and state["caja_session_id"]:
        try:
            resultado2 = backend.abrir_caja_session(id_vendedor, monto_inicial=500.0, tipo_caja='turno')
            _log("FALLA", "Caja", "Abrir segunda caja", f"No lanzó excepción ni retornó error (retornó {resultado2})")
        except ValueError as ve:
            _log("OK", "Caja", f"Abrir segunda caja → bloqueado con ValueError ✓ ('{ve}')")
        except Exception as e2:
            _log("PARCIAL", "Caja", "Abrir segunda caja", f"Lanzó excepción no-ValueError: {type(e2).__name__}: {e2}")
    else:
        _log("FALLA", "Caja", "Intentar abrir segunda caja", "No hay caja abierta previa para el test")
except Exception as e:
    _log("FALLA", "Caja", "Intentar abrir segunda caja", f"Excepción inesperada: {e}")

# 7.4 Ver movimientos del turno actual
try:
    if state["caja_session_id"]:
        movimientos = backend.obtener_historial_movimientos_caja(id_session=state["caja_session_id"])
        _log("OK", "Caja", f"Ver movimientos del turno → {len(movimientos)} movimientos")
    else:
        _log("FALLA", "Caja", "Ver movimientos del turno", "No hay caja abierta")
except Exception as e:
    _log("FALLA", "Caja", "Ver movimientos del turno", f"Excepción: {e}")

# 7.5 Transferir a Tesorería (requiere autorización)
# La validación de autorización es en la UI (autorizacion.py), aquí verificamos el backend
try:
    if state["caja_session_id"]:
        # Obtener tesorería activa
        tesoreria = backend.obtener_tesoreria_activa()
        if not tesoreria:
            # Crear tesorería para hoy si no existe
            tesoreria = backend.obtener_o_crear_tesoreria_hoy(id_admin)
        
        if tesoreria:
            id_tesoreria = tesoreria.get("id_session")
            # Intentar transferencia de $100
            resultado_tf = backend.transferir_entre_cajas(
                origen=state["caja_session_id"],
                destino=id_tesoreria,
                monto=100.0,
                id_usuario=id_vendedor,
                motivo_salida="transferencia_tesoreria",
                motivo_entrada="ingreso_turno",
                obs="Prueba transferencia funcional",
                id_autorizador=id_admin
            )
            if resultado_tf:
                _log("OK", "Caja", "Transferencia a Tesorería → registrada ✓")
            else:
                _log("FALLA", "Caja", "Transferencia a Tesorería", "transferir_entre_cajas retornó False")
        else:
            _log("PARCIAL", "Caja", "Transferencia a Tesorería", "No hay Tesorería activa para el test")
except Exception as e:
    _log("FALLA", "Caja", "Transferencia a Tesorería", f"Excepción: {e}")

# ═════════════════════════════════════════════════════════════════════════════
# SECCIÓN 8: VENTAS (POS)
# ═════════════════════════════════════════════════════════════════════════════
seccion("8. VENTAS (POS)")

# 8.1 Verificar que vendedor sin caja abierta no puede vender
# (La validación es en la UI, pero verificamos el estado)
try:
    caja_activa = backend.obtener_session_abierta(id_vendedor) if id_vendedor else None
    if caja_activa:
        _log("OK", "Ventas", "Vendedor tiene caja abierta → puede acceder al POS ✓")
    else:
        _log("PARCIAL", "Ventas", "Verificar caja para POS", "No hay caja activa (la apertura anterior falló)")
except Exception as e:
    _log("FALLA", "Ventas", "Verificar caja para POS", f"Excepción: {e}")

# 8.2 Preparar datos para venta
clientes = backend.obtener_clientes()
cliente_cf = next((c for c in clientes if "consumidor" in c.get("nombre", "").lower()), None)
if not cliente_cf and clientes:
    cliente_cf = clientes[0]

productos = backend.obtener_productos()
producto_venta = backend.buscar_producto_por_id(state["producto_nuevo_id"]) if state["producto_nuevo_id"] else (productos[0] if productos else None)

# 8.3 Registrar stock antes de la venta
if producto_venta:
    state["stock_antes_venta"] = backend.obtener_stock(producto_venta["id_producto"])

# 8.4 Registrar venta en efectivo con Consumidor Final
try:
    if producto_venta and id_vendedor and state["caja_session_id"]:
        # DB.registrar_venta_completa espera list[tuple[id_producto, nombre, cantidad, precio_unitario, codigo_barras]]
        items_venta = [
            (
                producto_venta["id_producto"],
                producto_venta.get("nombre", "Producto de prueba"),
                2.0,
                float(producto_venta.get("precio", 100.0)),
                producto_venta.get("codigo_barras", None)
            )
        ]
        id_venta = backend.registrar_venta_completa(
            id_usuario=id_vendedor,
            id_cliente=cliente_cf["id_cliente"] if cliente_cf else None,
            items=items_venta,
            tipo_pago="efectivo",
            id_session=state["caja_session_id"]
        )
        if id_venta:
            state["id_venta_prueba"] = id_venta
            _log("OK", "Ventas", f"Venta en efectivo → ID_venta={id_venta} ✓")
        else:
            _log("FALLA", "Ventas", "Venta en efectivo", "registrar_venta_completa retornó None")
    else:
        faltantes = []
        if not producto_venta: faltantes.append("producto")
        if not id_vendedor: faltantes.append("vendedor")
        if not state["caja_session_id"]: faltantes.append("caja")
        _log("FALLA", "Ventas", "Venta en efectivo", f"Faltan: {', '.join(faltantes)}")
except Exception as e:
    _log("FALLA", "Ventas", "Venta en efectivo", f"Excepción: {e}")

# 8.5 Verificar descuento de stock tras venta
try:
    if state["id_venta_prueba"] and producto_venta:
        stock_post = backend.obtener_stock(producto_venta["id_producto"])
        stock_esperado = state["stock_antes_venta"] - 2  # vendimos 2 unidades
        if abs(stock_post - stock_esperado) < 0.01:
            _log("OK", "Ventas", f"Stock descontado correctamente: {state['stock_antes_venta']} → {stock_post} (−2) ✓")
        else:
            _log("FALLA", "Ventas", "Stock descontado tras venta", f"Stock esperado={stock_esperado}, Stock en BD={stock_post}")
    else:
        _log("FALLA", "Ventas", "Verificar descuento de stock", "No hay venta registrada")
except Exception as e:
    _log("FALLA", "Ventas", "Verificar descuento de stock", f"Excepción: {e}")

# 8.6 Registrar venta con tarjeta
try:
    if producto_venta and id_vendedor and state["caja_session_id"]:
        items_venta2 = [
            (
                producto_venta["id_producto"],
                producto_venta.get("nombre", "Producto de prueba"),
                1.0,
                float(producto_venta.get("precio", 100.0)),
                producto_venta.get("codigo_barras", None)
            )
        ]
        id_venta2 = backend.registrar_venta_completa(
            id_usuario=id_vendedor,
            id_cliente=None,
            items=items_venta2,
            tipo_pago="tarjeta",
            id_session=state["caja_session_id"]
        )
        if id_venta2:
            _log("OK", "Ventas", f"Venta con tarjeta → ID_venta={id_venta2} ✓")
        else:
            _log("FALLA", "Ventas", "Venta con tarjeta", "registrar_venta_completa retornó None")
    else:
        _log("FALLA", "Ventas", "Venta con tarjeta", "Falta producto/vendedor/caja")
except Exception as e:
    _log("FALLA", "Ventas", "Venta con tarjeta", f"Excepción: {e}")

# 8.7 Registrar venta en cuenta corriente
try:
    if producto_venta and id_vendedor and state["caja_session_id"] and cliente_cf:
        items_cc = [
            (
                producto_venta["id_producto"],
                producto_venta.get("nombre", "Producto de prueba"),
                1.0,
                float(producto_venta.get("precio", 100.0)),
                producto_venta.get("codigo_barras", None)
            )
        ]
        id_venta_cc = backend.registrar_venta_completa(
            id_usuario=id_vendedor,
            id_cliente=cliente_cf["id_cliente"],
            items=items_cc,
            tipo_pago="cuenta_corriente",
            id_session=state["caja_session_id"]
        )
        if id_venta_cc:
            _log("OK", "Ventas", f"Venta en cuenta corriente → ID_venta={id_venta_cc} ✓")
        else:
            _log("FALLA", "Ventas", "Venta en cuenta corriente", "registrar_venta_completa retornó None")
    else:
        faltantes = []
        if not cliente_cf: faltantes.append("cliente")
        if not state["caja_session_id"]: faltantes.append("caja")
        _log("PARCIAL", "Ventas", "Venta en cuenta corriente", f"Faltan: {', '.join(faltantes)}")
except Exception as e:
    _log("FALLA", "Ventas", "Venta en cuenta corriente", f"Excepción: {e}")

# ═════════════════════════════════════════════════════════════════════════════
# SECCIÓN 9: CIERRE DE CAJA CON ARQUEO
# ═════════════════════════════════════════════════════════════════════════════
seccion("9. CIERRE DE CAJA CON ARQUEO")

# 9.1 Obtener resumen de cierre
try:
    if state["caja_session_id"]:
        resumen = backend.obtener_resumen_cierre(state["caja_session_id"])
        if resumen:
            _log("OK", "Caja", f"Obtener resumen cierre → {resumen}")
        else:
            _log("PARCIAL", "Caja", "Obtener resumen cierre", "resumen vacío o None")
    else:
        _log("FALLA", "Caja", "Obtener resumen cierre", "No hay caja abierta")
except Exception as e:
    _log("FALLA", "Caja", "Obtener resumen cierre", f"Excepción: {e}")

# 9.2 Cerrar caja con arqueo
try:
    if state["caja_session_id"]:
        resumen = backend.obtener_resumen_cierre(state["caja_session_id"])
        efectivo_esperado = float(resumen.get("efectivo_esperado", 0)) if resumen else 1500.0
        efectivo_contado = efectivo_esperado + 50.0  # Simular diferencia de $50
        diferencia = efectivo_contado - efectivo_esperado
        
        resultado_cierre = backend.cerrar_caja_session(
            id_session=state["caja_session_id"],
            id_usuario_cierre=id_vendedor,
            efectivo_esperado=efectivo_esperado,
            efectivo_contado=efectivo_contado,
            diferencia=diferencia,
            obs="Cierre de prueba funcional"
        )
        if resultado_cierre:
            # Verificar que la caja quedó cerrada
            caja_post = backend.obtener_session_abierta(id_vendedor)
            if caja_post is None:
                _log("OK", "Caja", f"Cierre de caja con arqueo → diferencia=${diferencia:.2f}, caja cerrada en BD ✓")
            else:
                _log("FALLA", "Caja", "Cierre de caja", "cerrar_caja retornó True pero caja sigue abierta en BD")
        else:
            _log("FALLA", "Caja", "Cierre de caja con arqueo", "cerrar_caja_session retornó False")
    else:
        _log("FALLA", "Caja", "Cierre de caja con arqueo", "No hay caja abierta")
except Exception as e:
    _log("FALLA", "Caja", "Cierre de caja con arqueo", f"Excepción: {e}")

# 9.3 Verificar que el cierre quedó registrado en BD
try:
    conn = DB.conectar()
    cur = conn.cursor(dictionary=True)
    cur.execute(
        "SELECT id_session, estado, fecha_cierre FROM caja_session WHERE id_session=%s",
        (state["caja_session_id"],)
    )
    row = cur.fetchone()
    cur.close(); conn.close()
    if row and row.get("estado") == "cerrada" and row.get("fecha_cierre"):
        _log("OK", "Caja", f"Cierre registrado en BD: estado='{row['estado']}', fecha_cierre={row['fecha_cierre']} ✓")
    else:
        _log("FALLA", "Caja", "Verificar cierre en BD", f"Estado en BD: {row}")
except Exception as e:
    _log("FALLA", "Caja", "Verificar cierre en BD", f"Excepción: {e}")

# ═════════════════════════════════════════════════════════════════════════════
# SECCIÓN 10: HISTORIALES
# ═════════════════════════════════════════════════════════════════════════════
seccion("10. HISTORIALES Y RESTRICCIONES POR ROL")

hoy = date.today().isoformat()
hace_7 = (date.today() - timedelta(days=7)).isoformat()
hace_30 = (date.today() - timedelta(days=30)).isoformat()

# 10.1 Ver historial de ventas propio (vendedor)
try:
    if id_vendedor:
        ventas = backend.obtener_ventas_maestro(
            fecha_desde=hoy,
            fecha_hasta=hoy,
            id_cliente=None,
            id_vendedor=id_vendedor
        )
        _log("OK", "Historiales", f"Vendedor ver historial de ventas propio → {len(ventas)} venta(s) hoy")
    else:
        _log("FALLA", "Historiales", "Ver historial ventas vendedor", "No hay ID de vendedor")
except Exception as e:
    _log("FALLA", "Historiales", "Ver historial ventas vendedor", f"Excepción: {e}")

# 10.2 Verificar que vendedor NO puede ver ventas de otros
# (La restricción es en la UI: el filtro de vendedor está forzado al id del usuario)
try:
    puede_ver_todos = tiene_permiso(usuario_vendedor_dict, "ver_caja_todos")
    if not puede_ver_todos:
        _log("OK", "Historiales", "Vendedor NO tiene permiso ver_caja_todos → solo ve sus ventas ✓")
    else:
        _log("FALLA", "Historiales", "Restricción historial vendedor", "Vendedor tiene permiso ver_caja_todos (no debería)")
except Exception as e:
    _log("FALLA", "Historiales", "Restricción historial vendedor", f"Excepción: {e}")

# 10.3 Supervisor ver historial de ventas (últimos 7 días)
try:
    ventas_sup = backend.obtener_ventas_maestro(
        fecha_desde=hace_7,
        fecha_hasta=hoy,
        id_cliente=None,
        id_vendedor=None
    )
    _log("OK", "Historiales", f"Supervisor ver historial 7 días → {len(ventas_sup)} venta(s)")
except Exception as e:
    _log("FALLA", "Historiales", "Supervisor ver historial 7 días", f"Excepción: {e}")

# 10.4 Restricción de Supervisor a 7 días (verificar constante)
try:
    if DIAS_HISTORIAL_SUPERVISOR == 7:
        _log("OK", "Historiales", f"Restricción Supervisor a {DIAS_HISTORIAL_SUPERVISOR} días configurada ✓")
    else:
        _log("PARCIAL", "Historiales", "Restricción días supervisor", f"DIAS_HISTORIAL_SUPERVISOR={DIAS_HISTORIAL_SUPERVISOR} (esperado=7)")
except Exception as e:
    _log("FALLA", "Historiales", "Verificar restricción días supervisor", f"Excepción: {e}")

# 10.5 Admin ver historial sin restricciones de fecha
try:
    ventas_admin = backend.obtener_ventas_maestro(
        fecha_desde=hace_30,
        fecha_hasta=hoy,
        id_cliente=None,
        id_vendedor=None
    )
    _log("OK", "Historiales", f"Admin ver historial sin restricciones → {len(ventas_admin)} venta(s) en 30 días")
except Exception as e:
    _log("FALLA", "Historiales", "Admin ver historial sin restricciones", f"Excepción: {e}")

# 10.6 Ver historial de compras
try:
    compras = backend.obtener_compras_maestro(
        fecha_desde=hace_7,
        fecha_hasta=hoy,
        id_proveedor=None
    )
    _log("OK", "Historiales", f"Ver historial de compras → {len(compras)} compra(s)")
except Exception as e:
    _log("FALLA", "Historiales", "Ver historial compras", f"Excepción: {e}")

# 10.7 Ver historial de movimientos de caja
try:
    movimientos = backend.obtener_historial_movimientos_caja(
        fecha_desde=hoy,
        fecha_hasta=hoy
    )
    _log("OK", "Historiales", f"Ver historial movimientos caja → {len(movimientos)} movimiento(s)")
except Exception as e:
    _log("FALLA", "Historiales", "Ver historial movimientos caja", f"Excepción: {e}")

# 10.8 Ver historial de pagos de cuenta corriente
try:
    pagos = backend.obtener_pagos_maestro(
        fecha_desde=hoy,
        fecha_hasta=hoy,
        id_cliente=None,
        id_usuario=None
    )
    _log("OK", "Historiales", f"Ver historial pagos cc → {len(pagos)} pago(s)")
except Exception as e:
    _log("FALLA", "Historiales", "Ver historial pagos cc", f"Excepción: {e}")

# ═════════════════════════════════════════════════════════════════════════════
# SECCIÓN 11: PROVEEDORES Y COMPRAS
# ═════════════════════════════════════════════════════════════════════════════
seccion("11. PROVEEDORES Y COMPRAS")

id_supervisor = state["usuario_supervisor"]["id_usuario"] if state["usuario_supervisor"] else id_admin

# 11.1 Listar proveedores
try:
    proveedores = backend.obtener_proveedores()
    if isinstance(proveedores, list):
        _log("OK", "Proveedores", f"Listar proveedores → {len(proveedores)} proveedor(es)")
    else:
        _log("FALLA", "Proveedores", "Listar proveedores", f"Tipo inesperado: {type(proveedores)}")
except Exception as e:
    _log("FALLA", "Proveedores", "Listar proveedores", f"Excepción: {e}")

# 11.2 Crear proveedor nuevo
try:
    nombre_prov = f"Prov Test {ts}"
    # usuario_actual debe tener 'id_usuario' para que permisos funcionen correctamente
    usuario_supervisor_dict2 = {"id_rol": 3, "id_usuario": id_supervisor, "nombre": "supervisor"}
    id_prov = backend.crear_proveedor(
        nombre=f"Rep{ts}",
        empresa=nombre_prov,
        cuit_empresa=f"20{ts:09d}"[:11],
        dni_vendedor=f"3{ts:07d}"[:8],
        telefono="3514567890",
        email=f"prov{ts}@test.com",
        direccion="Av. Proveedor 789",
        id_usuario_admin=id_supervisor,
        usuario_actual=usuario_supervisor_dict2
    )
    if id_prov:
        state["proveedor_nuevo_id"] = id_prov
        _log("OK", "Proveedores", f"Crear proveedor '{nombre_prov}' → ID={id_prov} ✓")
    else:
        _log("FALLA", "Proveedores", "Crear proveedor", "crear_proveedor retornó None")
except Exception as e:
    _log("FALLA", "Proveedores", "Crear proveedor", f"Excepción: {e}")

# 11.3 Editar proveedor
try:
    if state["proveedor_nuevo_id"]:
        nombre_editado = f"Prov Editado {ts}"
        usuario_supervisor_dict2 = {"id_rol": 3, "id_usuario": id_supervisor, "nombre": "supervisor"}
        resultado = backend.actualizar_proveedor(
            id_proveedor=state["proveedor_nuevo_id"],
            nombre=f"Rep{ts}",
            empresa=nombre_editado,
            cuit_empresa=f"20{ts:09d}"[:11],
            dni_vendedor=f"3{ts:07d}"[:8],
            telefono="3514567890",
            email=f"prov{ts}@test.com",
            direccion="Av. Editada 999",
            id_usuario_admin=id_supervisor,
            usuario_actual=usuario_supervisor_dict2
        )
        if resultado:
            _log("OK", "Proveedores", f"Editar proveedor → '{nombre_editado}' ✓")
        else:
            _log("FALLA", "Proveedores", "Editar proveedor", "actualizar_proveedor retornó False")
    else:
        _log("FALLA", "Proveedores", "Editar proveedor", "No hay proveedor creado")
except Exception as e:
    _log("FALLA", "Proveedores", "Editar proveedor", f"Excepción: {e}")

# 11.4 Registrar compra con pago en efectivo
try:
    if state["proveedor_nuevo_id"] and state["producto_nuevo_id"]:
        # Guardar stock antes de compra
        state["stock_antes_compra"] = backend.obtener_stock(state["producto_nuevo_id"])
        
        usuario_supervisor_dict2 = {"id_rol": 3, "id_usuario": id_supervisor, "nombre": "supervisor"}
        # La UI construye items con clave 'id' (no 'id_producto') y 'precio_venta' (no 'precio_nuevo')
        items_compra = [
            {
                "id": state["producto_nuevo_id"],
                "cant": 10,
                "costo": 80.0,
                "precio_venta": 299.99
            }
        ]
        resultado_compra = backend.registrar_compra_mixta(
            id_usuario=id_supervisor,
            id_proveedor=state["proveedor_nuevo_id"],
            items=items_compra,
            medio_real="efectivo",
            monto_efectivo=800.0,
            usuario_actual=usuario_supervisor_dict2
        )
        if resultado_compra.get("id_compra"):
            state["id_compra_prueba"] = resultado_compra["id_compra"]
            pago_ok = resultado_compra.get("pago_exitoso", False)
            _log("OK", "Proveedores", f"Registrar compra en efectivo → ID_compra={state['id_compra_prueba']}, pago_exitoso={pago_ok} ✓")
        else:
            _log("FALLA", "Proveedores", "Registrar compra en efectivo", f"Resultado: {resultado_compra}")
    else:
        faltantes = []
        if not state["proveedor_nuevo_id"]: faltantes.append("proveedor")
        if not state["producto_nuevo_id"]: faltantes.append("producto")
        _log("FALLA", "Proveedores", "Registrar compra en efectivo", f"Faltan: {', '.join(faltantes)}")
except Exception as e:
    _log("FALLA", "Proveedores", "Registrar compra en efectivo", f"Excepción: {e}")

# 11.5 Verificar que stock se incrementó tras compra
try:
    if state["id_compra_prueba"] and state["producto_nuevo_id"]:
        stock_post_compra = backend.obtener_stock(state["producto_nuevo_id"])
        stock_esperado = state["stock_antes_compra"] + 10
        if abs(stock_post_compra - stock_esperado) < 0.01:
            _log("OK", "Proveedores", f"Stock incrementado: {state['stock_antes_compra']} → {stock_post_compra} (+10) ✓")
        else:
            _log("FALLA", "Proveedores", "Stock incrementado tras compra", f"Esperado={stock_esperado}, BD={stock_post_compra}")
    else:
        _log("FALLA", "Proveedores", "Verificar stock tras compra", "No hay compra registrada")
except Exception as e:
    _log("FALLA", "Proveedores", "Verificar stock tras compra", f"Excepción: {e}")

# 11.6 Registrar compra en cuenta corriente del proveedor
try:
    if state["proveedor_nuevo_id"] and state["producto_nuevo_id"]:
        usuario_supervisor_dict2 = {"id_rol": 3, "id_usuario": id_supervisor, "nombre": "supervisor"}
        items_cc = [
            {
                "id": state["producto_nuevo_id"],
                "cant": 5,
                "costo": 80.0,
                "precio_venta": 299.99
            }
        ]
        resultado_cc = backend.registrar_compra_mixta(
            id_usuario=id_supervisor,
            id_proveedor=state["proveedor_nuevo_id"],
            items=items_cc,
            medio_real="cuenta_corriente",
            usuario_actual=usuario_supervisor_dict2
        )
        if resultado_cc.get("id_compra"):
            _log("OK", "Proveedores", f"Compra en cuenta corriente proveedor → ID={resultado_cc['id_compra']} ✓")
        else:
            _log("FALLA", "Proveedores", "Compra en cuenta corriente proveedor", f"Resultado: {resultado_cc}")
    else:
        _log("FALLA", "Proveedores", "Compra en cuenta corriente", "Faltan proveedor o producto")
except Exception as e:
    _log("FALLA", "Proveedores", "Compra en cuenta corriente", f"Excepción: {e}")

# 11.7 Registrar compra por transferencia (no valida saldo de Tesorería)
try:
    if state["proveedor_nuevo_id"] and state["producto_nuevo_id"]:
        usuario_supervisor_dict2 = {"id_rol": 3, "id_usuario": id_supervisor, "nombre": "supervisor"}
        items_tf = [
            {
                "id": state["producto_nuevo_id"],
                "cant": 3,
                "costo": 80.0,
                "precio_venta": 299.99
            }
        ]
        resultado_tf = backend.registrar_compra_mixta(
            id_usuario=id_supervisor,
            id_proveedor=state["proveedor_nuevo_id"],
            items=items_tf,
            medio_real="transferencia",
            usuario_actual=usuario_supervisor_dict2
        )
        if resultado_tf.get("id_compra"):
            _log("OK", "Proveedores", f"Compra por transferencia → ID={resultado_tf['id_compra']} ✓")
        else:
            _log("FALLA", "Proveedores", "Compra por transferencia", f"Resultado: {resultado_tf}")
    else:
        _log("FALLA", "Proveedores", "Compra por transferencia", "Faltan proveedor o producto")
except Exception as e:
    _log("FALLA", "Proveedores", "Compra por transferencia", f"Excepción: {e}")

# ═════════════════════════════════════════════════════════════════════════════
# SECCIÓN 12: CUENTA CORRIENTE
# ═════════════════════════════════════════════════════════════════════════════
seccion("12. CUENTA CORRIENTE")

# 12.1 Ver clientes con deuda activa
try:
    clientes_deuda = backend.obtener_clientes_con_deuda()
    _log("OK", "CuentaCorriente", f"Ver clientes con deuda → {len(clientes_deuda)} cliente(s)")
except Exception as e:
    _log("FALLA", "CuentaCorriente", "Ver clientes con deuda", f"Excepción: {e}")

# 12.2 Registrar pago en efectivo
try:
    if cliente_cf:
        cuenta = backend.obtener_cuenta_por_cliente(cliente_cf["id_cliente"])
        if cuenta:
            saldo_antes = float(cuenta.get("saldo", 0))
            if saldo_antes < 0:
                monto_pago = min(100.0, abs(saldo_antes))
                resultado_pago = backend.registrar_pago_cuenta_corriente(
                    id_cuenta=cuenta["id_cuenta"],
                    monto=monto_pago,
                    metodo="efectivo",
                    id_usuario=id_supervisor
                )
                if resultado_pago:
                    cuenta_post = backend.obtener_cuenta_por_cliente(cliente_cf["id_cliente"])
                    saldo_post = float(cuenta_post.get("saldo", 0)) if cuenta_post else saldo_antes
                    diferencia = saldo_post - saldo_antes # El saldo debería aumentar (acercarse a 0)
                    if abs(diferencia - monto_pago) < 0.01:
                        _log("OK", "CuentaCorriente", f"Pago en efectivo ${monto_pago:.2f} → saldo actualizado ✓")
                    else:
                        _log("PARCIAL", "CuentaCorriente", "Pago en efectivo", f"Saldo antes={saldo_antes}, después={saldo_post}, pago={monto_pago}")
                else:
                    _log("FALLA", "CuentaCorriente", "Pago en efectivo", "registrar_pago_cuenta_corriente retornó False")
            else:
                _log("PARCIAL", "CuentaCorriente", "Registrar pago en efectivo", f"Cliente '{cliente_cf['nombre']}' no tiene saldo deudor ({saldo_antes})")
        else:
            _log("PARCIAL", "CuentaCorriente", "Registrar pago en efectivo", "No hay cuenta corriente para el cliente")
    else:
        _log("FALLA", "CuentaCorriente", "Registrar pago en efectivo", "No hay cliente disponible")
except Exception as e:
    _log("FALLA", "CuentaCorriente", "Registrar pago en efectivo", f"Excepción: {e}")

# ═════════════════════════════════════════════════════════════════════════════
# SECCIÓN 13: GESTIÓN DE USUARIOS
# ═════════════════════════════════════════════════════════════════════════════
seccion("13. GESTIÓN DE USUARIOS (ADMIN ONLY)")

# 13.1 Ver lista de usuarios
try:
    usuarios = backend.obtener_usuarios_con_rol()
    if usuarios:
        _log("OK", "Usuarios", f"Ver lista de usuarios → {len(usuarios)} usuario(s)")
    else:
        _log("FALLA", "Usuarios", "Ver lista de usuarios", "Lista vacía")
except Exception as e:
    _log("FALLA", "Usuarios", "Ver lista de usuarios", f"Excepción: {e}")

# 13.2 Crear usuario nuevo
try:
    nombre_usr = f"testuser{ts}"
    roles = backend.obtener_roles()
    id_rol_vendedor = next((r["id_rol"] for r in roles if r.get("nombre_rol", "").lower() == "vendedor"), 2)
    
    id_usr = backend.crear_usuario(
        nombre=nombre_usr,
        password_plana="testpass123",
        id_rol=id_rol_vendedor,
        id_usuario_admin=id_admin
    )
    if id_usr:
        state["usuario_nuevo_id"] = id_usr
        _log("OK", "Usuarios", f"Crear usuario '{nombre_usr}' → ID={id_usr} ✓")
    else:
        _log("FALLA", "Usuarios", "Crear usuario nuevo", "crear_usuario retornó None")
except Exception as e:
    _log("FALLA", "Usuarios", "Crear usuario nuevo", f"Excepción: {e}")

# 13.3 Crear usuario con nombre duplicado → debe fallar
try:
    if state["usuario_nuevo_id"]:
        usuarios_actuales = backend.obtener_usuarios_con_rol()
        nombre_existente = next((u["nombre"] for u in usuarios_actuales if u.get("id_usuario") == state["usuario_nuevo_id"]), None)
        if nombre_existente:
            id_dup = backend.crear_usuario(
                nombre=nombre_existente,
                password_plana="otrapass123",
                id_rol=2,
                id_usuario_admin=id_admin
            )
            if id_dup is None:
                _log("OK", "Usuarios", "Crear usuario con nombre duplicado → rechazado (retornó None) ✓")
            else:
                _log("FALLA", "Usuarios", "Crear usuario con nombre duplicado", f"Se creó con ID={id_dup} (debería fallar por UNIQUE)")
        else:
            _log("FALLA", "Usuarios", "Crear usuario con nombre duplicado", "No se encontró el nombre del usuario creado")
    else:
        _log("FALLA", "Usuarios", "Crear usuario con nombre duplicado", "No hay usuario previo para duplicar")
except Exception as e:
    # IntegrityError es el comportamiento esperado
    _log("OK", "Usuarios", f"Crear usuario con nombre duplicado → rechazado con excepción ({type(e).__name__}) ✓")

# 13.4 Cambiar contraseña de usuario
try:
    if state["usuario_nuevo_id"]:
        resultado = backend.resetear_password_usuario(
            id_usuario=state["usuario_nuevo_id"],
            password_plana_nueva="nuevapass456",
            id_usuario_admin=id_admin
        )
        if resultado:
            # Verificar que la nueva contraseña funciona
            login_test = backend.verificar_contraseña(nombre_usr, "nuevapass456", ignorar_sesion=True)
            if login_test and "id_usuario" in login_test:
                _log("OK", "Usuarios", "Cambiar contraseña usuario → nueva contraseña funciona ✓")
            else:
                _log("PARCIAL", "Usuarios", "Cambiar contraseña usuario", f"resetear retornó True pero login falló: {login_test}")
        else:
            _log("FALLA", "Usuarios", "Cambiar contraseña usuario", "resetear_password_usuario retornó False")
    else:
        _log("FALLA", "Usuarios", "Cambiar contraseña usuario", "No hay usuario creado")
except Exception as e:
    _log("FALLA", "Usuarios", "Cambiar contraseña usuario", f"Excepción: {e}")

# 13.5 Cambiar rol de usuario
try:
    if state["usuario_nuevo_id"]:
        roles = backend.obtener_roles()
        id_rol_sup = next((r["id_rol"] for r in roles if r.get("nombre_rol", "").lower() == "supervisor"), 3)
        resultado = backend.actualizar_rol_usuario(
            id_usuario=state["usuario_nuevo_id"],
            id_rol_nuevo=id_rol_sup
        )
        if resultado:
            usuarios_post = backend.obtener_usuarios_con_rol()
            usr_post = next((u for u in usuarios_post if u.get("id_usuario") == state["usuario_nuevo_id"]), None)
            if usr_post and usr_post.get("id_rol") == id_rol_sup:
                _log("OK", "Usuarios", f"Cambiar rol de usuario → ahora es Supervisor ✓")
            else:
                _log("PARCIAL", "Usuarios", "Cambiar rol de usuario", f"actualizar_rol retornó True pero rol en BD={usr_post.get('id_rol') if usr_post else 'N/A'}")
        else:
            _log("FALLA", "Usuarios", "Cambiar rol de usuario", "actualizar_rol_usuario retornó False")
    else:
        _log("FALLA", "Usuarios", "Cambiar rol de usuario", "No hay usuario creado")
except Exception as e:
    _log("FALLA", "Usuarios", "Cambiar rol de usuario", f"Excepción: {e}")

# 13.6 Forzar cierre de sesión de usuario
try:
    if state["usuario_nuevo_id"]:
        resultado = backend.forzar_cierre_sesion(state["usuario_nuevo_id"])
        if resultado:
            # Verificar token NULL
            conn = DB.conectar()
            cur = conn.cursor(dictionary=True)
            cur.execute("SELECT token_sesion FROM Usuario WHERE id_usuario=%s", (state["usuario_nuevo_id"],))
            row = cur.fetchone()
            cur.close(); conn.close()
            if row and row.get("token_sesion") is None:
                _log("OK", "Usuarios", "Forzar cierre de sesión → token_sesion=NULL ✓")
            else:
                _log("FALLA", "Usuarios", "Forzar cierre de sesión", f"Token no es NULL: {row}")
        else:
            _log("FALLA", "Usuarios", "Forzar cierre de sesión", "forzar_cierre_sesion retornó False")
    else:
        _log("FALLA", "Usuarios", "Forzar cierre de sesión", "No hay usuario creado")
except Exception as e:
    _log("FALLA", "Usuarios", "Forzar cierre de sesión", f"Excepción: {e}")

# 13.7 Intentar eliminar al único Admin (debe estar protegido a nivel UI)
try:
    usuarios = backend.obtener_usuarios_con_rol()
    admins = [u for u in usuarios if u.get("rol_nombre") == "admin" and u.get("activo")]
    if len(admins) == 1:
        # No hay función en backend que proteja esto explícitamente, es protección UI
        # Verificar que el permiso 'eliminar_usuarios' es solo de Admin
        puede_eliminar = tiene_permiso(usuario_supervisor_dict, "eliminar_usuarios")
        if not puede_eliminar:
            _log("OK", "Usuarios", "Solo Admin puede eliminar usuarios → permisos correctos ✓")
        else:
            _log("FALLA", "Usuarios", "Protección eliminar único admin", "Supervisor tiene permiso eliminar_usuarios (no debería)")
    else:
        _log("PARCIAL", "Usuarios", "Protección eliminar único admin", f"Hay {len(admins)} administradores activos (necesita exactamente 1 para la prueba)")
except Exception as e:
    _log("FALLA", "Usuarios", "Protección eliminar único admin", f"Excepción: {e}")

# ═════════════════════════════════════════════════════════════════════════════
# SECCIÓN 14: TESORERÍA
# ═════════════════════════════════════════════════════════════════════════════
seccion("14. TESORERÍA")

# 14.1 Ver tesorería del día
try:
    tesoreria = backend.obtener_tesoreria_activa()
    if not tesoreria:
        tesoreria = backend.obtener_o_crear_tesoreria_hoy(id_admin)
    
    if tesoreria:
        _log("OK", "Tesorería", f"Ver Tesorería del día → ID_session={tesoreria.get('id_session')}, saldo aprox=registros de movimientos")
    else:
        _log("FALLA", "Tesorería", "Ver Tesorería del día", "No hay Tesorería activa")
except Exception as e:
    _log("FALLA", "Tesorería", "Ver Tesorería del día", f"Excepción: {e}")

# 14.2 Registrar ingreso de capital con observación
try:
    resultado = backend.registrar_ingreso_capital(
        monto=5000.0,
        observacion="Ingreso de capital inicial de prueba",
        id_usuario=id_admin
    )
    if resultado:
        _log("OK", "Tesorería", "Registrar ingreso de capital $5000 → ✓")
    else:
        _log("FALLA", "Tesorería", "Registrar ingreso de capital", "registrar_ingreso_capital retornó False")
except Exception as e:
    _log("FALLA", "Tesorería", "Registrar ingreso de capital", f"Excepción: {e}")

# 14.3 Verificar que ingreso queda en Bitácora
try:
    bitacora = backend.obtener_bitacora_acciones(limit=10)
    if bitacora:
        _log("OK", "Tesorería", f"Bitácora accesible → {len(bitacora)} evento(s) recientes")
    else:
        _log("PARCIAL", "Tesorería", "Verificar ingreso en Bitácora", "Bitácora vacía")
except Exception as e:
    _log("FALLA", "Tesorería", "Verificar ingreso en Bitácora", f"Excepción: {e}")

# ═════════════════════════════════════════════════════════════════════════════
# SECCIÓN 15: BROADCAST Y MENSAJES
# ═════════════════════════════════════════════════════════════════════════════
seccion("15. BROADCAST Y MENSAJES")

# 15.1 Enviar mensaje a Todos
try:
    resultado = backend.enviar_mensaje_broadcast(
        contenido="Mensaje de prueba funcional a todos",
        id_admin=id_admin,
        destinatario_tipo="todos"
    )
    if resultado:
        _log("OK", "Broadcast", "Enviar mensaje a Todos → insertado en BD ✓")
    else:
        _log("FALLA", "Broadcast", "Enviar mensaje a Todos", "enviar_mensaje_broadcast retornó False")
except Exception as e:
    _log("FALLA", "Broadcast", "Enviar mensaje a Todos", f"Excepción: {e}")

# 15.2 Enviar mensaje solo a Vendedores (rol 2)
try:
    resultado = backend.enviar_mensaje_broadcast(
        contenido="Mensaje de prueba solo para vendedores",
        id_admin=id_admin,
        destinatario_tipo="rol",
        destinatario_id=2  # vendedor
    )
    if resultado:
        _log("OK", "Broadcast", "Enviar mensaje a Vendedores (rol 2) → ✓")
    else:
        _log("FALLA", "Broadcast", "Enviar mensaje a Vendedores", "retornó False")
except Exception as e:
    _log("FALLA", "Broadcast", "Enviar mensaje a Vendedores", f"Excepción: {e}")

# 15.3 Enviar mensaje a usuario específico
try:
    if state["usuario_vendedor"]:
        resultado = backend.enviar_mensaje_broadcast(
            contenido="Mensaje de prueba a usuario específico",
            id_admin=id_admin,
            destinatario_tipo="usuario",
            destinatario_id=state["usuario_vendedor"]["id_usuario"]
        )
        if resultado:
            _log("OK", "Broadcast", f"Enviar mensaje a usuario específico (ID={state['usuario_vendedor']['id_usuario']}) → ✓")
        else:
            _log("FALLA", "Broadcast", "Enviar mensaje a usuario específico", "retornó False")
    else:
        _log("FALLA", "Broadcast", "Enviar mensaje a usuario específico", "No hay ID de vendedor")
except Exception as e:
    _log("FALLA", "Broadcast", "Enviar mensaje a usuario específico", f"Excepción: {e}")

# 15.4 Verificar que mensajes se pueden leer por el receptor
try:
    if state["usuario_vendedor"]:
        msgs = backend.obtener_mensajes_no_leidos(
            id_rol=state["usuario_vendedor"]["id_rol"],
            id_usuario=state["usuario_vendedor"]["id_usuario"],
            ultimo_id=0
        )
        if isinstance(msgs, list):
            _log("OK", "Broadcast", f"Obtener mensajes no leídos para vendedor → {len(msgs)} mensaje(s)")
        else:
            _log("FALLA", "Broadcast", "Obtener mensajes no leídos", f"Tipo inesperado: {type(msgs)}")
    else:
        _log("FALLA", "Broadcast", "Obtener mensajes no leídos", "No hay ID de vendedor")
except Exception as e:
    _log("FALLA", "Broadcast", "Obtener mensajes no leídos", f"Excepción: {e}")

# ═════════════════════════════════════════════════════════════════════════════
# SECCIÓN 16: ANULACIÓN DE VENTAS Y COMPRAS (ADMIN)
# ═════════════════════════════════════════════════════════════════════════════
seccion("16. ANULACIÓN DE VENTAS Y COMPRAS")

# 16.1 Vendedor intenta anular venta → debe ser rechazado
try:
    if state["id_venta_prueba"] and id_vendedor:
        backend.anular_venta(
            id_venta=state["id_venta_prueba"],
            id_usuario=id_vendedor,
            motivo="Intento de anulación por vendedor"
        )
        _log("FALLA", "Anulación", "Vendedor intentar anular venta", "No lanzó PermissionError (debería haberlo hecho)")
    else:
        _log("FALLA", "Anulación", "Vendedor intentar anular venta", "No hay venta o vendedor disponible")
except PermissionError:
    _log("OK", "Anulación", "Vendedor intentar anular venta → rechazado con PermissionError ✓")
except Exception as e:
    _log("FALLA", "Anulación", "Vendedor intentar anular venta", f"Excepción inesperada: {type(e).__name__}: {e}")

# 16.2 Admin anular venta → stock debe volver
try:
    if state["id_venta_prueba"] and state["producto_nuevo_id"]:
        stock_antes_anulacion = backend.obtener_stock(state["producto_nuevo_id"])
        resultado = backend.anular_venta(
            id_venta=state["id_venta_prueba"],
            id_usuario=id_admin,
            motivo="Anulación de prueba funcional"
        )
        if resultado:
            stock_post_anulacion = backend.obtener_stock(state["producto_nuevo_id"])
            # El stock debe haber aumentado (se devolvieron 2 unidades vendidas)
            if stock_post_anulacion > stock_antes_anulacion:
                _log("OK", "Anulación", f"Admin anular venta → stock devuelto: {stock_antes_anulacion} → {stock_post_anulacion} ✓")
            else:
                _log("PARCIAL", "Anulación", "Admin anular venta", f"anular retornó True pero stock no cambió: antes={stock_antes_anulacion}, después={stock_post_anulacion}")
        else:
            _log("FALLA", "Anulación", "Admin anular venta", "anular_venta retornó False")
    else:
        _log("FALLA", "Anulación", "Admin anular venta", "No hay venta o producto disponible")
except ValueError as ve:
    _log("PARCIAL", "Anulación", "Admin anular venta", f"ValueError: {ve} (puede ser que ya estaba anulada)")
except Exception as e:
    _log("FALLA", "Anulación", "Admin anular venta", f"Excepción: {e}")

# 16.3 Verificar venta marcada como anulada en BD
try:
    if state["id_venta_prueba"]:
        conn = DB.conectar()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT estado FROM Venta WHERE id_venta=%s", (state["id_venta_prueba"],))
        row = cur.fetchone()
        cur.close(); conn.close()
        if row and row.get("estado") in ("cancelada", "anulada"):
            _log("OK", "Anulación", f"Venta marcada como '{row['estado']}' en BD ✓")
        else:
            _log("FALLA", "Anulación", "Verificar estado venta en BD", f"Estado en BD: {row}")
    else:
        _log("FALLA", "Anulación", "Verificar estado venta anulada", "No hay venta registrada")
except Exception as e:
    _log("FALLA", "Anulación", "Verificar estado venta en BD", f"Excepción: {e}")

# 16.4 Admin anular compra
try:
    if state["id_compra_prueba"]:
        stock_antes = backend.obtener_stock(state["producto_nuevo_id"]) if state["producto_nuevo_id"] else 0
        resultado = backend.anular_compra(
            id_compra=state["id_compra_prueba"],
            id_usuario=id_admin,
            motivo="Anulación de compra de prueba"
        )
        if resultado:
            if state["producto_nuevo_id"]:
                stock_post = backend.obtener_stock(state["producto_nuevo_id"])
                if stock_post < stock_antes:
                    _log("OK", "Anulación", f"Admin anular compra → stock descontado: {stock_antes} → {stock_post} ✓")
                else:
                    _log("PARCIAL", "Anulación", "Admin anular compra", f"anular retornó True pero stock no cambió: antes={stock_antes}, después={stock_post}")
            else:
                _log("OK", "Anulación", "Admin anular compra → retornó True ✓")
        else:
            _log("FALLA", "Anulación", "Admin anular compra", "anular_compra retornó False")
    else:
        _log("FALLA", "Anulación", "Admin anular compra", "No hay compra registrada")
except ValueError as ve:
    _log("PARCIAL", "Anulación", "Admin anular compra", f"ValueError: {ve}")
except Exception as e:
    _log("FALLA", "Anulación", "Admin anular compra", f"Excepción: {e}")

# ═════════════════════════════════════════════════════════════════════════════
# SECCIÓN 17: DASHBOARD Y KPIs
# ═════════════════════════════════════════════════════════════════════════════
seccion("17. DASHBOARD Y KPIs")

# 17.1 KPIs del Admin
try:
    kpis = backend.obtener_kpis_admin()
    if isinstance(kpis, dict):
        _log("OK", "Dashboard", f"KPIs Admin → ventas_dia=${kpis.get('ventas_dia',0):.2f}, tickets={kpis.get('tickets',0)}, efectivo=${kpis.get('efectivo_total',0):.2f}")
    else:
        _log("FALLA", "Dashboard", "KPIs Admin", f"Tipo inesperado: {type(kpis)}")
except Exception as e:
    _log("FALLA", "Dashboard", "KPIs Admin", f"Excepción: {e}")

# 17.2 Live Feed eventos
try:
    feed = backend.obtener_feed_eventos(limit=20)
    if isinstance(feed, list):
        _log("OK", "Dashboard", f"Live Feed → {len(feed)} evento(s) recientes")
    else:
        _log("FALLA", "Dashboard", "Live Feed", f"Tipo inesperado: {type(feed)}")
except Exception as e:
    _log("FALLA", "Dashboard", "Live Feed", f"Excepción: {e}")

# 17.3 Sesiones abiertas con totales (para dashboard)
try:
    sesiones = backend.obtener_sesiones_abiertas_con_totales()
    _log("OK", "Dashboard", f"Sesiones abiertas → {len(sesiones)} sesión(es) activa(s)")
except Exception as e:
    _log("FALLA", "Dashboard", "Sesiones abiertas con totales", f"Excepción: {e}")

# 17.4 Forzar cierre de caja (Supervisor/Admin)
try:
    # Abrir una caja temporal para probar el cierre forzado
    if id_vendedor:
        # Verificar si ya tiene caja abierta
        caja_actual = backend.obtener_session_abierta(id_vendedor)
        if not caja_actual:
            backend.abrir_caja_session(id_vendedor, monto_inicial=1000.0)
        
        caja_test = backend.obtener_session_abierta(id_vendedor)
        if caja_test:
            resultado_forzado = backend.cerrar_caja_por_supervisor(
                id_session=caja_test["id_session"],
                id_supervisor=id_supervisor,
                obs="Cierre forzado de prueba funcional"
            )
            if resultado_forzado:
                caja_post = backend.obtener_session_abierta(id_vendedor)
                if caja_post is None:
                    _log("OK", "Dashboard", "Forzar cierre de caja por Supervisor → caja cerrada en BD ✓")
                else:
                    _log("FALLA", "Dashboard", "Forzar cierre de caja", "cerrar retornó True pero caja sigue abierta")
            else:
                _log("FALLA", "Dashboard", "Forzar cierre de caja", "cerrar_caja_por_supervisor retornó False")
        else:
            _log("FALLA", "Dashboard", "Forzar cierre de caja", "No se pudo abrir caja temporal")
    else:
        _log("FALLA", "Dashboard", "Forzar cierre de caja", "No hay ID de vendedor")
except Exception as e:
    _log("FALLA", "Dashboard", "Forzar cierre de caja", f"Excepción: {e}")

# ═════════════════════════════════════════════════════════════════════════════
# SECCIÓN 18: BITÁCORA DE AUDITORÍA
# ═════════════════════════════════════════════════════════════════════════════
seccion("18. BITÁCORA DE AUDITORÍA")

# 18.1 Ver bitácora completa
try:
    bitacora = backend.obtener_bitacora_acciones(limit=50)
    if isinstance(bitacora, list):
        _log("OK", "Bitácora", f"Ver bitácora → {len(bitacora)} evento(s) accesibles")
    else:
        _log("FALLA", "Bitácora", "Ver bitácora", f"Tipo inesperado: {type(bitacora)}")
except Exception as e:
    _log("FALLA", "Bitácora", "Ver bitácora", f"Excepción: {e}")

# 18.2 Filtrar por usuario
try:
    bitacora_filtrada = backend.obtener_bitacora_acciones(id_usuario=id_admin, limit=10)
    _log("OK", "Bitácora", f"Filtrar bitácora por usuario admin → {len(bitacora_filtrada)} evento(s)")
except Exception as e:
    _log("FALLA", "Bitácora", "Filtrar bitácora por usuario", f"Excepción: {e}")

# 18.3 Filtrar por tipo de acción
try:
    bitacora_accion = backend.obtener_bitacora_acciones(accion="CREAR_PRODUCTO", limit=10)
    _log("OK", "Bitácora", f"Filtrar bitácora por acción CREAR_PRODUCTO → {len(bitacora_accion)} evento(s)")
except Exception as e:
    _log("FALLA", "Bitácora", "Filtrar bitácora por acción", f"Excepción: {e}")

# 18.4 Verificar que acciones clave del test están registradas
try:
    acciones_esperadas = ["CREAR_PRODUCTO", "CREAR_CLIENTE", "AJUSTE_STOCK_MANUAL", "CREAR_USUARIO"]
    bitacora_hoy = backend.obtener_bitacora_acciones(
        fecha_desde=hoy,
        fecha_hasta=hoy,
        limit=100
    )
    acciones_encontradas = {e.get("accion") for e in bitacora_hoy}
    encontradas = [a for a in acciones_esperadas if a in acciones_encontradas]
    if len(encontradas) == len(acciones_esperadas):
        _log("OK", "Bitácora", f"Todas las acciones clave registradas: {', '.join(encontradas)} ✓")
    elif encontradas:
        _log("PARCIAL", "Bitácora", "Acciones clave en bitácora", 
             f"Encontradas: {encontradas} | No encontradas: {[a for a in acciones_esperadas if a not in acciones_encontradas]}")
    else:
        _log("FALLA", "Bitácora", "Acciones clave en bitácora", f"Ninguna acción esperada encontrada. Halladas: {list(acciones_encontradas)[:5]}")
except Exception as e:
    _log("FALLA", "Bitácora", "Verificar acciones clave en bitácora", f"Excepción: {e}")

# 18.5 Verificar que bitácora solo tiene permiso de Admin
try:
    puede_ver = tiene_permiso(usuario_admin_dict, "ver_auditoria")
    no_puede_supervisor = not tiene_permiso(usuario_supervisor_dict, "ver_auditoria")
    no_puede_vendedor = not tiene_permiso(usuario_vendedor_dict, "ver_auditoria")
    if puede_ver and no_puede_supervisor and no_puede_vendedor:
        _log("OK", "Bitácora", "Solo Admin puede ver Bitácora → permisos correctos ✓")
    else:
        msgs = []
        if not puede_ver: msgs.append("Admin NO puede ver")
        if not no_puede_supervisor: msgs.append("Supervisor SÍ puede ver (error)")
        if not no_puede_vendedor: msgs.append("Vendedor SÍ puede ver (error)")
        _log("FALLA", "Bitácora", "Permisos de Bitácora", "; ".join(msgs))
except Exception as e:
    _log("FALLA", "Bitácora", "Verificar permisos Bitácora", f"Excepción: {e}")

# ═════════════════════════════════════════════════════════════════════════════
# SECCIÓN 19: REPORTES
# ═════════════════════════════════════════════════════════════════════════════
seccion("19. REPORTES")

# 19.1 Reporte ventas del día
try:
    resumen = backend.obtener_resumen_diario(fecha=hoy)
    if isinstance(resumen, dict):
        _log("OK", "Reportes", f"Reporte ventas del día → {resumen}")
    else:
        _log("PARCIAL", "Reportes", "Reporte ventas del día", f"Tipo: {type(resumen)}, Valor: {resumen}")
except Exception as e:
    _log("FALLA", "Reportes", "Reporte ventas del día", f"Excepción: {e}")

# 19.2 Reporte ventas por vendedor
try:
    reporte_vend = backend.reporte_ventas_por_vendedor(desde=hoy, hasta=hoy)
    _log("OK", "Reportes", f"Reporte ventas por vendedor → {len(reporte_vend)} entrada(s)")
except Exception as e:
    _log("FALLA", "Reportes", "Reporte ventas por vendedor", f"Excepción: {e}")

# 19.3 Ventas diarias con filtro de fecha
try:
    ventas_diarias = backend.obtener_ventas_diarias(desde=hace_7, hasta=hoy)
    _log("OK", "Reportes", f"Ventas diarias últimos 7 días → {len(ventas_diarias)} día(s) con datos")
except Exception as e:
    _log("FALLA", "Reportes", "Ventas diarias con filtro", f"Excepción: {e}")

# ═════════════════════════════════════════════════════════════════════════════
# SECCIÓN 20: LIMPIEZA Y CIERRE DE SESIONES
# ═════════════════════════════════════════════════════════════════════════════
seccion("20. LIMPIEZA Y CIERRE FINAL")

# Cerrar todas las sesiones activas de los usuarios de prueba
for nombre_key, uid in [("usuario_vendedor", state["usuario_vendedor"]),
                        ("usuario_supervisor", state["usuario_supervisor"]),
                        ("usuario_admin", state["usuario_admin"])]:
    if uid:
        try:
            backend.cerrar_sesion_usuario(uid["id_usuario"])
        except:
            pass

# Limpiar usuario de prueba (desactivar, no eliminar)
if state["usuario_nuevo_id"]:
    try:
        backend.desactivar_usuario(state["usuario_nuevo_id"], id_usuario_admin=id_admin)
        _log("OK", "Limpieza", f"Usuario de prueba ID={state['usuario_nuevo_id']} desactivado ✓")
    except Exception as e:
        _log("PARCIAL", "Limpieza", "Desactivar usuario de prueba", f"{e}")

# Limpiar producto de prueba (desactivar)
if state["producto_nuevo_id"]:
    try:
        backend.eliminar_producto(state["producto_nuevo_id"], id_usuario=id_admin)
        _log("OK", "Limpieza", f"Producto de prueba ID={state['producto_nuevo_id']} desactivado ✓")
    except Exception as e:
        _log("PARCIAL", "Limpieza", "Desactivar producto de prueba", f"{e}")

# ═════════════════════════════════════════════════════════════════════════════
# RESUMEN FINAL
# ═════════════════════════════════════════════════════════════════════════════
total = OK + FALLA + PARCIAL
print(f"""
{BOLD}{CYAN}
╔══════════════════════════════════════════════════════════════════════╗
║             RESUMEN EJECUTIVO - PRUEBA FUNCIONAL COMPLETA           ║
╠══════════════════════════════════════════════════════════════════════╣
║  Total de pruebas: {total:<50}║
║  ✅ OK:      {OK:<57}║
║  ❌ FALLA:   {FALLA:<57}║
║  ⚠️  PARCIAL: {PARCIAL:<57}║
╚══════════════════════════════════════════════════════════════════════╝
{RESET}""")

# ── LISTA DETALLADA DE FALLAS ──────────────────────────────────────────────
fallas = [(s, c, d, det) for s, c, d, det in RESULTADOS if s in ("FALLA", "PARCIAL")]
if fallas:
    print(f"{BOLD}{RED}{'='*70}")
    print(f"  LISTA DETALLADA DE FALLAS / PARCIALES")
    print(f"{'='*70}{RESET}")
    for i, (estado, cat, desc, detalle) in enumerate(fallas, 1):
        icono = f"{RED}❌{RESET}" if estado == "FALLA" else f"{YELLOW}⚠️{RESET}"
        print(f"\n  {i}. {icono} [{cat}] {desc}")
        if detalle:
            print(f"     Detalle: {detalle}")
        # Asignar prioridad
        if estado == "FALLA":
            if cat in ("Auth", "Ventas", "Caja", "Anulación"):
                print(f"     {RED}Prioridad: CRÍTICA{RESET}")
            elif cat in ("Permisos", "Usuarios", "Historiales"):
                print(f"     {YELLOW}Prioridad: ALTA{RESET}")
            else:
                print(f"     Prioridad: BAJA")
        else:
            print(f"     Prioridad: BAJA (comportamiento parcial)")
else:
    print(f"\n{GREEN}{BOLD}🎉 ¡No se registraron fallas ni resultados parciales!{RESET}")

print(f"\n{BOLD}Script finalizado.{RESET}\n")
