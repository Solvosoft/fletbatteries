import flet as ft

from fletbatteries.crud import CRUDView

from app_forms import PersonGroupForm, api_source


def group_card(item: dict) -> ft.Control:
    return ft.Column(
        [
            ft.Text(item["name"], size=16, weight=ft.FontWeight.BOLD),
            ft.Text(f"País: {PersonGroupForm.base_fields['country_id'].display(item.get('country_id'))}"),
            ft.Text(f"Personas: {PersonGroupForm.base_fields['people'].display(item.get('people'))}", size=12),
            ft.Text(f"Comunidades: {PersonGroupForm.base_fields['communities'].display(item.get('communities'))}",
                    size=12),
        ],
        spacing=4,
        tight=True,
    )


class PersonGroupCRUD(CRUDView):
    """CRUD completo contra la API REST (APISource) con selects remotos."""

    title = "People Groups"
    name = "grupo"
    form_class = PersonGroupForm
    mode = "cards"
    card = staticmethod(group_card)


def build_view_autocompletes(page: ft.Page) -> ft.Control:
    return PersonGroupCRUD(page, source=api_source("person_groups")).build()
