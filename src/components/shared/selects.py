import flet as ft
import unicodedata
import threading
from abc import ABC, abstractmethod

def _normalize_text(text: str) -> str:
    """Normalize text by removing accents and making it case-insensitive."""
    if not text:
        return ""
    normalized = unicodedata.normalize("NFD", text.lower().strip())
    return "".join(c for c in normalized if unicodedata.category(c) != "Mn")

class _Select(ABC):
    """Base class for Select components with common dropdown and search functionality."""

    def __init__(self, page: ft.Page, data: dict = None, label="Select", on_change=None, on_load_more=None, on_search_api=None, items_per_load=4, search_delay=0.3):

        self.page = page
        self.label = label
        self.on_change_cb = on_change
        self.on_load_more_cb = on_load_more
        self.on_search_api_cb = on_search_api
        self.items_per_load = items_per_load
        self.search_delay = search_delay

        self._data = {"results": {}, "pagination": {"more": False}}
        self._is_dropdown_open = False
        self._dropdown_max_height = 150
        self._dropdown_item_height = 40
        self._blur_timer = None
        self._is_interacting = False
        self._search_timer = None

        self._error_text = ft.Text(color=ft.Colors.RED)

        self._search_field = ft.TextField(
            hint_text="Search...",
            on_change=self._on_search,
            on_blur=self._handle_blur,
            on_focus=self._handle_focus,
            expand=True,
            dense=True
        )

        self._results_list = ft.ListView(
            spacing=2,
            padding=10,
            on_scroll=self._on_scroll,
            auto_scroll=False
        )

        self._results_container = ft.Container(
            content=self._results_list,
            expand=False,
            height=None
        )

        dropdown_content = []
        if isinstance(self, AutoCompleteSelect):
            dropdown_content.append(self._search_field)
        dropdown_content.append(self._results_container)

        self._dropdown_container = ft.Container(
            content=ft.Column(controls=dropdown_content, spacing=0),
            border=ft.border.all(1, ft.Colors.OUTLINE),
            border_radius=5,
            padding=5,
            visible=False,
            bgcolor=ft.Colors.SURFACE,
            shadow=ft.BoxShadow(spread_radius=1, blur_radius=5, color=ft.Colors.BLACK38),
            on_hover=self._on_dropdown_hover,
            on_click=self._handle_dropdown_click
        )

        if data:
            self.set_data(data)

    def _on_scroll(self, e: ft.OnScrollEvent):
        """Handles infinite scrolling by calling the provided `on_load_more` callback."""
        if e.pixels >= e.max_scroll_extent - 10 and self._data["pagination"].get("more") and self.on_load_more_cb:
            skip = len(self._data["results"])
            filter_text = self._search_field.value or ""

            def bg_load():
                try:
                    data = self.on_load_more_cb(skip, self.items_per_load, filter_text)
                    if not data or "results" not in data:
                        return
                    results_list = list(data["results"].values()) if isinstance(data["results"], dict) else data["results"]
                    more = bool(data.get("pagination", {}).get("more", False))
                    self.append_data(results_list, more)
                    self.page.update()
                except Exception:
                    return

            threading.Thread(target=bg_load, daemon=True).start()

    def _on_search(self, e):
        """Debounces the search input before executing a query."""
        if self._search_timer:
            self._search_timer.cancel()
        self._search_timer = threading.Timer(self.search_delay, self._execute_search)
        self._search_timer.start()

    def _execute_search(self):
        """Executes a search using the API callback or falls back to local filtering."""
        filter_text = self._search_field.value or ""
        if self.on_search_api_cb:
            def bg_search():
                try:
                    data = self.on_search_api_cb(skip=0, limit=self.items_per_load, filter_text=filter_text)
                    if data and "results" in data:
                        results_list = list(data["results"].values()) if isinstance(data["results"], dict) else data["results"]
                        more = bool(data.get("pagination", {}).get("more", False))

                        # Temporary refresh of results (does not overwrite `_data`)
                        self._refresh_options(filtered_results=results_list)
                        print(f"Search results for '{filter_text}': {results_list}")
                except Exception as e:
                    print("Search error:", e)

            threading.Thread(target=bg_search, daemon=True).start()
        else:
            self._refresh_options(filter_text)

    def append_data(self, results: list, more: bool = False):
        """Appends new results to the internal dataset while preserving selection and state."""
        if isinstance(results, dict):
            results = list(results.values())
        for item in results:
            id_str = str(item["id"])
            stored = self._data["results"].get(id_str)
            if stored:
                merged = {**item, "selected": stored.get("selected", False), "disabled": stored.get("disabled", False)}
                self._data["results"][id_str] = merged
            else:
                self._data["results"][id_str] = dict(item)
        self._data["pagination"]["more"] = bool(more)
        self._refresh_options(self._search_field.value or "")

    def set_data(self, data: dict):
        """Replaces the entire dataset with new results."""
        results = data.get("results", {})
        results_list = list(results.values()) if isinstance(results, dict) else results
        pagination = data.get("pagination", {}) or {}
        self._data["results"] = {str(item["id"]): dict(item) for item in results_list}
        self._data["pagination"] = {"more": bool(pagination.get("more", False))}
        self._refresh_options()

        for item in results_list:
            if item.get("selected"):
                self._select(self._data["results"].get(str(item["id"]), item))
                if isinstance(self, AutoCompleteSelect):
                    break

    def _on_dropdown_hover(self, e):
        self._is_interacting = e.data == "true"

    def _handle_dropdown_click(self, e):
        self._is_interacting = True
        if self._blur_timer:
            self._blur_timer.cancel()
            self._blur_timer = None
        self._search_field.focus()
        threading.Timer(0.1, lambda: setattr(self, "_is_interacting", False)).start()

    def _handle_focus(self, e):
        if self._blur_timer:
            self._blur_timer.cancel()
            self._blur_timer = None

    def _handle_blur(self, e):
        if self._blur_timer:
            self._blur_timer.cancel()
        self._blur_timer = threading.Timer(0.15, self._delayed_close)
        self._blur_timer.start()

    def _delayed_close(self):
        if not self._is_interacting and self._is_dropdown_open:
            self._close_dropdown()
        self._blur_timer = None

    def _toggle_dropdown(self, e=None):
        self._is_interacting = True
        if self._is_dropdown_open:
            self._close_dropdown()
        else:
            self._open_dropdown()
        threading.Timer(0.1, lambda: setattr(self, "_is_interacting", False)).start()

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

    @abstractmethod
    def _is_selected(self, item_id: str) -> bool:
        pass

    def _refresh_options(self, filter_text="", filtered_results=None):
        """Refreshes the dropdown options, either filtered or full dataset."""
        self._results_list.controls.clear()
        filter_text = _normalize_text(filter_text)

        results_to_show = filtered_results if filtered_results is not None else list(self._data["results"].values())

        for item in results_to_show:
            text = str(item.get("text", ""))
            item_id = str(item.get("id", ""))
            if filter_text and filter_text not in _normalize_text(text):
                continue
            disabled = bool(item.get("disabled", False))
            is_selected = self._is_selected(item_id)

            option_btn = ft.TextButton(
                 content=ft.Row(
                    [
                        ft.Image(src=item["image"], width=24, height=24) if item.get("image") else ft.Container(),
                        ft.Text(text) if text else ft.Container(),
                    ],
                    spacing=5,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER
                ),
                data=item_id,
                disabled=disabled,
                on_click=lambda e, i=item: self._handle_option_click(i),
                expand=True,
                style=ft.ButtonStyle(
                    bgcolor={ft.ControlState.DEFAULT: ft.Colors.SECONDARY_CONTAINER if is_selected else None,
                             ft.ControlState.DISABLED: ft.Colors.BLUE_GREY_100},
                    color={ft.ControlState.DEFAULT: ft.Colors.ON_SURFACE,
                           ft.ControlState.DISABLED: ft.Colors.OUTLINE},
                    overlay_color={ft.ControlState.DISABLED: ft.Colors.TRANSPARENT},
                )
            )
            self._results_list.controls.append(option_btn)

        if not self._results_list.controls:
            self._results_list.controls.append(ft.Text("No results found", color=ft.Colors.OUTLINE, italic=True))

        self._results_container.height = min(len(self._results_list.controls) * self._dropdown_item_height, self._dropdown_max_height)
        self.page.update()

    def _handle_option_click(self, item):
        stored = self._data["results"].get(str(item["id"]), item)
        self._select(stored)

    def show_error(self, message: str = ""):
        """Shows or hides the error message."""
        self._error_text.value = message
        if isinstance(self, AutoCompleteSelect):
            self._text_field.error = None
            if message:
                self._text_field.error = self._error_text
            self._text_field.update()
        elif isinstance(self, AutoCompleteSelectMultiple):
            self._bordered_content.border = ft.border.all(1, ft.Colors.RED if message else ft.Colors.OUTLINE)
            self._error_container.visible = bool(message)
            self._main_column.update()

    @property
    def control(self):
        return self._main_column


class AutoCompleteSelect(_Select):
    """Single selection autocomplete with a dropdown search field."""

    def __init__(self, page, data, label="Select", on_change=None, on_load_more=None,
                 on_search_api=None, expand=False, width=None, items_per_load=4):
        self._selected_value = None
        self._selected_text = ""
        super().__init__(page, data, label, on_change, on_load_more, on_search_api, items_per_load)

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

        self._main_column = ft.Column(controls=[self._text_field, self._dropdown_container], spacing=5, expand=expand)

    def _is_selected(self, item_id: str) -> bool:
        return self._selected_value == item_id

    @property
    def value(self):
        return self._selected_value

    @property
    def selected_item(self):
        return self._data["results"].get(self._selected_value) if self._selected_value else None

    def _select(self, item: dict):
        if self._selected_value:
            prev = self._data["results"].get(self._selected_value)
            if prev:
                prev["selected"] = False

        item_id = str(item["id"])
        stored = self._data["results"].get(item_id, item)
        stored["selected"] = True
        self._selected_value = item_id
        self._selected_text = str(stored.get("text", ""))
        self._text_field.value = self._selected_text
        self.page.update()
        self._close_dropdown()
        if self.on_change_cb:
            self.on_change_cb(self, self.value, self.selected_item)


class AutoCompleteSelectMultiple(_Select):
    """Multi-selection autocomplete with chips showing selected elements."""

    def __init__(self, page, data, label="Select", on_change=None, on_load_more=None, on_search_api=None, expand=False, width=None, items_per_load=4):
        self._selected_values = []
        self._selected_items = []
        super().__init__(page, data, label, on_change, on_load_more, on_search_api, items_per_load)

        self._chips_container = ft.Row(wrap=True, spacing=5, run_spacing=5)
        self._search_field.hint_text = label
        self._search_field.suffix_icon = ft.Icons.ARROW_DROP_DOWN
        self._search_field.border_color = ft.Colors.OUTLINE
        self._search_field.on_click = self._toggle_dropdown

        self._error_container = ft.Container(content=self._error_text,margin=ft.margin.only(left=12, top=4), visible=False)#The error message is wrapped in a container to be able to apply margin.

        self._bordered_content = ft.Container(
            content=ft.Column(
                controls=[self._chips_container, ft.Row([self._search_field], alignment=ft.MainAxisAlignment.START)],
                spacing=10,
            ),
            border=ft.border.all(1, ft.Colors.OUTLINE),
            border_radius=6,
            padding=10,
            bgcolor=ft.Colors.SURFACE,
        )

        self._main_column = ft.Column(controls=[self._bordered_content, self._dropdown_container, self._error_container], spacing=0, expand=False)

    def _is_selected(self, item_id: str) -> bool:
        return item_id in self._selected_values

    @property
    def value(self):
        return self._selected_values

    @property
    def selected_items(self):
        return self._selected_items

    def _update_chips(self):
        self._chips_container.controls.clear()
        for item in self._selected_items:
            item_id = item.get("id")
            chip = ft.Chip(
                label=ft.Text(item.get("text", "")),
                on_delete=lambda e, item_id=item_id: self._remove_item(item_id),
                bgcolor=ft.Colors.SECONDARY_CONTAINER,
                check_color=ft.Colors.ON_SECONDARY_CONTAINER,
                delete_icon_color=ft.Colors.ON_SECONDARY_CONTAINER
            )
            self._chips_container.controls.append(chip)

    def _remove_item(self, item_id):
        item_id_str = str(item_id)
        if item_id_str in self._selected_values:
            self._selected_values.remove(item_id_str)
            stored = self._data["results"].get(item_id_str)
            if stored:
                stored["selected"] = False
            self._selected_items = [i for i in self._selected_items if str(i["id"]) != item_id_str]
            self._update_chips()

            self.page.update()
            if self.on_change_cb:
                self.on_change_cb(self, self.value, self.selected_items)
            self._close_dropdown()

    def _select(self, item: dict):
        item_id = str(item["id"])
        stored = self._data["results"].get(item_id, item)
        if item_id not in self._selected_values:
            self._selected_values.append(item_id)
            self._selected_items.append(stored)
            stored["selected"] = True
            self._update_chips()
            self.page.update()
            if self.on_change_cb:
                self.on_change_cb(self, self.value, self.selected_items)
        self._close_dropdown()

class AutoCompleteSelectMultipleImage(_Select):
    """Multi-selection autocomplete with chips showing selected elements."""   
    def __init__(self, page, data=None, value=None, label="Select", on_change=None, 
                 on_load_more=None, on_search_api=None, expand=False, width=None, items_per_load=4):
        self._selected_values = []
        self._selected_items = []
        super().__init__(page, data, label, on_change, on_load_more, on_search_api, items_per_load)

        # Chips y campo de búsqueda
        self._chips_container = ft.Row(wrap=True, spacing=5, run_spacing=5)
        self._search_field.hint_text = label
        self._search_field.suffix_icon = ft.Icons.ARROW_DROP_DOWN
        self._search_field.border_color = ft.Colors.OUTLINE
        self._search_field.on_click = self._toggle_dropdown

        self._error_container = ft.Container(content=self._error_text,margin=ft.margin.only(left=12, top=4), visible=False)#The error message is wrapped in a container to be able to apply margin.
        self._bordered_content = ft.Container(
            content=ft.Column(
                controls=[self._chips_container, ft.Row([self._search_field], alignment=ft.MainAxisAlignment.START)],
                spacing=10,
            ),
            border=ft.border.all(1, ft.Colors.OUTLINE),
            border_radius=6,
            padding=10,
            bgcolor=ft.Colors.SURFACE,
        )

        self._main_column = ft.Column(
            controls=[self._bordered_content, self._dropdown_container, self._error_container],
            spacing=0,
            expand=False
        )

        # Inicializar selección externa
        if value:
            self.set_value(value)

    # ---------------------
    # Public API
    # ---------------------
    @property
    def control(self):
        return self._main_column

    @property
    def value(self):
        return self._selected_values

    @property
    def selected_items(self):
        return self._selected_items

    def set_value(self, ids: list[str]):
        self._selected_values.clear()
        self._selected_items.clear()
        for item_id in ids:
            item = self._data["results"].get(str(item_id))
            if item:
                item["selected"] = True
                self._selected_values.append(str(item_id))
                self._selected_items.append(item)
        self._update_chips()
        self.page.update()
        if self.on_change_cb:
            self.on_change_cb(self, self._selected_values, self._selected_items)

    def refresh_data(self, data: dict):
        """Reemplaza los items del dropdown sin perder la selección."""
        results = data.get("results", {})
        results_list = list(results.values()) if isinstance(results, dict) else results
        self._data["results"] = {str(item["id"]): dict(item) for item in results_list}
        # Mantener la selección actual
        for item in self._selected_items:
            id_str = str(item["id"])
            if id_str in self._data["results"]:
                self._data["results"][id_str]["selected"] = True
        self._refresh_options()
        self.page.update()

    def show_error(self, message: str):
        """Muestra un mensaje de error bajo el campo."""
        self._error_container.content.value = message
        self._error_container.visible = bool(message)
        self._main_column.update()

    # ---------------------
    # Internal logic
    # ---------------------
    def _is_selected(self, item_id: str) -> bool:
        return item_id in self._selected_values

    def _update_chips(self):
        self._chips_container.controls.clear()
        for item in self._selected_items:
            item_id = item.get("id")
            chip = ft.Chip(
                label=ft.Text(""),
                leading=ft.Image(src=item.get("image")) if item.get("image") else None,
                on_delete=lambda e, item_id=item_id: self._remove_item(item_id),
                bgcolor=ft.Colors.SECONDARY_CONTAINER,
                check_color=ft.Colors.ON_SECONDARY_CONTAINER,
                delete_icon_color=ft.Colors.ON_SECONDARY_CONTAINER,
            )
            self._chips_container.controls.append(chip)

    def _remove_item(self, item_id):
        item_id_str = str(item_id)
        if item_id_str in self._selected_values:
            self._selected_values.remove(item_id_str)
            stored = self._data["results"].get(item_id_str)
            if stored:
                stored["selected"] = False
            self._selected_items = [i for i in self._selected_items if str(i["id"]) != item_id_str]
            self._update_chips()
            self.page.update()
            if self.on_change_cb:
                self.on_change_cb(self, self._selected_values, self._selected_items)

    def _select(self, item: dict):
        item_id = str(item["id"])
        if item_id not in self._selected_values:
            self._selected_values.append(item_id)
            self._selected_items.append(item)
            item["selected"] = True
            self._update_chips()
            self.page.update()
            if self.on_change_cb:
                self.on_change_cb(self, self._selected_values, self._selected_items)
        self._close_dropdown()
    
    def clear(self):
        """Limpia la selección actual."""
        for item_id in list(self._selected_values):
            self._remove_item(item_id)
        self._selected_values = []
        self._selected_items = []
        self._update_chips()
        self.page.update()

