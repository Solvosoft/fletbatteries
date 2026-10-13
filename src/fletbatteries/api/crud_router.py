"""
Router CRUD genérico para FastAPI (equivalente a `BaseObjectManagement` de djgentelella).

    from fletbatteries.api import crud_router
    app.include_router(crud_router(CustomerManager(), prefix="/api/customers"))

Endpoints:

    GET    /                ?page=&size=&search=&order_by=&<campo>[__op]=   -> {"items", "total", "page", "size"}
    GET    /lookup          ?skip=&limit=&q=                                 -> formato select2
    GET    /{id}
    POST   /                (JSON)
    PUT    /{id}            (JSON, campos parciales)
    DELETE /{id}

`APISource(url)` consume estos endpoints desde las vistas de Flet.
"""

from datetime import date, datetime, time
from typing import Any, Optional

import sqlalchemy as sa
from fastapi import APIRouter, Body, HTTPException, Request
from fastapi.encoders import jsonable_encoder
from pydantic import create_model

from fletbatteries.data.manager import BaseManager, Query
from fletbatteries.data.source import SQLAlchemySource

RESERVED_PARAMS = {"page", "size", "search", "order_by", "skip", "limit", "q"}


def schema_from_model(model, name: Optional[str] = None, exclude=("id",), optional: bool = False):
    """
    Crea un modelo Pydantic a partir de las columnas de un modelo SQLAlchemy.
    Las relaciones muchos-a-muchos / uno-a-muchos se reciben como listas de ids.
    """
    fields = {}
    mapper = sa.inspect(model)
    for rel in mapper.relationships:
        if rel.uselist and rel.key not in exclude:
            fields[rel.key] = (Optional[list[int]], None)
    for column in mapper.columns:
        if column.key in exclude:
            continue
        try:
            py_type = column.type.python_type
        except NotImplementedError:
            py_type = Any
        required = not optional and not column.nullable and column.default is None and column.server_default is None
        fields[column.key] = (py_type, ...) if required else (Optional[py_type], None)
    return create_model(name or f"{model.__name__}Schema", **fields)


def _convert(value: str, column):
    try:
        py_type = column.property.columns[0].type.python_type
    except (AttributeError, NotImplementedError, IndexError):
        return value
    if py_type is bool:
        return value.lower() in ("1", "true", "yes", "on")
    if py_type is datetime:
        return datetime.fromisoformat(value)
    if py_type is date:
        return date.fromisoformat(value[:10])
    if py_type is time:
        return time.fromisoformat(value)
    try:
        return py_type(value)
    except (TypeError, ValueError):
        return value


def parse_filters(manager: BaseManager, params: dict) -> dict:
    """Convierte los query params (`campo`, `campo__op`) en filtros del manager."""
    filters = {}
    for key, raw in params.items():
        if key in RESERVED_PARAMS or raw in (None, ""):
            continue
        name, _sep, op = key.partition("__")
        column = getattr(manager.model, name, None)
        if column is None:
            continue
        if op in ("in", "range"):
            values = [_convert(v, column) for v in raw.split(",")]
            filters[key] = tuple(values) if op == "range" else values
        elif op == "isnull":
            filters[key] = raw.lower() in ("1", "true", "yes")
        else:
            filters[key] = raw if op == "icontains" else _convert(raw, column)
    return filters


def crud_router(manager: BaseManager, prefix: str = "", tags: Optional[list] = None, schema=None,
                update_schema=None, label_field: Optional[str] = None, dependencies=None) -> APIRouter:
    router = APIRouter(prefix=prefix, tags=tags or [manager.model.__name__], dependencies=dependencies or [])
    source = SQLAlchemySource(manager, label_field=label_field)
    create_schema = schema or schema_from_model(manager.model)
    partial_schema = update_schema or schema_from_model(manager.model, name=f"{manager.model.__name__}Update",
                                                        optional=True)

    def dump(item: dict) -> dict:
        return jsonable_encoder(item)

    @router.get("")
    def list_items(request: Request, page: int = 1, size: int = 10, search: str = "",
                   order_by: Optional[str] = None):
        try:
            filters = parse_filters(manager, dict(request.query_params))
            result = source.list(Query(page=page, size=size, search=search, filters=filters, order_by=order_by))
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        return {"items": [dump(i) for i in result.items], "total": result.total, "page": page, "size": size}

    @router.get("/lookup")
    def lookup(request: Request, skip: int = 0, limit: int = 10, q: str = ""):
        filters = parse_filters(manager, dict(request.query_params))
        return source.lookup(skip=skip, limit=limit, q=q, filters=filters)

    @router.get("/{pk}")
    def get_item(pk: int):
        item = source.get(pk)
        if item is None:
            raise HTTPException(status_code=404, detail="Not found")
        return dump(item)

    @router.post("", status_code=201)
    def create_item(payload: create_schema = Body(...)):  # type: ignore[valid-type]
        try:
            return dump(source.create(payload.model_dump(exclude_unset=False)))
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    @router.put("/{pk}")
    def update_item(pk: int, payload: partial_schema = Body(...)):  # type: ignore[valid-type]
        try:
            return dump(source.update(pk, payload.model_dump(exclude_unset=True)))
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))

    @router.delete("/{pk}")
    def delete_item(pk: int):
        if not source.delete(pk):
            raise HTTPException(status_code=404, detail="Not found")
        return {"deleted": True}

    return router
