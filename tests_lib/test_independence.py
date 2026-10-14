"""La librería no depende de la demo."""

import ast
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src" / "fletbatteries"
DEMO_MODULES = {"settings", "views", "data", "controls", "scripts", "main", "app_forms", "components"}


def test_src_does_not_import_demo_modules():
    offenders = []
    for path in SRC.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            names = []
            if isinstance(node, ast.Import):
                names = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                names = [node.module]
            for name in names:
                if name.split(".")[0] in DEMO_MODULES:
                    offenders.append(f"{path.relative_to(ROOT)}: import {name}")
    assert not offenders, "\n".join(offenders)


def test_library_works_without_demo_on_path(tmp_path):
    """Importa todos los módulos y hace un CRUD + exportación con solo `src` en el PYTHONPATH."""
    code = f"""
import importlib, pkgutil, sys
import fletbatteries
assert not any(p.endswith('demo') for p in sys.path), sys.path
for mod in pkgutil.walk_packages(fletbatteries.__path__, 'fletbatteries.'):
    if mod.name.startswith('fletbatteries.migrations.env') or mod.name == 'fletbatteries.__main__':
        continue
    importlib.import_module(mod.name)
from fletbatteries.data import Database, set_default_database, import_models, ListSource, Query
from fletbatteries.data.export import export_csv
from fletbatteries.auth.backend import UserManager, DatabaseAuthBackend
db = set_default_database(Database('sqlite:///{tmp_path / "solo.db"}'))
import_models(); db.create_all()
UserManager().create_superuser('ana', 'Clave-segura-1')
assert DatabaseAuthBackend().authenticate('ana', 'Clave-segura-1').is_superuser
data = export_csv(ListSource([{{'id': 1, 'name': 'x'}}]), Query(), ['name'])
assert data.decode('utf-8-sig').splitlines() == ['Name', 'x']
print('ok')
"""
    env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
    env["PYTHONPATH"] = str(ROOT / "src")
    result = subprocess.run([sys.executable, "-c", code], env=env, capture_output=True, text=True, cwd=tmp_path)
    assert result.returncode == 0, result.stderr
    assert "ok" in result.stdout
