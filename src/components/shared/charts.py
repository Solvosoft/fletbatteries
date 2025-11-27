import flet as ft
from typing import Any, Dict, List, Optional, Callable


# ____________________________________________________
# PieChart
# ____________________________________________________

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
        self.page = page
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

    def get_labels_column(self):
        labels = []

        for i, section in enumerate(self.sections):
            if self.values[i].get("label", None) is not None:
                labels.append(
                    ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.SQUARE, color=section.color),
                            ft.Text(self.values[i].get("label")),
                        ],
                        alignment=ft.alignment.center,
                        expand=True,
                        spacing=5,
                    )
                )

        return ft.Column(
            controls=labels,
            alignment=ft.alignment.center,
            expand=True,
            scroll=ft.ScrollMode.AUTO,
        )

    def get_with_labels(self):

        return ft.Row(
            controls=[
                self,
                self.get_labels_column(),
            ],
            alignment=ft.alignment.center,
            expand=True,
            spacing=10,
        )


# ____________________________________________________
# BarChart
# ____________________________________________________

class GenericBarChart(ft.BarChart):
    def __init__(
            self,
            *,
            grid_lines: bool = True,
            tooltip_bgcolor: ft.Colors | None = None,
            max_y: int | None = 100,
            interactive: bool = True,
            expand: bool = True,
            labels_bottom: [str] = None,
            labels_size: int = 50,
            title: str | None = None,
            border: ft.Border | None = None,
            data: [dict] = None,
            bar_width: int = 40,
            title_size: int = 40,
            width: int | None = None,
            height: int | None = None,
    ):
        super().__init__()
        self.labels_bottom = labels_bottom
        self.grid_lines = grid_lines
        self.add_grid_lines()
        self.tooltip_bgcolor = tooltip_bgcolor or ft.Colors.with_opacity(0.5, ft.Colors.GREY_300)
        self.max_y = max_y
        self.interactive = interactive
        self.expand = expand
        self.labels_size = labels_size
        self.title = title
        self.title_size = title_size
        self.bar_width = bar_width
        self.border = border or ft.border.all(1, ft.Colors.GREY_400)
        self.values = data
        self.width = width
        self.height = height

        # build components
        self.add_title()
        self.add_grid_lines()
        self.add_labels_bottom()
        self.add_bar_groups()

    def add_title(self):
        if not self.title:
            return

        self.left_axis = ft.ChartAxis(
            labels_size=self.labels_size,
            title=ft.Text(self.title, weight=ft.FontWeight.BOLD),
            title_size=self.title_size,
        )

    def add_grid_lines(self):
        if not self.grid_lines:
            return

        self.horizontal_grid_lines = ft.ChartGridLines(
            color=ft.Colors.GREY_300, width=1, dash_pattern=[3, 3]
        )

    def add_labels_bottom(self):
        if not self.labels_bottom:
            return

        self.bottom_axis = ft.ChartAxis(
            labels=self.build_bottom_axis(),
            labels_size=self.labels_size,
        )

    def build_bottom_axis(self):
        labels = []

        for i, label in enumerate(self.labels_bottom):
            labels.append(
                ft.ChartAxisLabel(
                    value=i, label=ft.Container(ft.Text(label), padding=10)
                )
            )

        return labels

    def add_bar_groups(self):
        if not self.values:
            return

        self.bar_groups = self.build_bar_groups()

    def build_bar_groups(self):
        bar_groups = []
        colors = self.random_color()

        for i, item in enumerate(self.values):
            bar = ft.BarChartGroup(
                x=i,
                bar_rods=[
                    ft.BarChartRod(
                        from_y=0,
                        to_y=item.get("value", 0),
                        width=self.bar_width,
                        color=item.get("color", None) or colors[i],
                        tooltip=item.get("tooltip", None),
                        border_radius=0,
                    )
                ],
            )
            bar_groups.append(bar)

        return bar_groups

    def random_color(self):
        length = len(self.values)
        colors = []

        for i in range(length):
            colors.append(ft.Colors.random(exclude=colors))

        return colors

    def update_data(self, new_data):
        self.values = new_data
        self.bar_groups = self._build_bar_groups()
        self.update()


# ____________________________________________________
# LineChart
# ____________________________________________________

class GenericLineChart(ft.LineChart):
    def __init__(
            self,
            data: [dict],
            tooltip_bgcolor: ft.Colors | None = None,
            expand: bool = True,
            grid_lines_h: bool = True,
            grid_lines_v: bool = True,
            title: str | None = None,
            title_size: int = 30,
            min_y: int = 0,
            min_x: int = 0,
            max_y: int = 100,
            max_x: int = 100,
            labels_bottom: [str] = None,
            labels_left: [str] = None,
            labels_size: int = 80,
            width: int | None = None,
            height: int | None = None,
            curved: bool = False,
            border: ft.Border | None = None,
            line_width: int = 2,
            interactive: bool = True,
    ):
        super().__init__()
        self.tooltip_bgcolor = tooltip_bgcolor or ft.Colors.with_opacity(0.5, ft.Colors.GREY_300)
        self.values = data
        self.expand = expand
        self.grid_lines_h = grid_lines_h
        self.grid_lines_v = grid_lines_v
        self.title = title
        self.title_size = title_size
        self.min_y = min_y
        self.min_x = min_x
        self.max_y = max_y
        self.max_x = max_x
        self.labels_bottom = labels_bottom
        self.labels_left = labels_left
        self.labels_size = labels_size
        self.curved = curved
        self.line_width = line_width
        self.border = border or ft.border.all(1, ft.Colors.GREY_400)
        self.width = width
        self.height = height
        self.interactive = interactive

        # build components
        self.add_title()
        self.add_grid_lines()
        self.add_labels_bottom()
        self.add_labels_left()
        self.add_line_groups()

    def random_color(self):
        length = len(self.values)
        colors = []

        for i in range(length):
            colors.append(ft.Colors.random(exclude=colors))

        return colors

    def add_title(self):
        if not self.title:
            return

        self.top_axis = ft.ChartAxis(
            labels_size=self.labels_size,
            title=ft.Text(self.title, weight=ft.FontWeight.BOLD),
            title_size=self.title_size,
        )

    def add_grid_lines(self):
        if self.grid_lines_h:
            self.horizontal_grid_lines = ft.ChartGridLines(
                dash_pattern=[3, 3], color=ft.Colors.with_opacity(0.2, ft.Colors.ON_SURFACE), width=1
            )

        if self.grid_lines_v:
            self.vertical_grid_lines = ft.ChartGridLines(
                dash_pattern=[3, 3], color=ft.Colors.with_opacity(0.2, ft.Colors.ON_SURFACE), width=1
            )

    def add_labels_bottom(self):
        if not self.labels_bottom:
            return

        self.bottom_axis = ft.ChartAxis(
            labels=self.build_labels_axis(self.labels_bottom, "x"),
            labels_size=self.labels_size,
        )

    def add_labels_left(self):
        if not self.labels_left:
            return

        self.left_axis = ft.ChartAxis(
            labels=self.build_labels_axis(self.labels_left, "y"),
            labels_size=self.labels_size,
        )

    def build_labels_axis(self, data, axis):
        labels = []

        for  item in data:
            if item.get("value", None) is None or item.get("label", None) is None:
                continue

            labels.append(
                ft.ChartAxisLabel(
                    value=item.get("value"), label=ft.Container(ft.Text(item.get("label")), padding=10)
                )
            )

        return labels

    def add_line_groups(self):
        if not self.values:
            return

        self.data_series = self.build_line_points()

    def build_line_points(self):
        colors = self.random_color()
        line_groups = []

        for i, item in enumerate(self.values):
            if item.get("points", None) is None:
                print("Points no found.")
                continue

            line = ft.LineChartData(
                data_points=self.build_points_item(item.get("points", None)),
                stroke_width=self.line_width,
                color=item.get("color", None) or colors[i],
                curved=self.curved,
                stroke_cap_round=True,
            )

            line_groups.append(line)

        return line_groups

    def build_points_item(self, points):

        if not points:
            return

        points_item = []

        for point in points:
            points_item.append(
                ft.LineChartDataPoint(
                    x=point.get("x", 0),
                    y=point.get("y", 0),
                    tooltip=point.get("tooltip", None),
                )
            )

        return points_item

    def update_data(self, new_data):
        self.values = new_data
        self.data_series = self._build_line_points()
        self.update()