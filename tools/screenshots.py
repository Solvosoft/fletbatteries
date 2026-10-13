#!/usr/bin/env python3
"""
Toma capturas de pantalla de la app ejecutándose en modo web.

Levanta `src/main.py` como servidor web (sin abrir navegador) contra una copia
temporal de la base de datos, abre cada ruta con Chromium headless (Playwright)
y guarda `screenshots/<ruta>.png` y `screenshots/report.json`.

Pensado para que una persona o un agente revise visualmente el comportamiento:

    make screenshots                       # todas las rutas
    make screenshots ROUTES="/calendar /charts"

El exit code es distinto de 0 si el servidor registra errores, la consola del
navegador reporta errores o alguna captura sale en blanco.
"""

import argparse
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.parse
import urllib.request
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = BASE_DIR / "src"



def app_routes() -> list[str]:
    """Rutas registradas en la app (login primero)."""
    sys.path.insert(0, str(SRC_DIR))
    from controls.router.views import Views

    routes = [v.route for v in Views(page=None, forms=None).views]
    return sorted(routes, key=lambda r: (r != "/login", r != "/"))



def is_app_error(block: str) -> bool:
    """
    Un bloque del log es un error de la app si Flet reporta un handler fallido o
    si el traceback pasa por código de `src/`. Se ignoran las desconexiones de
    websocket que ocurren al cerrar cada pestaña.
    """
    return "Unhandled error" in block or f'File "{SRC_DIR}{os.sep}' in block


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def wait_http(url: str, timeout: float) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2) as resp:
                if resp.status == 200:
                    return
        except OSError:
            pass
        time.sleep(0.3)
    raise TimeoutError(f"El servidor no respondió en {url} después de {timeout}s")


def route_file_name(route: str) -> str:
    name = route.strip("/").replace("/", "_") or "home"
    return f"{name}.png"


def has_problem(entry: dict) -> bool:
    return entry["blank"] or entry["redirected"] or bool(entry["console_errors"])


def is_blank(png: bytes) -> bool:
    """True si la imagen es prácticamente de un solo color."""
    from io import BytesIO

    from PIL import Image

    image = Image.open(BytesIO(png)).convert("L")
    low, high = image.getextrema()
    return high - low < 8


def launch_browser(playwright):
    try:
        return playwright.chromium.launch()
    except Exception as bundled_error:
        # Si Playwright no descargó su Chromium, usar el del sistema
        for candidate in (os.environ.get("CHROMIUM_PATH"), "chromium", "chromium-browser", "google-chrome"):
            path = candidate and shutil.which(candidate)
            if path:
                return playwright.chromium.launch(executable_path=path)
        raise RuntimeError(
            "No se encontró Chromium. Ejecuta `uv run playwright install chromium` "
            "o define CHROMIUM_PATH."
        ) from bundled_error


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("routes", nargs="*", help="Rutas a capturar (por defecto todas)")
    parser.add_argument("--out", default=str(BASE_DIR / "screenshots"), help="Directorio de salida")
    parser.add_argument("--width", type=int, default=1440)
    parser.add_argument("--height", type=int, default=900)
    parser.add_argument("--wait", type=float, default=3.0, help="Segundos a esperar tras cargar cada ruta")
    parser.add_argument("--timeout", type=float, default=60.0, help="Segundos máximos para que arranque el servidor")
    parser.add_argument("--db", default=str(BASE_DIR / "template.db"), help="Base de datos a copiar para la sesión")
    args = parser.parse_args()

    from playwright.sync_api import sync_playwright

    routes = [r if r.startswith("/") else f"/{r}" for r in (args.routes or app_routes())]
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    tmp_dir = Path(tempfile.mkdtemp(prefix="fletbatteries-screens-"))
    db_copy = tmp_dir / "screens.db"
    if Path(args.db).exists():
        shutil.copy(args.db, db_copy)

    port = free_port()
    api_port = free_port()
    base_url = f"http://127.0.0.1:{port}"
    api_url = f"http://127.0.0.1:{api_port}"
    server_log_path = out_dir / "server.log"
    api_log_path = out_dir / "api.log"
    env = {
        **os.environ,
        "FLET_FORCE_WEB_SERVER": "1",
        "FLET_SERVER_PORT": str(port),
        "FLET_SERVER_IP": "127.0.0.1",
        "FLETBATTERIES_DB_URL": f"sqlite:///{db_copy}",
        "FLETBATTERIES_API_URL": api_url,
        "FLETBATTERIES_SKIP_LOGIN": "1",
        "PYTHONUNBUFFERED": "1",
    }
    # Asegura que el esquema esté completo (p. ej. tablas nuevas como calendar_events)
    subprocess.run(
        [sys.executable, str(SRC_DIR / "scripts" / "init_db.py"), "update_schema"],
        cwd=BASE_DIR, env={**env, "PYTHONPATH": str(SRC_DIR)}, check=True, stdout=subprocess.DEVNULL,
    )

    report = {"base_url": base_url, "api_url": api_url, "routes": [], "server_errors": []}
    with open(server_log_path, "w") as server_log, open(api_log_path, "w") as api_log:
        # La API la consumen las vistas de autocompletes
        api = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "scripts.api:app", "--app-dir", str(SRC_DIR),
             "--host", "127.0.0.1", "--port", str(api_port)],
            cwd=BASE_DIR,
            env=env,
            stdout=api_log,
            stderr=subprocess.STDOUT,
        )
        server = subprocess.Popen(
            [sys.executable, str(SRC_DIR / "main.py")],
            cwd=BASE_DIR,
            env=env,
            stdout=server_log,
            stderr=subprocess.STDOUT,
        )
        try:
            wait_http(api_url + "/countries", args.timeout)
            wait_http(base_url, args.timeout)
            with sync_playwright() as p:
                browser = launch_browser(p)
                for route in routes:
                    context = browser.new_context(viewport={"width": args.width, "height": args.height})
                    page = context.new_page()
                    console_errors = []
                    page.on("console", lambda msg, errs=console_errors: msg.type == "error" and errs.append(msg.text))
                    page.on("pageerror", lambda exc, errs=console_errors: errs.append(str(exc)))

                    file = out_dir / route_file_name(route)
                    entry = {
                        "route": route,
                        "file": str(file.relative_to(BASE_DIR) if file.is_relative_to(BASE_DIR) else file),
                        "blank": False,
                        "redirected": False,
                        "console_errors": console_errors,
                    }
                    try:
                        page.goto(base_url + route, wait_until="networkidle", timeout=args.timeout * 1000)
                        page.wait_for_selector("flutter-view, flt-glass-pane", state="attached", timeout=args.timeout * 1000)
                        page.wait_for_timeout(args.wait * 1000)
                    except Exception as ex:
                        console_errors.append(f"Timeout/carga: {ex}".splitlines()[0])
                    png = page.screenshot(path=str(file))
                    entry["final_url"] = page.url
                    entry["redirected"] = urllib.parse.urlsplit(page.url).path != route
                    entry["blank"] = is_blank(png)
                    report["routes"].append(entry)
                    status = "REVISAR" if has_problem(entry) else "OK"
                    print(f"[{status}] {route} -> {entry['file']}")
                    context.close()
                browser.close()
        finally:
            for process in (server, api):
                process.terminate()
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()
            shutil.rmtree(tmp_dir, ignore_errors=True)

    log_text = server_log_path.read_text(errors="replace") + "\n\n" + api_log_path.read_text(errors="replace")
    report["server_errors"] = [
        block for block in log_text.split("\n\n") if is_app_error(block)
    ]
    report_path = out_dir / "report.json"
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False))

    problems = [r for r in report["routes"] if has_problem(r)]
    print(f"\nReporte: {report_path}  |  Logs: {server_log_path}, {api_log_path}")
    if report["server_errors"]:
        print(f"Los servidores registraron {len(report['server_errors'])} error(es); ver los logs")
    if problems:
        print("Rutas con problemas: " + ", ".join(r["route"] for r in problems))
    return 1 if problems or report["server_errors"] else 0


if __name__ == "__main__":
    sys.exit(main())
