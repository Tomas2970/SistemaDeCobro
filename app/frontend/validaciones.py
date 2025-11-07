"""
Funciones de validación reutilizables para formularios.
Sistema de Cobro - Supermercado Don Atilio
"""
import re
import unicodedata

def validar_email(email: str) -> bool:
    """
    Valida formato de email.
    
    Args:
        email: String con el email a validar
        
    Returns:
        True si es válido o vacío (NULL permitido), False si es inválido
        
    Ejemplos:
        validar_email("") -> True (NULL permitido)
        validar_email("cliente@ejemplo.com") -> True
        validar_email("mail_invalido") -> False
    """
    if not email or not email.strip():
        return True  # Email vacío es válido (NULL en BD)
        
    # Patrón RFC 5322 simplificado
    patron = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(patron, email.strip()))

def normalizar_texto(texto: str) -> str:
    """
    Convierte a minúsculas y quita acentos para búsquedas.
    
    Args:
        texto: String a normalizar
        
    Returns:
        Texto en minúsculas sin acentos
        
    Ejemplos:
        normalizar_texto("José García") -> "jose garcia"
        normalizar_texto("ÑANDÚ") -> "nandu"
    """
    if not texto:
        return ""
        
    # Descomponer caracteres Unicode (á -> a + ´)
    texto_nfd = unicodedata.normalize('NFD', texto.lower())
        
    # Quitar marcas diacríticas (acentos)
    texto_sin_acentos = ''.join(
        char for char in texto_nfd 
        if unicodedata.category(char) != 'Mn'
    )
        
    return texto_sin_acentos

def validar_dni_argentino(dni: str) -> bool:
    """
    Valida formato de DNI argentino (7-8 dígitos).
    
    Args:
        dni: String con el DNI a validar
        
    Returns:
        True si es válido o vacío, False si es inválido
    """
    if not dni or not dni.strip():
        return True  # DNI vacío es válido (NULL en BD)
        
    # Remover puntos y espacios
    dni_limpio = dni.replace('.', '').replace(' ', '').strip()
        
    # Debe tener 7-8 dígitos numéricos
    if not dni_limpio.isdigit():
        return False
        
    if len(dni_limpio) not in [7, 8]:
        return False
        
    return True

def formatear_precio(precio: float) -> str:
    """Formatea un precio con separadores de miles."""
    try:
        return f"$ {float(precio):,.2f}"
    except:
        return "$ 0.00"