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