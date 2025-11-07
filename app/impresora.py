"""
Módulo de Impresión de Tickets
Sistema de Cobro - Supermercado Don Atilio
"""

import os
import win32print
import win32api
from datetime import datetime

# =====================================
# Configuración
# =====================================
NOMBRE_IMPRESORA = "sam4s giant 100s"
ANCHO_TICKET = 42

# =====================================
# Funciones de Formato
# =====================================
def centrar_texto(texto, ancho=ANCHO_TICKET):
    """Centra un texto en el ancho del ticket"""
    espacios = (ancho - len(texto)) // 2
    return ' ' * espacios + texto

def linea_separadora(caracter='-', ancho=ANCHO_TICKET):
    """Genera una línea separadora"""
    return caracter * ancho

def formato_precio(precio):
    """Formatea un precio con 2 decimales"""
    try:
        return f"${float(precio):,.2f}"
    except Exception:
        return "$ 0.00"

def justificar_texto(izquierda, derecha, ancho=ANCHO_TICKET):
    """Justifica texto a izquierda y derecha"""
    espacios = ancho - len(izquierda) - len(derecha)
    return izquierda + ' ' * espacios + derecha

# =====================================
# Función Principal de Impresión
# =====================================
def imprimir_ticket(id_venta, items_de_la_venta: list, nombre_vendedor="Vendedor"):
    """
    Imprime un ticket de venta
    
    Args:
        id_venta: ID de la venta a imprimir
        items_de_la_venta: Una LISTA de tuplas (id_prod, nombre, cant, precio, cod)
        nombre_vendedor: Nombre del vendedor (opcional)
    
    Returns:
        True si se imprimió correctamente, False si hubo error
    """
    try:
        if not items_de_la_venta:
            print(f"❌ Error: No hay items para imprimir en la venta #{id_venta}")
            return False
        
        # Generar contenido del ticket
        ticket = generar_contenido_ticket(id_venta, items_de_la_venta, nombre_vendedor)
        
        # Imprimir
        enviar_a_impresora(ticket)
        
        print(f"✅ Ticket #{id_venta} enviado a la impresora '{NOMBRE_IMPRESORA}'")
        return True
        
    except Exception as e:
        print(f"❌ Error al imprimir ticket: {e}")
        return False

def generar_contenido_ticket(id_venta, items, nombre_vendedor):
    """
    Genera el contenido formateado del ticket
    
    Returns:
        String con el contenido completo del ticket
    """
    ticket = []
    
    # ========================================
    # ENCABEZADO
    # ========================================
    ticket.append("\n")
    ticket.append(centrar_texto("SUPERMERCADO DON ATILIO"))
    ticket.append(centrar_texto("==============================="))
    ticket.append(centrar_texto("Direccion del Local"))
    ticket.append(centrar_texto("Tel: (381) 123-4567"))
    ticket.append(centrar_texto("CUIT: 20-12345678-9"))
    ticket.append(linea_separadora())
    ticket.append("\n")
    
    # ========================================
    # INFORMACIÓN DE LA VENTA
    # ========================================
    fecha_hora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    ticket.append(f"Fecha: {fecha_hora}")
    ticket.append(f"Ticket N°: {id_venta:06d}")
    ticket.append(f"Vendedor: {nombre_vendedor}")
    ticket.append(linea_separadora())
    
    # ========================================
    # PRODUCTOS (Formato 4 Columnas)
    # ========================================
    
    # --- ¡MODIFICACIÓN DE ANCHO! ---
    # Anchos: 15 (Prod) + 6 (Cant) + 8 (P.Unit) + 10 (Subt) + 3 espacios = 42
    
    head_prod = "PRODUCTO".ljust(15)  # (15)
    head_cant = "CANT".rjust(6)       # (6)
    head_punit = "P.UNIT".rjust(8)    # (8)
    head_subt = "SUBTOTAL".rjust(10)  # (10)
    # --- FIN MODIFICACIÓN ---
    
    ticket.append(f"{head_prod} {head_cant} {head_punit} {head_subt}")
    ticket.append(linea_separadora())
    
    total = 0
    # items es: (id_prod, nombre, cantidad, precio, cod)
    for (id_prod, nombre, cantidad, precio, cod) in items:
        
        # Aseguramos que cantidad sea float para la multiplicación
        try:
            cantidad_float = float(cantidad)
        except ValueError:
            cantidad_float = 0.0
            
        subtotal = cantidad_float * float(precio)
        total += subtotal
        
        # Formatear datos para las columnas
        nombre_col = nombre[:15].ljust(15) # Truncar a 15
        
        # --- ¡MODIFICACIÓN! Formato de cantidad (pesable/entero) ---
        if cantidad_float == int(cantidad_float):
            cant_str = str(int(cantidad_float)) # Muestra "5"
        else:
            cant_str = f"{cantidad_float:.3f}" # Muestra "5.250"
        
        cantidad_col = cant_str.rjust(6) # Alinea en 6 chars
        # --- FIN MODIFICACIÓN ---
        
        p_unit_col = formato_precio(precio).rjust(8)
        subtotal_col = formato_precio(subtotal).rjust(10)
        
        # Unir en una sola línea
        linea = f"{nombre_col} {cantidad_col} {p_unit_col} {subtotal_col}"
        ticket.append(linea)

        # Si el nombre es más largo que 15, imprimir el resto abajo
        if len(nombre) > 15:
            resto_nombre = "  " + nombre[15:]
            ticket.append(resto_nombre[:ANCHO_TICKET])
    
    ticket.append(linea_separadora())
    ticket.append("\n")
    
    # ========================================
    # TOTAL
    # ========================================
    ticket.append(justificar_texto("TOTAL:", formato_precio(total)))
    ticket.append(linea_separadora('='))
    ticket.append("\n")
    
    # ========================================
    # PIE DE PÁGINA
    # ========================================
    ticket.append(centrar_texto("¡Gracias por su compra!"))
    ticket.append(centrar_texto("Vuelva pronto"))
    ticket.append("\n")
    ticket.append(centrar_texto("Este ticket no es valido"))
    ticket.append(centrar_texto("como factura fiscal"))
    ticket.append("\n\n\n")
    
    # Unir todas las líneas
    return '\n'.join(ticket)


# =====================================
# Funciones de Impresión (TU MEJORA)
# =====================================
def enviar_a_impresora(contenido):
    """
    Envía el contenido a la impresora térmica con manejo robusto de codificación.
    """
    try:
        impresora = obtener_impresora()
        
        if not impresora:
            print(f"⚠️  No se encontró impresora '{NOMBRE_IMPRESORA}' ni una por defecto.")
            guardar_ticket_txt(contenido)
            return
        
        imprimir_con_win32(contenido, impresora)
        
    except Exception as e:
        print(f"❌ Error al enviar a impresora: {e}")
        guardar_ticket_txt(contenido)

def imprimir_con_win32(contenido, impresora):
    """
    Imprime usando la API de Windows (win32print) con manejo robusto de codificación.
    """
    try:
        hPrinter = win32print.OpenPrinter(impresora)
        try:
            hJob = win32print.StartDocPrinter(hPrinter, 1, ("Ticket", None, "RAW"))
            try:
                win32print.StartPagePrinter(hPrinter)
                
                # ¡TU MEJORA!
                contenido_bytes = codificar_para_impresora(contenido)
                win32print.WritePrinter(hPrinter, contenido_bytes)
                
                win32print.EndPagePrinter(hPrinter)
            finally:
                win32print.EndDocPrinter(hPrinter)
        finally:
            win32print.ClosePrinter(hPrinter)
        
        print(f"✅ Impresión enviada correctamente a {impresora}")
        
    except Exception as e:
        print(f"❌ Error en win32print: {e}")
        raise


def codificar_para_impresora(contenido: str) -> bytes:
    """
    Codifica el contenido del ticket con el mejor encoding disponible.
    (Esta es tu excelente función)
    """
    encodings = [
        ('cp850', 'strict'),   # Mejor para español (tiene ñ, á, é, etc.)
        ('cp437', 'replace'),  # Común en impresoras térmicas
        ('latin-1', 'replace'),# ISO-8859-1
        ('utf-8', 'replace')   # Último recurso
    ]
    
    for encoding, error_mode in encodings:
        try:
            contenido_bytes = contenido.encode(encoding, errors=error_mode)
            print(f"✅ Codificación exitosa: {encoding}")
            return contenido_bytes
        except UnicodeEncodeError:
            print(f"⚠️  Encoding {encoding} falló, probando siguiente...")
            continue
    
    print("⚠️  Usando codificación de emergencia: cp850 con reemplazo de caracteres")
    return contenido.encode('cp850', errors='replace')


# =====================================
# Funciones de Soporte
# =====================================
def guardar_ticket_txt(contenido):
    """
    Guarda el ticket en un archivo .txt como alternativa
    """
    try:
        if not os.path.exists('tickets'):
            os.makedirs('tickets')
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nombre_archivo = f"tickets/ticket_{timestamp}.txt"
        
        with open(nombre_archivo, 'w', encoding='utf-8') as f:
            f.write(contenido)
        
        print(f"💾 Ticket guardado en: {nombre_archivo}")
        print("⚠️  (No se imprimió porque no hay impresora configurada)")
        
        return nombre_archivo
        
    except Exception as e:
        print(f"❌ Error al guardar ticket: {e}")
        return None

def obtener_impresora():
    """
    Obtiene el nombre de la impresora a usar
    """
    try:
        impresoras = win32print.EnumPrinters(2) 
        nombres_impresoras = [imp[2] for imp in impresoras]
        
        if NOMBRE_IMPRESORA in nombres_impresoras:
            return NOMBRE_IMPRESORA
        
        print(f"⚠️  Advertencia: No se encontró la impresora '{NOMBRE_IMPRESORA}'.")
        impresora_default = win32print.GetDefaultPrinter()
        print(f"    Usando la impresora por defecto: {impresora_default}")
        return impresora_default
        
    except Exception as e:
        print(f"❌ Error al obtener impresora: {e}")
        return None

def listar_impresoras():
    """
    Lista todas las impresoras disponibles en Windows
    """
    try:
        impresoras = win32print.EnumPrinters(2)
        
        print("\n📋 IMPRESORAS DISPONIBLES EN WINDOWS:")
        print("="*50)
        
        for i, impresora in enumerate(impresoras, 1):
            nombre = impresora[2]
            print(f"{i}. {nombre}")
        
        print("="*50)
        print(f"\n💡 Asegúrate de que el nombre en la línea 18 sea EXACTO:")
        print(f"   NOMBRE_IMPRESORA = \"{NOMBRE_IMPRESORA}\"")
        
    except Exception as e:
        print(f"❌ Error al listar impresoras: {e}")

# =====================================
# Funciones de Prueba
# =====================================
def imprimir_ticket_prueba():
    """
    Imprime un ticket de prueba para verificar la impresora
    """
    ticket = []
    ticket.append("\n")
    ticket.append(centrar_texto("=== TICKET DE PRUEBA ==="))
    ticket.append("\n")
    ticket.append(centrar_texto("SUPERMERCADO DON ATILIO"))
    ticket.append(linea_separadora())
    ticket.append("\n")
    ticket.append("Si puedes leer esto, ¡funciona!")
    ticket.append("Prueba de caracteres: ñ Ñ á é í ó ú $")
    ticket.append("\n")
    
    # --- Prueba del nuevo formato ---
    head_prod = "PRODUCTO".ljust(15)
    head_cant = "CANT".rjust(6)
    head_punit = "P.UNIT".rjust(8)
    head_subt = "SUBTOTAL".rjust(10)
    ticket.append(f"\n{head_prod} {head_cant} {head_punit} {head_subt}")
    ticket.append(linea_separadora('.'))
    # Item 1 (Entero)
    nombre_col = "Producto A".ljust(15)
    cantidad_col = "2".rjust(6)
    p_unit_col = "$100.00".rjust(8)
    subtotal_col = "$200.00".rjust(10)
    ticket.append(f"{nombre_col} {cantidad_col} {p_unit_col} {subtotal_col}")
    # Item 2 (Pesable)
    nombre_col = "Producto Pesable".ljust(15)
    cantidad_col = "1.250".rjust(6)
    p_unit_col = "$100.00".rjust(8)
    subtotal_col = "$125.00".rjust(10)
    ticket.append(f"{nombre_col} {cantidad_col} {p_unit_col} {subtotal_col}")
    ticket.append(linea_separadora('.'))
    # --- Fin Prueba ---
    
    ticket.append("\n")
    ticket.append(centrar_texto(f"Modelo: {NOMBRE_IMPRESORA}"))
    ticket.append(centrar_texto(f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}"))
    ticket.append("\n\n\n")
    
    contenido = '\n'.join(ticket)
    
    try:
        enviar_a_impresora(contenido)
        print("✅ Ticket de prueba enviado")
    except Exception as e:
        print(f"❌ Error: {e}")
