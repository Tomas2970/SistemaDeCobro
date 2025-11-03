# app/frontend/stock_alerts.py
"""
Alertas de stock bajo reutilizables para Inventario y Venta.
'Por qué': UI decide cuándo alertar; backend se mantiene limpio.
"""
from __future__ import annotations
from typing import Any, Dict, Iterable, List, Optional
from tkinter import messagebox

def _low_stock_rows(productos: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for p in productos:
        try:
            # (Asumimos que tu backend_adapter ahora filtra productos inactivos,
            # pero por las dudas lo dejamos)
            if int(p.get("activo", 1)) != 1:
                continue
            stock = int(p.get("stock", 0))
            minimo = int(p.get("stock_minimo", 0))
            if stock <= minimo:
                rows.append(p)
        except Exception:
            continue
    return rows

def show_low_stock_alert(parent, backend) -> None:
    """Llamar al abrir Inventario o Productos (ABM)."""
    try:
        # Usamos la función optimizada del backend si existe
        if hasattr(backend, "obtener_stock_bajo"):
            bajos = backend.obtener_stock_bajo()
        else:
            # Fallback por si no existe
            prods = backend.obtener_productos_full()
            bajos = _low_stock_rows(prods)
            
        if not bajos:
            return
            
        lines = []
        for p in bajos[:50]: # Limitar a 50 para no saturar
            nombre = str(p.get("nombre", ""))
            cb = p.get("codigo_barras") or "-"
            stock = p.get("stock")
            minimo = p.get("stock_minimo")
            lines.append(f"• {nombre} (CB {cb}) — stock {stock} / mínimo {minimo}")
            
        extra = "" if len(bajos) <= 50 else f"\n... y {len(bajos)-50} más"
        msg = "Hay productos en o por debajo del stock mínimo:\n\n" + "\n".join(lines) + extra
        messagebox.showwarning("⚠️ Stock bajo", msg, parent=parent)
    except Exception as e:
        print(f"[stock_alerts] show_low_stock_alert error: {e}")

def check_low_stock_after_sale(parent, backend, items_vendidos: Iterable[Dict[str, Any]]) -> None:
    """Llamar inmediatamente luego de confirmar la venta exitosa."""
    try:
        ids = []
        for it in items_vendidos:
            pid = it.get("id_producto")
            if pid is not None:
                ids.append(int(pid))
        if not ids:
            return

        afectados: List[Dict[str, Any]] = []
        buscar_id = getattr(backend, "buscar_producto_por_id", None)
        
        # Si tenemos la función rápida 'buscar_id', la usamos
        if callable(buscar_id):
            for pid in set(ids): # Usar set() evita buscar el mismo ID varias veces
                p = buscar_id(pid)
                if p:
                    afectados.append(p)
        else:
            # Fallback lento si no hay 'buscar_id'
            todo = backend.obtener_productos_full()
            mp = {int(p["id"]): p for p in todo if "id" in p}
            for pid in set(ids):
                if pid in mp:
                    afectados.append(mp[pid])

        bajos = _low_stock_rows(afectados)
        if not bajos:
            return

        lines = []
        for p in bajos:
            nombre = str(p.get("nombre", ""))
            cb = p.get("codigo_barras") or "-"
            stock = p.get("stock")
            minimo = p.get("stock_minimo")
            lines.append(f"• {nombre} (CB {cb}) — stock {stock} (mínimo {minimo})")
        msg = "Tras la venta, quedaron en mínimo o por debajo:\n\n" + "\n".join(lines)
        messagebox.showwarning("⚠️ Stock mínimo alcanzado", msg, parent=parent)
    except Exception as e:
        print(f"[stock_alerts] check_low_stock_after_sale error: {e}")