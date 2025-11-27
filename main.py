import flet as ft
import os
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
from flet_webview import WebView

SAVE_DIR = os.path.abspath("contenido")
os.makedirs(SAVE_DIR, exist_ok=True)


class TinyRequestHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path.startswith("/save_content"):
            length = int(self.headers["Content-Length"])
            data = json.loads(self.rfile.read(length))
            editor_id = self.path.split("=")[-1]
            content = data.get("content", "")

            filename = os.path.join(SAVE_DIR, f"{editor_id}.html")
            with open(filename, "w", encoding="utf-8") as f:
                f.write(content)

            self.send_response(200)
            self.end_headers()


threading.Thread(
    target=lambda: HTTPServer(("localhost", 8000), TinyRequestHandler).serve_forever(),
    daemon=True,
).start()


def main(page: ft.Page):
    page.title = "TinyMCE en Flet"
    page.scroll = "auto"
    page.padding = 20
    page.bgcolor = ft.Colors.WHITE

    contenido_basic_val = ""
    contenido_advanced_val = ""

    resultado_text = ft.Column(scroll="auto", expand=True)

    webview = WebView(
        url="http://localhost:8000/assets/editor1.html",
        expand=True,
        height=500,
    )

    def recibir_mensaje(e):
        nonlocal contenido_basic_val, contenido_advanced_val
        try:
            data = json.loads(e.data)
            editor = data.get("editor")
            content = data.get("content")
            action = data.get("action", "")

            if editor == "editor_basic":
                contenido_basic_val = content
            elif editor == "editor_advanced":
                contenido_advanced_val = content

            filename = os.path.join(SAVE_DIR, f"{editor}.html")
            with open(filename, "w", encoding="utf-8") as f:
                f.write(content)

            resultado_text.controls.clear()
            resultado_text.controls.append(ft.Text(f"📌 Última acción: {action}", color=ft.Colors.BLUE))
            if contenido_basic_val:
                resultado_text.controls.append(ft.Text("📝 Contenido Básico:", weight="bold"))
                resultado_text.controls.append(ft.Text(contenido_basic_val, selectable=True))
            if contenido_advanced_val:
                resultado_text.controls.append(ft.Text("📑 Contenido Avanzado:", weight="bold"))
                resultado_text.controls.append(ft.Text(contenido_advanced_val, selectable=True))
            page.update()

        except Exception as err:
            print("Error al procesar mensaje:", err)

    page.add(
        webview,
        resultado_text,
    )

ft.app(target=main, view=ft.WEB_BROWSER)
