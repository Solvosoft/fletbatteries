import flet as ft
import json
import os
import shutil
from uuid import uuid4

from components.shared.inputs.inputs import Input


class Form:
    def __init__(self, title: str, name: str, inputs: []):
        self.title = title
        self.name = name
        self.inputs = inputs
        self.id = uuid4().hex

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

    def get_filters(self):
        filters = []
        for input in self.inputs:
            if input.filter:
                filters.append(input.filter)
        return filters

    def clear_filters(self):
        for input in self.inputs:
            if input.filter:
                input.filter.value = ""

    def activate_on_upload(self):
        for input in self.inputs:
            if input.type == "ImageField":
                input.on_upload()

    def activate_on_filter(self, function):
        for input in self.inputs:
            if input.filter:
                input.filter.on_change = (
                    lambda e, _input=input: function(_input.filter.value, _input.name)
                )

    def clean(self):
        for input in self.inputs:
            if input.type == "ImageField":
                input.widget.controls[0].data = {"path": "", "name": ""}
                input.widget.controls[1].value = "Ninguna imagen seleccionada"
            elif input.type == "DateField" or input.type == "DateTimeField":
                input.widget.controls[0].value = ""
            else:
                input.widget.value = ""

    def get_item(self):
        item = {}
        for input in self.inputs:
            if input.type == "IntergerField":
                item[input.name] = int(input.widget.value) if input.widget.value else None
            elif input.type == "ImageField":
                item[input.name] = input.widget.controls[0].data["name"]
            elif input.type == "DateField" or input.type == "DateTimeField":
                item[input.name] = input.widget.controls[0].value
            elif input.type == "SelectField":
                item[input.name] = (
                    input._select_component.value if hasattr(input, "_select_component") else None
                )
            elif input.type == "SelectMultipleField":
                item[input.name] = (
                    input._select_component.value if hasattr(input, "_select_component") else []
                )
            else:
                item[input.name] = input.widget.value
        return item

    from uuid import uuid4


class GenerateForms:
    def __init__(self, page: ft.Page):
        self.page = page
        self.forms = []
        self.data = None
        with open("src/components/shared/form_example.json") as f:
            self.data = json.load(f)

    def generate_forms(self):
        if self.data is None:
            with open("src/components/shared/form_example.json") as f:
                self.data = json.load(f)
        for form in self.data["forms"]:
            inputs = []
            for input in form["inputs"]:
                inputs.append(Input(self.page, input["name"], input["type"], input["label"],
                                    input["required"], input.get("max_length", 255), input.get("visible_form", True),
                                    input.get("visible_table", True),
                                    input.get("filter", False), input.get("tooltip", "")))

            self.forms.append(Form(form["title"], form["name"], inputs))
        return self.forms

    def clone(self, name_form):
        for form in self.data["forms"]:
            if form["name"] == name_form:
                inputs = []
                for input in form["inputs"]:
                    inputs.append(Input(self.page, input["name"], input["type"], input["label"],
                                        input["required"], input.get("max_length", 255),
                                        input.get("visible_form", True),
                                        input.get("visible_table", True),
                                        input.get("filter", False), input.get("tooltip", ""),
                                        input.get("min_date", ""), input.get("max_date", "")
                                        )
                                  )
                return Form(form["title"], form["name"], inputs)
