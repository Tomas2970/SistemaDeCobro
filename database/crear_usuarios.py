"""
Script para crear usuarios iniciales
Sistema de Cobro - Supermercado Don Atilio

Ejecutar DESPUÉS de ejecutar schema.sql
Ejecutar: python crear_usuarios.py
"""

from database.DB import insertar_usuario, obtener_roles, obtener_usuarios

def crear_usuarios_iniciales():
    """Crea los usuarios iniciales del sistema"""
    
    print("="*60)
    print("CREACIÓN DE USUARIOS INICIALES".center(60))
    print("="*60)
    print()
    
    # Verificar que existan roles
    roles = obtener_roles()
    if not roles:
        print("❌ Error: No se encontraron roles en la base de datos")
        print("   Asegúrate de haber ejecutado schema.sql primero")
        return False
    
    print(f"✅ Se encontraron {len(roles)} roles:")
    for rol in roles:
        print(f"   • {rol['nombre']}: {rol['descripcion']}")
    print()
    
    # Verificar si ya existen usuarios
    usuarios_existentes = obtener_usuarios()
    if usuarios_existentes:
        print(f"⚠️  Ya existen {len(usuarios_existentes)} usuarios en el sistema:")
        for usuario in usuarios_existentes:
            print(f"   • {usuario['nombre']} ({usuario['rol']})")
        print()
        respuesta = input("¿Desea crear más usuarios de todos modos? (s/n): ")
        if respuesta.lower() != 's':
            print("\n❌ Operación cancelada")
            return False
        print()
    
    # Usuarios a crear
    usuarios = [
        {
            'nombre': 'admin',
            'contraseña': 'admin123',
            'rol': 'admin',
            'descripcion': 'Administrador del sistema'
        },
        {
            'nombre': 'vendedor1',
            'contraseña': 'vend123',
            'rol': 'vendedor',
            'descripcion': 'Vendedor de turno mañana'
        },
        {
            'nombre': 'vendedor2',
            'contraseña': 'vend123',
            'rol': 'vendedor',
            'descripcion': 'Vendedor de turno tarde'
        },
        {
            'nombre': 'supervisor',
            'contraseña': 'super123',
            'rol': 'supervisor',
            'descripcion': 'Supervisor de tienda'
        }
    ]
    
    print("Se crearán los siguientes usuarios:")
    print()
    for i, usuario in enumerate(usuarios, 1):
        print(f"{i}. Usuario: {usuario['nombre']}")
        print(f"   Contraseña: {usuario['contraseña']}")
        print(f"   Rol: {usuario['rol']}")
        print(f"   Descripción: {usuario['descripcion']}")
        print()
    
    respuesta = input("¿Confirmar creación? (s/n): ")
    if respuesta.lower() != 's':
        print("\n❌ Operación cancelada")
        return False
    
    print("\n" + "="*60)
    print("Creando usuarios...")
    print("="*60)
    print()
    
    # Mapear nombres de roles a IDs
    roles_map = {rol['nombre']: rol['id_rol'] for rol in roles}
    
    creados = 0
    errores = 0
    
    for usuario in usuarios:
        nombre = usuario['nombre']
        contraseña = usuario['contraseña']
        id_rol = roles_map.get(usuario['rol'])
        
        if not id_rol:
            print(f"❌ {nombre}: Rol '{usuario['rol']}' no encontrado")
            errores += 1
            continue
        
        id_usuario = insertar_usuario(nombre, contraseña, id_rol)
        
        if id_usuario:
            print(f"✅ {nombre}: Creado con ID {id_usuario}")
            creados += 1
        else:
            print(f"❌ {nombre}: Error al crear (posiblemente ya existe)")
            errores += 1
    
    print()
    print("="*60)
    print(f"Resumen: {creados} creados, {errores} errores")
    print("="*60)
    print()
    
    if creados > 0:
        print("⚠️  IMPORTANTE: Cambia estas contraseñas en producción!")
        print()
        print("Usuarios creados:")
        usuarios_finales = obtener_usuarios()
        for usuario in usuarios_finales:
            print(f"   • {usuario['nombre']} ({usuario['rol']})")
        print()
    
    return creados > 0

def main():
    """Función principal"""
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║                                                          ║
    ║          👥 CREACIÓN DE USUARIOS INICIALES 👥           ║
    ║                                                          ║
    ║     Sistema de Cobro - Supermercado Don Atilio          ║
    ║                                                          ║
    ╚══════════════════════════════════════════════════════════╝
    """)
    
    try:
        exito = crear_usuarios_iniciales()
        
        if exito:
            print("✅ ¡Usuarios creados exitosamente!")
            print("\nPuedes hacer login con:")
            print("   Usuario: admin")
            print("   Contraseña: admin123")
            print()
            return 0
        else:
            print("⚠️  No se crearon usuarios")
            return 1
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Operación cancelada por el usuario\n")
        return 2
    except Exception as e:
        print(f"\n\n❌ Error fatal: {e}\n")
        return 3

if __name__ == "__main__":
    import sys
    sys.exit(main())