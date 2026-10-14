import flet as ft
import pytest

from tests.harness import layout_errors

ROUTES = [
    ("/", "Inicio"),
    ("/products", None),
    ("/users", None),
    ("/customers", None),
    ("/spinner", None),
    ("/modals", None),
    ("/fontawesome_icons", None),
    ("/friconix", None),
    ("/charts", None),
    ("/rive_animations", None),
    ("/calendar", None),
    ("/profile", None),
    ("/settings", None),
    ("/test", None),
    ("/autocompletes", None),
    ("/autocomplete_related", None),
    ("/widgets", "Widgets"),
    ("/forms", "Formularios"),
    ("/admin/users", "Usuarios"),
    ("/admin/groups", "Grupos"),
    ("/admin/permissions", "Permisos"),
    ("/notes", "Notas"),
    ("/maps", "Mapa de notas"),
    ("/history", "Historial"),
    ("/trash", "Papelera"),
    ("/admin/settings", "Configuración"),
    ("/admin/logins", "Intentos de ingreso"),
    ("/account/password", "Cambiar contraseña"),
    ("/account/tokens", "Tokens del API"),
    ("/wizard", "Grupos de campos"),
]


async def test_starts_on_login(app):
    assert app.page.route == "/login"
    app.find_one(key="login_submit")
    app.assert_no_errors()


@pytest.mark.parametrize("route,expected_text", ROUTES)
async def test_route_renders(logged_app, route, expected_text):
    app = logged_app
    await app.goto(route)
    app.assert_no_errors()
    assert app.page.route == route
    layout = app.find_one(where=lambda c: type(c).__name__ == "Layout")
    view = layout.controls[1]
    assert list(app.walk(view)), f"La vista {route} está vacía"
    if expected_text:
        assert expected_text in app.all_texts()


@pytest.mark.parametrize("route", [r for r, _ in ROUTES])
async def test_route_control_types(logged_app, route):
    app = logged_app
    await app.goto(route)
    errors = layout_errors(app.page)
    assert not errors, "\n".join(errors)


async def test_login_control_types(app):
    errors = layout_errors(app.page)
    assert not errors, "\n".join(errors)


def test_layout_rules_detect_flutter_errors():
    cases = [
        ft.Row([ft.Container(expand=True)], wrap=True),
        ft.ListView([ft.TextButton("x", expand=True)]),
        ft.Row([ft.Text("x")], alignment=ft.Alignment.CENTER),
    ]
    for ctrl in cases:
        assert layout_errors(ctrl), ctrl
    assert not layout_errors(ft.Column([ft.Container(expand=True)], expand=True))


async def test_deep_link_goes_to_login_and_back():
    from main import main
    from tests.harness import AppHarness

    app = await AppHarness(main, route="/charts").start()
    try:
        assert app.page.route == "/login?next=%2Fcharts"
        await app.fill(app.find_one(key="login_username"), "admin")
        await app.fill(app.find_one(key="login_password"), "admin")
        await app.click(app.find_one(key="login_submit"))
        assert app.page.route == "/charts"
        assert "Charts" in app.all_texts()
        app.assert_no_errors()
    finally:
        await app.stop()


async def test_unknown_route_goes_to_login():
    from main import main
    from tests.harness import AppHarness

    app = await AppHarness(main, route="/no-existe").start()
    try:
        assert app.page.route == "/login?next=%2Fno-existe"
        app.assert_no_errors()
    finally:
        await app.stop()


async def test_unknown_route_when_logged_shows_not_found(logged_app):
    await logged_app.goto("/no-existe")
    assert logged_app.find(text="Página no encontrada")
    logged_app.assert_no_errors()


def _all_routes():
    from main import app

    return [r.path for r in app.routes]


def test_route_list_covers_all_views():
    # /password-reset no usa el layout (se prueba en test_flows sin sesión)
    tested = {"/login", "/customers/:id", "/password-reset"} | {r for r, _ in ROUTES}
    assert set(_all_routes()) == tested


def test_routes_do_not_collide_with_assets():
    """En modo web los assets se sirven en la raíz: /<carpeta> redirige al directorio estático."""
    from settings import ASSETS_DIR

    assets = {p.name for p in ASSETS_DIR.iterdir()}
    collisions = [r for r in _all_routes() if r.strip("/").split("/")[0] in assets]
    assert not collisions, f"Rutas que chocan con demo/assets: {collisions}"


async def test_app_does_not_depend_on_cwd(tmp_path, monkeypatch):
    """`flet run` ejecuta la app con el cwd en demo/: no debe haber rutas relativas al cwd."""
    from fletbatteries.auth import AuthUser, login
    from main import main
    from tests.harness import AppHarness

    monkeypatch.chdir(tmp_path)
    app = await AppHarness(main).start()
    login(app.page, AuthUser(id=1, username="admin", is_superuser=True))
    try:
        for route in [r for r, _ in ROUTES]:
            await app.goto(route)
        app.assert_no_errors()
    finally:
        await app.stop()


def test_models_configure_in_a_fresh_process():
    """Las relaciones entre modelos deben resolverse sin depender del orden de imports de las pruebas."""
    import os
    import subprocess
    import sys
    from pathlib import Path

    root = Path(__file__).resolve().parent.parent
    code = "import main\nfrom sqlalchemy.orm import configure_mappers\nconfigure_mappers()\n"
    env = {**os.environ, "PYTHONPATH": f"{root / 'demo'}{os.pathsep}{root / 'src'}"}
    result = subprocess.run([sys.executable, "-c", code], env=env, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
