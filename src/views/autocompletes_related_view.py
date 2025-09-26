import flet as ft
from components.shared.modals import CrudModal
from controls.utils import get_form
from components.shared.autocompletes_related import RelationalSelectGroup

def build_view_autocompletes_related(page: ft.Page, forms: []) -> ft.Container:
    form = get_form(forms, "RelationalForm")
    form_dialog = CrudModal(page)

    # ----------------- utilidades internas -----------------
    def _normalize_items(selected_items):
        if not selected_items:
            return []
        if isinstance(selected_items, dict):
            return [selected_items]
        if isinstance(selected_items, list):
            return selected_items
        return [selected_items]

    def _texts_from_items(selected_items):
        items = _normalize_items(selected_items)
        return [it.get("text", "") for it in items if isinstance(it, dict)]

    # ----------------- data functions -----------------
    def get_a(_, __):
        return {
            "results": {
                "1": {"id": 1, "text": "A1"},
                "2": {"id": 2, "text": "A2"},
            },
            "pagination": {"more": False},
        }

    def get_b(selected_ids, selected_items_from_a):
        texts_a = _texts_from_items(selected_items_from_a)
        if not texts_a:
            return {"results": {}, "pagination": {"more": False}}
        tag = ", ".join(texts_a)
        return {
            "results": {
                "11": {"id": 11, "text": f"B1 {tag}"},
                "12": {"id": 12, "text": f"B2 {tag}"},
            },
            "pagination": {"more": False},
        }

    def get_c(selected_ids, selected_items_from_b):
        texts_b = _texts_from_items(selected_items_from_b)
        if not texts_b:
            return {"results": {}, "pagination": {"more": False}}
        cadena = ", ".join(texts_b)
        return {
            "results": {
                "21": {"id": 21, "text": f"C1 {cadena}"},
                "22": {"id": 22, "text": f"C2 {cadena}"},
            },
            "pagination": {"more": False},
        }

    # ----------------- relations -----------------
    relations = [
        {"label": "Seleccione A", "type": "single", "data_fn": get_a},
        {"label": "Seleccione B", "type": "multiple", "data_fn": get_b},
        {"label": "Seleccione C", "type": "single", "data_fn": get_c},
    ]

    # ----------------- asignar RelationalSelectGroup al input -----------------
    for input in form.inputs:
        if input.type == "RelationalSelectGroupField" and input.name == "related_selects":
            relational_group = RelationalSelectGroup(page, relations)
            input._select_component = relational_group  # referencia interna opcional
            input.widget = relational_group            # importante: esto hace que se vea en el form

    # ----------------- submit -----------------
    def submit():
        if form.is_valid():
            try:
                item = form.get_item()
                print("Guardado:", item)
                page.update()
                return True
            except Exception as ex:
                print(f"Error al guardar: {ex}")
                form_dialog.title = ft.Text(str(ex), color=ft.Colors.RED)
                page.update()
                return False
        page.update()
        return False

    def on_add_item(e):
        form.clean()
        form_dialog.open(
            kind="create",
            title=f"Agregar {form.title}",
            content_controls=form.get_inputs(),
            on_accept=submit,
            success_text="Guardado con éxito",
            error_text="Error al guardar",
            width=600,
        )
        page.update()

    # ----------------- retornar Container -----------------
    return ft.Container(
        content=ft.Column(
            [
                ft.Row(
                    controls=[
                        ft.Text("Relational Selects", size=20),
                        ft.ElevatedButton("Add", on_click=on_add_item),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                )
            ],
            spacing=20,
        ),
        alignment=ft.alignment.top_center,
        padding=20,
        expand=True,
    )