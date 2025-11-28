import flet as ft
import requests
from components.shared.modals import CrudModal
from controls.utils import get_form
from components.shared.autocompletes_related import RelationalSelectGroup
from components.shared.generic_card import GenericCard

API_URL = "http://127.0.0.1:8000/"
ABC_URL = API_URL + "abc"


def build_view_autocompletes_related(page: ft.Page, forms: []) -> ft.Container:
    form = get_form(forms, "RelationalForm")
    form_dialog = CrudModal(page)

    # ----------------- Mock data functions -----------------
    def get_a(_, __):
        return {
            "results": {
                "1": {"id": 1, "text": "A1"},
                "2": {"id": 2, "text": "A2"},
            },
            "pagination": {"more": False},
        }

    def get_b(selected_ids, selected_a):
        if not selected_a:
            return {"results": {}, "pagination": {"more": False}}
        a_text = selected_a.get("text", "") if isinstance(selected_a, dict) else ""
        return {
            "results": {
                "11": {"id": 11, "text": f"B1 {a_text}"},
                "12": {"id": 12, "text": f"B2 {a_text}"},
            },
            "pagination": {"more": False},
        }

    def get_c(selected_ids, selected_b):
        if not selected_b:
            return {"results": {}, "pagination": {"more": False}}
        b_texts = [item.get("text", "") for item in selected_b] if isinstance(selected_b, list) else []
        b_text = ", ".join(b_texts)
        return {
            "results": {
                "21": {"id": 21, "text": f"C1 {b_text}"},
                "22": {"id": 22, "text": f"C2 {b_text}"},
            },
            "pagination": {"more": False},
        }

    # ----------------- Relations setup -----------------
    relations = [
        {"label": "Select A", "type": "single", "data_fn": get_a},
        {"label": "Select B", "type": "multiple", "data_fn": get_b},
        {"label": "Select C", "type": "single", "data_fn": get_c},
    ]

    # Assign relational widget to the form
    for input in form.inputs:
        if input.type == "RelationalSelectGroupField" and input.name == "related_selects":
            relational = RelationalSelectGroup(page, relations)
            input._select_component = relational
            input.widget = relational

    # ----------------- API helpers -----------------
    def api_get_all():
        resp = requests.get(ABC_URL)
        if resp.status_code == 200:
            data = resp.json()
            return list(data.get("results", {}).values())
        return []

    def api_create(name: str):
        return requests.post(f"{ABC_URL}?name={name}")

    def api_update(item_id: int, name: str):
        return requests.put(f"{ABC_URL}/{item_id}?name={name}")

    def api_delete(item_id: int):
        return requests.delete(f"{ABC_URL}/{item_id}")

    # ----------------- CRUD operations -----------------
    def submit_add():
        if not form.is_valid():
            return False

        values = form.get_item()
        selected_data = values.get("related_selects", [])

        a_item = selected_data[0].get('items') if len(selected_data) >= 1 else None
        b_items = selected_data[1].get('items') if len(selected_data) >= 2 else []
        if not isinstance(b_items, list):
            b_items = [b_items]
        c_item = selected_data[2].get('items') if len(selected_data) >= 3 else None

        a_text = a_item.get("text", "") if a_item else ""
        b_texts = [item.get("text", "") for item in b_items] if b_items else []
        c_text = c_item.get("text", "") if c_item else ""

        name = f"A:{a_text} B:{','.join(b_texts)} C:{c_text}"
        resp = api_create(name)

        if resp.status_code == 200:
            refresh_cards()
            return True
        return False

    def submit_edit(item):
        if not form.is_valid():
            return False

        values = form.get_item()
        selected_data = values.get("related_selects", [])

        a_item = selected_data[0].get('items') if len(selected_data) >= 1 else None
        b_items = selected_data[1].get('items') if len(selected_data) >= 2 else []
        if not isinstance(b_items, list):
            b_items = [b_items]
        c_item = selected_data[2].get('items') if len(selected_data) >= 3 else None

        a_text = a_item.get("text", "") if a_item else ""
        b_texts = [item.get("text", "") for item in b_items] if b_items else []
        c_text = c_item.get("text", "") if c_item else ""

        name = f"A:{a_text} B:{','.join(b_texts)} C:{c_text}"
        resp = api_update(item["id"], name)

        if resp.status_code == 200:
            refresh_cards()
            return True
        return False

    # ----------------- Form dialogs -----------------
    def on_add_item(e):
        form.clean()
        form_dialog.open(
            kind="create",
            title="Add Relations",
            content_controls=form.get_inputs(),
            on_accept=submit_add,
            success_text="Saved",
            error_text="Error saving",
            width=650,
        )

    def on_edit_item(item):
        # Example selected values (could come from API)
        a_value = {"id": 1, "text": "A1"}
        b_values = [{"id": 12, "text": "B2 A1"}]
        c_value = {"id": 22, "text": "C2 B2 A1"}

        for input_field in form.inputs:
            if input_field.name == "related_selects":
                rgroup = input_field._select_component

                # Set select A
                rgroup.selects[0].value = str(a_value["id"])
                rgroup.selects[0]._select(a_value)

                # Reload select B based on A
                b_data = rgroup.relations[1]["data_fn"](None, a_value)
                rgroup.selects[1].set_data(b_data)
                rgroup.selects[1].value = [str(v["id"]) for v in b_values]
                for v in b_values:
                    rgroup.selects[1]._select(v)

                # Reload select C based on B
                c_data = rgroup.relations[2]["data_fn"]([v["id"] for v in b_values], b_values)
                rgroup.selects[2].set_data(c_data)
                rgroup.selects[2].value = str(c_value["id"])
                rgroup.selects[2]._select(c_value)

        form_dialog.open(
            kind="edit",
            title="Edit Relations",
            content_controls=form.get_inputs(),
            on_accept=lambda: submit_edit(item),
            success_text="Updated",
            error_text="Error updating",
            width=650,
        )

    def on_delete_item(item):
        def confirm():
            resp = api_delete(item["id"])
            if resp.status_code == 200:
                refresh_cards()
                return True
            return False

        form_dialog.open(
            kind="delete",
            title="Delete item",
            content_controls=[ft.Text(f"Are you sure you want to delete the item with ID {item['id']}?")],
            on_accept=confirm,
            success_text="Deleted",
            error_text="Error deleting",
            width=520,
        )

    # ----------------- Cards -----------------
    def load_cards():
        items = api_get_all()
        cards = []

        for item in items:
            card = GenericCard(
                content=[
                    ft.Column(
                        [
                            ft.Text(f"ID: {item['id']}", size=16, weight="bold"),
                            ft.Text(f"Items: {item.get('text', '')}"),
                        ],
                        spacing=5,
                    )
                ],
                actions=[
                    ft.ElevatedButton("Edit", on_click=lambda e, it=item: on_edit_item(it)),
                    ft.ElevatedButton(
                        "Delete",
                        style=ft.ButtonStyle(bgcolor=ft.Colors.RED_600, color=ft.Colors.WHITE),
                        on_click=lambda e, it=item: on_delete_item(it),
                    ),
                ],
                height=200,
            )
            cards.append(card)

        return cards

    def refresh_cards():
        cards_row.controls = load_cards()
        page.update()

    # ----------------- Layout -----------------
    cards_row = ft.Row(
        wrap=True,
        spacing=20,
        run_spacing=20,
        controls=load_cards()
    )

    return ft.Column(
        [
            ft.Container(
                padding=20,
                content=ft.Row(
                    [
                        ft.Text("ABC Groups", size=22, weight=ft.FontWeight.BOLD),
                        ft.Container(expand=True),
                        ft.ElevatedButton("Add", on_click=on_add_item)
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
            ),
            cards_row
        ],
        spacing=20,
        expand=True
    )