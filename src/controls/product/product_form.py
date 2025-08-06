
import flet as ft
import os

from data.models.product import Product

class ProductForm:
    def __init__(self, name_field, code_field, image_picker_controls, price_field):
        self.name_field = name_field
        self.code_field = code_field
        self.image_picker_controls = image_picker_controls
        self.price_field = price_field
        self.selected_image_path = ""
        self.id = 0
        self.product = None

    def get_inputs(self):
        return [self.name_field, self.code_field, self.image_picker_controls, self.price_field]

    def get_selected_image_name(self):
        return os.path.basename(self.selected_image_path) if self.selected_image_path else ""

    def validate_form(self):
        for control in [self.name_field, self.code_field, self.price_field]:
            control.error_text = ""

        name = self.name_field.value.strip()
        code = self.code_field.value.strip()
        image_name = self.get_selected_image_name()
        price = self.price_field.value.strip()

        if not name:
            self.name_field.error_text = "Este campo es obligatorio"
            return False
        if not code:
            self.code_field.error_text = "Este campo es obligatorio"
            return False
        if not image_name:
            self.image_picker_controls.controls[1].value = "Seleccione una imagen"
            self.image_picker_controls.controls[1].color = ft.Colors.RED
            return False
        if not price:
            self.price_field.error_text = "Este campo es obligatorio"
            return False

        try:
            price_value = float(price)
            if price_value < 0:
                self.price_field.error_text = ft.Text("El precio debe ser un número positivo", color=ft.Colors.RED)
        except ValueError:
            self.price_field.error_text = ft.Text("El precio debe ser un número positivo", color=ft.Colors.RED)
            return False
        id = 0
        if self.id != 0:
            id = self.id
        self.product = Product(id=id, code=code, name=name, price=price, image=image_name)
        return True

    def on_image_selected(self, e: ft.FilePickerResultEvent):
        if e.files:
            self.selected_image_path = e.files[0].path
            file_name = os.path.basename(self.selected_image_path)
            self.image_picker_controls.controls[1].value = f"Seleccionada: {file_name}"
            self.image_picker_controls.controls[1].color = ft.Colors.BLACK
        else:
            self.selected_image_path = ""
            self.image_picker_controls.controls[1].value = "Ninguna imagen seleccionada"

