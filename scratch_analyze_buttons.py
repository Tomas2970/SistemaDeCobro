import os
import re
import sys
import codecs

sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

files_to_check = [
    "interfaz_venta.py",
    "interfaz_caja.py",
    "interfaz_caja_operativa.py",
    "interfaz_gestion_clientes.py",
    "interfaz_gestion_proveedores.py",
    "interfaz_productos.py",
    "interfaz_inventario.py",
    "interfaz_historiales.py",
    "interfaz_reportes.py",
    "interfaz_auditoria.py",
    "interfaz_gestion_usuarios.py",
    "interfaz_compra.py",
    "interfaz_cuenta_corriente.py",
    "interfaz_categorias.py"
]

frontend_dir = r"c:\Users\Tomas\Documents\GitHub\SistemaDeCobro\SistemaDeCobro\app\frontend"

for f in files_to_check:
    path = os.path.join(frontend_dir, f)
    if not os.path.exists(path):
        print(f"NOT FOUND: {f}")
        continue
    with open(path, "r", encoding="utf-8") as file:
        content = file.read()
        
    buttons = re.findall(r'CTkButton[^>]*?text\s*=\s*[\'"]([^\'"]+)[\'"]', content, re.IGNORECASE)
    buttons += re.findall(r'Button[^>]*?text\s*=\s*[\'"]([^\'"]+)[\'"]', content, re.IGNORECASE)
    
    close_btns = [b for b in buttons if "cerrar" in b.lower() or "salir" in b.lower()]
    
    if close_btns:
        print(f"OK: {f} has {close_btns}")
    else:
        print(f"MISSING: {f} (Buttons found: {list(set(buttons))})")
