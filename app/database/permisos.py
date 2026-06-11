# app/database/permisos.py

# =====================================
# DEFINICIÓN DE PERMISOS POR ROL
# OPCIÓN A: SEGURIDAD MÁXIMA
# =====================================

PERMISOS = {
    # ADMINISTRADOR: Puede hacer TODO
    'admin': [
        # Usuarios
        'ver_usuarios',
        'crear_usuarios',
        'editar_usuarios',
        'eliminar_usuarios',
        
        # Productos
        'ver_productos',
        'crear_productos',
        'editar_productos',
        'eliminar_productos',
        'modificar_precios',  # ← EXCLUSIVO Admin/Supervisor
        'gestionar_categorias',
        
        # Inventario
        'ver_inventario',
        'ajustar_inventario_manual',  # ← Solo Admin/Supervisor (desde ABM)
        'ver_stock_bajo',
        
        # Ventas
        # NO realiza ventas operativas
        'ver_ventas',
        'cancelar_ventas',
        'procesar_devoluciones',
        
        # Clientes (OPCIÓN A)
        'ver_clientes',
        'crear_clientes',        # ← Admin puede crear
        'editar_clientes',       # ← Admin puede editar todo
        'eliminar_clientes',     # ← Solo Admin
        'gestionar_cuenta_corriente',  # Cobrar pagos
        
        # Proveedores y Compras
        'ver_proveedores',
        'crear_proveedores',
        'registrar_compras',
        
        # Reportes
        'ver_reportes',
        'ver_estadisticas',
        'ver_auditoria',
        
        # CAJA Y SUPERVISIÓN GLOBAL
        'ver_todas_las_cajas',
        'cerrar_caja_ajena',
        'broadcast_mensaje',
        'bloqueo_emergencia',
        'cerrar_caja',
        'movimientos_caja_manuales',
        'ver_caja_todos',
        'ver_historial_movimientos',
        
        # Configuración
        'configurar_sistema',
        'ver_logs',
        
        # TESORERÍA
        'abrir_tesoreria',
        'cerrar_tesoreria',
        'ingreso_extraordinario',
        'transferencia_tesoreria',
    ],
    
    # SUPERVISOR: Encargado de Turno
    'supervisor': [
        # Productos
        'ver_productos',
        'crear_productos',
        'editar_productos',
        'modificar_precios',  # ← Solo Admin/Supervisor
        
        # Inventario
        'ver_inventario',
        'ajustar_inventario_manual',
        'ver_stock_bajo',
        
        # Ventas
        # NO realiza ventas directamente
        'ver_ventas',
        'procesar_devoluciones',
        
        # Clientes (OPCIÓN A)
        'ver_clientes',
        'crear_clientes',        # ← Supervisor puede crear
        'editar_clientes',       # ← Supervisor puede editar
        'gestionar_cuenta_corriente',  # Puede cobrar
        # NO tiene 'eliminar_clientes'
        
        # Proveedores
        'ver_proveedores',
        'crear_proveedores',
        'registrar_compras',
        
        # Reportes
        'ver_reportes',
        'ver_estadisticas',
        
        # CAJA Y AUTORIZACIÓN (Encargado de Turno)
        'ver_cajas_activas_turno',
        'cerrar_caja_ajena',
        'autorizar_operaciones',
        'movimientos_caja_manuales',
        'ver_caja_todos',
        'ver_historial_movimientos',
        
        # TESORERÍA
        'transferencia_tesoreria',
    ],
    
    # VENDEDOR: Solo Ventas y Consultas (MUY RESTRINGIDO)
    'vendedor': [
        # Productos (Solo lectura)
        'ver_productos',
        # NO: crear_productos, editar_productos, modificar_precios
        
        # Inventario (Solo lectura)
        'ver_inventario',
        'ver_stock_bajo',
        # NO: ajustar_inventario_manual
        
        # Ventas
        'realizar_ventas',
        'ver_ventas',  # Solo sus propias ventas
        # NO: procesar_devoluciones, cancelar_ventas
        
        # Clientes (OPCIÓN A - SOLO CONSULTA)
        'ver_clientes',  # ← Solo puede VER/BUSCAR clientes
        # NO: crear_clientes, editar_clientes, eliminar_clientes
        # NO: gestionar_cuenta_corriente (no puede cobrar)
        
        # Caja (Individual, sin movimientos manuales)
        'abrir_caja',
        'cerrar_caja',
        # NO: movimientos_caja_manuales, ver_caja_todos, ver_historial_movimientos
    ]
}

# =====================================
# FUNCIONES DE VALIDACIÓN
# =====================================

def obtener_rol_nombre(id_rol):
    """Convierte ID de rol a nombre"""
    roles = {
        1: 'admin',
        2: 'vendedor',
        3: 'supervisor'
    }
    return roles.get(id_rol, 'vendedor')

def tiene_permiso(usuario, accion):
    """Verifica si un usuario tiene permiso para realizar una acción"""
    if not usuario:
        return False
    
    id_rol = usuario.get('id_rol')
    nombre_rol = obtener_rol_nombre(id_rol)
    permisos_rol = PERMISOS.get(nombre_rol, [])
    
    return accion in permisos_rol

def requiere_permiso(accion):
    """Decorador para funciones que requieren un permiso específico"""
    def decorador(func):
        def wrapper(usuario, *args, **kwargs):
            if not tiene_permiso(usuario, accion):
                raise PermissionError(f"No tienes permiso para: {accion}")
            return func(usuario, *args, **kwargs)
        return wrapper
    return decorador

def obtener_permisos_usuario(usuario):
    """Obtiene lista completa de permisos de un usuario"""
    if not usuario:
        return []
    
    id_rol = usuario.get('id_rol')
    nombre_rol = obtener_rol_nombre(id_rol)
    
    return PERMISOS.get(nombre_rol, [])

def puede_modificar_precios(usuario):
    """Verifica si puede modificar precios (Solo Admin/Supervisor)"""
    return tiene_permiso(usuario, 'modificar_precios')

def puede_ajustar_inventario_manual(usuario):
    """Verifica si puede ajustar stock manualmente desde ABM"""
    return tiene_permiso(usuario, 'ajustar_inventario_manual')

def puede_movimientos_caja_manuales(usuario):
    """Verifica si puede hacer retiros/ingresos manuales en caja"""
    return tiene_permiso(usuario, 'movimientos_caja_manuales')

def puede_procesar_devoluciones(usuario):
    """Verifica si puede procesar devoluciones"""
    return tiene_permiso(usuario, 'procesar_devoluciones')

# =====================================
# FUNCIONES DE AYUDA PARA FRONTEND
# =====================================

def obtener_menu_items(usuario):
    """Genera items de menú según permisos del usuario"""
    return {
        'dashboard': True,
        'panel_control': tiene_permiso(usuario, 'ver_todas_las_cajas'),
        
        'ventas': {
            'habilitado': True,
            'nueva_venta': tiene_permiso(usuario, 'realizar_ventas'),
            'ver_ventas': tiene_permiso(usuario, 'ver_ventas'),
            'cancelar_venta': tiene_permiso(usuario, 'cancelar_ventas'),
            'devoluciones': tiene_permiso(usuario, 'procesar_devoluciones'),
        },
        
        'productos': {
            'habilitado': tiene_permiso(usuario, 'ver_productos'),
            'agregar': tiene_permiso(usuario, 'crear_productos'),
            'editar': tiene_permiso(usuario, 'editar_productos'),
            'eliminar': tiene_permiso(usuario, 'eliminar_productos'),
            'modificar_precios': tiene_permiso(usuario, 'modificar_precios'),
        },
        
        'inventario': {
            'habilitado': tiene_permiso(usuario, 'ver_inventario'),
            'ajustar_manual': tiene_permiso(usuario, 'ajustar_inventario_manual'),
            'alertas': tiene_permiso(usuario, 'ver_stock_bajo'),
        },
        
        'clientes': {
            'habilitado': tiene_permiso(usuario, 'ver_clientes'),
            'agregar': tiene_permiso(usuario, 'crear_clientes'),
            'editar': tiene_permiso(usuario, 'editar_clientes'),
            'eliminar': tiene_permiso(usuario, 'eliminar_clientes'),
            'cuenta_corriente': tiene_permiso(usuario, 'gestionar_cuenta_corriente'),
        },
        
        'proveedores': {
            'habilitado': tiene_permiso(usuario, 'ver_proveedores'),
            'agregar': tiene_permiso(usuario, 'crear_proveedores'),
        },
        
        'reportes': {
            'habilitado': tiene_permiso(usuario, 'ver_reportes'),
            'estadisticas': tiene_permiso(usuario, 'ver_estadisticas'),
            'auditoria': tiene_permiso(usuario, 'ver_auditoria'),
        },
        
        'caja': {
            'habilitado': True,
            'abrir': tiene_permiso(usuario, 'abrir_caja'),
            'cerrar': tiene_permiso(usuario, 'cerrar_caja'),
            'movimientos_manuales': tiene_permiso(usuario, 'movimientos_caja_manuales'),
            'ver_historial': tiene_permiso(usuario, 'ver_caja_todos'),
            'ver_movimientos': tiene_permiso(usuario, 'ver_historial_movimientos'),
        },
        
        'usuarios': {
            'habilitado': tiene_permiso(usuario, 'ver_usuarios'),
            'agregar': tiene_permiso(usuario, 'crear_usuarios'),
            'editar': tiene_permiso(usuario, 'editar_usuarios'),
            'eliminar': tiene_permiso(usuario, 'eliminar_usuarios'),
        },
        
        'configuracion': {
            'habilitado': tiene_permiso(usuario, 'configurar_sistema'),
        },
        
        'tesoreria': {
            'habilitado': tiene_permiso(usuario, 'transferencia_tesoreria'),
            'abrir': tiene_permiso(usuario, 'abrir_tesoreria'),
            'cerrar': tiene_permiso(usuario, 'cerrar_tesoreria'),
            'ingreso_extraordinario': tiene_permiso(usuario, 'ingreso_extraordinario'),
        }
    }

def describir_rol(nombre_rol):
    """Devuelve una descripción de lo que puede hacer cada rol"""
    descripciones = {
        'admin': """
ADMINISTRADOR - Control y supervisión global del sistema
• Observador con poder de intervención en tiempo real
• Monitorear estado de todas las cajas simultáneamente
• Enviar mensajes a vendedores y bloqueo de emergencia
• Gestionar usuarios, productos y configuración
• Modificar precios y ajustar stock manualmente
• Crear, editar y eliminar clientes
• Forzar cierre de cajas ajenas (no opera caja propia)
• Procesar devoluciones y cancelar ventas
• Ver todos los reportes y auditoría
• Control total sobre la Tesorería (Apertura, Cierre, Aportes)
        """,
        
        'supervisor': """
ENCARGADO DE TURNO - Supervisión Operativa
• NO realiza ventas ni opera como cajero
• Autoriza operaciones restringidas (retiros, devoluciones)
• Monitorea todas las cajas activas del turno
• Puede forzar el cierre de cajas de otros usuarios
• Administrar inventario y productos (con precios)
• Gestionar clientes y proveedores
• Procesar devoluciones
• Ver reportes y estadísticas del turno
• NO puede eliminar clientes ni gestionar usuarios
• Operar Tesorería (Transferencias y cobros), pero NO abrir/cerrar.
        """,
        
        'vendedor': """
VENDEDOR - Solo Ventas y Consultas
• Realizar ventas a clientes existentes
• Consultar productos, inventario y precios
• Consultar lista de clientes (solo búsqueda)
• Abrir y cerrar su propia caja (sin movimientos manuales)
• ❌ NO puede crear/editar/eliminar clientes
• ❌ NO puede modificar precios ni productos
• ❌ NO puede ajustar stock manualmente
• ❌ NO puede cobrar cuenta corriente
• ❌ NO puede procesar devoluciones
• ❌ NO puede hacer retiros/ingresos de caja
        """
    }
    
    return descripciones.get(nombre_rol, "Rol desconocido")