from typing import Callable, Optional, Sequence

import flet as ft

from fletbatteries.layout.menu import MenuItem
from fletbatteries.utils import safe_update


class Sidebar(ft.Container):
    """Menú lateral con grupos desplegables."""

    def __init__(self, on_navigate: Callable[[str], None], title: Optional[str] = None, width: int = 250):
        self.on_navigate = on_navigate
        self.selected_route: Optional[str] = None
        self.items: list[MenuItem] = []
        self.list = ft.ListView(spacing=2, expand=True)
        header = [ft.Text(title, weight=ft.FontWeight.BOLD)] if title else []
        super().__init__(
            content=ft.Column([*header, self.list], expand=True, spacing=10),
            padding=ft.Padding.all(12),
            width=width,
            key="sidebar",
        )

    def set_items(self, items: Sequence[MenuItem]):
        self.items = list(items)
        self._render()

    def select(self, route: Optional[str]):
        self.selected_route = route
        self._render()

    def _tile(self, item: MenuItem) -> ft.Control:
        if item.children:
            expanded = any(c.route == self.selected_route for c in item.children)
            return ft.ExpansionTile(
                title=ft.Text(item.title),
                leading=ft.Icon(item.icon) if item.icon else None,
                expanded=expanded,
                controls=[self._tile(c) for c in item.children],
                key=f"menu-group-{item.title}",
            )
        return ft.ListTile(
            title=ft.Text(item.title, size=14),
            leading=ft.Icon(item.icon) if item.icon else None,
            selected=item.route == self.selected_route,
            selected_tile_color=ft.Colors.SECONDARY_CONTAINER,
            dense=True,
            shape=ft.RoundedRectangleBorder(radius=8),
            data=item.route,
            key=f"menu-{item.route}",
            on_click=lambda e, r=item.route: self.on_navigate(r),
        )

    def _render(self):
        self.list.controls = [self._tile(i) for i in self.items]
        safe_update(self)

    def toggle(self, e=None):
        self.visible = not self.visible
        safe_update(self)
