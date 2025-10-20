import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date

def interfaz_reportes(backend, usuario):
    """Ventana de reportes del sistema (solo para roles con permiso)"""
    ventana = tk.Toplevel()
    ventana.title("📊 Reportes - Supermercado Don Atilio")
    ventana.geometry("900x600")
    ventana.config(bg="#f4f4f8")

    tk.Label(
        ventana,
        text="Generador de Reportes",
        bg="#4CAF50",
        fg="white",
        font=("Arial", 16, "bold"),
        pady=10
    ).pack(fill=tk.X)

    frame_opciones = tk.Frame(ventana, bg="#f4f4f8")
    frame_opciones.pack(pady=20)

    tk.Label(frame_opciones, text="Tipo de reporte:", bg="#f4f4f8").grid(row=0, column=0, padx=10)
    tipo_reporte = ttk.Combobox(frame_opciones, values=[
        "Ventas por vendedor",
        "Ventas por período",
        "Ventas totales"
    ], state="readonly", width=30)
    tipo_reporte.grid(row=0, column=1)
    tipo_reporte.current(0)

    tk.Label(frame_opciones, text="Desde (YYYY-MM-DD):", bg="#f4f4f8").grid(row=1, column=0, padx=10, pady=5)
    entry_desde = tk.Entry(frame_opciones, width=15)
    entry_desde.insert(0, f"{date.today().year}-01-01")
    entry_desde.grid(row=1, column=1)

    tk.Label(frame_opciones, text="Hasta (YYYY-MM-DD):", bg="#f4f4f8").grid(row=2, column=0, padx=10, pady=5)
    entry_hasta = tk.Entry(frame_opciones, width=15)
    entry_hasta.insert(0, str(date.today()))
    entry_hasta.grid(row=2, column=1)

    # Treeview para mostrar datos
    columnas = ("col1", "col2", "col3", "col4", "col5")
    tree = ttk.Treeview(ventana, columns=columnas, show="headings")
    tree.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

    scrollbar = ttk.Scrollbar(ventana, orient="vertical", command=tree.yview)
    tree.configure(yscroll=scrollbar.set)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    # Función para generar reportes
    def generar_reporte():
        for row in tree.get_children():
            tree.delete(row)

        tipo = tipo_reporte.get()
        desde = entry_desde.get()
        hasta = entry_hasta.get()

        try:
            if tipo == "Ventas por vendedor":
                resultados = backend.reporte_ventas_por_vendedor()
                encabezados = ["ID Vendedor", "Nombre", "Total Ventas", "Monto Total"]
            elif tipo == "Ventas por período":
                resultados = backend.reporte_ventas_por_periodo(desde, hasta)
                encabezados = ["Fecha", "Cantidad Ventas", "Monto Total"]
            else:
                resultados = backend.reporte_ventas_totales()
                encabezados = ["ID Venta", "Fecha", "Vendedor", "Total"]

            # Encabezados dinámicos
            tree["columns"] = [f"col{i}" for i in range(1, len(encabezados) + 1)]
            for i, h in enumerate(encabezados):
                tree.heading(f"col{i+1}", text=h)
                tree.column(f"col{i+1}", width=180)

            for fila in resultados:
                tree.insert("", tk.END, values=list(fila.values()))

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo generar el reporte:\n{e}")

    tk.Button(
        ventana,
        text="📈 Generar Reporte",
        bg="#2196F3",
        fg="white",
        font=("Arial", 11, "bold"),
        width=20,
        command=generar_reporte
    ).pack(pady=10)

    tk.Button(
        ventana,
        text="Cerrar",
        bg="#f44336",
        fg="white",
        width=12,
        command=ventana.destroy
    ).pack(pady=10)

    ventana.mainloop()
