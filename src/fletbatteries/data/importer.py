"""
Importar registros desde CSV validando cada fila con un formulario.

    importer = CSVImporter(CustomerForm, SQLAlchemySource(CustomerManager()), key_field="email")
    result = importer.preview(Path("clientes.csv").read_bytes())   # no guarda nada
    for row in result.invalid_rows:
        print(row.line, row.errors)
    counts = importer.run(result)          # guarda solo las filas válidas -> {"created", "updated", "failed"}

Los encabezados del CSV se relacionan con los campos por nombre o por
etiqueta (sin importar mayúsculas). Los valores se convierten con
`field.from_text` (opciones por llave o texto, registros relacionados por id
o etiqueta, listas separadas por `;`).

Con `key_field` las filas cuyo valor ya existe actualizan ese registro; sin
él, todas las filas crean registros nuevos. Si la fuente usa
`HistoryMixin`/`TrashMixin`, envuelva `run()` en `acting_as(usuario)`.
"""

import csv
import dataclasses
import io
import logging
from typing import Any, Optional

from fletbatteries.data.manager import Query
from fletbatteries.forms.validators import ValidationError
from fletbatteries.i18n import _

log = logging.getLogger(__name__)


@dataclasses.dataclass
class RowResult:
    line: int
    raw: dict
    data: dict = dataclasses.field(default_factory=dict)
    errors: dict = dataclasses.field(default_factory=dict)
    action: str = "create"  # "create" | "update"
    pk: Any = None

    @property
    def valid(self) -> bool:
        return not self.errors

    def error_text(self) -> str:
        parts = []
        for name, messages in self.errors.items():
            prefix = "" if name == "__all__" else f"{name}: "
            parts.append(prefix + " ".join(messages))
        return "; ".join(parts)


@dataclasses.dataclass
class ImportResult:
    rows: list[RowResult] = dataclasses.field(default_factory=list)
    columns: dict = dataclasses.field(default_factory=dict)  # encabezado -> campo
    unknown_columns: list[str] = dataclasses.field(default_factory=list)
    error: Optional[str] = None

    @property
    def valid_rows(self) -> list[RowResult]:
        return [r for r in self.rows if r.valid]

    @property
    def invalid_rows(self) -> list[RowResult]:
        return [r for r in self.rows if not r.valid]

    @property
    def to_create(self) -> int:
        return sum(1 for r in self.valid_rows if r.action == "create")

    @property
    def to_update(self) -> int:
        return sum(1 for r in self.valid_rows if r.action == "update")


def decode(data: bytes) -> str:
    for encoding in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


def read_csv(data: bytes) -> tuple[list[str], list[dict]]:
    """Encabezados y filas de un CSV (detecta el separador `,` `;` o tabulador)."""
    text = decode(data)
    sample = text[:4096]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
    except csv.Error:
        dialect = csv.excel
    reader = csv.DictReader(io.StringIO(text), dialect=dialect)
    rows = [row for row in reader if any((v or "").strip() for v in row.values() if isinstance(v, str))]
    return [h for h in (reader.fieldnames or []) if h is not None], rows


class CSVImporter:
    def __init__(self, form_class, source, key_field: Optional[str] = None, fields: Optional[list[str]] = None,
                 fixed_data: Optional[dict] = None):
        self.form_class = form_class
        self.source = source
        self.key_field = key_field
        self.fields = list(fields) if fields is not None else None
        self.fixed_data = dict(fixed_data or {})

    # ------------------------------------------------------------------
    # Columnas
    # ------------------------------------------------------------------
    def import_fields(self) -> dict:
        fields = self.form_class.base_fields
        names = self.fields or [n for n, f in fields.items() if not f.disabled]
        return {n: fields[n] for n in names if n in fields}

    def template_csv(self) -> bytes:
        """CSV vacío con los encabezados que se esperan (para descargar como plantilla)."""
        from fletbatteries.data.export import write_csv

        header = list(self.import_fields())
        if self.key_field and self.key_field not in header:
            header.insert(0, self.key_field)
        return write_csv([header])

    def map_columns(self, headers: list[str]) -> tuple[dict, list[str]]:
        fields = self.import_fields()
        lookup = {}
        for name, field in fields.items():
            lookup[name.lower()] = name
            if field.label:
                lookup.setdefault(str(field.label).strip().lower(), name)
        if self.key_field:
            lookup.setdefault(self.key_field.lower(), self.key_field)
        mapping, unknown = {}, []
        for header in headers:
            name = lookup.get((header or "").strip().lower())
            if name:
                mapping[header] = name
            else:
                unknown.append(header)
        return mapping, unknown

    # ------------------------------------------------------------------
    # Vista previa y ejecución
    # ------------------------------------------------------------------
    def find_existing(self, key_value) -> Optional[dict]:
        if not self.key_field or key_value in (None, ""):
            return None
        if self.key_field == getattr(self.source, "pk_field", "id"):
            try:
                return self.source.get(int(key_value) if str(key_value).isdigit() else key_value)
            except Exception:  # noqa: BLE001
                return None
        items = self.source.list(Query(page=1, size=1, filters={self.key_field: key_value})).items
        return items[0] if items else None

    def preview(self, data: bytes) -> ImportResult:
        """Lee y valida todas las filas sin guardar nada."""
        try:
            headers, rows = read_csv(data)
        except Exception as ex:  # noqa: BLE001
            log.exception("No se pudo leer el CSV")
            return ImportResult(error=_("The file could not be read: {error}", error=str(ex)))
        mapping, unknown = self.map_columns(headers)
        result = ImportResult(columns=mapping, unknown_columns=unknown)
        if not mapping:
            result.error = _("No column of the file matches the form fields.")
            return result
        fields = self.import_fields()
        for index, raw in enumerate(rows, start=2):  # la línea 1 es el encabezado
            values = {mapping[h]: v for h, v in raw.items() if h in mapping}
            row = RowResult(line=index, raw=raw)
            existing = self.find_existing(values.get(self.key_field)) if self.key_field else None
            form = self.form_class(instance=existing)
            if existing is not None:
                row.action, row.pk = "update", existing.get(getattr(self.source, "pk_field", "id"))
                # Las columnas que no vienen en el archivo conservan su valor
                base = {n: form.initial.get(n) for n in fields}
            else:
                base = {}
            converted = {n: fields[n].from_text(v) for n, v in values.items() if n in fields}
            prepared = {n: fields[n].prepare_value(v) if v is not None else None for n, v in base.items()}
            cleaned, errors = form.validate_data({**prepared, **converted})
            # save_data(): los archivos pasan a su nombre guardado, como en el CRUD
            row.data, row.errors = (form.save_data() if not errors else cleaned), errors
            result.rows.append(row)
        return result

    def save_row(self, row: RowResult) -> dict:
        data = {**row.data, **self.fixed_data}
        if row.action == "update":
            return self.source.update(row.pk, data)
        return self.source.create(data)

    def run(self, result: ImportResult) -> dict:
        """Guarda las filas válidas; devuelve los conteos y los errores al guardar (por línea)."""
        counts = {"created": 0, "updated": 0, "failed": 0, "errors": {}}
        for row in result.valid_rows:
            try:
                self.save_row(row)
            except ValidationError as e:
                row.errors = e.error_dict or {"__all__": e.messages}
            except Exception as e:  # noqa: BLE001 - se informa por fila
                log.exception("Error importando la línea %s", row.line)
                row.errors = {"__all__": [str(e) or type(e).__name__]}
            if row.errors:
                counts["failed"] += 1
                counts["errors"][row.line] = row.error_text()
            else:
                counts["created" if row.action == "create" else "updated"] += 1
        return counts
