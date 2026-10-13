def router(self, route, views):
    # Busca en la lista de vistas la que coincida con la ruta actual; si no encuentra ninguna, usa la primera por defecto
    rv = next((v for v in views if v.route == route), views[0])

    content = rv.builder()

    # Limpia todos los controles actuales de la página
    if route == "/login":
        self.page.controls.clear()
        self.page.appbar = None
        self.page.floating_action_button = None
        self.page.add(content)
    else:
        if self.layout_container not in self.page.controls:
            self.page.controls.clear()
            self.page.appbar = self.navbar.appbar
            self.page.add(self.layout_container)

        self.layout.update_view(content)

    # Actualiza la interfaz de la página para reflejar los cambios
    self.page.update()
