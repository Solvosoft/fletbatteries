import flet as ft
import os
import shutil

from controls.product.product_control import ProductControl
from controls.product.product_form import ProductForm
from components.shared.generic_card import GenericCard
from components.shared.generic_card_crud import GenericCardCRUD

class ProductView:
    def __init__(self, page: ft.Page, forms: []):
        self.page = page
        self.product_control = ProductControl()
        self.products = []
        self.selected_product = None
        self.name_field = ft.TextField(label="Nombre del producto")
        self.code_field = ft.TextField(label="Código del producto")
        self.price_field = ft.TextField(label="Precio", keyboard_type=ft.KeyboardType.NUMBER)
        self.image_display = ft.Text("Ninguna imagen seleccionada")
        self.file_picker = ft.FilePicker(on_result=self.on_image_selected)
        self.page.overlay.append(self.file_picker)
        self.product_to_delete = None
        self.forms = forms

        self.image_picker_controls = ft.Row(
            controls=[
                ft.ElevatedButton(
                    text="Seleccionar Imagen",
                    icon=ft.Icons.IMAGE,
                    on_click=lambda _: self.file_picker.pick_files(
                        allow_multiple=False,
                        allowed_extensions=["jpg", "jpeg", "png"]
                    )
                ),
                self.image_display
            ],
            spacing=10
        )

        self.form = ProductForm(self.name_field, self.code_field, self.image_picker_controls, self.price_field)

        self.dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Agregar nuevo producto"),
            content=ft.Column(
                controls=self.form.get_inputs(),
                tight=True,
                spacing=10
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: self.close_dialog()),
                ft.ElevatedButton("Guardar", on_click=self.submit_product),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self.confirm_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("¿Eliminar producto?"),
            content=ft.Text(f"¿Estás seguro de que deseas eliminar el producto?"),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: self.cancel_delete()),
                ft.TextButton("Eliminar", on_click= self.confirm_delete),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self.page.overlay.append(self.confirm_dialog)
        self.page.overlay.append(self.dialog)

    def on_add_product(self, e):
        self.clear_form()
        self.dialog.title = ft.Text("Agregar nuevo producto")
        self.dialog.open = True
        self.page.update()

    def confirm_delete(self, e):
        product = self.product_to_delete
        if product:
            try:
                self.product_control.delete_product(product.id)
                self.products = [p for p in self.products if p.id != product.id]
                self.product_list_container.controls = self.build_product_cards()
                self.product_list_container.update()
            except Exception as ex:
                print(f"Error al eliminar producto: {ex}")
            finally:
                self.product_to_delete = None

        self.confirm_dialog.open = False
        self.page.dialog = None
        self.page.update()

    def cancel_delete(self):
        self.confirm_dialog.open = False
        self.page.update()

    def on_delete_product(self, product):
        self.product_to_delete = product
        self.page.dialog = self.confirm_dialog
        self.confirm_dialog.open = True
        self.page.update()

    def on_select_product(self, product):
        self.clear_form()
        self.form.id = product.id
        self.form.name_field.value = product.name
        self.form.code_field.value = product.code
        self.form.price_field.value = str(product.price)
        self.form.image_picker_controls.controls[1].value = f"Seleccionada: {product.image}"
        self.form.selected_image_path = os.path.join("src/assets/image", product.image)
        self.dialog.open = True
        self.page.update()
        self.selected_product = product

    def close_dialog(self):
        self.dialog.open = False
        self.page.update()

    def clear_form(self):
        self.form.name_field.value = ""
        self.form.code_field.value = ""
        self.form.price_field.value = ""
        self.form.selected_image_path = ""
        self.image_display.value = "Ninguna imagen seleccionada"
        self.page.update()

    def on_image_selected(self, e: ft.FilePickerResultEvent):
        self.form.on_image_selected(e)
        self.page.update()

    def submit_product(self, e):
        if self.form.validate_form():
            try:
                product = self.form.product
                if product.id == 0:
                    self.products.append(
                        self.product_control.create_product(product.name, product.code, product.price, product.image))
                else:
                    product = self.product_control.update_product(product.id, product.name, product.code, product.price,
                                                                  product.image)
                    self.products = [p for p in self.products if p.id !=  product.id]
                    self.products.append(product)
                self.dialog.open = False
                self.product_list_container.controls = self.build_product_cards()
                self.product_list_container.update()
                self.page.update()
            except Exception as ex:
                print(f"Error al agregar producto view: {ex}")
                self.dialog.title = ft.Text(ex, color=ft.Colors.RED)
                self.page.update()
            try:
                os.makedirs("src/assets/image", exist_ok=True)
                shutil.copy(self.form.selected_image_path, os.path.join("src/assets/image", self.form.image_picker_controls.controls[1].value))
            except Exception as ex:
                print(f"Error al copiar imagen: {ex}")
            self.page.update()
        else:
            self.page.update()

    def build_product_cards(self):
        self.products = self.product_control.get_all_products()
        return [
            GenericCard(
                content=[
                    ft.Image(
                        src=f"/image/{product.image}",
                        fit=ft.ImageFit.COVER,
                        width=300,
                        height=200,
                    ),
                    ft.Divider(color=ft.Colors.GREY_300),
                    ft.Text(product.name, size=16, weight=ft.FontWeight.BOLD),
                    ft.Text(f"${product.price:.2f}", size=14),
                    ft.Text(product.code, size=12, color=ft.Colors.GREY_600),
                ],
                on_edit=lambda e, p=product: self.on_select_product(p),
                on_delete=lambda e, p=product: self.on_delete_product(p),
                height=400,
            )
            for product in self.products
        ]

    def get_products(self):
        return self.product_control.get_all_products()

    def create_product(self, product):
        return self.product_control.create_product(
            product["name"],
            product["code"],
            product["price"],
            product["image"]
        )

    def build_view_product(self) -> ft.Container:

        return GenericCardCRUD(
            page=self.page,
            title="Productos",
            get_method=self.get_products,
            create_method=self.create_product,
            update_method=self.product_control.update_product,
            delete_method=self.product_control.delete_product,
            card_content=lambda item:[
                ft.Image(
                    src=f"/image/{item.image}",
                    fit=ft.ImageFit.COVER,
                    width=300,
                    height=200,
                ),
                ft.Divider(color=ft.Colors.GREY_300),
                ft.Text(item.name, size=16, weight=ft.FontWeight.BOLD),
                ft.Text(f"${item.price:.2f}", size=14),
                ft.Text(item.code, size=12, color=ft.Colors.GREY_600),
            ],
            form_name="ProductForm",
            forms=self.forms,

        ).build_view()
