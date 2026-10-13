"""
Selects con búsqueda tipo Select2 (equivalentes a AutocompleteSelect de djgentelella).

Los datos siguen el formato de las APIs de lookup:

    {"results": {"1": {"id": 1, "text": "Costa Rica", "disabled": False, "image": None}},
     "pagination": {"more": True}}

Pueden venir de:
- `data` / `choices`: datos locales (la búsqueda se hace en memoria).
- `source`: objeto con `lookup(skip, limit, q) -> dict` (p. ej. un `DataSource`).
- `on_load_more(skip, limit, q)` y `on_search_api(skip=, limit=, filter_text=)`: callbacks.
"""

import asyncio
import unicodedata
from typing import Any, Callable, Optional

import flet as ft

from fletbatteries.i18n import _
from fletbatteries.widgets.base import Widget


def normalize_text(text: str) -> str:
    """Quita tildes y pasa a minúsculas para comparar textos."""
    if not text:
        return ""
    normalized = unicodedata.normalize("NFD", str(text).lower().strip())
    return "".join(c for c in normalized if unicodedata.category(c) != "Mn")


def choices_to_data(choices) -> dict:
    if callable(choices):
        choices = choices()
    if isinstance(choices, dict):
        choices = list(choices.items())
    results = {}
    for c in choices or []:
        key, text = (c[0], c[1]) if isinstance(c, (tuple, list)) else (c, c)
        results[str(key)] = {"id": key, "text": str(text)}
    return {"results": results, "pagination": {"more": False}}


def results_list(data: dict) -> list:
    results = (data or {}).get("results", {})
    return list(results.values()) if isinstance(results, dict) else list(results)


class _Select(Widget):
    """Base de los selects con dropdown, búsqueda, scroll infinito y debounce."""

    show_search_in_dropdown = True

    def __init__(
        self,
        label: Optional[str] = None,
        help_text: Optional[str] = None,
        data: Optional[dict] = None,
        choices=None,
        source=None,
        on_select: Optional[Callable] = None,
        on_load_more: Optional[Callable] = None,
        on_search_api: Optional[Callable] = None,
        items_per_load: int = 10,
        search_delay: float = 0.3,
        width=None,
        expand=False,
        **kwargs,
    ):
        super().__init__(label=label or _("Select..."), help_text=help_text, width=width, expand=expand, **kwargs)
        self.source = source
        self.lookup_filters: dict = {}
        self.on_select = on_select
        self.on_load_more_cb = on_load_more or (self._source_lookup if source is not None else None)
        self.on_search_api_cb = on_search_api or (self._source_search if source is not None else None)
        self.items_per_load = items_per_load
        self.search_delay = search_delay
        self._loaded = source is None

        self._data: dict[str, Any] = {"results": {}, "pagination": {"more": False}}
        self._is_dropdown_open = False
        self._dropdown_max_height = 200
        self._dropdown_item_height = 40
        self._blur_timer = None
        self._is_interacting = False
        self._search_timer = None

        self._error_text = ft.Text(color=ft.Colors.ERROR, size=12)
        self._search_field = ft.TextField(
            hint_text=_("Search..."),
            on_change=self._on_search,
            on_blur=self._handle_blur,
            on_focus=self._handle_focus,
            expand=True,
            dense=True,
        )
        self._results_list = ft.ListView(spacing=2, padding=10, on_scroll=self._on_scroll, auto_scroll=False)
        self._results_container = ft.Container(content=self._results_list, expand=False, height=None)

        dropdown_content = []
        if self.show_search_in_dropdown:
            dropdown_content.append(self._search_field)
        dropdown_content.append(self._results_container)

        self._dropdown_container = ft.Container(
            content=ft.Column(controls=dropdown_content, spacing=0),
            border=ft.Border.all(1, ft.Colors.OUTLINE),
            border_radius=5,
            padding=5,
            visible=False,
            bgcolor=ft.Colors.SURFACE,
            shadow=ft.BoxShadow(spread_radius=1, blur_radius=5, color=ft.Colors.BLACK_38),
            on_hover=self._on_dropdown_hover,
            on_click=self._handle_dropdown_click,
        )

        if choices is not None and data is None:
            data = choices_to_data(choices)
        self._initial_data = data

    def _finish_init(self):
        """Lo llaman las subclases cuando ya crearon sus controles."""
        if self._initial_data:
            self.set_data(self._initial_data)

    # ------------------------------------------------------------------
    # Fuentes de datos
    # ------------------------------------------------------------------
    def _source_lookup(self, skip, limit, filter_text=""):
        return self.source.lookup(skip=skip, limit=limit, q=filter_text, filters=self.lookup_filters)

    def _source_search(self, skip=0, limit=10, filter_text=""):
        return self.source.lookup(skip=skip, limit=limit, q=filter_text, filters=self.lookup_filters)

    def set_lookup_filters(self, filters: dict):
        """Cambia los filtros de la fuente remota y vuelve a cargar las opciones al abrir."""
        self.lookup_filters = dict(filters)
        self._data = {"results": {}, "pagination": {"more": False}}
        self._loaded = self.source is None
        self._clear_selection()
        self._refresh_options()

    def _ensure_item(self, key) -> Optional[dict]:
        """Busca el item `key`; si no está cargado y hay `source`, pide su etiqueta."""
        item = self._data["results"].get(str(key))
        if item is None and self.source is not None and hasattr(self.source, "label_for"):
            text = self.source.label_for(key)
            if text is not None:
                item = {"id": key, "text": text}
                self._data["results"][str(key)] = item
        return item

    def _load_initial(self):
        if self._loaded or self.on_search_api_cb is None:
            return
        self._loaded = True

        async def bg_load():
            data = await asyncio.to_thread(self.on_search_api_cb, skip=0, limit=self.items_per_load, filter_text="")
            if data:
                self.append_data(results_list(data), bool(data.get("pagination", {}).get("more", False)))
                self.refresh()

        self.app_page.run_task(bg_load)

    # ------------------------------------------------------------------
    # Eventos internos
    # ------------------------------------------------------------------
    def _run_later(self, delay: float, callback):
        """Ejecuta `callback` en el loop de la página tras `delay` segundos; devuelve un Future cancelable."""

        async def run():
            await asyncio.sleep(delay)
            callback()

        page = self.app_page
        return page.run_task(run) if page else None

    def _on_scroll(self, e: ft.OnScrollEvent):
        if e.pixels >= e.max_scroll_extent - 10 and self._data["pagination"].get("more") and self.on_load_more_cb:
            skip = len(self._data["results"])
            filter_text = self._search_field.value or ""

            async def bg_load():
                data = await asyncio.to_thread(self.on_load_more_cb, skip, self.items_per_load, filter_text)
                if not data or "results" not in data:
                    return
                self.append_data(results_list(data), bool(data.get("pagination", {}).get("more", False)))
                self.refresh()

            self.app_page.run_task(bg_load)

    def _on_search(self, e):
        if self._search_timer:
            self._search_timer.cancel()
        self._search_timer = self._run_later(self.search_delay, self._execute_search)

    def _execute_search(self):
        filter_text = self._search_field.value or ""
        if self.on_search_api_cb:

            async def bg_search():
                data = await asyncio.to_thread(
                    self.on_search_api_cb, skip=0, limit=self.items_per_load, filter_text=filter_text
                )
                if data and "results" in data:
                    found = results_list(data)
                    # Guarda los items encontrados para poder seleccionarlos
                    for item in found:
                        self._data["results"].setdefault(str(item["id"]), dict(item))
                    self._refresh_options(filtered_results=found)
                    self.refresh()

            self.app_page.run_task(bg_search)
        else:
            self._refresh_options(filter_text)
            self.refresh()

    def _on_dropdown_hover(self, e):
        self._is_interacting = e.data == "true" or e.data is True

    def _handle_dropdown_click(self, e):
        self._is_interacting = True
        if self._blur_timer:
            self._blur_timer.cancel()
            self._blur_timer = None
        self.app_page.run_task(self._search_field.focus)
        self._run_later(0.1, lambda: setattr(self, "_is_interacting", False))

    def _handle_focus(self, e):
        if self._blur_timer:
            self._blur_timer.cancel()
            self._blur_timer = None

    def _handle_blur(self, e):
        if self._blur_timer:
            self._blur_timer.cancel()
        self._blur_timer = self._run_later(0.15, self._delayed_close)

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
        self._run_later(0.1, lambda: setattr(self, "_is_interacting", False))

    def _open_dropdown(self):
        self._is_dropdown_open = True
        self._search_field.value = ""
        self._refresh_options()
        self._dropdown_container.visible = True
        self.refresh()
        self._load_initial()

    def _close_dropdown(self):
        self._is_dropdown_open = False
        self._dropdown_container.visible = False
        self.refresh()

    # ------------------------------------------------------------------
    # Datos
    # ------------------------------------------------------------------
    def append_data(self, results, more: bool = False):
        """Agrega resultados conservando la selección."""
        if isinstance(results, dict):
            results = list(results.values())
        for item in results:
            id_str = str(item["id"])
            stored = self._data["results"].get(id_str)
            if stored:
                self._data["results"][id_str] = {**item, "selected": stored.get("selected", False)}
            else:
                self._data["results"][id_str] = dict(item)
        self._data["pagination"]["more"] = bool(more)
        self._refresh_options(self._search_field.value or "")

    def set_data(self, data: dict):
        """Reemplaza todos los resultados."""
        items = results_list(data)
        pagination = (data or {}).get("pagination", {}) or {}
        self._data["results"] = {str(item["id"]): dict(item) for item in items}
        self._data["pagination"] = {"more": bool(pagination.get("more", False))}
        self._loaded = True
        self._clear_selection()
        self._refresh_options()
        for item in items:
            if item.get("selected"):
                self._select(self._data["results"][str(item["id"])], notify=False)
                if not self.multiple:
                    break

    def set_choices(self, choices):
        self.set_data(choices_to_data(choices))

    def _refresh_options(self, filter_text="", filtered_results=None):
        self._results_list.controls.clear()
        filter_text = normalize_text(filter_text)
        to_show = filtered_results if filtered_results is not None else list(self._data["results"].values())

        for item in to_show:
            text = str(item.get("text", ""))
            item_id = str(item.get("id", ""))
            if filter_text and filter_text not in normalize_text(text):
                continue
            is_selected = self._is_selected(item_id)
            disabled = bool(item.get("disabled", False))
            label = ft.Text(text, color=ft.Colors.OUTLINE if disabled else ft.Colors.ON_SURFACE)
            content = label
            if item.get("image"):
                content = ft.Row([ft.Image(src=item["image"], width=24, height=24, border_radius=12), label],
                                 spacing=8)
            # Sin `expand`: un hijo expandido dentro de un ListView no se puede dibujar en Flutter
            self._results_list.controls.append(
                ft.Container(
                    content=content,
                    data=item_id,
                    key=f"option-{item_id}",
                    padding=ft.Padding.symmetric(horizontal=12, vertical=8),
                    border_radius=4,
                    bgcolor=ft.Colors.SECONDARY_CONTAINER if is_selected else None,
                    ink=not disabled,
                    disabled=disabled,
                    on_click=None if disabled else (lambda e, i=item: self._handle_option_click(i)),
                )
            )

        if not self._results_list.controls:
            self._results_list.controls.append(ft.Text(_("No results found"), color=ft.Colors.OUTLINE, italic=True))

        self._results_container.height = min(
            max(1, len(self._results_list.controls)) * self._dropdown_item_height + 20, self._dropdown_max_height
        )

    def _handle_option_click(self, item):
        self._select(self._data["results"].get(str(item["id"]), item))

    @property
    def options(self) -> list[dict]:
        return list(self._data["results"].values())

    @property
    def control(self):
        """Compatibilidad: antes el select exponía su control en `.control`."""
        return self

    # A implementar
    multiple = False

    def _is_selected(self, item_id: str) -> bool:
        raise NotImplementedError

    def _select(self, item: dict, notify: bool = True):
        raise NotImplementedError

    def _clear_selection(self):
        raise NotImplementedError

    def _emit_selection(self, items):
        if self.on_select:
            self.on_select(self, self.value, items)
        self.changed()


class AutocompleteSelect(_Select):
    """Selección única con búsqueda."""

    def __init__(self, label=None, help_text=None, **kwargs):
        self._selected_value = None
        super().__init__(label=label, help_text=help_text, **kwargs)
        self._text_field = ft.TextField(
            label=self.label,
            helper=help_text,
            read_only=True,
            expand=self.expand,
            suffix_icon=ft.Icons.ARROW_DROP_DOWN,
            on_click=self._toggle_dropdown,
            on_blur=self._handle_blur,
            on_focus=self._handle_focus,
        )
        self.content = ft.Column(controls=[self._text_field, self._dropdown_container], spacing=5,
                                 horizontal_alignment=ft.CrossAxisAlignment.STRETCH)
        self._finish_init()

    def _is_selected(self, item_id: str) -> bool:
        return self._selected_value == item_id

    @property
    def selected_item(self):
        return self._data["results"].get(self._selected_value) if self._selected_value else None

    def _clear_selection(self):
        self._selected_value = None
        self._text_field.value = ""

    def _select(self, item: dict, notify: bool = True):
        if self._selected_value:
            prev = self._data["results"].get(self._selected_value)
            if prev:
                prev["selected"] = False
        item_id = str(item["id"])
        stored = self._data["results"].setdefault(item_id, item)
        stored["selected"] = True
        self._selected_value = item_id
        self._text_field.value = str(stored.get("text", ""))
        self._close_dropdown()
        if notify:
            self._emit_selection(self.selected_item)

    def get_value(self):
        return self._selected_value

    def set_value(self, value):
        if value in (None, ""):
            self._clear_selection()
            return
        item = self._ensure_item(value)
        if item:
            self._select(item, notify=False)

    def show_error(self, message):
        self._text_field.error = message

    def apply_label(self, label):
        self._text_field.label = label


class AutocompleteSelectMultiple(_Select):
    """Selección múltiple con chips."""

    multiple = True
    show_search_in_dropdown = False

    def __init__(self, label=None, help_text=None, **kwargs):
        self._selected_values: list[str] = []
        self._selected_items: list[dict] = []
        super().__init__(label=label, help_text=help_text, **kwargs)
        self._chips_container = ft.Row(wrap=True, spacing=5, run_spacing=5)
        self._search_field.hint_text = self.label
        self._search_field.suffix_icon = ft.Icons.ARROW_DROP_DOWN
        self._search_field.on_click = self._toggle_dropdown
        self._error_container = ft.Container(
            content=self._error_text, margin=ft.Margin.only(left=12, top=4), visible=False
        )
        self._bordered_content = ft.Container(
            content=ft.Column(
                controls=[self._chips_container, ft.Row([self._search_field], alignment=ft.MainAxisAlignment.START)],
                spacing=10,
            ),
            border=ft.Border.all(1, ft.Colors.OUTLINE),
            border_radius=6,
            padding=10,
            bgcolor=ft.Colors.SURFACE,
        )
        self.content = ft.Column(
            controls=[self._bordered_content, self._dropdown_container, self._error_container], spacing=0,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        )
        self._finish_init()

    def _is_selected(self, item_id: str) -> bool:
        return item_id in self._selected_values

    @property
    def selected_items(self):
        return self._selected_items

    def _update_chips(self):
        self._chips_container.controls = [
            ft.Chip(
                label=ft.Text(item.get("text", "")),
                leading=ft.Image(src=item["image"], width=20, height=20) if item.get("image") else None,
                on_delete=lambda e, item_id=item.get("id"): self._remove_item(item_id),
                bgcolor=ft.Colors.SECONDARY_CONTAINER,
                delete_icon_color=ft.Colors.ON_SECONDARY_CONTAINER,
            )
            for item in self._selected_items
        ]

    def _remove_item(self, item_id):
        item_id_str = str(item_id)
        if item_id_str in self._selected_values:
            self._selected_values.remove(item_id_str)
            stored = self._data["results"].get(item_id_str)
            if stored:
                stored["selected"] = False
            self._selected_items = [i for i in self._selected_items if str(i["id"]) != item_id_str]
            self._update_chips()
            self._close_dropdown()
            self._emit_selection(self.selected_items)

    def _clear_selection(self):
        self._selected_values = []
        self._selected_items = []
        if hasattr(self, "_chips_container"):
            self._update_chips()

    def _select(self, item: dict, notify: bool = True):
        item_id = str(item["id"])
        stored = self._data["results"].setdefault(item_id, item)
        if item_id not in self._selected_values:
            self._selected_values.append(item_id)
            self._selected_items.append(stored)
            stored["selected"] = True
            self._update_chips()
            if notify:
                self._emit_selection(self.selected_items)
        self._close_dropdown()

    def get_value(self):
        return list(self._selected_values)

    def set_value(self, values):
        for item in self._data["results"].values():
            item["selected"] = False
        self._clear_selection()
        for v in values or []:
            item = self._ensure_item(v)
            if item:
                self._select(item, notify=False)
        self._update_chips()

    def show_error(self, message):
        self._error_text.value = message or ""
        self._bordered_content.border = ft.Border.all(1, ft.Colors.ERROR if message else ft.Colors.OUTLINE)
        self._error_container.visible = bool(message)


class AutocompleteSelectImage(AutocompleteSelect):
    """Igual que AutocompleteSelect; cada opción puede traer `image` (URL o asset)."""


class AutocompleteSelectMultipleImage(AutocompleteSelectMultiple):
    """Igual que AutocompleteSelectMultiple con imágenes en opciones y chips."""
