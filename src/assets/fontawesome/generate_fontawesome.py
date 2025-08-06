import os

# Ruta base (ajústala si este script no está en la misma carpeta que brands/, regular/, solid/)
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
import os
import re
import tempfile
import flet as ft
import webbrowser

def apply_color_to_svg(svg_path, color):
    with open(svg_path, "r", encoding="utf-8") as f:
        content = f.read()

    if 'fill="' in content:
        content = re.sub(r'fill="[^"]+"', f'fill="{color}"', content)
    else:
        content = content.replace("<svg", f'<svg fill="{color}"', 1)

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".svg", mode="w", encoding="utf-8")
    temp_file.write(content)
    temp_file.close()
    return temp_file.name


def get_icon(name, color=None, size=40):
    path = icons.get(name)
    if not path:
        print(f"[get_icon] Icono no encontrado: {name}")
        return None

    full_path = os.path.join("assets/fontwesome", path)

    if color:
        full_path = apply_color_to_svg(full_path, color)

    return ft.Image(
        src=full_path,
        width=size,
        height=size,
        fit=ft.ImageFit.CONTAIN
    )


def social_item(name, link, tooltip="", color=None, width=100, height=100, size=40):
    return ft.Card(
        content=ft.Container(
            width=width,
            height=height,
            alignment=ft.alignment.center,
            padding=10,
            content=ft.GestureDetector(
                on_tap=lambda e: webbrowser.open(link),
                content=get_icon(name, size=size, color=color),
                mouse_cursor=ft.MouseCursor.CLICK,
            ),
            tooltip=tooltip,
        ),
        elevation=4,
    )

""")

print(f"Archivo generado: {output_file}")
