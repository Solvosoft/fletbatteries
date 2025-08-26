import flet as ft
from components.shared.calendar import Calendar

def build_view_calendar(page):
    return ft.Container(
        content=Calendar(),
        expand=True,
    )

if __name__ == "__main__":
    ft.app(target=build_view_calendar)
