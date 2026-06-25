import ast
from collections import defaultdict
import re

def extract_tables(query):
    # Very naive table extractor
    matches = re.findall(r'(?i)(?:FROM|JOIN|INTO|UPDATE)\s+([a-zA-Z0-9_]+)', query)
    return set([m.lower() for m in matches])

def analyze_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        source = f.read()
    tree = ast.parse(source)
    
    queries = []
    class SQLVisitor(ast.NodeVisitor):
        def __init__(self):
            self.current_func = None
        def visit_FunctionDef(self, node):
            old = self.current_func
            self.current_func = node.name
            self.generic_visit(node)
            self.current_func = old
        def visit_Call(self, node):
            if isinstance(node.func, ast.Attribute) and node.func.attr == 'execute':
                if node.args:
                    arg = node.args[0]
                    if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                        q = arg.value.strip()
                        queries.append((self.current_func, q))
            self.generic_visit(node)
            
    v = SQLVisitor()
    v.visit(tree)
    return queries

db_queries = analyze_file(r'd:\Windows\Documentos\GitHub\SistemaDeCobro\SistemaDeCobro\app\database\DB.py')

table_to_queries = defaultdict(list)
for func, q in db_queries:
    tables = extract_tables(q)
    for t in tables:
        table_to_queries[t].append((func, q))

target_tables = ['usuario', 'caja_session', 'caja_movimiento', 'cliente', 'proveedor']

for t in target_tables:
    print(f"\n=== Table: {t.upper()} ===")
    for func, q in table_to_queries[t]:
        # print first 60 chars of query
        short_q = " ".join(q.split())
        print(f"[{func}] {short_q}")
