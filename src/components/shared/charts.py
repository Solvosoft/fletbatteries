import flet as ft
from typing import Any, Dict, List, Optional, Callable

#____________________________________________________
# PieChart
#____________________________________________________

class GenericPieChart(ft.PieChart):
    def __init__(
            self,
            data: [dict],
            tooltip: str | None = None,
            expand: bool = True,
            callback_event: callable = None,
            show_snackbar=False,
            page: ft.Page | None = None,
            snackbar_time=1500,
            *,
            normal_radius: int = 50,
            hover_radius: int = 60,
            sections_space: float = 0,
            center_space_radius: float = 0,
            normal_title_style: ft.TextStyle | None = None,
            hover_title_style: ft.TextStyle | None = None,

    ):

        super().__init__()
        self.values = data
        self.tooltip = tooltip
        self.expand = expand
        self.normal_radius = normal_radius
        self.hover_radius = hover_radius
        self.hover_title_style = hover_title_style or ft.TextStyle(
            size=18,
            color=ft.Colors.WHITE,
            weight=ft.FontWeight.BOLD,
            shadow=ft.BoxShadow(blur_radius=2, color=ft.Colors.BLACK54),
        )
        self.normal_title_style = normal_title_style or ft.TextStyle(
            size=12,
            color=ft.Colors.WHITE,
            weight=ft.FontWeight.BOLD
        )
        self.sections_space = sections_space
        self.center_space_radius = center_space_radius
        self.on_chart_event = self.chart_event or callback_event
        self.sections = self.build_sections()
        self.show_snackbar = show_snackbar
        self._page = page
        self.snackbar_time = snackbar_time

    def build_sections(self):
        sections = []
        colors = self.random_color()

        for i, item in enumerate(self.values):
            if item.get("value", None) is None:
                print(f"Valor no encontrado para {item}")
                continue

            content = ft.PieChartSection(
                value=item.get("value"),
                title=item.get("title", None) or f"{item.get('value')} %",
                color=item.get("color", None) or colors[i],
                radius=item.get("radius", None) or self.normal_radius,
                title_position=item.get("title_position", 0.3),
            )

            badge = item.get("badge", None)

            if badge:
                content.badge = self.section_badge(
                    badge.get("icon"),
                    badge.get("size", 40),
                    badge.get("tooltip", None) or item.get("title", None),
                    border=badge.get("border", None),
                )
                content.badge_position = item.get("badge_position", 1)

            sections.append(
                content
            )

        return sections

    def random_color(self):
        length = len(self.values)
        colors = []

        for i in range(length):
            colors.append(ft.Colors.random(exclude=colors))

        return colors

    def section_badge(self, icon, size, tooltip, border: ft.border = None, bgcolor=None):
        return ft.Container(
            ft.Icon(icon),
            width=size,
            height=size,
            border=border or ft.border.all(1, ft.Colors.BLACK),
            border_radius=size / 2,
            bgcolor=bgcolor or ft.Colors.WHITE,
            tooltip=tooltip,
        )

    def chart_event(self, e: ft.PieChartEvent):
        if not getattr(self, "sections", None):
            return

        idx = e.section_index if isinstance(e.section_index, int) else -1

        for i, section in enumerate(self.sections):
            if i == idx:
                section.radius = self.hover_radius
                section.title_style = self.hover_title_style
            else:
                section.radius = self.normal_radius
                section.title_style = self.normal_title_style


        if self.show_snackbar and self.page and 0 <= idx < len(self.sections):
            title_text = str(self.sections[idx].title or "")
            if title_text:
               snack_bar = ft.SnackBar(ft.Text(title_text), duration=self.snackbar_time)
               self.page.open(snack_bar)
               self.page.update()

        self.update()

    def update_data(self, new_data):
        self.values = new_data
        self.sections = self._build_sections()
        self.update()

