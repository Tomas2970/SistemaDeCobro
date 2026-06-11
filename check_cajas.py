import mysql.connector

conn = mysql.connector.connect(
    host='localhost',
    port=3307,
    user='root',
    password='',
    database='supermercado_don_atilio'
)
cur = conn.cursor(dictionary=True)

# 1. Consultar sesiones abiertas
cur.execute("SELECT cs.id_session, cs.estado, cs.id_usuario_apertura, cs.fecha_apertura FROM caja_session cs WHERE cs.estado = 'abierta'")
rows = cur.fetchall()
print(f"=== Sesiones con estado 'abierta': {len(rows)} ===")
for r in rows:
    print(r)

# 2. Consultar TODAS las sesiones recientes para ver estados
print("\n=== Últimas 10 sesiones (cualquier estado) ===")
cur.execute("SELECT cs.id_session, cs.estado, cs.id_usuario_apertura, cs.fecha_apertura, cs.fecha_cierre FROM caja_session cs ORDER BY cs.id_session DESC LIMIT 10")
rows2 = cur.fetchall()
for r in rows2:
    print(r)

cur.close()
conn.close()
