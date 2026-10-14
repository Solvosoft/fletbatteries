import logging
import os

import flet as ft

from fletbatteries.app import FletBatteriesApp
from fletbatteries.auth import AuthUser
from fletbatteries.layout import Footer

from controls.router.views import register_views
from settings import ASSETS_DIR, INITIAL_ROUTE, SKIP_LOGIN

# FLETBATTERIES_LOG_FILE=/ruta.log guarda el log de Python (útil en la app compilada, que no tiene consola)
if os.environ.get("FLETBATTERIES_LOG_FILE"):
    import faulthandler

    logging.basicConfig(filename=os.environ["FLETBATTERIES_LOG_FILE"], level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    faulthandler.enable(open(os.environ["FLETBATTERIES_LOG_FILE"] + ".fault", "w"))

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
    initial_route=INITIAL_ROUTE,
    languages=[("es", "Español"), ("en", "English")],
)
register_views(app)


def main(page: ft.Page):
    logging.getLogger("demo").info("Nueva sesión: route=%s platform=%s", page.route, page.platform)
    app.main(page)


if __name__ == "__main__":
    app.run()
