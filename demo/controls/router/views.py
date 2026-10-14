"""Registro de las vistas de la demo en la app de fletbatteries."""

import flet as ft

from views.animation_view import build_view_animation
from views.autocompletes_related_view import build_view_autocompletes_related
from views.autocompletes_view import build_view_autocompletes
from views.calendar_view import build_view_calendar
from views.charts_view import build_view_charts
from views.customer_view import build_view_customer, build_view_customer_detail
from views.fontawesome_view import build_view_fontawesome
from views.forms_view import build_view_forms
from views.friconix_view import build_view_friconix
from views.home_view import build_view_home
from views.modals_view import build_view_modals
from views.notes_view import NoteCRUD, build_view_maps, notes_badge
from views.product_view import build_view_product
from views.profile_view import build_view_profile
from views.settings_view import build_view_settings
from views.spinner_view import build_view_spinner
from views.test_view import build_view_test
from views.user_view import build_view_user
from views.widgets_view import build_view_widgets
from views.wizard_view import build_view_wizard

ADMIN = "Administración"


def register_views(app):
    app.add_view("/", build_view_home, title="Inicio", icon=ft.Icons.HOME)
    app.add_view("/products", build_view_product, title="Products", icon=ft.Icons.LOCAL_MALL)
    app.add_view("/users", build_view_user, title="Users", icon=ft.Icons.PERSON)
    app.add_view("/customers", build_view_customer, title="Customer", icon=ft.Icons.SUPERVISED_USER_CIRCLE)
    app.add_view("/customers/:id", build_view_customer_detail, title="Detalle del cliente", menu=None,
                 parent="/customers")
    app.add_view("/spinner", build_view_spinner, title="Spinner", icon=ft.Icons.CALL_TO_ACTION)
    app.add_view("/modals", build_view_modals, title="Modals", icon=ft.Icons.SELECT_ALL)
    app.add_view("/fontawesome_icons", build_view_fontawesome, title="Fontawesome", icon=ft.Icons.NOW_WALLPAPER)
    app.add_view("/friconix", build_view_friconix, title="Friconix", icon=ft.Icons.NOW_WALLPAPER)
    app.add_view("/charts", build_view_charts, title="Charts", icon=ft.Icons.DONUT_SMALL_ROUNDED)
    app.add_view("/rive_animations", build_view_animation, title="Animations", icon=ft.Icons.SPORTS_HANDBALL_ROUNDED)
    app.add_view("/calendar", build_view_calendar, title="Calendar", icon=ft.Icons.CALENDAR_MONTH)
    app.add_view("/test", build_view_test, title="Test", icon=ft.Icons.QUESTION_MARK)
    app.add_view("/autocompletes", build_view_autocompletes, title="Autocomplete", icon=ft.Icons.EXPAND_MORE)
    app.add_view("/autocomplete_related", build_view_autocompletes_related, title="Autocomplete related",
                 icon=ft.Icons.UNFOLD_MORE)
    app.add_view("/widgets", build_view_widgets, title="Widgets", icon=ft.Icons.WIDGETS)
    app.add_view("/forms", build_view_forms, title="Forms", icon=ft.Icons.DYNAMIC_FORM)
    app.add_crud(NoteCRUD, title="Notas", icon=ft.Icons.STICKY_NOTE_2, badge=notes_badge)
    app.add_view("/wizard", build_view_wizard, title="Wizard", icon=ft.Icons.LINEAR_SCALE)
    app.add_view("/maps", build_view_maps, title="Mapa", icon=ft.Icons.MAP)

    # Vistas del framework: administración (permiso auth.manage; el superusuario lo tiene) y cuenta
    app.add_admin_views(group=ADMIN)
    app.add_account_views(password_reset=True)

    # Menú superior
    app.add_view("/profile", build_view_profile, title="Profile", icon=ft.Icons.PERSON, menu="top")
    app.add_view("/settings", build_view_settings, title="Settings", icon=ft.Icons.SETTINGS, menu="top")
