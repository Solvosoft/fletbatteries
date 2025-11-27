import flet as ft

def change_theme_mode(e, page, sw):
    if page.theme_mode == ft.ThemeMode.DARK:
        page.theme_mode = ft.ThemeMode.LIGHT
        sw.thumb_icon = ft.Icons.LIGHT_MODE
    else:
        sw.thumb_icon = ft.Icons.DARK_MODE
        page.theme_mode = ft.ThemeMode.DARK
    page.update()


def on_color_change(color, page, preview):
    page.theme = ft.Theme(color_scheme_seed=color)
    preview.bgcolor = color
    page.update()
