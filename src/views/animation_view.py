import flet as ft
import flet_rive as fr

def build_view_animation(page: ft.Page) -> ft.Container:

    animation1 = fr.Rive(
            "https://cdn.rive.app/animations/vehicles.riv",
            placeholder=ft.ProgressBar(),
            width=300,
            height=200,
            use_artboard_size=True,
        )

    animation2 = fr.Rive(
        "src/assets/animations/tree-animation.riv",
            placeholder=ft.ProgressBar(),
            width=300,
            height=200,
            use_artboard_size=True,
        )

    return ft.Container(
        expand=True,
        content=ft.Column(
            controls=[
                ft.Text("Animation", size=20),
                ft.Divider(),
                ft.Text("Rive", size=20),
                animation1,
                ft.Divider(),
                ft.Text("Custom", size=20),
                animation2,

            ],
            alignment=ft.alignment.center,
            spacing=10,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        ),
        alignment=ft.alignment.center,
        padding=10,
    )