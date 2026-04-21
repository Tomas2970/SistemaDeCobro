import re

def patch():
    with open('app/frontend/interfaz_historiales.py', 'r', encoding='utf-8') as f:
        code = f.read()

    # Imports
    code = re.sub(r'import tkinter as tk\nfrom tkinter import ttk', 'import tkinter as tk\nimport customtkinter as ctk\nfrom tkinter import ttk\nfrom app.frontend.theme_config import THEME_COLORS, get_color, aplicar_tema_ventana, configurar_estilo_notebook, configurar_estilo_treeview', code)

    # Toplevel
    code = code.replace('self.win = tk.Toplevel(parent)', 'self.win = ctk.CTkToplevel(parent)')
    code = code.replace('self.win.config(bg="#f4f4f8")', 'aplicar_tema_ventana(self.win)')

    # Notebook
    code = code.replace('self.notebook = ttk.Notebook(self.win)', 'configurar_estilo_notebook()\n        self.notebook = ttk.Notebook(self.win, style="Custom.TNotebook")')
    
    # Header
    code = code.replace('frm_header = tk.Frame(self.win, bg="#3b82f6", pady=15)', 'frm_header = ctk.CTkFrame(self.win, fg_color=get_color("accent_primary"), corner_radius=0)')
    code = code.replace('tk.Label(frm_header, text="HISTORIALES DEL SISTEMA", \n                 font=("Segoe UI", 16, "bold"), fg="white", bg="#3b82f6").pack()', 'ctk.CTkLabel(frm_header, text="HISTORIALES DEL SISTEMA", font=("Segoe UI", 18, "bold"), text_color="white").pack(pady=15)')

    # Footer
    code = code.replace('frm_footer = tk.Frame(self.win, bg="#f4f4f8", pady=8)', 'frm_footer = ctk.CTkFrame(self.win, fg_color="transparent")')
    code = code.replace('tk.Button(frm_footer, text="Cerrar", command=self.win.destroy,\n                  bg="#64748b", fg="white", font=("Segoe UI", 10),\n                  relief="flat", padx=20, pady=6, cursor="hand2").pack(side=tk.RIGHT)', 'ctk.CTkButton(frm_footer, text="Cerrar", command=self.win.destroy, fg_color=get_color("button_secondary"), hover_color=get_color("button_secondary_hover"), font=("Segoe UI", 13, "bold"), width=120).pack(side=tk.RIGHT, pady=10)')

    # Tabs frm
    code = re.sub(r'frm = tk\.Frame\(self\.tab_([a-z]+), bg="#f4f4f8", padx=10, pady=10\)\s*frm\.pack\(fill=tk\.X\)', 
                  r'frm = ctk.CTkFrame(self.tab_\1, fg_color="transparent")\n        frm.pack(fill="x", padx=10, pady=10)', code)

    # Labels "Rango:", "Desde:", "Hasta:"
    code = re.sub(r'tk\.Label\(frm, text="Rango:", bg="#f4f4f8", font=\("bold", 9\)\)', 
                  r'ctk.CTkLabel(frm, text="Rango:", font=("Segoe UI", 13, "bold"), text_color=get_color("text_primary"))', code)
    code = re.sub(r'tk\.Label\(frm, text="Desde:", bg="#f4f4f8"\)', 
                  r'ctk.CTkLabel(frm, text="Desde:", font=("Segoe UI", 13, "bold"), text_color=get_color("text_primary"))', code)
    code = re.sub(r'tk\.Label\(frm, text="Hasta:", bg="#f4f4f8"\)', 
                  r'ctk.CTkLabel(frm, text="Hasta:", font=("Segoe UI", 13, "bold"), text_color=get_color("text_primary"))', code)

    for label in ["Vendedor:", "Cliente:", "Proveedor:", "Usuario:", "Registró:", "Mostrar:"]:
        code = code.replace(f'tk.Label(frm, text="{label}", bg="#f4f4f8")', 
                            f'ctk.CTkLabel(frm, text="{label}", font=("Segoe UI", 13, "bold"), text_color=get_color("text_primary"))')

    # Button Factory
    code = re.sub(
        r'def crear_boton_accion\(self, parent, text, command, color, width=12\):.*?return btn',
        r'''def crear_boton_accion(self, parent, text, command, color, width=12):
        return ctk.CTkButton(parent, text=text, command=command, fg_color=color, hover_color=self._darken_color(color), width=width*8, font=("Segoe UI", 13, "bold"), cursor="hand2")''',
        code, flags=re.DOTALL
    )

    # Treeview Styles removal (delegating to configurar_estilo_treeview)
    code = re.sub(
        r'style\.configure\("Modern\.Treeview"[\s\S]*?\[\(\'active\', \'#e5e7eb\'\)\]\)',
        'configurar_estilo_treeview()',
        code
    )

    with open('app/frontend/interfaz_historiales.py', 'w', encoding='utf-8') as f:
        f.write(code)

if __name__ == "__main__":
    patch()
