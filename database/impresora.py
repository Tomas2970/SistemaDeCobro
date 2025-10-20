"""
Módulo de Impresión de Tickets
Sistema de Cobro - Supermercado Don Atilio

IMPORTANTE: 
- Las impresoras térmicas funcionan como impresoras normales de Windows
- NO requieren librerías especiales en la mayoría de casos
- Se imprimen como documentos de texto
"""

import os
import win32print
import win32api
from datetime import datetime
from database.DB import obtener_detalle_venta, obtener_clientes

# =====================================
# Configuración
# =====================================
# Nombre de la impresora térmica en Windows
# Para ver el nombre exacto: Panel de Control → Impresoras
NOMBRE_IMPRESORA = "POS-80"  # Cambiar por el nombre real de tu impresora
# Ejemplos comunes: "POS-80", "TM-T20", "Ticket Printer", etc.

# Ancho del ticket (caracteres)
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
    return f"${precio:,.2f}"

def justificar_texto(izquierda, derecha, ancho=ANCHO_TICKET):
    """Justifica texto a izquierda y derecha"""
    espacios = ancho - len(izquierda) - len(derecha)
    return izquierda + ' ' * espacios + derecha

# =====================================
# Función Principal de Impresión
# =====================================
def imprimir_ticket(id_venta, nombre_vendedor="Vendedor"):
    """
    Imprime un ticket de venta
    
    Args:
        id_venta: ID de la venta a imprimir
        nombre_vendedor: Nombre del vendedor (opcional)
    
    Returns:
        True si se imprimió correctamente, False si hubo error
    """
    try:
        # Obtener datos de la venta
        items = obtener_detalle_venta(id_venta)
        
        if not items:
            print(f"❌ Error: No se encontró venta con ID {id_venta}")
            return False
        
        # Generar contenido del ticket
        ticket = generar_contenido_ticket(id_venta, items, nombre_vendedor)
        
        # Imprimir
        enviar_a_impresora(ticket)
        
        print(f"✅ Ticket #{id_venta} impreso correctamente")
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
    ticket.append(centrar_texto("Dirección del Local"))
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
    ticket.append("\n")
    
    # ========================================
    # PRODUCTOS
    # ========================================
    ticket.append("PRODUCTO                  CANT  PRECIO")
    ticket.append(linea_separadora())
    
    total = 0
    for item in items:
        nombre = item['producto'][:25]  # Truncar si es muy largo
        cantidad = item['cantidad']
        precio = item['precio_unitario']
        subtotal = item['subtotal']
        
        # Línea 1: Nombre del producto
        ticket.append(nombre)
        
        # Línea 2: Cantidad, precio unitario y subtotal
        linea = f"  {cantidad} x {formato_precio(precio)}"
        linea = justificar_texto(linea, formato_precio(subtotal))
        ticket.append(linea)
        
        total += subtotal
    
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
    ticket.append(centrar_texto("Este ticket no es válido"))
    ticket.append(centrar_texto("como factura fiscal"))
    ticket.append("\n\n\n")  # Espacio para cortar el ticket
    
    # Unir todas las líneas
    return '\n'.join(ticket)

# =====================================
# Funciones de Impresión
# =====================================
def enviar_a_impresora(contenido):
    """
    Envía el contenido a la impresora térmica
    
    Args:
        contenido: String con el contenido a imprimir
    """
    try:
        # Obtener impresora por defecto o la configurada
        impresora = obtener_impresora()
        
        if not impresora:
            print("⚠️  No se encontró impresora configurada")
            # Guardar en archivo como alternativa
            guardar_ticket_txt(contenido)
            return
        
        # Método 1: Usando win32print (Recomendado para Windows)
        imprimir_con_win32(contenido, impresora)
        
    except Exception as e:
        print(f"❌ Error al enviar a impresora: {e}")
        # Alternativa: guardar en archivo
        guardar_ticket_txt(contenido)

def imprimir_con_win32(contenido, impresora):
    """
    Imprime usando la API de Windows (win32print)
    
    Requiere: pip install pywin32
    """
    try:
        # Abrir impresora
        hPrinter = win32print.OpenPrinter(impresora)
        
        try:
            # Iniciar documento
            hJob = win32print.StartDocPrinter(hPrinter, 1, ("Ticket", None, "RAW"))
            
            try:
                win32print.StartPagePrinter(hPrinter)
                
                # Enviar contenido
                contenido_bytes = contenido.encode('cp850')  # Codificación para impresoras
                win32print.WritePrinter(hPrinter, contenido_bytes)
                
                win32print.EndPagePrinter(hPrinter)
                
            finally:
                win32print.EndDocPrinter(hPrinter)
                
        finally:
            win32print.ClosePrinter(hPrinter)
        
        print("✅ Impresión enviada correctamente")
        
    except Exception as e:
        print(f"❌ Error en win32print: {e}")
        raise

def imprimir_con_comando_windows(contenido):
    """
    Alternativa: Imprime usando el comando PRINT de Windows
    No requiere librerías adicionales
    """
    try:
        # Crear archivo temporal
        archivo_temp = "ticket_temp.txt"
        
        with open(archivo_temp, 'w', encoding='cp850') as f:
            f.write(contenido)
        
        # Enviar a impresora usando comando de Windows
        impresora = obtener_impresora()
        os.system(f'PRINT /D:"{impresora}" {archivo_temp}')
        
        # Eliminar archivo temporal
        os.remove(archivo_temp)
        
        print("✅ Ticket impreso con comando Windows")
        
    except Exception as e:
        print(f"❌ Error al imprimir con comando: {e}")

def guardar_ticket_txt(contenido):
    """
    Guarda el ticket en un archivo .txt como alternativa
    Útil para pruebas o cuando no hay impresora
    """
    try:
        # Crear carpeta si no existe
        if not os.path.exists('tickets'):
            os.makedirs('tickets')
        
        # Nombre del archivo con timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nombre_archivo = f"tickets/ticket_{timestamp}.txt"
        
        # Guardar
        with open(nombre_archivo, 'w', encoding='utf-8') as f:
            f.write(contenido)
        
        print(f"💾 Ticket guardado en: {nombre_archivo}")
        print("⚠️  (No se imprimió porque no hay impresora configurada)")
        
        return nombre_archivo
        
    except Exception as e:
        print(f"❌ Error al guardar ticket: {e}")
        return None

# =====================================
# Funciones de Configuración
# =====================================
def obtener_impresora():
    """
    Obtiene el nombre de la impresora a usar
    
    Returns:
        Nombre de la impresora o None si no se encuentra
    """
    try:
        # Intentar usar la impresora configurada
        impresoras = win32print.EnumPrinters(2)
        nombres_impresoras = [imp[2] for imp in impresoras]
        
        # Buscar la impresora configurada
        if NOMBRE_IMPRESORA in nombres_impresoras:
            return NOMBRE_IMPRESORA
        
        # Si no existe, usar la impresora por defecto
        impresora_default = win32print.GetDefaultPrinter()
        print(f"⚠️  Usando impresora por defecto: {impresora_default}")
        return impresora_default
        
    except Exception as e:
        print(f"❌ Error al obtener impresora: {e}")
        return None

def listar_impresoras():
    """
    Lista todas las impresoras disponibles en Windows
    Útil para saber el nombre exacto de tu impresora
    """
    try:
        impresoras = win32print.EnumPrinters(2)
        
        print("\n📋 IMPRESORAS DISPONIBLES:")
        print("="*50)
        
        for i, impresora in enumerate(impresoras, 1):
            nombre = impresora[2]
            print(f"{i}. {nombre}")
        
        print("="*50)
        print("\n💡 Copia el nombre exacto y ponlo en NOMBRE_IMPRESORA")
        print(f"   Ejemplo: NOMBRE_IMPRESORA = \"{impresoras[0][2]}\"")
        
    except Exception as e:
        print(f"❌ Error al listar impresoras: {e}")

def configurar_impresora(nombre):
    """
    Configura el nombre de la impresora a usar
    
    Args:
        nombre: Nombre exacto de la impresora en Windows
    """
    global NOMBRE_IMPRESORA
    NOMBRE_IMPRESORA = nombre
    print(f"✅ Impresora configurada: {nombre}")

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
    ticket.append("Si puedes leer esto,")
    ticket.append("la impresora funciona correctamente!")
    ticket.append("\n")
    ticket.append(centrar_texto(f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}"))
    ticket.append("\n\n\n")
    
    contenido = '\n'.join(ticket)
    
    try:
        enviar_a_impresora(contenido)
        print("✅ Ticket de prueba enviado")
    except Exception as e:
        print(f"❌ Error: {e}")

# =====================================
# Ejemplo de uso
# =====================================
if __name__ == "__main__":
    print("╔══════════════════════════════════════════════════════════╗")
    print("║     MÓDULO DE IMPRESIÓN DE TICKETS                      ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print()
    
    # 1. Listar impresoras disponibles
    listar_impresoras()
    
    # 2. Configurar impresora (opcional)
    # configurar_impresora("TU_IMPRESORA_AQUI")
    
    # 3. Imprimir ticket de prueba
    print("\n¿Desea imprimir un ticket de prueba? (s/n): ", end='')
    respuesta = input().lower()
    
    if respuesta == 's':
        imprimir_ticket_prueba()
    
    # 4. Ejemplo: Imprimir una venta real
    # imprimir_ticket(id_venta=1, nombre_vendedor="Admin")