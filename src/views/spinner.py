import flet as ft
from components.shared.rotating_boxes_loader import RotatingBoxesLoader

def build_view_spinner(page: ft.Page) -> ft.Container:

    loader = RotatingBoxesLoader(
        size=100,
        color_a_border="#e9665a",
        color_b_border="#7df6dd",
        color_a_bg=None,
        color_b_bg="#1f262f",
        text="Loading...",
        text_size=14,
        text_color="white",
        step_seconds=0.7,
        border_width=2.5,
    )

    return ft.Container(
        expand=True,
        content=ft.Column(
            controls=[
                ft.Text("Spinner", size=20),
                ft.Divider(),
                ft.Container(
                    content=loader,
                    expand=True,
                    alignment=ft.alignment.center,
                ),
            ],
            alignment=ft.alignment.center,
        ),
        alignment=ft.alignment.center,
        padding=10,
    )