try:
    from app.database.permisos import tiene_permiso as _tiene_permiso
except Exception:
    def _tiene_permiso(usuario: dict, permiso: str) -> bool:
        rol = str(usuario.get("id_rol", "")).lower()
        mapa = {
            "admin": {"realizar_ventas","ver_inventario","registrar_compras","crear_clientes","ver_usuarios","ver_reportes"},
            "vendedor": {"realizar_ventas","ver_inventario","crear_clientes"},
        }
        return permiso in mapa.get(rol, set())

tiene_permiso = _tiene_permiso
