import flet as ft

from fletbatteries.app import shell_of
from fletbatteries.widgets import color_picker


def build_view_settings(page: ft.Page) -> ft.Container:
    shell = shell_of(page)
    preview = ft.Container(
        width=36,
        height=36,
        bgcolor=page.theme.color_scheme_seed,
        border_radius=8,
        border=ft.Border.all(1, ft.Colors.GREY_400),
    )

    def on_color(color):
        preview.bgcolor = color
        shell.set_theme(color=color)

    def on_mode(e):
        dark = bool(sw.value)
        sw.thumb_icon = ft.Icons.DARK_MODE if dark else ft.Icons.LIGHT_MODE
        shell.set_theme(mode=ft.ThemeMode.DARK if dark else ft.ThemeMode.LIGHT)

    sw = ft.Switch(
        value=page.theme_mode == ft.ThemeMode.DARK,
        thumb_icon=ft.Icons.DARK_MODE if page.theme_mode == ft.ThemeMode.DARK else ft.Icons.LIGHT_MODE,
        on_change=on_mode,
    )
    picker_icon = color_picker(page, callback=on_color)

    return ft.Container(
        expand=True,
        padding=10,
        content=ft.Column(
            controls=[
                ft.Text("Settings", size=20),
                ft.Text("El tema se guarda en la base de datos (fletbatteries.contrib.settings).", size=12),
                ft.Row([preview, picker_icon, sw], alignment=ft.MainAxisAlignment.SPACE_AROUND),
            ],
        ),
    )
