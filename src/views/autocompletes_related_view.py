import flet as ft
from components.shared.selects import AutoCompleteSelect, AutoCompleteSelectMultiple
from components.shared.autocompletes_related import RelationalSelectGroup

def build_view_autocompletes_related(page: ft.Page) -> ft.Container:
    # ----------------- utilidades internas -----------------
    def _normalize_items(selected_items):
        # Normaliza a lista de dicts con al menos la llave "text"
        # Puede venir como None, un solo dict, una lista de dicts, o un dict mapeando id->dict
        if not selected_items:
            return []
        if isinstance(selected_items, dict):
            # Si es dict y parece item (tiene 'text'), lo envolvemos en lista;
            # si es dict mapeando id->item, usamos values()
            return [selected_items] if "text" in selected_items else list(selected_items.values())
        if isinstance(selected_items, list):
            return selected_items
        # Cualquier otro caso lo envolvemos y dejamos que falle con gracia si no trae 'text'
        return [selected_items]

    def _texts_from_items(selected_items):
        # Extrae la lista de textos de los items normalizados
        items = _normalize_items(selected_items)
        return [it.get("text", "") for it in items if isinstance(it, dict)]

    # ----------------- data fns -----------------
    def get_a(_, __):
        # Inicial: A no depende de nadie
        return {
            "results": {
                "1": {"id": 1, "text": "A1", "disabled": False, "selected": False},
                "2": {"id": 2, "text": "A2", "disabled": False, "selected": False},
            },
            "pagination": {"more": False},
        }

    def get_b(_selected_ids, selected_items_from_a):
        # B depende de A, pero queremos mostrar el NOMBRE de A, no su id
        texts_a = _texts_from_items(selected_items_from_a)
        if not texts_a:
            return {"results": {}, "pagination": {"more": False}}

        # Si A es single, será un solo texto; si no, los juntamos por si acaso
        etiqueta_a = ", ".join(texts_a)
        return {
            "results": {
                "11": {"id": 11, "text": f"B1 {etiqueta_a}", "disabled": False, "selected": False},
                "12": {"id": 12, "text": f"B2 {etiqueta_a}", "disabled": False, "selected": False},
            },
            "pagination": {"more": False},
        }

    def get_c(_selected_ids, selected_items_from_b):
        # C depende de B; B ya incluye el nombre de A en su "text"
        textos_b = _texts_from_items(selected_items_from_b)
        if not textos_b:
            return {"results": {}, "pagination": {"more": False}}

        cadena = ", ".join(textos_b)  # p.ej. "B1 A1, B2 A2"
        return {
            "results": {
                "21": {"id": 21, "text": f"C1 {cadena}", "disabled": False, "selected": False},
                "22": {"id": 22, "text": f"C2 {cadena}", "disabled": False, "selected": False},
            },
            "pagination": {"more": False},
        }

    # definir relaciones (igual que tenías, solo que las data_fn aceptan (values, items))
    relations = [
        {"label": "Seleccione A", "type": "single", "data_fn": get_a},
        {"label": "Seleccione B", "type": "multiple", "data_fn": get_b},
        {"label": "Seleccione C", "type": "single", "data_fn": get_c},
    ]

    relational_selects = RelationalSelectGroup(page, relations)

    return ft.Container(
        content=ft.Column(
            [
                ft.Text("Relational Autocomplete Selects", size=20),
                relational_selects,
            ],
            spacing=20,
            alignment=ft.MainAxisAlignment.START,
            expand=True,
        ),
        alignment=ft.alignment.top_center,
        padding=20,
        expand=True,
    )

