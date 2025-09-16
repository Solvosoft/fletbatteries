import flet as ft
import requests
from components.shared.selects import AutoCompleteSelect, AutoCompleteSelectMultiple

API_URL = "http://127.0.0.1:8000/"

def fetch_countries(skip=0, limit=10):
    response = requests.get(API_URL+"countries", params={"skip": skip, "limit": limit})
    if response.status_code == 200:
        return response.json()
    return {"results": {}, "pagination": {"more": False}}

def fetch_people(skip=0, limit=5):
    response = requests.get(API_URL+"persons", params={"skip": skip, "limit": limit})
    if response.status_code == 200:
        return response.json()
    return {"results": {}, "pagination": {"more": False}}

def build_view_autocompletes(page: ft.Page) -> ft.Container:
    countries_data = fetch_countries()
    people_data = fetch_people()

    def on_select_change(self, selected_values, items):
        print(f"Selected values: {selected_values}")
        print(f"Selected items: {items}")

    select = AutoCompleteSelect(
        page,
        countries_data,
        label="Seleccione un país",
        on_change=on_select_change,
    )

    select_multiple = AutoCompleteSelectMultiple(
        page,
        people_data,
        label="Seleccione personas",
        on_change=on_select_change,
    )

    return ft.Container(
        content=ft.Column(
            [
                ft.Text("Autocompletes", size=20),
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