# app/frontend/interfaz_asignar_productos.py
from __future__ import annotations
import tkinter as tk
from tkinter import ttk, messagebox, Listbox, Scrollbar, SINGLE, EXTENDED, END, Toplevel
from typing import Any

def ui_asignar_productos(parent: tk.Misc, backend, id_proveedor: int, nombre_proveedor: str):
    """
    Abre una ventana para asignar productos a un proveedor específico.
    """
    win = Toplevel(parent)
    win.title(f"Asignar Productos a: {nombre_proveedor}")
    win.geometry("800x500")
    win.config(bg="#f4f4f8")
    win.resizable(False, False)

    # Lista de productos en memoria
    productos_asignados: list[dict] = []
    productos_disponibles: list[dict] = []

    # --- Función de formato simple ---
    def _fmt(p: dict):
        return f"{p.get('id_producto')} | {p.get('nombre')}"
    
    def _get_id_from_selection(listbox: Listbox) -> list[int]:
        ids = []
        try:
            for i in listbox.curselection():
                linea = listbox.get(i)
                id_prod = int(linea.split("|")[0].strip())
                ids.append(id_prod)
        except Exception as e:
            print(f"Error obteniendo ID de lista: {e}")
        return ids

    # --- Paneles principales ---
    frame_izq = tk.Frame(win, bg="#f4f4f8", padx=10, pady=10)
    frame_izq.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    frame_centro = tk.Frame(win, bg="#f4f4f8", padx=10, pady=10)
    frame_centro.pack(side=tk.LEFT, fill=tk.Y, pady=100) # Centra los botones verticalmente

    frame_der = tk.Frame(win, bg="#f4f4f8", padx=10, pady=10)
    frame_der.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    # --- Panel Izquierdo (Asignados) ---
    tk.Label(frame_izq, text="Productos ASIGNADOS a este proveedor", bg="#f4f4f8", font=("Helvetica", 10, "bold")).pack(pady=5)
    
    frame_lista_izq = tk.Frame(frame_izq)
    frame_lista_izq.pack(fill=tk.BOTH, expand=True)
    
    sc_izq = Scrollbar(frame_lista_izq, orient=tk.VERTICAL)
    lista_asignados = Listbox(frame_lista_izq, selectmode=EXTENDED, yscrollcommand=sc_izq.set, height=20)
    sc_izq.config(command=lista_asignados.yview)
    sc_izq.pack(side=tk.RIGHT, fill=tk.Y)
    lista_asignados.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    # --- Panel Derecho (Disponibles) ---
    tk.Label(frame_der, text="Productos DISPONIBLES (Generales)", bg="#f4f4f8", font=("Helvetica", 10, "bold")).pack(pady=5)
    
    # Búsqueda para disponibles
    var_filtro = tk.StringVar()
    ent_filtro = tk.Entry(frame_der, textvariable=var_filtro, width=40)
    ent_filtro.pack(fill=tk.X, pady=(0, 5))
    
    frame_lista_der = tk.Frame(frame_der)
    frame_lista_der.pack(fill=tk.BOTH, expand=True)
    
    sc_der = Scrollbar(frame_lista_der, orient=tk.VERTICAL)
    lista_disponibles = Listbox(frame_lista_der, selectmode=EXTENDED, yscrollcommand=sc_der.set, height=18)
    sc_der.config(command=lista_disponibles.yview)
    sc_der.pack(side=tk.RIGHT, fill=tk.Y)
    lista_disponibles.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    # --- Lógica de Carga de Datos ---
    def cargar_listas():
        nonlocal productos_asignados, productos_disponibles
        try:
            productos_asignados = backend.obtener_productos_por_proveedor(id_proveedor)
            productos_disponibles = backend.obtener_productos_sin_asignar(id_proveedor)
            
            _filtrar_listas()
            
        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron cargar las listas de productos:\n{e}", parent=win)

    def _filtrar_listas(event=None):
        lista_asignados.delete(0, END)
        lista_disponibles.delete(0, END)
        
        filtro = var_filtro.get().strip().lower()
        
        for p in productos_asignados:
            lista_asignados.insert(END, _fmt(p))
            
        for p in productos_disponibles:
            if filtro in (p.get('nombre') or '').lower() or filtro == str(p.get('id_producto')):
                lista_disponibles.insert(END, _fmt(p))

    var_filtro.trace_add("write", _filtrar_listas)

    # --- Lógica de Botones de Mapeo ---
    def asignar():
        ids = _get_id_from_selection(lista_disponibles)
        if not ids: return
        
        for id_prod in ids:
            backend.asignar_producto_a_proveedor(id_proveedor, id_prod)
        
        cargar_listas() # Recarga todo

    def quitar():
        ids = _get_id_from_selection(lista_asignados)
        if not ids: return
        
        for id_prod in ids:
            backend.quitar_producto_a_proveedor(id_proveedor, id_prod)
            
        cargar_listas() # Recarga todo

    # --- Botones del Centro ---
    btn_asignar = tk.Button(frame_centro, text="< Asignar", command=asignar, bg="#4CAF50", fg="white", width=10)
    btn_asignar.pack(pady=10)
    
    btn_quitar = tk.Button(frame_centro, text="Quitar >", command=quitar, bg="#f44336", fg="white", width=10)
    btn_quitar.pack(pady=10)

    # --- Carga Inicial ---
    cargar_listas()
    win.grab_set()
    win.transient(parent)