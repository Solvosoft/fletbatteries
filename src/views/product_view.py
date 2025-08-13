import flet as ft
import os
import shutil

from controls.product.product_control import ProductControl
from components.shared.generic_card_crud import GenericCardCRUD
from controls.utils import text_with_truncate
from components.shared.modals import CrudModal

class ProductView:
    def __init__(self, page: ft.Page, forms: []):
        self.page = page
        self.product_control = ProductControl()
        self.forms = forms
        self.top_actions = [
            ft.ElevatedButton(
                content=ft.Icon(ft.Icons.ADD),
                on_click=lambda e: self.on_add_item(e),
            )
        ]
        self.form_dialog = CrudModal(self.page)
        self.card_actions = [
            lambda item: ft.ElevatedButton(
                content=ft.Icon(ft.Icons.EDIT),
                on_click=lambda e, it=item: self.on_select_item(it),
            ),
            lambda item: ft.ElevatedButton(
                content=ft.Icon(ft.Icons.DELETE),
                on_click=lambda e, it=item: self.on_delete_item(it),
            ),
        ]
        self.form = None
        for form in self.forms:
            if form.name == "ProductForm":
                self.form = form
        self.crud_view = None
    def get_all_products(self,):
        return self.product_control.get_all_products()

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

    def on_add_item(self, e):
        self.form.clean()
        self.form_dialog.open(
            kind="create",
            title=f"Agregar {self.form.title}",
            content_controls=self.form.get_inputs(),
            on_accept=self.submit,
            success_text="Producto guardado",
            error_text="Error al guardar producto",
            width=600,
        )
        self.page.update()

    def confirm_delete(self, item):
        if item:
            try:
                result = self.delete_product(item)
                self.page.update()
                self.crud_view.reload(self.get_all_products())
                return result
            except Exception as ex:
                print(f"Error al eliminar producto: {ex}")
                return False
        return False

    def on_delete_item(self, item):
        self.form_dialog.open(
            kind="delete",
            title=f"Eliminar {self.form.title}",
            content_controls=[ft.Text("¿Estás seguro de eliminar este registro?")],
            on_accept=lambda: self.confirm_delete(item),
            success_text="Producto eliminado",
            error_text="Error al eliminar producto",
            width=600,
        )
        self.page.update()

    def on_select_item(self, item):

        for field, value in item.items():
            for input in self.form.inputs:
                if input.name == field:
                    input.set_value(value)
        self.form_dialog.open(
            kind="edit",
            title=f"Agregar {self.form.title}",
            content_controls=self.form.get_inputs(),
            on_accept=self.submit,
            success_text="Producto guardado",
            error_text="Error al guardar producto",
            width=600,
        )
        self.page.update()

    def submit(self):
        if self.form.is_valid():
            try:
                item = self.form.get_item()
                print(item)
                if item["id"] == 0 or item["id"] is None:
                    item = self.create_product(item)
                else:
                    item = self.update_product(item)
                self.form.activate_on_upload()
                self.page.update()
                self.crud_view.reload(self.get_all_products())
                return True
            except Exception as ex:
                print(f"Error al agregar producto: {ex}")
                self.form_dialog.title = ft.Text(str(ex), color=ft.Colors.RED)
                self.page.update()
                return False
        self.page.update()
        return False

    def build_view_product(self) -> ft.Container:
        self.crud_view = GenericCardCRUD(
            page=self.page,
            data=self.get_all_products(),
            title="Productos",
            form=self.form,
            card_content=lambda item:[
                ft.Image(
                    src=f"/image/{item['image']}",
                    fit=ft.ImageFit.COVER,
                    width=400,
                    height=300,
                ),
                ft.Divider(color=ft.Colors.GREY_300),
                text_with_truncate(item['name'], size=14, bold=True, max_length=15, max_line=1),
                ft.Text(f"${item['price']:.2f}", size=14),
                ft.Text(item['code'], size=12, color=ft.Colors.GREY_600),
            ],
            card_actions=self.card_actions,
            top_actions=self.top_actions,
            card_width=500,
            card_height=400,

        )
        return self.crud_view.build_view()
