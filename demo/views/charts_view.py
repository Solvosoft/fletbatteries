import flet as ft
from components.shared.charts import GenericPieChart, GenericBarChart, GenericLineChart
from fletbatteries.widgets import charts as fbc

from data.manager.note_manager import NoteManager

SALES = {
    "labels": ["Ene", "Feb", "Mar", "Abr", "May", "Jun"],
    "datasets": [
        {"label": "Tienda", "data": [12, 19, 8, 15, 22, 17]},
        {"label": "En línea", "data": [7, 11, 13, 9, 14, 20]},
    ],
}


def declarative_charts():
    """Gráficos de fletbatteries a partir de datos con el formato de Chart.js."""
    return ft.Column(
        [
            ft.Text("Gráficos declarativos (fletbatteries)", size=18, weight=ft.FontWeight.BOLD),
            ft.ResponsiveRow(
                [
                    ft.Container(fbc.BarChart(SALES, title="Barras"), col={"md": 6}),
                    ft.Container(fbc.StackedBarChart(SALES, title="Barras apiladas"), col={"md": 6}),
                    ft.Container(fbc.LineChart(SALES, title="Líneas"), col={"md": 6}),
                    ft.Container(fbc.HorizontalBarChart(SALES, title="Barras horizontales"), col={"md": 6}),
                    ft.Container(fbc.DoughnutChart(
                        {"labels": SALES["labels"], "datasets": [SALES["datasets"][0]]}, title="Dona"), col={"md": 6}),
                    ft.Container(fbc.ScatterChart(
                        {"labels": [], "datasets": [{"label": "Puntos", "data": [(1, 2), (2, 5), (3, 3), (4, 8)]}]},
                        title="Dispersión"), col={"md": 6}),
                    ft.Container(fbc.PieChart(source=fbc.count_by(NoteManager(), "category", label="Notas"),
                                              title="Notas por categoría (desde la BD)", key="notes_by_category"),
                                 col={"md": 6}),
                ]
            ),
        ]
    )


def build_view_charts(page: ft.Page) -> ft.Container:
    data1 = [
        {"value": 40, "color": ft.Colors.BLUE, "title_position": 0.5, "label": "Costa Rica"},
        {"value": 30, "color": ft.Colors.YELLOW, "title_position": 0.5, "label": "Panama"},
        {"value": 15, "color": ft.Colors.PURPLE, "title_position": 0.5, "label": "Salvador"},
        {"value": 15, "color": ft.Colors.GREEN, "title_position": 0.5, "label": "Guatemala"},
    ]

    data2 = [
        {"value": 40, "title_position": 0.5, "badge": {"icon": ft.Icons.AC_UNIT, "size": 40}},
        {"value": 30, "title_position": 0.5, "badge": {"icon": ft.Icons.ACCESS_ALARM, "size": 40}},
        {"value": 15, "title_position": 0.5, "badge": {"icon": ft.Icons.APPLE, "size": 40}},
        {"value": 15, "title_position": 0.5,
         "badge": {"icon": ft.Icons.PEDAL_BIKE, "size": 40}},
    ]

    pie_chart_1 = GenericPieChart(
        data1,
        expand=True,
        sections_space=0,
        center_space_radius=50,
        normal_radius=100,
        hover_radius=120,
    )

    pie_chart_2 = GenericPieChart(
        data1,
        expand=True,
        sections_space=0,
        center_space_radius=0,
        normal_radius=100,
        hover_radius=120,
        page=page,
        show_snackbar=True,
    )

    pie_chart_3 = GenericPieChart(
        data2,
        expand=True,
        sections_space=0,
        center_space_radius=0,
        normal_radius=100,
        hover_radius=120,
    )

    pie_chart_4 = GenericPieChart(
        data1,
        expand=True,
        sections_space=0,
        center_space_radius=0,
        normal_radius=100,
        hover_radius=120,
    ).get_with_labels()

    # BarChart
    labels_bottom = ["Apple", "Blueberry", "Cherry", "Orange"]
    data_bar = [
        {"value": 40, "label": "Apple", "color": ft.Colors.GREEN},
        {"value": 100, "label": "Blueberry", "color": ft.Colors.BLUE},
        {"value": 30, "label": "Cherry", "color": ft.Colors.RED},
        {"value": 60, "label": "Orange", "color": ft.Colors.ORANGE},
    ]
    bar_chart_1 = GenericBarChart(
        title="Fruit supply",
        labels_bottom=labels_bottom,
        data=data_bar,
        expand=True,
        interactive=True,
        max_y=110,
        height=500,
    )

    # LineChart
    data_line = [
        {"points": [{"x": 0, "y": 40}, {"x": 10, "y": 80}, {"x": 40, "y": 30}, {"x": 80, "y": 80}], "color": ft.Colors.RED},
        {"points": [{"x": 0, "y": 20}, {"x": 10, "y": 50}, {"x": 20, "y": 30}, {"x": 80, "y": 60}], "color": ft.Colors.BLUE},
        {"points": [{"x": 0, "y": 10}, {"x": 10, "y": 30}, {"x": 40, "y": 20}, {"x": 60, "y": 60}], "color": ft.Colors.GREEN},
        {"points": [{"x": 0, "y": 25}, {"x": 10, "y": 20}, {"x": 30, "y": 30}, {"x": 70, "y": 70}], "color": ft.Colors.ORANGE},
    ]
    labels_left = [{"value": 20, "label": "20K"}, {"value": 40, "label": "40K"}, {"value": 60, "label": "60K"}, {"value": 80, "label": "80K"}, {"value": 100, "label": "100K"}]
    labels_bottom = [{"value": 0, "label": "2020"}, {"value": 20, "label": "2022"}, {"value": 40, "label": "2024"}, {"value": 60, "label": "2026"}, {"value": 80, "label": "2028"}, {"value": 100, "label": "2030"}]
    line_chart_1 = GenericLineChart(
        data_line,
        expand=True,
        interactive=True,
        max_y=110, # always add a one more point
        max_x=110, # always add a one more point
        height=500,
        labels_left=labels_left,
        labels_bottom=labels_bottom,
    )

    return ft.Container(
        expand=True,
        content=ft.Column(
            controls=[
                ft.Text("Charts", size=20),
                ft.Divider(),
                declarative_charts(),
                ft.Divider(),
                ft.Text("PieChart", size=14),
                pie_chart_1,
                pie_chart_2,
                pie_chart_3,
                pie_chart_4,
                ft.Text("BarChart", size=14),
                ft.Container(height=10, expand=True),# divider
                bar_chart_1,
                ft.Text("LineChart", size=14),
                ft.Container(height=10, expand=True),  # divider
                line_chart_1,
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            expand=True,
            scroll=ft.ScrollMode.AUTO,
        ),
        alignment=ft.Alignment.CENTER,
        padding=10,
    )
