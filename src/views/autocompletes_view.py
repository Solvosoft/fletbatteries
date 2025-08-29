import flet as ft
from components.shared.selects import AutoCompleteSelect, AutoCompleteSelectMultiple

def build_view_autocompletes(page: ft.Page) -> ft.Container:
    countries_data = {
        "results": {
            "1": {"id": 1, "text": "Costa Rica", "disabled": False, "selected": False},
            "2": {"id": 2, "text": "Panamá", "disabled": False, "selected": True},
            "3": {"id": 3, "text": "Nicaragua", "disabled": True, "selected": False},
            "4": {"id": 4, "text": "El Salvador", "disabled": False, "selected": False},
            "5": {"id": 5, "text": "Guatemala", "disabled": False, "selected": False},
            "6": {"id": 6, "text": "Honduras", "disabled": False, "selected": False},
            "7": {"id": 7, "text": "Belize", "disabled": False, "selected": False},
        },
        "pagination": {"more": False}
    }

    people_data = {
        "results": {
            "1": {"id": 1, "text": "Persona 1", "disabled": False, "selected": False},
            "2": {"id": 2, "text": "Persona 2", "disabled": False, "selected": True},
            "3": {"id": 3, "text": "Persona 3", "disabled": True, "selected": False},
            "4": {"id": 4, "text": "Persona 4", "disabled": False, "selected": False},
            "5": {"id": 5, "text": "Persona 5", "disabled": False, "selected": False},
            "6": {"id": 6, "text": "Persona 6", "disabled": False, "selected": False},
            "7": {"id": 7, "text": "Persona 7", "disabled": False, "selected": False},
        },
        "pagination": {"more": False}
    }

    def on_select_change(select, values, items):
        print(f"Selected values: {values}")
        print(f"Selected items: {items}")

    select = AutoCompleteSelect(
        page,
        countries_data,
        label="Seleccione un elemento",
        on_change=on_select_change,
        expand=True,
    )

    select_multiple = AutoCompleteSelectMultiple(
        page,
        people_data,
        label="Seleccione elementos",
        on_change=on_select_change,
        expand=True,
    )

    return ft.Container(
        content=ft.Column(
            [
                ft.Text("Autocompletes", size=20, weight="bold"),
                select.control(),
                select_multiple.control(),
            ],
            spacing=20,
            alignment=ft.MainAxisAlignment.START,
            expand=True,
        ),
        alignment=ft.alignment.top_center,
        padding=20,
        expand=True,
    )