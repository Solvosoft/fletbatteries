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


def option(app, text, root=None):
    """Opción visible de un select con búsqueda (fletbatteries.widgets.selects)."""
    return app.find_one(root=root, where=lambda c: isinstance(c, ft.Container) and str(c.key or "").startswith("option-")
                        and any(t.value == text for t in app.find(type=ft.Text, root=c)))


async def test_login_navigates_home(app):
    await app.fill(app.find_one(key="login_username"), "admin")
    await app.fill(app.find_one(key="login_password"), "incorrecta")
    await app.click(app.find_one(key="login_submit"))
    assert app.page.route == "/login"
    assert app.find_one(key="login_error").value == "Usuario o contraseña incorrectos."

    await app.fill(app.find_one(key="login_password"), "admin")
    await app.click(app.find_one(key="login_submit"))
    assert app.page.route == "/"
    assert app.find(text="Panel")  # sidebar visible
    app.assert_no_errors()


async def test_logout(logged_app):
    app = logged_app
    await app.click(app.find_one(key="logout", visible_only=False))
    assert app.page.route == "/login"
    await app.goto("/customers")
    assert app.page.route == "/login?next=%2Fcustomers"
    app.assert_no_errors()


async def test_sidebar_navigation(logged_app):
    app = logged_app
    await app.click(app.find_one(key="menu-/charts"))
    assert app.page.route == "/charts"
    assert "Charts" in app.all_texts()
    assert app.find_one(key="menu-/charts").selected
    # Breadcrumbs: Inicio › Charts
    crumbs = app.find_one(key="breadcrumbs")
    assert [c.value for c in crumbs.controls if isinstance(c, ft.Text)] == ["Charts"]
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
    await app.click(app.find_one(key="crud_add"))
    assert app.find(text="Agregar producto")

    await app.fill(app.find_one(type=ft.TextField, text="Nombre"), "Café")
    await app.fill(app.find_one(type=ft.TextField, text="Código"), "CAFE-001")
    await app.fill(app.find_one(type=ft.TextField, text="Precio"), "1500")
    await app.click(app.find_one(type=ft.Button, text="Seleccionar imagen"))
    assert app.find(text=f"Seleccionado: {image.name}")
    await app.click(app.find_one(type=ft.Button, text="Guardar"))

    product = ProductManager().first(code="CAFE-001")
    assert product is not None
    assert product.name == "Café" and product.price == 1500
    assert app.find(text="Guardado exitosamente")
    assert app.find(text="Café")  # la tarjeta aparece en la lista
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
        await app.click(app.find_one(type=ft.TextButton, text="Cancelar"))
        assert not app.find(text="Seleccionar color")
    app.assert_no_errors()


async def test_datatable_page_size_and_pagination(logged_app):
    from data.manager.customer_manager import CustomerManager

    cm = CustomerManager()
    for i in range(12):
        cm.create(name=f"Cliente {i:02d}", last_name="Prueba", phone="8888-0000", email=f"cliente{i}@example.com")

    app = logged_app
    await app.goto("/customers")
    info = app.find_one(key="datatable_page_info")
    assert info.value.startswith("1–10 de ")

    await app.select(app.find_one(key="datatable_page_size"), "5")
    assert info.value.startswith("1–5 de ")

    await app.click(icon_button(app, ft.Icons.CHEVRON_RIGHT))
    assert info.value.startswith("6–10 de ")
    app.assert_no_errors()


# ----------------------------------------------------------------------
# Widgets y formularios de fletbatteries
# ----------------------------------------------------------------------
async def test_widgets_catalog_validates(logged_app):
    app = logged_app
    await app.goto("/widgets")
    await app.click(app.find_one(type=ft.Button, text="Validar"))
    result = app.find_one(key="widgets_result")
    assert result.value.startswith("Errores en:")
    assert app.find(text="Este campo es obligatorio.")

    await app.fill(app.find_one(type=ft.TextField, text="Nombre"), "Ana")
    await app.fill(app.find_one(type=ft.TextField, text="Correo"), "ana@example.com")
    await app.fill(app.find_one(type=ft.TextField, text="Edad"), "30")

    # Autocomplete: abrir y elegir una opción
    country = app.find_one(key="country")
    await app.click(country._text_field)
    await app.click(option(app, "Panamá"))
    assert country.value == "pa"

    checkbox = app.find_one(type=ft.Checkbox, text="Acepto los términos")
    app.session.apply_patch(checkbox._i, {"value": True})
    await app.trigger(checkbox, "change")

    await app.click(app.find_one(type=ft.Button, text="Validar"))
    assert result.value.startswith("{"), result.value
    assert '"country": "Panamá"' in result.value
    app.assert_no_errors()


async def test_widgets_mask_and_yes_no(logged_app):
    app = logged_app
    await app.goto("/widgets")
    phone = app.find_one(key="phone")
    await app.fill(phone.field, "88881234")
    assert phone.value == "8888-1234"

    office = app.find_one(key="office", visible_only=False)
    assert office.visible is False  # remote=True oculta la oficina
    switch = app.find_one(key="remote").switch
    app.session.apply_patch(switch._i, {"value": False})
    await app.trigger(switch, "change")
    assert office.visible is True
    app.assert_no_errors()


async def test_widgets_tagging_and_select_with_add(logged_app):
    app = logged_app
    await app.goto("/widgets")
    tags = app.find_one(key="tags")
    await app.fill(tags.input, "flet")
    await app.trigger(tags.input, "submit")
    assert tags.value == ["flet"]

    emails = app.find_one(key="emails")
    await app.fill(emails.input, "no-es-correo")
    await app.trigger(emails.input, "submit")
    assert emails.value == []

    add = app.find_one(key="country_add")
    await app.click(add.add_button)
    assert app.find(text="Agregar País (con +)")
    dialog = dialog_open(app)[-1]
    await app.fill(app.find_one(type=ft.TextField, text="Código", root=dialog), "gt")
    await app.fill(app.find_one(type=ft.TextField, text="Nombre", root=dialog), "Guatemala")
    await app.click(app.find_one(type=ft.Button, text="Guardar"))
    assert add.value == "gt"
    assert ("gt", "Guatemala") in add.choices
    app.assert_no_errors()


async def test_widgets_filtered_select_and_tree(logged_app):
    app = logged_app
    await app.goto("/widgets")
    skills = app.find_one(key="skills")
    await app.click(app.find_one(type=ft.Container, root=skills.available_list,
                                 where=lambda c: isinstance(c.content, ft.Text) and c.content.value == "Python"))
    await app.click(app.find_one(type=ft.IconButton, root=skills, where=lambda c: c.icon == ft.Icons.ARROW_FORWARD))
    assert skills.value == ["py"]

    category = app.find_one(key="category")
    await app.click(app.find_one(type=ft.IconButton, root=category, where=lambda c: c.icon == ft.Icons.CHEVRON_RIGHT))
    web = app.find_one(type=ft.Checkbox, text="Web", root=category)
    app.session.apply_patch(web._i, {"value": True})
    await app.trigger(web, "change")
    assert category.value == "web"
    app.assert_no_errors()


async def test_forms_render_types_and_formset(logged_app):
    app = logged_app
    await app.goto("/forms")
    for render_type in ("plain", "horizontal", "inline", "grid"):
        await app.select(app.find_one(key="render_type"), render_type)
        assert app.find(type=ft.TextField, text="Correo") or render_type == "horizontal"
    app.assert_no_errors()

    await app.click(app.find_one(type=ft.Button, text="Enviar"))
    assert app.find_one(key="forms_result").value == "Hay errores"

    await app.fill(app.find_one(key="first_name").field, "maría")
    await app.fill(app.find_one(key="email").field, "maria@example.com")
    await app.fill(app.find_one(key="form-0-street").field, "Av. Central")
    await app.fill(app.find_one(key="form-0-city").field, "San José")
    await app.click(app.find_one(type=ft.TextButton, text="Agregar elemento"))
    assert app.find(key="form-1-street")
    await app.click(app.find(type=ft.IconButton, where=lambda c: c.icon == ft.Icons.DELETE_OUTLINE)[-1])
    await app.click(app.find_one(type=ft.Button, text="Enviar"))
    assert app.find_one(key="forms_result").value == "OK: María con 1 direcciones"
    app.assert_no_errors()


async def test_autocomplete_search_filters_local_options(logged_app):
    import asyncio

    app = logged_app
    await app.goto("/widgets")
    country = app.find_one(key="country")
    await app.click(country._text_field)
    await app.fill(country._search_field, "pan")
    await asyncio.sleep(0.4)  # debounce de la búsqueda
    await app.settle()
    shown = [t.value for t in app.find(type=ft.Text, root=country._results_list)]
    assert shown == ["Panamá"]
    await app.click(option(app, "Panamá", root=country))
    assert country.value == "pa" and country._text_field.value == "Panamá"
    app.assert_no_errors()


async def test_markdown_preview_toggle(logged_app):
    app = logged_app
    await app.goto("/widgets")
    notes = app.find_one(key="notes")
    await app.click(notes.preview_button)
    assert notes.body.content is notes.preview_box
    assert app.find(text="No hay nada que mostrar")
    await app.click(notes.write_button)
    await app.fill(notes.editor, "# Hola")
    await app.click(notes.preview_button)
    assert notes.preview.value == "# Hola" and notes.preview in notes.preview_box.content.controls
    app.assert_no_errors()

