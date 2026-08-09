import sys

path = r'c:\Users\Tomas\Documents\GitHub\SistemaDeCobro\SistemaDeCobro\app\database\DB.py'
with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
in_obtener_vendedores = False
skip_next = False
for line in lines:
    if skip_next:
        skip_next = False
        continue
    
    if line.startswith('def obtener_vendedores() -> list[dict]:'):
        # Insert all three methods
        new_lines.append(line)
        new_lines.append('    conn = cur = None\n')
        new_lines.append('    try:\n')
        new_lines.append('        conn = conectar()\n')
        new_lines.append('        cur = conn.cursor(dictionary=True)\n')
        new_lines.append('        cur.execute(\n')
        new_lines.append('            """\n')
        new_lines.append('            SELECT u.id_usuario, u.nombre\n')
        new_lines.append('            FROM Usuario u\n')
        new_lines.append('            WHERE u.activo = 1 AND u.id_rol = 2\n')
        new_lines.append('            ORDER BY u.nombre\n')
        new_lines.append('            """\n')
        new_lines.append('        )\n')
        new_lines.append('        return list(cur.fetchall() or [])\n')
        new_lines.append('    except Exception as e:\n')
        new_lines.append('        logger.error(f"obtener_vendedores: {e}")\n')
        new_lines.append('        return []\n')
        new_lines.append('\n')
        
        new_lines.append('def obtener_compradores() -> list[dict]:\n')
        new_lines.append('    conn = cur = None\n')
        new_lines.append('    try:\n')
        new_lines.append('        conn = conectar()\n')
        new_lines.append('        cur = conn.cursor(dictionary=True)\n')
        new_lines.append('        cur.execute(\n')
        new_lines.append('            """\n')
        new_lines.append('            SELECT u.id_usuario, u.nombre\n')
        new_lines.append('            FROM Usuario u\n')
        new_lines.append('            WHERE u.activo = 1 AND u.id_rol IN (1, 3)\n')
        new_lines.append('            ORDER BY u.nombre\n')
        new_lines.append('            """\n')
        new_lines.append('        )\n')
        new_lines.append('        return list(cur.fetchall() or [])\n')
        new_lines.append('    except Exception as e:\n')
        new_lines.append('        logger.error(f"obtener_compradores: {e}")\n')
        new_lines.append('        return []\n')
        new_lines.append('\n')
        
        new_lines.append('def obtener_usuarios_operativos() -> list[dict]:\n')
        new_lines.append('    conn = cur = None\n')
        new_lines.append('    try:\n')
        new_lines.append('        conn = conectar()\n')
        new_lines.append('        cur = conn.cursor(dictionary=True)\n')
        new_lines.append('        cur.execute(\n')
        new_lines.append('            """\n')
        new_lines.append('            SELECT u.id_usuario, u.nombre\n')
        new_lines.append('            FROM Usuario u\n')
        new_lines.append('            WHERE u.activo = 1 AND u.id_rol IN (1, 2, 3)\n')
        new_lines.append('            ORDER BY u.nombre\n')
        new_lines.append('            """\n')
        new_lines.append('        )\n')
        new_lines.append('        return list(cur.fetchall() or [])\n')
        new_lines.append('    except Exception as e:\n')
        new_lines.append('        logger.error(f"obtener_usuarios_operativos: {e}")\n')
        new_lines.append('        return []\n')
        
        in_obtener_vendedores = True
    elif in_obtener_vendedores:
        if line.startswith('def '):
            in_obtener_vendedores = False
            new_lines.append(line)
    else:
        new_lines.append(line)

with open(path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
print('DB.py updated')
