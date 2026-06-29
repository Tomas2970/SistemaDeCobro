import sys; sys.path.append('.')
from app.database import DB
conn = DB.conectar()
cur = conn.cursor()
cur.execute("UPDATE Usuario SET token_sesion = NULL")
conn.commit()
print('Todas las sesiones fueron cerradas forzosamente.')
