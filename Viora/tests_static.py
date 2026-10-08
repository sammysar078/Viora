import ast
from pathlib import Path
ROOT=Path(__file__).parent
for p in ROOT.rglob('*.py'):
    ast.parse(p.read_text())
print(f'Viora static AST check: PASS ({len(list(ROOT.rglob("*.py")))} Python files)')
