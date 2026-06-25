# app/frontend/validaciones_ui.py
# 🎯 SISTEMA DE VALIDACIÓN UNIFICADO PARA TODA LA APLICACIÓN
# 🔥 CORREGIDO: Teléfono ahora rechaza números incompletos
import tkinter as tk
import re
import unicodedata

# ============================================================================
# 🔒 VALIDADORES DE TECLADO (KEY PRESS) - Bloquean caracteres inválidos
# ============================================================================

class ValidadoresTeclado:
    """Validadores que se ejecutan en cada tecla presionada."""
    
    @staticmethod
    def solo_numeros(nuevo_valor: str) -> bool:
        """Solo permite dígitos (0-9)."""
        return nuevo_valor.isdigit() or nuevo_valor == ""
    
    @staticmethod
    def solo_letras(nuevo_valor: str) -> bool:
        """Solo permite letras, espacios y tildes."""
        # Incluye tildes, ñ y caracteres especiales latinos
        if nuevo_valor == "":
            return True
        for c in nuevo_valor:
            if c.isspace():
                continue
            # Normalizar para quitar tildes temporalmente y verificar si es letra
            normalized = unicodedata.normalize('NFD', c)
            if any(char.isalpha() for char in normalized) or c == 'ñ' or c == 'Ñ':
                continue
            return False
        return True
    
    @staticmethod
    def letras_y_numeros(nuevo_valor: str) -> bool:
        """Permite letras, números y espacios."""
        return all(c.isalnum() or c.isspace() for c in nuevo_valor) or nuevo_valor == ""
    
    @staticmethod
    def dni(nuevo_valor: str) -> bool:
        """DNI: máximo 8 dígitos."""
        if len(nuevo_valor) > 8:
            return False
        return nuevo_valor.isdigit() or nuevo_valor == ""
    
    @staticmethod
    def cuit(nuevo_valor: str) -> bool:
        """CUIT: máximo 11 dígitos."""
        if len(nuevo_valor) > 11:
            return False
        return nuevo_valor.isdigit() or nuevo_valor == ""
    
    @staticmethod
    def telefono(nuevo_valor: str) -> bool:
        """Teléfono: máximo 10 dígitos (argentino)."""
        if len(nuevo_valor) > 10:
            return False
        return nuevo_valor.isdigit() or nuevo_valor == ""
    
    @staticmethod
    def decimal(nuevo_valor: str) -> bool:
        """Permite números decimales con punto o coma."""
        if nuevo_valor == "":
            return True
        # Permite dígitos, punto y coma (solo uno)
        patron = r'^[0-9]*[.,]?[0-9]*$'
        return bool(re.match(patron, nuevo_valor))
    
    @staticmethod
    def email(nuevo_valor: str) -> bool:
        """Email: permite caracteres válidos para email."""
        if nuevo_valor == "":
            return True
        # Permite letras, números, @ . _ - +
        return all(c.isalnum() or c in '@._-+' for c in nuevo_valor)

# ============================================================================
# ✅ VALIDADORES EN TIEMPO REAL (VISUAL FEEDBACK)
# ============================================================================

class ValidadoresVisuales:
    """Validadores que dan feedback visual mientras el usuario escribe."""
    
    @staticmethod
    def validar_nombre(nombre: str) -> tuple[bool, str]:
        """Valida que el nombre tenga al menos 3 caracteres."""
        nombre = nombre.strip()
        if len(nombre) < 3:
            return False, "❌ Mínimo 3 caracteres"
        if not nombre[0].isalpha():
            return False, "❌ Debe empezar con letra"
        return True, "✓ Válido"
    
    @staticmethod
    def validar_dni(dni: str) -> tuple[bool, str]:
        """Valida DNI argentino (7-8 dígitos)."""
        dni = dni.strip()
        if len(dni) == 0:
            return False, "⚠️ DNI obligatorio"
        if len(dni) < 7:
            return False, f"❌ Faltan {7 - len(dni)} dígitos"
        if len(dni) > 8:
            return False, "❌ Máximo 8 dígitos"
        if not dni.isdigit():
            return False, "❌ Solo números"
        return True, "✓ Válido"
    
    @staticmethod
    def validar_cuit(cuit: str) -> tuple[bool, str]:
        """Valida CUIT argentino (11 dígitos)."""
        cuit = cuit.strip()
        if len(cuit) == 0:
            return True, "⚪ Opcional"  # CUIT es opcional
        if len(cuit) < 11:
            return False, f"❌ Faltan {11 - len(cuit)} dígitos"
        if len(cuit) > 11:
            return False, "❌ Máximo 11 dígitos"
        if not cuit.isdigit():
            return False, "❌ Solo números"
        return True, "✓ Válido"
    
    @staticmethod
    def validar_telefono(telefono: str) -> tuple[bool, str]:
        """🔥 CORREGIDO: Teléfono argentino (10 dígitos completos o vacío)."""
        telefono = telefono.strip()
        if len(telefono) == 0:
            return True, "⚪ Opcional"
        
        # 🔥 CAMBIO CRÍTICO: Si tiene entre 1-9 dígitos → INVÁLIDO
        if len(telefono) < 10:
            return False, f"❌ Faltan {10 - len(telefono)} dígitos"
        
        if len(telefono) > 10:
            return False, "❌ Máximo 10 dígitos"
        if not telefono.isdigit():
            return False, "❌ Solo números"
        return True, "✓ Válido"
    
    @staticmethod
    def validar_email(email: str) -> tuple[bool, str]:
        """Valida formato de email."""
        email = email.strip()
        if len(email) == 0:
            return True, "⚪ Opcional"
        
        # Regex simple pero efectivo
        patron = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(patron, email):
            if '@' not in email:
                return False, "❌ Falta @"
            if '.' not in email.split('@')[-1]:
                return False, "❌ Falta dominio (.com)"
            return False, "❌ Formato inválido"
        return True, "✓ Válido"
    
    @staticmethod
    def validar_monto(monto_str: str) -> tuple[bool, str]:
        """Valida que sea un número positivo."""
        monto_str = monto_str.strip().replace(',', '.')
        if len(monto_str) == 0:
            return False, "⚠️ Campo obligatorio"
        try:
            monto = float(monto_str)
            if monto <= 0:
                return False, "❌ Debe ser mayor a 0"
            if monto > 999999999:
                return False, "❌ Valor muy alto"
            return True, "✓ Válido"
        except ValueError:
            return False, "❌ Número inválido"

    @staticmethod
    def validar_nombre_empresa(nombre: str) -> tuple[bool, str]:
        """Valida el nombre de una empresa (mínimo 3 chars, sin restricción de primer carácter).

        A diferencia de validar_nombre(), permite que empiece con número
        (ej: "3M", "7-Eleven") ya que es válido para razones sociales.
        """
        nombre = nombre.strip()
        if len(nombre) < 3:
            return False, "❌ Mínimo 3 caracteres"
        return True, "✓ Válido"

    @staticmethod
    def validar_cuit_obligatorio(cuit: str) -> tuple[bool, str]:
        """Valida CUIT argentino (11 dígitos), tratándolo como campo OBLIGATORIO.

        Usar en formularios de proveedores donde el CUIT es requerido.
        A diferencia de validar_cuit(), el campo vacío es un error.
        """
        cuit = cuit.strip()
        if len(cuit) == 0:
            return False, "⚠️ CUIT obligatorio"
        if len(cuit) < 11:
            return False, f"❌ Faltan {11 - len(cuit)} dígitos"
        if len(cuit) > 11:
            return False, "❌ Máximo 11 dígitos"
        if not cuit.isdigit():
            return False, "❌ Solo números"
        return True, "✓ Válido"

    @staticmethod
    def validar_telefono_obligatorio(telefono: str) -> tuple[bool, str]:
        """Valida teléfono argentino (10 dígitos exactos), tratándolo como campo OBLIGATORIO.

        Usar en formularios de proveedores donde el teléfono es requerido.
        A diferencia de validar_telefono(), el campo vacío es un error.
        """
        telefono = telefono.strip()
        if len(telefono) == 0:
            return False, "⚠️ Teléfono obligatorio"
        if len(telefono) < 10:
            return False, f"❌ Faltan {10 - len(telefono)} dígitos"
        if len(telefono) > 10:
            return False, "❌ Máximo 10 dígitos"
        if not telefono.isdigit():
            return False, "❌ Solo números"
        return True, "✓ Válido"


# ============================================================================
# 🎨 COMPONENTES UI CON VALIDACIÓN INTEGRADA
# ============================================================================

class EntryValidado(tk.Entry):
    """Entry que valida en tiempo real y muestra feedback visual."""
    
    def __init__(self, parent, tipo_validacion: str, **kwargs):
        """
        Args:
            tipo_validacion: 'nombre', 'dni', 'cuit', 'telefono', 'email', 'monto', 'decimal', 'solo_numeros', 'solo_letras'
        """
        super().__init__(parent, **kwargs)
        
        self.tipo_validacion = tipo_validacion
        self.label_feedback = None
        self.color_original = self.cget('bg')
        
        # Configurar validación de teclado
        self._configurar_validacion_teclado()
        
        # Configurar validación visual
        self._configurar_validacion_visual()
    
    def _configurar_validacion_teclado(self):
        """Aplica validación de teclas según el tipo."""
        validador = None
        
        if self.tipo_validacion == 'dni':
            validador = ValidadoresTeclado.dni
        elif self.tipo_validacion == 'cuit':
            validador = ValidadoresTeclado.cuit
        elif self.tipo_validacion == 'telefono':
            validador = ValidadoresTeclado.telefono
        elif self.tipo_validacion == 'solo_numeros':
            validador = ValidadoresTeclado.solo_numeros
        elif self.tipo_validacion == 'solo_letras':
            validador = ValidadoresTeclado.solo_letras
        elif self.tipo_validacion == 'letras_y_numeros':
            validador = ValidadoresTeclado.letras_y_numeros
        elif self.tipo_validacion == 'decimal' or self.tipo_validacion == 'monto':
            validador = ValidadoresTeclado.decimal
        elif self.tipo_validacion == 'email':
            validador = ValidadoresTeclado.email
        elif self.tipo_validacion == 'nombre':
            validador = ValidadoresTeclado.solo_letras  # 🔥 CORREGIDO: solo letras
        
        if validador:
            vcmd = (self.register(validador), '%P')
            self.config(validate='key', validatecommand=vcmd)
    
    def _configurar_validacion_visual(self):
        """Configura validación visual en tiempo real."""
        self.bind('<KeyRelease>', self._validar_contenido)
        self.bind('<FocusOut>', self._validar_contenido)
    
    def _validar_contenido(self, event=None):
        """Valida el contenido y muestra feedback visual."""
        contenido = self.get()
        valido = False
        mensaje = ""
        
        # Obtener validador visual apropiado
        if self.tipo_validacion == 'nombre':
            valido, mensaje = ValidadoresVisuales.validar_nombre(contenido)
        elif self.tipo_validacion == 'dni':
            valido, mensaje = ValidadoresVisuales.validar_dni(contenido)
        elif self.tipo_validacion == 'cuit':
            valido, mensaje = ValidadoresVisuales.validar_cuit(contenido)
        elif self.tipo_validacion == 'telefono':
            valido, mensaje = ValidadoresVisuales.validar_telefono(contenido)
        elif self.tipo_validacion == 'email':
            valido, mensaje = ValidadoresVisuales.validar_email(contenido)
        elif self.tipo_validacion == 'monto':
            valido, mensaje = ValidadoresVisuales.validar_monto(contenido)
        else:
            return  # Sin validación visual para otros tipos
        
        # Actualizar color del Entry (Ajustado para Dark Mode)
        if contenido.strip() == "":
            self.config(bg=self.color_original)
        elif valido:
            self.config(bg="#064e3b")  # Verde oscuro
        else:
            self.config(bg="#7f1d1d")  # Rojo oscuro
        
        # Actualizar label de feedback si existe
        if self.label_feedback:
            self.label_feedback.config(text=mensaje)
            if valido:
                self.label_feedback.config(fg="#059669")  # Verde
            elif "Opcional" in mensaje:
                self.label_feedback.config(fg="#6b7280")  # Gris
            else:
                self.label_feedback.config(fg="#dc2626")  # Rojo
    
    def asociar_label_feedback(self, label: tk.Label):
        """Asocia un label para mostrar mensajes de validación."""
        self.label_feedback = label
    
    def es_valido(self) -> bool:
        """🔥 NUEVO: Retorna True si el contenido es válido."""
        contenido = self.get()
        
        if self.tipo_validacion == 'nombre':
            valido, _ = ValidadoresVisuales.validar_nombre(contenido)
        elif self.tipo_validacion == 'dni':
            valido, _ = ValidadoresVisuales.validar_dni(contenido)
        elif self.tipo_validacion == 'cuit':
            valido, _ = ValidadoresVisuales.validar_cuit(contenido)
        elif self.tipo_validacion == 'telefono':
            valido, _ = ValidadoresVisuales.validar_telefono(contenido)
        elif self.tipo_validacion == 'email':
            valido, _ = ValidadoresVisuales.validar_email(contenido)
        elif self.tipo_validacion == 'monto':
            valido, _ = ValidadoresVisuales.validar_monto(contenido)
        else:
            return True  # Sin validación específica
        
        return valido

# ============================================================================
# 📋 FUNCIÓN HELPER PARA CREAR CAMPOS VALIDADOS
# ============================================================================

def crear_campo_validado(parent, label_texto: str, tipo_validacion: str, fila: int, 
                         obligatorio: bool = False, width: int = 35) -> tuple[EntryValidado, tk.Label]:
    """
    Crea un campo de entrada con validación automática.
    
    Args:
        parent: Frame contenedor
        label_texto: Texto del label
        tipo_validacion: Tipo de validación ('nombre', 'dni', 'cuit', etc.)
        fila: Número de fila en el grid
        obligatorio: Si es campo obligatorio (agrega *)
        width: Ancho del Entry
    
    Returns:
        Tupla (EntryValidado, Label de feedback)
    """
    # Label del campo
    texto_final = f"{label_texto} (*)" if obligatorio else label_texto
    tk.Label(parent, text=texto_final, bg="#111827", fg="white", anchor="w").grid(
        row=fila, column=0, sticky="ew", pady=5, padx=(0, 10)
    )
    
    # Entry validado
    entry = EntryValidado(parent, tipo_validacion=tipo_validacion, width=width, font=("Segoe UI", 10))
    entry.grid(row=fila, column=1, sticky="ew", pady=5)
    
    # Label de feedback
    lbl_feedback = tk.Label(parent, text="", bg="#111827", fg="#9ca3af", font=("Segoe UI", 8), anchor="w")
    lbl_feedback.grid(row=fila, column=2, sticky="w", padx=(5, 0))
    
    entry.asociar_label_feedback(lbl_feedback)
    
    return entry, lbl_feedback

# ============================================================================
# 🔍 VALIDADOR FINAL (ANTES DE ENVIAR AL BACKEND)
# ============================================================================

class ValidadorFormulario:
    """Valida todos los campos de un formulario antes de enviar."""
    
    @staticmethod
    def validar_campos(campos: dict) -> tuple[bool, str]:
        """
        Valida múltiples campos de un formulario.
        
        Args:
            campos: Dict con formato {'nombre_campo': (valor, tipo_validacion, obligatorio)}
        
        Returns:
            Tupla (es_valido, mensaje_error)
        """
        for nombre_campo, (valor, tipo_validacion, obligatorio) in campos.items():
            valor = str(valor).strip()
            
            # Verificar obligatoriedad
            if obligatorio and not valor:
                return False, f"El campo '{nombre_campo}' es obligatorio"
            
            # Si está vacío y no es obligatorio, saltar validación
            if not valor and not obligatorio:
                continue
            
            # Validar según tipo
            if tipo_validacion == 'nombre':
                valido, msg = ValidadoresVisuales.validar_nombre(valor)
            elif tipo_validacion == 'nombre_empresa':
                valido, msg = ValidadoresVisuales.validar_nombre_empresa(valor)
            elif tipo_validacion == 'dni':
                valido, msg = ValidadoresVisuales.validar_dni(valor)
            elif tipo_validacion == 'cuit':
                valido, msg = ValidadoresVisuales.validar_cuit(valor)
            elif tipo_validacion == 'cuit_obligatorio':
                valido, msg = ValidadoresVisuales.validar_cuit_obligatorio(valor)
            elif tipo_validacion == 'telefono':
                valido, msg = ValidadoresVisuales.validar_telefono(valor)
            elif tipo_validacion == 'telefono_obligatorio':
                valido, msg = ValidadoresVisuales.validar_telefono_obligatorio(valor)
            elif tipo_validacion == 'email':
                valido, msg = ValidadoresVisuales.validar_email(valor)
            elif tipo_validacion == 'monto':
                valido, msg = ValidadoresVisuales.validar_monto(valor)
            else:
                continue  # Sin validación específica
            
            if not valido:
                return False, f"{nombre_campo}: {msg}"
        
        return True, "Todos los campos son válidos"

# ============================================================================
# 🌐 HELPERS PARA CTkEntry (customtkinter)
# Compatible con border_color — no depende de tk.Entry bg
# ============================================================================

def aplicar_feedback_ctk(entry_ctk, label_ctk, valido: bool, mensaje: str) -> None:
    """
    Aplica feedback visual a un CTkEntry y su label de feedback asociado.

    Equivalente a EntryValidado._validar_contenido(), pero compatible con
    CTkEntry (usa border_color en lugar de bg del Entry).

    Args:
        entry_ctk:  CTkEntry al que aplicar el borde de color.
        label_ctk:  CTkLabel donde mostrar el mensaje (puede ser None).
        valido:     True si el campo es válido.
        mensaje:    Texto a mostrar en el label.
    """
    valor = entry_ctk.get().strip()

    if valor == "":
        if valido:
            # Campo opcional vacío → sin borde destacado
            entry_ctk.configure(border_width=1, border_color="#4b5563")
        else:
            # Campo obligatorio vacío → borde rojo
            entry_ctk.configure(border_width=2, border_color="#ef4444")
    else:
        entry_ctk.configure(
            border_width=2,
            border_color="#10b981" if valido else "#ef4444"
        )

    if label_ctk:
        if "Opcional" in mensaje:
            color = "#9ca3af"
        elif valido:
            color = "#10b981"
        else:
            color = "#ef4444"
        label_ctk.configure(text=mensaje, text_color=color)


def registrar_validadores_teclado_ctk(entry_ctk, tipo_validacion: str, ventana) -> None:
    """
    Registra el validador de teclado de ValidadoresTeclado en un CTkEntry.

    Evita duplicar el registro manual de validatecommand en cada módulo.

    Args:
        entry_ctk:        El CTkEntry al que aplicar el bloqueo de teclado.
        tipo_validacion:  Uno de: 'dni', 'cuit', 'telefono', 'solo_numeros',
                          'solo_letras', 'letras_y_numeros', 'decimal', 'monto',
                          'email', 'nombre'.
        ventana:          La ventana (CTkToplevel o Tk) para register().
    """
    mapa = {
        'dni':             ValidadoresTeclado.dni,
        'cuit':            ValidadoresTeclado.cuit,
        'telefono':        ValidadoresTeclado.telefono,
        'solo_numeros':    ValidadoresTeclado.solo_numeros,
        'solo_letras':     ValidadoresTeclado.solo_letras,
        'letras_y_numeros':ValidadoresTeclado.letras_y_numeros,
        'decimal':         ValidadoresTeclado.decimal,
        'monto':           ValidadoresTeclado.decimal,
        'email':           ValidadoresTeclado.email,
        'nombre':          ValidadoresTeclado.solo_letras,
    }
    validador = mapa.get(tipo_validacion)
    if validador:
        vcmd = (ventana.register(validador), '%P')
        entry_ctk.configure(validate='key', validatecommand=vcmd)


def conectar_validacion_ctk(entry_ctk, label_ctk, tipo_validacion: str, ventana) -> None:
    """
    Configura un CTkEntry completo: bloqueo de teclado + feedback visual en
    tiempo real. Es el equivalente a EntryValidado para CTkEntry.

    Registra <KeyRelease> y <FocusOut> que llaman a aplicar_feedback_ctk().

    Args:
        entry_ctk:        CTkEntry a conectar.
        label_ctk:        CTkLabel de feedback (puede ser None).
        tipo_validacion:  Tipo de validación (ver registrar_validadores_teclado_ctk).
        ventana:          Ventana para register().
    """
    registrar_validadores_teclado_ctk(entry_ctk, tipo_validacion, ventana)

    def _on_change(event=None):
        valor = entry_ctk.get()
        vv = ValidadoresVisuales
        if tipo_validacion == 'nombre':
            valido, msg = vv.validar_nombre(valor)
        elif tipo_validacion == 'nombre_empresa':
            valido, msg = vv.validar_nombre_empresa(valor)
        elif tipo_validacion == 'dni':
            valido, msg = vv.validar_dni(valor)
        elif tipo_validacion == 'cuit':
            valido, msg = vv.validar_cuit(valor)
        elif tipo_validacion == 'cuit_obligatorio':
            valido, msg = vv.validar_cuit_obligatorio(valor)
        elif tipo_validacion == 'telefono':
            valido, msg = vv.validar_telefono(valor)
        elif tipo_validacion == 'telefono_obligatorio':
            valido, msg = vv.validar_telefono_obligatorio(valor)
        elif tipo_validacion == 'email':
            valido, msg = vv.validar_email(valor)
        elif tipo_validacion == 'monto':
            valido, msg = vv.validar_monto(valor)
        else:
            return  # Sin validación visual para tipos genéricos
        aplicar_feedback_ctk(entry_ctk, label_ctk, valido, msg)

    entry_ctk.bind('<KeyRelease>', _on_change)
    entry_ctk.bind('<FocusOut>', _on_change)
    # Aplicar estado inicial (útil en modo edición donde ya hay datos)
    _on_change()

# ============================================================================
# 📝 EJEMPLO DE USO
# ============================================================================

if __name__ == "__main__":
    root = tk.Tk()
    root.title("Test de Validaciones")
    root.geometry("500x400")
    root.config(bg="#f4f4f8")
    
    frame = tk.Frame(root, bg="#f4f4f8", padx=20, pady=20)
    frame.pack(fill="both", expand=True)
    
    frame.columnconfigure(1, weight=1)
    
    # Crear campos con validación
    entry_nombre, _ = crear_campo_validado(frame, "Nombre", "nombre", 0, obligatorio=True)
    entry_dni, _ = crear_campo_validado(frame, "DNI", "dni", 1, obligatorio=True)
    entry_cuit, _ = crear_campo_validado(frame, "CUIT", "cuit", 2, obligatorio=False)
    entry_tel, _ = crear_campo_validado(frame, "Teléfono", "telefono", 3, obligatorio=False)
    entry_email, _ = crear_campo_validado(frame, "Email", "email", 4, obligatorio=False)
    
    def validar_form():
        campos = {
            'Nombre': (entry_nombre.get(), 'nombre', True),
            'DNI': (entry_dni.get(), 'dni', True),
            'CUIT': (entry_cuit.get(), 'cuit', False),
            'Teléfono': (entry_tel.get(), 'telefono', False),
            'Email': (entry_email.get(), 'email', False),
        }
        
        valido, mensaje = ValidadorFormulario.validar_campos(campos)
        
        if valido:
            print("✅ FORMULARIO VÁLIDO")
        else:
            print(f"❌ ERROR: {mensaje}")
    
    tk.Button(frame, text="Validar Formulario", command=validar_form, 
              bg="#10b981", fg="white", font=("Segoe UI", 10, "bold"),
              relief="flat", padx=20, pady=10).grid(row=5, column=1, pady=20)
    
    root.mainloop()