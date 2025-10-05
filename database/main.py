from DB import obtener_inventario, insertar_venta, insertar_detalle_venta

# Ver inventario antes
print("Inventario inicial:", obtener_inventario())

# Registrar una venta de cliente 1 con usuario 2
id_venta = insertar_venta(2, 1)

# Vender 2 Yerbas (id_producto=1, precio=1800)
insertar_detalle_venta(id_venta, 1, 2, 1800)

# Ver inventario después
print("Inventario actualizado:", obtener_inventario())
