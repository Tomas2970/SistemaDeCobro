import os
import re

file_path = 'app/frontend/interfaz_reportes.py'
out_path = 'app/frontend/interfaz_caja_operativa.py'

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

out_lines = []
in_reports_func = False
in_selector_func = False

for line in lines:
    if line.startswith('def _crear_selector_entidad_reportes('):
        in_selector_func = True
    elif in_selector_func and line.startswith('def '):
        in_selector_func = False

    if line.startswith('def _construir_panel_reportes('):
        in_reports_func = True
    elif in_reports_func and line.startswith('def '):
        in_reports_func = False

    if not in_reports_func and not in_selector_func:
        out_lines.append(line)

new_code = "".join(out_lines)

# Rename the main function
new_code = new_code.replace('def ui_reportes(parent: tk.Misc, backend, usuario: dict, modo_vista: str = \'caja\'):', 'def ui_caja_operativa(parent: tk.Misc, backend, usuario: dict):')

# Remove the 'if modo_vista == "caja":' wrapping and 'else:' block entirely by regex
# We will just do a simple string replace for the header and then we'll find the logic
new_code = re.sub(
    r"    if modo_vista == 'caja':\n(.*?)    else:\n        win.title\(\"📊 Reportes de Ventas\"\)\n.*?_construir_panel_reportes\(win, backend, usuario\)\n",
    r"\1",
    new_code,
    flags=re.DOTALL
)

# Fix indentation of the extracted block
def unindent_block(match):
    lines = match.group(0).split('\n')
    unindented = []
    for l in lines:
        if l.startswith('    '):
            unindented.append(l[4:])
        else:
            unindented.append(l)
    return '\n'.join(unindented)

new_code = re.sub(
    r"        if usuario\.get\('id_rol'\) == 1:.*?(?=\n    configurar_navegacion_ventana\(win\))",
    unindent_block,
    new_code,
    flags=re.DOTALL
)

# Update internal self-reference
new_code = new_code.replace('ui_reportes(parent', 'ui_caja_operativa(parent')
new_code = new_code.replace('# app/frontend/interfaz_reportes.py', '# app/frontend/interfaz_caja_operativa.py')

with open(out_path, 'w', encoding='utf-8') as f:
    f.write(new_code)

print("Extraction completed.")
