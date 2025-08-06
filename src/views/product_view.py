import flet as ft
import os
import shutil

from controls.product.product_control import ProductControl
from controls.product.product_form import ProductForm


class ProductView:
    def __init__(self, page: ft.Page):
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
        self.page.dialog = None
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
                print(f"Error al agregar producto: {ex}")
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
            ft.Container(
                content=ft.Card(
                    ft.Container(
                        content=ft.Column(
                            controls=[
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
                                ft.Row(
                                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                    controls=[
                                        ft.IconButton(
                                            icon=ft.Icons.EDIT,
                                            tooltip="Editar",
                                            on_click=lambda e, p=product: self.on_select_product(p)
                                        ),
                                        ft.IconButton(
                                            icon=ft.Icons.DELETE,
                                            tooltip="Eliminar",
                                            icon_color=ft.Colors.RED,
                                            on_click=lambda e, p=product: self.on_delete_product(p)
                                        ),
                                    ]
                                )
                            ],
                            spacing=5,
                            alignment=ft.MainAxisAlignment.START,
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER
                        ),
                        padding=10,
                        width=300,
                    )
                ),
                width=320,
                padding=5,
            )
            for product in self.products
        ]

    def build_view_product(self) -> ft.Container:

        self.product_list_container = ft.Column(
            controls=self.build_product_cards(),
            scroll=ft.ScrollMode.AUTO,
            spacing=15,
            wrap=False,
            expand=True,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER
        )

        return ft.Container(
            expand=True,
            bgcolor=ft.Colors.BLUE_GREY_50,
            content=ft.Column(
                spacing=0,
                controls=[
                    ft.Container(
                        bgcolor=ft.Colors.BLUE_GREY_900,
                        padding=ft.Padding(20, 10, 20, 10),
                        content=ft.Row(
                            controls=[
                                ft.Text("Productos", size=22, color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD),
                                ft.Container(expand=True),
                                ft.ElevatedButton(
                                    text="Agregar",
                                    icon=ft.Icons.ADD,
                                    bgcolor=ft.Colors.AMBER,
                                    color=ft.Colors.BLACK,
                                    on_click=self.on_add_product,
                                )
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        )
                    ),
                    ft.Container(
                        expand=True,
                        padding=20,
                        content=self.product_list_container,
                        alignment=ft.alignment.center,
                    )
                ]
            )
        )
