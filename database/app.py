from flask import Flask, request, jsonify
from DB import (
    obtener_clientes, insertar_cliente,
    obtener_productos, insertar_producto,
    actualizar_stock, obtener_inventario,
    insertar_venta, insertar_detalle_venta
)

app = Flask(__name__)

# -----------------------
# Clientes
# -----------------------
@app.route("/clientes", methods=["GET"])
def listar_clientes():
    return jsonify(obtener_clientes())

@app.route("/clientes", methods=["POST"])
def agregar_cliente():
    data = request.json
    insertar_cliente(
        data["nombre"],
        data.get("direccion", ""),
        data.get("telefono", ""),
        data.get("email", "")
    )
    return jsonify({"mensaje": "Cliente agregado"}), 201

# -----------------------
# Productos
# -----------------------
@app.route("/productos", methods=["GET"])
def listar_productos():
    return jsonify(obtener_productos())

@app.route("/productos", methods=["POST"])
def agregar_producto_api():
    data = request.json
    insertar_producto(
        data["nombre"],
        data["precio"],
        data["id_categoria"]
    )
    return jsonify({"mensaje": "Producto agregado"}), 201

# -----------------------
# Inventario
# -----------------------
@app.route("/inventario", methods=["GET"])
def listar_inventario():
    inventario = obtener_inventario()
    # Convertir a lista de dicts si es necesario
    return jsonify([{"nombre": i[0], "cantidad": i[1], "stock_minimo": i[2]} for i in inventario])

@app.route("/inventario", methods=["PUT"])
def actualizar_stock_api():
    data = request.json
    actualizar_stock(data["id_producto"], data["cantidad"])
    return jsonify({"mensaje": "Stock actualizado"}), 200

# -----------------------
# Ventas
# -----------------------
@app.route("/ventas", methods=["POST"])
def registrar_venta():
    data = request.json
    id_venta = insertar_venta(data["id_usuario"], data["id_cliente"])
    for item in data["productos"]:
        insertar_detalle_venta(
            id_venta,
            item["id_producto"],
            item["cantidad"],
            item["precio_unitario"]
        )
    return jsonify({"mensaje": "Venta registrada", "id_venta": id_venta}), 201

# -----------------------
# Corriendo el backend
# -----------------------
if __name__ == "__main__":
    app.run(debug=True)
