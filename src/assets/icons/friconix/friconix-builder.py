#!/usr/bin/env python3
# Genera frx_flet.py (PATHS + helpers) y un índice JSON/CSV a partir de un JS con paths SVG.

import argparse
from pathlib import Path
import re, json, csv

PAIR_RE = re.compile(
    r'''(?P<key>["']?[\w\-\.:/]+["']?)\s*:\s*["'](?P<val>M[^"']+)["']''',
    re.MULTILINE
)

HEADER = """# frx_flet.py
# ============================================================
# Generado automáticamente por friconix-builder.py
# Provee utilidades para usar íconos (paths SVG) en Flet sin HTML/JS.
# Requiere: Flet >= 0.28 (botones con `content`).
# Buscar nombre de iconos en: https://friconix.com/
# ------------------------------------------------------------
# Uso rápido:
#   from frx_flet import frx_icon, frx_button, PATHS
#   ico = frx_icon("plus-solid", size=20, color="#2563eb")
#   btn = frx_button("Agregar", "plus-solid", color="#2563eb")
# ============================================================
from __future__ import annotations
import base64
from typing import Dict, Optional
import flet as ft
"""

CORE = """
def _svg_to_data_uri(svg_str: str) -> str:
    b64 = base64.b64encode(svg_str.encode('utf-8')).decode('ascii')
    return f"data:image/svg+xml;base64,{b64}"

def frx_icon(
    name: str,
    size: int = 24,
    color: str = "#000000",
    viewbox: str = "0 0 1000 1000",
    stroke: Optional[str] = None,
    stroke_width: Optional[int] = None,
    preserve_aspect_ratio: str = "xMidYMid meet",
    *,
    use_svg_control: bool = True,   # << clave: usar ft.Svg (Flet >= 0.28)
) -> ft.Control:
    if name not in PATHS:
        raise KeyError(f"Icono '{name}' no encontrado. Revisa PATHS.keys().")

    d = PATHS[name]
    stroke_attr = f' stroke="{stroke}" stroke-width="{stroke_width}"' if stroke and stroke_width else ""
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{viewbox}" '
        f'width="{size}" height="{size}" preserveAspectRatio="{preserve_aspect_ratio}">'
        f'\n  <path d="{d}" fill="{color}"{stroke_attr} />\n'
        f'</svg>'
    )

    if use_svg_control and hasattr(ft, "Svg"):
        # Flet vectorial nativo (recomendado para SVG)
        return ft.Svg(svg, width=size, height=size)  # en Flet ≥ 0.28, Svg acepta el contenido SVG como primer arg
    else:
        # Fallback (no recomendado para SVG; Image no renderiza SVG en desktop)
        b64 = base64.b64encode(svg.encode("utf-8")).decode("ascii")
        return ft.Image(src_base64=b64, width=size, height=size)

def frx_button(
    text: str,
    icon_name: str,
    *,
    icon_size: int = 20,
    icon_color: str = '#000000',
    spacing: int = 8,
    reverse: bool = False,
    button_cls=ft.ElevatedButton,
    **button_kwargs,
) -> ft.Control:
    # Crea un botón con contenido personalizado (ícono + texto) para Flet >= 0.28
    icon = frx_icon(icon_name, size=icon_size, color=icon_color)
    label = ft.Text(text)
    items = [label, icon] if reverse else [icon, label]
    row = ft.Row(controls=items, spacing=spacing,
                 alignment=ft.MainAxisAlignment.CENTER,
                 vertical_alignment=ft.CrossAxisAlignment.CENTER)
    return button_cls(content=row, **button_kwargs)
"""

def py_escape(s: str) -> str:
    return s.replace("\\", "\\\\").replace('"', '\\"')

def parse_js(js_text: str) -> dict[str, str]:
    pairs = []
    for m in PAIR_RE.finditer(js_text):
        raw_key = m.group("key").strip()
        if (raw_key.startswith("'") and raw_key.endswith("'")) or (raw_key.startswith('"') and raw_key.endswith('"')):
            key = raw_key[1:-1]
        else:
            key = raw_key
        val = m.group("val").strip()
        pairs.append((key, val))

    icon_map: dict[str, str] = {}
    for k, v in pairs:
        icon_map[k] = v
    return icon_map

def write_outputs(icon_map: dict[str, str], out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)

    module_path = out_dir / "frx_flet.py"
    with module_path.open("w", encoding="utf-8") as f:
        f.write(HEADER)
        f.write("\nPATHS: Dict[str, str] = {\n")
        for k, v in icon_map.items():
            f.write(f'    "{py_escape(k)}": "{py_escape(v)}",\n')
        f.write("}\n\n")
        f.write(CORE)

    (out_dir / "icons_index.json").write_text(
        json.dumps(icon_map, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    with (out_dir / "icons_index.csv").open("w", encoding="utf-8", newline="") as csvf:
        w = csv.writer(csvf)
        w.writerow(["name", "path"])
        for k, v in icon_map.items():
            w.writerow([k, v])

    return module_path

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("js_file", type=str, help="Ruta al archivo JS con diccionario nombre -> path")
    ap.add_argument("--out-dir", type=str, default=".", help="Directorio de salida")
    args = ap.parse_args()

    js_path = Path(args.js_file)
    out_dir = Path(args.out_dir)

    if not js_path.exists():
        raise SystemExit(f"No existe: {js_path}")

    js_text = js_path.read_text(encoding="utf-8")
    icon_map = parse_js(js_text)

    if not icon_map:
        raise SystemExit("No se detectaron entradas nombre->path en el JS. Revisa el formato.")

    module_path = write_outputs(icon_map, out_dir)
    print(f"OK. Íconos: {len(icon_map)}")
    print(f"Módulo: {module_path}")
    print(f"Índice JSON: {out_dir / 'icons_index.json'}")
    print(f"Índice CSV: {out_dir / 'icons_index.csv'}")

if __name__ == "__main__":
    main()

#  command line:
#  python3 ./friconix-builder.py ./friconix.js --out-dir ./