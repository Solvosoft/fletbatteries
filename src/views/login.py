import flet as ft


def form_login(page: ft.Page):
    return ft.Container(
        expand=False,
        content=ft.Card(
            shadow_color=ft.Colors.ON_SURFACE_VARIANT,
            content=ft.Container(
                ft.Column(
                    controls=[
                        ft.TextField(label="Username", icon=ft.Icons.PERSON),
                        ft.TextField(label="Password", icon=ft.Icons.PASSWORD, password=True),
                        ft.ElevatedButton("Login", on_click=lambda e: page.go("/")),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                padding=10,
            ),
        ),
        alignment=ft.alignment.center,
        width=450,
        height=300,
    )


def build_view_login(page: ft.Page) -> ft.Container:
    return ft.Container(
        expand=True,
        padding=10,
        content=ft.Column(
            controls=[
                ft.Container(
                  ft.Image(
                    src="image/icon.png",
                  ),
                    width=150,
                    height=150,
                ),
                ft.Text("Login",size=20),
                form_login(page),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        alignment=ft.alignment.center,
    )
