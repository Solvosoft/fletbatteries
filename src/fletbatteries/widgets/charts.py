"""
Gráficos declarativos (equivalentes a `BaseChartGetter` + Chart.js de djgentelella).

Los datos usan el formato de Chart.js:

    {"labels": ["Ene", "Feb"], "datasets": [{"label": "Ventas", "data": [10, 20], "color": "#1E88E5"}]}

    BarChart(data)                    # o BarChart(source=fn) para recargar con .refresh()
    PieChart(count_by(CustomerManager(), "city"))

Tipos: BarChart, StackedBarChart, HorizontalBarChart, LineChart, PieChart,
DoughnutChart y ScatterChart (en este los datos son pares `(x, y)`).
Requiere el extra `fletbatteries[charts]` (flet-charts), salvo HorizontalBarChart.
"""

from typing import Callable, Optional

import flet as ft
import sqlalchemy as sa

from fletbatteries.utils import safe_update

PALETTE = ["#1E88E5", "#43A047", "#FB8C00", "#8E24AA", "#E53935", "#00ACC1", "#FDD835", "#6D4C41", "#3949AB",
           "#D81B60"]


def color_for(dataset: dict, index: int) -> str:
    return dataset.get("color") or PALETTE[index % len(PALETTE)]


def count_by(manager, column: str, value: Optional[str] = None, agg: str = "count", label: Optional[str] = None,
             filters: Optional[dict] = None) -> Callable[[], dict]:
    """
    Fuente de datos agrupada por `column`: cuenta registros o suma/promedia `value`.
    Devuelve una función para usar como `source=` de un gráfico.
    """

    def load() -> dict:
        col = getattr(manager.model, column)
        if agg == "count":
            measure = sa.func.count()
        else:
            measure = getattr(sa.func, agg)(getattr(manager.model, value))
        base = manager.apply_filters(manager.base_query(), filters or {}).subquery()
        stmt = sa.select(base.c[col.key], measure).group_by(base.c[col.key]).order_by(base.c[col.key])
        with manager.session() as s:
            rows = s.execute(stmt).all()
        return {
            "labels": ["—" if k is None else str(k) for k, _v in rows],
            "datasets": [{"label": label or (value or column), "data": [float(v or 0) for _k, v in rows]}],
        }

    return load


class Chart(ft.Container):
    def __init__(self, data: Optional[dict] = None, source: Optional[Callable[[], dict]] = None,
                 title: Optional[str] = None, height: int = 300, legend: bool = True, **kwargs):
        kwargs.setdefault("padding", 10)
        super().__init__(**kwargs)
        self.source = source
        self.chart_data = data or (source() if source else {"labels": [], "datasets": []})
        self.title = title
        self.chart_height = height
        self.show_legend = legend
        self.content = self._build()

    def refresh(self):
        if self.source:
            self.chart_data = self.source()
        self.content = self._build()
        safe_update(self)

    def set_data(self, data: dict):
        self.chart_data = data
        self.content = self._build()
        safe_update(self)

    def _legend_items(self) -> list[tuple[str, str]]:
        return [(d.get("label", ""), color_for(d, i)) for i, d in enumerate(self.chart_data.get("datasets", []))]

    def _legend(self) -> ft.Control:
        return ft.Row(
            [ft.Row([ft.Container(width=12, height=12, border_radius=6, bgcolor=c), ft.Text(t, size=12)], spacing=4,
                    tight=True) for t, c in self._legend_items()],
            wrap=True,
            spacing=12,
        )

    def _build(self) -> ft.Control:
        controls = []
        if self.title:
            controls.append(ft.Text(self.title, size=16, weight=ft.FontWeight.BOLD))
        controls.append(ft.Container(self.build_chart(self.chart_data), height=self.chart_height))
        if self.show_legend:
            controls.append(self._legend())
        return ft.Column(controls, spacing=8, tight=True)

    def build_chart(self, data: dict) -> ft.Control:
        raise NotImplementedError

    @staticmethod
    def _max(data: dict, stacked: bool = False) -> float:
        datasets = data.get("datasets", [])
        if not datasets:
            return 1
        if stacked:
            sums = [sum(d["data"][i] for d in datasets if i < len(d["data"])) for i in range(len(data["labels"]))]
            return max(sums or [1]) or 1
        return max((max(d["data"] or [0]) for d in datasets), default=1) or 1


def nice_max(value: float) -> float:
    """Redondea hacia arriba a 1, 2, 2.5, 5 o 10 por la potencia de 10 (para el eje Y)."""
    import math

    if value <= 0:
        return 1
    exp = 10 ** math.floor(math.log10(value))
    for step in (1, 2, 2.5, 5, 10):
        if value <= step * exp:
            return step * exp
    return 10 * exp


def _bottom_axis(labels):
    import flet_charts as fch

    return fch.ChartAxis(
        labels=[fch.ChartAxisLabel(value=i, label=ft.Text(str(label), size=11)) for i, label in enumerate(labels)],
        label_size=32,
    )


class BarChart(Chart):
    stacked = False

    def build_chart(self, data):
        import flet_charts as fch

        datasets = data.get("datasets", [])
        groups = []
        for i, _label in enumerate(data.get("labels", [])):
            if self.stacked:
                total = 0
                items = []
                for j, d in enumerate(datasets):
                    value = d["data"][i] if i < len(d["data"]) else 0
                    items.append(fch.BarChartRodStackItem(from_y=total, to_y=total + value, color=color_for(d, j)))
                    total += value
                rods = [fch.BarChartRod(from_y=0, to_y=total, stack_items=items, border_radius=2)]
            else:
                rods = [fch.BarChartRod(from_y=0, to_y=d["data"][i] if i < len(d["data"]) else 0,
                                        color=color_for(d, j), border_radius=2)
                        for j, d in enumerate(datasets)]
            groups.append(fch.BarChartGroup(x=i, rods=rods))
        return fch.BarChart(
            groups=groups,
            max_y=nice_max(self._max(data, self.stacked) * 1.05),
            bottom_axis=_bottom_axis(data.get("labels", [])),
            left_axis=fch.ChartAxis(label_size=40),
            horizontal_grid_lines=fch.ChartGridLines(color=ft.Colors.OUTLINE_VARIANT, width=1),
            interactive=True,
            expand=True,
        )


class StackedBarChart(BarChart):
    stacked = True


class HorizontalBarChart(Chart):
    """Barras horizontales dibujadas con contenedores (no requiere flet-charts)."""

    def build_chart(self, data):
        maximum = self._max(data)
        rows = []
        for i, label in enumerate(data.get("labels", [])):
            bars = []
            for j, d in enumerate(data.get("datasets", [])):
                value = d["data"][i] if i < len(d["data"]) else 0
                bars.append(ft.Row([
                    ft.Container(bgcolor=color_for(d, j), height=14, border_radius=3,
                                 expand=max(1, int(1000 * value / maximum)), tooltip=f"{d.get('label', '')}: {value}"),
                    ft.Container(expand=max(1, 1000 - int(1000 * value / maximum))),
                    ft.Text(f"{value:g}", size=11, width=50),
                ], spacing=4))
            rows.append(ft.Row([ft.Text(str(label), width=120, size=12), ft.Column(bars, spacing=2, expand=True)],
                               vertical_alignment=ft.CrossAxisAlignment.CENTER))
        return ft.Column(rows, spacing=8, scroll=ft.ScrollMode.AUTO)


class LineChart(Chart):
    curved = True

    def build_chart(self, data):
        import flet_charts as fch

        series = [
            fch.LineChartData(
                points=[fch.LineChartDataPoint(x=i, y=v) for i, v in enumerate(d["data"])],
                color=color_for(d, j),
                stroke_width=3,
                curved=self.curved,
                rounded_stroke_cap=True,
            )
            for j, d in enumerate(data.get("datasets", []))
        ]
        return fch.LineChart(
            data_series=series,
            min_y=0,
            max_y=nice_max(self._max(data) * 1.05),
            min_x=0,
            max_x=max(len(data.get("labels", [])) - 1, 1),
            bottom_axis=_bottom_axis(data.get("labels", [])),
            left_axis=fch.ChartAxis(label_size=40),
            horizontal_grid_lines=fch.ChartGridLines(color=ft.Colors.OUTLINE_VARIANT, width=1),
            interactive=True,
            expand=True,
        )


class PieChart(Chart):
    center_space_radius = 0

    def _legend_items(self):
        labels = self.chart_data.get("labels", [])
        dataset = (self.chart_data.get("datasets") or [{}])[0]
        colors = dataset.get("colors") or []
        return [(str(label), colors[i] if i < len(colors) else PALETTE[i % len(PALETTE)])
                for i, label in enumerate(labels)]

    def build_chart(self, data):
        import flet_charts as fch

        dataset = (data.get("datasets") or [{"data": []}])[0]
        total = sum(dataset["data"]) or 1
        colors = [c for _l, c in self._legend_items()]
        sections = [
            fch.PieChartSection(
                value=v,
                color=colors[i],
                title=f"{100 * v / total:.0f}%",
                title_style=ft.TextStyle(color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD, size=12),
                radius=100,
            )
            for i, v in enumerate(dataset["data"])
        ]
        return fch.PieChart(sections=sections, center_space_radius=self.center_space_radius, sections_space=1,
                            expand=True)


class DoughnutChart(PieChart):
    center_space_radius = 50


class ScatterChart(Chart):
    def build_chart(self, data):
        import flet_charts as fch

        spots = []
        xs, ys = [0], [0]
        for j, d in enumerate(data.get("datasets", [])):
            for x, y in d["data"]:
                xs.append(x)
                ys.append(y)
                spots.append(fch.ScatterChartSpot(x=x, y=y, color=color_for(d, j), radius=6))
        return fch.ScatterChart(spots=spots, min_x=min(xs), max_x=max(xs) * 1.1 or 1, min_y=min(ys),
                                max_y=max(ys) * 1.1 or 1, expand=True,
                                left_axis=fch.ChartAxis(label_size=40), bottom_axis=fch.ChartAxis(label_size=30))
