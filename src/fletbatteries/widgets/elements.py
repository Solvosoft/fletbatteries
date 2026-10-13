"""Elementos de dashboard: contadores y tiles (equivalentes a `StatsElement` / `BoxTileElement`)."""

from typing import Optional, Sequence

import flet as ft


class StatsElement(ft.Container):
    """Contador con ícono, título y una línea de tendencia opcional (p. ej. "+4% desde ayer")."""

    def __init__(self, title: str, count, icon=ft.Icons.INSIGHTS, trend: Optional[str] = None,
                 trend_up: Optional[bool] = None, color=ft.Colors.PRIMARY, width: int = 220, on_click=None,
                 **kwargs):
        trend_color = None
        trend_icon = None
        if trend_up is not None:
            trend_color = ft.Colors.GREEN_700 if trend_up else ft.Colors.RED_600
            trend_icon = ft.Icons.ARROW_UPWARD if trend_up else ft.Icons.ARROW_DOWNWARD
        self.count_text = ft.Text(str(count), size=30, weight=ft.FontWeight.BOLD)
        trend_row = ft.Row(
            [ft.Icon(trend_icon, size=14, color=trend_color) if trend_icon else ft.Container(),
             ft.Text(trend or "", size=12, color=trend_color)],
            spacing=2,
            visible=bool(trend),
        )
        super().__init__(
            width=width,
            padding=14,
            border_radius=10,
            bgcolor=ft.Colors.SURFACE_CONTAINER_LOW,
            border=ft.Border.only(left=ft.BorderSide(4, color)),
            on_click=on_click,
            content=ft.Column(
                [
                    ft.Row([ft.Icon(icon, color=color, size=18), ft.Text(title, size=13, color=ft.Colors.OUTLINE)],
                           spacing=6),
                    self.count_text,
                    trend_row,
                ],
                spacing=4,
                tight=True,
            ),
            **kwargs,
        )

    def set_count(self, value):
        self.count_text.value = str(value)
        from fletbatteries.utils import safe_update

        safe_update(self.count_text)


class BoxTileElement(ft.Container):
    """Tile con ícono grande a la izquierda, número y descripción."""

    def __init__(self, title: str, count, description: str = "", icon=ft.Icons.DASHBOARD,
                 color=ft.Colors.PRIMARY, width: int = 280, on_click=None, **kwargs):
        super().__init__(
            width=width,
            padding=14,
            border_radius=10,
            border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
            on_click=on_click,
            content=ft.Row(
                [
                    ft.Container(ft.Icon(icon, color=ft.Colors.WHITE, size=28), bgcolor=color, border_radius=30,
                                 width=56, height=56, alignment=ft.Alignment.CENTER),
                    ft.Column(
                        [ft.Text(str(count), size=24, weight=ft.FontWeight.BOLD),
                         ft.Text(title, weight=ft.FontWeight.W_500),
                         ft.Text(description, size=12, color=ft.Colors.OUTLINE, visible=bool(description))],
                        spacing=0,
                        tight=True,
                        expand=True,
                    ),
                ],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            **kwargs,
        )


def StatsCountList(elements: Sequence[ft.Control]) -> ft.Row:
    """Fila de contadores que se acomoda en varias líneas."""
    return ft.Row(list(elements), wrap=True, spacing=12, run_spacing=12)


BoxStatsCountList = StatsCountList
