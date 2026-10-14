from typing import Callable, Optional, Sequence

import flet as ft

from fletbatteries.i18n import _
from fletbatteries.layout.menu import MenuItem


class Navbar:
    """AppBar con botón de menú, logo, título, menú superior, campana y menú de usuario."""

    def __init__(self, title: str, on_navigate: Callable[[str], None], on_toggle_sidebar=None,
                 on_logout=None, logo: Optional[str] = None, bgcolor=ft.Colors.LIGHT_BLUE_ACCENT_700,
                 color=ft.Colors.WHITE, actions: Sequence[ft.Control] = ()):
        self.on_navigate = on_navigate
        self.on_logout = on_logout
        self.color = color
        self.user_menu = ft.PopupMenuButton(icon=ft.Icons.ACCOUNT_CIRCLE, icon_color=color, items=[],
                                            key="user_menu", visible=False)
        self.top_menu = ft.PopupMenuButton(icon=ft.Icons.MORE_VERT, icon_color=color, items=[], key="top_menu",
                                           visible=False)
        title_controls = []
        if logo:
            title_controls.append(ft.Image(src=logo, width=32, height=32))
        title_controls.append(ft.Text(title, size=24, color=color))
        self.appbar = ft.AppBar(
            leading=ft.IconButton(icon=ft.Icons.MENU, icon_color=color, on_click=on_toggle_sidebar, key="menu_toggle"),
            leading_width=72,
            title=ft.Row(title_controls, vertical_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
            center_title=False,
            toolbar_height=72,
            bgcolor=bgcolor,
            actions=[*actions, self.top_menu, self.user_menu, ft.Container(width=12)],
        )

    def set_top_menu(self, items: Sequence[MenuItem]):
        self.top_menu.items = [
            ft.PopupMenuItem(content=i.title, icon=i.icon, data=i.route,
                             on_click=lambda e, r=i.route: self.on_navigate(r))
            for i in items
        ]
        self.top_menu.visible = bool(items)

    def set_user(self, user, profile_route: Optional[str] = None, links: Sequence[tuple] = (),
                 languages: Sequence[tuple] = (), language: Optional[str] = None, on_language=None):
        """
        Menú de usuario: perfil, `links` extra `(título, ruta, ícono)`, selector
        de idioma (`languages=[("es", "Español"), ...]`) y salir.
        """
        if user is None and not languages:
            self.user_menu.visible = False
            self.user_menu.items = []
            return
        items = []
        if user is not None:
            items.append(ft.PopupMenuItem(content=user.display_name, icon=ft.Icons.PERSON,
                                          disabled=profile_route is None,
                                          on_click=(lambda e: self.on_navigate(profile_route)) if profile_route
                                          else None))
            for title, route, icon in links:
                items.append(ft.PopupMenuItem(content=title, icon=icon, key=f"user-menu-{route}",
                                              on_click=lambda e, r=route: self.on_navigate(r)))
        if languages and on_language is not None:
            items.append(ft.PopupMenuItem())  # separador
            for code, label in languages:
                items.append(ft.PopupMenuItem(content=label, checked=code == language, key=f"language-{code}",
                                              on_click=lambda e, c=code: on_language(c)))
        if user is not None and self.on_logout:
            if languages:
                items.append(ft.PopupMenuItem())
            items.append(ft.PopupMenuItem(content=_("Logout"), icon=ft.Icons.LOGOUT, key="logout",
                                          on_click=lambda e: self.on_logout()))
        self.user_menu.items = items
        self.user_menu.icon = ft.Icons.ACCOUNT_CIRCLE if user is not None else ft.Icons.LANGUAGE
        self.user_menu.visible = True
