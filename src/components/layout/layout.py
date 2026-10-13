import flet as ft
from components.layout.sidebar import Sidebar


class Layout(ft.Row):
    def __init__(self, navbar, page: ft.Page, views: [], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.navbar = navbar
        self.app_page = page
        self.navbar.appbar.leading.on_click = self.toggle_nav_rail
        self.sidebar = Sidebar(self, views)
        self.controls = [self.sidebar, ft.Container()]
        self.expand = True
        self.vertical_alignment = ft.CrossAxisAlignment.START

    def toggle_nav_rail(self, e):
        self.sidebar.visible = not self.sidebar.visible
        self.app_page.update()

    def update_view(self, view):
        # El router hace page.update() después de cambiar la vista
        self.controls[1] = view
