"""Historial, papelera, gráficos declarativos, mapas y Markdown."""

import flet as ft
import pytest

from fletbatteries import forms
from fletbatteries.auth import AuthUser
from fletbatteries.contrib.history import acting_as, history_for
from tests.test_flows import dialog_open

EDITOR = AuthUser(id=5, username="editora")


@pytest.fixture
def notes():
    from data.manager.note_manager import NoteManager

    return NoteManager()


def test_history_records_changes_with_user(notes):
    with acting_as(EDITOR):
        note = notes.create(title="Historial", category="ideas")
        notes.update(note.id, title="Historial 2", category="ideas")
        notes.update(note.id, title="Historial 2")  # sin cambios: no registra
    entries = list(reversed(history_for("Note", note.id)))
    assert [e.action for e in entries] == ["created", "updated"]
    assert entries[1].changes_dict == {"title": ["Historial", "Historial 2"]}
    assert all(e.username == "editora" for e in entries)
    assert notes.history(note.id)[0].action == "updated"


def test_trash_soft_delete_restore_and_purge(notes):
    with acting_as(EDITOR):
        note = notes.create(title="A la papelera")
        assert notes.delete(note.id)
    assert notes.get(note.id) is None
    assert notes.first(title="A la papelera") is None
    trashed = notes.list_deleted().items
    assert [n.title for n in trashed if n.id == note.id] == ["A la papelera"]
    assert trashed[0].deleted_by == "editora"

    with acting_as(EDITOR):
        assert notes.restore(note.id)
    assert notes.get(note.id).title == "A la papelera"
    assert [e.action for e in history_for("Note", note.id)][:2] == ["restored", "deleted"]

    notes.delete(note.id)
    assert notes.hard_delete(note.id)
    assert not notes.restore(note.id)
    assert note.id not in [n.id for n in notes.list_deleted().items]


async def test_notes_crud_markdown_color_location_and_history(logged_app, notes):
    app = logged_app
    await app.goto("/notes")
    await app.click(app.find_one(key="crud_add"))
    await app.fill(app.find_one(key="title").field, "Nota de prueba")
    content = app.find_one(key="content")
    await app.fill(content.editor, "Texto")
    await app.click(app.find_one(type=ft.IconButton, root=content, where=lambda c: c.icon == ft.Icons.FORMAT_BOLD))
    assert content.value == "Texto****"
    await app.click(content.preview_button)
    assert content.preview.visible and content.preview.value == "Texto****"
    await app.click(content.write_button)

    await app.fill(app.find_one(key="color").field, "#43a047")
    location = app.find_one(key="location")
    await app.fill(location.lat_field, "9.93")
    await app.fill(location.lng_field, "-84.08")
    assert location.value == "9.930000,-84.080000"
    assert len(location.marker_layer.markers) == 1
    await app.click(app.find_one(type=ft.Button, text="Guardar"))
    assert app.find(text="Guardado exitosamente")

    note = notes.first(title="Nota de prueba")
    assert note.color == "#43A047" and note.location == "9.930000,-84.080000" and note.content == "Texto****"

    await app.click(app.find_one(key=f"history-{note.id}"))
    assert app.find(contains="Creado · admin")
    await app.click(app.find_one(type=ft.TextButton, text="Cerrar"))

    await app.click(app.find_one(key=f"delete-{note.id}"))
    await app.click(app.find_one(type=ft.Button, text="Eliminar"))
    assert notes.get(note.id) is None and note.id in [n.id for n in notes.list_deleted().items]

    # Restaurar desde la papelera
    await app.goto("/trash")
    await app.click(app.find_one(key=f"restore-{note.id}"))
    assert app.find(text="Restaurado exitosamente")
    assert notes.get(note.id) is not None

    # Historial general con filtro por acción
    await app.goto("/history")
    table = app.find_one(where=lambda c: type(c).__name__ == "DataTable" and hasattr(c, "source"))
    table.set_filters(action="restored", model="Note")
    assert all(i["action"] == "restored" for i in table.items) and table.items
    app.assert_no_errors()


async def test_trash_view_purge(logged_app, notes):
    note = notes.create(title="Borrar definitivo")
    notes.delete(note.id)
    app = logged_app
    await app.goto("/trash")
    await app.click(app.find_one(key=f"purge-{note.id}"))
    assert dialog_open(app)
    await app.click(app.find_one(type=ft.Button, text="Eliminar definitivamente"))
    assert note.id not in [n.id for n in notes.list_deleted().items]
    app.assert_no_errors()


def test_count_by_and_charts(notes):
    from fletbatteries.widgets import charts as fbc

    for cat in ("trabajo", "trabajo", "personal"):
        notes.create(title=f"Chart {cat}", category=cat)
    data = fbc.count_by(notes, "category", filters={"title__icontains": "Chart "})()
    assert dict(zip(data["labels"], data["datasets"][0]["data"])) == {"personal": 1.0, "trabajo": 2.0}

    sales = {"labels": ["a", "b"], "datasets": [{"label": "x", "data": [1, 3]}, {"label": "y", "data": [2, 2]}]}
    for cls in (fbc.BarChart, fbc.StackedBarChart, fbc.HorizontalBarChart, fbc.LineChart, fbc.PieChart,
                fbc.DoughnutChart):
        chart = cls(sales, title=cls.__name__)
        assert chart.content is not None
    stacked = fbc.StackedBarChart(sales).content.controls[-2].content
    assert [g.rods[0].to_y for g in stacked.groups] == [3, 5]
    scatter = fbc.ScatterChart({"labels": [], "datasets": [{"label": "p", "data": [(1, 2), (3, 4)]}]})
    assert len(scatter.content.controls[-2].content.spots) == 2

    assert [fbc.nice_max(v) for v in (0, 0.7, 24.2, 40.7, 101)] == [1, 1, 25, 50, 200]

    source_calls = []
    chart = fbc.PieChart(source=lambda: source_calls.append(1) or sales)
    chart.refresh()
    assert len(source_calls) == 2


def test_map_point_field_and_widget():
    from fletbatteries.widgets.maps import MapPointInput

    field = forms.MapPointField()
    assert field.clean("10.5, -84") == "10.500000,-84.000000"
    with pytest.raises(forms.ValidationError, match="punto válido"):
        field.clean("100,0")
    assert forms.MapPointField(required=False).clean("") is None

    widget = MapPointInput()
    widget.value = (9.5, -83.25)
    assert widget.value == "9.500000,-83.250000" and widget.lat_field.value == "9.500000"
    widget.value = None
    assert widget.value == "" and widget.marker_layer.markers == []


async def test_map_tap_sets_point(logged_app):
    import flet_map as fm

    app = logged_app
    await app.goto("/notes")
    await app.click(app.find_one(key="crud_add"))
    location = app.find_one(key="location")
    location._on_tap(fm.MapTapEvent(name="tap", control=location.map, kind=None, local_position=None,
                                    global_position=None, coordinates=fm.MapLatitudeLongitude(10.0, -85.0)))
    assert location.value == "10.000000,-85.000000"
    app.assert_no_errors()


async def test_maps_view_shows_notes_with_location(logged_app, notes):
    notes.create(title="Con ubicación", location="9.9,-84.0")
    app = logged_app
    await app.goto("/maps")
    count = app.find_one(key="maps_count").value
    assert int(count.split()[0]) >= 1
    app.assert_no_errors()
