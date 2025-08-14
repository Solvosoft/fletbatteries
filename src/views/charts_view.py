import flet as ft
from components.shared.charts import GenericPieChart


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
            ],
            alignment=ft.alignment.center,
            expand=True,
            scroll=ft.ScrollMode.AUTO,
        ),
        alignment=ft.alignment.center,
        padding=10,
    )
