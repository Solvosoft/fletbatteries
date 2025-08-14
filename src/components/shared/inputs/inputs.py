import flet as ft
import os
import shutil
from components.shared.inputs.inputs_type import InputType
from datetime import datetime, timedelta


class Input:
    def __init__(self, page: ft.Page, name: str, type: str, label: str,
                 required: bool, max_length: int,
                 visible_form: bool = True, visible_table: bool = True, active_filter: bool = True,
                 tooltip: str = "", min_date: str = "", max_date: str = ""):
        self.page = page
        self.name = name
        self.type = type
        self.label = label
        self.required = required
        self.max_length = max_length
        self.visible_form = visible_form
        self.visible_table = visible_table
        self.min_date = min_date
        self.max_date = max_date
        self.picker = None
        if self.type == "ImageField":
            self.picker = ft.FilePicker(on_result=self.on_file_picked)
        elif self.type == "DateField" or self.type == "DateTimeField":
            self.picker = ft.DatePicker(on_change=self.on_date_picked)
        self.filter = None
        self.widget = None
        self.tooltip = tooltip
        self.active_filter = active_filter
        self.widget = InputType(self.page, self.type, self.label, self.visible_form, self.visible_table,
                                self.picker).get_widget()
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

    def on_date_picked(self, e):
        value = e.control.value
        if hasattr(value, "strftime"):
            if self.type == "DateField":
                self.widget.controls[0].value = value.strftime("%d-%m-%Y")
            elif self.type == "DateTimeField":
                now = datetime.now().time()
                combined = datetime.combine(value, now)
                self.widget.controls[0].value = combined.strftime("%d-%m-%Y %H:%M:%S")
        else:
            self.widget.controls[0].value = str(value)

        self.widget.controls[0].update()

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
        elif self.type == "DateField" or self.type == "DateTimeField":
            self.widget.controls[0].value = value
        else:
            self.widget.value = value

    def parse_relative_date(self, code: str, is_min: bool) -> datetime:
        today = datetime.today()
        if not code:
            return None
        unit = code[0].lower()
        try:
            value = int(code[1:])
        except ValueError:
            return None
        if unit == "d":
            if is_min:
                return today - timedelta(days=value)
            else:
                return today + timedelta(days=value)
        elif unit == "m":
            if is_min:
                return today - relativedelta(months=value)
            else:
                return today + relativedelta(months=value)
        elif unit == "y":
            if is_min:
                return today - relativedelta(years=value)
            else:
                return today + relativedelta(years=value)
        return None

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
                if len(val) > self.max_length:
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
        elif self.type == "DateField":
            self.widget.error = None
            value = self.widget.controls[0].value
            if value == "":
                self.widget.controls[0].error = ft.Text("Este campo es requerido", color=ft.Colors.RED)
                return False
            if value:
                try:
                    selected_date = datetime.strptime(value, "%d-%m-%Y")
                except ValueError as ex:
                    print(f"Error al parsear fecha: {ex}")
                    self.widget.controls[0].error = ft.Text("La fecha debe tener el formato dd-mm-aaaa",
                                                            color=ft.Colors.RED)
                    return False
                if self.min_date:
                    min_date = self.parse_relative_date(self.min_date, True)
                    if isinstance(min_date, datetime):
                        min_date = min_date.date()
                    if isinstance(selected_date, datetime):
                        selected_date = selected_date.date()
                    if min_date and selected_date < min_date:
                        self.widget.controls[0].error = ft.Text(f"La fecha no puede ser menor a {min_date.date()}",
                                                                color=ft.Colors.RED)
                        return False
                if self.max_date:
                    max_date = self.parse_relative_date(self.max_date, False)
                    if isinstance(max_date, datetime):
                        max_date = max_date.date()
                    if isinstance(selected_date, datetime):
                        selected_date = selected_date.date()
                    if max_date and selected_date > max_date:
                        self.widget.controls[0].error = ft.Text(f"La fecha no puede ser mayor a {max_date.date()}",
                                                                color=ft.Colors.RED)
                        return False
        elif self.type == "DateTimeField":
            print("Entrando a DateTimeField")
            self.widget.error = None
            value = self.widget.controls[0].value
            if value == "":
                self.widget.controls[0].error = ft.Text("Este campo es requerido", color=ft.Colors.RED)
                return False
            if value:
                try:
                    selected_date = datetime.strptime(value, "%d-%m-%Y %H:%M:%S")
                except ValueError as ex:
                    print(f"Error al parsear fecha: {ex}")
                    self.widget.controls[0].error = ft.Text("La fecha y hora debe tener el formato dd-mm-aaaa hh:mm:ss",
                                                            color=ft.Colors.RED)
                    return False
                try:
                    print("Entrando a las validaciones de rango")
                    if self.min_date:
                        min_date = self.parse_relative_date(self.min_date, True)
                        if isinstance(min_date, datetime):
                            min_date = min_date.date()
                        if isinstance(selected_date, datetime):
                            selected_date = selected_date.date()
                        if min_date and selected_date < min_date:
                            self.widget.controls[0].error = ft.Text(
                                f"La fecha y hora no puede ser menor a {min_date}", color=ft.Colors.RED)
                            return False
                    if self.max_date:
                        max_date = self.parse_relative_date(self.max_date, False)
                        if isinstance(max_date, datetime):
                            max_date = max_date.date()
                        if isinstance(selected_date, datetime):
                            selected_date = selected_date.date()
                        if max_date and selected_date > max_date:
                            self.widget.controls[0].error = ft.Text(
                                f"La fecha y hora no puede ser mayor a {max_date}", color=ft.Colors.RED)
                            return False
                except ValueError as ex:
                    print(f"Error al parsear fecha: {ex}")
                    return False
        return True
