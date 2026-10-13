"""App shell: permisos, rutas con parámetros, notificaciones, ayuda, tema y administración."""

import flet as ft

from tests.test_flows import option

from fletbatteries.auth import AuthUser, login


async def as_user(app, **kwargs):
    login(app.page, AuthUser(**{"id": 999, "username": "limitado", **kwargs}))
    await app.goto("/")


async def test_menu_and_routes_respect_permissions(app):
    await as_user(app)
    assert app.find(key="menu-/customers")
    assert not app.find(key="menu-/admin/users")  # requiere auth.manage
    assert not app.find(key="menu-group-Administración")
    await app.goto("/admin/users")
    assert app.find(text="No tiene permiso para ver esta página.")

    # Con el permiso el menú se reconstruye
    await as_user(app, permissions=frozenset({"auth.manage"}))
    assert app.find(key="menu-group-Administración")
    await app.goto("/admin/users")
    assert app.find(text="Usuarios")
    app.assert_no_errors()


async def test_route_with_params_and_breadcrumbs(logged_app):
    from data.manager.customer_manager import CustomerManager

    customer = CustomerManager().create(name="Paula", last_name="Ruta", email="paula@shell.test")
    app = logged_app
    await app.goto(f"/customers/{customer.id}")
    assert app.find_one(key="customer_title").value == "Paula Ruta"
    crumbs = app.find_one(key="breadcrumbs")
    texts = [c.content if isinstance(c, ft.TextButton) else c.value for c in crumbs.controls
             if isinstance(c, (ft.Text, ft.TextButton))]
    assert texts == ["Inicio", "Customer", "Detalle del cliente"]
    await app.click(app.find_one(type=ft.TextButton, text="Customer", root=crumbs))
    assert app.page.route == "/customers"

    await app.goto("/customers/999999")
    assert app.find(key="customer_not_found")
    CustomerManager().delete(customer.id)
    app.assert_no_errors()


async def test_notifications_bell(logged_app):
    from fletbatteries.contrib.notifications import NotificationManager, create_notification

    app = logged_app
    bell = app.find_one(key="notification_bell")
    before = bell.count
    await app.click(app.find_one(key="create_notification"))
    assert bell.count == before + 1 and bell.badge.visible

    n = create_notification(1, "Revise los clientes", level="warning", link="/customers")
    await app.goto("/charts")  # al navegar se actualiza el contador
    assert bell.count == before + 2

    await app.click(bell.button)
    assert app.find(text="Revise los clientes")
    await app.click(app.find_one(key=f"notification-{n.id}"))
    assert app.page.route == "/customers"
    assert NotificationManager().get(n.id).read
    assert bell.count == before + 1

    await app.click(bell.button)
    await app.click(app.find_one(type=ft.TextButton, text="Marcar todas como leídas"))
    assert bell.count == 0 and not bell.badge.visible
    app.assert_no_errors()


async def test_help_button_edit(logged_app):
    from fletbatteries.contrib.help import HelpManager

    app = logged_app
    await app.click(app.find_one(key="help-home"))
    assert app.find(text="No hay ayuda disponible.")
    await app.click(app.find_one(type=ft.TextButton, text="Editar ayuda"))
    await app.fill(app.find_one(key="help_editor"), "**Bienvenido** al panel")
    await app.click(app.find_one(type=ft.TextButton, text="Guardar"))
    assert HelpManager().get_help("home").text == "**Bienvenido** al panel"
    assert app.find(text="**Bienvenido** al panel")
    app.assert_no_errors()


async def test_help_button_read_only_without_permission(app):
    await as_user(app)
    await app.click(app.find_one(key="help-home"))
    assert not app.find(type=ft.TextButton, text="Editar ayuda")
    app.assert_no_errors()


async def test_theme_is_persisted_between_sessions(logged_app):
    from fletbatteries.contrib.settings import clear_settings_cache, get_setting, set_setting
    from main import main
    from tests.harness import AppHarness

    app = logged_app
    await app.goto("/settings")
    switch = app.find_one(type=ft.Switch)
    app.session.apply_patch(switch._i, {"value": True})
    await app.trigger(switch, "change")
    assert get_setting("theme.mode") == "dark"

    clear_settings_cache()
    other = await AppHarness(main).start()
    try:
        assert other.page.theme_mode == ft.ThemeMode.DARK
    finally:
        await other.stop()
        set_setting("theme.mode", "light")


async def test_admin_users_with_groups_and_permissions(logged_app):
    from fletbatteries.auth.backend import DatabaseAuthBackend, GroupManager, PermissionManager, UserManager

    perm = PermissionManager().ensure("reports.view", "Ver reportes")
    group = GroupManager().create(name="Analistas", permissions=[perm.id])

    app = logged_app
    await app.goto("/admin/users")
    await app.click(app.find_one(key="crud_add"))
    await app.fill(app.find_one(key="username").field, "analista")
    await app.fill(app.find_one(key="password").field, "clave123")
    groups = app.find_one(key="groups")
    await app.click(groups._search_field)
    await app.click(option(app, "Analistas"))
    await app.click(app.find_one(type=ft.Button, text="Guardar"))
    assert app.find(text="Guardado exitosamente")

    user = UserManager().get_by_username("analista")
    assert [g.name for g in user.groups] == ["Analistas"]
    auth_user = DatabaseAuthBackend().authenticate("analista", "clave123")
    assert auth_user.has_perm("reports.view") and not auth_user.has_perm("auth.manage")
    assert DatabaseAuthBackend().authenticate("analista", "otra") is None

    # La lista no muestra el hash de la contraseña
    assert not any(t.startswith("$2b$") for t in app.all_texts())
    UserManager().delete(user.id)
    GroupManager().delete(group.id)
    app.assert_no_errors()


def test_settings_store():
    from fletbatteries.contrib.settings import clear_settings_cache, get_setting, set_setting

    assert get_setting("x.missing", default=5) == 5
    set_setting("x.list", [1, 2])
    clear_settings_cache()
    assert get_setting("x.list") == [1, 2]
    set_setting("x.list", {"a": 1})
    assert get_setting("x.list") == {"a": 1}
