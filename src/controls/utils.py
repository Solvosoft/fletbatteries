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

