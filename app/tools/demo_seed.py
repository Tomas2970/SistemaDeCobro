from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any


@dataclass(frozen=True)
class DemoContext:
    usuarios: dict[str, int]
    categorias: dict[str, int]
    clientes: dict[str, int]
    proveedores: dict[str, int]
    productos: dict[str, int]


class DemoSeeder:
    """Carga una base demo usando las mismas puertas de entrada que usa la UI."""

    def __init__(self) -> None:
        from app.database.backend_adapter import BackendAdapter
        from app.database import DB

        self.backend = BackendAdapter()
        self.DB = DB
        self.today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    def run(self) -> dict[str, int]:
        print("Reparando estructura antes de poblar demo...")
        from app.database.auto_migrate import ejecutar_migraciones

        ejecutar_migraciones()
        self._reset_connection_pool()
        self._clean_database()
        self._seed_roles_and_categories()
        ctx = self._seed_master_data()
        admin_session = self._open_admin_treasury(ctx.usuarios["admin"])
        self._seed_purchases(ctx, admin_session)
        self._seed_sales_days(ctx, admin_session)
        self._seed_history_exports(ctx)
        self._close_admin_treasury(admin_session, ctx.usuarios["admin"])
        self._age_master_data(ctx)
        return self._verify_counts()

    def _reset_connection_pool(self) -> None:
        self.DB.db_pool = None

    def _connect(self):
        return self.DB.conectar()

    def _clean_database(self) -> None:
        print("Limpiando base operativa...")
        tables = [
            "mensajes_broadcast",
            "nota_credito",
            "caja_movimiento",
            "PagoProveedor",
            "Pago",
            "DetalleVenta",
            "DetalleCompra",
            "Venta",
            "Compra",
            "caja_session",
            "AuditoriaInventario",
            "AuditoriaAcciones",
            "Proveedor_Producto",
            "Inventario",
            "Producto",
            "CuentaCorriente",
            "Cliente",
            "Proveedor",
            "Usuario",
            "Categoria",
            "Rol",
        ]

        conn = self._connect()
        cur = conn.cursor()
        try:
            cur.execute("SET FOREIGN_KEY_CHECKS=0")
            existing = self._existing_tables(cur)
            for table in tables:
                if table.lower() in existing:
                    cur.execute(f"DELETE FROM {table}")
                    try:
                        cur.execute(f"ALTER TABLE {table} AUTO_INCREMENT = 1")
                    except Exception:
                        pass
            cur.execute("SET FOREIGN_KEY_CHECKS=1")
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            try:
                cur.execute("SET FOREIGN_KEY_CHECKS=1")
            except Exception:
                pass
            cur.close()
            conn.close()
        self._reset_connection_pool()

    def _existing_tables(self, cur) -> set[str]:
        cur.execute("SHOW TABLES")
        return {str(row[0]).lower() for row in cur.fetchall()}

    def _seed_roles_and_categories(self) -> None:
        print("Cargando roles y categorias base...")
        categorias = [
            (1, "Bebidas", 30.0, 0),
            (2, "Almacen", 30.0, 0),
            (3, "Lacteos", 25.0, 0),
            (4, "Carnes", 35.0, 1),
            (5, "Limpieza", 30.0, 0),
            (6, "Panaderia", 40.0, 0),
            (7, "Congelados", 30.0, 0),
            (8, "Golosinas", 40.0, 0),
            (9, "Verduleria", 35.0, 1),
            (10, "Fiambres", 35.0, 1),
        ]
        conn = self._connect()
        cur = conn.cursor()
        try:
            cur.execute(
                """
                INSERT INTO Rol (id_rol, nombre, descripcion) VALUES
                (1, 'admin', 'Administrador del sistema'),
                (2, 'vendedor', 'Vendedor de salon'),
                (3, 'supervisor', 'Supervisor de operaciones')
                """
            )
            cur.executemany(
                """
                INSERT INTO Categoria
                    (id_categoria, nombre, descripcion, margen_ganancia, es_pesable_default, activa)
                VALUES (%s, %s, %s, %s, %s, 1)
                """,
                [
                    (cat_id, nombre, f"Categoria demo: {nombre}", margen, pesable)
                    for cat_id, nombre, margen, pesable in categorias
                ],
            )
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cur.close()
            conn.close()
        self._reset_connection_pool()

    def _seed_master_data(self) -> DemoContext:
        print("Creando usuarios, clientes, proveedores y productos...")
        usuarios = self._seed_users()
        categorias = self._load_ids("Categoria", "id_categoria", "nombre")
        clientes = self._seed_clients(usuarios["admin"])
        proveedores = self._seed_suppliers(usuarios["admin"])
        productos = self._seed_products(usuarios["admin"], categorias)
        self._assign_supplier_products(proveedores, productos)
        return DemoContext(usuarios, categorias, clientes, proveedores, productos)

    def _seed_users(self) -> dict[str, int]:
        specs = [
            ("admin", "admin123", 1, "10000001"),
            ("supervisor", "super123", 3, "10000002"),
            ("lucia", "lucia123", 2, "20000001"),
            ("martin", "martin123", 2, "20000002"),
            ("sofia", "sofia123", 2, "20000003"),
        ]
        ids: dict[str, int] = {}
        for nombre, password, rol, codigo in specs:
            user_id = self.backend.crear_usuario(nombre, password, rol, codigo_barras=codigo)
            if not user_id:
                raise RuntimeError(f"No se pudo crear el usuario demo {nombre}")
            ids[nombre] = int(user_id)
        return ids

    def _seed_clients(self, admin_id: int) -> dict[str, int]:
        specs = [
            ("Ana Pereyra", "30124567", "20301245671", "Godoy Cruz 124", "2615551842", "ana.pereyra@example.com", 65000),
            ("Carlos Molina", "28765432", "20287654321", "San Martin 840", "2615552088", "carlos.molina@example.com", 85000),
            ("Despensa El Molino", None, "30711222331", "Belgrano 911", "2615554021", "elmolino@example.com", 160000),
            ("Mariana Ruiz", "33444555", "27334445558", "Las Heras 230", "2615553177", "mariana.ruiz@example.com", 55000),
            ("Roberto Quiroga", "25999888", "20259998883", "Mitre 655", "2615556644", "roberto.quiroga@example.com", 70000),
            ("Valeria Castro", "36888111", "27368881112", "Colon 1550", "2615557733", "valeria.castro@example.com", 50000),
            ("Comedor Los Pinos", None, "30709888771", "Peru 330", "2615559344", "lospinos@example.com", 190000),
            ("Nicolas Herrera", "39222111", "20392221115", "Rivadavia 72", "2615551199", "nicolas.herrera@example.com", 45000),
            ("Paula Sosa", "31555123", "27315551231", "Sarmiento 101", "2615552922", "paula.sosa@example.com", 60000),
        ]
        ids: dict[str, int] = {}
        for nombre, dni, cuit, direccion, telefono, email, limite in specs:
            client_id = self.backend.crear_cliente(
                nombre,
                dni or "",
                cuit,
                direccion,
                telefono,
                email,
                limite,
                id_usuario_admin=admin_id,
            )
            if not client_id:
                raise RuntimeError(f"No se pudo crear el cliente demo {nombre}")
            ids[nombre] = int(client_id)
        return ids

    def _seed_suppliers(self, admin_id: int) -> dict[str, int]:
        specs = [
            ("Miguel Torres", "Distribuidora Cuyo SRL", "30700111223", "24555111", "2615557001", "ventas@cuyosrl.com", "Acceso Este 4500"),
            ("Laura Pena", "Lacteos Andinos", "30700222334", "27888222", "2615557002", "pedidos@lacteosandinos.com", "Ruta 40 Km 18"),
            ("Sergio Arce", "Limpieza Total", "30700333445", "30111333", "2615557003", "contacto@limpiezatotal.com", "Brasil 1880"),
            ("Natalia Vega", "Verduras del Valle", "30700444556", "32999444", "2615557004", "ventas@verdurasvalle.com", "Mercado Coop Nave 2"),
        ]
        ids: dict[str, int] = {}
        for nombre, empresa, cuit, dni, telefono, email, direccion in specs:
            supplier_id = self.backend.crear_proveedor(
                nombre,
                empresa,
                cuit,
                dni,
                telefono,
                email,
                direccion,
                id_usuario_admin=admin_id,
            )
            if not supplier_id:
                raise RuntimeError(f"No se pudo crear el proveedor demo {empresa}")
            ids[empresa] = int(supplier_id)
        return ids

    def _seed_products(self, admin_id: int, categorias: dict[str, int]) -> dict[str, int]:
        specs = [
            ("Coca Cola 1.5L", "Bebidas", "7790895001011", 2350, 18, 8, False),
            ("Agua Mineral 2L", "Bebidas", "7790895001028", 980, 30, 10, False),
            ("Jugo Naranja 1L", "Bebidas", "7790895001035", 1250, 20, 8, False),
            ("Arroz Largo Fino 1kg", "Almacen", "7790895002018", 1450, 26, 10, False),
            ("Fideos Tallarin 500g", "Almacen", "7790895002025", 890, 32, 12, False),
            ("Aceite Girasol 900ml", "Almacen", "7790895002032", 2100, 16, 8, False),
            ("Azucar 1kg", "Almacen", "7790895002049", 1150, 24, 10, False),
            ("Leche Entera 1L", "Lacteos", "7790895003015", 1180, 18, 12, False),
            ("Yogur Vainilla 1L", "Lacteos", "7790895003022", 1650, 14, 8, False),
            ("Queso Cremoso kg", "Lacteos", "7790895003039", 6200, 8.5, 4, True),
            ("Carne Molida kg", "Carnes", "7790895004012", 5400, 10.0, 5, True),
            ("Pollo Entero kg", "Carnes", "7790895004029", 3100, 12.0, 5, True),
            ("Detergente 750ml", "Limpieza", "7790895005019", 1350, 20, 8, False),
            ("Lavandina 1L", "Limpieza", "7790895005026", 950, 22, 8, False),
            ("Papel Higienico x4", "Limpieza", "7790895005033", 1800, 15, 6, False),
            ("Pan Frances kg", "Panaderia", "7790895006016", 1800, 9.0, 4, True),
            ("Medialunas unidad", "Panaderia", "7790895006023", 420, 36, 12, False),
            ("Hamburguesas x4", "Congelados", "7790895007013", 2850, 12, 6, False),
            ("Helado 1kg", "Congelados", "7790895007020", 4300, 8, 4, False),
            ("Chocolate 100g", "Golosinas", "7790895008010", 1250, 18, 8, False),
            ("Caramelos surtidos 500g", "Golosinas", "7790895008027", 1600, 14, 6, False),
            ("Tomate kg", "Verduleria", "7790895009017", 1600, 18.0, 6, True),
            ("Papa kg", "Verduleria", "7790895009024", 850, 28.0, 10, True),
            ("Jamon Cocido kg", "Fiambres", "7790895010013", 7200, 6.5, 3, True),
            ("Salame Picado Fino kg", "Fiambres", "7790895010020", 9800, 4.5, 2, True),
        ]
        ids: dict[str, int] = {}
        for nombre, categoria, codigo, precio, stock, minimo, pesable in specs:
            product_id = self.backend.crear_producto_completo(
                nombre=nombre,
                categoria_id=categorias[categoria],
                codigo_barras=codigo,
                precio=precio,
                stock_inicial=stock,
                stock_minimo=minimo,
                es_pesable=pesable,
                id_usuario=admin_id,
            )
            if not product_id:
                raise RuntimeError(f"No se pudo crear el producto demo {nombre}")
            ids[nombre] = int(product_id)
        return ids

    def _assign_supplier_products(self, proveedores: dict[str, int], productos: dict[str, int]) -> None:
        asignaciones = {
            "Distribuidora Cuyo SRL": [
                "Coca Cola 1.5L", "Agua Mineral 2L", "Jugo Naranja 1L",
                "Arroz Largo Fino 1kg", "Fideos Tallarin 500g", "Aceite Girasol 900ml",
                "Azucar 1kg", "Chocolate 100g", "Caramelos surtidos 500g",
            ],
            "Lacteos Andinos": ["Leche Entera 1L", "Yogur Vainilla 1L", "Queso Cremoso kg", "Jamon Cocido kg", "Salame Picado Fino kg"],
            "Limpieza Total": ["Detergente 750ml", "Lavandina 1L", "Papel Higienico x4", "Hamburguesas x4", "Helado 1kg"],
            "Verduras del Valle": ["Tomate kg", "Papa kg", "Pan Frances kg", "Medialunas unidad", "Carne Molida kg", "Pollo Entero kg"],
        }
        for proveedor, nombres_productos in asignaciones.items():
            for producto in nombres_productos:
                self.backend.asignar_producto_a_proveedor(proveedores[proveedor], productos[producto])

    def _open_admin_treasury(self, admin_id: int) -> int:
        self.backend.abrir_caja_session(admin_id, 500000.0, "administrativa")
        session = self._latest_session_for_user(admin_id, "administrativa")
        return int(session["id_session"])

    def _seed_purchases(self, ctx: DemoContext, admin_session: int) -> None:
        purchase_specs = [
            (-28, "Distribuidora Cuyo SRL", "transferencia", [
                ("Coca Cola 1.5L", 24, 1600, 2350),
                ("Arroz Largo Fino 1kg", 30, 980, 1450),
                ("Fideos Tallarin 500g", 36, 560, 890),
                ("Aceite Girasol 900ml", 18, 1450, 2100),
            ]),
            (-24, "Lacteos Andinos", "cuenta_corriente", [
                ("Leche Entera 1L", 36, 760, 1180),
                ("Yogur Vainilla 1L", 18, 1100, 1650),
                ("Queso Cremoso kg", 12, 4300, 6200),
            ]),
            (-18, "Verduras del Valle", "transferencia", [
                ("Tomate kg", 25, 950, 1600),
                ("Papa kg", 35, 500, 850),
                ("Pan Frances kg", 18, 1100, 1800),
            ]),
            (-12, "Limpieza Total", "cuenta_corriente", [
                ("Detergente 750ml", 24, 900, 1350),
                ("Lavandina 1L", 30, 620, 950),
                ("Papel Higienico x4", 18, 1200, 1800),
            ]),
        ]

        cancelled_purchase: int | None = None
        for day_offset, supplier, method, items in purchase_specs:
            op_dt = self._dt(day_offset, 10, 15)
            purchase_id = self.backend.registrar_compra(
                ctx.usuarios["admin"],
                ctx.proveedores[supplier],
                [
                    {"id": ctx.productos[name], "cant": qty, "costo": cost, "precio_venta": sale_price}
                    for name, qty, cost, sale_price in items
                ],
                medio_pago=method,
            )
            if not purchase_id:
                raise RuntimeError(f"No se pudo registrar compra demo a {supplier}")
            self._date_purchase(int(purchase_id), op_dt)
            if supplier == "Limpieza Total":
                cancelled_purchase = int(purchase_id)

        if cancelled_purchase:
            self.backend.anular_compra(cancelled_purchase, ctx.usuarios["admin"], "Mercaderia recibida con remito duplicado")
            self._date_purchase(cancelled_purchase, self._dt(-11, 9, 40))
            self._date_audit("ANULAR_COMPRA", "Compra", cancelled_purchase, self._dt(-11, 9, 45))

        self._date_session(admin_session, self._dt(-30, 8, 0), None)

    def _seed_sales_days(self, ctx: DemoContext, admin_session: int) -> None:
        days = [
            (-27, "lucia", [
                ("Ana Pereyra", "efectivo", [("Coca Cola 1.5L", 2), ("Fideos Tallarin 500g", 3), ("Chocolate 100g", 2)]),
                (None, "tarjeta", [("Agua Mineral 2L", 2), ("Medialunas unidad", 6)]),
                ("Carlos Molina", "cuenta_corriente", [("Aceite Girasol 900ml", 2), ("Azucar 1kg", 4), ("Leche Entera 1L", 3)]),
            ]),
            (-22, "martin", [
                ("Mariana Ruiz", "transferencia", [("Arroz Largo Fino 1kg", 2), ("Detergente 750ml", 1), ("Lavandina 1L", 2)]),
                ("Despensa El Molino", "cuenta_corriente", [("Coca Cola 1.5L", 8), ("Jugo Naranja 1L", 6), ("Caramelos surtidos 500g", 4)]),
                (None, "efectivo", [("Pan Frances kg", 1.5), ("Jamon Cocido kg", 0.35), ("Queso Cremoso kg", 0.55)]),
            ]),
            (-16, "sofia", [
                ("Roberto Quiroga", "efectivo", [("Carne Molida kg", 1.2), ("Papa kg", 3), ("Tomate kg", 1.5)]),
                ("Comedor Los Pinos", "cuenta_corriente", [("Pollo Entero kg", 4.8), ("Arroz Largo Fino 1kg", 6), ("Aceite Girasol 900ml", 4)]),
                ("Valeria Castro", "tarjeta", [("Yogur Vainilla 1L", 2), ("Helado 1kg", 1), ("Chocolate 100g", 3)]),
            ]),
            (-9, "lucia", [
                ("Nicolas Herrera", "efectivo", [("Hamburguesas x4", 2), ("Papel Higienico x4", 1), ("Agua Mineral 2L", 3)]),
                ("Carlos Molina", "cuenta_corriente", [("Carne Molida kg", 1.4), ("Tomate kg", 2), ("Pan Frances kg", 1)]),
                (None, "transferencia", [("Coca Cola 1.5L", 1), ("Medialunas unidad", 12)]),
            ]),
            (-3, "martin", [
                ("Paula Sosa", "tarjeta", [("Leche Entera 1L", 4), ("Azucar 1kg", 2), ("Fideos Tallarin 500g", 2)]),
                ("Despensa El Molino", "cuenta_corriente", [("Queso Cremoso kg", 2.2), ("Jamon Cocido kg", 1.1), ("Salame Picado Fino kg", 0.7)]),
                (None, "efectivo", [("Detergente 750ml", 1), ("Lavandina 1L", 1), ("Caramelos surtidos 500g", 1)]),
            ]),
        ]

        venta_para_anular: int | None = None
        for day_offset, vendedor, ventas in days:
            vendedor_id = ctx.usuarios[vendedor]
            self.backend.abrir_caja_session(vendedor_id, 25000.0, "turno")
            session = self._latest_session_for_user(vendedor_id, "turno")
            session_id = int(session["id_session"])
            self._date_session(session_id, self._dt(day_offset, 8, 30), None)
            self._date_latest_movement(session_id, self._dt(day_offset, 8, 30))

            for idx, (cliente, medio, items) in enumerate(ventas):
                op_dt = self._dt(day_offset, 9 + idx * 2, 15 + idx * 10)
                sale_id = self.backend.registrar_venta_completa(
                    vendedor_id,
                    ctx.clientes[cliente] if cliente else None,
                    self._sale_items(ctx, items),
                    medio,
                    session_id,
                )
                if not sale_id:
                    raise RuntimeError(f"No se pudo registrar venta demo de {vendedor}")
                self._date_sale(int(sale_id), op_dt)
                if cliente == "Paula Sosa":
                    venta_para_anular = int(sale_id)

            if vendedor == "lucia" and day_offset == -9:
                self.backend.registrar_movimiento_manual(
                    session_id,
                    "egreso",
                    6000.0,
                    "retiro_caja",
                    "Retiro parcial autorizado hacia tesoreria",
                    vendedor_id,
                )
                self._date_latest_movement(session_id, self._dt(day_offset, 14, 5))
                self.backend.transferir_entre_cajas(
                    session_id,
                    admin_session,
                    8000.0,
                    vendedor_id,
                    "transferencia_tesoreria_salida",
                    "transferencia_tesoreria_entrada",
                    "Transferencia de efectivo de turno a tesoreria",
                    ctx.usuarios["supervisor"],
                )
                self._date_latest_movements(2, self._dt(day_offset, 15, 0))

            self._seed_customer_payments_for_day(ctx, vendedor_id, session_id, day_offset)
            resumen = self.backend.obtener_resumen_cierre(session_id)
            esperado = float(resumen.get("efectivo_esperado", 0.0))
            contado = esperado - (150.0 if day_offset == -16 else 0.0)
            self.backend.cerrar_caja_session(
                session_id,
                vendedor_id,
                esperado,
                contado,
                contado - esperado,
                "Cierre demo con arqueo normal" if contado == esperado else "Diferencia menor detectada en arqueo",
            )
            self._date_session(session_id, self._dt(day_offset, 8, 30), self._dt(day_offset, 17, 20))
            self._date_audit("CIERRE_CAJA", "caja_session", session_id, self._dt(day_offset, 17, 25))

        if venta_para_anular:
            self.backend.anular_venta(venta_para_anular, ctx.usuarios["supervisor"], "Cliente informo error en medio de pago")
            self._date_sale(venta_para_anular, self._dt(-2, 11, 10))
            self._date_audit("ANULAR_VENTA", "Venta", venta_para_anular, self._dt(-2, 11, 15))

    def _seed_customer_payments_for_day(self, ctx: DemoContext, vendedor_id: int, session_id: int, day_offset: int) -> None:
        pagos = {
            -16: [("Carlos Molina", 9000.0, "efectivo", 15, 20)],
            -9: [("Despensa El Molino", 14000.0, "transferencia", 13, 35)],
            -3: [("Comedor Los Pinos", 18000.0, "efectivo", 14, 10)],
        }.get(day_offset, [])
        for cliente, monto, metodo, hour, minute in pagos:
            cuenta = self.backend.obtener_cuenta_por_cliente(ctx.clientes[cliente])
            if not cuenta:
                raise RuntimeError(f"No existe cuenta corriente para {cliente}")
            self.backend.registrar_pago_cuenta_corriente(int(cuenta["id_cuenta"]), monto, metodo, vendedor_id)
            self._date_latest_payment(ctx.clientes[cliente], session_id, self._dt(day_offset, hour, minute))

    def _seed_history_exports(self, ctx: DemoContext) -> None:
        exports = [
            (ctx.usuarios["admin"], -7, "EXPORTAR_HISTORIAL", "Venta", {"reporte": "ventas", "rango": "ultimos_30_dias"}),
            (ctx.usuarios["supervisor"], -4, "EXPORTAR_HISTORIAL", "caja_movimiento", {"reporte": "caja", "rango": "semana"}),
            (ctx.usuarios["admin"], -1, "EXPORTAR_HISTORIAL", "AuditoriaAcciones", {"reporte": "auditoria", "formato": "csv"}),
        ]
        for user_id, day_offset, action, table, data in exports:
            self.DB.registrar_auditoria(user_id, action, table, None, None, data)
            self._date_latest_audit(action, self._dt(day_offset, 16, 45))

    def _close_admin_treasury(self, admin_session: int, admin_id: int) -> None:
        resumen = self.backend.obtener_resumen_cierre(admin_session)
        esperado = float(resumen.get("efectivo_esperado", 0.0))
        self.backend.cerrar_caja_session(
            admin_session,
            admin_id,
            esperado,
            esperado,
            0.0,
            "Cierre de tesoreria demo luego de carga historica",
        )
        self._date_session(admin_session, self._dt(-30, 8, 0), self._dt(-1, 18, 30))
        self._date_audit("CIERRE_CAJA", "caja_session", admin_session, self._dt(-1, 18, 35))

    def _sale_items(self, ctx: DemoContext, items: list[tuple[str, float]]) -> list[tuple[int, str, float, float, str]]:
        products = self._products_by_id()
        sale_items: list[tuple[int, str, float, float, str]] = []
        for name, qty in items:
            product_id = ctx.productos[name]
            product = products[product_id]
            sale_items.append((product_id, name, float(qty), float(product["precio"]), product["codigo_barras"] or ""))
        return sale_items

    def _products_by_id(self) -> dict[int, dict[str, Any]]:
        return {int(p["id_producto"]): p for p in self.backend.obtener_productos()}

    def _latest_session_for_user(self, user_id: int, tipo_caja: str) -> dict[str, Any]:
        conn = self._connect()
        cur = conn.cursor(dictionary=True)
        try:
            cur.execute(
                """
                SELECT * FROM caja_session
                WHERE id_usuario_apertura=%s AND tipo_caja=%s
                ORDER BY id_session DESC LIMIT 1
                """,
                (user_id, tipo_caja),
            )
            row = cur.fetchone()
            if not row:
                raise RuntimeError(f"No hay caja {tipo_caja} para usuario {user_id}")
            return row
        finally:
            cur.close()
            conn.close()

    def _load_ids(self, table: str, id_col: str, name_col: str) -> dict[str, int]:
        conn = self._connect()
        cur = conn.cursor()
        try:
            cur.execute(f"SELECT {id_col}, {name_col} FROM {table}")
            return {str(name): int(row_id) for row_id, name in cur.fetchall()}
        finally:
            cur.close()
            conn.close()

    def _dt(self, day_offset: int, hour: int, minute: int) -> datetime:
        return self.today + timedelta(days=day_offset, hours=hour, minutes=minute)

    def _date_purchase(self, purchase_id: int, dt: datetime) -> None:
        self._execute(
            "UPDATE Compra SET fecha=%s WHERE id_compra=%s",
            (dt, purchase_id),
            "UPDATE caja_movimiento SET fecha_hora=%s WHERE id_compra=%s",
            (dt + timedelta(minutes=3), purchase_id),
            "UPDATE AuditoriaInventario SET fecha=%s WHERE tipo_movimiento='compra' AND id_referencia=%s",
            (dt + timedelta(minutes=2), purchase_id),
        )

    def _date_sale(self, sale_id: int, dt: datetime) -> None:
        self._execute(
            "UPDATE Venta SET fecha=%s WHERE id_venta=%s",
            (dt, sale_id),
            "UPDATE caja_movimiento SET fecha_hora=%s WHERE id_venta=%s",
            (dt + timedelta(minutes=1), sale_id),
            "UPDATE AuditoriaInventario SET fecha=%s WHERE tipo_movimiento='venta' AND id_referencia=%s",
            (dt + timedelta(minutes=1), sale_id),
        )

    def _date_session(self, session_id: int, opened_at: datetime, closed_at: datetime | None) -> None:
        self._execute(
            """
            UPDATE caja_session
            SET fecha_apertura=%s, fecha_cierre=%s
            WHERE id_session=%s
            """,
            (opened_at, closed_at, session_id),
        )

    def _date_latest_movement(self, session_id: int, dt: datetime) -> None:
        self._execute(
            """
            UPDATE caja_movimiento
            SET fecha_hora=%s
            WHERE id_movimiento=(
                SELECT id_movimiento FROM (
                    SELECT id_movimiento FROM caja_movimiento
                    WHERE id_session=%s
                    ORDER BY id_movimiento DESC LIMIT 1
                ) x
            )
            """,
            (dt, session_id),
        )

    def _date_latest_movements(self, count: int, dt: datetime) -> None:
        conn = self._connect()
        cur = conn.cursor()
        try:
            cur.execute("SELECT id_movimiento FROM caja_movimiento ORDER BY id_movimiento DESC LIMIT %s", (count,))
            ids = [row[0] for row in cur.fetchall()]
            for idx, mov_id in enumerate(ids):
                cur.execute(
                    "UPDATE caja_movimiento SET fecha_hora=%s WHERE id_movimiento=%s",
                    (dt + timedelta(minutes=idx), mov_id),
                )
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cur.close()
            conn.close()

    def _date_latest_payment(self, client_id: int, session_id: int, dt: datetime) -> None:
        self._execute(
            """
            UPDATE Pago
            SET fecha=%s
            WHERE id_pago=(
                SELECT id_pago FROM (
                    SELECT p.id_pago
                    FROM Pago p
                    JOIN CuentaCorriente cc ON cc.id_cuenta=p.id_cuenta
                    WHERE cc.id_cliente=%s
                    ORDER BY p.id_pago DESC LIMIT 1
                ) x
            )
            """,
            (dt, client_id),
            """
            UPDATE caja_movimiento
            SET fecha_hora=%s
            WHERE id_movimiento=(
                SELECT id_movimiento FROM (
                    SELECT id_movimiento FROM caja_movimiento
                    WHERE id_session=%s AND id_cliente=%s
                    ORDER BY id_movimiento DESC LIMIT 1
                ) y
            )
            """,
            (dt + timedelta(minutes=1), session_id, client_id),
        )

    def _date_audit(self, action: str, table: str, record_id: int, dt: datetime) -> None:
        self._execute(
            """
            UPDATE AuditoriaAcciones
            SET fecha=%s
            WHERE accion=%s AND tabla_afectada=%s AND id_registro=%s
            """,
            (dt, action, table, record_id),
        )

    def _date_latest_audit(self, action: str, dt: datetime) -> None:
        self._execute(
            """
            UPDATE AuditoriaAcciones
            SET fecha=%s
            WHERE id_auditoria=(
                SELECT id_auditoria FROM (
                    SELECT id_auditoria FROM AuditoriaAcciones
                    WHERE accion=%s
                    ORDER BY id_auditoria DESC LIMIT 1
                ) x
            )
            """,
            (dt, action),
        )

    def _age_master_data(self, ctx: DemoContext) -> None:
        base = self._dt(-30, 7, 30)
        self._execute(
            "UPDATE Usuario SET fecha_creacion=%s, ultimo_acceso=NULL, token_sesion=NULL, token_timestamp=NULL",
            (base,),
            "UPDATE Cliente SET fecha_registro=%s",
            (base + timedelta(hours=1),),
            "UPDATE Proveedor SET fecha_registro=%s",
            (base + timedelta(hours=2),),
            "UPDATE Producto SET fecha_creacion=%s",
            (base + timedelta(hours=3),),
            "UPDATE Categoria SET fecha_creacion=%s",
            (base,),
            "UPDATE Inventario SET ultima_actualizacion=%s",
            (self._dt(-1, 12, 0),),
        )
        self._date_latest_audit("CREAR_USUARIO", base + timedelta(minutes=10))

    def _verify_counts(self) -> dict[str, int]:
        conn = self._connect()
        cur = conn.cursor()
        checks = {
            "usuarios": "SELECT COUNT(*) FROM Usuario",
            "clientes": "SELECT COUNT(*) FROM Cliente",
            "proveedores": "SELECT COUNT(*) FROM Proveedor",
            "productos": "SELECT COUNT(*) FROM Producto",
            "compras": "SELECT COUNT(*) FROM Compra",
            "ventas": "SELECT COUNT(*) FROM Venta",
            "pagos": "SELECT COUNT(*) FROM Pago",
            "cajas": "SELECT COUNT(*) FROM caja_session",
            "movimientos_caja": "SELECT COUNT(*) FROM caja_movimiento",
            "clientes_con_deuda": "SELECT COUNT(*) FROM CuentaCorriente WHERE saldo < 0",
            "auditoria": "SELECT COUNT(*) FROM AuditoriaAcciones",
            "inventario": "SELECT COUNT(*) FROM Inventario",
        }
        try:
            result: dict[str, int] = {}
            for key, sql in checks.items():
                cur.execute(sql)
                result[key] = int(cur.fetchone()[0])
            required = {
                "usuarios": 5,
                "clientes": 8,
                "proveedores": 4,
                "productos": 20,
                "compras": 4,
                "ventas": 12,
                "pagos": 3,
                "cajas": 5,
                "movimientos_caja": 20,
                "clientes_con_deuda": 2,
                "auditoria": 10,
                "inventario": 20,
            }
            missing = [f"{key}={result[key]}(<{minimum})" for key, minimum in required.items() if result[key] < minimum]
            if missing:
                raise RuntimeError("La verificacion demo fallo: " + ", ".join(missing))
            return result
        finally:
            cur.close()
            conn.close()

    def _execute(self, *sql_and_params: Any) -> None:
        if len(sql_and_params) % 2 != 0:
            raise ValueError("_execute requiere pares sql, params")
        conn = self._connect()
        cur = conn.cursor()
        try:
            for idx in range(0, len(sql_and_params), 2):
                cur.execute(sql_and_params[idx], sql_and_params[idx + 1])
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cur.close()
            conn.close()


def run_demo_seed() -> dict[str, int]:
    return DemoSeeder().run()
