import flet as ft
import requests
from components.shared.selects import AutoCompleteSelect, AutoCompleteSelectMultiple
from components.shared.modals import CrudModal
from controls.utils import get_form
from data.manager.person_group_manager import PersonGroupManager
from components.shared.generic_card import GenericCard

API_URL = "http://127.0.0.1:8000/"

GET_COUNTRIES_URL = API_URL + "countries"
GET_PERSONS_URL = API_URL + "persons"
GET_COMMUNITIES_URL = API_URL + "communities"
GET_PERSON_GROUPS_URL = API_URL + "persons_groups"

person_group_manager = PersonGroupManager()

def fetch_data(url: str, skip=0, limit=10, q: str = ""):
    response = requests.get(
        url,
        params={"skip": skip, "limit": limit, "q": q},
    )
    if response.status_code == 200:
        return response.json()
    return {"results": {}, "pagination": {"more": False}}


def make_loader(url: str, default_limit: int):
    def loader(skip: int, limit: int = default_limit, filter_text: str = ""):
        return fetch_data(url, skip=skip, limit=limit, q=filter_text)
    return loader


def build_view_autocompletes(page: ft.Page, forms: []) -> ft.Container:
    form = get_form(forms, "PeopleForm")
    form_dialog = CrudModal(page)

    def on_select_change(select_component, selected_values, items):
        print(f"Selected values: {selected_values}")
        print(f"Selected items: {items}")

    for input in form.inputs:
        if input.type == "SelectField" and input.name == "country":
            select = AutoCompleteSelect(
                page,
                data=fetch_data(GET_COUNTRIES_URL, limit=10),
                label=input.label,
                on_change=on_select_change,
                on_load_more=make_loader(GET_COUNTRIES_URL, 6),
                on_search_api=make_loader(GET_COUNTRIES_URL, 6),
            )
            input._select_component = select
            input.widget = select.control

        elif input.type == "SelectMultipleField" and input.name == "people":
            select_multi = AutoCompleteSelectMultiple(
                page,
                data=fetch_data(GET_PERSONS_URL, limit=5),
                label=input.label,
                on_change=on_select_change,
                on_load_more=make_loader(GET_PERSONS_URL, 6),
                on_search_api=make_loader(GET_PERSONS_URL, 6),
            )
            input.widget = select_multi.control
            input._select_component = select_multi

        elif input.type == "SelectMultipleField" and input.name == "communities":
            select_multi = AutoCompleteSelectMultiple(
                page,
                data=fetch_data(GET_COMMUNITIES_URL, limit=5),
                label=input.label,
                on_change=on_select_change,
                on_load_more=make_loader(GET_COMMUNITIES_URL, 6),
                on_search_api=make_loader(GET_COMMUNITIES_URL, 6),
            )
            input.widget = select_multi.control
            input._select_component = select_multi

    def load_cards():
        person_groups_data = fetch_data(GET_PERSON_GROUPS_URL, limit=50)
        groups_list = list(person_groups_data.get("results", {}).values())
        cards = []

        for item in groups_list:
            persons_text = ", ".join([p["name"] for p in item.get("Persons", [])])
            communities_text = ", ".join([c["name"] for c in item.get("Communities", [])])
            country_text = item.get("Country", {}).get("name", "N/A")

            card = GenericCard(
                content=[
                    ft.Column(
                        [
                            ft.Text(item["nombre"], size=18, weight="bold"),
                            ft.Text(f"Country: {country_text}"),
                            ft.Text(f"Persons: {persons_text}"),
                            ft.Text(f"Communities: {communities_text}"),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.START,
                        alignment=ft.MainAxisAlignment.START,
                        expand=True,
                        spacing=5,
                    )
                ],
                actions=[
                    ft.ElevatedButton("Editar", on_click=lambda e, it=item: on_edit_item(it)),
                    ft.ElevatedButton(
                        "Eliminar",
                        style=ft.ButtonStyle(bgcolor=ft.Colors.RED_600, color=ft.Colors.WHITE),
                        on_click=lambda e, it=item: on_delete_item(it),
                    ),
                ],
                width=350,
                height=200,
                horizontal_alignment=ft.CrossAxisAlignment.START,
            )
            cards.append(card)

        return cards

    def refresh_cards():
        cards_row.controls = load_cards()
        page.update()

    #CRUD Functions
    def submit_add():
        if form.is_valid():
            try:
                item = form.get_item()
                person_group_manager.create(
                    name=item["name"],
                    country_id=int(item["country"]),
                    people_ids=[int(pid) for pid in item.get("people", [])],
                    community_ids=[int(cid) for cid in item.get("communities", [])],
                )
                form.clean()
                refresh_cards()
                return True
            except Exception as ex:
                form_dialog.title = ft.Text(str(ex), color=ft.Colors.RED)
                page.update()
                return False
        return False

    def submit_edit(item):
        if form.is_valid():
            item_data = form.get_item()
            update_resp = requests.put(
                f"{GET_PERSON_GROUPS_URL}/{item['id']}",
                json={
                    "name": item_data["name"],
                    "country_id": int(item_data["country"]),
                    "people_ids": [int(pid) for pid in item_data.get("people", [])],
                    "community_ids": [int(cid) for cid in item_data.get("communities", [])],
                }
            )
            if update_resp.status_code == 200:
                form.clean()
                refresh_cards()
                return True
            return False

    def on_add_item(e):
        form.clean()
        form_dialog.open(
            kind="create",
            title=form.title,
            content_controls=form.get_inputs(),
            on_accept=submit_add,
            success_text="Guardado con éxito",
            error_text="Error al guardar",
            width=600,
        )

    def on_edit_item(item):
        for input in form.inputs:
            if input.name == "name":
                input.set_value(item["nombre"])
            elif input.name == "country":
                input.set_value(str(item["Country"]["id"]) if item.get("Country") else "")
            elif input.name == "people":
                input.set_value([str(p["id"]) for p in item.get("Persons", [])])
            elif input.name == "communities":
                input.set_value([str(c["id"]) for c in item.get("Communities", [])])

        form_dialog.open(
            kind="edit",
            title=f"Editar grupo {item['nombre']}",
            content_controls=form.get_inputs(),
            on_accept=lambda: submit_edit(item),
            success_text="Actualizado con éxito",
            error_text="Error al actualizar",
            width=600,
        )

    def on_delete_item(item):
        def confirm_delete():
            resp = requests.delete(f"{GET_PERSON_GROUPS_URL}/{item['id']}")
            if resp.status_code == 200:
                refresh_cards()
                return True
            return False

        form_dialog.open(
            kind="delete",
            title=f"Eliminar grupo {item['nombre']}",
            content_controls=[ft.Text(f"¿Estás seguro que quieres eliminar el grupo '{item['nombre']}'?")],
            on_accept=confirm_delete,
            success_text="Grupo eliminado",
            error_text="No se pudo eliminar",
            width=520,
        )

    # Construcción de la vista
    cards_row = ft.Row(
        controls=load_cards(),
        wrap=True,
        spacing=20,
        run_spacing=20,
        alignment=ft.MainAxisAlignment.START
    )

    return ft.Column(
        [
            ft.Container(
                padding=20,
                content=ft.Row(
                    [
                        ft.Text("People Groups", size=22, weight=ft.FontWeight.BOLD),
                        ft.Container(expand=True),
                        ft.ElevatedButton("Add", on_click=on_add_item)
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                )
            ),
            cards_row
        ],
        spacing=20,
        expand=True
    )