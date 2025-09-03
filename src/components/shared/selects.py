import flet as ft
import unicodedata
from abc import ABC, abstractmethod
import threading


def _normalize_text(text: str) -> str:
    """Normalize text for case-insensitive and accent-insensitive search."""
    if not text:
        return ""
    normalized = unicodedata.normalize("NFD", text.lower().strip())
    return "".join(c for c in normalized if unicodedata.category(c) != "Mn")


class _Select(ABC):
    """Base class for Select components with common dropdown and search functionality."""

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
        self._dropdown_max_height: int = 150
        self._dropdown_item_height: int = 40
        self._blur_timer = None
        self._is_interacting = False

        self._search_field = ft.TextField(
            hint_text="Search...",
            on_change=self._on_search,
            on_blur=self._handle_blur,
            on_focus=self._handle_focus,
            expand=True,
            dense=True,
        )

        self._results_list = ft.ListView(spacing=2, padding=10)

        self._results_container = ft.Container(
            content=self._results_list,
            expand=False,
            height=None,
        )

        dropdown_content = []
        if isinstance(self, AutoCompleteSelect):
            dropdown_content.append(self._search_field)

        dropdown_content.append(self._results_container)

        self._dropdown_container = ft.Container(
            content=ft.Column(
                controls=dropdown_content,
                spacing=0,
            ),
            border=ft.border.all(1, ft.Colors.OUTLINE),
            border_radius=5,
            padding=5,
            visible=False,
            bgcolor=ft.Colors.SURFACE,
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=5,
                color=ft.Colors.BLACK38,
            ),
            # Add mouse events to detect interactions
            on_hover=self._on_dropdown_hover,
            on_click=self._handle_dropdown_click,
        )

    def _on_dropdown_hover(self, e):
        """Detect when the mouse is over the dropdown"""
        self._is_interacting = e.data == "true"

    def _handle_dropdown_click(self, e):
        """Handles clicks on empty areas of the dropdown"""
        self._is_interacting = True

        # Cancel any pending blur timer
        if self._blur_timer:
            self._blur_timer.cancel()
            self._blur_timer = None

        # Set focus on the search field
        if hasattr(self, '_search_field'):
            self._search_field.focus()

        # Reset flag after a short delay
        threading.Timer(0.1, lambda: setattr(self, '_is_interacting', False)).start()

    def _handle_focus(self, e):
        """Handle when the field receives focus"""
        if self._blur_timer:
            self._blur_timer.cancel()
            self._blur_timer = None

    def _handle_blur(self, e):
        """Handle when the field loses focus with delay"""
        # Cancel previous timer if exists
        if self._blur_timer:
            self._blur_timer.cancel()

        # Create a new timer with delay
        self._blur_timer = threading.Timer(0.15, self._delayed_close)
        self._blur_timer.start()

    def _delayed_close(self):
        """Close the dropdown after a delay if there is no interaction"""
        if not self._is_interacting and self._is_dropdown_open:
            self._close_dropdown()
        self._blur_timer = None

    def set_data(self, data: dict):
        """Load/reload options from the JSON data."""
        results = data.get("results", {})
        results_list = list(results.values())
        pagination = data.get("pagination", {}) or {}

        self._data["results"] = {str(item["id"]): item for item in results_list}
        self._data["pagination"] = {"more": bool(pagination.get("more", False))}
        self._refresh_options()

        for item in results.values():
            if item.get("selected"):
                self._select(item)
                if isinstance(self, AutoCompleteSelect):
                    break

    def _toggle_dropdown(self, e=None):
        # Mark that we are interacting
        self._is_interacting = True

        if self._is_dropdown_open:
            self._close_dropdown()
        else:
            self._open_dropdown()

        # Reset flag after a short delay
        threading.Timer(0.1, lambda: setattr(self, '_is_interacting', False)).start()

    def _open_dropdown(self):
        self._is_dropdown_open = True
        self._search_field.value = ""
        self._refresh_options()

        self._dropdown_container.visible = True
        if hasattr(self.page, 'update'):
            self.page.update()

    def _close_dropdown(self):
        self._is_dropdown_open = False
        self._dropdown_container.visible = False
        if hasattr(self.page, 'update'):
            self.page.update()

    def _on_search(self, e):
        self._refresh_options(self._search_field.value or "")

    @abstractmethod
    def _is_selected(self, item_id: str) -> bool:
        """Return True if the item is currently selected."""
        pass

    def _refresh_options(self, filter_text: str = ""):
        self._results_list.controls.clear()
        filter_text = _normalize_text(filter_text)

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
                disabled=disabled,
                on_click=lambda e, i=item: self._handle_option_click(i),
                expand=True,
                style=ft.ButtonStyle(
                    bgcolor={
                        ft.ControlState.DEFAULT: ft.Colors.SECONDARY_CONTAINER if is_selected else None,
                        ft.ControlState.DISABLED: ft.Colors.BLUE_GREY_100,
                    },
                    color={
                        ft.ControlState.DEFAULT: ft.Colors.ON_SURFACE,
                        ft.ControlState.DISABLED: ft.Colors.OUTLINE,
                    },
                    overlay_color={
                        ft.ControlState.DISABLED: ft.Colors.TRANSPARENT,
                    },
                    text_style=ft.TextStyle(
                        decoration=ft.TextDecoration.LINE_THROUGH if disabled else None,
                        decoration_color=ft.Colors.OUTLINE,
                    ) if disabled else None,
                ),
            )
            self._results_list.controls.append(option_btn)

        if not self._results_list.controls:
            self._results_list.controls.append(
                ft.Text("No results found", color=ft.Colors.OUTLINE, italic=True)
            )

        total_height = min(len(self._results_list.controls) * self._dropdown_item_height, self._dropdown_max_height)
        self._results_container.height = total_height

        if self._results_container.page:
            self._results_container.update()
        if self._results_list.page:
            self._results_list.update()

    def _handle_option_click(self, item):
        """Handle click on an option with interaction control"""
        # Mark that we are interacting
        self._is_interacting = True

        # Cancel blur timer if exists
        if self._blur_timer:
            self._blur_timer.cancel()
            self._blur_timer = None

        # Execute selection
        self._select(item)

    @abstractmethod
    def _select(self, item: dict):
        pass


class AutoCompleteSelect(_Select):
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

        # Main read-only text field that opens dropdown
        self._text_field = ft.TextField(
            label=self.label,
            read_only=True,
            expand=expand,
            width=width,
            suffix_icon=ft.Icons.ARROW_DROP_DOWN,
            on_click=self._toggle_dropdown,
            on_blur=self._handle_blur,
            on_focus=self._handle_focus,
            border_color=ft.Colors.OUTLINE,
        )

        self._main_column = ft.Column(
            controls=[
                self._text_field,
                self._dropdown_container,
            ],
            spacing=5,
            expand=expand,
        )

        self.set_data(data)

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

        if self._text_field.page:
            self._text_field.update()

        self._close_dropdown()

        if self.on_change_cb:
            self.on_change_cb(self, self.value, self.selected_item)


class AutoCompleteSelectMultiple(_Select):
    """Multi-selection autocomplete with chips showing selected elements."""

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
        self._search_field.border_color = ft.Colors.OUTLINE
        self._search_field.on_click = self._toggle_dropdown

        bordered_content = ft.Container(
            content=ft.Column(
                controls=[
                    self._chips_container,
                    ft.Row([self._search_field], alignment=ft.MainAxisAlignment.START),
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

            self._close_dropdown()

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