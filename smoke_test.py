from pathlib import Path
import ast, zipfile
root=Path('Viora')
files=list(root.rglob('*.py'))
for p in files:
    ast.parse(p.read_text(encoding='utf-8'), filename=str(p))
required=['app.py','config.py','requirements.txt','core/db.py','core/game_manager.py','games/engine.py']
missing=[x for x in required if not (root/x).exists()]
assert not missing, missing
print(f'AST PASS: {len(files)} Python files')
print('Required files PASS')
