"""
Sistema de Permisos por Rol
Sistema de Cobro - Supermercado Don Atilio

Define qué puede hacer cada rol en el sistema
"""

# =====================================
# DEFINICIÓN DE PERMISOS POR ROL
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
        'modificar_precios',
        
        # Inventario
        'ver_inventario',
        'ajustar_inventario',
        'ver_stock_bajo',
        
        # Ventas
        'realizar_ventas',
        'ver_ventas',
        'cancelar_ventas',
        
        # Clientes
        'ver_clientes',
        'crear_clientes',
        'editar_clientes',
        'eliminar_clientes',
        'gestionar_cuenta_corriente',
        
        # Proveedores y Compras
        'ver_proveedores',
        'crear_proveedores',
        'registrar_compras',
        
        # Reportes
        'ver_reportes',
        'cierre_caja',
        'ver_estadisticas',
        'ver_auditoria',
        
        # Configuración
        'configurar_sistema',
        'ver_logs',
    ],
    
    # SUPERVISOR: Puede gestionar inventario y ver reportes
    'supervisor': [
        # Productos (solo ver y editar, no eliminar)
        'ver_productos',
        'editar_productos',
        
        # Inventario
        'ver_inventario',
        'ajustar_inventario',
        'ver_stock_bajo',
        
        # Ventas
        'realizar_ventas',
        'ver_ventas',
        
        # Clientes
        'ver_clientes',
        'crear_clientes',
        'editar_clientes',
        'ver_cuenta_corriente',  # ← NUEVO: Puede ver cuánto deben
        
        # Proveedores
        'ver_proveedores',
        'registrar_compras',
        
        # Reportes (puede ver pero no cierre de caja total)
        'ver_reportes',
        'ver_estadisticas',
    ],
    
    # VENDEDOR: Solo puede vender y gestionar clientes
    'vendedor': [
        # Productos (solo ver)
        'ver_productos',
        
        # Inventario (solo consultar)
        'ver_inventario',
        'ver_stock_bajo',
        
        # Ventas
        'realizar_ventas',
        'ver_ventas',  # Solo sus propias ventas
        
        # Clientes
        'ver_clientes',
        'crear_clientes',
        'ver_cuenta_corriente',  # ← NUEVO: Puede ver cuánto deben
        
        # Reportes (solo su propio cierre)
        'cierre_caja',  # Solo su propia caja
    ]
}

# =====================================
# FUNCIONES DE VALIDACIÓN
# =====================================

def obtener_rol_nombre(id_rol):
    """
    Convierte ID de rol a nombre
    
    Args:
        id_rol: 1=admin, 2=vendedor, 3=supervisor
    
    Returns:
        Nombre del rol como string
    """
    roles = {
        1: 'admin',
        2: 'vendedor',
        3: 'supervisor'
    }
    return roles.get(id_rol, 'vendedor')

def tiene_permiso(usuario, accion):
    """
    Verifica si un usuario tiene permiso para realizar una acción
    
    Args:
        usuario: Dict con datos del usuario (debe tener 'id_rol')
        accion: String con el nombre del permiso a verificar
    
    Returns:
        True si tiene permiso, False si no
    
    Ejemplo:
        if tiene_permiso(usuario_actual, 'crear_productos'):
            # Mostrar botón de agregar producto
    """
    if not usuario:
        return False
    
    # Obtener rol del usuario
    id_rol = usuario.get('id_rol')
    nombre_rol = obtener_rol_nombre(id_rol)
    
    # Obtener permisos del rol
    permisos_rol = PERMISOS.get(nombre_rol, [])
    
    # Verificar si tiene el permiso
    return accion in permisos_rol

def requiere_permiso(accion):
    """
    Decorador para funciones que requieren un permiso específico
    
    Uso:
        @requiere_permiso('crear_productos')
        def agregar_producto():
            # código...
    """
    def decorador(func):
        def wrapper(usuario, *args, **kwargs):
            if not tiene_permiso(usuario, accion):
                raise PermissionError(f"No tienes permiso para: {accion}")
            return func(usuario, *args, **kwargs)
        return wrapper
    return decorador

def obtener_permisos_usuario(usuario):
    """
    Obtiene lista completa de permisos de un usuario
    
    Args:
        usuario: Dict con datos del usuario
    
    Returns:
        Lista de strings con todos los permisos
    """
    if not usuario:
        return []
    
    id_rol = usuario.get('id_rol')
    nombre_rol = obtener_rol_nombre(id_rol)
    
    return PERMISOS.get(nombre_rol, [])

def puede_ver_usuario(usuario_actual, usuario_objetivo):
    """
    Verifica si un usuario puede ver/editar a otro usuario
    
    Args:
        usuario_actual: Usuario que intenta ver
        usuario_objetivo: Usuario que se quiere ver
    
    Returns:
        True si puede ver/editar, False si no
    
    Regla: Solo admin puede gestionar usuarios
           Un usuario puede ver su propio perfil
    """
    # Admin puede ver todos
    if tiene_permiso(usuario_actual, 'ver_usuarios'):
        return True
    
    # Un usuario puede verse a sí mismo
    if usuario_actual.get('id_usuario') == usuario_objetivo.get('id_usuario'):
        return True
    
    return False

def puede_ver_venta(usuario_actual, venta):
    """
    Verifica si un usuario puede ver una venta específica
    
    Args:
        usuario_actual: Usuario que intenta ver la venta
        venta: Dict con datos de la venta (debe tener 'id_usuario')
    
    Returns:
        True si puede ver, False si no
    
    Regla: Admin y Supervisor pueden ver todas
           Vendedor solo puede ver sus propias ventas
    """
    id_rol = usuario_actual.get('id_rol')
    
    # Admin y Supervisor pueden ver todas
    if id_rol in [1, 3]:
        return True
    
    # Vendedor solo puede ver sus propias ventas
    if id_rol == 2:
        return usuario_actual.get('id_usuario') == venta.get('id_usuario')
    
    return False

def puede_ver_cierre_completo(usuario):
    """
    Verifica si puede ver cierre de caja de todos los vendedores
    
    Returns:
        True si puede ver cierre completo, False si solo el suyo
    """
    # Solo Admin puede ver cierre completo
    return tiene_permiso(usuario, 'ver_reportes')

# =====================================
# FUNCIONES DE AYUDA PARA FRONTEND
# =====================================

def obtener_menu_items(usuario):
    """
    Genera items de menú según permisos del usuario
    
    Returns:
        Dict con secciones del menú y si están habilitadas
    """
    return {
        'dashboard': True,  # Todos pueden ver dashboard básico
        
        'ventas': {
            'habilitado': True,  # Todos pueden acceder a ventas
            'nueva_venta': tiene_permiso(usuario, 'realizar_ventas'),
            'ver_ventas': tiene_permiso(usuario, 'ver_ventas'),
            'cancelar_venta': tiene_permiso(usuario, 'cancelar_ventas'),
        },
        
        'productos': {
            'habilitado': tiene_permiso(usuario, 'ver_productos'),
            'agregar': tiene_permiso(usuario, 'crear_productos'),
            'editar': tiene_permiso(usuario, 'editar_productos'),
            'eliminar': tiene_permiso(usuario, 'eliminar_productos'),
        },
        
        'inventario': {
            'habilitado': tiene_permiso(usuario, 'ver_inventario'),
            'ajustar': tiene_permiso(usuario, 'ajustar_inventario'),
            'alertas': tiene_permiso(usuario, 'ver_stock_bajo'),
        },
        
        'clientes': {
            'habilitado': tiene_permiso(usuario, 'ver_clientes'),
            'agregar': tiene_permiso(usuario, 'crear_clientes'),
            'editar': tiene_permiso(usuario, 'editar_clientes'),
            'cuenta_corriente': tiene_permiso(usuario, 'gestionar_cuenta_corriente'),
        },
        
        'proveedores': {
            'habilitado': tiene_permiso(usuario, 'ver_proveedores'),
            'agregar': tiene_permiso(usuario, 'crear_proveedores'),
        },
        
        'reportes': {
            'habilitado': tiene_permiso(usuario, 'ver_reportes') or tiene_permiso(usuario, 'cierre_caja'),
            'cierre_caja': tiene_permiso(usuario, 'cierre_caja'),
            'estadisticas': tiene_permiso(usuario, 'ver_estadisticas'),
            'auditoria': tiene_permiso(usuario, 'ver_auditoria'),
        },
        
        'usuarios': {
            'habilitado': tiene_permiso(usuario, 'ver_usuarios'),
            'agregar': tiene_permiso(usuario, 'crear_usuarios'),
            'editar': tiene_permiso(usuario, 'editar_usuarios'),
            'eliminar': tiene_permiso(usuario, 'eliminar_usuarios'),
        },
        
        'configuracion': {
            'habilitado': tiene_permiso(usuario, 'configurar_sistema'),
        }
    }

def describir_rol(nombre_rol):
    """
    Devuelve una descripción de lo que puede hacer cada rol
    
    Returns:
        String con descripción
    """
    descripciones = {
        'admin': """
ADMINISTRADOR - Acceso Total
• Gestionar usuarios, productos y configuración
• Ver todos los reportes y estadísticas
• Acceso completo al sistema
• Modificar precios y realizar ajustes
        """,
        
        'supervisor': """
SUPERVISOR - Gestión Operativa
• Realizar ventas y gestionar clientes
• Administrar inventario y productos
• Ver reportes y estadísticas
• Registrar compras a proveedores
• NO puede gestionar usuarios ni configuración
        """,
        
        'vendedor': """
VENDEDOR - Operaciones de Venta
• Realizar ventas
• Gestionar clientes
• Consultar productos e inventario
• Ver su propio cierre de caja
• NO puede modificar productos ni ver reportes generales
        """
    }
    
    return descripciones.get(nombre_rol, "Rol desconocido")

