import flet as ft
from assets.fontawesome import fontawesome as fa


def build_view_fontawesome(page: ft.Page) -> ft.Container:

    icon = fa.get_icon("user", color="black", size=30)

    media_item = fa.social_item(name="facebook", link="https://facebook.com", tooltip="Facebook", color="blue", size=45)

    def on_click():
        print("Clicked")

    btn_icon = fa.get_button_icon("vial_virus", color="green", size=30, callback=lambda e: on_click(), height=40, width=80)

    return ft.Container(
        expand=True,
        content=ft.Column(
            controls=[
                ft.Text("Fontawesome", size=20),
                ft.Divider(),
                ft.Text("Icon", size=20),
                ft.Container(
                    content=icon,
                    expand=True,
                    alignment=ft.alignment.center,
                ),
                ft.Text("Media items", size=20),
                ft.Container(
                    content=media_item,
                    expand=True,
                    alignment=ft.alignment.center,
                ),
                ft.Text("Button icons", size=20),
                ft.Container(
                    content=btn_icon,
                    expand=True,
                    alignment=ft.alignment.center,
                ),
            ],
            alignment=ft.alignment.center,
        ),
        alignment=ft.alignment.center,
        padding=10,
    )
