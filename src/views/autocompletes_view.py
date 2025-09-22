import flet as ft
import requests
from components.shared.selects import AutoCompleteSelect, AutoCompleteSelectMultiple
from components.shared.modals import CrudModal
from controls.utils import get_form

API_URL = "http://127.0.0.1:8000/"

def fetch_data(end_point: str, skip=0, limit=10, q: str = ""):
    response = requests.get(
        f"{API_URL}{end_point}",
        params={"skip": skip, "limit": limit, "q": q},
    )
    if response.status_code == 200:
        return response.json()
    return {"results": {}, "pagination": {"more": False}}

def make_loader(end_point: str, default_limit: int):
    def loader(skip: int, limit: int = default_limit, filter_text: str = ""):
        return fetch_data(end_point, skip=skip, limit=limit, q=filter_text)
    return loader

def build_view_autocompletes(page: ft.Page, forms: []) -> ft.Container:
    form = get_form(forms, "PeopleForm")
    form_dialog = CrudModal(page)

    # Callback de selects
    def on_select_change(select_component, selected_values, items):
        print(f"Selected values: {selected_values}")
        print(f"Selected items: {items}")

    for input in form.inputs:
        if input.type == "SelectField" and input.name == "country":
            select = AutoCompleteSelect(
                page,
                data=fetch_data("countries", limit=10),
                label=input.label,
                on_change=on_select_change,
                on_load_more=make_loader("countries", 6),
                on_search_api=make_loader("countries", 6),
            )
            input._select_component = select
            input.widget = select.control

        elif input.type == "SelectMultipleField" and input.name == "people":
            select_multi = AutoCompleteSelectMultiple(
                page,
                data=fetch_data("persons", limit=5),
                label=input.label,
                on_change=on_select_change,
                on_load_more=make_loader("persons", 6),
            )
            input.widget = select_multi.control
            input._select_component = select_multi

        elif input.type == "SelectMultipleField" and input.name == "communities":
            select_multi = AutoCompleteSelectMultiple(
                page,
                data=fetch_data("communities", limit=5),
                label=input.label,
                on_change=on_select_change,
                on_load_more=make_loader("communities", 6),
            )
            input.widget = select_multi.control
            input._select_component = select_multi

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

    return ft.Container(
        content=ft.Column(
            [
                ft.Row(
                    controls=[
                        ft.Text("People group", size=20),
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

"""
    return ft.Container(
        content=ft.Column(
            [
                ft.Text("Autocompletes", size=20),
                select.control,
                select_multiple.control,
            ],
            spacing=20,
            alignment=ft.MainAxisAlignment.START,
            expand=True,
        ),
        alignment=ft.alignment.top_center,
        padding=20,
        expand=True,
    )
"""