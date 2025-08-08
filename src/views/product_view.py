import flet as ft
import os
import shutil

from controls.product.product_control import ProductControl
from components.shared.generic_card_crud import GenericCardCRUD
from controls.utils import text_with_truncate

class ProductView:
    def __init__(self, page: ft.Page, forms: []):
        self.page = page
        self.product_control = ProductControl()
        self.forms = forms

    def get_products(self, page_number, page_size):
        return self.product_control.get_products_paginated(page_number, page_size)

    def get_product_by_id(self, id):
        return self.product_control.get_product_by_id(id)

    def create_product(self, product):
        return self.product_control.create_product(
            product["name"],
            product["code"],
            product["price"],
            product["image"]
        )

    def update_product(self, product):
        return self.product_control.update_product(
            product["id"],
            product["name"],
            product["code"],
            product["price"],
            product["image"]
        )

    def delete_product(self, product):
        return self.product_control.delete_product(product["id"])

    def build_view_product(self) -> ft.Container:

        return GenericCardCRUD(
            page=self.page,
            title="Productos",
            get_method=self.get_products,
            get_method_by_id=self.get_product_by_id,
            create_method=self.create_product,
            update_method=self.update_product,
            delete_method=self.delete_product,
            card_content=lambda item:[
                ft.Image(
                    src=f"/image/{item['image']}",
                    fit=ft.ImageFit.COVER,
                    width=300,
                    height=200,
                ),
                ft.Divider(color=ft.Colors.GREY_300),
                text_with_truncate(item['name'], size=14, bold=True, max_length=15, max_line=1),
                # ft.Text(item.name, size=16, weight=ft.FontWeight.BOLD),
                ft.Text(f"${item['price']:.2f}", size=14),
                ft.Text(item['code'], size=12, color=ft.Colors.GREY_600),
            ],
            form_name="ProductForm",
            forms=self.forms,
            card_width=500,
            card_height=400,

        ).build_view()
