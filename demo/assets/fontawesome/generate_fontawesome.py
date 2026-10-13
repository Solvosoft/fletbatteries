import os

# Ruta base
BASE_PATH = os.path.dirname(os.path.abspath(__file__))

# Diccionario que guardará iconos como: "facebook": "brands/facebook.svg"
icons = {}

# Recorremos cada carpeta: brands, regular, solid
for style in ["brands", "regular", "solid"]:
    style_path = os.path.join(BASE_PATH, style)
    if not os.path.exists(style_path):
        continue

    for file in os.listdir(style_path):
        if file.endswith(".svg"):
            name = file.removesuffix(".svg").replace("-", "_")
            icons[name] = f"{style}/{file}"

# Archivo destino
output_file = os.path.join(BASE_PATH, "fontwesome.py")

# Generar archivo Python
with open(output_file, "w", encoding="utf-8") as f:
    f.write("# Auto-generado: mapa de iconos FontAwesome locales\n")
    f.write("icons = {\n")
    for name in sorted(icons.keys()):
        f.write(f'    "{name}": "{icons[name]}",\n')
    f.write("}\n\n")
    f.write("""
import re
from pathlib import Path

import flet as ft

FONTAWESOME_DIR = Path(__file__).resolve().parent


def svg_content(path, color=None) -> bytes:
    # Contenido del SVG (opcionalmente recoloreado) listo para `ft.Image(src=...)`
    with open(FONTAWESOME_DIR / path, "r", encoding="utf-8") as f:
        content = f.read()

    if color:
        if 'fill="' in content:
            content = re.sub(r'fill="[^"]+"', f'fill="{color}"', content)
        else:
            content = content.replace("<svg", f'<svg fill="{color}"', 1)

    return content.encode("utf-8")


def get_icon(name, color=None, size=40):
    path = icons.get(name)
    if not path:
        print(f"[get_icon] Icono no encontrado: {name}")
        return None

    # Los bytes funcionan igual en escritorio y en web (no dependen del cwd)
    return ft.Image(
        src=svg_content(path, color),
        width=size,
        height=size,
        fit=ft.BoxFit.CONTAIN
    )


def social_item(name, link, tooltip="", color=None, width=100, height=100, size=40):
    async def open_link(e):
        await ft.UrlLauncher().launch_url(link)

    return ft.Card(
        content=ft.Container(
            width=width,
            height=height,
            alignment=ft.Alignment.CENTER,
            padding=10,
            content=ft.GestureDetector(
                on_tap=open_link,
                content=get_icon(name, size=size, color=color),
                mouse_cursor=ft.MouseCursor.CLICK,
            ),
            tooltip=tooltip,
        ),
        elevation=4,
    )

""")

print(f"Archivo generado: {output_file}")
