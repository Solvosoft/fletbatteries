import flet as ft
from components.shared.charts import GenericPieChart, GenericBarChart, GenericLineChart


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
            alignment=ft.alignment.center,
            expand=True,
            scroll=ft.ScrollMode.AUTO,
        ),
        alignment=ft.alignment.center,
        padding=10,
    )
