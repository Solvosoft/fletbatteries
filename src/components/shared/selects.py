import flet as ft
import unicodedata


def _normalize_text(text: str) -> str:
    """Normaliza texto para búsqueda sin tildes y case-insensitive"""
    if not text:
        return ""
    normalized = unicodedata.normalize('NFD', text.lower())
    return ''.join(c for c in normalized if unicodedata.category(c) != 'Mn')


class SimpleSelect:
    """
    Select with a search bar that filters among the available options
    """
    def __init__(self, page: ft.Page, data: dict, label: str = "Select", on_change=None, expand=False, width=None):
        self.page = page
        self.label = label
        self.on_change_cb = on_change
        self._data = {"results": {}, "pagination": {"more": False}}
        self._is_dropdown_open = False
        self._selected_value = None
        self._selected_text = ""

        # Main textfield
        self._text_field = ft.TextField(
            label=self.label,
            read_only=True,
            expand=expand,
            width=width,
            suffix_icon=ft.Icons.ARROW_DROP_DOWN,
            on_focus=self._toggle_dropdown,
        )

        # Gesture to handle click events
        self._text_field_gesture = ft.GestureDetector(
            content=self._text_field,
            on_tap=self._toggle_dropdown,
        )

        self._search_field = ft.TextField(
            hint_text="Buscar...",
            on_change=self._on_search,
            expand=True,
            dense=True,
        )

        self._results_list = ft.ListView(
            height=150,
            spacing=2,
            padding=10,
        )

        self._dropdown_container = ft.Container(
            content=ft.Column(
                controls=[
                    self._search_field,
                    ft.Divider(height=1),
                    self._results_list,
                ],
                spacing=0,
            ),
            border=ft.border.all(1),
            border_radius=5,
            padding=5,
            visible=False,
        )

        # Main control/container
        self._main_column = ft.Column(
            controls=[
                self._text_field_gesture,
                self._dropdown_container,
            ],
            spacing=5,
            expand=expand,
        )

        self.set_data(data)


    def set_data(self, data: dict):
        """Loads/reloads options from the JSON."""
        results_list = list(data.get("results", {}).values())
        pagination = data.get("pagination", {}) or {}

        self._data["results"] = {str(item["id"]): item for item in results_list}
        self._data["pagination"] = {"more": bool(pagination.get("more", False))}

        # Set initial selection if exists
        for item in self._data["results"].values():
            if item.get("selected", False) and not item.get("disabled", False):
                self._selected_value = str(item["id"])
                self._selected_text = str(item.get("text", ""))
                self._text_field.value = self._selected_text
                break

        self._refresh_options()

    @property
    def value(self):
        return self._selected_value

    @property
    def selected_item(self):
        if self._selected_value is None:
            return None
        return self._data["results"].get(self._selected_value, None)

    def control(self) -> ft.Control:
        return self._main_column

    def _refresh_options(self, filter_text: str = ""):
        self._results_list.controls.clear()
        filter_text = filter_text.lower().strip()

        for item in self._data["results"].values():
            text = str(item.get("text", ""))
            item_id = str(item.get("id", ""))

            # Filter by text
            if filter_text and filter_text not in _normalize_text(text):
                continue

            disabled = bool(item.get("disabled", False))
            is_selected = self._selected_value == item_id

            option_btn = ft.TextButton(
                text,
                data=item_id,
                disabled=disabled,
                on_click=lambda e, i=item: self._select(i),
                expand=True,
                style=ft.ButtonStyle(
                    bgcolor=ft.Colors.BLUE_50 if is_selected else None,
                ),
            )
            self._results_list.controls.append(option_btn)

        if not self._results_list.controls:
            self._results_list.controls.append(
                ft.Text("No se encontraron resultados", color=ft.Colors.GREY_500, italic=True)
            )

        if hasattr(self._results_list, "page") and self._results_list.page:
            self._results_list.update()

    def _select(self, item: dict):

        if self._selected_value:
            self._data["results"][self._selected_value]["selected"] = False

        new_id = str(item["id"])
        self._data["results"][new_id]["selected"] = True

        self._selected_value = new_id
        self._selected_text = str(item.get("text", ""))
        self._text_field.value = self._selected_text
        self._text_field.update()

        self._close_dropdown()

        if self.on_change_cb:
            self.on_change_cb(self, self.value, self.selected_item)

    def _toggle_dropdown(self, e=None):
        if self._is_dropdown_open:
            self._close_dropdown()
        else:
            self._open_dropdown()

    def _open_dropdown(self):
        self._is_dropdown_open = True
        self._dropdown_container.visible = True
        self._search_field.value = ""
        self._refresh_options()
        if hasattr(self._dropdown_container, "page") and self._dropdown_container.page:
            self._dropdown_container.update()

    def _close_dropdown(self):
        self._is_dropdown_open = False
        self._dropdown_container.visible = False
        if hasattr(self._dropdown_container, "page") and self._dropdown_container.page:
            self._dropdown_container.update()

    def _on_search(self, e):
        self._refresh_options(self._search_field.value or "")
