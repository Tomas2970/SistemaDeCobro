import sys; sys.path.append('.')
from app.database.backend_adapter import BackendAdapter
from app.database import DB

adapter = BackendAdapter()
print('DB Connected.')

user = adapter.verificar_contraseña('admin', 'admin123')
print('Login result:', user)

if user:
    try:
        conn = DB.conectar()

        cur = conn.cursor()
        cur.execute("INSERT INTO Proveedor (nombre, empresa, cuit, activo) VALUES ('Test Proveedor', 'Test SRL', '20-12345678-9', 1)")
        conn.commit()
        id_proveedor = cur.lastrowid
        print(f'Test proveedor created: {id_proveedor}')
        
        productos = [] 
        cur.execute("INSERT INTO Compra (id_proveedor, total, id_usuario, estado, medio_pago) VALUES (%s, %s, %s, %s, %s)", (id_proveedor, 0.0, 1, 'pendiente', 'efectivo'))
        id_compra = cur.lastrowid
        conn.commit()
        print(f'Test purchase created: id_compra={id_compra}')
        
    except Exception as e:
        print('Error creating purchase:', e)



