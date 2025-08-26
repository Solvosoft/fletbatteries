import flet as ft
from components.shared.selects import SimpleSelect

def build_view_autocompletes(page: ft.Page) -> ft.Container:
    data = {
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

    def on_select_change(select, value, item):
        print(f"Selected: {value}, Item: {item}")

    select = SimpleSelect( page,
        data,
        label="Seleccione un elemento",
        on_change=on_select_change,
        expand=True,
    )

    return ft.Container(
        content=ft.Column(
            [
                ft.Text("Autocompletes", size=20, weight="bold"),
                ft.Container(
                    content=select.control(),
                    expand=True,
                ),
            ],
            spacing=20,
            alignment=ft.MainAxisAlignment.START,
            expand=True,
        ),
        alignment=ft.alignment.top_center,
        padding=20,
        expand=True,
    )
