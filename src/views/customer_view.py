import flet as ft
from components.shared.datatable import init_datatable

def build_view_customer(page: ft.Page) -> ft.Container:


    return ft.Container(
        expand=True,
        content=ft.Column(
            controls=[
                ft.Text("Customer", size=20),
                init_datatable(),
            ],
            alignment=ft.alignment.top_center,
        )
    )