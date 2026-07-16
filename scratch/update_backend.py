import sys

path = r'c:\Users\Tomas\Documents\GitHub\SistemaDeCobro\SistemaDeCobro\app\database\backend_adapter.py'
with open(path, 'r', encoding='utf-8') as f:
    c = f.read()

target = '''    def obtener_vendedores(self) -> list[dict[str, Any]]:
        fn = getattr(DB, "obtener_vendedores", None)
        return list(fn() or []) if callable(fn) else []'''

repl = '''    def obtener_vendedores(self) -> list[dict[str, Any]]:
        fn = getattr(DB, "obtener_vendedores", None)
        return list(fn() or []) if callable(fn) else []

    def obtener_compradores(self) -> list[dict[str, Any]]:
        fn = getattr(DB, "obtener_compradores", None)
        return list(fn() or []) if callable(fn) else []

    def obtener_usuarios_operativos(self) -> list[dict[str, Any]]:
        fn = getattr(DB, "obtener_usuarios_operativos", None)
        return list(fn() or []) if callable(fn) else []'''

if target in c:
    with open(path, 'w', encoding='utf-8') as f:
        f.write(c.replace(target, repl))
    print('backend_adapter.py updated')
else:
    print('target not found in backend_adapter')
