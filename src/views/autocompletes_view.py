import flet as ft
import requests
from components.shared.selects import AutoCompleteSelect, AutoCompleteSelectMultiple

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
    """Returns a call back to manage the pagination"""
    def loader(skip: int, limit: int = default_limit, filter_text: str = ""):
        return fetch_data(end_point, skip=skip, limit=limit, q=filter_text)
    return loader

def build_view_autocompletes(page: ft.Page) -> ft.Container:
    countries_data = fetch_data("countries", limit=10)
    people_data = fetch_data("persons", limit=5)

    def on_select_change(select_component, selected_values, items):
        print(f"Selected values: {selected_values}")
        print(f"Selected items: {items}")

    select = AutoCompleteSelect(
        page,
        countries_data,
        label="Seleccione un país",
        on_change=on_select_change,
        on_load_more=make_loader("countries", 6),
        on_search_api=make_loader("countries", 6),
    )

    select_multiple = AutoCompleteSelectMultiple(
        page,
        people_data,
        label="Seleccione personas",
        on_change=on_select_change,
        on_load_more=make_loader("persons", 6),
    )

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