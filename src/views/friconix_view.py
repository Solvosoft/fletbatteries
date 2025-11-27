import flet as ft
from assets.icons.friconix.frx_flet import frx_icon, frx_button


def build_view_friconix(page: ft.Page) -> ft.Container:
    btn = frx_button(
        "Buscar",
        "magnifying-glass-solid",
        icon_size=22,
        icon_color="#ffffff",
        bgcolor="#2563eb",
        button_cls=ft.FilledButton,
        tooltip="Haz clic para buscar",
        style=ft.ButtonStyle(padding=20),
        on_click=lambda e: print("Buscar..."),
    )

    defaults = ft.Row(
        controls=[
            frx_icon("archive"),
            frx_icon("question-mark"),
            frx_icon("circle"),
            frx_icon("gift"),
            frx_icon("octagon"),
            frx_icon("info"),
            frx_icon("label"),
            frx_icon("facebook"),
        ],
        spacing=16,
        wrap=True,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )

    customs = ft.Row(
        controls=[
            frx_icon("user-solid", size=28, color="#2563eb"),
            frx_icon("user-tie-circle", size=28, color="#16a34a"),
            frx_icon("instagram", size=28, color="#eab308"),
            frx_icon("magnifying-glass-solid", size=28, color="#2563eb"),
            frx_icon("check", size=28, color="#16a34a"),
            frx_icon("warning-solid", size=28, color="#eab308"),

            # Solo contorno (sin relleno):
            frx_icon("question-mark", size=32, color="none", stroke="#0ea5e9", stroke_width=60),
        ],
        spacing=16,
        wrap=True,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )

    btn_link = frx_button(
        "Ir a Google",
        "link-solid",
        icon_size=22,
        icon_color="#ffffff",
        bgcolor="#2563eb",
        button_cls=ft.FilledButton,
        tooltip="Haz clic aquí para ir a Google",
        on_click=lambda e: e.page.launch_url("https://www.google.com")
    )

    return ft.Container(
        expand=True,
        content=ft.Column(
            controls=[
                ft.Text("Friconix", size=20),
                ft.Divider(),
                ft.Text("Default icons", size=20),
                ft.Container(
                    content=defaults,
                    expand=True,
                    alignment=ft.alignment.center,
                ),
                ft.Text("Custom icons", size=20),
                ft.Container(
                    content=customs,
                    expand=True,
                    alignment=ft.alignment.center,
                ),
                ft.Text("Button icons", size=20),
                ft.Container(
                    content=btn,
                    expand=False,
                    alignment=ft.alignment.center,
                ),
                ft.Row(
                    controls=[
                        frx_button("Facebook", "facebook", icon_size=28, icon_color="#3b5998", bgcolor="#ffffff",
                                   button_cls=ft.FilledButton,
                                   style=ft.ButtonStyle(padding=20, side=ft.BorderSide(1, "#2563eb"),
                                    shape=ft.RoundedRectangleBorder(radius=8))),
                        frx_button("Instagram", "instagram", icon_size=28, icon_color="#C97034", bgcolor="#ffffff",
                                   button_cls=ft.FilledButton, style=ft.ButtonStyle(padding=20, side=ft.BorderSide(1, "#000000"))),
                        frx_button("Twitter", "twitter", icon_size=28, icon_color="#3434C9", bgcolor="#ffffff",
                                   button_cls=ft.FilledButton, style=ft.ButtonStyle(padding=20, side=ft.BorderSide(1, "#000000"))),
                    ],
                    expand=False,
                    alignment=ft.alignment.center,
                ),
                ft.Text("Buttons with link", size=20),
                ft.Container(
                    content=btn_link,
                    expand=False,
                    alignment=ft.alignment.center,
                ),
            ],
            alignment=ft.alignment.center,
        ),
        alignment=ft.alignment.center,
        padding=10,
    )
