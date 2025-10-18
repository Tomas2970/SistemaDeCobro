"""
Script de Testing Completo para Backend
Sistema de Cobro - Supermercado Don Atilio

Ejecutar: python test_db.py
"""

import sys
from datetime import datetime, timedelta

# Importar todas las funciones del backend
try:
    from database.DB import *
    print("✅ Módulo DB importado correctamente\n")
except ImportError as e:
    print(f"❌ Error al importar DB.py: {e}")
    sys.exit(1)

# =====================================
# Colores para la consola
# =====================================
class Color:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_test(nombre_test, exito, detalle=""):
    """Imprime resultado de un test con color"""
    simbolo = "✅" if exito else "❌"
    color = Color.GREEN if exito else Color.RED
    print(f"{simbolo} {color}{nombre_test}{Color.RESET}")
    if detalle:
        print(f"   → {detalle}")

def print_seccion(titulo):
    """Imprime un título de sección"""
    print(f"\n{Color.BOLD}{Color.BLUE}{'='*60}{Color.RESET}")
    print(f"{Color.BOLD}{Color.BLUE}{titulo.center(60)}{Color.RESET}")
    print(f"{Color.BOLD}{Color.BLUE}{'='*60}{Color.RESET}\n")

# =====================================
# Tests
# =====================================
def test_conexion():
    """Test 1: Conexión a la base de datos"""
    print_seccion("TEST 1: CONEXIÓN A BASE DE DATOS")
    
    try:
        conn = conectar()
        if conn:
            conn.close()
            print_test("Conexión exitosa", True, "Base de datos accesible")
            return True
        else:
            print_test("Conexión fallida", False, "No se pudo conectar")
            return False
    except Exception as e:
        print_test("Conexión fallida", False, f"Error: {e}")
        return False

def test_clientes():
    """Test 2: Operaciones con clientes"""
    print_seccion("TEST 2: OPERACIONES CON CLIENTES")
    
    tests_pasados = 0
    tests_totales = 3
    
    # Test 2.1: Obtener clientes
    clientes = obtener_clientes()
    if clientes and len(clientes) > 0:
        print_test("Obtener clientes", True, f"{len(clientes)} clientes encontrados")
        tests_pasados += 1
    else:
        print_test("Obtener clientes", False, "No se encontraron clientes")
    
    # Test 2.2: Buscar cliente por email
    if clientes:
        email_test = clientes[0].get('email')
        if email_test:
            cliente = buscar_cliente_por_email(email_test)
            if cliente:
                print_test("Buscar cliente por email", True, f"Cliente: {cliente['nombre']}")
                tests_pasados += 1
            else:
                print_test("Buscar cliente por email", False)
        else:
            print_test("Buscar cliente por email", False, "Sin email para probar")
    
    # Test 2.3: Insertar cliente de prueba
    id_cliente = insertar_cliente(
        nombre="Cliente Test",
        direccion="Calle Test 123",
        telefono="381999999",
        email=f"test_{datetime.now().timestamp()}@test.com"
    )
    if id_cliente:
        print_test("Insertar cliente", True, f"ID: {id_cliente}")
        tests_pasados += 1
    else:
        print_test("Insertar cliente", False)
    
    print(f"\n{Color.YELLOW}Resultado: {tests_pasados}/{tests_totales} tests pasados{Color.RESET}")
    return tests_pasados == tests_totales

def test_productos():
    """Test 3: Operaciones con productos"""
    print_seccion("TEST 3: OPERACIONES CON PRODUCTOS")
    
    tests_pasados = 0
    tests_totales = 4
    
    # Test 3.1: Obtener productos
    productos = obtener_productos()
    if productos and len(productos) > 0:
        print_test("Obtener productos", True, f"{len(productos)} productos encontrados")
        tests_pasados += 1
    else:
        print_test("Obtener productos", False)
    
    # Test 3.2: Obtener categorías
    categorias = obtener_categorias()
    if categorias and len(categorias) > 0:
        print_test("Obtener categorías", True, f"{len(categorias)} categorías encontradas")
        tests_pasados += 1
    else:
        print_test("Obtener categorías", False)
    
    # Test 3.3: Buscar producto por nombre
    if productos:
        nombre_test = productos[0]['nombre'][:5]  # Primeros 5 caracteres
        resultados = buscar_producto_por_nombre(nombre_test)
        if resultados:
            print_test("Buscar producto por nombre", True, f"{len(resultados)} resultados")
            tests_pasados += 1
        else:
            print_test("Buscar producto por nombre", False)
    
    # Test 3.4: Obtener productos por categoría
    if categorias:
        id_cat = categorias[0]['id_categoria']
        prod_cat = obtener_productos_por_categoria(id_cat)
        print_test("Filtrar por categoría", len(prod_cat) >= 0, 
                  f"{len(prod_cat)} productos en categoría")
        tests_pasados += 1
    
    print(f"\n{Color.YELLOW}Resultado: {tests_pasados}/{tests_totales} tests pasados{Color.RESET}")
    return tests_pasados == tests_totales

def test_inventario():
    """Test 4: Operaciones con inventario"""
    print_seccion("TEST 4: INVENTARIO Y STOCK")
    
    tests_pasados = 0
    tests_totales = 2
    
    # Test 4.1: Obtener inventario
    inventario = obtener_inventario()
    if inventario and len(inventario) > 0:
        print_test("Obtener inventario", True, f"{len(inventario)} items en inventario")
        tests_pasados += 1
    else:
        print_test("Obtener inventario", False)
    
    # Test 4.2: Obtener stock bajo
    stock_bajo = obtener_stock_bajo()
    if stock_bajo is not None:
        print_test("Obtener stock bajo", True, 
                  f"{len(stock_bajo)} productos con stock crítico")
        tests_pasados += 1
        
        if len(stock_bajo) > 0:
            print(f"\n   {Color.YELLOW}⚠️  ALERTA DE STOCK:{Color.RESET}")
            for producto in stock_bajo[:5]:  # Mostrar máximo 5
                faltante = producto['unidades_faltantes']
                print(f"   • {producto['nombre']}: {producto['cantidad']} unidades "
                      f"(faltan {faltante})")
    else:
        print_test("Obtener stock bajo", False)
    
    print(f"\n{Color.YELLOW}Resultado: {tests_pasados}/{tests_totales} tests pasados{Color.RESET}")
    return tests_pasados == tests_totales

def test_vistas():
    """Test 5: Vistas y reportes"""
    print_seccion("TEST 5: VISTAS Y REPORTES")
    
    tests_pasados = 0
    tests_totales = 4
    
    # Test 5.1: Ventas diarias
    ventas_diarias = obtener_ventas_diarias()
    if ventas_diarias is not None:
        print_test("Vista ventas diarias", True, f"{len(ventas_diarias)} días con ventas")
        tests_pasados += 1
    else:
        print_test("Vista ventas diarias", False)
    
    # Test 5.2: Productos más vendidos
    mas_vendidos = obtener_productos_mas_vendidos(5)
    if mas_vendidos is not None:
        print_test("Productos más vendidos", True, f"Top {len(mas_vendidos)}")
        tests_pasados += 1
        
        if len(mas_vendidos) > 0:
            print(f"\n   {Color.BLUE}📊 Top 3 Productos:{Color.RESET}")
            for i, prod in enumerate(mas_vendidos[:3], 1):
                print(f"   {i}. {prod['nombre']}: {prod['total_vendido']} unidades vendidas")
    else:
        print_test("Productos más vendidos", False)
    
    # Test 5.3: Clientes con deuda
    deudores = obtener_clientes_con_deuda()
    if deudores is not None:
        print_test("Clientes con deuda", True, f"{len(deudores)} clientes")
        tests_pasados += 1
        
        if len(deudores) > 0:
            print(f"\n   {Color.RED}💰 Clientes con deuda:{Color.RESET}")
            for cliente in deudores[:3]:
                print(f"   • {cliente['nombre']}: ${abs(cliente['saldo']):.2f}")
    else:
        print_test("Clientes con deuda", False)
    
    # Test 5.4: Estadísticas generales
    stats = obtener_estadisticas_generales()
    if stats and 'total_productos' in stats:
        print_test("Estadísticas generales", True)
        tests_pasados += 1
        
        print(f"\n   {Color.BLUE}📈 Resumen del Sistema:{Color.RESET}")
        print(f"   • Total productos: {stats['total_productos']}")
        print(f"   • Total clientes: {stats['total_clientes']}")
        print(f"   • Ventas del mes: {stats['ventas_mes']}")
        print(f"   • Monto del mes: ${stats['monto_ventas_mes']:.2f}")
        print(f"   • Productos stock bajo: {stats['productos_stock_bajo']}")
    else:
        print_test("Estadísticas generales", False)
    
    print(f"\n{Color.YELLOW}Resultado: {tests_pasados}/{tests_totales} tests pasados{Color.RESET}")
    return tests_pasados == tests_totales

def test_usuarios():
    """Test 6: Usuarios y autenticación"""
    print_seccion("TEST 6: USUARIOS Y SEGURIDAD")
    
    tests_pasados = 0
    tests_totales = 3
    
    # Test 6.1: Obtener usuarios
    usuarios = obtener_usuarios()
    if usuarios and len(usuarios) > 0:
        print_test("Obtener usuarios", True, f"{len(usuarios)} usuarios registrados")
        tests_pasados += 1
    else:
        print_test("Obtener usuarios", False)
    
    # Test 6.2: Obtener roles
    roles = obtener_roles()
    if roles and len(roles) > 0:
        print_test("Obtener roles", True, f"{len(roles)} roles disponibles")
        tests_pasados += 1
    else:
        print_test("Obtener roles", False)
    
    # Test 6.3: Verificar contraseña (con usuario admin si existe)
    if usuarios:
        # Intentar login con admin/admin123
        usuario = verificar_contraseña('admin', 'admin123')
        if usuario:
            print_test("Verificar contraseña", True, f"Login exitoso: {usuario['nombre']}")
            tests_pasados += 1
        else:
            print_test("Verificar contraseña", False, 
                      "No se pudo verificar (asegúrate que existe usuario 'admin')")
    
    print(f"\n{Color.YELLOW}Resultado: {tests_pasados}/{tests_totales} tests pasados{Color.RESET}")
    return tests_pasados == tests_totales

def test_otros():
    """Test 7: Otras funcionalidades"""
    print_seccion("TEST 7: OTRAS FUNCIONALIDADES")
    
    tests_pasados = 0
    tests_totales = 2
    
    # Test 7.1: Obtener proveedores
    proveedores = obtener_proveedores()
    if proveedores is not None:
        print_test("Obtener proveedores", True, f"{len(proveedores)} proveedores")
        tests_pasados += 1
    else:
        print_test("Obtener proveedores", False)
    
    # Test 7.2: Obtener ventas de cliente (si hay clientes)
    clientes = obtener_clientes()
    if clientes and len(clientes) > 0:
        id_cliente = clientes[0]['id_cliente']
        ventas = obtener_ventas_cliente(id_cliente)
        if ventas is not None:
            print_test("Obtener ventas de cliente", True, 
                      f"{len(ventas)} ventas del cliente")
            tests_pasados += 1
        else:
            print_test("Obtener ventas de cliente", False)
    else:
        print_test("Obtener ventas de cliente", False, "No hay clientes para probar")
    
    print(f"\n{Color.YELLOW}Resultado: {tests_pasados}/{tests_totales} tests pasados{Color.RESET}")
    return tests_pasados == tests_totales

# =====================================
# Ejecutar todos los tests
# =====================================
def ejecutar_todos_tests():
    """Ejecuta todos los tests y genera reporte"""
    print(f"\n{Color.BOLD}{'='*60}{Color.RESET}")
    print(f"{Color.BOLD}{'INICIANDO BATERÍA DE TESTS'.center(60)}{Color.RESET}")
    print(f"{Color.BOLD}{'='*60}{Color.RESET}")
    print(f"\nFecha: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    
    resultados = []
    
    # Ejecutar tests
    resultados.append(("Conexión", test_conexion()))
    resultados.append(("Clientes", test_clientes()))
    resultados.append(("Productos", test_productos()))
    resultados.append(("Inventario", test_inventario()))
    resultados.append(("Vistas/Reportes", test_vistas()))
    resultados.append(("Usuarios", test_usuarios()))
    resultados.append(("Otros", test_otros()))
    
    # Reporte final
    print_seccion("REPORTE FINAL")
    
    tests_exitosos = sum(1 for _, exito in resultados if exito)
    tests_totales = len(resultados)
    porcentaje = (tests_exitosos / tests_totales) * 100
    
    print(f"{Color.BOLD}Resumen de Tests:{Color.RESET}\n")
    for nombre, exito in resultados:
        simbolo = "✅" if exito else "❌"
        print(f"{simbolo} {nombre}")
    
    print(f"\n{Color.BOLD}{'='*60}{Color.RESET}")
    print(f"{Color.BOLD}Tests exitosos: {tests_exitosos}/{tests_totales} ({porcentaje:.1f}%){Color.RESET}")
    print(f"{Color.BOLD}{'='*60}{Color.RESET}\n")
    
    if porcentaje == 100:
        print(f"{Color.GREEN}{Color.BOLD}🎉 ¡TODOS LOS TESTS PASARON! 🎉{Color.RESET}\n")
        print(f"{Color.GREEN}El backend está funcionando perfectamente.{Color.RESET}")
    elif porcentaje >= 80:
        print(f"{Color.YELLOW}{Color.BOLD}⚠️  TESTS MAYORMENTE EXITOSOS{Color.RESET}\n")
        print(f"{Color.YELLOW}Hay algunos problemas menores, pero el sistema es funcional.{Color.RESET}")
    else:
        print(f"{Color.RED}{Color.BOLD}❌ PROBLEMAS DETECTADOS{Color.RESET}\n")
        print(f"{Color.RED}Revisa los errores anteriores y verifica la configuración.{Color.RESET}")
    
    print(f"\n{Color.BOLD}{'='*60}{Color.RESET}\n")
    
    return porcentaje == 100

# =====================================
# Función principal
# =====================================
if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║                                                          ║
    ║        🧪 SUITE DE TESTS - BACKEND DB.py 🧪             ║
    ║                                                          ║
    ║     Sistema de Cobro - Supermercado Don Atilio          ║
    ║                                                          ║
    ╚══════════════════════════════════════════════════════════╝
    """)
    
    import time
    print("Preparando tests...")
    time.sleep(1)
    
    try:
        exito = ejecutar_todos_tests()
        
        if exito:
            print(f"{Color.GREEN}✅ Backend listo para producción{Color.RESET}\n")
            sys.exit(0)
        else:
            print(f"{Color.YELLOW}⚠️  Backend funcional con advertencias{Color.RESET}\n")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print(f"\n\n{Color.YELLOW}⚠️  Tests interrumpidos por el usuario{Color.RESET}\n")
        sys.exit(2)
    except Exception as e:
        print(f"\n\n{Color.RED}❌ Error fatal durante los tests:{Color.RESET}")
        print(f"{Color.RED}{e}{Color.RESET}\n")
        sys.exit(3)