"""Pruebas de la capa de datos (BaseManager, DataSource), del router REST y de CRUDView."""

import datetime

import flet as ft
import pytest

from fletbatteries.data import APISource, BaseManager, ListSource, Query, SQLAlchemySource
from tests.test_flows import dialog_open, option


# ----------------------------------------------------------------------
# BaseManager
# ----------------------------------------------------------------------
@pytest.fixture
def customers():
    from data.manager.customer_manager import CustomerManager

    cm = CustomerManager()
    created = [
        cm.create(name=name, last_name=last, email=f"{name.lower()}.{last.lower()}@crud.test", phone=phone)
        for name, last, phone in [
            ("Ana", "Mora", "8888-0001"),
            ("Beto", "Rojas", "8888-0002"),
            ("Carla", "Mora", "8888-0003"),
            ("Diego", "Solís", "8888-0004"),
        ]
    ]
    yield cm, created
    for c in created:
        cm.delete(c.id)


def test_manager_list_search_filter_order(customers):
    cm, created = customers
    base = {"email__icontains": "@crud.test"}
    page = cm.list(Query(page=1, size=2, filters=base, order_by="-name"))
    assert page.total == 4 and page.pages == 2 and page.has_next
    assert [c.name for c in page.items] == ["Diego", "Carla"]

    assert [c.name for c in cm.list(search="mora", filters=base, order_by="name").items] == ["Ana", "Carla"]
    assert cm.count(last_name="Mora", email__icontains="@crud.test") == 2
    assert {c.name for c in cm.filter(name__in=["Ana", "Beto"])} == {"Ana", "Beto"}
    assert cm.first(email="beto.rojas@crud.test").name == "Beto"
    with pytest.raises(ValueError, match="no tiene el campo"):
        cm.list(filters={"nope": 1})
    with pytest.raises(ValueError, match="Operador"):
        cm.list(filters={"name__regex": "x"})


def test_manager_unique_fields_and_update(customers):
    cm, created = customers
    with pytest.raises(ValueError, match="Ya existe"):
        cm.create(name="Otra", email=created[0].email)
    with pytest.raises(ValueError, match="Ya existe"):
        cm.update(created[1].id, email=created[0].email)
    # Guardar el mismo correo en el mismo registro no es duplicado
    assert cm.update(created[0].id, email=created[0].email, phone="1111-2222").phone == "1111-2222"
    with pytest.raises(ValueError, match="no encontrado"):
        cm.update(999999, name="x")


def test_manager_relationships():
    from data.manager.country_manager import CountryManager
    from data.manager.person_group_manager import PersonGroupManager
    from data.manager.person_manager import PersonManager

    country = CountryManager().create(name="País relación")
    people = [PersonManager().create(name=f"Rel {i}") for i in range(3)]
    gm = PersonGroupManager()
    group = gm.create(name="Grupo relación", country_id=country.id, people=[p.id for p in people[:2]])
    assert {p.name for p in group.people} == {"Rel 0", "Rel 1"}
    assert group.country.name == "País relación"
    data = gm.to_dict(group)
    assert sorted(data["people"]) == sorted(p.id for p in people[:2])

    group = gm.update(group.id, people=[people[2].id])
    assert [p.name for p in group.people] == ["Rel 2"]
    assert gm.delete(group.id)
    # Borrar el grupo no borra a las personas (solo la relación)
    assert PersonManager().get(people[2].id) is not None


def test_manager_date_range_filter():
    from data.manager.calendar_event_manager import CalendarEventManager

    m = CalendarEventManager()
    ev = m.create(title="Rango", start_time=datetime.datetime(2031, 5, 10, 9), end_time=datetime.datetime(2031, 5, 10, 10))
    found = m.filter(start_time__range=(datetime.date(2031, 5, 10), datetime.date(2031, 5, 10)))
    assert [e.title for e in found] == ["Rango"]
    m.delete(ev.id)


# ----------------------------------------------------------------------
# DataSources
# ----------------------------------------------------------------------
def test_list_source():
    src = ListSource([{"id": 1, "name": "Ángel", "age": 30}, {"id": 2, "name": "Bea", "age": 20}])
    assert src.list(Query(search="angel")).total == 1
    assert [i["name"] for i in src.list(Query(order_by="age")).items] == ["Bea", "Ángel"]
    assert src.list(Query(filters={"age__gte": 25})).items[0]["id"] == 1
    created = src.create({"name": "Carlos"})
    assert created["id"] == 3 and src.label_for(3) == "Carlos"
    assert src.update(3, {"name": "Carla"})["name"] == "Carla"
    assert src.delete(3) and not src.delete(3)
    lookup = src.lookup(skip=0, limit=1, q="")
    assert list(lookup["results"]) == ["1"] and lookup["pagination"]["more"] is True
    assert src.lookup(skip=1, limit=1)["pagination"]["more"] is False


def test_sqlalchemy_source(customers):
    cm, created = customers
    src = SQLAlchemySource(cm, fixed_filters={"last_name": "Mora"})
    page = src.list(Query(size=10))
    assert {i["name"] for i in page.items} == {"Ana", "Carla"}
    assert src.label_for(created[0].id) == "Ana"
    assert src.label_for(999999) is None
    lookup = src.lookup(q="car")
    assert [r["text"] for r in lookup["results"].values()] == ["Carla"]
    # Lo creado con una fuente fija hereda el filtro
    new = src.create({"name": "Elena", "email": "elena@crud.test"})
    assert new["last_name"] == "Mora"
    cm.delete(new["id"])


def test_api_router_and_api_source(api_client, customers):
    cm, created = customers
    resp = api_client.get("/api/customers", params={"email__icontains": "@crud.test", "order_by": "name", "size": 3})
    body = resp.json()
    assert resp.status_code == 200 and body["total"] == 4 and len(body["items"]) == 3
    assert api_client.get("/api/customers", params={"last_name__in": "Mora,Rojas",
                                                    "email__icontains": "@crud.test"}).json()["total"] == 3
    assert api_client.get("/api/customers/999999").status_code == 404
    assert api_client.post("/api/customers", json={"name": "Sin correo"}).status_code == 422

    src = APISource("http://testserver/api/customers")
    page = src.list(Query(search="mora", filters={"email__icontains": "@crud.test"}, order_by="-name"))
    assert [i["name"] for i in page.items] == ["Carla", "Ana"]
    new = src.create({"name": "Fabio", "email": "fabio@crud.test"})
    assert src.get(new["id"])["name"] == "Fabio"
    assert src.update(new["id"], {"phone": "7777-0000"})["phone"] == "7777-0000"
    with pytest.raises(ValueError):
        src.create({"name": "Repetido", "email": "fabio@crud.test"})
    assert src.label_for(new["id"]) == "Fabio"
    lookup = src.lookup(q="fabio")
    assert [r["text"] for r in lookup["results"].values()] == ["Fabio"]
    assert src.delete(new["id"]) is True
    assert src.delete(new["id"]) is False


def test_api_relationships(api_client):
    countries = api_client.get("/api/countries", params={"size": 1}).json()["items"]
    persons = api_client.get("/api/persons", params={"size": 2}).json()["items"]
    created = api_client.post("/api/person_groups", json={
        "name": "Grupo API", "country_id": countries[0]["id"], "people": [p["id"] for p in persons],
    })
    assert created.status_code == 201, created.text
    group = created.json()
    assert sorted(group["people"]) == sorted(p["id"] for p in persons)
    updated = api_client.put(f"/api/person_groups/{group['id']}", json={"people": []}).json()
    assert updated["people"] == [] and updated["name"] == "Grupo API"
    assert api_client.delete(f"/api/person_groups/{group['id']}").json() == {"deleted": True}


# ----------------------------------------------------------------------
# CRUDView (flujos en la app)
# ----------------------------------------------------------------------
async def test_customer_crud_flow(logged_app):
    from data.manager.customer_manager import CustomerManager

    app = logged_app
    await app.goto("/customers")

    # Crear: primero sin datos (errores en el formulario, el diálogo sigue abierto)
    await app.click(app.find_one(key="crud_add"))
    assert app.find(text="Agregar cliente")
    await app.click(app.find_one(type=ft.Button, text="Guardar"))
    assert app.find_one(key="name").error == "Este campo es obligatorio."
    assert dialog_open(app)

    await app.fill(app.find_one(key="name").field, "Zoe")
    await app.fill(app.find_one(key="last_name").field, "Vargas")
    await app.fill(app.find_one(key="email").field, "zoe@flow.test")
    await app.fill(app.find_one(key="phone").field, "60001234")
    await app.click(app.find_one(type=ft.Button, text="Guardar"))
    assert app.find(text="Guardado exitosamente")
    zoe = CustomerManager().first(email="zoe@flow.test")
    assert zoe.phone == "6000-1234"

    # Buscar
    await app.fill(app.find_one(key="datatable_search"), "zoe@flow")
    assert app.find(text="Zoe") and app.find(key=f"edit-{zoe.id}")

    # Correo duplicado: error general en el formulario
    await app.click(app.find_one(key="crud_add"))
    await app.fill(app.find_one(key="name").field, "Otra")
    await app.fill(app.find_one(key="last_name").field, "Persona")
    await app.fill(app.find_one(key="email").field, "zoe@flow.test")
    await app.click(app.find_one(type=ft.Button, text="Guardar"))
    assert app.find(contains="Ya existe un registro")
    await app.click(app.find_one(type=ft.TextButton, text="Cancelar"))

    # Editar
    await app.click(app.find_one(key=f"edit-{zoe.id}"))
    assert app.find(text="Editar cliente")
    assert app.find_one(key="name").value == "Zoe"
    await app.fill(app.find_one(key="name").field, "Zoé")
    await app.click(app.find_one(type=ft.Button, text="Actualizar"))
    assert CustomerManager().get(zoe.id).name == "Zoé"
    assert app.find(text="Zoé")

    # Detalle
    await app.click(app.find_one(key=f"detail-{zoe.id}"))
    assert app.find(text="Detalle de cliente") and app.find(text="zoe@flow.test")
    await app.click(app.find_one(type=ft.TextButton, text="Cerrar"))

    # Eliminar
    await app.click(app.find_one(key=f"delete-{zoe.id}"))
    await app.click(app.find_one(type=ft.Button, text="Eliminar"))
    assert CustomerManager().get(zoe.id) is None
    assert app.find(text="No hay registros")
    app.assert_no_errors()


async def test_customer_filters_sort_and_selection(logged_app, customers):
    cm, created = customers
    app = logged_app
    await app.goto("/customers")
    table = app.find_one(where=lambda c: type(c).__name__ == "DataTable" and hasattr(c, "source"))

    await app.click(app.find_one(type=ft.IconButton, where=lambda c: c.icon == ft.Icons.FILTER_LIST))
    filter_form = table.filter_form
    await app.fill(filter_form["email"].field, "@crud.test")
    await app.fill(filter_form["name"].field, "a")
    await app.click(app.find_one(key="datatable_apply_filters"))
    assert table.filters == {"email__icontains": "@crud.test", "name__icontains": "a"}
    assert {i["name"] for i in table.items} == {"Ana", "Carla"}  # "Diego" no tiene "a"

    table.sort_by("name", ascending=False)
    assert [i["name"] for i in table.items] == ["Carla", "Ana"]

    row = table.table.rows[0]
    await app.trigger(row, "select_change", True)
    assert [i["name"] for i in table.selected_items] == ["Carla"]
    assert app.find(text="1 seleccionados")

    await app.click(app.find_one(type=ft.TextButton, text="Limpiar filtros"))
    assert table.filters == {} and filter_form["name"].value == ""
    app.assert_no_errors()


async def test_users_crud_hashes_password(logged_app):
    from controls.encrypt import verify_password
    from data.manager.user_manager import UserManager

    app = logged_app
    await app.goto("/users")
    await app.click(app.find_one(key="crud_add"))
    await app.fill(app.find_one(key="name").field, "Usuario Demo")
    await app.fill(app.find_one(key="email").field, "demo@users.test")
    await app.click(app.find_one(type=ft.Button, text="Guardar"))
    assert app.find_one(key="password").error == "Este campo es obligatorio."
    await app.fill(app.find_one(key="password").field, "secreta")
    await app.click(app.find_one(type=ft.Button, text="Guardar"))
    user = UserManager().first(email="demo@users.test")
    assert verify_password("secreta", user.password)

    # Editar sin contraseña la conserva
    await app.click(app.find_one(key=f"edit-{user.id}"))
    assert app.find_one(key="password").value == ""
    await app.fill(app.find_one(key="name").field, "Usuario Editado")
    await app.click(app.find_one(type=ft.Button, text="Actualizar"))
    user = UserManager().get(user.id)
    assert user.name == "Usuario Editado" and verify_password("secreta", user.password)
    app.assert_no_errors()


async def test_test_view_cards_with_list_source(logged_app):
    app = logged_app
    await app.goto("/test")
    assert app.find(text="Test 1")
    await app.click(app.find_one(key="edit-1"))
    assert app.find_one(key="date").value == datetime.date(2023, 1, 1)
    await app.fill(app.find_one(key="name").field, "Test uno")
    await app.click(app.find_one(type=ft.Button, text="Actualizar"))
    assert app.find(text="Test uno")
    app.assert_no_errors()


async def test_person_groups_via_api_source(logged_app):
    from data.manager.person_group_manager import PersonGroupManager

    app = logged_app
    await app.goto("/autocompletes")
    await app.click(app.find_one(key="crud_add"))
    await app.fill(app.find_one(key="name").field, "Grupo desde la vista")

    country = app.find_one(key="country_id")
    await app.click(country._text_field)  # carga la primera página desde la API
    await app.click(option(app, "Argentina"))
    assert country.value == str(country.selected_item["id"])

    people = app.find_one(key="people")
    await app.click(people._search_field)
    await app.click(option(app, "Persona 1"))
    await app.click(app.find_one(type=ft.Button, text="Guardar"))
    assert app.find(text="Guardado exitosamente"), app.all_texts()

    group = PersonGroupManager().first(name="Grupo desde la vista")
    assert group.country.name == "Argentina"
    assert [p.name for p in group.people] == ["Persona 1"]
    assert app.find(text="País: Argentina")
    PersonGroupManager().delete(group.id)
    app.assert_no_errors()


async def test_related_selects_view(logged_app):
    from data.manager.abc_manager import ABCManager

    app = logged_app
    await app.goto("/autocomplete_related")
    await app.click(app.find_one(key="crud_add"))
    b = app.find_one(key="b")
    c = app.find_one(key="c")
    assert b.disabled and c.disabled

    await app.select(app.find_one(key="a").dropdown, "2")
    assert not b.disabled
    assert [o["text"] for o in b.options] == ["B1 A2", "B2 A2"]
    await app.click(b._search_field)
    await app.click(option(app, "B2 A2"))
    assert not c.disabled
    assert [o.key for o in c.dropdown.options] == ["221", "222"]
    await app.select(c.dropdown, "222")
    await app.click(app.find_one(type=ft.Button, text="Guardar"))
    assert ABCManager().first(name="A:A2 B:B2 A2 C:C2 (22)") is not None

    # Cambiar A limpia B y C
    await app.click(app.find_one(key="crud_add"))
    await app.select(app.find_one(key="a").dropdown, "1")
    assert app.find_one(key="b").value == [] and app.find_one(key="c").value is None
    app.assert_no_errors()


async def test_inline_crud(app):
    from fletbatteries import forms
    from fletbatteries.crud import InlineCRUD

    class AddressForm(forms.Form):
        customer_id = forms.IntegerField(label="Cliente")
        street = forms.CharField(label="Dirección")

    source = ListSource([{"id": 1, "customer_id": 7, "street": "Calle 7"}, {"id": 2, "customer_id": 8, "street": "Otra"}])
    crud = InlineCRUD(app.page, parent_id=7, parent_field="customer_id", source=source, form_class=AddressForm,
                      name="dirección")
    app.page.controls.clear()
    app.page.add(crud.build())
    await app.settle()
    assert app.find(text="Calle 7") and not app.find(text="Otra")

    await app.click(app.find_one(key="crud_add"))
    assert app.find_one(key="customer_id").disabled
    await app.fill(app.find_one(key="street").field, "Nueva")
    await app.click(app.find_one(type=ft.Button, text="Guardar"))
    assert source.all(customer_id=7)[-1]["street"] == "Nueva"
    assert app.find(text="Nueva")
    app.assert_no_errors()


async def test_autocomplete_search_via_api(logged_app):
    import asyncio

    app = logged_app
    await app.goto("/autocompletes")
    await app.click(app.find_one(key="crud_add"))
    country = app.find_one(key="country_id")
    await app.click(country._text_field)
    await app.fill(country._search_field, "cost")
    await asyncio.sleep(0.4)
    await app.settle()
    shown = [t.value for t in app.find(type=ft.Text, root=country._results_list)]
    assert shown == ["Costa Rica"]
    app.assert_no_errors()


async def test_edit_product_keeps_existing_image(logged_app, tmp_path):
    from data.manager.product_manager import ProductManager

    pm = ProductManager()
    product = pm.create(code="IMG-001", name="Con imagen", price=10, image="ejemplo.jpg")
    app = logged_app
    await app.goto("/products")
    await app.click(app.find_one(key=f"edit-{product.id}"))
    image = app.find_one(key="image")
    assert image.value.stored and image.value.name == "ejemplo.jpg"
    assert app.find(text="Archivo actual: ejemplo.jpg")
    assert image.preview.src == "image/ejemplo.jpg"
    await app.fill(app.find_one(key="name").field, "Con imagen editado")
    await app.click(app.find_one(type=ft.Button, text="Actualizar"))
    assert app.find(text="Guardado exitosamente")
    saved = pm.get(product.id)
    assert saved.name == "Con imagen editado" and saved.image == "ejemplo.jpg"

    # Quitar la imagen en un campo obligatorio muestra el error
    await app.click(app.find_one(key=f"edit-{product.id}"))
    await app.click(app.find_one(key="image").clear_button)
    await app.click(app.find_one(type=ft.Button, text="Actualizar"))
    assert app.find(text="Este campo es obligatorio.")
    pm.delete(product.id)
    app.assert_no_errors()
