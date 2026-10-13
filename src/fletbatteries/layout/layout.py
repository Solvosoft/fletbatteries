import flet as ft

from fletbatteries.layout.breadcrumbs import Breadcrumbs
from fletbatteries.layout.sidebar import Sidebar


class Layout(ft.Row):
    """Sidebar a la izquierda y contenido (breadcrumbs + vista) a la derecha."""

    def __init__(self, sidebar: Sidebar, breadcrumbs: Breadcrumbs):
        self.sidebar = sidebar
        self.breadcrumbs = breadcrumbs
        self.view_container = ft.Container(expand=True)
        self.content_column = ft.Column(
            [ft.Container(breadcrumbs, padding=ft.Padding.only(left=10, top=4)), self.view_container],
            expand=True,
            spacing=0,
        )
        super().__init__(controls=[sidebar, self.content_column], expand=True,
                         vertical_alignment=ft.CrossAxisAlignment.START)

    def update_view(self, view: ft.Control):
        self.view_container.content = view

    @property
    def view(self):
        return self.view_container.content
