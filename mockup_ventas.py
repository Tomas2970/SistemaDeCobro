import customtkinter as ctk
from tkinter import ttk

def correr_mockup():
    ctk.set_appearance_mode("Light")
    ctk.set_default_color_theme("blue")
    
    app = ctk.CTk()
    app.title("Prototipo Visual: Punto de Venta (Fase 5)")
    app.geometry("1200x800")
    app.configure(fg_color="#f3f4f6")
    
    # Fuentes
    font_title = ("Segoe UI", 16, "bold")
    font_normal = ("Segoe UI", 14)
    font_big = ("Segoe UI", 24, "bold")
    
    # 1. HEADER (Cliente)
    frm_header = ctk.CTkFrame(app, fg_color="white", corner_radius=10, border_width=1, border_color="#e5e7eb")
    frm_header.pack(fill="x", padx=25, pady=(25, 10))
    
    ctk.CTkLabel(frm_header, text="👤 Cliente Actual:", font=font_title, text_color="#374151").pack(side="left", padx=20, pady=20)
    ctk.CTkLabel(frm_header, text="Consumidor Final (Predeterminado)", font=font_normal, text_color="#6b7280").pack(side="left")
    
    ctk.CTkButton(frm_header, text="🔍 Buscar / Cambiar Cliente", font=("Segoe UI", 14, "bold"), fg_color="#3b82f6", hover_color="#2563eb", width=220, height=45).pack(side="right", padx=20)
    ctk.CTkButton(frm_header, text="➕ Nuevo", font=("Segoe UI", 14, "bold"), fg_color="#10b981", hover_color="#059669", width=120, height=45).pack(side="right", padx=(0, 10))

    # 2. INPUTS (Cantidad y Producto)
    frm_inputs = ctk.CTkFrame(app, fg_color="white", corner_radius=10, border_width=1, border_color="#e5e7eb")
    frm_inputs.pack(fill="x", padx=25, pady=10)
    
    ctk.CTkLabel(frm_inputs, text="Cant.", font=font_title, text_color="#374151").pack(side="left", padx=(20, 10), pady=20)
    ctk.CTkEntry(frm_inputs, placeholder_text="1", width=80, height=50, font=font_big, justify="center").pack(side="left")
    
    ctk.CTkLabel(frm_inputs, text="Código o Nombre del Producto:", font=font_title, text_color="#374151").pack(side="left", padx=(30, 10))
    ctk.CTkEntry(frm_inputs, placeholder_text="Escanear código de barras o buscar... (Ej: Yerba)", width=500, height=50, font=font_normal).pack(side="left", expand=True, fill="x", padx=(0, 20))

    # 4. FOOTER (Cobrar y Total - EMPAQUETADO PRIMERO HACIA ABAJO)
    frm_footer = ctk.CTkFrame(app, fg_color="white", corner_radius=10, border_width=1, border_color="#e5e7eb")
    frm_footer.pack(side="bottom", fill="x", padx=25, pady=(10, 25))
    
    ctk.CTkButton(frm_footer, text="🗑️ Cancelar Venta", font=("Segoe UI", 16, "bold"), fg_color="#ef4444", hover_color="#dc2626", width=200, height=60).pack(side="left", padx=20, pady=20)
    ctk.CTkButton(frm_footer, text="➖ Quitar Ítem", font=("Segoe UI", 16, "bold"), fg_color="#f59e0b", hover_color="#d97706", width=180, height=60).pack(side="left", padx=(0, 20), pady=20)
    
    ctk.CTkButton(frm_footer, text="💳 COBRAR (F12)", font=("Segoe UI", 24, "bold"), fg_color="#10b981", hover_color="#059669", width=260, height=75).pack(side="right", padx=20, pady=20)
    
    # Texto Total
    ctk.CTkLabel(frm_footer, text="$ 3.850,00", font=("Segoe UI", 56, "bold"), text_color="#111827").pack(side="right", padx=30)
    ctk.CTkLabel(frm_footer, text="TOTAL A PAGAR", font=("Segoe UI", 18, "bold"), text_color="#6b7280").pack(side="right", padx=(0, 0))

    # 3. LISTA DE PRODUCTOS (Se empaca al final para usar el espacio restante)
    frm_tv = ctk.CTkFrame(app, fg_color="white", corner_radius=10, border_width=1, border_color="#e5e7eb")
    frm_tv.pack(fill="both", expand=True, padx=25, pady=10)
    
    style = ttk.Style(app)
    style.theme_use('clam')
    style.configure("Modern.Treeview", background="white", foreground="#1f2937", rowheight=50, font=('Segoe UI', 13), borderwidth=0)
    style.configure("Modern.Treeview.Heading", background="#f8fafc", foreground="#475569", font=('Segoe UI', 12, 'bold'), borderwidth=0, padding=12)
    style.map('Modern.Treeview', background=[('selected', '#eff6ff')], foreground=[('selected', '#1e40af')])
    
    tv = ttk.Treeview(frm_tv, columns=("cant", "desc", "precio", "sub"), show="headings", style="Modern.Treeview")
    tv.heading("cant", text="CANT.")
    tv.heading("desc", text="DESCRIPCIÓN DEL PRODUCTO")
    tv.heading("precio", text="PRECIO UNIT.")
    tv.heading("sub", text="SUBTOTAL")
    
    tv.column("cant", width=100, anchor="center")
    tv.column("desc", width=500, anchor="w")
    tv.column("precio", width=150, anchor="e")
    tv.column("sub", width=150, anchor="e")
    
    tv.pack(fill="both", expand=True, padx=5, pady=5)
    
    # Filas de prueba (Solo visuales)
    tv.insert("", "end", values=("2", "Yerba Mate Taragüi 1Kg", "$ 1.250", "$ 2.500"))
    tv.insert("", "end", values=("1", "Leche La Serenísima 1L", "$ 850", "$ 850"))
    tv.insert("", "end", values=("0.5", "Pan Francés (Kg)", "$ 1.000", "$ 500"))

    app.mainloop()

if __name__ == "__main__":
    correr_mockup()
