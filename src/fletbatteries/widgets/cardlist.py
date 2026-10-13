"""
Lista de tarjetas paginada con búsqueda (equivalente a `CardList` de djgentelella).

    CardList(source, card=lambda item: ft.Text(item["name"]), actions=[RowAction(...)])

Las páginas siguientes se cargan con el botón "Cargar más" o al llegar al final
del scroll.
"""

from typing import Any, Callable, Optional, Sequence

import flet as ft

from fletbatteries.data.manager import Query
from fletbatteries.i18n import _
from fletbatteries.utils import safe_update
from fletbatteries.widgets.datatable import RowAction


def default_card(fields: Sequence[str], title_field: Optional[str] = None, image_field: Optional[str] = None,
                 image_prefix: str = "", form=None) -> Callable[[dict], ft.Control]:
    """Tarjeta simple: imagen opcional, título y una línea por campo (con etiquetas y formato del `form`)."""
    form_fields = getattr(form, "base_fields", {}) if form is not None else {}

    def label(name):
        field = form_fields.get(name)
        return field.label if field is not None and field.label else name.replace("_", " ").capitalize()

    def display(name, value):
        field = form_fields.get(name)
        return field.display(value) if field is not None else ("" if value is None else str(value))

    def build(item: dict) -> ft.Control:
        controls = []
        if image_field and item.get(image_field):
            controls.append(ft.Image(src=f"{image_prefix}{item[image_field]}", height=120, fit=ft.BoxFit.COVER,
                                     border_radius=6))
        if title_field:
            controls.append(ft.Text(display(title_field, item.get(title_field)), size=16, weight=ft.FontWeight.BOLD))
        for name in fields:
            if name in (title_field, image_field):
                continue
            controls.append(ft.Text(f"{label(name)}: {display(name, item.get(name))}", size=12))
        return ft.Column(controls, spacing=4, tight=True)

    return build


class CardList(ft.Container):
    def __init__(
        self,
        source,
        card: Callable[[dict], ft.Control],
        title: Optional[str] = None,
        actions: Sequence[RowAction] = (),
        top_actions: Sequence[ft.Control] = (),
        page_size: int = 12,
        card_width: int = 260,
        searchable: bool = True,
        filters: Optional[dict] = None,
        order_by: Optional[str] = None,
        auto_load: bool = True,
        **kwargs: Any,
    ):
        kwargs.setdefault("expand", True)
        super().__init__(**kwargs)
        self.source = source
        self.card_builder = card
        self.actions = list(actions)
        self.page_size = page_size
        self.card_width = card_width
        self.filters = dict(filters or {})
        self.order_by = order_by
        self.search = ""
        self.loaded_pages = 0
        self.total = 0
        self.items: list[dict] = []

        self.search_field = ft.TextField(
            key="cardlist_search", hint_text=_("Search..."), prefix_icon=ft.Icons.SEARCH, dense=True, width=260,
            visible=searchable, on_change=self._on_search, on_submit=self._on_search,
        )
        self.grid = ft.Row(wrap=True, spacing=12, run_spacing=12)
        self.empty_text = ft.Text(_("No records"), italic=True, color=ft.Colors.OUTLINE, visible=False)
        self.more_button = ft.TextButton(_("Load more"), icon=ft.Icons.EXPAND_MORE, key="cardlist_more",
                                         on_click=lambda e: self.load_more(), visible=False)
        self.content = ft.Column(
            [
                ft.Row([ft.Text(title or "", size=18, weight=ft.FontWeight.BOLD, visible=bool(title)),
                        ft.Container(expand=True), self.search_field, *top_actions],
                       vertical_alignment=ft.CrossAxisAlignment.CENTER),
                self.grid,
                self.empty_text,
                ft.Row([self.more_button], alignment=ft.MainAxisAlignment.CENTER),
            ],
            spacing=10,
            scroll=ft.ScrollMode.AUTO,
            on_scroll=self._on_scroll,
        )
        if auto_load:
            self.reload()

    def _card(self, item: dict) -> ft.Control:
        buttons = [b for b in (a.build(item) for a in self.actions) if b is not None]
        body = self.card_builder(item)
        return ft.Card(
            width=self.card_width,
            data=item.get("id"),
            content=ft.Container(
                padding=12,
                content=ft.Column(
                    [body, ft.Row(buttons, alignment=ft.MainAxisAlignment.END, spacing=0)] if buttons else [body],
                    spacing=8,
                    tight=True,
                ),
            ),
        )

    def reload(self):
        self.loaded_pages = 0
        self.items = []
        self.grid.controls = []
        self.load_more()

    def load_more(self):
        page = self.source.list(Query(page=self.loaded_pages + 1, size=self.page_size, search=self.search,
                                      filters=self.filters, order_by=self.order_by))
        self.loaded_pages += 1
        self.total = page.total
        self.items.extend(page.items)
        self.grid.controls.extend(self._card(i) for i in page.items)
        self.empty_text.visible = not self.items
        self.more_button.visible = len(self.items) < self.total
        safe_update(self)

    @property
    def has_more(self) -> bool:
        return len(self.items) < self.total

    def _on_search(self, e):
        value = self.search_field.value or ""
        if value != self.search:
            self.search = value
            self.reload()

    def _on_scroll(self, e: ft.OnScrollEvent):
        if e.pixels >= e.max_scroll_extent - 40 and self.has_more:
            self.load_more()

    def set_filters(self, **filters):
        self.filters = dict(filters)
        self.reload()
