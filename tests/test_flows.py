import flet as ft

from settings import ASSETS_DIR


def icon_button(app, icon):
    """Botón (Button/IconButton) cuyo ícono es `icon`."""
    def match(c):
        if isinstance(c, ft.IconButton):
            return c.icon == icon
        if isinstance(c, ft.Button):
            return c.icon == icon or (isinstance(c.content, ft.Icon) and c.content.icon == icon)
        return False
    return app.find_one(where=match)


def dialog_open(app):
    return [d for d in app.page._dialogs.controls if d.open]


async def test_login_navigates_home(app):
    await app.fill(app.find_one(type=ft.TextField, text="Username"), "admin")
    await app.click(app.find_one(type=ft.Button, text="Login"))
    assert app.page.route == "/"
    assert app.find(text="Panel")  # sidebar visible
    app.assert_no_errors()


async def test_sidebar_navigation(logged_app):
    app = logged_app
    rail = app.find_one(type=ft.NavigationRail)
    index = [d.data for d in rail.destinations].index("/charts")
    app.session.apply_patch(rail._i, {"selected_index": index})
    await app.trigger(rail, "change", index)
    assert app.page.route == "/charts"
    assert "Charts" in app.all_texts()
    app.assert_no_errors()


async def test_modal_create_validates_and_saves(logged_app):
    app = logged_app
    await app.goto("/modals")
    await app.click(app.find_one(type=ft.Button, text="Agregar"))
    assert app.find(text="Agregar usuario")

    # Sin datos: el callback falla y el diálogo sigue abierto
    await app.click(app.find_one(type=ft.Button, text="Guardar"))
    assert app.find(text="Faltan datos")
    assert app.find(text="Agregar usuario")

    await app.fill(app.find_one(type=ft.TextField, text="Nombre"), "Ana")
    await app.fill(app.find_one(type=ft.TextField, text="Email"), "ana@example.com")
    await app.click(app.find_one(type=ft.Button, text="Guardar"))
    assert app.find(text="Usuario guardado")
    assert not app.find(text="Agregar usuario")
    app.assert_no_errors()


async def test_create_product(logged_app):
    from data.manager.product_manager import ProductManager

    app = logged_app
    image = ASSETS_DIR / "image" / "ejemplo.jpg"
    app.client_methods["pick_files"] = lambda args: [
        {"id": 1, "name": image.name, "path": str(image), "size": image.stat().st_size}
    ]

    await app.goto("/products")
    await app.click(icon_button(app, ft.Icons.ADD))
    assert app.find(text="Agregar Registro de Productos")

    await app.fill(app.find_one(type=ft.TextField, text="Nombre"), "Café")
    await app.fill(app.find_one(type=ft.TextField, text="Código"), "CAFE-001")
    await app.fill(app.find_one(type=ft.TextField, text="Precio"), "1500")
    await app.click(app.find_one(type=ft.Button, text="Seleccionar Imagen"))
    assert app.find(text=f"Seleccionada: {image.name}")
    await app.click(app.find_one(type=ft.Button, text="Guardar"))

    product = ProductManager().get_product_by_code("CAFE-001")
    assert product is not None
    assert product.name == "Café"
    assert app.find(text="Producto guardado")
    app.assert_no_errors()


async def test_calendar_create_event_persists(logged_app):
    from data.manager.calendar_event_manager import CalendarEventManager

    app = logged_app
    await app.goto("/calendar")
    await app.click(icon_button(app, ft.Icons.ADD))
    assert app.find(text="Nuevo evento")

    await app.fill(app.find_one(type=ft.TextField, text="Agregar título"), "Reunión de equipo")
    await app.click(app.find_one(type=ft.FilledButton, text="Guardar"))

    titles = [e["title"] for e in CalendarEventManager().get_all_events()]
    assert "Reunión de equipo" in titles
    assert not app.find(text="Nuevo evento")
    assert app.find(text="Reunión de equipo")  # se dibuja en la grilla
    app.assert_no_errors()


async def test_calendar_week_navigation(logged_app):
    app = logged_app
    await app.goto("/calendar")
    before = app.find_one(where=lambda c: isinstance(c, ft.Text) and c.size == 16).value
    await app.click(icon_button(app, ft.Icons.ARROW_FORWARD))
    await app.click(icon_button(app, ft.Icons.ARROW_FORWARD))
    await app.click(icon_button(app, ft.Icons.ARROW_FORWARD))
    await app.click(icon_button(app, ft.Icons.ARROW_FORWARD))
    await app.click(icon_button(app, ft.Icons.ARROW_FORWARD))
    after = app.find_one(where=lambda c: isinstance(c, ft.Text) and c.size == 16).value
    assert before != after
    app.assert_no_errors()


async def test_color_picker_changes_theme(logged_app):
    app = logged_app
    await app.goto("/settings")
    await app.click(app.find_one(key="color_picker_button"))
    assert app.find(text="Seleccionar color")

    await app.click(app.find_one(key="swatch_#E53935"))
    assert app.find_one(key="color_picker_hex").value == "#E53935"

    # Valor hexadecimal inválido muestra error y no cambia el color
    hex_field = app.find_one(key="color_picker_hex")
    await app.fill(hex_field, "#12")
    assert hex_field.error

    await app.fill(hex_field, "#00897B")
    await app.click(app.find_one(key="color_picker_ok"))
    assert not app.find(text="Seleccionar color")
    assert app.page.theme.color_scheme_seed == "#00897B"
    app.assert_no_errors()


async def test_theme_mode_switch(logged_app):
    app = logged_app
    await app.goto("/settings")
    switch = app.find_one(type=ft.Switch)
    app.session.apply_patch(switch._i, {"value": True})
    await app.trigger(switch, "change")
    assert app.page.theme_mode == ft.ThemeMode.DARK
    app.assert_no_errors()


async def test_calendar_edit_and_delete_event(logged_app):
    from data.manager.calendar_event_manager import CalendarEventManager

    app = logged_app
    await app.goto("/calendar")
    await app.click(icon_button(app, ft.Icons.ADD))
    await app.fill(app.find_one(type=ft.TextField, text="Agregar título"), "Evento editable")
    await app.click(app.find_one(type=ft.FilledButton, text="Guardar"))

    # Abrir el evento desde la grilla y cambiar el título
    event_box = app.find_one(where=lambda c: isinstance(c, ft.Container) and isinstance(c.content, ft.Text)
                             and c.content.value == "Evento editable" and c.on_click is not None)
    await app.click(event_box)
    assert app.find(text="Editar evento")
    await app.fill(app.find_one(type=ft.TextField, text="Agregar título"), "Evento editado")
    await app.click(app.find_one(type=ft.FilledButton, text="Guardar"))

    events = {e["title"]: e for e in CalendarEventManager().get_all_events()}
    assert "Evento editado" in events and "Evento editable" not in events

    # Eliminar
    event_box = app.find_one(where=lambda c: isinstance(c, ft.Container) and isinstance(c.content, ft.Text)
                             and c.content.value == "Evento editado" and c.on_click is not None)
    await app.click(event_box)
    await app.click(app.find_one(where=lambda c: isinstance(c, ft.CupertinoButton) and c.icon == ft.Icons.DELETE))
    titles = [e["title"] for e in CalendarEventManager().get_all_events()]
    assert "Evento editado" not in titles
    assert not app.find(text="Evento editado")
    app.assert_no_errors()


async def test_color_picker_can_reopen(logged_app):
    app = logged_app
    await app.goto("/settings")
    for _ in range(2):
        await app.click(app.find_one(key="color_picker_button"))
        assert app.find(text="Seleccionar color")
        await app.click(app.find_one(type=ft.TextButton, text="Cancel"))
        assert not app.find(text="Seleccionar color")
    app.assert_no_errors()


async def test_datatable_page_size_and_pagination(logged_app):
    from data.manager.customer_manager import CustomerManager

    cm = CustomerManager()
    for i in range(12):
        cm.create_customer(f"Cliente {i:02d}", "Prueba", "8888-0000", f"cliente{i}@example.com")

    app = logged_app
    await app.goto("/customers")
    info = app.find_one(where=lambda c: isinstance(c, ft.Text) and isinstance(c.value, str) and " de " in c.value)
    assert info.value.startswith("1–10 de ")

    dropdown = app.find_one(type=ft.Dropdown)
    await app.select(dropdown, "5")
    assert info.value.startswith("1–5 de ")

    await app.click(icon_button(app, ft.Icons.CHEVRON_RIGHT))
    assert info.value.startswith("6–10 de ")
    app.assert_no_errors()
