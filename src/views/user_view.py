import flet as ft

def build_view_user(page: ft.Page) -> ft.Container:


    return ft.Container(
        expand=True,
        content=ft.Column(
            controls=[
                ft.Text("Users", size=20),

            ],
            alignment=ft.alignment.top_center,
        )
    )