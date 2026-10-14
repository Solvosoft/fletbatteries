"""
App shell: router con parámetros y guards, menú con permisos, login, navbar,
breadcrumbs, notificaciones y tema persistente.

    app = FletBatteriesApp(title="Mi app", logo="image/icon.png")

    @app.view("/", title="Inicio", icon=ft.Icons.HOME)
    def home(page):
        return ft.Text("Hola")

    @app.view("/customers/:id", title="Cliente", menu=None, perms=["customers.view"])
    def customer_detail(page, id):
        ...

    app.add_crud(CustomerCRUD, "/customers", title="Clientes", icon=ft.Icons.PEOPLE)
    app.add_account_views()          # /account/password, /account/tokens, /password-reset
    app.add_admin_views()            # usuarios, grupos, permisos, historial, papelera, ...
    app.run()        # o ft.run(app.main)

Opciones de seguridad: `password_validators`, `password_reset=True` (recuperar
la contraseña con un código por correo), `session_idle_minutes` y
`session_max_minutes` (la sesión vence y vuelve al login). Idiomas:
`languages=[("es", "Español"), ("en", "English")]` agrega un selector en el
menú de usuario.

`FletBatteriesApp` es la configuración (compartida entre sesiones en modo web);
cada sesión crea un `AppShell` con sus propios controles.
"""

import asyncio
import dataclasses
import datetime
import logging
from typing import Any, Callable, Optional, Sequence
from urllib.parse import parse_qs, urlencode, urlsplit

import flet as ft

from fletbatteries.auth.session import AuthUser, get_user, has_perms, login, logout
from fletbatteries.i18n import _, get_language, set_language
from fletbatteries.layout.breadcrumbs import Breadcrumbs
from fletbatteries.layout.footer import Footer
from fletbatteries.layout.layout import Layout
from fletbatteries.layout.menu import MenuItem, filter_menu
from fletbatteries.layout.navbar import Navbar
from fletbatteries.layout.sidebar import Sidebar

log = logging.getLogger(__name__)

SESSION_SHELL_KEY = "fletbatteries.shell"
ADMIN_PERMISSION = "auth.manage"


@dataclasses.dataclass
class Route:
    path: str
    builder: Callable[..., ft.Control]
    title: str = ""
    icon: Any = None
    perms: Sequence[str] = ()
    any_perm: bool = False
    login_required: Optional[bool] = None  # None = lo que diga la app
    menu: Optional[str] = "sidebar"  # "sidebar" | "top" | None
    group: Optional[str] = None
    group_icon: Any = None
    layout: bool = True
    parent: Optional[str] = None  # ruta padre para los breadcrumbs
    badge: Optional[Callable[[Any], Any]] = None  # badge(page) -> número para el menú

    def match(self, path: str) -> Optional[dict]:
        if ":" not in self.path and "*" not in self.path:
            return {} if path == self.path else None
        t = ft.TemplateRoute(path)
        if not t.match(self.path):
            return None
        return {name.lstrip(":").rstrip("*?+"): getattr(t, name.lstrip(":").rstrip("*?+"), None)
                for name in self.path.split("/") if name.startswith(":")}


class FletBatteriesApp:
    def __init__(
        self,
        title: str = "FletBatteries",
        logo: Optional[str] = None,
        home: str = "/",
        login_required: bool = True,
        auth_backend=None,
        auto_login: Optional[AuthUser] = None,
        theme: Optional[ft.Theme] = None,
        theme_mode: ft.ThemeMode = ft.ThemeMode.LIGHT,
        persist_theme: bool = False,
        navbar_color=ft.Colors.LIGHT_BLUE_ACCENT_700,
        footer: Optional[ft.Control] = None,
        notifications: bool = False,
        notification_poll_interval: Optional[float] = 30,
        sidebar_title: Optional[str] = None,
        profile_route: Optional[str] = None,
        fonts: Optional[dict] = None,
        assets_dir: Optional[str] = None,
        menu: Sequence[MenuItem] = (),
        initial_route: Optional[str] = None,
        languages: Sequence[tuple[str, str]] = (),
        password_validators: Optional[Sequence] = None,
        password_reset: bool = False,
        session_idle_minutes: Optional[float] = None,
        session_max_minutes: Optional[float] = None,
        session_check_seconds: float = 30,
    ):
        self.title = title
        # Ruta al abrir la app cuando el cliente arranca en "/" (escritorio); útil para depurar
        self.initial_route = initial_route
        self.logo = logo
        self.home = home
        self.login_required = login_required
        self.auth_backend = auth_backend
        self.auto_login = auto_login
        self.theme = theme
        self.theme_mode = theme_mode
        self.persist_theme = persist_theme
        self.navbar_color = navbar_color
        self.footer = footer
        self.notifications = notifications
        self.notification_poll_interval = notification_poll_interval
        self.sidebar_title = sidebar_title
        self.profile_route = profile_route
        self.fonts = fonts
        self.assets_dir = assets_dir
        self.extra_menu = list(menu)
        self.languages = list(languages)
        # None = validadores por defecto (`auth.password_validation.default_password_validators`)
        self.password_validators = password_validators
        self.password_reset = password_reset
        self.session_idle_minutes = session_idle_minutes
        self.session_max_minutes = session_max_minutes
        self.session_check_seconds = session_check_seconds
        # Enlaces extra del menú de usuario: (título, ruta, ícono)
        self.user_links: list[tuple] = []
        self.routes: list[Route] = []
        if login_required:
            self.add_view("/login", self._login_builder, title=_("Login"), menu=None, login_required=False,
                          layout=False)

    # ------------------------------------------------------------------
    # Registro
    # ------------------------------------------------------------------
    def add_view(self, path: str, builder: Callable[..., ft.Control], title: str = "", **options) -> Route:
        route = Route(path=path, builder=builder, title=title or path.strip("/").capitalize(), **options)
        self.routes = [r for r in self.routes if r.path != path] + [route]
        return route

    def view(self, path: str, title: str = "", **options):
        """Decorador para registrar una vista: `builder(page, **params) -> Control`."""

        def decorator(fn):
            self.add_view(path, fn, title=title, **options)
            return fn

        return decorator

    def add_crud(self, crud_class, path: Optional[str] = None, title: Optional[str] = None, **options) -> Route:
        """Registra un `CRUDView`; por defecto exige su permiso de "view" si lo define."""
        path = path or crud_class.route
        if not path:
            raise ValueError(f"{crud_class.__name__} necesita `route` o `path`")
        options.setdefault("icon", crud_class.icon)
        perm = crud_class.permissions.get("view") if crud_class.permissions else None
        options.setdefault("perms", [perm] if perm else [])
        return self.add_view(path, lambda page: crud_class(page).build(), title=title or crud_class.title or path,
                             **options)

    def add_account_views(self, password_change: bool = True, api_tokens: bool = True,
                          password_reset: Optional[bool] = None):
        """
        Vistas de la cuenta del usuario: `/account/password` (cambiar la
        contraseña), `/account/tokens` (tokens del API) y, si
        `password_reset` (o la opción de la app), `/password-reset`.
        """
        if password_change:
            self.add_view("/account/password", self._password_change_builder, title=_("Change password"),
                          icon=ft.Icons.LOCK_RESET, menu=None)
            self.user_links.append((_("Change password"), "/account/password", ft.Icons.LOCK_RESET))
        if api_tokens:
            from fletbatteries.auth.views import ApiTokenCRUD

            self.add_view("/account/tokens", lambda page: ApiTokenCRUD(page).build(), title=_("API tokens"),
                          icon=ft.Icons.KEY, menu=None)
            self.user_links.append((_("API tokens"), "/account/tokens", ft.Icons.KEY))
        if password_reset if password_reset is not None else self.password_reset:
            self.password_reset = True
            self.add_view("/password-reset", self._password_reset_builder, title=_("Reset password"), menu=None,
                          login_required=False, layout=False)
        return self

    def add_admin_views(self, group: Optional[str] = None, group_icon=ft.Icons.ADMIN_PANEL_SETTINGS,
                        perms: Sequence[str] = (ADMIN_PERMISSION,), users: bool = True, groups: bool = True,
                        permissions: bool = True, history: bool = True, trash: bool = True, settings: bool = True,
                        logins: bool = True):
        """Vistas de administración del framework, agrupadas en el menú (`group`)."""
        from fletbatteries.auth.views import (
            GroupAdminCRUD,
            LoginAttemptCRUD,
            PermissionAdminCRUD,
            UserAdminCRUD,
        )

        group = group or _("Administration")
        options = {"group": group, "group_icon": group_icon, "perms": list(perms)}
        cruds = []
        if users:
            cruds.append(UserAdminCRUD)
        if groups:
            cruds.append(GroupAdminCRUD)
        if permissions:
            cruds.append(PermissionAdminCRUD)
        if history:
            from fletbatteries.contrib.history import HistoryCRUD

            cruds.append(HistoryCRUD)
        if logins:
            cruds.append(LoginAttemptCRUD)
        if settings:
            from fletbatteries.contrib.settings import build_settings_crud

            cruds.append(build_settings_crud())
        for crud in cruds:
            if crud is UserAdminCRUD and self.password_validators is not None:
                crud = type("UserAdminCRUD", (UserAdminCRUD,), {
                    "form_class": type("UserAdminForm", (UserAdminCRUD.form_class,),
                                       {"password_validators": self.password_validators})})
            self.add_crud(crud, **options)
        if trash:
            from fletbatteries.contrib.trash import build_trash_view

            self.add_view("/trash", build_trash_view, title=_("Trash"), icon=ft.Icons.DELETE_SWEEP, **options)
        return self

    def resolve(self, path: str) -> tuple[Optional[Route], dict]:
        for route in self.routes:
            params = route.match(path)
            if params is not None:
                return route, params
        return None, {}

    def get_route(self, path: str) -> Optional[Route]:
        return next((r for r in self.routes if r.path == path), None)

    def menu_items(self) -> list[MenuItem]:
        """Menú a partir de las vistas registradas (más `menu` extra)."""
        items: list[MenuItem] = []
        groups: dict[str, MenuItem] = {}
        for r in self.routes:
            if not r.menu or ":" in r.path:
                continue
            item = MenuItem(title=r.title, route=r.path, icon=r.icon, perms=r.perms, position=r.menu,
                            any_perm=r.any_perm, badge=r.badge)
            if r.group:
                if r.group not in groups:
                    groups[r.group] = MenuItem(title=r.group, icon=r.group_icon, position=r.menu)
                    items.append(groups[r.group])
                groups[r.group].children.append(item)
            else:
                items.append(item)
        return items + self.extra_menu

    # ------------------------------------------------------------------
    # Ejecución
    # ------------------------------------------------------------------
    def main(self, page: ft.Page):
        AppShell(self, page)

    def run(self, **kwargs):
        if self.assets_dir:
            kwargs.setdefault("assets_dir", str(self.assets_dir))
        ft.run(self.main, **kwargs)

    def _login_builder(self, page: ft.Page):
        from fletbatteries.auth.views import build_login_view
        from fletbatteries.utils import route_query

        shell: AppShell = page.session.store.get(SESSION_SHELL_KEY)
        message = _("Your session has expired. Please log in again.") if route_query(page).get("expired") else None
        on_forgot = (lambda: shell.navigate("/password-reset")) if self.get_route("/password-reset") else None
        return build_login_view(shell.do_login, title=self.title, logo=self.logo, message=message,
                                on_forgot=on_forgot)

    def _password_change_builder(self, page: ft.Page):
        from fletbatteries.auth.views import build_password_change_view

        return build_password_change_view(page, validators=self.password_validators)

    def _password_reset_builder(self, page: ft.Page):
        from fletbatteries.auth.views import build_password_reset_view

        shell: AppShell = page.session.store.get(SESSION_SHELL_KEY)
        return build_password_reset_view(page, on_back=lambda: shell.navigate("/login"), title=self.title)


def shell_of(page: ft.Page) -> "AppShell":
    return page.session.store.get(SESSION_SHELL_KEY)


class AppShell:
    """Estado de una sesión: navbar, sidebar, layout y navegación."""

    def __init__(self, app: FletBatteriesApp, page: ft.Page):
        self.app = app
        self.page = page
        page.session.store.set(SESSION_SHELL_KEY, self)
        page.title = app.title
        page.padding = 0
        if app.fonts:
            page.fonts = app.fonts
        page.theme = app.theme or ft.Theme(color_scheme_seed=ft.Colors.BLUE_GREY_500)
        page.theme_mode = app.theme_mode
        if app.persist_theme:
            self._load_theme()
        if app.auto_login is not None and get_user(page) is None:
            login(page, app.auto_login)

        self.current_route: Optional[Route] = None
        self.breadcrumbs = Breadcrumbs(self.navigate)
        self.sidebar = Sidebar(self.navigate, title=app.sidebar_title)
        actions = []
        self.bell = None
        if app.notifications:
            from fletbatteries.contrib.notifications import NotificationBell

            self.bell = NotificationBell(poll_interval=app.notification_poll_interval, on_navigate=self.navigate)
            actions.append(self.bell)
        self.navbar = Navbar(app.title, self.navigate, on_toggle_sidebar=self.sidebar.toggle,
                             on_logout=self.do_logout if app.login_required else None, logo=app.logo,
                             bgcolor=app.navbar_color, actions=actions)
        self.layout = Layout(self.sidebar, self.breadcrumbs)
        footer = app.footer if app.footer is not None else ft.Container()
        self.footer_links = ft.Row(wrap=True, spacing=4, visible=False, key="footer_menu",
                                   alignment=ft.MainAxisAlignment.CENTER)
        self.container = ft.Column([self.layout, ft.Container(self.footer_links, padding=ft.Padding.symmetric(
            horizontal=10)), footer], expand=True, spacing=0)
        self._menu_user = object()
        self._menu_items: list[MenuItem] = []
        # Expiración de la sesión
        self.logged_at: Optional[datetime.datetime] = None
        self.last_activity: Optional[datetime.datetime] = None
        self._session_task = None
        if get_user(page) is not None:
            self.logged_at = self.last_activity = datetime.datetime.now()
        self._start_session_watch()

        page.on_route_change = lambda e: self.render(e.route)
        start = page.route or app.home
        if app.initial_route and start in ("/", ""):
            start = app.initial_route
        self.render(start, initial=True)

    # ------------------------------------------------------------------
    # Tema
    # ------------------------------------------------------------------
    def _load_theme(self):
        from fletbatteries.contrib.settings import get_setting

        try:
            mode = get_setting("theme.mode")
            color = get_setting("theme.color")
        except Exception:
            log.exception("No se pudo leer el tema guardado")
            return
        if mode:
            self.page.theme_mode = ft.ThemeMode(mode)
        if color:
            self.page.theme = ft.Theme(color_scheme_seed=color, font_family=self.page.theme.font_family)

    # ------------------------------------------------------------------
    # Idioma
    # ------------------------------------------------------------------
    def set_language(self, language: str):
        """Cambia el idioma de esta sesión y vuelve a dibujar la vista actual."""
        set_language(language, self.page)
        self._menu_user = object()
        self.render(self.page.route or self.app.home)

    def set_theme(self, mode: Optional[ft.ThemeMode] = None, color: Optional[str] = None):
        if mode is not None:
            self.page.theme_mode = mode
        if color is not None:
            self.page.theme = ft.Theme(color_scheme_seed=color, font_family=self.page.theme.font_family)
        if self.app.persist_theme:
            from fletbatteries.contrib.settings import set_setting

            if mode is not None:
                set_setting("theme.mode", mode.value)
            if color is not None:
                set_setting("theme.color", color)
        self.page.update()

    # ------------------------------------------------------------------
    # Navegación
    # ------------------------------------------------------------------
    def navigate(self, route: str):
        self.page.navigate(route)

    def _redirect(self, route: str, initial: bool):
        if initial and self.page.route == route:
            self.render(route)
        else:
            self.page.navigate(route)

    def render(self, full_route: str, initial: bool = False):
        if self.session_expired():
            return self.expire_session()
        self.touch()
        parts = urlsplit(full_route or "/")
        path = parts.path or "/"
        query = {k: v[0] for k, v in parse_qs(parts.query).items()}
        route, params = self.app.resolve(path)
        user = get_user(self.page)
        needs_login = self.app.login_required and (route is None or route.login_required is not False)

        if needs_login and user is None:
            if path == "/login":
                return
            target = "/login" + (f"?{urlencode({'next': full_route})}" if path not in ("/", "") else "")
            return self._redirect(target, initial)
        if route is not None and route.path == "/login" and user is not None:
            return self._redirect(query.get("next") or self.app.home, initial)

        self._sync_menu(user)
        if route is None:
            content, title = self._message_view(ft.Icons.SEARCH_OFF, _("Page not found")), _("Page not found")
        elif not has_perms(self.page, route.perms, any_perm=route.any_perm):
            content, title = (self._message_view(ft.Icons.LOCK_OUTLINE, _("You do not have permission to view this "
                                                                           "page.")), route.title)
        else:
            try:
                content = route.builder(self.page, **params) if params else route.builder(self.page)
            except Exception:
                log.exception("Error construyendo la vista %s", path)
                raise
            title = route.title

        self.current_route = route
        if route is not None and not route.layout:
            self.page.controls.clear()
            self.page.appbar = None
            self.page.add(content)
        else:
            if self.container not in self.page.controls:
                self.page.controls.clear()
                self.page.appbar = self.navbar.appbar
                self.page.add(self.container)
            self.refresh_badges()
            self.sidebar.select(route.path if route else None)
            self.breadcrumbs.set_items(self._breadcrumbs(route, title))
            self.layout.update_view(content)
            if self.bell is not None:
                self.bell.refresh()
        self.page.update()

    def _sync_menu(self, user):
        key = (user.id, user.permissions, user.is_superuser) if user else None
        if key == self._menu_user:
            return
        self._menu_user = key
        items = filter_menu(self.app.menu_items(), self.page)
        self._menu_items = items
        self.sidebar.set_items([i for i in items if i.position == "sidebar"])
        self.navbar.set_top_menu([i for i in items if i.position == "top"])
        self._set_footer_menu([i for i in items if i.position == "footer"])
        links = [link for link in self.app.user_links if self.app.get_route(link[1]) is not None]
        self.navbar.set_user(user, self.app.profile_route, links=links, languages=self.app.languages,
                             language=get_language(self.page), on_language=self.set_language)

    def _set_footer_menu(self, items: Sequence[MenuItem]):
        self.footer_links.controls = [
            ft.TextButton(i.title, icon=i.icon, key=f"footer-{i.route}",
                          on_click=lambda e, r=i.route: self.navigate(r))
            for i in items if i.route
        ]
        self.footer_links.visible = bool(self.footer_links.controls)

    def refresh_badges(self):
        """Recalcula los badges del menú (`Route.badge` / `MenuItem.badge`)."""
        from fletbatteries.layout.menu import flatten

        badges = {}
        for item in flatten(self._menu_items):
            if item.badge is not None and item.route:
                badges[item.route] = item.badge_value(self.page)
        self.sidebar.set_badges(badges)

    def _breadcrumbs(self, route: Optional[Route], title: str) -> list:
        home = self.app.get_route(self.app.home)
        crumbs = [(home.title if home else _("Home"), self.app.home)]
        chain = []
        current = route
        while current is not None and current.parent:
            parent = self.app.get_route(current.parent)
            if parent is None:
                break
            chain.insert(0, (parent.title, parent.path))
            current = parent
        crumbs += chain
        if route is None or route.path != self.app.home:
            if route is not None and route.group:
                crumbs.append((route.group, None))
            crumbs.append((title, None))
        return crumbs

    def set_breadcrumbs(self, items: Sequence[tuple[str, Optional[str]]]):
        """Permite que una vista defina sus propios breadcrumbs."""
        self.breadcrumbs.set_items(items)

    def _message_view(self, icon, message: str) -> ft.Control:
        return ft.Container(
            expand=True,
            alignment=ft.Alignment.CENTER,
            content=ft.Column(
                [ft.Icon(icon, size=64, color=ft.Colors.OUTLINE), ft.Text(message, size=18),
                 ft.TextButton(_("Back to home"), on_click=lambda e: self.navigate(self.app.home))],
                tight=True,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

    # ------------------------------------------------------------------
    # Sesión
    # ------------------------------------------------------------------
    def do_login(self, username: str, password: str) -> Optional[str]:
        from fletbatteries.auth.backend import AuthError

        backend = self.app.auth_backend
        if backend is None:
            from fletbatteries.auth.backend import DatabaseAuthBackend

            backend = self.app.auth_backend = DatabaseAuthBackend()
        try:
            user = backend.authenticate(username, password)
        except AuthError as e:
            return str(e)
        if user is None:
            return _("Invalid username or password.")
        login(self.page, user)
        self.logged_at = self.last_activity = datetime.datetime.now()
        query = {k: v[0] for k, v in parse_qs(urlsplit(self.page.route).query).items()}
        self.navigate(query.get("next") or self.app.home)
        return None

    def do_logout(self, route: str = "/login"):
        logout(self.page)
        self.logged_at = self.last_activity = None
        self._menu_user = object()
        self.navigate(route)

    # ------------------------------------------------------------------
    # Expiración de la sesión
    # ------------------------------------------------------------------
    def touch(self):
        """Marca actividad del usuario (cada navegación la marca sola)."""
        if get_user(self.page) is not None:
            now = datetime.datetime.now()
            self.last_activity = now
            if self.logged_at is None:
                self.logged_at = now

    def session_expired(self, now: Optional[datetime.datetime] = None) -> bool:
        if get_user(self.page) is None or not self.app.login_required:
            return False
        now = now or datetime.datetime.now()
        idle, max_age = self.app.session_idle_minutes, self.app.session_max_minutes
        if idle and self.last_activity and now - self.last_activity > datetime.timedelta(minutes=idle):
            return True
        if max_age and self.logged_at and now - self.logged_at > datetime.timedelta(minutes=max_age):
            return True
        return False

    def expire_session(self):
        log.info("Sesión vencida")
        self.do_logout("/login?expired=1")

    def _start_session_watch(self):
        if not (self.app.session_idle_minutes or self.app.session_max_minutes):
            return

        async def watch():
            while True:
                await asyncio.sleep(self.app.session_check_seconds)
                if self.session_expired():
                    self.expire_session()

        try:
            self._session_task = self.page.run_task(watch)
        except Exception:  # noqa: BLE001 - sin loop (p. ej. pruebas síncronas) no se vigila
            log.exception("No se pudo iniciar la vigilancia de la sesión")
