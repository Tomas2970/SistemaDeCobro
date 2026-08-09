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
NOMBRE_IMPRESORA = "SAM4S GIANT-100"
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
# Función Principal de Impresión (Ticket Venta)
# =====================================
def imprimir_ticket(id_venta, items_de_la_venta: list, nombre_vendedor="Vendedor", 
                   metodo_pago="efectivo", monto_entregado=0, vuelto=0, cliente="Consumidor Final"):
    """
    Imprime un ticket de venta
    """
    try:
        if not items_de_la_venta:
            print(f"❌ Error: No hay items para imprimir en la venta #{id_venta}")
            return False
        
        ticket = generar_contenido_ticket(id_venta, items_de_la_venta, nombre_vendedor, 
                                        metodo_pago, monto_entregado, vuelto, cliente)
        
        enviar_a_impresora(ticket)
        print(f"✅ Ticket #{id_venta} enviado a la impresora")
        return True
        
    except Exception as e:
        print(f"❌ Error al imprimir ticket: {e}")
        return False

def generar_contenido_ticket(id_venta, items, nombre_vendedor, metodo_pago, 
                           monto_entregado, vuelto, cliente):
    """Genera el contenido del ticket de venta"""
    ticket = []
    
    # Encabezado
    ticket.append("\n")
    ticket.append(centrar_texto("SUPERMERCADO DON ATILIO"))
    ticket.append(centrar_texto("==============================="))
    ticket.append(centrar_texto("Direccion del Local"))
    ticket.append(centrar_texto("Tel: (381) 123-4567"))
    ticket.append(centrar_texto("CUIT: 20-12345678-9"))
    ticket.append(linea_separadora())
    
    # Info Venta
    fecha_hora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    ticket.append(f"Fecha: {fecha_hora}")
    ticket.append(f"Ticket N°: {id_venta:06d}")
    ticket.append(f"Vendedor: {nombre_vendedor}")
    ticket.append(f"Cliente : {cliente}")
    ticket.append(linea_separadora())
    
    # Columnas
    head_prod = "PRODUCTO".ljust(15)
    head_cant = "CANT".rjust(6)
    head_punit = "P.UNIT".rjust(8)
    head_subt = "SUBTOTAL".rjust(10)
    ticket.append(f"{head_prod} {head_cant} {head_punit} {head_subt}")
    ticket.append(linea_separadora())
    
    total = 0
    for (id_prod, nombre, cantidad, precio, cod) in items:
        try: cantidad_float = float(cantidad)
        except: cantidad_float = 0.0
            
        subtotal = cantidad_float * float(precio)
        total += subtotal
        
        nombre_col = nombre[:15].ljust(15)
        
        if cantidad_float == int(cantidad_float):
            cant_str = str(int(cantidad_float))
        else:
            cant_str = f"{cantidad_float:.3f}"
        
        cantidad_col = cant_str.rjust(6)
        p_unit_col = formato_precio(precio).rjust(8)
        subtotal_col = formato_precio(subtotal).rjust(10)
        
        ticket.append(f"{nombre_col} {cantidad_col} {p_unit_col} {subtotal_col}")

        if len(nombre) > 15:
            ticket.append("  " + nombre[15:ANCHO_TICKET])
    
    ticket.append(linea_separadora())
    
    # Totales
    ticket.append(justificar_texto("TOTAL:", formato_precio(total)))
    ticket.append(linea_separadora('='))
    
    # Pago
    ticket.append("INFORMACION DE PAGO:")
    ticket.append(linea_separadora('.'))
    
    metodo_str = metodo_pago.upper().replace("_", " ")
    ticket.append(f"Metodo: {metodo_str}")
    
    if metodo_pago == "efectivo" and monto_entregado > 0:
        ticket.append(justificar_texto("Entrego:", formato_precio(monto_entregado)))
        if vuelto > 0:
            ticket.append(justificar_texto("Vuelto :", formato_precio(vuelto)))
    
    ticket.append(linea_separadora('='))
    ticket.append("\n")
    
    # Pie
    ticket.append(centrar_texto("¡Gracias por su compra!"))
    ticket.append(centrar_texto("Vuelva pronto"))
    ticket.append("\n")
    ticket.append(centrar_texto("Este ticket no es valido"))
    ticket.append(centrar_texto("como factura fiscal"))
    ticket.append("\n\n\n")
    
    return '\n'.join(ticket)


# =====================================
# Envío a Impresora
# =====================================
def enviar_a_impresora(contenido):
    try:
        impresora = obtener_impresora()
        if not impresora:
            guardar_ticket_txt(contenido)
            return
        imprimir_con_win32(contenido, impresora)
    except Exception as e:
        print(f"❌ Error al enviar a impresora: {e}")
        guardar_ticket_txt(contenido)

def imprimir_con_win32(contenido, impresora):
    try:
        hPrinter = win32print.OpenPrinter(impresora)
        try:
            hJob = win32print.StartDocPrinter(hPrinter, 1, ("Ticket", None, "RAW"))
            try:
                win32print.StartPagePrinter(hPrinter)
                contenido_bytes = codificar_para_impresora(contenido)
                win32print.WritePrinter(hPrinter, contenido_bytes)
                win32print.EndPagePrinter(hPrinter)
            finally:
                win32print.EndDocPrinter(hPrinter)
        finally:
            win32print.ClosePrinter(hPrinter)
    except Exception as e:
        print(f"❌ Error en win32print: {e}")
        raise

def codificar_para_impresora(contenido: str) -> bytes:
    encodings = [('cp850', 'strict'), ('cp437', 'replace'), ('latin-1', 'replace'), ('utf-8', 'replace')]
    for encoding, error_mode in encodings:
        try:
            return contenido.encode(encoding, errors=error_mode)
        except UnicodeEncodeError:
            continue
    return contenido.encode('cp850', errors='replace')

def guardar_ticket_txt(contenido):
    try:
        if not os.path.exists('tickets'): os.makedirs('tickets')
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        with open(f"tickets/ticket_{timestamp}.txt", 'w', encoding='utf-8') as f:
            f.write(contenido)
    except: pass

def obtener_impresora():
    try:
        impresoras = [imp[2] for imp in win32print.EnumPrinters(2)]
        if NOMBRE_IMPRESORA in impresoras: return NOMBRE_IMPRESORA
        return win32print.GetDefaultPrinter()
    except: return None

# =====================================
# Reportes Gerenciales
# =====================================

def imprimir_resumen_diario(datos: dict):
    """
    Imprime el 'Reporte Gerencial' con desglose por vendedor y financiero.
    """
    ticket = []
    ticket.append("\n")
    ticket.append(centrar_texto("SUPERMERCADO DON ATILIO"))
    ticket.append(centrar_texto("==========================="))
    ticket.append(centrar_texto("REPORTE GERENCIAL DEL DIA"))
    ticket.append(linea_separadora())
    
    fecha_str = datetime.strptime(datos['fecha'], "%Y-%m-%d").strftime("%d/%m/%Y")
    ticket.append(f"Fecha: {fecha_str}")
    ticket.append(linea_separadora())
    
    # 1. VENTAS POR VENDEDOR
    if 'ventas_por_vendedor' in datos and datos['ventas_por_vendedor']:
        ticket.append("\n>> VENTAS POR VENDEDOR:")
        for vend in datos['ventas_por_vendedor']:
            nombre = vend['vendedor'][:20].ljust(20)
            monto = formato_precio(vend['monto_total'])
            ticket.append(justificar_texto(nombre, monto))
        ticket.append(linea_separadora('-'))

    # 2. VENTAS POR CATEGORÍA
    ticket.append("\n>> VENTAS POR CATEGORIA:")
    for cat in datos.get('categorias', []):
        nombre = cat['nombre_categoria'][:20].ljust(20)
        cant = f"({int(cat['cantidad_ventas'])})"
        monto = formato_precio(cat['monto_total'])
        ticket.append(justificar_texto(f"{nombre} {cant}", monto))
    
    ticket.append(linea_separadora('='))
    ticket.append(justificar_texto(
        f"TOTAL FACTURADO ({datos['total_ventas']})",
        formato_precio(datos['monto_total'])
    ))
    ticket.append(linea_separadora('='))
    
    # 3. DESGLOSE FINANCIERO (MÉTODOS DE PAGO)
    ticket.append("\n>> DINERO REAL (DESGLOSE):")
    metodos = datos.get('metodos_pago', {})
    
    efectivo = metodos.get('efectivo', 0.0)
    tarjeta = metodos.get('tarjeta', 0.0)
    transf = metodos.get('transferencia', 0.0)
    bancos = tarjeta + transf
    cta_cte = metodos.get('cuenta_corriente', 0.0)
    
    ticket.append(justificar_texto("Efectivo (Caja):", formato_precio(efectivo)))
    ticket.append(justificar_texto("Bancos (Tarj/Trans):", formato_precio(bancos)))
    ticket.append(justificar_texto("A Cobrar (Fiado):", formato_precio(cta_cte)))
    
    ticket.append(linea_separadora('='))
    
    # 4. MOVIMIENTOS DE CAJA (Solo si hubo extras)
    mov = datos.get('movimientos_caja', {})
    if mov and (mov.get('cobros_cc', 0) > 0 or mov.get('egresos', 0) > 0):
        ticket.append("\n>> MOVIMIENTOS EXTRA CAJA:")
        if mov.get('cobros_cc', 0) > 0:
            ticket.append(justificar_texto("+ Cobros C.C.:", formato_precio(mov['cobros_cc'])))
        if mov.get('egresos', 0) > 0:
            ticket.append(justificar_texto("- Egresos/Retiros:", formato_precio(mov['egresos'])))
        
        ticket.append(linea_separadora('.'))
        ticket.append(justificar_texto("EFECTIVO FINAL:", formato_precio(mov['efectivo_final'])))
    
    ticket.append("\n\n\n")
    enviar_a_impresora('\n'.join(ticket))


def imprimir_cierre_caja(datos_cierre, movimientos, nombre_usuario):
    """
    🔥 MEJORADO: Imprime el ticket de cierre de caja con medios de pago completos
    """
    ticket = []
    ticket.append("\n")
    ticket.append(centrar_texto("SUPERMERCADO DON ATILIO"))
    ticket.append(centrar_texto("==========================="))
    ticket.append(centrar_texto("CIERRE DE CAJA"))
    ticket.append(linea_separadora())
    
    # Fechas
    fecha_apertura_raw = datos_cierre.get('fecha_apertura')
    fecha_cierre_actual = datetime.now().strftime("%d/%m/%Y %H:%M")
    
    if fecha_apertura_raw:
        if isinstance(fecha_apertura_raw, str):
            # CORREGIDO: convertir "2026-03-04 13:42:37" a "04/03/2026 13:42"
            for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
                try:
                    f_ap = datetime.strptime(fecha_apertura_raw, fmt).strftime("%d/%m/%Y %H:%M")
                    break
                except ValueError:
                    continue
            else:
                f_ap = fecha_apertura_raw
        else:
            f_ap = fecha_apertura_raw.strftime("%d/%m/%Y %H:%M")
        ticket.append(f"Apertura: {f_ap}")
    
    ticket.append(f"Cierre  : {fecha_cierre_actual}")
    ticket.append(f"Cajero  : {nombre_usuario}")
    ticket.append(linea_separadora())
    
    # 🔥 SECCIÓN 1: ARQUEO DE EFECTIVO
    ticket.append(centrar_texto("ARQUEO DE EFECTIVO"))
    ticket.append(linea_separadora('.'))
    
    monto_ini = datos_cierre.get('monto_inicial', 0)
    ingresos = datos_cierre.get('total_ingresos', 0)
    egresos = datos_cierre.get('total_egresos', 0)
    esperado = datos_cierre.get('efectivo_esperado', 0)
    contado = datos_cierre.get('efectivo_contado', 0)
    diferencia = datos_cierre.get('diferencia', 0)
    
    ticket.append(justificar_texto("Saldo Inicial:", formato_precio(monto_ini)))
    ticket.append(justificar_texto("(+) Ingresos:", formato_precio(ingresos)))
    ticket.append(justificar_texto("(-) Egresos:", formato_precio(egresos)))
    ticket.append(linea_separadora('-'))
    
    ticket.append(justificar_texto("Efectivo Esperado:", formato_precio(esperado)))
    ticket.append(justificar_texto("Efectivo Contado:", formato_precio(contado)))
    
    ticket.append(linea_separadora('='))
    texto_dif = "DIFERENCIA:"
    val_dif = formato_precio(diferencia)
    
    if diferencia != 0:
        val_dif += " (!)"
        
    ticket.append(justificar_texto(texto_dif, val_dif))
    ticket.append(linea_separadora('='))
    
    # 🔥 SECCIÓN 2: OTROS MEDIOS DE PAGO (Solo Registro)
    medios_pago = datos_cierre.get('medios_pago', {})
    
    if medios_pago and any(medios_pago.values()):
        ticket.append("\n")
        ticket.append(centrar_texto("OTROS MEDIOS DE PAGO"))
        ticket.append(centrar_texto("(Solo Registro)"))
        ticket.append(linea_separadora('.'))
        
        tarjetas = medios_pago.get('tarjetas', 0)
        transferencias = medios_pago.get('transferencias', 0)
        cuenta_corriente = medios_pago.get('cuenta_corriente', 0)
        
        ticket.append(">> INGRESOS:")
        ticket.append(justificar_texto("  Tarjetas:", formato_precio(tarjetas)))
        ticket.append(justificar_texto("  Transferencias:", formato_precio(transferencias)))
        ticket.append(justificar_texto("  Cuenta Corriente:", formato_precio(cuenta_corriente)))

        tra_egr = datos_cierre.get('total_egresos_transferencia', 0)
        tar_egr = datos_cierre.get('total_egresos_tarjeta', 0)
        if tra_egr > 0 or tar_egr > 0:
            ticket.append(linea_separadora('-'))
            ticket.append(">> EGRESOS:")
            if tar_egr > 0:
                ticket.append(justificar_texto("  Tarjetas (pagos):", formato_precio(tar_egr)))
            if tra_egr > 0:
                ticket.append(justificar_texto("  Transf. (pagos):", formato_precio(tra_egr)))

        ticket.append(linea_separadora('='))
    
    # SECCIÓN 3: TOTAL RECAUDADO
    # CORREGIDO: total = solo ingresos reales (efectivo vendido + otros medios)
    # El saldo inicial NO se suma porque es plata que ya estaba en caja, no dinero nuevo
    medios_pago = datos_cierre.get('medios_pago', {})
    ingresos_efectivo = datos_cierre.get('total_ingresos', 0)
    egresos = datos_cierre.get('total_egresos', 0)
    tarjetas_t = medios_pago.get('tarjetas', 0)
    transferencias_t = medios_pago.get('transferencias', 0)
    cuenta_corriente_t = medios_pago.get('cuenta_corriente', 0)

    # Total recaudado = lo que ENTRÓ en el turno (Liquidez Real)
    # 🔥 CORRECCIÓN: NO sumar Cuenta Corriente al Total Recaudado (es deuda, no dinero ingresado aún)
    total_general = ingresos_efectivo + tarjetas_t + transferencias_t

    if total_general > 0:
        ticket.append("\n")
        ticket.append(centrar_texto("TOTAL RECAUDADO"))
        ticket.append(centrar_texto(formato_precio(total_general)))
        ticket.append(centrar_texto("(Efectivo + Tarjetas + Transf.)"))
        ticket.append(linea_separadora('='))
    
    # Mostrar opcionalmente el total de crédito otorgado hoy
    if cuenta_corriente_t > 0:
        ticket.append(justificar_texto("Crédito a Cobrar (C.C.):", formato_precio(cuenta_corriente_t)))
        ticket.append(linea_separadora('.'))
    
    # Observaciones
    obs = datos_cierre.get('observaciones', '')
    if obs:
        ticket.append("\n")
        ticket.append("OBSERVACIONES:")
        ticket.append(linea_separadora('.'))
        # Dividir observaciones largas en líneas
        palabras = obs.split()
        linea_actual = ""
        for palabra in palabras:
            if len(linea_actual) + len(palabra) + 1 <= ANCHO_TICKET:
                linea_actual += palabra + " "
            else:
                ticket.append(linea_actual.strip())
                linea_actual = palabra + " "
        if linea_actual:
            ticket.append(linea_actual.strip())
    
    ticket.append("\n\n\n")
    enviar_a_impresora('\n'.join(ticket))