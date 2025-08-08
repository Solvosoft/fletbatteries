import flet as ft
from components.shared.datatable import FBDataTable

def build_view_customer(page: ft.Page) -> ft.Container:
    data = [
        {"id": 1, "name": "Ana", "last_name": "Gómez", "phone": 88888888, "email": "ana@gmail.com"},
        {"id": 2, "name": "Luis", "last_name": "Rojas", "phone": 55555555, "email": "luis@gmail.com"},
        {"id": 3, "name": "Eva", "last_name": "Zamora", "phone": 66666666, "email": "eva@gmail.com"},
        {"id": 4, "name": "Juan", "last_name": "Perez", "phone": 77777777, "email": "juan@gmail.com"},
        {"id": 5, "name": "Maria", "last_name": "Rodríguez", "phone": 88888888, "email": "maria@gmail.com"},
    ]

    columns_names = [
        {"name": "ID", "type": "filter", "expand": True},
        {"name": "Name", "type": "filter", "expand": True},
        {"name": "Last Name", "type": "text", "expand": True},
        {"name": "Phone", "type": "filter", "expand": True},
        {"name": "Email", "type": "text", "expand": True},
    ]

    datatable = FBDataTable(data, columns_names, title="Customers")

    return ft.Container(
        expand=True,
        content=ft.Column(
            controls=[
                ft.Text("Customer", size=20),
                ft.Divider(),
                ft.Container(
                    content=datatable,
                    expand=True,
                    padding=10,
                    alignment=ft.alignment.center,
                )
            ],
            alignment=ft.alignment.top_center,
        )
    )