"""Selects avanzados: con botón "+", dos paneles, árbol y etiquetas (tagging)."""

import re
from typing import Callable, Optional

import flet as ft

from fletbatteries.i18n import _
from fletbatteries.widgets.base import LabeledWidget, Widget
from fletbatteries.widgets.inputs import Select, _normalize_choices
from fletbatteries.widgets.modals import CrudModal
from fletbatteries.widgets.selects import normalize_text

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class SelectWithAdd(Widget):
    """
    Select con un botón "+" que abre un formulario para crear una opción nueva.

    `add_form` es una clase `Form`; `on_add(cleaned_data)` guarda el registro y
    devuelve `(key, text)` de la opción creada, que queda seleccionada.
    """

    def __init__(
        self,
        label=None,
        help_text=None,
        choices=(),
        add_form=None,
        on_add: Optional[Callable[[dict], tuple]] = None,
        add_title: Optional[str] = None,
        **kwargs,
    ):
        super().__init__(label=label, help_text=help_text, **kwargs)
        self.select = Select(label=label, help_text=help_text, choices=choices, expand=True)
        self.select.add_change_listener(self.changed)
        self.add_form = add_form
        self.on_add = on_add
        self.add_title = add_title or _("Add {name}", name=label or "")
        self.add_button = ft.IconButton(icon=ft.Icons.ADD, tooltip=_("Add"), on_click=self.open_add)
        self.content = ft.Row([self.select, self.add_button], vertical_alignment=ft.CrossAxisAlignment.START)

    def open_add(self, e=None):
        form = self.add_form()
        modal = CrudModal(self.app_page)

        def accept():
            if not form.is_valid():
                return None
            key, text = self.on_add(form.cleaned_data)
            self.select.set_choices(self.select.choices + [(str(key), str(text))])
            self.select.set_value(key)
            self.refresh()
            self.changed()
            return True

        modal.open("create", self.add_title, [form.control], on_accept=accept)

    @property
    def choices(self):
        return self.select.choices

    def set_choices(self, choices):
        self.select.set_choices(choices)

    def get_value(self):
        return self.select.get_value()

    def set_value(self, value):
        self.select.set_value(value)

    def show_error(self, message):
        self.select.show_error(message)

    def apply_label(self, label):
        self.select.apply_label(label)


class FilteredSelectMultiple(LabeledWidget):
    """Dos paneles "disponibles / elegidos" con búsqueda (como el admin de Django)."""

    def __init__(self, label=None, help_text=None, choices=(), height: int = 220, **kwargs):
        self.search = ft.TextField(hint_text=_("Filter"), dense=True, prefix_icon=ft.Icons.SEARCH,
                                   on_change=lambda e: self._render())
        self.available_list = ft.ListView(height=height, spacing=0)
        self.chosen_list = ft.ListView(height=height, spacing=0)
        self._marked_available: set[str] = set()
        self._marked_chosen: set[str] = set()
        self._chosen: list[str] = []

        def panel(title, lst, footer):
            return ft.Container(
                expand=True,
                border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
                border_radius=6,
                padding=6,
                content=ft.Column([ft.Text(title, weight=ft.FontWeight.BOLD), lst, footer], spacing=4, tight=True),
            )

        buttons = ft.Column(
            [
                ft.IconButton(icon=ft.Icons.ARROW_FORWARD, tooltip=_("Add"),
                              on_click=lambda e: self._move(True)),
                ft.IconButton(icon=ft.Icons.ARROW_BACK, tooltip=_("Remove"), on_click=lambda e: self._move(False)),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            tight=True,
        )
        body = ft.Column(
            [
                self.search,
                ft.Row(
                    [
                        panel(_("Available"), self.available_list,
                              ft.TextButton(_("Choose all"), on_click=lambda e: self._move_all(True))),
                        buttons,
                        panel(_("Chosen"), self.chosen_list,
                              ft.TextButton(_("Remove all"), on_click=lambda e: self._move_all(False))),
                    ],
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            ],
            tight=True,
        )
        super().__init__(body, label=label, help_text=help_text, **kwargs)
        self.set_choices(choices)

    def set_choices(self, choices):
        self.choices = _normalize_choices(choices)
        keys = {k for k, _t in self.choices}
        self._chosen = [k for k in self._chosen if k in keys]
        self._render()

    def _item(self, key, text, marked: set):
        def toggle(e):
            marked.symmetric_difference_update({key})
            self._render()
            self.refresh()

        return ft.Container(
            content=ft.Text(text),
            data=key,
            padding=ft.Padding.symmetric(horizontal=8, vertical=6),
            bgcolor=ft.Colors.SECONDARY_CONTAINER if key in marked else None,
            border_radius=4,
            on_click=toggle,
        )

    def _render(self):
        q = normalize_text(self.search.value or "")
        texts = dict(self.choices)
        self.available_list.controls = [
            self._item(k, t, self._marked_available)
            for k, t in self.choices
            if k not in self._chosen and (not q or q in normalize_text(t))
        ]
        self.chosen_list.controls = [self._item(k, texts[k], self._marked_chosen) for k in self._chosen if k in texts]

    def _move(self, to_chosen: bool):
        if to_chosen:
            self._chosen += [k for k, _t in self.choices if k in self._marked_available and k not in self._chosen]
            self._marked_available.clear()
        else:
            self._chosen = [k for k in self._chosen if k not in self._marked_chosen]
            self._marked_chosen.clear()
        self._render()
        self.refresh()
        self.changed()

    def _move_all(self, to_chosen: bool):
        if to_chosen:
            q = normalize_text(self.search.value or "")
            self._chosen += [k for k, t in self.choices
                             if k not in self._chosen and (not q or q in normalize_text(t))]
        else:
            self._chosen = []
        self._marked_available.clear()
        self._marked_chosen.clear()
        self._render()
        self.refresh()
        self.changed()

    def get_value(self):
        return list(self._chosen)

    def set_value(self, value):
        keys = {k for k, _t in self.choices}
        self._chosen = [str(v) for v in (value or []) if str(v) in keys]
        self._render()


class TreeSelect(LabeledWidget):
    """
    Selección en un árbol. `nodes` es una lista de `{"id", "text", "children": [...]}`.

    Con `multiple=True` el valor es una lista de ids; si no, un id.
    """

    multiple = False

    def __init__(self, label=None, help_text=None, nodes=(), multiple: Optional[bool] = None, **kwargs):
        if multiple is not None:
            self.multiple = multiple
        self.tree = ft.Column(spacing=0)
        super().__init__(self.tree, label=label, help_text=help_text, **kwargs)
        self._selected: list[str] = []
        self._expanded: set[str] = set()
        self.set_nodes(nodes)

    def set_nodes(self, nodes):
        self.nodes = list(nodes() if callable(nodes) else nodes)
        self._render()

    def _render(self):
        self.tree.controls = []
        self._render_nodes(self.nodes, 0)

    def _render_nodes(self, nodes, depth):
        for node in nodes:
            key = str(node["id"])
            children = node.get("children") or []
            expanded = key in self._expanded
            toggle = ft.IconButton(
                icon=ft.Icons.EXPAND_MORE if expanded else ft.Icons.CHEVRON_RIGHT,
                icon_size=18,
                visible=bool(children),
                on_click=lambda e, k=key: self._toggle(k),
            )
            spacer = ft.Container(width=40, visible=not children)
            check = ft.Checkbox(
                label=str(node.get("text", key)),
                value=key in self._selected,
                data=key,
                disabled=bool(node.get("disabled")),
                on_change=lambda e, k=key: self._check(k, e.control.value),
            )
            self.tree.controls.append(
                ft.Row([ft.Container(width=depth * 20), toggle, spacer, check], spacing=0, tight=True)
            )
            if children and expanded:
                self._render_nodes(children, depth + 1)

    def _toggle(self, key):
        self._expanded.symmetric_difference_update({key})
        self._render()
        self.refresh()

    def _check(self, key, checked):
        if self.multiple:
            if checked and key not in self._selected:
                self._selected.append(key)
            elif not checked and key in self._selected:
                self._selected.remove(key)
        else:
            self._selected = [key] if checked else []
        self._render()
        self.refresh()
        self.changed()

    def expand_all(self):
        def walk(nodes):
            for n in nodes:
                if n.get("children"):
                    self._expanded.add(str(n["id"]))
                    walk(n["children"])

        walk(self.nodes)
        self._render()

    def get_value(self):
        if self.multiple:
            return list(self._selected)
        return self._selected[0] if self._selected else None

    def set_value(self, value):
        if self.multiple:
            self._selected = [str(v) for v in (value or [])]
        else:
            self._selected = [] if value in (None, "") else [str(value)]
        # Expande los ancestros de lo seleccionado para que se vea
        def walk(nodes, path):
            for n in nodes:
                key = str(n["id"])
                if key in self._selected:
                    self._expanded.update(path)
                walk(n.get("children") or [], path + [key])

        walk(self.nodes, [])
        self._render()


class TreeSelectMultiple(TreeSelect):
    multiple = True


class TaggingInput(LabeledWidget):
    """
    Etiquetas libres como chips. Se agregan con Enter (o coma).

    `suggestions` es una lista o un callable `fn(texto) -> list[str]` (p. ej. una
    consulta remota) que muestra sugerencias mientras se escribe.
    """

    def __init__(self, label=None, help_text=None, suggestions=None, max_tags: Optional[int] = None, **kwargs):
        self.suggestions = suggestions
        self.max_tags = max_tags
        self._tags: list[str] = []
        self.chips = ft.Row(wrap=True, spacing=5, run_spacing=5)
        self.input = ft.TextField(
            hint_text=_("Write and press Enter"),
            dense=True,
            on_submit=self._on_submit,
            on_change=self._on_input_change,
        )
        self.suggestion_box = ft.Column(spacing=0, visible=False)
        body = ft.Container(
            border=ft.Border.all(1, ft.Colors.OUTLINE),
            border_radius=6,
            padding=8,
            content=ft.Column([self.chips, self.input, self.suggestion_box], spacing=6, tight=True),
        )
        super().__init__(body, label=label, help_text=help_text, **kwargs)

    def validate_tag(self, tag: str) -> bool:
        return bool(tag)

    def _on_input_change(self, e):
        text = self.input.value or ""
        if "," in text:
            for part in text.split(","):
                self.add_tag(part)
            self.input.value = ""
            self.suggestion_box.visible = False
            self.refresh()
            return
        self._show_suggestions(text)

    def _show_suggestions(self, text):
        if not self.suggestions or not text.strip():
            self.suggestion_box.visible = False
            self.refresh()
            return
        source = self.suggestions(text) if callable(self.suggestions) else self.suggestions
        q = normalize_text(text)
        found = [s for s in source if q in normalize_text(s) and s not in self._tags][:8]
        self.suggestion_box.controls = [
            ft.TextButton(s, on_click=lambda e, s=s: self._pick(s)) for s in found
        ]
        self.suggestion_box.visible = bool(found)
        self.refresh()

    def _pick(self, text):
        self.add_tag(text)
        self.input.value = ""
        self.suggestion_box.visible = False
        self.refresh()

    def _on_submit(self, e):
        self.add_tag(self.input.value or "")
        self.input.value = ""
        self.suggestion_box.visible = False
        self.refresh()

    def add_tag(self, tag: str):
        tag = tag.strip()
        if not tag or tag in self._tags:
            return
        if self.max_tags and len(self._tags) >= self.max_tags:
            return
        if not self.validate_tag(tag):
            self.show_error(_("Enter a valid email address."))
            self.refresh()
            return
        self._tags.append(tag)
        self._render_chips()
        self.changed()

    def remove_tag(self, tag: str):
        if tag in self._tags:
            self._tags.remove(tag)
            self._render_chips()
            self.refresh()
            self.changed()

    def _render_chips(self):
        self.chips.controls = [
            ft.Chip(label=ft.Text(t), on_delete=lambda e, t=t: self.remove_tag(t)) for t in self._tags
        ]

    def get_value(self):
        return list(self._tags)

    def set_value(self, value):
        if isinstance(value, str):
            value = [v for v in value.split(",") if v.strip()]
        self._tags = [str(v).strip() for v in (value or [])]
        self._render_chips()


class EmailTaggingInput(TaggingInput):
    """Etiquetas que solo aceptan correos electrónicos válidos."""

    def validate_tag(self, tag: str) -> bool:
        return bool(EMAIL_RE.match(tag))
