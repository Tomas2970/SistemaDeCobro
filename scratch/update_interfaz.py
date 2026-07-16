import sys

path = r'c:\Users\Tomas\Documents\GitHub\SistemaDeCobro\SistemaDeCobro\app\frontend\interfaz_historiales.py'
with open(path, 'r', encoding='utf-8') as f:
    c = f.read()

target1 = '''                vends = self.backend.obtener_vendedores() or []
                clis = self.backend.listar_clientes() or []'''
repl1 = '''                vends = self.backend.obtener_vendedores() or []
                comps = self.backend.obtener_compradores() or []
                ops = self.backend.obtener_usuarios_operativos() or []
                clis = self.backend.listar_clientes() or []'''

target2 = '''                    self.vendedores_raw = vends
                    self.clientes_raw = clis'''
repl2 = '''                    self.vendedores_raw = vends
                    self.compradores_raw = comps
                    self.usuarios_operativos_raw = ops
                    self.clientes_raw = clis'''

# Now we must update the dropdowns in Compras, Pagos, Caja
target3 = '''command=lambda: self._abrir_selector_entidad("Vendedor", self.usuario_c_sel, self.vendedores_raw, self.lbl_usuario_c))'''
repl3 = '''command=lambda: self._abrir_selector_entidad("Usuario", self.usuario_c_sel, self.compradores_raw, self.lbl_usuario_c))'''

target4 = '''command=lambda: self._abrir_selector_entidad("Usuario", self.usuario_p_sel, self.vendedores_raw, self.lbl_usuario_p))'''
repl4 = '''command=lambda: self._abrir_selector_entidad("Usuario", self.usuario_p_sel, self.usuarios_operativos_raw, self.lbl_usuario_p))'''

target5 = '''command=lambda: self._abrir_selector_entidad("Usuario", self.usuario_caja_sel, self.vendedores_raw, self.lbl_usuario_cj))'''
repl5 = '''command=lambda: self._abrir_selector_entidad("Usuario", self.usuario_caja_sel, self.usuarios_operativos_raw, self.lbl_usuario_cj))'''

# Also change the label from "Vendedor:" to "Usuario:" in Compras if it's there
# Wait, let's see how it was defined in Compras tab
target6 = '''        ctk.CTkLabel(frm, text="Vendedor:", font=("Segoe UI", 12, "bold"), text_color=get_color("text_primary")).grid(row=0, column=8, padx=(10, 3), sticky="e")'''
repl6 = '''        ctk.CTkLabel(frm, text="Usuario:", font=("Segoe UI", 12, "bold"), text_color=get_color("text_primary")).grid(row=0, column=8, padx=(10, 3), sticky="e")'''

# And Compras columns might include "Vendedor", change it to "Usuario"
target7 = '''cols = ("ID", "Fecha", "Empresa", "CUIT", "Total", "Estado", "Pago", "Vendedor")'''
repl7 = '''cols = ("ID", "Fecha", "Empresa", "CUIT", "Total", "Estado", "Pago", "Usuario")'''

target8 = '''self.tree_maestro_c.configure(displaycolumns=("Fecha", "Empresa", "CUIT", "Total", "Estado", "Pago", "Vendedor"))'''
repl8 = '''self.tree_maestro_c.configure(displaycolumns=("Fecha", "Empresa", "CUIT", "Total", "Estado", "Pago", "Usuario"))'''

c = c.replace(target1, repl1)
c = c.replace(target2, repl2)
c = c.replace(target3, repl3)
c = c.replace(target4, repl4)
c = c.replace(target5, repl5)
c = c.replace(target6, repl6)
c = c.replace(target7, repl7)
c = c.replace(target8, repl8)

with open(path, 'w', encoding='utf-8') as f:
    f.write(c)
print('interfaz_historiales.py updated')
