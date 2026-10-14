"""Flujos de interfaz con la app mínima de la librería (sin la demo)."""

import asyncio
import datetime
from decimal import Decimal

import flet as ft

from fletbatteries.auth.backend import UserManager

from tests_lib.conftest import build_app, start_app
from tests_lib.models import CategoryManager, DocManager, ItemManager


def make_items(n: int = 12):
    cat = CategoryManager().create(name="General")
    return [ItemManager().create(name=f"Item {i:02d}", code=f"C-{i:02d}", price=Decimal(i), kind="a",
                                 category_id=cat.id) for i in range(n)]


def table(app):
    from fletbatteries.widgets.datatable import DataTable

    return app.find_one(type=DataTable)


async def test_search_is_debounced(lib_app):
    make_items(12)
    app = lib_app
    await app.goto("/items")
    dt = table(app)
    assert dt.total == 12
    await app.fill(app.find_one(key="datatable_search"), "Item 1")
    assert dt.total == 12  # todavía no consulta
    await asyncio.sleep(dt.search_delay + 0.05)
    await app.settle()
    assert dt.total == 2
    # Enter busca de inmediato
    app.session.apply_patch(app.find_one(key="datatable_search")._i, {"value": "Item 05"})
    await app.trigger(app.find_one(key="datatable_search"), "submit")
    assert dt.total == 1
    app.assert_no_errors()


async def test_bulk_delete_keeps_selection_across_pages(lib_app):
    items = make_items(12)
    app = lib_app
    await app.goto("/items")
    dt = table(app)
    rows = dt.table.rows
    await app.trigger(rows[0], "select_change", True)
    await app.click(dt.btn_next)
    await app.trigger(dt.table.rows[0], "select_change", True)
    assert len(dt.selected_items) == 2
    assert app.find_one(key="datatable_bulk_count").value == "2 seleccionados"
    await app.click(app.find_one(key="bulk-delete"))
    await app.click(app.find_one(key="bulk_confirm"))
    assert ItemManager().count() == 10
    assert ItemManager().get(items[0].id) is None
    assert app.find(contains="2 registros eliminados")
    assert not dt.selected_items
    # Seleccionar todos los que cumplen la búsqueda
    await app.trigger(dt.table.rows[0], "select_change", True)
    await app.click(app.find_one(key="datatable_select_all"))
    assert len(dt.selected_items) == 10
    await app.click(app.find_one(key="datatable_clear_selection"))
    assert not dt.selected_items and not dt.bulk_bar.visible
    app.assert_no_errors()


async def test_export_csv_saves_file(lib_app, tmp_path):
    make_items(3)
    app = lib_app
    target = tmp_path / "items.csv"
    calls = []

    def save_file(args):
        calls.append(args)
        return str(target)

    app.client_methods["save_file"] = save_file
    await app.goto("/items")
    await app.click(app.find_one(key="datatable_export"))
    await app.settle()
    assert calls and calls[0]["file_name"].startswith("Items-") and calls[0]["file_name"].endswith(".csv")
    lines = target.read_bytes().decode("utf-8-sig").splitlines()
    assert lines[0] == "Nombre,Código,Precio,Tipo,Categoría" and len(lines) == 4
    assert lines[1] == "Item 00,C-00,0.00,Tipo A,General"
    app.assert_no_errors()


async def test_import_dialog(lib_app, tmp_path):
    make_items(2)
    app = lib_app
    csv_file = tmp_path / "nuevos.csv"
    csv_file.write_text("Nombre,Código,Precio\nNuevo,N-1,5\nCambiado,C-00,7\n,X,abc\n", encoding="utf-8")
    app.client_methods["pick_files"] = lambda args: [
        {"id": 1, "name": csv_file.name, "path": str(csv_file), "size": csv_file.stat().st_size}]
    await app.goto("/items")
    await app.click(app.find_one(key="crud_import"))
    await app.click(app.find_one(key="import_pick"))
    await app.settle()
    assert app.find_one(key="import_summary").value.startswith("1 nuevos, 1 por actualizar, 1 con errores")
    await app.click(app.find_one(key="import_run"))
    assert ItemManager().first(code="N-1").name == "Nuevo"
    assert ItemManager().first(code="C-00").name == "Cambiado"
    assert app.find(contains="Importación terminada: 1 creados, 1 actualizados")
    assert table(app).total == 3
    app.assert_no_errors()


async def test_clone_record(lib_app):
    items = make_items(1)
    app = lib_app
    await app.goto("/items")
    await app.click(app.find_one(key=f"clone-{items[0].id}"))
    assert app.find(text="Duplicar item")
    assert app.find_one(key="name").value == "Item 00"
    assert app.find_one(key="code").value in ("", None)  # campo único vacío
    await app.fill(app.find_one(key="code").field, "C-99")
    await app.click(app.find_one(type=ft.Button, text="Guardar"))
    assert ItemManager().count(name="Item 00") == 2
    app.assert_no_errors()


async def test_unique_error_shows_on_field(lib_app):
    make_items(1)
    app = lib_app
    await app.goto("/items")
    await app.click(app.find_one(key="crud_add"))
    await app.fill(app.find_one(key="name").field, "Otro")
    await app.fill(app.find_one(key="code").field, "C-00")
    await app.click(app.find_one(type=ft.Button, text="Guardar"))
    assert "Ya existe" in (app.find_one(key="code").error or "")
    app.assert_no_errors()


async def test_delete_error_message_and_undo(lib_app, monkeypatch):
    from sqlalchemy.exc import IntegrityError

    items = make_items(1)
    app = lib_app
    await app.goto("/items")

    def fail(self, s, obj):
        raise IntegrityError("DELETE", {}, Exception("FOREIGN KEY constraint failed"))

    monkeypatch.setattr(ItemManager, "perform_delete", fail)
    await app.click(app.find_one(key=f"delete-{items[0].id}"))
    await app.click(app.find_one(type=ft.Button, text="Eliminar"))
    assert app.find(contains="está en uso por otros registros")
    monkeypatch.undo()
    # Con error el diálogo queda abierto
    await app.click(app.find_one(type=ft.TextButton, text="Cancelar"))

    # Con papelera: "Deshacer" restaura
    doc = DocManager().create(title="Contrato")
    await app.goto("/docs")
    await app.click(app.find_one(key=f"delete-{doc.id}"))
    await app.click(app.find_one(type=ft.Button, text="Eliminar"))
    assert DocManager().count() == 0
    snack = app.find_one(type=ft.SnackBar, contains=None, where=lambda c: c.action is not None)
    await app.click(snack.action)
    assert DocManager().count() == 1
    assert app.find(text="Restaurado exitosamente")
    app.assert_no_errors()


async def test_menu_badge_and_footer_links(admin):
    from fletbatteries.auth import login
    from fletbatteries.auth.backend import to_auth_user
    from fletbatteries.layout.menu import MenuItem

    make_items(4)
    app_config = build_app()
    app_config.extra_menu.append(MenuItem("Ayuda", route="/docs", icon=ft.Icons.HELP, position="footer"))
    app = await start_app(app_config)
    try:
        login(app.page, to_auth_user(admin))
        await app.goto("/")
        badge = app.find_one(key="menu-badge-/items").badge
        assert badge.label == "4"
        ItemManager().create(name="otro")
        await app.goto("/docs")
        assert app.find_one(key="menu-badge-/items").badge.label == "5"
        await app.click(app.find_one(key="footer-/docs"))
        assert app.page.route == "/docs"
        app.assert_no_errors()
    finally:
        await app.stop()


async def test_framework_views_render(lib_app):
    app = lib_app
    for route in ("/account/password", "/account/tokens", "/admin/users", "/admin/groups", "/admin/permissions",
                  "/history", "/trash", "/admin/settings", "/admin/logins"):
        await app.goto(route)
        assert app.page.route == route
        assert not app.find(text="Página no encontrada"), route
    app.assert_no_errors()


async def test_password_change_view(lib_app, admin):
    app = lib_app
    await app.goto("/")
    await app.click(app.find_one(key="user-menu-/account/password"))
    assert app.page.route == "/account/password"
    await app.fill(app.find_one(key="old_password").field, "mala")
    await app.fill(app.find_one(key="new_password").field, "Nueva-clave-55")
    await app.fill(app.find_one(key="confirm").field, "Nueva-clave-55")
    await app.click(app.find_one(key="password_change"))
    assert "no es correcta" in (app.find_one(key="old_password").error or "")
    await app.fill(app.find_one(key="old_password").field, "S3guro-root!")
    await app.fill(app.find_one(key="confirm").field, "otra")
    await app.click(app.find_one(key="password_change"))
    assert app.find_one(key="confirm").error
    await app.fill(app.find_one(key="confirm").field, "Nueva-clave-55")
    await app.click(app.find_one(key="password_change"))
    assert app.find(text="Su contraseña se cambió.")
    from fletbatteries.auth.passwords import verify_password

    assert verify_password("Nueva-clave-55", UserManager().get(admin.id).password)
    app.assert_no_errors()


async def test_login_lockout_and_password_reset(admin, outbox):
    app = await start_app(build_app(), route="/login")
    try:
        for _i in range(5):
            await app.fill(app.find_one(key="login_username"), "root")
            await app.fill(app.find_one(key="login_password"), "mala")
            await app.click(app.find_one(key="login_submit"))
        await app.fill(app.find_one(key="login_password"), "S3guro-root!")
        await app.click(app.find_one(key="login_submit"))
        assert "Demasiados intentos" in app.find_one(key="login_error").value

        await app.click(app.find_one(key="login_forgot"))
        assert app.page.route == "/password-reset"
        await app.fill(app.find_one(key="reset_identifier"), "root@example.com")
        await app.click(app.find_one(key="reset_send"))
        await app.settle(0.05)
        assert outbox and app.find_one(key="reset_info").visible
        code = outbox[-1].body.split(": ")[1].split()[0]
        await app.fill(app.find_one(key="reset_code"), code)
        await app.fill(app.find_one(key="reset_new_password"), "Recuperada-123")
        await app.fill(app.find_one(key="reset_confirm"), "Recuperada-123")
        await app.click(app.find_one(key="reset_submit"))
        assert "Ya puede ingresar" in app.find_one(key="reset_info").value
        # Recuperar la contraseña desbloquea la cuenta
        await app.click(app.find_one(key="reset_back"))
        await app.fill(app.find_one(key="login_username"), "root")
        await app.fill(app.find_one(key="login_password"), "Recuperada-123")
        await app.click(app.find_one(key="login_submit"))
        assert app.page.route == "/"
        app.assert_no_errors()
    finally:
        await app.stop()


async def test_session_idle_expiry(admin):
    app = await start_app(build_app(session_idle_minutes=5, session_check_seconds=0.05), route="/login")
    try:
        await app.fill(app.find_one(key="login_username"), "root")
        await app.fill(app.find_one(key="login_password"), "S3guro-root!")
        await app.click(app.find_one(key="login_submit"))
        assert app.page.route == "/"
        from fletbatteries.app import shell_of

        shell = shell_of(app.page)
        shell.last_activity = datetime.datetime.now() - datetime.timedelta(minutes=6)
        await asyncio.sleep(0.15)
        await app.settle()
        assert app.page.route == "/login?expired=1"
        assert "sesión venció" in app.find_one(key="login_error").value
        app.assert_no_errors()
    finally:
        await app.stop()


async def test_api_tokens_view(lib_app):
    from fletbatteries.auth.tokens import ApiTokenManager, authenticate_token

    app = lib_app
    await app.goto("/account/tokens")
    await app.click(app.find_one(key="crud_add"))
    await app.fill(app.find_one(key="name").field, "Reportes")
    await app.click(app.find_one(type=ft.Button, text="Guardar"))
    await app.settle(0.05, rounds=6)
    raw = app.find_one(key="api_token_value").value
    assert authenticate_token(raw).username == "root"
    await app.click(app.find_one(key="api_token_close"))
    token = ApiTokenManager().first(name="Reportes")
    await app.click(app.find_one(key=f"delete-{token.id}"))
    await app.click(app.find_one(type=ft.Button, text="Revocar"))
    assert ApiTokenManager().get(token.id).revoked
    app.assert_no_errors()


async def test_settings_admin(lib_app):
    from fletbatteries.contrib.settings import get_setting, set_setting

    set_setting("app.name", "Viejo")
    app = lib_app
    await app.goto("/admin/settings")
    await app.click(app.find_one(key="crud_add"))
    await app.fill(app.find_one(key="key").field, "app.limit")
    await app.fill(app.find_one(key="value").field, "{no json")
    await app.click(app.find_one(type=ft.Button, text="Guardar"))
    assert app.find_one(key="value").error
    await app.fill(app.find_one(key="value").field, '{"max": 5}')
    await app.click(app.find_one(type=ft.Button, text="Guardar"))
    assert get_setting("app.limit") == {"max": 5}
    app.assert_no_errors()
