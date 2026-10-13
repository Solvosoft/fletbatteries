"""
Fuentes de datos para tablas, CRUD, selects y calendario.

Todas trabajan con registros como `dict` (con la llave `id`) y comparten la API:

    source.list(Query(...)) -> Page(items=[dict], total=int)
    source.get(pk) -> dict | None
    source.create(data) -> dict
    source.update(pk, data) -> dict
    source.delete(pk) -> bool
    source.lookup(skip, limit, q) -> {"results": {...}, "pagination": {"more": bool}}   # selects
    source.label_for(pk) -> str | None

Implementaciones: `SQLAlchemySource` (un `BaseManager`), `APISource` (una API
REST creada con `fletbatteries.api.crud_router`) y `ListSource` (en memoria).
"""

from __future__ import annotations

import dataclasses
import itertools
from datetime import date, datetime, time
from decimal import Decimal
from typing import Any, Callable, Iterable, Optional

from fletbatteries.data.manager import EMPTY, BaseManager, Page, Query
from fletbatteries.widgets.selects import normalize_text


class DataSource:
    label_field: Optional[str] = None
    pk_field = "id"

    # --- A implementar -------------------------------------------------
    def list(self, query: Query) -> Page:
        raise NotImplementedError

    def get(self, pk) -> Optional[dict]:
        raise NotImplementedError

    def create(self, data: dict) -> dict:
        raise NotImplementedError

    def update(self, pk, data: dict) -> dict:
        raise NotImplementedError

    def delete(self, pk) -> bool:
        raise NotImplementedError

    # --- Comunes -------------------------------------------------------
    def all(self, **filters) -> list[dict]:
        return self.list(Query(page=1, size=0, filters=filters)).items

    def to_label(self, item: dict) -> str:
        if self.label_field:
            return str(item.get(self.label_field, ""))
        for key in ("name", "title", "text", "username", "email"):
            if item.get(key):
                return str(item[key])
        return str(item.get(self.pk_field, ""))

    def label_for(self, pk) -> Optional[str]:
        if pk in EMPTY:
            return None
        item = self.get(pk)
        return self.to_label(item) if item else None

    def lookup(self, skip: int = 0, limit: int = 10, q: str = "", filters: Optional[dict] = None) -> dict:
        page = self.list(Query(skip=skip, size=max(1, limit), search=q or "", filters=filters or {}))
        results = {
            str(item[self.pk_field]): {"id": item[self.pk_field], "text": self.to_label(item),
                                       "disabled": bool(item.get("disabled", False))}
            for item in page.items
        }
        return {"results": results, "pagination": {"more": skip + len(page.items) < page.total}}


class SQLAlchemySource(DataSource):
    """Fuente sobre un `BaseManager` (o un modelo, que se envuelve en uno)."""

    def __init__(self, manager, label_field: Optional[str] = None, to_dict: Optional[Callable] = None,
                 fixed_filters: Optional[dict] = None):
        self.manager = manager if isinstance(manager, BaseManager) else BaseManager(manager)
        self.label_field = label_field
        self._to_dict = to_dict
        self.fixed_filters = dict(fixed_filters or {})

    @property
    def pk_field(self):
        return self.manager.pk_name

    def to_dict(self, obj) -> dict:
        return self._to_dict(obj) if self._to_dict else self.manager.to_dict(obj)

    def to_label(self, item: dict) -> str:
        if self.label_field:
            return str(item.get(self.label_field, ""))
        return super().to_label(item)

    def list(self, query: Query) -> Page:
        if self.fixed_filters:
            query = dataclasses.replace(query, filters={**query.filters, **self.fixed_filters})
        page = self.manager.list(query)
        return Page(items=[self.to_dict(o) for o in page.items], total=page.total, page=page.page, size=page.size)

    def get(self, pk):
        obj = self.manager.get(pk)
        return self.to_dict(obj) if obj is not None else None

    def create(self, data: dict) -> dict:
        return self.to_dict(self.manager.create(**{**data, **self.fixed_filters}))

    def update(self, pk, data: dict) -> dict:
        return self.to_dict(self.manager.update(pk, **data))

    def delete(self, pk) -> bool:
        return self.manager.delete(pk)


class ListSource(DataSource):
    """Registros en memoria (útil para demos, pruebas y tablas locales)."""

    def __init__(self, items: Iterable[dict] = (), search_fields: Optional[Iterable[str]] = None,
                 label_field: Optional[str] = None):
        self.items = [dict(i) for i in items]
        self.search_fields = list(search_fields) if search_fields else None
        self.label_field = label_field
        start = max([i.get("id", 0) for i in self.items if isinstance(i.get("id"), int)], default=0) + 1
        self._ids = itertools.count(start)

    def _matches(self, item, query: Query) -> bool:
        for key, value in query.filters.items():
            if value in EMPTY:
                continue
            name, _sep, op = key.partition("__")
            current = item.get(name)
            if op in ("", "exact") and current != value:
                return False
            if op == "icontains" and normalize_text(str(value)) not in normalize_text(str(current or "")):
                return False
            if op == "in" and current not in value:
                return False
            if op == "gte" and (current is None or current < value):
                return False
            if op == "lte" and (current is None or current > value):
                return False
            if op == "range" and (current is None or not value[0] <= current <= value[1]):
                return False
        if query.search:
            q = normalize_text(query.search)
            fields = self.search_fields or list(item)
            if not any(q in normalize_text(str(item.get(f, ""))) for f in fields):
                return False
        return True

    def list(self, query: Query) -> Page:
        found = [i for i in self.items if self._matches(i, query)]
        if query.order_by:
            key = query.order_by.lstrip("-")
            found.sort(key=lambda i: (i.get(key) is None, i.get(key)), reverse=query.order_by.startswith("-"))
        total = len(found)
        if query.size:
            found = found[query.offset:query.offset + query.size]
        return Page(items=[dict(i) for i in found], total=total, page=query.page, size=query.size)

    def _find(self, pk):
        for item in self.items:
            if str(item.get("id")) == str(pk):
                return item
        return None

    def get(self, pk):
        item = self._find(pk)
        return dict(item) if item else None

    def create(self, data: dict) -> dict:
        item = {"id": next(self._ids), **data}
        self.items.append(item)
        return dict(item)

    def update(self, pk, data: dict) -> dict:
        item = self._find(pk)
        if item is None:
            raise ValueError(f"Registro {pk} no encontrado")
        item.update(data)
        return dict(item)

    def delete(self, pk) -> bool:
        item = self._find(pk)
        if item is None:
            return False
        self.items.remove(item)
        return True


def to_jsonable(value: Any):
    if isinstance(value, (datetime, date, time)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, dict):
        return {k: to_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_jsonable(v) for v in value]
    if hasattr(value, "name") and hasattr(value, "read"):  # UploadedFile
        return value.name
    return value


class APISource(DataSource):
    """
    Fuente sobre una API REST con el formato de `fletbatteries.api.crud_router`:

        GET    {url}?page=&size=&search=&order_by=&<filtros>  -> {"items": [...], "total": n}
        GET    {url}/lookup?skip=&limit=&q=                     -> formato select2
        GET    {url}/{id}    POST {url}    PUT {url}/{id}    DELETE {url}/{id}
    """

    def __init__(self, url: str, label_field: Optional[str] = None, timeout: float = 10, headers: Optional[dict] = None,
                 session=None):
        self.url = url.rstrip("/")
        self.label_field = label_field
        self.timeout = timeout
        self.headers = headers or {}
        self._session = session

    @property
    def http(self):
        if self._session is not None:
            return self._session
        import requests

        return requests

    def _request(self, method: str, path: str = "", **kwargs):
        response = getattr(self.http, method)(f"{self.url}{path}", headers=self.headers, timeout=self.timeout, **kwargs)
        if response.status_code == 404 and method in ("get", "delete"):
            return None
        if response.status_code >= 400:
            try:
                detail = response.json().get("detail")
            except Exception:
                detail = response.text
            raise ValueError(detail or f"Error {response.status_code}")
        return response.json()

    def list(self, query: Query) -> Page:
        params = {"page": query.page, "size": query.size, "search": query.search or ""}
        if query.order_by:
            params["order_by"] = query.order_by
        for key, value in query.filters.items():
            if value in EMPTY:
                continue
            params[key] = ",".join(str(to_jsonable(v)) for v in value) if isinstance(value, (list, tuple)) else \
                to_jsonable(value)
        data = self._request("get", params=params)
        return Page(items=data["items"], total=data["total"], page=query.page, size=query.size)

    def get(self, pk):
        return self._request("get", f"/{pk}")

    def create(self, data: dict) -> dict:
        return self._request("post", json=to_jsonable(data))

    def update(self, pk, data: dict) -> dict:
        return self._request("put", f"/{pk}", json=to_jsonable(data))

    def delete(self, pk) -> bool:
        result = self._request("delete", f"/{pk}")
        return bool(result and result.get("deleted", True))

    def lookup(self, skip: int = 0, limit: int = 10, q: str = "", filters: Optional[dict] = None) -> dict:
        return self._request("get", "/lookup", params={"skip": skip, "limit": limit, "q": q or "", **(filters or {})})
