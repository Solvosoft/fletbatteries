import flet as ft
from components.shared.color_picker import color_picker
from controls.handler.handler_settings import on_color_change, change_theme_mode

def build_view_settings(page: ft.Page) -> ft.Container:
    # page.theme = ft.Theme(
    #     color_scheme_seed=ft.Colors.WHITE,
    # )

    preview = ft.Container(width=36, height=36,
                           bgcolor=page.theme.color_scheme_seed,
                           border_radius=8,
                           border=ft.border.all(1, ft.Colors.GREY_400),
                           )

    sw = ft.Switch(thumb_icon=ft.Icons.LIGHT_MODE, on_change=lambda e: change_theme_mode(e, page, sw))

    picker_icon = color_picker(page, callback=lambda color: on_color_change(color, page, preview))

    settings = ft.Row(
        [preview, picker_icon, sw],
        alignment=ft.MainAxisAlignment.SPACE_AROUND,
    )


    return ft.Container(
        expand=True,
        content=ft.Column(
            controls=[
                ft.Text("Settings", size=20),
                settings,
            ],
            alignment=ft.alignment.center,
        )
    )