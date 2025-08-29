import flet as ft
import unicodedata
from abc import ABC, abstractmethod
from flet_core import MaterialState

def _normalize_text(text: str) -> str:
    """Normalize text for case-insensitive and accent-insensitive search."""
    if not text:
        return ""
    normalized = unicodedata.normalize("NFD", text.lower())
    return "".join(c for c in normalized if unicodedata.category(c) != "Mn")

class Select(ABC):
    """
    Base class for Select components with common dropdown and search functionality.
    """
    def __init__(
        self,
        page: ft.Page,
        data: dict,
        label: str = "Select",
        on_change=None,
        expand=False,
        width=None,
    ):
        self.page = page
        self.label = label
        self.on_change_cb = on_change
        self._data = {"results": {}, "pagination": {"more": False}}
        self._is_dropdown_open = False

        # Search field
        self._search_field = ft.TextField(
            hint_text="Search...",
            on_change=self._on_search,
            expand=True,
            dense=True,
        )

        # Results list
        self._results_list = ft.ListView(height=150, spacing=2, padding=10)

        # Dropdown container (invisible at start)
        dropdown_controls = []

        # Add search field only in AutoCompleteSelect class
        if isinstance(self, AutoCompleteSelect):
            dropdown_controls.append(self._search_field)

        dropdown_controls.append(ft.Divider(height=1))
        dropdown_controls.append(self._results_list)

        self._dropdown_container = ft.Container(
            content=ft.Column(
                controls=dropdown_controls,
                spacing=0,
            ),
            border=ft.border.all(1, ft.Colors.OUTLINE),
            border_radius=5,
            padding=5,
            visible=False,
            bgcolor=ft.Colors.SURFACE,

            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=5,
                color=ft.Colors.BLACK38,
            ),
        )

        self.set_data(data)

    def set_data(self, data: dict):
        """Load/reload options from the JSON data."""
        results_list = list(data.get("results", {}).values())
        pagination = data.get("pagination", {}) or {}

        self._data["results"] = {str(item["id"]): item for item in results_list}
        self._data["pagination"] = {"more": bool(pagination.get("more", False))}
        self._refresh_options()

    def _toggle_dropdown(self, e=None):
        if self._is_dropdown_open:
            self._close_dropdown()
        else:
            self._open_dropdown()

    def _open_dropdown(self):
        self._is_dropdown_open = True
        self._search_field.value = ""
        self._refresh_options()

        self._dropdown_container.visible = True

        self.page.update()

    def _close_dropdown(self):
        self._is_dropdown_open = False
        self._dropdown_container.visible = False

        self.page.update()

    def _on_search(self, e):
        self._refresh_options(self._search_field.value or "")

    @abstractmethod
    def _is_selected(self, item_id: str) -> bool:
        """Return True if the item is currently selected."""
        pass

    def _refresh_options(self, filter_text: str = ""):
        self._results_list.controls.clear()
        filter_text = _normalize_text(filter_text.lower().strip())

        for item in self._data["results"].values():
            text = str(item.get("text", ""))
            item_id = str(item.get("id", ""))

            if filter_text and filter_text not in _normalize_text(text):
                continue

            disabled = bool(item.get("disabled", False))
            is_selected = self._is_selected(item_id)

            option_btn = ft.TextButton(
                text,
                data=item_id,
                disabled=disabled
                or (is_selected and getattr(self, "_selected_values", None) is not None),
                on_click=lambda e, i=item: self._select(i),
                expand=True,
                style=ft.ButtonStyle(
                    bgcolor={
                        MaterialState.DEFAULT: ft.Colors.SECONDARY_CONTAINER if is_selected else None
                    },
                    color={
                        MaterialState.DEFAULT: ft.Colors.ON_SURFACE
                    },
                ),
            )
            self._results_list.controls.append(option_btn)

        if not self._results_list.controls:
            self._results_list.controls.append(
                ft.Text("No results found", color=ft.Colors.OUTLINE, italic=True)
            )

        if self._results_list.page:
            self._results_list.update()

class AutoCompleteSelect(Select):
    """Single selection autocomplete with a dropdown search field."""
    def __init__(
        self,
        page: ft.Page,
        data: dict,
        label: str = "Select",
        on_change=None,
        expand=False,
        width=None,
    ):
        self._selected_value = None
        self._selected_text = ""

        super().__init__(page, data, label, on_change, expand, width)

        # Main readonly text field that opens dropdown
        self._text_field = ft.TextField(
            label=self.label,
            read_only=True,
            expand=expand,
            width=width,
            suffix_icon=ft.Icons.ARROW_DROP_DOWN,
            on_focus=self._toggle_dropdown,
            on_blur= self.focus_lost,
            border_color=ft.Colors.OUTLINE,
        )

        # Gesture detector to capture clicks
        self._text_field_gesture = ft.GestureDetector(
            content=self._text_field, on_tap=self._toggle_dropdown
        )

        self._main_column = ft.Column(
            controls=[
                self._text_field_gesture,
                self._dropdown_container,
            ],
            spacing=5,
            expand=expand,
        )

        self.set_data(data)

    def focus_lost(self, e):
        print("Se perdió el foco del TextField")

    def _is_selected(self, item_id: str) -> bool:
        return self._selected_value == item_id

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

class AutoCompleteSelectMultiple(Select):
    """Multi selection autocomplete with chips showing selected elements."""
    def __init__(
        self,
        page: ft.Page,
        data: dict,
        label: str = "Select",
        on_change=None,
        expand=False,
        width=None,
    ):
        self._selected_values = []
        self._selected_items = []

        super().__init__(page, data, label, on_change, expand, width)

        self._chips_container = ft.Row(wrap=True, spacing=5, run_spacing=5)

        self._search_field.hint_text = label
        self._search_field.suffix_icon = ft.Icons.ARROW_DROP_DOWN
        self._search_field.on_focus = self._toggle_dropdown
        self._search_field.border_color = ft.Colors.OUTLINE

        self._search_gesture = ft.GestureDetector(
            content=self._search_field, on_tap=self._toggle_dropdown
        )

        bordered_content = ft.Container(
            content=ft.Column(
                controls=[
                    self._chips_container,
                    ft.Row([self._search_gesture], alignment=ft.MainAxisAlignment.START),
                ],
                spacing=10,
            ),
            border=ft.border.all(1, ft.Colors.OUTLINE),
            border_radius=6,
            padding=10,
            bgcolor=ft.Colors.SURFACE,
        )

        self._main_column = ft.Column(
            controls=[
                bordered_content,
                self._dropdown_container,
            ],
            spacing=0,
            expand=False,
        )

        self.set_data(data)

    def _is_selected(self, item_id: str) -> bool:
        return item_id in self._selected_values

    @property
    def value(self):
        return self._selected_values

    @property
    def selected_items(self):
        return self._selected_items

    def control(self) -> ft.Control:
        return self._main_column

    def _update_chips(self):
        self._chips_container.controls.clear()
        for item in self._selected_items:
            chip = ft.Chip(
                label=ft.Text(item.get("text", "")),
                on_delete=lambda e, item_id=item["id"]: self._remove_item(item_id),
                bgcolor=ft.Colors.SECONDARY_CONTAINER,
                check_color=ft.Colors.ON_SECONDARY_CONTAINER,
                delete_icon_color=ft.Colors.ON_SECONDARY_CONTAINER,
            )
            self._chips_container.controls.append(chip)

    def _remove_item(self, item_id):
        item_id_str = str(item_id)
        if item_id_str in self._selected_values:
            self._selected_values.remove(item_id_str)
            self._selected_items = [
                i for i in self._selected_items if str(i["id"]) != item_id_str
            ]
            self._update_chips()

            if self._chips_container.page:
                self._chips_container.update()

            if self.on_change_cb:
                self.on_change_cb(self, self.value, self.selected_items)

    def _select(self, item: dict):
        item_id = str(item["id"])
        if item_id not in self._selected_values:
            self._selected_values.append(item_id)
            self._selected_items.append(item)
            self._update_chips()

            if self._chips_container.page:
                self._chips_container.update()

            if self.on_change_cb:
                self.on_change_cb(self, self.value, self.selected_items)

        self._close_dropdown()