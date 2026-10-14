"""Conexión a la base de datos (un engine por URL) y sesiones transaccionales."""

import importlib
from contextlib import contextmanager
from typing import Iterable, Iterator, Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

Base = declarative_base()

# Módulos con los modelos que trae el framework (tablas `fb_*`)
FRAMEWORK_MODEL_MODULES = (
    "fletbatteries.auth.models",
    "fletbatteries.contrib.settings",
    "fletbatteries.contrib.notifications",
    "fletbatteries.contrib.help",
    "fletbatteries.contrib.history",
)


def import_models(modules: Iterable[str] = (), framework: bool = True) -> list:
    """
    Importa los módulos de modelos para registrarlos en `Base.metadata` (antes
    de `create_all` o de generar migraciones). Incluye los del framework.
    """
    names = [*(FRAMEWORK_MODEL_MODULES if framework else ()), *modules]
    return [importlib.import_module(name) for name in names if name]


class Database:
    """
    Envuelve un engine de SQLAlchemy.

        db = Database("sqlite:///app.db")
        with db.session() as s:
            s.add(obj)          # commit automático al salir, rollback si hay error
    """

    _engines: dict = {}

    def __init__(self, url: str, **engine_kwargs):
        self.url = url
        if url not in self._engines:
            if url.startswith("sqlite"):
                engine_kwargs.setdefault("connect_args", {"check_same_thread": False})
            self._engines[url] = create_engine(url, **engine_kwargs)
        self.engine = self._engines[url]
        # expire_on_commit=False: los objetos devueltos siguen usables después de cerrar la sesión
        self.SessionLocal = sessionmaker(bind=self.engine, autoflush=False, expire_on_commit=False)

    @contextmanager
    def session(self) -> Iterator[Session]:
        s = self.SessionLocal()
        try:
            yield s
            s.commit()
        except Exception:
            s.rollback()
            raise
        finally:
            s.close()

    def create_all(self, base=None):
        (base or Base).metadata.create_all(bind=self.engine)

    def drop_all(self, base=None):
        (base or Base).metadata.drop_all(bind=self.engine)


_default: Optional[Database] = None


def set_default_database(db: "Database | str") -> Database:
    """Define la base de datos que usan los managers que no reciben `db`."""
    global _default
    _default = Database(db) if isinstance(db, str) else db
    return _default


def get_default_database() -> Database:
    if _default is None:
        raise RuntimeError("No hay base de datos por defecto: llame a set_default_database(url)")
    return _default
