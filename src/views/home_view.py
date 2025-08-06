import flet as ft
from controls.utils import random_image_url
from components.shared.carousel import Carousel

def build_view_home(page: ft.Page) -> ft.Container:
    carousel_images = [
        random_image_url(width=600, height=400),
        random_image_url(width=600, height=400),
        random_image_url(width=600, height=400),
        random_image_url(width=600, height=400),
        random_image_url(width=600, height=400),
    ]

    carousel = Carousel(carousel_images, auto_play=True, interval=5, width=page.width, height=400)
    carousel.start_autoplay(page)

    return ft.Container(
        expand=True,
        content=ft.Column(
            controls=[
                ft.Text("Home", size=20),
                carousel,
            ],
            alignment=ft.alignment.center,
        ),
        alignment=ft.alignment.center,
        padding=10,
    )