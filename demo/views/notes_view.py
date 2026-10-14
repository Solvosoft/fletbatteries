import flet as ft

from fletbatteries import forms
from fletbatteries.crud import ACTIONS, CRUDView
from fletbatteries.data import SQLAlchemySource
from fletbatteries.widgets.datatable import Column, color_swatch, yes_no
from fletbatteries.widgets.maps import MapView, parse_point

from data.manager.note_manager import NoteManager

CATEGORIES = [("trabajo", "Trabajo"), ("personal", "Personal"), ("ideas", "Ideas")]


class NoteForm(forms.Form):
    title = "Notas"
    render_type = "grid"
    grid_representation = [
        [["title"], ["category"], ["color"]],
        [["content"]],
        [["location"]],
        [["pinned"]],
    ]

    title = forms.CharField(label="Título", max_length=120)
    category = forms.ChoiceField(label="Categoría", choices=CATEGORIES, required=False)
    color = forms.ColorField(label="Color", required=False)
    content = forms.MarkdownField(label="Contenido", required=False, list_display=False)
    location = forms.MapPointField(label="Ubicación", required=False, list_display=False)
    pinned = forms.BooleanField(label="Fijada")


class NoteCRUD(CRUDView):
    title = "Notas"
    name = "nota"
    manager = NoteManager()
    form_class = NoteForm
    list_fields = ["title", "category", Column("color", render=color_swatch), Column("pinned", render=yes_no)]
    filter_fields = ["title", "category"]
    route = "/notes"
    # Funciones del CRUD: duplicar, acciones masivas, exportar e importar CSV
    actions = ACTIONS + ("clone",)
    bulk_delete = True
    export = True
    importable = True
    import_key_field = "title"


def notes_badge(page) -> int:
    """Cantidad de notas fijadas (se muestra como badge en el menú)."""
    return NoteManager().count(pinned=True)


def build_view_notes(page: ft.Page) -> ft.Control:
    return NoteCRUD(page).build()


def build_view_maps(page: ft.Page) -> ft.Control:
    """Mapa de solo lectura con las notas que tienen ubicación."""
    notes = SQLAlchemySource(NoteManager()).all(location__isnull=False)
    points = []
    for n in notes:
        point = parse_point(n["location"])
        if point:
            points.append({"lat": point[0], "lng": point[1], "title": n["title"], "color": n["color"] or ft.Colors.RED})
    return ft.Container(
        padding=10,
        expand=True,
        content=ft.Column([
            ft.Text("Mapa de notas", size=20),
            ft.Text(f"{len(points)} notas con ubicación", key="maps_count"),
            MapView(points, height=480),
        ]),
    )
