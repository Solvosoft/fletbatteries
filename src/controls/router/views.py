
import flet as ft
import typing as t

from dataclasses import dataclass
from views.home_view import build_view_home
from views.login_view import build_view_login
from views.settings_view import build_view_settings
from views.product_view import ProductView
from views.customer_view import build_view_customer
from views.user_view import UserView
from views.profile_view import build_view_profile
from views.spinner_view import build_view_spinner
from views.modals_view import build_view_modals
from views.fontawesome_view import build_view_fontawesome
from views.animation_view import build_view_animation
from views.friconix_view import build_view_friconix
from views.charts_view import build_view_charts
from views.test_view import TestView
from views.autocompletes_view import build_view_autocompletes
from views.autocompletes_related_view import build_view_autocompletes_related
from assets.icons.friconix.frx_flet import frx_icon


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
            RouteView("Users", "/users", ft.Icons.PERSON, lambda:UserView(page, forms).build_view_user(), position["side"]),
            RouteView("Customer", "/customers", ft.Icons.SUPERVISED_USER_CIRCLE, lambda:build_view_customer(page, forms), position["side"]),
            RouteView("Spinner", "/spinner", ft.Icons.CALL_TO_ACTION, lambda:build_view_spinner(page), position["side"]),
            RouteView("Modals", "/modals", ft.Icons.SELECT_ALL, lambda:build_view_modals(page), position["side"]),
            RouteView("Fontawesome", "/fontawesome", ft.Icons.NOW_WALLPAPER, lambda:build_view_fontawesome(page), position["side"]),
            RouteView("Friconix", "/friconix", ft.Icons.NOW_WALLPAPER, lambda:build_view_friconix(page), position["side"]),
            RouteView("Charts", "/charts", ft.Icons.DONUT_SMALL_ROUNDED, lambda:build_view_charts(page), position["side"]),
            RouteView("Animations", "/animations", ft.Icons.SPORTS_HANDBALL_ROUNDED, lambda:build_view_animation(page), position["side"]),
            RouteView("Login", "/login", ft.Icons.LOGIN, lambda:build_view_login(page), position["top"]),
            RouteView("Profile", "/profile", ft.Icons.PERSON, lambda:build_view_profile(page), position["top"]),
            RouteView("Settings", "/settings", ft.Icons.SETTINGS, lambda:build_view_settings(page), position["top"]),
            RouteView("Test", "/test", ft.Icons.QUESTION_MARK, lambda:TestView(page, forms).build_view_test(), position["side"]),
            RouteView("Autocomplete", "/autocompletes", ft.Icons.EXPAND_MORE,  lambda: build_view_autocompletes(page, forms), position["side"]),
            RouteView("Autocomplete related", "/autocomplete_related", ft.Icons.UNFOLD_MORE, lambda: build_view_autocompletes_related(page), position["side"]),
        ]