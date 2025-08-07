import flet as ft


class Footer(ft.Container):
    def __init__(self):
        super().__init__(
            height=48,
            bgcolor=ft.Colors.BLUE_GREY_900,
            content=ft.Row(
                [
                    ft.Image(src="src/assets/image/icon.png", width=32, height=32),
                    ft.Text(
                        "© 2025 Solvo",
                        color=ft.Colors.WHITE,
                        size=12,
                    ),
                    ft.Container(expand=True),
                    ft.IconButton(
                        icon=ft.Icons.ADD_LINK,
                        tooltip="Solvo",
                        url="https://solvosoft.com/es/",
                        icon_color=ft.Colors.WHITE,
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.padding.symmetric(horizontal=20),
        )
