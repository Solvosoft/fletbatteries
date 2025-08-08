import flet as ft
import json
import os
import shutil

class Form:
    def __init__(self, title: str, name: str, inputs: []):
        self.title = title
        self.name = name
        self.inputs = inputs

    def is_valid(self):
        for input in self.inputs:
            if not input.is_valid():
                return False
        return True

    def get_inputs(self):
        widgets = []
        for input in self.inputs:
                widgets.append(input.widget)
        return widgets

    def activate_on_upload(self):
        for input in self.inputs:
            if input.type == "ImageField":
                input.on_upload()

    def clean(self):
        for input in self.inputs:
            if input.widget_flet == "TextField":
                input.widget.value = ""
            if input.widget_flet == "IntergerField":
                input.widget.value = ""
            if input.widget_flet == "ImageField":
                input.widget.controls[0].data = {"path": "", "name": ""}
                input.widget.controls[1] = ft.Text("Ninguna imagen seleccionada")

    def get_item(self):
        item = {}
        for input in self.inputs:
            if input.widget_flet == "TextField":
                item[input.name] = input.widget.value
            elif input.widget_flet == "IntergerField":
                item[input.name] = int(input.widget.value) if input.widget.value else None
            elif input.widget_flet == "ImageField":
                item[input.name] = input.widget.controls[0].data["name"]
        return item

class Input:
    def __init__(self, page: ft.Page, name: str, type: str, label: str, widget: str, required: bool, max_length: int, widget_flet: str,  visible: bool = True ):
        self.page = page
        self.name = name
        self.type = type
        self.label = label
        self.widget = widget
        self.required = required
        self.max_length = max_length
        self.widget_flet = widget_flet
        self.visible = visible
        self.file_picker = ft.FilePicker(on_result=self.on_file_picked)
        self.widget = None
        if self.widget_flet == "TextField":
            self.widget = ft.TextField(
                label=self.label,
                visible=self.visible,
            )
        elif self.widget_flet == "IntergerField":
            self.widget = ft.TextField(
                label=self.label,
                keyboard_type=ft.KeyboardType.NUMBER,
                visible=self.visible,
            )
        elif self.widget_flet == "ImageField":
            self.page.overlay.append(self.file_picker)
            self.widget = ft.Row(
                controls=[
                    ft.ElevatedButton(
                        text="Seleccionar Imagen",
                        icon=ft.Icons.IMAGE,
                        on_click=lambda _: self.file_picker.pick_files(
                            allow_multiple=False,
                            allowed_extensions=["jpg", "jpeg", "png"]
                        )
                    ),
                    ft.Text("Ninguna imagen seleccionada")
                ],
                spacing=10
            )

    def on_file_picked(self, e: ft.FilePickerResultEvent):
        if self.widget_flet == "ImageField":
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
                os.makedirs("src/assets/image", exist_ok=True)
                src_path = self.widget.controls[0].data["path"]
                dest_path = os.path.join("src/assets/image", self.widget.controls[0].data["name"])
                if os.path.abspath(src_path) != os.path.abspath(dest_path):
                    shutil.copy(src_path, dest_path)
            except Exception as ex:
                print(f"Error al copiar imagen: {ex}")
            self.page.update()

    def set_value(self, value):
        if self.widget_flet == "TextField" or self.widget_flet == "IntergerField":
            self.widget.value = value
        elif self.widget_flet == "ImageField":
            self.widget.controls[0].data = {"path": "src/assets/image/"+value, "name": value}
            self.widget.controls[1] = ft.Text("Seleccionada: " + value)

    def is_valid(self):
        if self.widget_flet == "TextField":
            self.widget.error = None
            if self.required and self.widget.value == "":
                self.widget.error = ft.Text("Este campo es requerido", color=ft.Colors.RED)
                return False
            if self.max_length and len(self.widget.value) > self.max_length:
                self.widget.error = ft.Text(f"El valor debe tener menos de {self.max_length} caracteres", color=ft.Colors.RED)
                return False
        elif self.widget_flet == "IntergerField":
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
        elif self.widget_flet == "ImageField":
            if self.required and self.widget.controls[0].data["path"] == "" or self.widget.controls[0].data is None:
                self.widget.controls[1] = ft.Text("Ninguna imagen seleccionada", color=ft.Colors.RED)
                return False
        return True

class GenerateForms:
    def __init__(self, page: ft.Page):
        self.page = page
        self.forms = []
        with open("src/components/shared/form_example.json") as f:
            self.data = json.load(f)
        self.generate_forms()

    def generate_forms(self):
        for form in self.data["forms"]:
            inputs = []
            for input in form["inputs"]:
                if input["type"] == "CharField":
                    inputs.append(Input(self.page, input["name"], input["type"], input["label"], "TextInput",
                                        input["required"], input["max_length"], "TextField",
                                        input.get("visible", True)))
                elif input["type"] == "IntergerField":
                    inputs.append(Input(self.page, input["name"], input["type"], input["label"], "IntergerField",
                                        input["required"], 0, "IntergerField",
                                        input.get("visible", True)))
                elif input["type"] == "ImageField":
                    inputs.append(Input(self.page, input["name"], input["type"], input["label"], "ImageField",
                                        input["required"], 0, "ImageField",
                                        input.get("visible", True)))
            self.forms.append(Form(form["title"], form["name"], inputs))