import flet as ft
from components.layout.navbar import Navbar
from components.layout.layout import Layout
from components.layout.footer import Footer
from controls.router.views import Views
from controls.router.router import router
from components.shared.form import GenerateForms
from settings import ASSETS_DIR, SKIP_LOGIN


class AppTemplate:
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = "FletBatteries"
        self.page.padding = 0
        self.page.theme_mode = ft.ThemeMode.LIGHT
        self.page.theme = ft.Theme(
            font_family="Verdana",
            color_scheme_seed=ft.Colors.BLUE_GREY_500,
            page_transitions=ft.PageTransitionsTheme(windows=ft.PageTransitionTheme.CUPERTINO),
        )
        self.page.fonts = {"Pacifico": "fonts/Pacifico-Regular.ttf"}
        self.generate_forms = GenerateForms(self.page)
        self.forms = self.generate_forms.generate_forms()
        self.views = Views(page=self.page, forms=self.forms).views
        self.navbar = Navbar(page, settings=self.navbar_settings())
        self.layout = Layout(self.navbar, page, self.views)
        self.footer = Footer()
        self.layout_container = self.create_layout()
        self.page.add(self.layout_container)
        self.build_view()

    def create_layout(self):
        return ft.Column(
            controls=[
                self.layout,
                self.footer
            ],
            expand=True,
            alignment=ft.MainAxisAlignment.START,
        )

    def build_view(self):
        self.page.on_route_change = lambda e: router(self, e.route, self.views)
        # Respeta la ruta inicial (p. ej. una URL abierta directamente en modo web);
        # si no corresponde a ninguna vista se inicia en el login
        routes = {v.route for v in self.views}
        if not SKIP_LOGIN:
            routes.discard("/")
        initial = self.page.route if self.page.route in routes else "/login"
        if self.page.route == initial:
            router(self, initial, self.views)
        else:
            self.page.navigate(initial)

    def navbar_settings(self):
        return {
            "title": "FletBatteries",
            "logo": "image/icon.png",
            "color_bg": ft.Colors.LIGHT_BLUE_ACCENT_700,
            "color_text": ft.Colors.WHITE,
            "items": [
                ft.PopupMenuItem(content=v.name, data=v.route, icon=v.icon, on_click=self.redirect_navbar)
                for v in self.views if v.position == 0
            ]
        }

    def redirect_navbar(self, e):
        self.page.navigate(e.control.data)


def main(page: ft.Page):
    AppTemplate(page)


if __name__ == "__main__":
    ft.run(main, assets_dir=str(ASSETS_DIR))
