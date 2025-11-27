import flet as ft

class Navbar:
    def __init__(self, page: ft.Page, settings: dict):
        self.page = page
        self.settings = settings
        self.action = None
        self.appbar_items = self.settings.get("items", [])
        self.appbar = ft.AppBar(

            leading=ft.IconButton(icon=ft.Icons.MENU),
            leading_width=100,
            title=self.create_header(),
            center_title=False,
            toolbar_height=75,
            bgcolor=self.settings.get("color_bg"),
            actions=[
                ft.Container(
                    content=ft.PopupMenuButton(
                        items=self.appbar_items
                    ),
                    margin=ft.margin.only(left=50, right=25)
                )
            ],
        )
        self.page.appbar = self.appbar
        self.page.update()

    def create_header(self):
        return ft.Row(
            controls=[
                ft.Image(src=self.settings.get("logo"), width=32, height=32),
                ft.Text(self.settings.get("title"), size=24, color=self.settings.get("color_text")),
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=10,
        )

    def action(self, action):
        self.action = action

