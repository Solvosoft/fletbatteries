import flet as ft
from components.shared.selects import AutoCompleteSelect, AutoCompleteSelectMultiple

class RelationalSelectGroup(ft.Column):
    def __init__(self, page, relations):
        """
        relations: lista de dicts con:
            - "label": etiqueta a mostrar
            - "type": "single" o "multiple"
            - "data_fn": función que recibe (values_del_padre, items_del_padre) y retorna dataset
        """
        super().__init__(spacing=20)
        self.page = page
        self.relations = relations
        self.selects = []

        # inicializar selects y agregarlos al Column
        for i, rel in enumerate(self.relations):
            if rel["type"] == "single":
                select = AutoCompleteSelect(
                    self.page,
                    data=rel["data_fn"](None, None),  # inicial
                    label=rel["label"],
                    # ✅ Pasamos también items para que el hijo pueda construir el texto
                    on_change=lambda self_ref, vals, items, idx=i: self._on_change(idx, vals, items),
                )
            else:
                select = AutoCompleteSelectMultiple(
                    self.page,
                    data=rel["data_fn"](None, None),  # inicial
                    label=rel["label"],
                    on_change=lambda self_ref, vals, items, idx=i: self._on_change(idx, vals, items),
                )
            self.selects.append(select)
            self.controls.append(select.control)  # añadir al Column

    def _on_change(self, idx, values, items):
        """Cuando cambia un select, actualizar el siguiente"""
        if idx + 1 < len(self.selects):
            next_rel = self.relations[idx + 1]
            next_select = self.selects[idx + 1]

            # Reset de selects siguientes
            for i in range(idx + 1, len(self.selects)):
                self.selects[i].set_data({})  # mantiene tu comportamiento previo

            # ✅ Generar nuevas opciones del siguiente usando ids + items (con textos)
            data = next_rel["data_fn"](values, items)
            next_select.set_data(data)

        self.page.update()