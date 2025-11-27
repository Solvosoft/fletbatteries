import flet as ft
from flet_contrib.color_picker import ColorPicker


def open_color_picker(e, page,  dialog):
    page.open(dialog)
    page.update()

def change_color(e, page, picker, color_icon, dialog, callback=None):
    color_icon.icon_color = picker.color
    if callback:
        callback(picker.color)
    page.close(dialog)
    page.update()

def color_picker(page, callback=None):
    piker = ColorPicker(color="#c8df6f", width=300)
    icon = ft.IconButton(icon=ft.Icons.BRUSH)

    dialog = ft.AlertDialog(
        content=piker,
        actions=[
            ft.TextButton("OK", on_click=lambda e: change_color(e, page, piker, icon, dialog, callback)),
            ft.TextButton("Cancel", on_click=lambda e: page.close(dialog)),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
        on_dismiss=lambda e: page.close(dialog),
    )

    icon.on_click = lambda e: open_color_picker(e, page, dialog)

    return icon




