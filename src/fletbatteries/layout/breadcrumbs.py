from typing import Callable, Optional, Sequence

import flet as ft

from fletbatteries.utils import safe_update


class Breadcrumbs(ft.Row):
    """Ruta de navegación: Inicio › Clientes › Detalle."""

    def __init__(self, on_navigate: Callable[[str], None]):
        super().__init__(spacing=2, key="breadcrumbs", wrap=True)
        self.on_navigate = on_navigate
        self.items: list[tuple[str, Optional[str]]] = []

    def set_items(self, items: Sequence[tuple[str, Optional[str]]]):
        self.items = list(items)
        controls = []
        for i, (title, route) in enumerate(self.items):
            last = i == len(self.items) - 1
            if i:
                controls.append(ft.Icon(ft.Icons.CHEVRON_RIGHT, size=16, color=ft.Colors.OUTLINE))
            if route and not last:
                controls.append(ft.TextButton(title, on_click=lambda e, r=route: self.on_navigate(r)))
            else:
                controls.append(ft.Text(title, weight=ft.FontWeight.BOLD if last else None))
        self.controls = controls
        self.visible = len(self.items) > 1
        safe_update(self)
