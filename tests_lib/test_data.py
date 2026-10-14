"""Manager (lookups, únicos, masivos), fuentes, exportar e importar CSV y migraciones."""

from decimal import Decimal

import pytest

from fletbatteries.data import ListSource, Query, SQLAlchemySource
from fletbatteries.data.importer import CSVImporter
from fletbatteries.forms.validators import ValidationError

from tests_lib.models import CategoryManager, DocManager, ItemManager, Tag
from tests_lib.views import ItemForm


@pytest.fixture
def items(db):
    cats = CategoryManager()
    hw = cats.create(name="Hardware")
    sw = cats.create(name="Software")
    manager = ItemManager()
    with manager.session() as s:
        s.add_all([Tag(name="nuevo"), Tag(name="oferta")])
    rows = [
        dict(name="Teclado", code="K-1", price=Decimal("25.50"), kind="a", category_id=hw.id, tags=[1]),
        dict(name="Mouse", code="M-1", price=Decimal("10"), kind="b", category_id=hw.id, tags=[2]),
        dict(name="Editor 100%", code="E_1", price=Decimal("99"), kind="a", category_id=sw.id),
        dict(name="Monitor", code=None, price=None, kind=None, active=False),
    ]
    return [manager.create(**r) for r in rows]


def names(result) -> list[str]:
    return sorted(i.name for i in result)


def test_manager_lookups(items):
    m = ItemManager()
    assert names(m.filter(price__gt=Decimal("10"))) == ["Editor 100%", "Teclado"]
    assert names(m.filter(price__lt=Decimal("25"))) == ["Mouse"]
    assert names(m.filter(kind__ne="a")) == ["Mouse"]
    assert names(m.filter(name__istartswith="mo")) == ["Monitor", "Mouse"]
    assert names(m.filter(name__startswith="Mo")) == ["Monitor", "Mouse"]
    assert names(m.filter(name__endswith="do")) == ["Teclado"]
    assert names(m.filter(name__iexact="TECLADO")) == ["Teclado"]
    assert names(m.filter(name__contains="100%")) == ["Editor 100%"]
    # Los comodines de LIKE se escapan
    assert names(m.filter(code__icontains="_")) == ["Editor 100%"]
    assert names(m.filter(name__icontains="%")) == ["Editor 100%"]
    assert names(m.filter(__or__=[{"kind": "b"}, {"active": False}])) == ["Monitor", "Mouse"]
    # A través de relaciones (muchos-a-uno y muchos-a-muchos)
    assert names(m.filter(category__name="Software")) == ["Editor 100%"]
    assert names(m.filter(category__name__icontains="hard")) == ["Mouse", "Teclado"]
    assert names(m.filter(tags__name="oferta")) == ["Mouse"]
    with pytest.raises(ValueError):
        m.filter(price__nope=1)


def test_list_source_lookups():
    src = ListSource([{"id": 1, "name": "Ana", "age": 30}, {"id": 2, "name": "Álvaro", "age": 20},
                      {"id": 3, "name": "Berta", "age": None}])

    def found(**filters):
        return sorted(i["name"] for i in src.list(Query(size=0, filters=filters)).items)

    assert found(age__gt=25) == ["Ana"]
    assert found(age__lt=25) == ["Álvaro"]
    assert found(name__istartswith="a") == ["Ana", "Álvaro"]
    assert found(name__ne="Ana") == ["Berta", "Álvaro"]
    assert found(age__isnull=True) == ["Berta"]
    assert found(__or__=[{"age__gte": 30}, {"name": "Berta"}]) == ["Ana", "Berta"]


def test_validate_unique_raises_field_error(items):
    with pytest.raises(ValidationError) as info:
        ItemManager().create(name="Otro", code="K-1")
    assert set(info.value.error_dict) == {"code"}
    assert isinstance(info.value, ValueError)  # compatibilidad con quien capturaba ValueError


def test_bulk_operations(items):
    m = ItemManager()
    result = m.update_many([items[0].id, items[1].id, 999], active=False)
    assert result.done == [items[0].id, items[1].id] and 999 in result.failed
    assert m.count(active=False) == 3
    src = SQLAlchemySource(m)
    deleted = src.delete_many([items[0].id, 12345])
    assert deleted.done == [items[0].id] and deleted.failed == {12345: "not found"}
    assert m.get(items[0].id) is None


def test_bulk_delete_uses_trash_and_history(db):
    from fletbatteries.contrib.history import history_for

    docs = DocManager()
    a, b = docs.create(title="A"), docs.create(title="B")
    assert docs.delete_many([a.id, b.id]).count == 2
    assert docs.count() == 0 and docs.list_deleted().total == 2
    assert [e.action for e in history_for("Doc", a.id)] == ["deleted", "created"]


def test_export_csv_all_pages_with_labels(items):
    src = SQLAlchemySource(ItemManager())
    from fletbatteries.widgets.datatable import DataTable

    table = DataTable(src, columns=["name", "kind", "category_id", "price", "active"], form=ItemForm,
                      page_size=2, order_by="name")
    data = table.export_csv()
    assert data.startswith(b"\xef\xbb\xbf")  # BOM para Excel
    lines = data.decode("utf-8-sig").splitlines()
    assert lines[0] == "Nombre,Tipo,Categoría,Precio,Active"
    assert len(lines) == 5  # todas las páginas, no solo la visible
    assert lines[1] == "Editor 100%,Tipo A,Software,99.00,Sí"
    # Respeta la búsqueda actual
    table.search = "mo"
    assert len(table.export_csv().decode("utf-8-sig").splitlines()) == 3


CSV_IMPORT = (
    "Nombre;Código;Precio;Tipo;Categoría;Extra\n"
    "Parlante;P-1;15,5;Tipo B;Hardware;x\n"
    "Teclado mecánico;K-1;30;a;;\n"
    ";X-1;abc;Tipo Z;Nada;\n"
).encode("cp1252")


def test_importer_preview_and_run(items):
    src = SQLAlchemySource(ItemManager())
    importer = CSVImporter(ItemForm, src, key_field="code")
    result = importer.preview(CSV_IMPORT)
    assert result.error is None
    assert result.unknown_columns == ["Extra"]
    assert [r.action for r in result.rows] == ["create", "update", "create"]
    assert result.to_create == 1 and result.to_update == 1
    bad = result.invalid_rows[0]
    assert bad.line == 4 and {"name", "price", "kind", "category_id"} <= set(bad.errors)
    good = result.rows[0]
    assert good.data["price"] == Decimal("15.50") and good.data["kind"] == "b"
    assert good.data["category_id"] == items[0].category_id  # categoría por etiqueta

    counts = importer.run(result)
    assert counts == {"created": 1, "updated": 1, "failed": 0, "errors": {}}
    m = ItemManager()
    assert m.first(code="P-1").name == "Parlante"
    updated = m.first(code="K-1")
    # La fila de actualización conserva lo que no venía en el archivo
    assert updated.name == "Teclado mecánico" and updated.category_id is None and updated.kind == "a"


def test_importer_template_and_errors(db):
    importer = CSVImporter(ItemForm, SQLAlchemySource(ItemManager()), key_field="code")
    header = importer.template_csv().decode("utf-8-sig").strip()
    assert header == "name,code,price,active,kind,category_id"
    assert importer.preview(b"a,b\n1,2\n").error  # ninguna columna coincide


def test_framework_migrations(tmp_path, monkeypatch):
    """Revisión autogenerada para las tablas del framework, aplicada a una BD vacía, sin diferencias."""
    from fletbatteries.data import migrations

    monkeypatch.chdir(tmp_path)
    url = f"sqlite:///{tmp_path / 'mig.db'}"
    config = migrations.MigrationConfig(db_url=url, migrations_dir=str(tmp_path / "versions"), root=tmp_path)
    # Solo los modelos del framework (las tablas de prueba están en otra Base)
    script = migrations.makemigrations("inicial", config)
    assert script is not None and (tmp_path / "versions").exists()
    migrations.migrate("head", config)
    assert migrations.check(config) == []
    assert migrations.current(config) == script.revision
    # Sin cambios no se crea otra revisión
    assert migrations.makemigrations("nada", config) is None
