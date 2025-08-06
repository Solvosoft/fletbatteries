import flet as ft
from components.layout.sidebar import Sidebar


class Layout(ft.Row):
    def __init__(self, navbar, page: ft.Page, settings: dict, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.navbar = navbar
        self.page = page
        self.navbar.appbar.leading.on_click = self.toggle_nav_rail
        self.sidebar = Sidebar(self)
        self.controls = [self.sidebar, ft.Container()]
        self.expand = True
        self.alignment = ft.alignment.top_center

    @property
    def active_view(self):
        return self._active_view

    @active_view.setter
    def active_view(self, view):
        self._active_view = view
        self.update()

    def toggle_nav_rail(self, e):
        self.sidebar.visible = not self.sidebar.visible
        self.page.update()

    def update_view(self, view):
        self.controls[1]= view
        self.update()

