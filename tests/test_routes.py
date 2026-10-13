import flet as ft
import pytest

from tests.harness import children

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
]


async def test_starts_on_login(app):
    assert app.page.route == "/login"
    app.find_one(text="Login")
    app.assert_no_errors()


@pytest.mark.parametrize("route,expected_text", ROUTES)
async def test_route_renders(app, route, expected_text):
    await app.goto(route)
    app.assert_no_errors()
    assert app.page.route == route
    layout = app.find_one(where=lambda c: type(c).__name__ == "Layout")
    view = layout.controls[1]
    assert list(app.walk(view)), f"La vista {route} está vacía"
    if expected_text:
        assert expected_text in app.all_texts()


def _check_types(ctrl, errors):
    """Valida tipos que Flet no comprueba en Python pero que rompen el render en Flutter."""
    name = type(ctrl).__name__
    if isinstance(ctrl, (ft.Row, ft.Column, ft.ResponsiveRow)):
        if ctrl.alignment is not None and not isinstance(ctrl.alignment, ft.MainAxisAlignment):
            errors.append(f"{name}.alignment={ctrl.alignment!r}")
        cross = "horizontal_alignment" if isinstance(ctrl, ft.Column) else "vertical_alignment"
        value = getattr(ctrl, cross, None)
        if value is not None and not isinstance(value, ft.CrossAxisAlignment):
            errors.append(f"{name}.{cross}={value!r}")
    if isinstance(ctrl, (ft.Container, ft.Stack)):
        value = getattr(ctrl, "alignment", None)
        if value is not None and not isinstance(value, ft.Alignment):
            errors.append(f"{name}.alignment={value!r}")
    for child in children(ctrl):
        _check_types(child, errors)


@pytest.mark.parametrize("route", ["/login"] + [r for r, _ in ROUTES])
async def test_route_control_types(app, route):
    await app.goto(route)
    errors = []
    _check_types(app.page, errors)
    assert not errors, "\n".join(errors)


async def test_deep_link_opens_route():
    from main import main
    from tests.harness import AppHarness

    app = await AppHarness(main, route="/charts").start()
    try:
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
        assert app.page.route == "/login"
        app.assert_no_errors()
    finally:
        await app.stop()


def _all_views():
    from controls.router.views import Views

    return Views(page=None, forms=None).views


def test_route_list_covers_all_views():
    tested = {"/login"} | {r for r, _ in ROUTES}
    assert {v.route for v in _all_views()} == tested


def test_routes_do_not_collide_with_assets():
    """En modo web los assets se sirven en la raíz: /<carpeta> redirige al directorio estático."""
    from settings import ASSETS_DIR

    assets = {p.name for p in ASSETS_DIR.iterdir()}
    collisions = [v.route for v in _all_views() if v.route.strip("/").split("/")[0] in assets]
    assert not collisions, f"Rutas que chocan con src/assets: {collisions}"


async def test_app_does_not_depend_on_cwd(tmp_path, monkeypatch):
    """`flet run` ejecuta la app con el cwd en src/: no debe haber rutas relativas al cwd."""
    from main import main
    from tests.harness import AppHarness

    monkeypatch.chdir(tmp_path)
    app = await AppHarness(main).start()
    try:
        for route in [r for r, _ in ROUTES]:
            await app.goto(route)
        app.assert_no_errors()
    finally:
        await app.stop()
