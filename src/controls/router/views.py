
import flet as ft
import typing as t

from dataclasses import dataclass
from views.home_view import build_view_home
from views.login import build_view_login
from views.settings_view import build_view_settings
from views.product_view import ProductView
from views.customer_view import build_view_customer
from views.user_view import build_view_user
from views.profile import build_view_profile


position = {
    "top": 0,
    "side": 1,
    "bottom": 2,
}

@dataclass
class RouteView:
    name: str
    route: str
    icon: str
    builder: t.Callable[[], ft.Control]
    position: int

class Views:
    def __init__(self, page, forms):
        self.views = [
            RouteView("Inicio", "/", ft.Icons.HOME, lambda:build_view_home(page), position["side"]),
            RouteView("Products", "/products", ft.Icons.LOCAL_MALL, lambda:ProductView(page, forms).build_view_product(), position["side"]),
            RouteView("Users", "/users", ft.Icons.PERSON, lambda:build_view_user(page), position["side"]),
            RouteView("Customer", "/customers", ft.Icons.SUPERVISED_USER_CIRCLE, lambda:build_view_customer(page), position["side"]),
            RouteView("Login", "/login", ft.Icons.LOGIN, lambda:build_view_login(page), position["top"]),
            RouteView("Profile", "/profile", ft.Icons.PERSON, lambda:build_view_profile(page), position["top"]),
            RouteView("Settings", "/settings", ft.Icons.SETTINGS, lambda:build_view_settings(page), position["top"]),
        ]
