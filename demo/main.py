import flet as ft

from fletbatteries.app import FletBatteriesApp
from fletbatteries.auth import AuthUser
from fletbatteries.layout import Footer

from controls.router.views import register_views
from settings import ASSETS_DIR, SKIP_LOGIN

app = FletBatteriesApp(
    title="FletBatteries",
    logo="image/icon.png",
    sidebar_title="Panel",
    theme=ft.Theme(
        font_family="Verdana",
        color_scheme_seed=ft.Colors.BLUE_GREY_500,
        page_transitions=ft.PageTransitionsTheme(windows=ft.PageTransitionTheme.CUPERTINO),
    ),
    fonts={"Pacifico": "fonts/Pacifico-Regular.ttf"},
    persist_theme=True,
    notifications=True,
    profile_route="/profile",
    # Permite abrir cualquier ruta sin pasar por el login (capturas/demos)
    auto_login=AuthUser(id=0, username="demo", is_superuser=True) if SKIP_LOGIN else None,
    footer=Footer("© 2025 Solvo", logo="image/icon.png", links=[("Solvo", "https://solvosoft.com/es/")]),
    assets_dir=ASSETS_DIR,
)
register_views(app)


def main(page: ft.Page):
    app.main(page)


if __name__ == "__main__":
    app.run()
