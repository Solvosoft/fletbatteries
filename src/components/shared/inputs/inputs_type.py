import sys

import flet as ft
from ..selects import AutoCompleteSelect, AutoCompleteSelectMultiple
from ..autocompletes_related import RelationalSelectGroup

class InputType:
    def __init__(self, page, type, label, visible_form, visible_table, picker, extra_config=None):
        self.page = page
        self.type = type
        self.label = label
        self.visible_form = visible_form
        self.visible_table = visible_table
        self.picker = picker
        self.extra_config = extra_config or {}

    def get_widget(self):
        widget = None
        if self.type == "CharField":
            widget = ft.TextField(
                label=self.label,
                visible=self.visible_form,
            )
        elif self.type == "IntergerField":
            widget = ft.TextField(
                label=self.label,
                keyboard_type=ft.KeyboardType.NUMBER,
                visible=self.visible_form,
            )
        elif self.type == "ImageField":
            self.page.overlay.append(self.picker)
            widget = ft.Row(
                controls=[
                    ft.ElevatedButton(
                        text="Seleccionar Imagen",
                        icon=ft.Icons.IMAGE,
                        on_click=lambda _: self.picker.pick_files(
                            allow_multiple=False,
                            allowed_extensions=["jpg", "jpeg", "png"]
                        )
                    ),
                    ft.Text("Ninguna imagen seleccionada")
                ],
                spacing=10
            )
        elif self.type == "EmailField":
            widget = ft.TextField(
                label=self.label,
                visible=self.visible_form,
                keyboard_type=ft.KeyboardType.EMAIL,
            )
        elif self.type == "PasswordField":
            widget = ft.TextField(
                label=self.label,
                password=True,
                can_reveal_password=True,
            )
        elif self.type == "DateField":
            widget = ft.Row(
                controls=[
                    ft.TextField(label=self.label,read_only=True,visible=self.visible_form, width=250),
                    ft.IconButton(
                        icon=ft.Icons.CALENDAR_MONTH,
                        tooltip="Seleccionar fecha",
                        on_click=lambda e: self.page.open(self.picker)
                    ),
                ],
                spacing=10,
                visible=self.visible_form,
            )
        elif self.type == "DateTimeField":
            widget = ft.Row(
                controls=[
                    ft.TextField(label=self.label,read_only=True,visible=self.visible_form, width=250),
                    ft.IconButton(
                        icon=ft.Icons.CALENDAR_MONTH,
                        tooltip="Seleccionar fecha y hora",
                        on_click=lambda e: self.page.open(self.picker)
                    ),
                ],
                spacing=10,
                visible=self.visible_form,
            )
        elif self.type == "SelectField":
            widget = AutoCompleteSelect(
                self.page,
                data={},  # datos iniciales
                label=self.label
            ).control
        elif self.type == "SelectMultipleField":
            widget = AutoCompleteSelectMultiple(
                self.page,
                data={},
                label=self.label
            ).control
        elif self.type == "RelationalSelectGroupField":
            widget = RelationalSelectGroup(self.page, relations=self.extra_config.get("relations", []))
        return widget
