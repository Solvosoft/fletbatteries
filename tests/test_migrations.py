"""Las migraciones de la demo (demo/migrations) crean el mismo esquema que los modelos."""

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def run_cli(*args, db_url: str):
    env = {**os.environ, "FLETBATTERIES_DB_URL": db_url}
    return subprocess.run([sys.executable, "-m", "fletbatteries", *args], cwd=ROOT, env=env, capture_output=True,
                          text=True)


def test_demo_migrations_match_models(tmp_path):
    url = f"sqlite:///{tmp_path / 'mig.db'}"
    result = run_cli("migrate", db_url=url)
    assert result.returncode == 0, result.stderr
    result = run_cli("check", db_url=url)
    assert result.returncode == 0, result.stdout + result.stderr


def test_createdb_stamps_head(tmp_path):
    url = f"sqlite:///{tmp_path / 'new.db'}"
    assert run_cli("createdb", db_url=url).returncode == 0
    current = run_cli("current", db_url=url)
    assert current.returncode == 0 and "sin migraciones" not in current.stdout
    assert run_cli("check", db_url=url).returncode == 0


def test_template_db_is_up_to_date():
    """template.db (la usan las capturas y la app compilada) debe estar migrada."""
    url = f"sqlite:///{ROOT / 'template.db'}"
    result = run_cli("check", db_url=url)
    assert result.returncode == 0, result.stdout + result.stderr
