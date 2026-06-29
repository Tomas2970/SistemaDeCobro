import sys
sys.path.append('.')
from dotenv import load_dotenv
load_dotenv()
import mysql.connector
import os

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = int(os.getenv('DB_PORT', '3307'))
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')
DB_NAME = os.getenv('DB_NAME', 'supermercado_don_atilio')

print("Dropping DB...")
conn = mysql.connector.connect(host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASSWORD)
cur = conn.cursor()
cur.execute(f'DROP DATABASE IF EXISTS {DB_NAME}')
cur.execute(f'CREATE DATABASE {DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci')
cur.close()
conn.close()
print('DB dropped and created.')

mysql_exe = os.path.join('mysql', 'bin', 'mysql.exe')
if not os.path.exists(mysql_exe):
    mysql_exe = 'mysql'
cmd = f'"{mysql_exe}" -h {DB_HOST} -P {DB_PORT} -u {DB_USER} '
if DB_PASSWORD:
    cmd += f'-p"{DB_PASSWORD}" '
cmd += f'{DB_NAME} < app\\database\\schema.sql'
res = os.system(cmd)
print('schema.sql executed with code:', res)

from app.database import auto_migrate
auto_migrate.ejecutar_migraciones()
print('auto_migrate executed.')

from app.tools import seed_initial_data
seed_initial_data.main()
print('seed_initial_data executed.')
