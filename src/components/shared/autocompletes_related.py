import flet as ft
from components.shared.selects import AutoCompleteSelect, AutoCompleteSelectMultiple

class RelationalSelectGroup(ft.Column):
    def __init__(self, page, relations):
        super().__init__(spacing=20)
        self.page = page
        self.relations = relations
        self.selects = []

        # Initialize select components based on relation type
        for i, rel in enumerate(self.relations):
            if rel["type"] == "single":
                select = AutoCompleteSelect(
                    self.page,
                    data=rel["data_fn"](None, None),
                    label=rel["label"],
                    on_change=lambda self_ref, vals, items, idx=i: self._on_change(idx, vals, items),
                )
            else:
                select = AutoCompleteSelectMultiple(
                    self.page,
                    data=rel["data_fn"](None, None),
                    label=rel["label"],
                    on_change=lambda self_ref, vals, items, idx=i: self._on_change(idx, vals, items),
                )
            self.selects.append(select)
            self.controls.append(select.control)

    def _on_change(self, idx, values, items):
        # Reset and update all subsequent selects
        if idx + 1 < len(self.selects):
            for i in range(idx + 1, len(self.selects)):
                sel = self.selects[i]
                sel.value = None if isinstance(sel, AutoCompleteSelect) else []

            next_rel = self.relations[idx + 1]
            next_select = self.selects[idx + 1]
            data = next_rel["data_fn"](values, items)
            next_select.set_data(data)

        self.page.update()

    def set_values(self, values_list):
        """
        Preload selections.
        values_list: [
            {"value": <value(s)>, "items": <item(s)>}, ...
        ]
        """
        for idx, val in enumerate(values_list):
            if idx >= len(self.selects):
                break
            select = self.selects[idx]
            items = val.get("items", None)
            if items is not None:
                if isinstance(select, AutoCompleteSelect):
                    select.value = items
                else:
                    select.value = items if isinstance(items, list) else [items]

                # Update next select based on this selection
                if idx + 1 < len(self.selects):
                    next_rel = self.relations[idx + 1]
                    next_select = self.selects[idx + 1]
                    next_data = next_rel["data_fn"](val.get("value"), items)
                    next_select.set_data(next_data)

        self.page.update()