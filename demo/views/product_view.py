import flet as ft

from fletbatteries.crud import CRUDView

from app_forms import ProductForm
from data.manager.product_manager import ProductManager


def product_card(item: dict) -> ft.Control:
    return ft.Column(
        [
            ft.Image(src=f"image/{item['image']}", height=140, fit=ft.BoxFit.COVER, border_radius=6)
            if item.get("image") else ft.Container(height=140),
            ft.Text(item["name"], size=16, weight=ft.FontWeight.BOLD),
            ft.Text(f"Código: {item['code']}", size=12),
            ft.Text(f"₡ {item['price']:,.2f}", size=14, color=ft.Colors.PRIMARY),
        ],
        spacing=4,
        tight=True,
    )


class ProductCRUD(CRUDView):
    title = "Products"
    name = "producto"
    manager = ProductManager()
    form_class = ProductForm
    mode = "cards"
    card = staticmethod(product_card)
    page_size = 8


def build_view_product(page: ft.Page) -> ft.Control:
    return ProductCRUD(page).build()
