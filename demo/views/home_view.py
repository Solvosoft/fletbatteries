import flet as ft

from fletbatteries.auth import get_user
from fletbatteries.contrib.help import HelpButton
from fletbatteries.contrib.notifications import create_notification
from fletbatteries.app import shell_of
from fletbatteries.widgets.elements import BoxTileElement, StatsCountList, StatsElement

from components.shared.carousel import Carousel
from controls.utils import random_image_url
from data.manager.customer_manager import CustomerManager
from data.manager.person_group_manager import PersonGroupManager
from data.manager.product_manager import ProductManager
from data.manager.user_manager import UserManager


def build_view_home(page: ft.Page) -> ft.Container:
    carousel_images = [random_image_url(width=600, height=400) for _ in range(5)]
    carousel = Carousel(carousel_images, auto_play=True, interval=5, width=page.width, height=300)
    carousel.start_autoplay(page)

    stats = StatsCountList([
        StatsElement("Clientes", CustomerManager().count(), icon=ft.Icons.SUPERVISED_USER_CIRCLE,
                     trend="+4% desde ayer", trend_up=True, on_click=lambda e: page.navigate("/customers")),
        StatsElement("Productos", ProductManager().count(), icon=ft.Icons.LOCAL_MALL, color=ft.Colors.TEAL),
        StatsElement("Usuarios", UserManager().count(), icon=ft.Icons.PERSON, color=ft.Colors.ORANGE,
                     trend="-2% esta semana", trend_up=False),
        BoxTileElement("Grupos", PersonGroupManager().count(), "Grupos de personas", icon=ft.Icons.GROUPS,
                       color=ft.Colors.PURPLE),
    ])

    def notify(e):
        user = get_user(page)
        create_notification(user.id if user else None, "Notificación de prueba desde el inicio", level="success",
                            link="/customers")
        shell_of(page).bell.refresh()

    return ft.Container(
        expand=True,
        padding=10,
        content=ft.Column(
            controls=[
                ft.Row([ft.Text("Home", size=20), HelpButton("home", title="Inicio")]),
                stats,
                ft.Button(content="Crear notificación", icon=ft.Icons.NOTIFICATIONS_ACTIVE, on_click=notify,
                          key="create_notification"),
                carousel,
            ],
            scroll=ft.ScrollMode.AUTO,
        ),
    )
