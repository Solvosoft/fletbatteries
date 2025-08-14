import flet as ft
import os
import shutil
from components.shared.inputs.inputs_type import InputType


class Input:
    def __init__(self, page: ft.Page, name: str, type: str, label: str,
                 required: bool, max_length: int,
                 visible_form: bool = True, visible_table: bool = True, active_filter: bool = True,
                 tooltip: str = ""):
        self.page = page
        self.name = name
        self.type = type
        self.label = label
        self.required = required
        self.max_length = max_length
        self.visible_form = visible_form
        self.visible_table = visible_table
        self.file_picker = ft.FilePicker(on_result=self.on_file_picked)
        self.filter = None
        self.widget = None
        self.tooltip = tooltip
        self.active_filter = active_filter
        self.widget = InputType(self.page, self.type, self.label, self.visible_form, self.visible_table,
                                self.file_picker).get_widget()
        if self.type == "CharField" or self.type == "EmailField" or self.type == "IntergerField":
            self.filter = ft.TextField(label=self.name, width=250)

    def on_file_picked(self, e: ft.FilePickerResultEvent):
        if self.type == "ImageField":
            if e.files:
                file_name = os.path.basename(e.files[0].path)
                self.widget.controls[0].data = {"path": e.files[0].path, "name": file_name}
                self.widget.controls[1] = ft.Text(f"Seleccionada: {file_name}")
            else:
                self.widget.controls[1] = ft.Text("Ninguna imagen seleccionada")
                self.widget.controls[0].data = {"path": "", "name": ""}
        self.page.update()

    def on_upload(self):
        if self.type == "ImageField":
            try:
                data = getattr(self.widget.controls[0], "data", None)

                if not isinstance(data, dict) or not data.get("path"):
                    return

                src_path = data["path"]
                dest_path = os.path.join("src/assets/image", data.get("name", ""))

                os.makedirs("src/assets/image", exist_ok=True)

                if os.path.abspath(src_path) != os.path.abspath(dest_path):
                    shutil.copy(src_path, dest_path)

            except Exception as ex:
                print(f"Error al copiar imagen: {ex}")

            self.page.update()

    def set_value(self, value):
        if self.type == "ImageField":
            self.widget.controls[0].data = {"path": "src/assets/image/" + value, "name": value}
            self.widget.controls[1] = ft.Text("Seleccionada: " + value)
        else:
            self.widget.value = value

    def is_valid(self):
        if self.type == "CharField":
            self.widget.error = None
            if self.required and self.widget.value == "":
                self.widget.error = ft.Text("Este campo es requerido", color=ft.Colors.RED)
                return False
            if self.max_length and len(self.widget.value) > self.max_length:
                self.widget.error = ft.Text(f"El valor debe tener menos de {self.max_length} caracteres",
                                            color=ft.Colors.RED)
                return False
        elif self.type == "IntergerField":
            self.widget.error = None
            if self.required and self.widget.value == "":
                self.widget.error = ft.Text("Este campo es requerido", color=ft.Colors.RED)
                return False
            if not self.required and self.widget.value == "":
                return True
            try:
                parsed = int(self.widget.value)
                if parsed < 0:
                    self.widget.error = ft.Text("El valor debe ser mayor o igual a 0", color=ft.Colors.RED)
                    return False
            except ValueError:
                self.widget.error = ft.Text("El valor debe ser un número", color=ft.Colors.RED)
                return False
        elif self.type == "ImageField":
            if self.required and (
                    self.widget.controls[0].data is None or
                    self.widget.controls[0].data.get('path', '') == ''
            ):
                self.widget.controls[1] = ft.Text("Ninguna imagen seleccionada", color=ft.Colors.RED)
                return False
        elif self.type == "EmailField":
            self.widget.error = None
            if self.required and self.widget.value == "":
                self.widget.error = ft.Text("Este campo es requerido", color=ft.Colors.RED)
                return False
            if self.widget.value:
                import re
                patron = r"^[\w\.-]+@[\w\.-]+\.\w+$"
                if not re.match(patron, self.widget.value):
                    self.widget.error = ft.Text("El correo no es válido", color=ft.Colors.RED)
                    return False
        elif self.type == "PasswordField":
            self.widget.error = None
            val = (self.widget.value or "")
            if self.required and val.strip() == "":
                self.widget.error = ft.Text("Este campo es requerido", color=ft.Colors.RED)
                return False
            if val:
                if  len(val) > self.max_length:
                    self.widget.error = ft.Text(f"La contraseña no debe exceder {self.max_length} caracteres",
                                                color=ft.Colors.RED)
                    return False
                if len(val) < 8:
                    self.widget.error = ft.Text("La contraseña debe tener al menos 8 caracteres",
                                                color=ft.Colors.RED)
                    return False
                import re
                if not re.search(r"[A-Za-z]", val) or not re.search(r"\d", val):
                    self.widget.error = ft.Text("La contraseña debe incluir letras y números",
                                                color=ft.Colors.RED)
                    return False
        return True
