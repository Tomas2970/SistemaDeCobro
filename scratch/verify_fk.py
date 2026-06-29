import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = int(os.getenv('DB_PORT', '3307'))
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')
DB_NAME = os.getenv('DB_NAME', 'supermercado_don_atilio')

conn = mysql.connector.connect(host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASSWORD, database=DB_NAME)
cur = conn.cursor(dictionary=True)

tables_to_check = ['Compra', 'caja_session', 'caja_movimiento', 'nota_credito']

for tbl in tables_to_check:
    print(f"\\n--- Verifying Table: {tbl} ---")
    
    # Check Engine
    cur.execute("SELECT ENGINE FROM information_schema.TABLES WHERE TABLE_SCHEMA=%s AND TABLE_NAME=%s", (DB_NAME, tbl))
    engine_row = cur.fetchone()
    if engine_row:
        print(f"ENGINE: {engine_row['ENGINE']}")
    else:
        print("TABLE NOT FOUND IN information_schema.TABLES!")
        
    # Check FKs
    query = """
    SELECT 
        CONSTRAINT_NAME, 
        COLUMN_NAME, 
        REFERENCED_TABLE_NAME, 
        REFERENCED_COLUMN_NAME
    FROM information_schema.KEY_COLUMN_USAGE
    WHERE TABLE_SCHEMA=%s AND TABLE_NAME=%s AND REFERENCED_TABLE_NAME IS NOT NULL
    """
    cur.execute(query, (DB_NAME, tbl))
    fks = cur.fetchall()
    if not fks:
        print("NO FOREIGN KEYS FOUND.")
    else:
        for fk in fks:
            print(f"FK: {fk['CONSTRAINT_NAME']} -> Column {fk['COLUMN_NAME']} references {fk['REFERENCED_TABLE_NAME']}({fk['REFERENCED_COLUMN_NAME']})")
    
    # Just to be 100% sure the FKs are correctly formed, let's verify if referenced tables and columns exist and match type
    for fk in fks:
        cur.execute("SELECT COLUMN_TYPE FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=%s AND TABLE_NAME=%s AND COLUMN_NAME=%s", (DB_NAME, fk['REFERENCED_TABLE_NAME'], fk['REFERENCED_COLUMN_NAME']))
        ref_type = cur.fetchone()['COLUMN_TYPE']
        
        cur.execute("SELECT COLUMN_TYPE FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=%s AND TABLE_NAME=%s AND COLUMN_NAME=%s", (DB_NAME, tbl, fk['COLUMN_NAME']))
        col_type = cur.fetchone()['COLUMN_TYPE']
        
        print(f"  Validating Type Match: {tbl}.{fk['COLUMN_NAME']} ({col_type}) == {fk['REFERENCED_TABLE_NAME']}.{fk['REFERENCED_COLUMN_NAME']} ({ref_type}) -> {'OK' if col_type == ref_type else 'MISMATCH'}")

cur.close()
conn.close()
