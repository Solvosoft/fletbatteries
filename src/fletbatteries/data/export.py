"""
Exportar registros de una fuente de datos a CSV.

    data = export_csv(source, Query(search="ana", filters={"active": True}), ["name", "email"])
    Path("clientes.csv").write_bytes(data)

Las columnas pueden ser nombres o `datatable.Column`; si una columna tiene un
campo de formulario (`field`), el valor se escribe con `field.display()` (por
ejemplo la etiqueta de una opción en vez de su llave). El archivo se escribe en
UTF-8 con BOM para que Excel reconozca los acentos.
"""

import csv
import dataclasses
import io
from datetime import date, datetime, time
from decimal import Decimal
from typing import Any, Iterable, Iterator, Optional

from fletbatteries.data.manager import Query

CHUNK_SIZE = 500


def _column_info(column) -> tuple[str, str, Any]:
    if isinstance(column, str):
        return column, column.replace("_", " ").capitalize(), None
    name = column.name
    label = column.label or name.replace("_", " ").capitalize()
    return name, label, getattr(column, "field", None)


def format_value(value, field=None) -> str:
    """Texto de una celda: usa `field.display()` si hay campo; listas separadas por `;`."""
    if field is not None:
        try:
            return field.display(value)
        except Exception:  # noqa: BLE001 - un display roto no debe impedir exportar
            pass
    if value is None:
        return ""
    if isinstance(value, bool):
        return "1" if value else "0"
    if isinstance(value, (datetime, date, time)):
        return value.isoformat(sep=" ") if isinstance(value, datetime) else value.isoformat()
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, (list, tuple, set)):
        return ";".join(format_value(v) for v in value)
    return str(value)


def iter_records(source, query: Optional[Query] = None, chunk_size: int = CHUNK_SIZE) -> Iterator[dict]:
    """Recorre todos los registros de la consulta por bloques (sin cargar todo a la vez)."""
    query = query or Query()
    page = 1
    while True:
        result = source.list(dataclasses.replace(query, page=page, size=chunk_size, skip=None))
        yield from result.items
        if not result.items or page * chunk_size >= result.total:
            break
        page += 1


def write_csv(rows: Iterable[Iterable[str]], delimiter: str = ",") -> bytes:
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter=delimiter, lineterminator="\r\n")
    writer.writerows(rows)
    return buffer.getvalue().encode("utf-8-sig")


def export_csv(source, query: Optional[Query] = None, columns: Optional[Iterable] = None, delimiter: str = ",",
               header: bool = True) -> bytes:
    """CSV (bytes) con los registros de `source` que cumplen `query`."""
    records = iter_records(source, query)
    if columns is None:
        first = next(records, None)
        columns = list(first.keys()) if first else []
        records = _prepend(first, records)
    info = [_column_info(c) for c in columns]

    def rows():
        if header:
            yield [label for _name, label, _field in info]
        for item in records:
            yield [format_value(item.get(name), field) for name, _label, field in info]

    return write_csv(rows(), delimiter=delimiter)


def _prepend(first, rest):
    if first is not None:
        yield first
    yield from rest
