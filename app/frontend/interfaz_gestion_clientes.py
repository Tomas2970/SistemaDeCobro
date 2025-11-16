# app/frontend/interfaz_gestion_clientes.py
import tkinter as tk
from tkinter import ttk, messagebox

from app.frontend.interfaz_crear_cliente import ui_crear_cliente
from app.frontend.navegacion_teclado_comun import configurar_navegacion_ventana


def ui_gestion_clientes(parent: tk.Misc, backend, usuario: dict):
    win = tk.Toplevel(parent)
    win.title("Gestión de Clientes")
    win.geometry("1100x500")
    win.config(bg="#f4f4f8")
    win.resizable(False, False)

    # ============================
    # Frame: barra superior (búsqueda + checkbox)
    # ============================
    frame_top = tk.Frame(win, bg="#f4f4f8")
    frame_top.pack(fill="x", padx=20, pady=(15, 0))

    tk.Label(frame_top, text="Buscar (Nombre / DNI):", bg="#f4f4f8").pack(side=tk.LEFT)
    var_buscar = tk.StringVar()
    entry_buscar = tk.Entry(frame_top, textvariable=var_buscar, width=30)
    entry_buscar.pack(side=tk.LEFT, padx=(5, 20))

    # Checkbox para mostrar también inactivos
    var_mostrar_inactivos = tk.BooleanVar(value=False)
    chk_inactivos = tk.Checkbutton(
        frame_top,
        text="Mostrar también inactivos",
        variable=var_mostrar_inactivos,
        onvalue=True,
        offvalue=False,
        bg="#f4f4f8",
    )
    chk_inactivos.pack(side=tk.LEFT)

    # ============================
    # Frame: listado (Treeview)
    # ============================
    frame_lista = tk.Frame(win, bg="#f4f4f8")
    frame_lista.pack(pady=10, padx=20, fill="both", expand=True)

    cols = (
        "ID",
        "Nombre",
        "DNI",
        "Teléfono",
        "Email",
        "Activo",
        "Saldo (Deuda)",
        "Límite Crédito",
    )

    tree = ttk.Treeview(frame_lista, columns=cols, show="headings", height=15)
    tree.pack(side="left", fill="both", expand=True)

    ys = ttk.Scrollbar(frame_lista, orient="vertical", command=tree.yview)
    ys.pack(side="right", fill="y")
    tree.configure(yscrollcommand=ys.set)

    for c in cols:
        tree.heading(c, text=c)

    tree.column("ID", width=60, anchor="center")
    tree.column("Nombre", width=220, anchor="w")
    tree.column("DNI", width=100, anchor="center")
    tree.column("Teléfono", width=120, anchor="w")
    tree.column("Email", width=200, anchor="w")
    tree.column("Activo", width=70, anchor="center")
    tree.column("Saldo (Deuda)", width=120, anchor="e")
    tree.column("Límite Crédito", width=120, anchor="e")

    # ============================
    # Funciones auxiliares
    # ============================
    def _normalizar_cliente(c: dict) -> dict:
        """Normaliza el diccionario del cliente a las columnas del Treeview."""
        id_cli = c.get("id_cliente") or c.get("id") or ""
        nombre = c.get("nombre") or ""
        dni = c.get("dni") or ""
        telefono = c.get("telefono") or ""
        email = c.get("email") or ""
        activo = "SI" if c.get("activo") else "NO"
        try:
            saldo = float(c.get("saldo") or 0.0)
        except Exception:
            saldo = 0.0
        try:
            limite = float(c.get("limite_credito") or 0.0)
        except Exception:
            limite = 0.0

        return {
            "ID": id_cli,
            "Nombre": nombre,
            "DNI": dni,
            "Teléfono": telefono,
            "Email": email,
            "Activo": activo,
            "Saldo (Deuda)": saldo,
            "Límite Crédito": limite,
        }

    def _poblar_tree(clientes: list[dict]):
        tree.delete(*tree.get_children())
        for c in clientes:
            n = _normalizar_cliente(c)
            tree.insert(
                "",
                tk.END,
                values=(
                    n["ID"],
                    n["Nombre"],
                    n["DNI"],
                    n["Teléfono"],
                    n["Email"],
                    n["Activo"],
                    f"{n['Saldo (Deuda)']:.2f}",
                    f"{n['Límite Crédito']:.2f}",
                ),
            )

    # ============================
    # Carga / Recarga de datos
    # ============================
    def cargar_datos():
        """Carga la lista completa según el checkbox y el filtro de búsqueda."""
        try:
            incluir_inactivos = var_mostrar_inactivos.get()
            clientes = backend.listar_clientes_con_saldos(
                incluir_inactivos=incluir_inactivos
            )

            filtro = var_buscar.get().strip().lower()
            if filtro:
                filtrados: list[dict] = []
                for c in clientes:
                    nombre = (c.get("nombre") or "").lower()
                    dni = (c.get("dni") or "").lower()
                    if filtro in nombre or filtro in dni:
                        filtrados.append(c)
                clientes = filtrados

            _poblar_tree(clientes)
        except Exception as e:
            messagebox.showerror(
                "Error",
                f"No se pudieron cargar los clientes:\n{e}",
                parent=win,
            )

    # ============================
    # Acciones (botones)
    # ============================
    def accion_recargar():
        var_buscar.set("")
        cargar_datos()

    def _obtener_id_seleccionado() -> int | None:
        sel = tree.selection()
        if not sel:
            return None
        item = sel[0]
        vals = tree.item(item, "values")
        if not vals:
            return None
        try:
            return int(vals[0])
        except Exception:
            return None

    def accion_crear():
        try:
            ui_crear_cliente(parent=win, backend=backend, usuario=usuario)
            # Al cerrar el popup, recargar lista
            win.after(100, cargar_datos)
        except Exception as e:
            messagebox.showerror(
                "Error",
                f"No se pudo abrir la ventana de creación de cliente:\n{e}",
                parent=win,
            )

    def accion_editar():
        id_cli = _obtener_id_seleccionado()
        if id_cli is None:
            messagebox.showwarning(
                "Atención",
                "Seleccione un cliente de la lista.",
                parent=win,
            )
            return
        try:
            ui_crear_cliente(
                parent=win,
                backend=backend,
                usuario=usuario,
                id_cliente_a_editar=id_cli,
            )
            win.after(100, cargar_datos)
        except Exception as e:
            messagebox.showerror(
                "Error",
                f"No se pudo abrir la ventana de edición:\n{e}",
                parent=win,
            )

    def accion_desactivar():
        id_cli = _obtener_id_seleccionado()
        if id_cli is None:
            messagebox.showwarning(
                "Atención",
                "Seleccione un cliente de la lista.",
                parent=win,
            )
            return

        if not messagebox.askyesno(
            "Confirmar",
            "¿Está seguro de desactivar este cliente?\n\n"
            "No se podrá seleccionar para futuras ventas.",
            parent=win,
        ):
            return

        try:
            if backend.eliminar_cliente_logico(id_cli):
                messagebox.showinfo(
                    "Éxito",
                    "Cliente desactivado.",
                    parent=win,
                )
                cargar_datos()
            else:
                messagebox.showerror(
                    "Error",
                    "No se pudo desactivar el cliente.",
                    parent=win,
                )
        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Ocurrió un error al desactivar el cliente:\n{e}",
                parent=win,
            )

    # ============================
    # Frame: botones inferiores
    # ============================
    frame_botones = tk.Frame(win, bg="#f4f4f8")
    frame_botones.pack(fill="x", padx=20, pady=(5, 15))

    btn_recargar = tk.Button(
        frame_botones,
        text="↻ Recargar Lista",
        command=accion_recargar,
        bg="#03A9F4",
        fg="white",
        width=15,
    )
    btn_recargar.pack(side=tk.LEFT, padx=(0, 10))

    btn_crear = tk.Button(
        frame_botones,
        text="+ Crear Cliente",
        command=accion_crear,
        bg="#4CAF50",
        fg="white",
        width=15,
    )
    btn_crear.pack(side=tk.LEFT, padx=10)

    btn_editar = tk.Button(
        frame_botones,
        text="✎ Editar Cliente",
        command=accion_editar,
        bg="#FFB300",
        fg="black",
        width=15,
    )
    btn_editar.pack(side=tk.LEFT, padx=10)

    btn_desactivar = tk.Button(
        frame_botones,
        text="⛔ Desactivar",
        command=accion_desactivar,
        bg="#E53935",
        fg="white",
        width=15,
    )
    btn_desactivar.pack(side=tk.LEFT, padx=10)

    btn_cerrar = tk.Button(
        frame_botones,
        text="Cerrar",
        command=win.destroy,
        bg="#607D8B",
        fg="white",
        width=15,
    )
    btn_cerrar.pack(side=tk.RIGHT, padx=0)

    # ============================
    # Eventos adicionales
    # ============================
    def on_doble_click(event):
        accion_editar()

    tree.bind("<Double-1>", on_doble_click)

    def on_enter_buscar(event):
        cargar_datos()

    entry_buscar.bind("<Return>", on_enter_buscar)

    def on_toggle_inactivos():
        cargar_datos()

    chk_inactivos.config(command=on_toggle_inactivos)

    # ============================
    # Boot: carga inicial y foco
    # ============================
    cargar_datos()
    configurar_navegacion_ventana(win)

    def _enfocar_inicial():
        try:
            win.focus_force()          # la ventana recibe el foco del teclado
            entry_buscar.focus_set()   # empezamos en el campo de búsqueda
        except Exception:
            pass

    win.after(50, _enfocar_inicial)
    win.grab_set()
    win.transient(parent)
