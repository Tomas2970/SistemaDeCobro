import sys
import os
import random
import string
from datetime import datetime
import traceback

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.database.backend_adapter import BackendAdapter
from dotenv import load_dotenv

def log_test(test_name, expected, actual, passed):
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status} | {test_name}")
    if not passed:
        print(f"    Expected: {expected}")
        print(f"    Actual  : {actual}")
    return {"test_name": test_name, "passed": passed, "expected": expected, "actual": actual}

def random_string(length=10):
    letters = string.ascii_letters + string.digits
    return ''.join(random.choice(letters) for i in range(length))

def run_qa_tests():
    load_dotenv()
    bd = BackendAdapter()
    
    results = []
    
    # -----------------------------------------------------
    # PREPARACIÓN DE CONTEXTO
    # -----------------------------------------------------
    usuarios = bd.obtener_usuarios_con_rol()
    admin = next((u for u in usuarios if u['id_rol'] == 1), None)
    vendedor = next((u for u in usuarios if u['id_rol'] == 2), None)
    supervisor = next((u for u in usuarios if u['id_rol'] == 3), None)
    
    if not admin or not vendedor or not supervisor:
        print("❌ Error: No se encontraron usuarios con los 3 roles requeridos para testear permisos.")
        return

    print("--- INICIANDO QA TESTING ---")

    # =====================================================
    # 1. PRUEBAS DE PERMISOS (RBAC)
    # =====================================================
    print("\n--- 1. Pruebas de Permisos ---")
    
    # Test 1.1: Vendedor intenta crear un cliente (Debería fallar/bloquearse si el backend lo restringe, pero BackendAdapter no tiene decoradores en sus métodos para saber QUIEN lo llama. BackendAdapter recibe acciones generales.
    # Uh oh, looking at the code, BackendAdapter doesn't take "usuario_actual" for most methods. Permisos are mostly handled in the UI via `permisos.py`.
    # Let's test the UI logic and backend logic.
    
    # Actually, `permisos.py` is checked in the UI. If the backend doesn't enforce permissions, that's a HUGE vulnerability!
    # Let's test if we can modify a price directly through the backend adapter without authenticating.
    try:
        productos = bd.obtener_productos_full()
        if productos:
            prod_id = productos[0]['id_producto']
            # Intentar actualizar producto (cambiamos el precio maliciosamente)
            # Pasamos un usuario 'None' o un 'id_vendedor' simulando que fue desde el backend
            bd.actualizar_producto(prod_id, nombre="Test Hack", precio=1.0, id_usuario=vendedor['id_usuario'])
            results.append(log_test("Vulnerabilidad RBAC en Backend (Productos)", "Debería lanzar Error de Permisos", "Permitió actualizar producto siendo Vendedor o sin validar permisos en backend", False))
    except Exception as e:
        results.append(log_test("Vulnerabilidad RBAC en Backend (Productos)", "Fallo de actualización o bloqueo", str(e), True))


    # =====================================================
    # 2. VALIDACIONES Y CASOS EXTREMOS
    # =====================================================
    print("\n--- 2. Validaciones Extremos ---")
    
    # Test 2.1: Crear producto con precio negativo
    try:
        cat_id = bd.obtener_categorias()[0]['id_categoria']
        bd.crear_producto_completo("Prod Negativo", cat_id, "NEG123", -500.0, -100.0, 10.0, False, admin['id_usuario'])
        results.append(log_test("Validación de Precio Negativo", "ValueError o Excepción", "Permitió crear producto con precio negativo", False))
    except Exception as e:
        results.append(log_test("Validación de Precio Negativo", "ValueError o Excepción", str(e), True))

    # Test 2.2: Crear producto con nombre absurdamente largo (SQL Truncation o Crash)
    long_name = "A" * 1000
    try:
        bd.crear_producto_completo(long_name, cat_id, "LONG123", 100.0, 50.0, 10.0, False, admin['id_usuario'])
        results.append(log_test("Validación de Nombre Largo", "DataError o Truncado seguro", "Creó el producto o rompió silenciosamente", False))
    except Exception as e:
        results.append(log_test("Validación de Nombre Largo", "DataError esperado", str(e), True))

    # Test 2.3: Inyección SQL básica en login
    try:
        user = bd.verificar_contraseña("admin' OR '1'='1", "cualquiercosa")
        if user:
            results.append(log_test("Inyección SQL en Login", "Retornar None", "Retornó un usuario (VULNERABLE!)", False))
        else:
            results.append(log_test("Inyección SQL en Login", "Retornar None", "Rechazado correctamente", True))
    except Exception as e:
         results.append(log_test("Inyección SQL en Login", "Controlado", str(e), True))


    # =====================================================
    # 3. COMPORTAMIENTO INESPERADO Y CAJA
    # =====================================================
    print("\n--- 3. Comportamiento de Caja y Ventas ---")
    
    # Test 3.1: Cerrar una caja que no existe
    try:
        bd.cerrar_caja_session(99999, admin['id_usuario'], 0.0, 0.0, 0.0, "Hacking caja")
        results.append(log_test("Cerrar Caja Inexistente", "Excepción/Error", "Se ejecutó sin errores (Falla Lógica)", False))
    except Exception as e:
         results.append(log_test("Cerrar Caja Inexistente", "Excepción", str(e), True))
         
    # Test 3.2: Ventas sin caja abierta
    # Nos aseguramos que el usuario "admin" no tenga caja abierta.
    # Bueno, vamos a intentar hacer una venta con un usuario inventado que no tiene caja.
    id_hacker = 9999
    try:
        bd.registrar_venta_completa(id_hacker, None, [], "efectivo")
        results.append(log_test("Venta con Carrito Vacío", "ValueError", "Permitió procesar", False))
    except Exception as e:
        results.append(log_test("Venta con Carrito Vacío", "ValueError", str(e), True))

    # Vamos a buscar un producto válido
    if productos:
        prod = productos[0]
        # Vender stock que no existe (ejemplo, vender 999999 unidades)
        try:
            # Primero abrimos caja para el admin si no está abierta
            try: bd.abrir_caja_session(admin['id_usuario'], 100.0)
            except: pass
            
            session = bd.obtener_session_activa()
            id_ses = session['id_session'] if session else None
            
            items = [(prod['id_producto'], prod['nombre'], 999999.0, float(prod['precio']), prod.get('codigo_barras', ''))]
            res = bd.registrar_venta_completa(admin['id_usuario'], None, items, "efectivo", id_ses)
            results.append(log_test("Vender más stock del disponible", "ValueError o Bloqueo", "Permitió la venta dejendo stock negativo", False))
        except Exception as e:
            results.append(log_test("Vender más stock del disponible", "ValueError o Bloqueo", str(e), True))
            
    # Test 3.3: Registrar Pago de Deuda Negativa o Absurda
    clientes = bd.listar_clientes()
    if clientes:
        cli = clientes[-1] # Agarramos uno cualquiera
        # Intentamos forzar la creación de cuenta corriente
        bd.crear_cuenta_corriente_si_no_existe(cli['id_cliente'])
        cuenta = bd.obtener_cuenta_por_cliente(cli['id_cliente'])
        if cuenta:
            try:
                # Intentar pagar un monto negativo (que podría aumentar la deuda a nuestro favor de forma ilícita)
                bd.registrar_pago_cuenta_corriente(cuenta['id_cuenta'], -50000.0, "efectivo", admin['id_usuario'])
                results.append(log_test("Pago Cta. Cte. Monto Negativo", "ValueError", "Permitió pago negativo (Grave Vulnerabilidad)", False))
            except Exception as e:
                results.append(log_test("Pago Cta. Cte. Monto Negativo", "ValueError", str(e), True))


    # =====================================================
    # 4. RESUMEN Y ESCRITURA DE ARCHIVO
    # =====================================================
    print("\n--- FINALIZADO ---")
    
    # Escribir el log crudo por si algo falla
    with open('qa_results_raw.txt', 'w', encoding='utf-8') as f:
        for r in results:
            f.write(f"{r}\n")

if __name__ == "__main__":
    run_qa_tests()
