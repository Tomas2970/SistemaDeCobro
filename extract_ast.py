import ast

def get_function_source(filename, func_names, outfile):
    with open(filename, 'r', encoding='utf-8') as f:
        source = f.read()
    
    tree = ast.parse(source)
    found = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name in func_names:
            found[node.name] = ast.get_source_segment(source, node)
    
    with open(outfile, 'w', encoding='utf-8') as out:
        for name in func_names:
            out.write(f"--- {name} in {filename} ---\n")
            if name in found:
                out.write(found[name])
            else:
                out.write("NOT FOUND")
            out.write("\n\n")

if __name__ == '__main__':
    db = 'app/database/DB.py'
    outfile = 'extract_ast_output5.txt'
    
    funcs = [
        'buscar_producto_por_nombre'
    ]
    
    get_function_source(db, funcs, outfile)
