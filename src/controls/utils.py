import random
import flet as ft


def random_image_url(width=300, height=200):
    img_id = random.randint(1, 1000)
    return f"https://picsum.photos/seed/{img_id}/{width}/{height}"


def truncate_str(data, max_length=30):
    full = (data or "").strip()

    if len(full) > max_length:
        short = full[:max_length].rstrip() + "..."
        return short, full

    return full, ""


def text_with_truncate(data, size=12, bold=False, color=ft.Colors.BLACK, max_length=30, max_line=1):
    msg, tooltip = truncate_str(data, max_length)

    text = ft.Text(
        msg,
        size=size,
        color=color,
        max_lines=max_line,
    )
    if bold:
        text.weight = ft.FontWeight.BOLD

    if tooltip:
        text.tooltip = tooltip

    return text


def get_form(forms, name):
    for form in forms:
        if form.name == name:
            return form
    return None


def show_snackbar(message: str, success: bool):
    return ft.SnackBar(
        content=ft.Row(
            spacing=8,
            controls=[
                ft.Icon(
                    ft.Icons.CHECK_CIRCLE_OUTLINE if success else ft.Icons.ERROR_OUTLINE,
                    color=ft.Colors.GREEN_600 if success else ft.Colors.RED_600,
                ),
                ft.Text(message, color=ft.Colors.BLACK),
            ],
        ),
        bgcolor=ft.Colors.GREEN_50 if success else ft.Colors.RED_50,
        show_close_icon=True,
    )



def is_mounted(control: ft.BaseControl) -> bool:
    """True si el control ya está agregado a una página (en Flet 1.x `control.page` lanza si no lo está)."""
    try:
        return control.page is not None
    except RuntimeError:
        return False


def safe_update(*controls: ft.BaseControl):
    """Actualiza solo los controles que ya están montados en la página."""
    for control in controls:
        if is_mounted(control):
            control.update()


def close_dialog(dialog: ft.DialogControl):
    """
    Cierra un diálogo específico.

    `page.pop_dialog()` cierra el diálogo abierto más reciente, que puede ser
    un SnackBar mostrado encima; este helper cierra exactamente `dialog`.
    """
    if dialog.open:
        dialog.open = False
        safe_update(dialog)
