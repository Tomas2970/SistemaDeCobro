import sys
import os
import random
from datetime import datetime, timedelta

# Asegurarse de cargar las rutas correctas para el import de módulos
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import mysql.connector
from dotenv import load_dotenv
from app.database.backend_adapter import BackendAdapter
import bcrypt

def limpiar_base_datos(cursor):
    print("🧹 Limpiando base de datos (borrando transacciones y catálogos...)")
    cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
    tablas = [
        "caja_movimiento", "caja_session", "DetalleVenta", "Venta",
        "DetalleCompra", "Compra", "Pago", "PagoProveedor", "nota_credito",
        "AuditoriaInventario", "AuditoriaAcciones", "Inventario", "Producto",
        "Categoria", "CuentaCorriente", "Cliente", "Proveedor_Producto",
        "Proveedor", "Usuario"
    ]
    for t in tablas:
        cursor.execute(f"TRUNCATE TABLE {t};")
    cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")

def generar_datos_demo():
    print("🚀 Iniciando Generación de Datos Demo Realistas...")
    
    # 1. Conexión directa para limpieza y setups iniciales
    load_dotenv()
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = int(os.getenv("DB_PORT", "3307"))
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_NAME = os.getenv("DB_NAME", "supermercado_don_atilio")
    
    conn = mysql.connector.connect(
        host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASSWORD, database=DB_NAME, autocommit=True
    )
    cursor = conn.cursor()
    
    limpiar_base_datos(cursor)
    
    # 2. Recrear ROLES
    cursor.execute("INSERT IGNORE INTO Rol (id_rol, nombre, descripcion) VALUES "
                   "(1, 'admin', 'Administrador'), "
                   "(2, 'vendedor', 'Vendedor'), "
                   "(3, 'supervisor', 'Supervisor')")
    
    # 3. USUARIOS
    print("👤 Creando Usuarios...")
    hashed_admin = bcrypt.hashpw("admin123".encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")
    hashed_vendedor = bcrypt.hashpw("vendedor123".encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")
    
    cursor.execute("INSERT INTO Usuario (nombre, contraseña, id_rol, activo) VALUES (%s, %s, %s, %s)", ("Admin Roberto", hashed_admin, 1, True))
    
    cursor.execute("INSERT INTO Usuario (nombre, contraseña, id_rol, activo) VALUES (%s, %s, %s, %s)", ("Ana Paula", hashed_vendedor, 2, True))
    id_ana = cursor.lastrowid
    
    cursor.execute("INSERT INTO Usuario (nombre, contraseña, id_rol, activo) VALUES (%s, %s, %s, %s)", ("Carlos Supervisor", hashed_admin, 3, True))
    id_carlos = cursor.lastrowid
    
    conn.close() 
    
    print("🔌 Conectando BackendAdapter para operar a través del sistema...")
    bd = BackendAdapter()
    id_admin = next((u["id_usuario"] for u in bd.obtener_usuarios_con_rol() if u["nombre"] == "Admin Roberto"), 1)
    
    # 4. CATEGORÍAS
    print("🏷️ Creando Categorías...")
    bd.crear_categoria("Almacén", 30.0, False)
    bd.crear_categoria("Bebidas", 40.0, False)
    bd.crear_categoria("Lácteos y Fiambres", 25.0, True)
    bd.crear_categoria("Limpieza", 35.0, False)
    
    categorias = bd.obtener_categorias()
    cat_map = {c["nombre"]: c["id_categoria"] for c in categorias}
    
    # 5. PRODUCTOS
    print("📦 Creando Productos Ficticios pero Realistas...")
    prods = [
        ("Coca Cola 2.25L", cat_map.get("Bebidas"), "7790895001109", 2500.0, 50, False),
        ("Cerveza Quilmes 1L", cat_map.get("Bebidas"), "7792798000010", 1800.0, 100, False),
        ("Yerba Playadito 1Kg", cat_map.get("Almacén"), "7790070308012", 3500.0, 30, False),
        ("Fideos Matarazzo 500g", cat_map.get("Almacén"), "7790742005014", 1200.0, 40, False),
        ("Arroz Gallo Oro 1kg", cat_map.get("Almacén"), "7790070300034", 1800.0, 25, False),
        ("Queso Cremoso La Paulina (x Kg)", cat_map.get("Lácteos y Fiambres"), "2000000000001", 5500.0, 15, True), 
        ("Leche Larga Vida Serenísima 1L", cat_map.get("Lácteos y Fiambres"), "7790387001013", 1400.0, 60, False),
        ("Lavandina Ayudín 1L", cat_map.get("Limpieza"), "7790310062015", 950.0, 30, False),
        ("Papel Higiénico Scott", cat_map.get("Limpieza"), "7790310062016", 2400.0, 20, False)
    ]
    
    for p in prods:
        bd.crear_producto_completo(p[0], p[1], p[2], p[3], p[4], 10, p[5], id_admin)
        
    productos_obj = bd.obtener_productos_full()
    
    # 6. PROVEEDORES Y COMPRAS
    print("🚚 Creando Proveedores y Compras iniciales para sustentar el stock...")
    bd.insertar_proveedor("Juan Distribuciones", "Distribuidora San Martin SA", "30-87654321-0", "28111222", "351-1112222", "ventas@sanmartin.com", "Av. Fuerza Aerea 1234")
    bd.insertar_proveedor("Lácteos El Amanecer", "El Amanecer SRL", "33-11223344-9", "30222333", "351-3334444", "pedidos@elamanecer.com", "Ruta 20 Km 5")
    
    proveedores = bd.obtener_proveedores()
    
    if proveedores and len(productos_obj) >= 3:
        # insertar_compra espera {'id': ..., 'cant': ..., 'costo': ...}
        items_compra_1 = [
            {"id": productos_obj[0]["id_producto"], "cant": 50, "costo": 1800.0},
            {"id": productos_obj[2]["id_producto"], "cant": 30, "costo": 2500.0}
        ]
        
        print("🏪 Abriendo Caja para Admin Roberto (requerido para registar compra)...")
        try:
            bd.abrir_caja_session(id_admin, 10000.0)
        except Exception:
            pass # Si ya estaba abierta, continuamos
            
        bd.insertar_compra(id_admin, proveedores[0]["id_proveedor"], items_compra_1, "transferencia")
    
    # 7. CLIENTES Y CUENTA CORRIENTE
    print("👥 Creando Clientes y habilitando Cuenta Corriente...")
    bd.crear_cliente("María González", "11222333", "27-11222333-4", "Calle Falsa 123", "351-5556666", "maria@gmail.com")
    bd.crear_cliente("Restaurante El Faro", "", "30-99887766-5", "Centro 456", "351-8889999", "compras@elfaro.com", 150000.0)
    
    clientes = bd.listar_clientes()
    id_elfaro = next((c["id_cliente"] for c in clientes if "Faro" in c["nombre"]), None)
    id_maria = next((c["id_cliente"] for c in clientes if "María" in c["nombre"]), None)
    
    if id_elfaro:
        bd.crear_cuenta_corriente_si_no_existe(id_elfaro)
    
    # 8. OPERATORIA DE CAJA Y VENTAS (Corazón de la demo)
    print("🏪 Abriendo Caja para Ana Paula...")
    bd.abrir_caja_session(id_ana, 50000.0) 
    sesion_ana = bd.obtener_session_abierta(id_ana)
    
    if sesion_ana:
        id_session = sesion_ana["id_session"]
        
        print("💰 Simulando Ventas y Pagos en Mostrador...")
        # Venta 1: Minorista, Efectivo
        # registrar_venta_completa espera list[tuple[id_producto, nombre, cantidad, precio, codigo_barras]]
        if len(productos_obj) >= 5:
            items_v1 = [
                (productos_obj[0]["id_producto"], productos_obj[0]["nombre"], 2.0, float(productos_obj[0]["precio"]), productos_obj[0].get("codigo_barras", "")),
                (productos_obj[4]["id_producto"], productos_obj[4]["nombre"], 1.0, float(productos_obj[4]["precio"]), productos_obj[4].get("codigo_barras", ""))
            ]
            bd.registrar_venta_completa(id_ana, id_maria, items_v1, "efectivo", id_session)
        
        # Venta 2: Restaurante El Faro, Cuenta Corriente
        if len(productos_obj) >= 6 and id_elfaro:
            items_v2 = [
                (productos_obj[1]["id_producto"], productos_obj[1]["nombre"], 24.0, float(productos_obj[1]["precio"]), productos_obj[1].get("codigo_barras", "")),
                (productos_obj[5]["id_producto"], productos_obj[5]["nombre"], 5.5, float(productos_obj[5]["precio"]), productos_obj[5].get("codigo_barras", ""))
            ]
            bd.registrar_venta_completa(id_ana, id_elfaro, items_v2, "cuenta_corriente", id_session)
        
        # Venta 3: Cliente Casual, Tarjeta
        if len(productos_obj) >= 9:
            items_v3 = [
                (productos_obj[7]["id_producto"], productos_obj[7]["nombre"], 1.0, float(productos_obj[7]["precio"]), productos_obj[7].get("codigo_barras", "")),
                (productos_obj[8]["id_producto"], productos_obj[8]["nombre"], 1.0, float(productos_obj[8]["precio"]), productos_obj[8].get("codigo_barras", ""))
            ]
            bd.registrar_venta_completa(id_ana, None, items_v3, "tarjeta", id_session)
        
        # El faro viene y paga una parte de la deuda
        if id_elfaro:
            cuenta_faro = bd.obtener_cuenta_por_cliente(id_elfaro)
            if cuenta_faro and cuenta_faro["saldo"] < 0:
                pago = abs(cuenta_faro["saldo"]) / 2
                print(f"💵 Restaurante El Faro realiza un pago parcial de ${pago}...")
                bd.registrar_pago_cuenta_corriente(cuenta_faro["id_cuenta"], float(pago), "efectivo", id_ana)
        
        print("🔒 Cerrando Caja de Ana Paula...")
        
        resumen = bd.obtener_resumen_cierre(id_session)
        efectivo_esperado = float(resumen.get("total_efectivo_caja", 50000.0))
        
        bd.cerrar_caja_session(id_session, id_ana, efectivo_esperado, efectivo_esperado + 200, 200, "Cierre ok, sobraron propinas")
        
    print("\n✅ ¡DATOS REALISTAS GENERADOS CORRECTAMENTE!")
    print("-------------------------------------------")
    print("Credenciales para demostrar:")
    print("Administrador : Admin Roberto | admin123")
    print("Vendedora     : Ana Paula     | vendedor123")
    print("-------------------------------------------")

if __name__ == "__main__":
    generar_datos_demo()
