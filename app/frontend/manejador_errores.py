# app/frontend/manejador_errores.py
# 🎯 SISTEMA CENTRALIZADO DE MANEJO DE ERRORES ESPECÍFICOS
from tkinter import messagebox
import mysql.connector
from typing import Optional, Tuple

# ============================================================================
# 📋 EXCEPCIONES PERSONALIZADAS
# ============================================================================

class ErrorNegocio(Exception):
    """Excepción base para errores de lógica de negocio."""
    def __init__(self, mensaje: str, titulo: str = "Error de Validación"):
        self.mensaje = mensaje
        self.titulo = titulo
        super().__init__(mensaje)

class DNIDuplicado(ErrorNegocio):
    def __init__(self, dni: str):
        super().__init__(
            f"⚠️ El DNI {dni} ya está registrado en el sistema.",
            "DNI Duplicado"
        )

class EmailDuplicado(ErrorNegocio):
    def __init__(self, email: str):
        super().__init__(
            f"⚠️ El email {email} ya está registrado en el sistema.",
            "Email Duplicado"
        )

class CUITDuplicado(ErrorNegocio):
    def __init__(self, cuit: str):
        super().__init__(
            f"⚠️ El CUIT {cuit} ya está registrado en el sistema.",
            "CUIT Duplicado"
        )

class StockInsuficiente(ErrorNegocio):
    def __init__(self, producto: str, disponible: float, solicitado: float):
        super().__init__(
            f"⚠️ Stock insuficiente para '{producto}'.\n\n"
            f"• Disponible: {disponible:.2f}\n"
            f"• Solicitado: {solicitado:.2f}\n"
            f"• Faltante: {solicitado - disponible:.2f}",
            "Stock Insuficiente"
        )

class SaldoInsuficiente(ErrorNegocio):
    def __init__(self, disponible: float, requerido: float):
        super().__init__(
            f"⚠️ Saldo insuficiente en caja.\n\n"
            f"• Saldo disponible: $ {disponible:,.2f}\n"
            f"• Monto requerido: $ {requerido:,.2f}\n"
            f"• Faltante: $ {requerido - disponible:,.2f}",
            "Saldo Insuficiente"
        )

class LimiteCreditoExcedido(ErrorNegocio):
    def __init__(self, limite: float, deuda_actual: float, venta: float):
        super().__init__(
            f"⚠️ Límite de crédito excedido.\n\n"
            f"• Límite total: $ {limite:,.2f}\n"
            f"• Deuda actual: $ {abs(deuda_actual):,.2f}\n"
            f"• Esta venta: $ {venta:,.2f}\n"
            f"• Crédito disponible: $ {max(0, limite - abs(deuda_actual)):,.2f}",
            "Límite de Crédito Excedido"
        )

class CajaYaAbierta(ErrorNegocio):
    def __init__(self, usuario: str):
        super().__init__(
            f"⚠️ El usuario '{usuario}' ya tiene una caja abierta.\n\n"
            "Debe cerrar la caja actual antes de abrir una nueva.",
            "Caja Ya Abierta"
        )

class CajaCerrada(ErrorNegocio):
    def __init__(self):
        super().__init__(
            "⚠️ No hay ninguna caja abierta.\n\n"
            "Debe abrir una caja antes de realizar esta operación.",
            "Caja Cerrada"
        )

class ProductoInactivo(ErrorNegocio):
    def __init__(self, producto: str):
        super().__init__(
            f"⚠️ El producto '{producto}' está inactivo.\n\n"
            "Solo se pueden vender productos activos.",
            "Producto Inactivo"
        )

class ClienteInactivo(ErrorNegocio):
    def __init__(self, cliente: str):
        super().__init__(
            f"⚠️ El cliente '{cliente}' está inactivo.\n\n"
            "Debe activar al cliente para operar con él.",
            "Cliente Inactivo"
        )

# ============================================================================
# 🔍 ANALIZADOR DE ERRORES DE MYSQL
# ============================================================================

class AnalizadorErroresMySQL:
    """Analiza errores de MySQL y los convierte en excepciones específicas."""
    
    @staticmethod
    def analizar(error: mysql.connector.Error, contexto: str = "") -> ErrorNegocio:
        """
        Analiza un error de MySQL y retorna una excepción específica.
        
        Args:
            error: Error de MySQL
            contexto: Información adicional (ej: "cliente", "proveedor")
        
        Returns:
            ErrorNegocio con mensaje específico
        """
        error_msg = str(error).lower()
        error_code = getattr(error, 'errno', None)
        
        # Error 1062: Duplicate entry
        if error_code == 1062 or 'duplicate' in error_msg:
            if 'dni' in error_msg:
                # Extraer DNI del mensaje si es posible
                dni = "ingresado"
                if contexto:
                    dni = contexto
                raise DNIDuplicado(dni)
            
            elif 'email' in error_msg:
                email = contexto if contexto else "ingresado"
                raise EmailDuplicado(email)
            
            elif 'cuit' in error_msg:
                cuit = contexto if contexto else "ingresado"
                raise CUITDuplicado(cuit)
            
            elif 'codigo_barras' in error_msg:
                raise ErrorNegocio(
                    "⚠️ El código de barras ya está registrado.",
                    "Código Duplicado"
                )
            
            elif 'nombre' in error_msg and 'usuario' in contexto.lower():
                raise ErrorNegocio(
                    f"⚠️ El nombre de usuario '{contexto}' ya existe.",
                    "Usuario Duplicado"
                )
            
            else:
                raise ErrorNegocio(
                    "⚠️ Ya existe un registro con estos datos.",
                    "Registro Duplicado"
                )
        
        # Error 1451: Cannot delete or update a parent row (Foreign Key)
        elif error_code == 1451:
            if 'cliente' in contexto.lower():
                raise ErrorNegocio(
                    "⚠️ No se puede eliminar el cliente porque tiene operaciones registradas.",
                    "Cliente con Operaciones"
                )
            elif 'proveedor' in contexto.lower():
                raise ErrorNegocio(
                    "⚠️ No se puede eliminar el proveedor porque tiene compras registradas.",
                    "Proveedor con Operaciones"
                )
            elif 'producto' in contexto.lower():
                raise ErrorNegocio(
                    "⚠️ No se puede eliminar el producto porque está en ventas/compras.",
                    "Producto en Uso"
                )
            else:
                raise ErrorNegocio(
                    "⚠️ No se puede eliminar porque tiene registros asociados.",
                    "Registro en Uso"
                )
        
        # Error 1452: Cannot add or update a child row (Foreign Key)
        elif error_code == 1452:
            raise ErrorNegocio(
                "⚠️ Referencia inválida. El registro relacionado no existe.",
                "Referencia Inválida"
            )
        
        # Error 1048: Column cannot be null
        elif error_code == 1048 or 'cannot be null' in error_msg:
            raise ErrorNegocio(
                "⚠️ Falta información obligatoria en el formulario.",
                "Campos Obligatorios"
            )
        
        # Error 1406: Data too long
        elif error_code == 1406 or 'too long' in error_msg:
            raise ErrorNegocio(
                "⚠️ Uno o más campos exceden la longitud máxima permitida.",
                "Datos Demasiado Largos"
            )
        
        # Error 1264: Out of range value
        elif error_code == 1264 or 'out of range' in error_msg:
            raise ErrorNegocio(
                "⚠️ Uno de los valores numéricos está fuera del rango permitido.",
                "Valor Fuera de Rango"
            )
        
        # Error de conexión
        elif 'lost connection' in error_msg or 'can\'t connect' in error_msg:
            raise ErrorNegocio(
                "⚠️ Se perdió la conexión con la base de datos.\n\n"
                "Verifica que el servidor MySQL esté activo.",
                "Error de Conexión"
            )
        
        # Error genérico de MySQL
        else:
            raise ErrorNegocio(
                f"⚠️ Error de base de datos:\n{str(error)}",
                "Error de Base de Datos"
            )

# ============================================================================
# 🎨 MANEJADOR DE ERRORES PARA UI
# ============================================================================

class ManejadorErroresUI:
    """Muestra errores específicos en messagebox."""
    
    @staticmethod
    def manejar_error(error: Exception, parent=None, contexto: str = ""):
        """
        Maneja cualquier excepción y la muestra apropiadamente.
        
        Args:
            error: Excepción a manejar
            parent: Ventana padre para el messagebox
            contexto: Contexto adicional (usado para errores MySQL)
        
        Returns:
            True si se manejó el error, False si es crítico
        """
        try:
            # Errores de negocio personalizados
            if isinstance(error, ErrorNegocio):
                messagebox.showerror(error.titulo, error.mensaje, parent=parent)
                return True
            
            # Errores de MySQL
            elif isinstance(error, mysql.connector.Error):
                try:
                    AnalizadorErroresMySQL.analizar(error, contexto)
                except ErrorNegocio as e:
                    messagebox.showerror(e.titulo, e.mensaje, parent=parent)
                    return True
            
            # ValueError con contexto específico
            elif isinstance(error, ValueError):
                msg = str(error)
                
                if "DNI_DUPLICADO" in msg or "dni" in msg.lower():
                    dni = contexto if contexto else "ingresado"
                    messagebox.showerror(
                        "DNI Duplicado",
                        f"⚠️ El DNI {dni} ya está registrado.",
                        parent=parent
                    )
                    return True
                
                elif "EMAIL_DUPLICADO" in msg or "email" in msg.lower():
                    messagebox.showerror(
                        "Email Duplicado",
                        f"⚠️ El email ya está registrado.",
                        parent=parent
                    )
                    return True
                
                elif "CUIT_DUPLICADO" in msg or "cuit" in msg.lower():
                    messagebox.showerror(
                        "CUIT Duplicado",
                        f"⚠️ El CUIT ya está registrado.",
                        parent=parent
                    )
                    return True
                
                elif "STOCK_INSUFICIENTE" in msg:
                    messagebox.showerror(
                        "Stock Insuficiente",
                        msg,
                        parent=parent
                    )
                    return True
                
                elif "SALDO_INSUFICIENTE" in msg:
                    messagebox.showerror(
                        "Saldo Insuficiente",
                        msg,
                        parent=parent
                    )
                    return True
                
                else:
                    messagebox.showwarning(
                        "Error de Validación",
                        str(error),
                        parent=parent
                    )
                    return True
            
            # Error genérico
            else:
                messagebox.showerror(
                    "Error Inesperado",
                    f"Ocurrió un error inesperado:\n\n{str(error)}",
                    parent=parent
                )
                return False
        
        except Exception as e:
            # Si hay error en el manejador mismo
            messagebox.showerror(
                "Error Crítico",
                f"Error crítico en el manejador de errores:\n{str(e)}",
                parent=parent
            )
            return False

# ============================================================================
# 🛠️ DECORADOR PARA FUNCIONES UI
# ============================================================================

def manejar_errores_ui(contexto: str = ""):
    """
    Decorador para manejar errores automáticamente en funciones de UI.
    
    Uso:
        @manejar_errores_ui(contexto="cliente")
        def guardar_cliente():
            # código...
    """
    def decorador(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                parent = kwargs.get('parent', None)
                ManejadorErroresUI.manejar_error(e, parent, contexto)
                return None
        return wrapper
    return decorador

# ============================================================================
# 📝 EJEMPLOS DE USO
# ============================================================================

if __name__ == "__main__":
    import tkinter as tk
    
    root = tk.Tk()
    root.withdraw()
    
    # Ejemplo 1: Error de DNI duplicado
    try:
        raise DNIDuplicado("12345678")
    except ErrorNegocio as e:
        ManejadorErroresUI.manejar_error(e)
    
    # Ejemplo 2: Error de stock insuficiente
    try:
        raise StockInsuficiente("Coca Cola 2L", disponible=5.0, solicitado=10.0)
    except ErrorNegocio as e:
        ManejadorErroresUI.manejar_error(e)
    
    # Ejemplo 3: Error de MySQL simulado
    try:
        error = mysql.connector.Error()
        error.errno = 1062
        error.msg = "Duplicate entry '12345678' for key 'dni'"
        AnalizadorErroresMySQL.analizar(error, "12345678")
    except ErrorNegocio as e:
        ManejadorErroresUI.manejar_error(e)
    
    print("✅ Ejemplos de manejo de errores ejecutados")