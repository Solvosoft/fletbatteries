import flet as ft
import json
import os
import shutil

from components.shared.inputs import Input

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

    def get_filters(self):
        filters = []
        for input in self.inputs:
            if input.filter:
                filters.append(input.filter)
        return filters

    def clear_filters(self):
        print("clear_filters")
        for input in self.inputs:
            if input.filter:
                input.filter.controls[1].value = ""

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
            if input.widget_flet == "TextField":
                input.widget.value = ""
            if input.widget_flet == "IntergerField":
                input.widget.value = ""
            if input.widget_flet == "ImageField":
                input.widget.controls[0].data = {"path": "", "name": ""}
                input.widget.controls[1].value = "Ninguna imagen seleccionada"

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

class GenerateForms:
    def __init__(self, page: ft.Page):
        self.page = page
        self.forms = []
        with open("src/components/shared/form_example.json") as f:
            self.data = json.load(f)
        self.generate_forms()

    def generate_forms(self):
        for form in self.data["forms"]:
            input_type = ""
            inputs = []

            for input in form["inputs"]:
                if input["type"] == "CharField":
                    input_type = "TextField"
                elif input["type"] == "IntergerField":
                    input_type = "IntergerField"
                elif input["type"] == "ImageField":
                   input_type = "ImageField"
                inputs.append(Input(self.page, input["name"], input["type"], input["label"], input_type,
                                    input["required"], 0, input_type,
                                    input.get("visible_form", True), input.get("visible_table", True),
                                    input.get("filter", False), input.get("tooltip", "")))

            self.forms.append(Form(form["title"], form["name"], inputs))