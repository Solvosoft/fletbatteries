import flet as ft
from components.layout.navbar import Navbar
from components.layout.layout import Layout
from components.layout.footer import Footer


def router(self, route, views):
    # Busca en la lista de vistas la que coincida con la ruta actual; si no encuentra ninguna, usa la primera por defecto

    content = next((v.view for v in views if v.route == route), views[0].view)

    # Limpia todos los controles actuales de la página
    if route == "/login" :
        self.page.controls.clear()
        self.page.appbar = None
        self.page.floating_action_button = None
        self.page.add(content)
    else:
        if not hasattr(self, "layout_container"):
            self.navbar = Navbar(self.page, settings=self.navbar_settings())
            self.page.appbar = self.navbar.appbar
            self.layout = Layout(self.navbar, self.page, self.layout_settings())
            self.layout_container = self.create_layout()
            self.page.controls.clear()
            self.page.appbar = self.navbar.appbar
            self.page.add(self.layout_container)


        elif self.layout_container not in self.page.controls:
            self.page.controls.clear()
            self.page.appbar = self.navbar.appbar
            self.page.add(self.layout_container)


        self.layout.update_view(content)

    # Actualiza el contenido de la página
    # Actualiza la interfaz de la página para reflejar los cambios
    self.page.update()
