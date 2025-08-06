import flet as ft
from components.layout.navbar import Navbar
from components.layout.layout import Layout
from components.layout.footer import Footer
from controls.router.views import Views
from controls.router.router import router


class AppTemplate(ft.Container):
    def __init__(self, page):
        super().__init__()
        self.page = page
        self.page.title = "Template"
        self.page.padding = 0
        self.page.theme_mode = ft.ThemeMode.LIGHT
        self.page.theme = ft.Theme(font_family="Verdana", color_scheme_seed=ft.Colors.BLUE_GREY_500)
        self.page.theme.page_transitions.windows = ft.PageTransitionTheme.CUPERTINO
        self.page.fonts = {"Pacifico": "./fonts/Pacifico-Regular.ttf"}

        self.views = Views(page=self.page).views
        self.navbar = Navbar(page, settings=self.navbar_settings())
        self.layout = Layout(self.navbar, page, self.layout_settings())
        self.footer = Footer()
        self.layout_container = self.create_layout()
        self.page.add(self.create_layout())
        self.page.add(self.layout_container)
        page.update()
        self.build_view()

    def create_layout(self):
        return ft.Column(
            controls=[
                self.layout,
                self.footer
            ],
            expand=True,
            alignment=ft.alignment.top_center,
        )

    def build_view(self):
        self.page.on_route_change = lambda r: router(self, self.page.route, self.views)
        self.page.go("/login")

    def navbar_settings(self):
        return {
            "title": "Template",
            "logo": "assets/image/icon.png",
            "color_bg": ft.Colors.LIGHT_BLUE_ACCENT_700,
            "color_text": ft.Colors.WHITE,
            "items": [
                ft.PopupMenuItem(text=v.name, data=v.route, icon=v.icon, on_click=lambda e: self.redirect_navbar(e))
                for v in self.views if v.position == 0
            ]
        }

    def redirect_navbar(self, e):
        self.page.go(e.control.data)

    def layout_settings(self):
        return {

        }
    
if __name__ == "__main__":
    ft.app(target=AppTemplate, assets_dir="src/assets")