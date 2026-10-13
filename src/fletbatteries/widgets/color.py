"""Selector de color (paleta + hexadecimal) y el widget de formulario `ColorInput`."""

import re
from typing import Optional

import flet as ft

from fletbatteries.i18n import _
from fletbatteries.utils import close_dialog
from fletbatteries.widgets.base import Widget

# Paleta Material (tonos 200, 400, 600, 800) por color
PALETTE = {
    "red": ["#EF9A9A", "#EF5350", "#E53935", "#C62828"],
    "pink": ["#F48FB1", "#EC407A", "#D81B60", "#AD1457"],
    "purple": ["#CE93D8", "#AB47BC", "#8E24AA", "#6A1B9A"],
    "indigo": ["#9FA8DA", "#5C6BC0", "#3949AB", "#283593"],
    "blue": ["#90CAF9", "#42A5F5", "#1E88E5", "#1565C0"],
    "cyan": ["#80DEEA", "#26C6DA", "#00ACC1", "#00838F"],
    "teal": ["#80CBC4", "#26A69A", "#00897B", "#00695C"],
    "green": ["#A5D6A7", "#66BB6A", "#43A047", "#2E7D32"],
    "lime": ["#E6EE9C", "#D4E157", "#C0CA33", "#9E9D24"],
    "amber": ["#FFE082", "#FFCA28", "#FFB300", "#FF8F00"],
    "orange": ["#FFCC80", "#FFA726", "#FB8C00", "#EF6C00"],
    "brown": ["#BCAAA4", "#8D6E63", "#6D4C41", "#4E342E"],
    "grey": ["#EEEEEE", "#BDBDBD", "#757575", "#424242"],
    "blue_grey": ["#B0BEC5", "#78909C", "#546E7A", "#37474F"],
}

HEX_PATTERN = re.compile(r"^#[0-9a-fA-F]{6}$")


class ColorPicker(ft.Column):
    """Selector de color: paleta de tonos, campo hexadecimal y vista previa."""

    def __init__(self, color: str = "#C8DF6F", on_change=None, width: int = 300):
        super().__init__(tight=True, spacing=12, width=width)
        self.color = color.upper()
        self.on_color_change = on_change
        self.preview = ft.Container(
            key="color_picker_preview",
            width=40,
            height=40,
            border_radius=8,
            bgcolor=self.color,
            border=ft.Border.all(1, ft.Colors.GREY_400),
        )
        self.hex_field = ft.TextField(
            key="color_picker_hex",
            label="Hex",
            value=self.color,
            width=140,
            dense=True,
            on_change=self.on_hex_change,
        )
        self.controls = [
            ft.Row([self.preview, self.hex_field], spacing=12),
            ft.Column(
                [
                    ft.Row(
                        [self.swatch(c) for c in shades],
                        spacing=4,
                    )
                    for shades in zip(*PALETTE.values())
                ],
                spacing=4,
            ),
        ]

    def swatch(self, color: str):
        return ft.Container(
            key=f"swatch_{color}",
            width=18,
            height=18,
            border_radius=4,
            bgcolor=color,
            tooltip=color,
            on_click=lambda e, c=color: self.set_color(c),
        )

    def set_color(self, color: str, update_field: bool = True):
        self.color = color.upper()
        self.preview.bgcolor = self.color
        self.hex_field.error = None
        if update_field:
            self.hex_field.value = self.color
        if self.on_color_change:
            self.on_color_change(self.color)
        self.refresh()

    def on_hex_change(self, e):
        value = (self.hex_field.value or "").strip()
        if not value.startswith("#"):
            value = f"#{value}"
        if HEX_PATTERN.match(value):
            self.set_color(value, update_field=False)
        else:
            self.hex_field.error = _("Format #RRGGBB")
            self.refresh()

    def refresh(self):
        from fletbatteries.utils import safe_update

        safe_update(self)


def color_picker(page: ft.Page, callback=None, color: str = "#C8DF6F"):
    """IconButton que abre un diálogo con el selector y devuelve el color elegido a `callback`."""
    picker = ColorPicker(color=color)
    icon = ft.IconButton(icon=ft.Icons.BRUSH, key="color_picker_button")

    def on_ok(e):
        icon.icon_color = picker.color
        if callback:
            callback(picker.color)
        close_dialog(dialog)
        page.update()

    dialog = ft.AlertDialog(
        title=ft.Text(_("Select color")),
        content=picker,
        actions=[
            ft.TextButton("OK", key="color_picker_ok", on_click=on_ok),
            ft.TextButton(_("Cancel"), on_click=lambda e: close_dialog(dialog)),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )

    icon.on_click = lambda e: page.show_dialog(dialog)

    return icon


def _color_dialog(picker: ColorPicker, on_ok) -> ft.AlertDialog:
    dialog = ft.AlertDialog(
        title=ft.Text(_("Select color")),
        content=picker,
        actions_alignment=ft.MainAxisAlignment.END,
    )
    dialog.actions = [
        ft.TextButton("OK", key="color_picker_ok", on_click=lambda e: on_ok(dialog)),
        ft.TextButton(_("Cancel"), on_click=lambda e: close_dialog(dialog)),
    ]
    return dialog


class ColorInput(Widget):
    """Campo de color: muestra, valor hexadecimal y botón que abre el selector."""

    def __init__(self, label=None, help_text=None, default: str = "#1E88E5", **kwargs):
        super().__init__(label=label, help_text=help_text, **kwargs)
        self.swatch = ft.Container(width=28, height=28, border_radius=6, border=ft.Border.all(1, ft.Colors.GREY_400))
        self.field = ft.TextField(
            label=label,
            helper=help_text,
            width=200,
            prefix=self.swatch,
            suffix=ft.IconButton(icon=ft.Icons.PALETTE, on_click=self.open_picker),
            on_change=self._on_text,
        )
        self.default = default
        self.content = self.field
        self.set_value(None)

    def _on_text(self, e):
        self._sync_swatch()
        self.refresh()
        self.changed(e)

    def _sync_swatch(self):
        value = (self.field.value or "").strip()
        self.swatch.bgcolor = value if HEX_PATTERN.match(value) else None

    def open_picker(self, e=None):
        picker = ColorPicker(color=self.get_value() or self.default)

        def on_ok(dialog):
            self.set_value(picker.color)
            close_dialog(dialog)
            self.refresh()
            self.changed()

        self.app_page.show_dialog(_color_dialog(picker, on_ok))

    def get_value(self) -> Optional[str]:
        value = (self.field.value or "").strip().upper()
        return value or None

    def set_value(self, value):
        self.field.value = (value or "").upper()
        self._sync_swatch()

    def show_error(self, message):
        self.field.error = message

    def apply_label(self, label):
        self.field.label = label
