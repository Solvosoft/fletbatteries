"""
Migraciones del esquema con Alembic (requiere el extra `fletbatteries[migrations]`).

No hace falta `alembic.ini` ni copiar un `env.py`: el `env.py` viene en el
paquete (`fletbatteries/migrations/`) y las revisiones se guardan en la
carpeta del proyecto. La configuración se toma (en este orden) de los
argumentos, de las variables de entorno o de `[tool.fletbatteries]` en el
`pyproject.toml` del proyecto:

    [tool.fletbatteries]
    models = ["myapp.models"]          # módulos con los modelos (los del framework se agregan solos)
    setup = ["myapp.settings"]         # módulos que se importan antes (p. ej. set_default_database)
    migrations_dir = "migrations"      # carpeta de las revisiones
    pythonpath = ["src"]               # rutas extra para importar los módulos
    db_url = "sqlite:///app.db"        # opcional; si no, la base por defecto que configure `setup`

    FLETBATTERIES_DB_URL, FLETBATTERIES_MODELS (separados por coma), FLETBATTERIES_SETUP,
    FLETBATTERIES_MIGRATIONS_DIR

Uso desde Python:

    from fletbatteries.data import migrations
    migrations.makemigrations("agregar clientes")
    migrations.migrate()                       # upgrade head
    migrations.stamp()                         # marcar una BD creada con create_all
    migrations.check()                         # [] si el esquema coincide con los modelos

o con el CLI: `fletbatteries makemigrations -m "..."`, `fletbatteries migrate`, etc.
"""

import dataclasses
import importlib
import logging
import os
import sys
from pathlib import Path
from typing import Optional, Sequence

log = logging.getLogger(__name__)

ENV_DIR = Path(__file__).resolve().parent.parent / "migrations"


@dataclasses.dataclass
class MigrationConfig:
    db_url: Optional[str] = None
    models: list[str] = dataclasses.field(default_factory=list)
    setup: list[str] = dataclasses.field(default_factory=list)
    migrations_dir: str = "migrations"
    pythonpath: list[str] = dataclasses.field(default_factory=list)
    root: Path = dataclasses.field(default_factory=Path.cwd)

    @property
    def versions_path(self) -> Path:
        path = Path(self.migrations_dir)
        return path if path.is_absolute() else self.root / path


def _split(value) -> list[str]:
    if not value:
        return []
    if isinstance(value, str):
        return [v.strip() for v in value.split(",") if v.strip()]
    return [str(v) for v in value]


def find_pyproject(start: Optional[Path] = None) -> Optional[Path]:
    current = (start or Path.cwd()).resolve()
    for folder in (current, *current.parents):
        candidate = folder / "pyproject.toml"
        if candidate.exists():
            return candidate
    return None


def _read_pyproject(path: Optional[Path]) -> dict:
    if path is None:
        return {}
    try:
        import tomllib
    except ImportError:  # Python < 3.11
        try:
            import tomli as tomllib  # type: ignore[no-redef]
        except ImportError:
            return {}
    with open(path, "rb") as fh:
        return tomllib.load(fh).get("tool", {}).get("fletbatteries", {})


def load_config(db_url: Optional[str] = None, models: Optional[Sequence[str]] = None,
                setup: Optional[Sequence[str]] = None, migrations_dir: Optional[str] = None,
                pythonpath: Optional[Sequence[str]] = None, root: Optional[Path] = None) -> MigrationConfig:
    """Configuración combinando argumentos, entorno y `[tool.fletbatteries]`."""
    pyproject = find_pyproject(root)
    tool = _read_pyproject(pyproject)
    base = Path(root) if root else (pyproject.parent if pyproject else Path.cwd())
    return MigrationConfig(
        db_url=db_url or os.environ.get("FLETBATTERIES_DB_URL") or tool.get("db_url"),
        models=list(models) if models is not None else _split(os.environ.get("FLETBATTERIES_MODELS"))
        or _split(tool.get("models")),
        setup=list(setup) if setup is not None else _split(os.environ.get("FLETBATTERIES_SETUP"))
        or _split(tool.get("setup")),
        migrations_dir=migrations_dir or os.environ.get("FLETBATTERIES_MIGRATIONS_DIR")
        or tool.get("migrations_dir") or "migrations",
        pythonpath=list(pythonpath) if pythonpath is not None else _split(tool.get("pythonpath")),
        root=base,
    )


def prepare(config: MigrationConfig) -> str:
    """Agrega el `pythonpath`, importa `setup` y los modelos; devuelve la URL de la base de datos."""
    from fletbatteries.data.db import get_default_database, import_models

    for path in reversed(config.pythonpath):
        full = str((config.root / path).resolve())
        if full not in sys.path:
            sys.path.insert(0, full)
    for module in config.setup:
        importlib.import_module(module)
    import_models(config.models)
    if config.db_url:
        return config.db_url
    try:
        return get_default_database().url
    except RuntimeError:
        raise RuntimeError("No hay URL de base de datos: use --db-url, FLETBATTERIES_DB_URL, `db_url` en "
                           "[tool.fletbatteries] o un módulo `setup` que llame a set_default_database()")


def alembic_config(config: Optional[MigrationConfig] = None):
    """`alembic.config.Config` en memoria (sin `alembic.ini`)."""
    from alembic.config import Config

    config = config or load_config()
    url = prepare(config)
    cfg = Config()
    cfg.set_main_option("script_location", str(ENV_DIR))
    cfg.set_main_option("path_separator", "os")
    cfg.set_main_option("version_locations", str(config.versions_path))
    cfg.set_main_option("sqlalchemy.url", url.replace("%", "%%"))
    cfg.set_main_option("file_template", "%%(year)d%%(month).2d%%(day).2d_%%(rev)s_%%(slug)s")
    cfg.attributes["fletbatteries"] = config
    return cfg


def init(config: Optional[MigrationConfig] = None) -> Path:
    """Crea la carpeta de revisiones del proyecto."""
    config = config or load_config()
    path = config.versions_path
    path.mkdir(parents=True, exist_ok=True)
    readme = path / "README"
    if not readme.exists():
        readme.write_text("Revisiones de Alembic generadas con `fletbatteries makemigrations`.\n")
    return path


def makemigrations(message: str = "auto", config: Optional[MigrationConfig] = None, autogenerate: bool = True,
                   empty_ok: bool = False):
    """Genera una revisión comparando los modelos con la base de datos (o una vacía con `autogenerate=False`)."""
    from alembic import command

    config = config or load_config()
    init(config)
    cfg = alembic_config(config)
    if autogenerate and not empty_ok and not check(config, cfg=cfg) and _has_revisions(config):
        log.info("No hay cambios en los modelos")
        return None
    return command.revision(cfg, message=message, autogenerate=autogenerate)


def _has_revisions(config: MigrationConfig) -> bool:
    return any(config.versions_path.glob("*.py"))


def migrate(revision: str = "head", config: Optional[MigrationConfig] = None):
    from alembic import command

    command.upgrade(alembic_config(config), revision)


upgrade = migrate


def downgrade(revision: str, config: Optional[MigrationConfig] = None):
    from alembic import command

    command.downgrade(alembic_config(config), revision)


def stamp(revision: str = "head", config: Optional[MigrationConfig] = None):
    """Marca la base de datos con `revision` sin ejecutar migraciones (p. ej. después de `create_all`)."""
    from alembic import command

    command.stamp(alembic_config(config), revision)


def current(config: Optional[MigrationConfig] = None) -> Optional[str]:
    from alembic.runtime.migration import MigrationContext
    from sqlalchemy import create_engine

    cfg = alembic_config(config)
    engine = create_engine(cfg.get_main_option("sqlalchemy.url"))
    try:
        with engine.connect() as conn:
            return MigrationContext.configure(conn).get_current_revision()
    finally:
        engine.dispose()


def check(config: Optional[MigrationConfig] = None, cfg=None) -> list:
    """Diferencias entre los modelos y la base de datos (lista vacía = sin cambios pendientes)."""
    from alembic.autogenerate import compare_metadata
    from alembic.runtime.migration import MigrationContext
    from sqlalchemy import create_engine

    from fletbatteries.data.db import Base

    cfg = cfg or alembic_config(config)
    url = cfg.get_main_option("sqlalchemy.url")
    engine = create_engine(url)
    try:
        with engine.connect() as conn:
            context = MigrationContext.configure(conn, opts={"compare_type": True,
                                                             "include_object": include_object})
            return compare_metadata(context, Base.metadata)
    finally:
        engine.dispose()


def include_object(obj, name, type_, reflected, compare_to):
    # La tabla de versiones de Alembic no es un modelo
    return not (type_ == "table" and name == "alembic_version")


def run_env(context):
    """Cuerpo del `env.py` genérico (modo offline y online)."""
    from sqlalchemy import engine_from_config, pool

    from fletbatteries.data.db import Base

    cfg = context.config
    config = cfg.attributes.get("fletbatteries")
    if config is None:  # ejecutado con el comando `alembic` directamente
        config = load_config()
        url = prepare(config)
        cfg.set_main_option("sqlalchemy.url", url.replace("%", "%%"))
    url = cfg.get_main_option("sqlalchemy.url")
    options = {
        "target_metadata": Base.metadata,
        "compare_type": True,
        "render_as_batch": url.startswith("sqlite"),
        "include_object": include_object,
    }
    if context.is_offline_mode():
        context.configure(url=url, literal_binds=True, dialect_opts={"paramstyle": "named"}, **options)
        with context.begin_transaction():
            context.run_migrations()
        return
    connectable = cfg.attributes.get("connection")
    if connectable is not None:
        context.configure(connection=connectable, **options)
        with context.begin_transaction():
            context.run_migrations()
        return
    engine = engine_from_config(cfg.get_section(cfg.config_ini_section, {}), prefix="sqlalchemy.",
                                poolclass=pool.NullPool)
    with engine.connect() as connection:
        context.configure(connection=connection, **options)
        with context.begin_transaction():
            context.run_migrations()
    engine.dispose()
