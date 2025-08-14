import flet as ft



def build_view_profile(page: ft.Page) -> ft.Container:


    return ft.Container(
        expand=True,
        content=ft.Column(
            controls=[
                ft.Text("Profile", size=20),

            ],
            alignment=ft.alignment.top_center,
        )
    )