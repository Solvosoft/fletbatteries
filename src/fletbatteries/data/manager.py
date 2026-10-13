"""
`BaseManager`: CRUD genérico sobre un modelo SQLAlchemy.

    class CustomerManager(BaseManager):
        model = Customer
        search_fields = ("name", "email")
        default_order = "name"

    manager = CustomerManager()
    page = manager.list(Query(page=1, size=10, search="ana", filters={"active": True}, order_by="-name"))
    page.items, page.total

Filtros: `campo`, `campo__icontains`, `campo__in`, `campo__gte`, `campo__lte`,
`campo__range` (tupla). Los valores vacíos se ignoran.
"""

from __future__ import annotations

import dataclasses
import math
from contextlib import contextmanager
from datetime import date, datetime
from typing import Any, Generic, Iterable, Optional, TypeVar

import sqlalchemy as sa
from sqlalchemy.orm import Session

from fletbatteries.data.db import Database, get_default_database

M = TypeVar("M")

EMPTY = (None, "", [], (), {})


@dataclasses.dataclass
class Query:
    page: int = 1
    size: int = 10
    search: str = ""
    filters: dict = dataclasses.field(default_factory=dict)
    order_by: Optional[str] = None  # "campo" o "-campo"
    skip: Optional[int] = None  # desplazamiento explícito (si no, se calcula con `page`)

    @property
    def offset(self) -> int:
        if self.skip is not None:
            return max(0, self.skip)
        return max(0, (self.page - 1) * self.size)


@dataclasses.dataclass
class Page:
    items: list
    total: int
    page: int = 1
    size: int = 10

    @property
    def pages(self) -> int:
        return max(1, math.ceil(self.total / self.size)) if self.size else 1

    @property
    def has_next(self) -> bool:
        return self.page < self.pages


class BaseManager(Generic[M]):
    model: Any = None
    search_fields: tuple = ()
    default_order: Optional[str] = None
    unique_fields: tuple = ()  # campos que no se pueden repetir (se valida antes de guardar)

    def __init__(self, model=None, db: Optional[Database] = None, search_fields: Optional[Iterable[str]] = None,
                 default_order: Optional[str] = None):
        if model is not None:
            self.model = model
        if self.model is None:
            raise ValueError(f"{type(self).__name__} necesita un modelo")
        self._db = db
        if search_fields is not None:
            self.search_fields = tuple(search_fields)
        if default_order is not None:
            self.default_order = default_order

    @property
    def db(self) -> Database:
        return self._db or get_default_database()

    @contextmanager
    def session(self):
        with self.db.session() as s:
            yield s

    # ------------------------------------------------------------------
    # Metadatos
    # ------------------------------------------------------------------
    @property
    def mapper(self):
        return sa.inspect(self.model)

    @property
    def pk_name(self) -> str:
        return self.mapper.primary_key[0].key

    def column_names(self) -> list[str]:
        return [c.key for c in self.mapper.column_attrs]

    def get_search_fields(self) -> tuple:
        if self.search_fields:
            return self.search_fields
        return tuple(c.key for c in self.mapper.columns if isinstance(c.type, sa.String))

    # ------------------------------------------------------------------
    # Consultas
    # ------------------------------------------------------------------
    def base_query(self):
        """Consulta base; las subclases pueden filtrar (p. ej. registros eliminados)."""
        return sa.select(self.model)

    def _column(self, name: str):
        attr = getattr(self.model, name, None)
        if attr is None:
            raise ValueError(f"{self.model.__name__} no tiene el campo '{name}'")
        return attr

    def apply_filters(self, stmt, filters: Optional[dict]):
        for key, value in (filters or {}).items():
            if value in EMPTY:
                continue
            name, _sep, op = key.partition("__")
            column = self._column(name)
            if op in ("", "exact"):
                stmt = stmt.where(column == value)
            elif op == "icontains":
                stmt = stmt.where(column.ilike(f"%{value}%"))
            elif op == "in":
                stmt = stmt.where(column.in_(list(value)))
            elif op == "gte":
                stmt = stmt.where(column >= value)
            elif op == "lte":
                stmt = stmt.where(column <= value)
            elif op == "range":
                start, end = value
                if isinstance(start, date) and not isinstance(start, datetime) and _is_datetime(column):
                    start = datetime.combine(start, datetime.min.time())
                    end = datetime.combine(end, datetime.max.time())
                stmt = stmt.where(column.between(start, end))
            elif op == "isnull":
                stmt = stmt.where(column.is_(None) if value else column.is_not(None))
            else:
                raise ValueError(f"Operador de filtro no soportado: {op}")
        return stmt

    def apply_search(self, stmt, search: str):
        search = (search or "").strip()
        if not search:
            return stmt
        clauses = [sa.cast(self._column(f), sa.String).ilike(f"%{search}%") for f in self.get_search_fields()]
        return stmt.where(sa.or_(*clauses)) if clauses else stmt

    def apply_order(self, stmt, order_by: Optional[str]):
        order_by = order_by or self.default_order
        if not order_by:
            return stmt.order_by(self._column(self.pk_name))
        desc = order_by.startswith("-")
        column = self._column(order_by.lstrip("-"))
        return stmt.order_by(column.desc() if desc else column.asc())

    def list(self, query: Optional[Query] = None, **kwargs) -> Page:
        query = query or Query(**kwargs)
        with self.session() as s:
            stmt = self.apply_search(self.apply_filters(self.base_query(), query.filters), query.search)
            total = s.scalar(sa.select(sa.func.count()).select_from(stmt.order_by(None).subquery()))
            stmt = self.apply_order(stmt, query.order_by)
            if query.size:
                stmt = stmt.offset(query.offset).limit(query.size)
            items = list(s.scalars(stmt).unique())
        return Page(items=items, total=total or 0, page=query.page, size=query.size)

    def get_all(self, **filters) -> list:
        with self.session() as s:
            stmt = self.apply_order(self.apply_filters(self.base_query(), filters), None)
            return list(s.scalars(stmt).unique())

    def filter(self, **filters) -> list:
        return self.get_all(**filters)

    def first(self, **filters):
        items = self.list(Query(page=1, size=1, filters=filters)).items
        return items[0] if items else None

    def count(self, **filters) -> int:
        with self.session() as s:
            stmt = self.apply_filters(self.base_query(), filters)
            return s.scalar(sa.select(sa.func.count()).select_from(stmt.subquery())) or 0

    def get(self, pk):
        with self.session() as s:
            stmt = self.base_query().where(self._column(self.pk_name) == pk)
            return s.scalars(stmt).unique().first()

    get_by_id = get

    # ------------------------------------------------------------------
    # Escritura
    # ------------------------------------------------------------------
    def _assign(self, s: Session, obj, data: dict):
        relationships = self.mapper.relationships
        for key, value in data.items():
            if key in relationships:
                rel = relationships[key]
                target = rel.mapper.class_
                if rel.uselist:
                    value = [v if isinstance(v, target) else s.get(target, v) for v in (value or [])]
                    value = [v for v in value if v is not None]
                elif value is not None and not isinstance(value, target):
                    value = s.get(target, value)
            elif not hasattr(self.model, key):
                continue
            setattr(obj, key, value)

    def validate_unique(self, s: Session, obj, data: dict):
        from fletbatteries.i18n import _

        pk_col = self._column(self.pk_name)
        current_pk = getattr(obj, self.pk_name, None)
        for name in self.unique_fields:
            if name not in data or data[name] in EMPTY:
                continue
            stmt = sa.select(pk_col).where(self._column(name) == data[name])
            if current_pk is not None:
                stmt = stmt.where(pk_col != current_pk)
            if s.scalar(stmt.limit(1)) is not None:
                raise ValueError(_("{field} \"{value}\" already exists.", field=name, value=data[name]))

    def before_save(self, s: Session, obj, data: dict, created: bool):
        """Hook antes de guardar (dentro de la transacción)."""

    def after_save(self, s: Session, obj, created: bool, changes: dict):
        """Hook después de guardar (dentro de la transacción)."""

    def before_delete(self, s: Session, obj):
        """Hook antes de eliminar (dentro de la transacción)."""

    def create(self, **data):
        with self.session() as s:
            obj = self.model()
            self.validate_unique(s, obj, data)
            self.before_save(s, obj, data, True)
            self._assign(s, obj, data)
            s.add(obj)
            s.flush()
            self.after_save(s, obj, True, {k: (None, v) for k, v in self.to_dict(obj).items()})
            s.flush()
            s.refresh(obj)
            self._load(obj)
            return obj

    def update(self, pk, **data):
        with self.session() as s:
            obj = s.scalars(self.base_query().where(self._column(self.pk_name) == pk)).unique().first()
            if obj is None:
                raise ValueError(f"{self.model.__name__} {pk} no encontrado")
            before = self.to_dict(obj)
            self.validate_unique(s, obj, data)
            self.before_save(s, obj, data, False)
            self._assign(s, obj, data)
            s.flush()
            after = self.to_dict(obj)
            changes = {k: (before.get(k), v) for k, v in after.items() if before.get(k) != v}
            self.after_save(s, obj, False, changes)
            s.flush()
            s.refresh(obj)
            self._load(obj)
            return obj

    def delete(self, pk) -> bool:
        with self.session() as s:
            obj = s.scalars(self.base_query().where(self._column(self.pk_name) == pk)).unique().first()
            if obj is None:
                return False
            self.before_delete(s, obj)
            self.perform_delete(s, obj)
            return True

    def perform_delete(self, s: Session, obj):
        s.delete(obj)

    def _load(self, obj):
        """Carga las relaciones antes de cerrar la sesión para usarlas después."""
        for rel in self.mapper.relationships:
            getattr(obj, rel.key)

    # ------------------------------------------------------------------
    # Serialización
    # ------------------------------------------------------------------
    def to_dict(self, obj) -> dict:
        data = {c.key: getattr(obj, c.key) for c in self.mapper.column_attrs}
        state = sa.inspect(obj)
        for rel in self.mapper.relationships:
            if rel.key in state.unloaded:
                continue
            value = getattr(obj, rel.key)
            if rel.uselist:
                data[rel.key] = [getattr(v, "id", v) for v in value or []]
            elif value is not None and rel.key not in data:
                data[rel.key] = getattr(value, "id", value)
        return data

    def label_for(self, obj) -> str:
        for attr in ("name", "title", "text", "username", "email"):
            value = getattr(obj, attr, None)
            if value:
                return str(value)
        return str(getattr(obj, self.pk_name, obj))


def _is_datetime(column) -> bool:
    try:
        return isinstance(column.property.columns[0].type, sa.DateTime)
    except (AttributeError, IndexError):
        return False
