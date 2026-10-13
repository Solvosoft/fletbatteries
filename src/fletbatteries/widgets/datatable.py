"""
Tabla de datos con paginación, búsqueda, ordenamiento y filtros del lado del
servidor (equivalente a la integración de DataTables de djgentelella).

    table = DataTable(
        source=SQLAlchemySource(CustomerManager()),
        form=CustomerForm,                          # columnas = campos con list_display
        filter_form=CustomerFilterForm,             # opcional
        actions=[RowAction(ft.Icons.EDIT, "Editar", on_click=edit)],
        top_actions=[ft.Button(content="Nuevo", on_click=create)],
    )

Los filtros se arman a partir de un `Form`: texto -> `__icontains`, rangos ->
`__range`, selección múltiple -> `__in` y el resto por igualdad. Un formulario de
filtros puede definir `lookups = {"campo": "gte"}` para cambiarlo.
"""

import dataclasses
import logging
from typing import Any, Callable, Iterable, Optional, Sequence

import flet as ft

from fletbatteries.data.manager import EMPTY, Query
from fletbatteries.i18n import _
from fletbatteries.utils import safe_update

log = logging.getLogger(__name__)


@dataclasses.dataclass
class Column:
    name: str
    label: Optional[str] = None
    sortable: bool = True
    render: Optional[Callable[[Any, dict], Any]] = None
    field: Any = None
    numeric: bool = False

    def cell(self, item: dict) -> ft.Control:
        value = item.get(self.name)
        if self.render:
            result = self.render(value, item)
            return result if isinstance(result, ft.Control) else ft.Text(str(result))
        if self.field is not None:
            from fletbatteries.forms.fields import BooleanField

            if isinstance(self.field, BooleanField):
                return yes_no(value, item)
            return ft.Text(self.field.display(value))
        return ft.Text("" if value is None else str(value))


@dataclasses.dataclass
class RowAction:
    icon: Any
    tooltip: str
    on_click: Callable[[dict], Any]
    visible: Optional[Callable[[dict], bool]] = None
    color: Any = None
    name: Optional[str] = None

    def build(self, item: dict) -> Optional[ft.Control]:
        if self.visible and not self.visible(item):
            return None
        return ft.IconButton(
            icon=self.icon,
            tooltip=self.tooltip,
            icon_color=self.color,
            data=item.get("id"),
            key=f"{self.name}-{item.get('id')}" if self.name else None,
            on_click=lambda e, it=item: self.on_click(it),
        )


# ----------------------------------------------------------------------
# Renderers de celdas
# ----------------------------------------------------------------------
def yes_no(value, item=None) -> ft.Control:
    if value is None:
        return ft.Text("")
    return ft.Icon(ft.Icons.CHECK_CIRCLE if value else ft.Icons.CANCEL,
                   color=ft.Colors.GREEN_600 if value else ft.Colors.RED_400, size=18,
                   tooltip=_("Yes") if value else _("No"))


def link(url_key: Optional[str] = None, text: Optional[str] = None):
    def render(value, item):
        url = item.get(url_key) if url_key else value
        return ft.TextButton(text or str(value or ""), url=url) if url else ft.Text(str(value or ""))

    return render


def color_swatch(value, item=None) -> ft.Control:
    return ft.Container(width=18, height=18, border_radius=4, bgcolor=value or None,
                        border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT), tooltip=value or "")


def image(width: int = 40, height: int = 40, prefix: str = ""):
    def render(value, item):
        if not value:
            return ft.Text("")
        return ft.Image(src=f"{prefix}{value}", width=width, height=height, fit=ft.BoxFit.COVER, border_radius=4)

    return render


def list_text(value, item=None) -> ft.Control:
    return ft.Text(", ".join(str(v) for v in value or []))


# ----------------------------------------------------------------------
# Filtros
# ----------------------------------------------------------------------
def default_lookup(field) -> str:
    from fletbatteries.forms import fields as f

    if isinstance(field, (f.DateRangeField, f.RangeField)):
        return "range"
    if isinstance(field, (f.MultipleChoiceField, f.ModelMultipleChoiceField)):
        return "in"
    if isinstance(field, f.CharField) and not isinstance(field, f.ColorField):
        return "icontains"
    return ""


def filters_from_form(form) -> dict:
    """Arma el dict de filtros a partir de un formulario ya validado."""
    lookups = getattr(form, "lookups", {}) or {}
    filters = {}
    for name, value in form.cleaned_data.items():
        if value in EMPTY or value is False:
            continue
        lookup = lookups.get(name, default_lookup(form.fields[name]))
        filters[f"{name}__{lookup}" if lookup else name] = value
    return filters


def filter_form_for(form_class, names: Sequence[str]):
    """Crea una clase de formulario de filtros con los campos `names` de `form_class` (opcionales)."""
    import copy

    from fletbatteries.forms.form import DeclarativeFieldsMetaclass, Form

    attrs = {"render_type": "inline"}
    for name in names:
        field = copy.deepcopy(form_class.base_fields[name])
        field.required = False
        field.validators = []
        field.creation_counter = len(attrs)
        attrs[name] = field
    return DeclarativeFieldsMetaclass(f"{form_class.__name__}Filter", (Form,), attrs)


# ----------------------------------------------------------------------
# Tabla
# ----------------------------------------------------------------------
class DataTable(ft.Container):
    def __init__(
        self,
        source,
        columns: Optional[Iterable] = None,
        form=None,
        title: Optional[str] = None,
        actions: Sequence[RowAction] = (),
        top_actions: Sequence[ft.Control] = (),
        filter_form=None,
        page_size: int = 10,
        page_sizes: Sequence[int] = (5, 10, 25, 50),
        searchable: bool = True,
        selectable: bool = False,
        on_selection_change: Optional[Callable[[list], Any]] = None,
        order_by: Optional[str] = None,
        base_filters: Optional[dict] = None,
        auto_load: bool = True,
        **kwargs,
    ):
        kwargs.setdefault("expand", True)
        super().__init__(**kwargs)
        self.source = source
        self.base_filters = dict(base_filters or {})
        self.columns = self._build_columns(columns, form)
        self.actions = list(actions)
        self.page_size = page_size
        self.page_number = 1
        self.total = 0
        self.items: list[dict] = []
        self.search = ""
        self.order_by = order_by
        self.filters: dict = {}
        self.selectable = selectable
        self.selected_ids: set = set()
        self.on_selection_change = on_selection_change
        self.filter_form = filter_form() if isinstance(filter_form, type) else filter_form

        # --- Barra superior
        self.title_text = ft.Text(title or "", size=18, weight=ft.FontWeight.BOLD, visible=bool(title))
        self.search_field = ft.TextField(
            key="datatable_search",
            hint_text=_("Search..."),
            prefix_icon=ft.Icons.SEARCH,
            dense=True,
            width=260,
            visible=searchable,
            on_submit=self._on_search,
            on_change=self._on_search,
        )
        self.filter_button = ft.IconButton(
            icon=ft.Icons.FILTER_LIST, tooltip=_("Filter"), visible=self.filter_form is not None,
            on_click=self.toggle_filters,
        )
        self.selection_text = ft.Text("", visible=False)
        toolbar = ft.Row(
            [self.title_text, ft.Container(expand=True), self.selection_text, self.search_field, self.filter_button,
             *top_actions],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        # --- Panel de filtros
        self.filter_panel = ft.Container(visible=False)
        if self.filter_form is not None:
            self.filter_panel.content = ft.Column(
                [
                    self.filter_form.control,
                    ft.Row([
                        ft.Button(content=_("Filter"), icon=ft.Icons.FILTER_ALT, on_click=self.apply_filters,
                                  key="datatable_apply_filters"),
                        ft.TextButton(_("Clear filters"), icon=ft.Icons.FILTER_ALT_OFF, on_click=self.clear_filters),
                    ]),
                ],
                tight=True,
            )
            self.filter_panel.padding = 10
            self.filter_panel.border = ft.Border.all(1, ft.Colors.OUTLINE_VARIANT)
            self.filter_panel.border_radius = 8

        # --- Tabla
        self.table = ft.DataTable(
            columns=self._data_columns(),
            rows=[],
            show_checkbox_column=selectable,
            border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
            border_radius=8,
            horizontal_lines=ft.BorderSide(1, ft.Colors.OUTLINE_VARIANT),
            heading_row_color=ft.Colors.SURFACE_CONTAINER_HIGHEST,
        )
        self.error_text = ft.Text("", color=ft.Colors.ERROR, visible=False)

        # --- Paginación
        self.page_size_dropdown = ft.Dropdown(
            key="datatable_page_size",
            width=90,
            dense=True,
            value=str(page_size),
            options=[ft.DropdownOption(str(s)) for s in sorted(set(page_sizes) | {page_size})],
            on_select=lambda e: self.set_page_size(int(e.control.value)),
        )
        self.btn_first = ft.IconButton(icon=ft.Icons.FIRST_PAGE, tooltip=_("First page"), on_click=lambda e: self.go(1))
        self.btn_prev = ft.IconButton(icon=ft.Icons.CHEVRON_LEFT, tooltip=_("Previous page"),
                                      on_click=lambda e: self.go(self.page_number - 1))
        self.btn_next = ft.IconButton(icon=ft.Icons.CHEVRON_RIGHT, tooltip=_("Next page"),
                                      on_click=lambda e: self.go(self.page_number + 1))
        self.btn_last = ft.IconButton(icon=ft.Icons.LAST_PAGE, tooltip=_("Last page"),
                                      on_click=lambda e: self.go(self.pages))
        self.page_info = ft.Text(size=12, key="datatable_page_info")
        pagination = ft.Row(
            [ft.Text(_("Rows:"), size=12), self.page_size_dropdown,
             self.btn_first, self.btn_prev, self.page_info, self.btn_next, self.btn_last],
            alignment=ft.MainAxisAlignment.END,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            wrap=True,
        )

        self.content = ft.Column(
            [
                toolbar,
                self.filter_panel,
                self.error_text,
                ft.Row([self.table], scroll=ft.ScrollMode.AUTO),
                pagination,
            ],
            spacing=8,
            scroll=ft.ScrollMode.AUTO,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        )
        if auto_load:
            self.load()

    # ------------------------------------------------------------------
    # Columnas
    # ------------------------------------------------------------------
    def _build_columns(self, columns, form) -> list[Column]:
        result = []
        fields = getattr(form, "base_fields", {}) if form is not None else {}
        if columns is None:
            columns = [name for name, field in fields.items() if field.list_display]
        for col in columns:
            if isinstance(col, Column):
                if col.field is None and col.name in fields:
                    col.field = fields[col.name]
                if col.label is None:
                    col.label = col.field.label if col.field is not None else col.name.replace("_", " ").capitalize()
                result.append(col)
            else:
                field = fields.get(col)
                label = field.label if field is not None and field.label else col.replace("_", " ").capitalize()
                result.append(Column(name=col, label=label, field=field))
        return result

    def _data_columns(self) -> list[ft.DataColumn]:
        cols = [
            ft.DataColumn(
                label=ft.Text(c.label, weight=ft.FontWeight.BOLD),
                numeric=c.numeric,
                on_sort=self._on_sort if c.sortable else None,
            )
            for c in self.columns
        ]
        if self.actions:
            cols.append(ft.DataColumn(label=ft.Text(_("Actions"), weight=ft.FontWeight.BOLD)))
        return cols

    # ------------------------------------------------------------------
    # Datos
    # ------------------------------------------------------------------
    @property
    def pages(self) -> int:
        return max(1, -(-self.total // self.page_size)) if self.page_size else 1

    def query(self) -> Query:
        return Query(page=self.page_number, size=self.page_size, search=self.search,
                     filters={**self.filters, **self.base_filters}, order_by=self.order_by)

    def load(self):
        try:
            result = self.source.list(self.query())
            self.items, self.total = result.items, result.total
            self.error_text.visible = False
        except Exception as ex:
            log.exception("Error cargando datos de la tabla")
            self.items, self.total = [], 0
            self.error_text.value = str(ex) or _("Sorry, an error occurred")
            self.error_text.visible = True
        if self.page_number > self.pages:
            self.page_number = self.pages
            return self.load()
        self._render_rows()
        self._render_pagination()
        safe_update(self)

    reload = load

    def _render_rows(self):
        rows = []
        for item in self.items:
            cells = [ft.DataCell(c.cell(item)) for c in self.columns]
            if self.actions:
                buttons = [b for b in (a.build(item) for a in self.actions) if b is not None]
                cells.append(ft.DataCell(ft.Row(buttons, spacing=0, tight=True)))
            row = ft.DataRow(cells=cells, data=item.get("id"))
            if self.selectable:
                row.selected = item.get("id") in self.selected_ids
                row.on_select_change = lambda e, pk=item.get("id"): self._toggle_selected(pk, e.data)
            rows.append(row)
        if not rows:
            empty = [ft.DataCell(ft.Text(_("No records"), italic=True, color=ft.Colors.OUTLINE))]
            empty += [ft.DataCell(ft.Text("")) for _i in range(len(self.table.columns) - 1)]
            rows.append(ft.DataRow(cells=empty))
        self.table.rows = rows

    def _render_pagination(self):
        if self.total == 0:
            info = _("{start}–{end} of {total}", start=0, end=0, total=0)
        else:
            start = (self.page_number - 1) * self.page_size + 1
            end = min(start + self.page_size - 1, self.total)
            info = (_("{start}–{end} of {total}", start=start, end=end, total=self.total)
                    + f"  ({_('page {page}/{pages}', page=self.page_number, pages=self.pages)})")
        self.page_info.value = info
        self.btn_first.disabled = self.btn_prev.disabled = self.page_number <= 1
        self.btn_last.disabled = self.btn_next.disabled = self.page_number >= self.pages
        self.selection_text.visible = self.selectable and bool(self.selected_ids)
        self.selection_text.value = _("{count} selected", count=len(self.selected_ids))

    # ------------------------------------------------------------------
    # Eventos
    # ------------------------------------------------------------------
    def go(self, page_number: int):
        self.page_number = min(max(1, page_number), self.pages)
        self.load()

    def set_page_size(self, size: int):
        self.page_size = max(1, int(size))
        self.page_number = 1
        self.load()

    def _on_search(self, e):
        value = self.search_field.value or ""
        if value != self.search:
            self.search = value
            self.page_number = 1
            self.load()

    def _on_sort(self, e):
        column = self.columns[e.column_index]
        self.order_by = column.name if e.ascending else f"-{column.name}"
        self.table.sort_column_index = e.column_index
        self.table.sort_ascending = e.ascending
        self.page_number = 1
        self.load()

    def sort_by(self, name: str, ascending: bool = True):
        index = next(i for i, c in enumerate(self.columns) if c.name == name)
        self._on_sort(ft.DataColumnSortEvent(name="sort", control=self.table, column_index=index,
                                             ascending=ascending))

    def toggle_filters(self, e=None):
        self.filter_panel.visible = not self.filter_panel.visible
        safe_update(self)

    def apply_filters(self, e=None):
        if not self.filter_form.is_valid():
            return
        self.filters = filters_from_form(self.filter_form)
        self.page_number = 1
        self.load()

    def clear_filters(self, e=None):
        if self.filter_form is not None:
            self.filter_form.clear()
        self.filters = {}
        self.search = ""
        self.search_field.value = ""
        self.page_number = 1
        self.load()

    def set_filters(self, **filters):
        self.filters = {k: v for k, v in filters.items() if v not in EMPTY}
        self.page_number = 1
        self.load()

    def _toggle_selected(self, pk, selected):
        if str(selected).lower() == "true" or selected is True:
            self.selected_ids.add(pk)
        else:
            self.selected_ids.discard(pk)
        self._render_rows()
        self._render_pagination()
        safe_update(self)
        if self.on_selection_change:
            self.on_selection_change(self.selected_items)

    @property
    def selected_items(self) -> list[dict]:
        return [i for i in self.items if i.get("id") in self.selected_ids]
