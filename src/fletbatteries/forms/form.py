"""
Formularios declarativos (equivalente a `GTForm` de djgentelella).

    class ContactForm(Form):
        title = "Contacto"
        render_type = "grid"
        grid_representation = [
            [["name"], ["email"]],
            [["message"]],
        ]

        name = CharField(max_length=50)
        email = EmailField()
        message = TextAreaField(required=False)

        def clean_name(self, value):
            return value.title()

    form = ContactForm(initial={"name": "ana"})
    page.add(form.control)
    if form.is_valid():
        save(form.cleaned_data)

Modos de render (`render_type`): `plain` (columna), `horizontal` (etiqueta a la
izquierda), `inline` (fila que se ajusta) y `grid` (filas y columnas según
`grid_representation`; un nombre puede ser un campo o un método del formulario
que devuelve un control).
"""

import copy
from typing import Any, Callable, Optional

import flet as ft

from fletbatteries.forms.fields import Field
from fletbatteries.forms.validators import ValidationError
from fletbatteries.utils import safe_update
from fletbatteries.widgets.base import Widget

RENDER_TYPES = ("plain", "horizontal", "inline", "grid")
NON_FIELD_ERRORS = "__all__"


class DeclarativeFieldsMetaclass(type):
    """Reúne los `Field` declarados en la clase y en sus bases, en orden de declaración."""

    def __new__(mcs, name, bases, attrs):
        current = [(key, value) for key, value in attrs.items() if isinstance(value, Field)]
        current.sort(key=lambda item: item[1].creation_counter)
        for key, _value in current:
            attrs.pop(key)
        new_class = super().__new__(mcs, name, bases, attrs)

        declared = {}
        for base in reversed(new_class.__mro__[1:]):
            if hasattr(base, "declared_fields"):
                declared.update(base.declared_fields)
            for attr, value in base.__dict__.items():
                if value is None and attr in declared:
                    declared.pop(attr)
        for key, field in current:
            field.set_name(key)
            declared[key] = field
        for attr, value in attrs.items():
            if value is None and attr in declared:
                declared.pop(attr)

        new_class.declared_fields = declared
        new_class.base_fields = declared
        return new_class


class BaseForm:
    title: Optional[str] = None
    render_type: str = "plain"
    grid_representation: Optional[list] = None
    label_width: int = 160
    inline_width: int = 240
    spacing: int = 12
    base_fields: dict[str, Field] = {}

    def __init__(
        self,
        initial: Optional[dict] = None,
        instance: Any = None,
        prefix: Optional[str] = None,
        render_type: Optional[str] = None,
        title: Optional[str] = None,
        on_change: Optional[Callable[["BaseForm", str], Any]] = None,
    ):
        self.fields: dict[str, Field] = copy.deepcopy(self.base_fields)
        self.instance = instance
        self.prefix = prefix
        if render_type:
            self.render_type = render_type
        if title:
            self.title = title
        if self.render_type not in RENDER_TYPES:
            raise ValueError(f"render_type debe ser uno de {RENDER_TYPES}")
        self.initial = {}
        if instance is not None:
            self.initial.update(self.initial_from_instance(instance))
        self.initial.update(initial or {})
        self.on_change = on_change
        self.errors: dict[str, list[str]] = {}
        self.cleaned_data: dict[str, Any] = {}
        self._widgets: Optional[dict[str, Widget]] = None
        self._control: Optional[ft.Control] = None
        self._non_field_errors = ft.Text("", color=ft.Colors.ERROR, visible=False)

    # ------------------------------------------------------------------
    # Widgets y valores
    # ------------------------------------------------------------------
    def initial_from_instance(self, instance) -> dict:
        if isinstance(instance, dict):
            return {name: instance.get(name) for name in self.base_fields if name in instance}
        return {name: getattr(instance, name) for name in self.base_fields if hasattr(instance, name)}

    def get_initial_for_field(self, name: str, field: Field):
        value = self.initial.get(name, field.initial)
        return value() if callable(value) else value

    @property
    def widgets(self) -> dict[str, Widget]:
        if self._widgets is None:
            self._widgets = {}
            for name, field in self.fields.items():
                widget = field.build_widget()
                widget.key = f"{self.prefix}-{name}" if self.prefix else name
                value = self.get_initial_for_field(name, field)
                if value is not None:
                    widget.set_value(field.prepare_value(value))
                widget.add_change_listener(lambda w, n=name: self._widget_changed(n))
                self._widgets[name] = widget
            for widget in self._widgets.values():
                if hasattr(widget, "bind_form"):
                    widget.bind_form(self)
            for name, field in self.fields.items():
                if field.depends_on:
                    self._widgets[field.depends_on].add_change_listener(
                        lambda w, child=name: self._update_dependent(child)
                    )
                    self._update_dependent(name, initial=True)
        return self._widgets

    def _update_dependent(self, name: str, initial: bool = False):
        """Recalcula las opciones del campo `name` según el valor de su campo padre."""
        field = self.fields[name]
        widget = self._widgets[name]
        parent_value = self._widgets[field.depends_on].value
        has_parent = parent_value not in (None, "", [])
        current = widget.value
        if field.related_choices is not None:
            field.choices = list(field.related_choices(parent_value)) if has_parent else []
            widget.set_choices(field.choices)
        elif field.related_filter and hasattr(widget, "set_lookup_filters"):
            widget.set_lookup_filters({field.related_filter: parent_value} if has_parent else {})
        # Sin valor en el padre el campo queda deshabilitado
        widget.disabled = field.disabled or not has_parent
        if initial and current not in (None, "", []):
            widget.set_value(current)
        elif not initial:
            widget.set_value(None)
            widget.refresh()
            widget.changed()

    def __getitem__(self, name: str) -> Widget:
        return self.widgets[name]

    def __iter__(self):
        return iter(self.widgets.items())

    def _widget_changed(self, name):
        if self.on_change:
            self.on_change(self, name)

    @property
    def data(self) -> dict:
        """Valores actuales de los widgets (sin limpiar)."""
        return {name: widget.value for name, widget in self.widgets.items()}

    def set_initial(self, initial: dict):
        """Carga valores en los widgets (p. ej. al editar un registro)."""
        for name, value in (initial or {}).items():
            if name in self.fields:
                self.widgets[name].set_value(self.fields[name].prepare_value(value))
        self.refresh()

    def load_instance(self, instance):
        self.instance = instance
        self.set_initial(self.initial_from_instance(instance))

    def reset(self):
        """Vuelve a los valores iniciales (incluidos los de `instance`) y limpia los errores."""
        for name, field in self.fields.items():
            value = self.get_initial_for_field(name, field)
            self.widgets[name].set_value(field.prepare_value(value) if value is not None else None)
        self.clear_errors()

    def clear(self):
        """Deja el formulario como nuevo: sin instancia ni valores iniciales propios (para crear)."""
        self.instance = None
        self.initial = {}
        self.reset()

    # ------------------------------------------------------------------
    # Validación
    # ------------------------------------------------------------------
    def is_valid(self) -> bool:
        self.full_clean()
        self.show_errors()
        return not self.errors

    def full_clean(self):
        self.errors = {}
        self.cleaned_data = {}
        for name, field in self.fields.items():
            if field.disabled:
                self.cleaned_data[name] = self.get_initial_for_field(name, field)
                continue
            try:
                value = field.clean(self.widgets[name].value)
                hook = getattr(self, f"clean_{name}", None)
                if hook:
                    value = hook(value)
                self.cleaned_data[name] = value
            except ValidationError as e:
                self.errors.setdefault(name, []).extend(e.messages)
        try:
            result = self.clean()
            if result is not None:
                self.cleaned_data = result
        except ValidationError as e:
            if e.error_dict:
                for name, messages in e.error_dict.items():
                    self.add_error(name, messages)
            else:
                self.add_error(None, e.messages)

    def save_data(self) -> dict:
        """`cleaned_data` lista para guardar: los archivos se copian a `upload_to` y se reemplazan por su nombre."""
        from fletbatteries.forms.fields import FileField

        data = {}
        for name, value in self.cleaned_data.items():
            field = self.fields.get(name)
            if isinstance(field, FileField):
                value = field.save_file(value)
            data[name] = value
        return data

    def clean(self) -> Optional[dict]:
        """Validación entre campos. Puede lanzar `ValidationError` o usar `add_error`."""
        return self.cleaned_data

    def add_error(self, field: Optional[str], error):
        messages = error.messages if isinstance(error, ValidationError) else (
            [error] if isinstance(error, str) else list(error)
        )
        key = field or NON_FIELD_ERRORS
        self.errors.setdefault(key, []).extend(messages)
        if field in self.cleaned_data:
            del self.cleaned_data[field]

    def non_field_errors(self) -> list[str]:
        return self.errors.get(NON_FIELD_ERRORS, [])

    def show_errors(self):
        for name, widget in self.widgets.items():
            messages = self.errors.get(name)
            widget.error = " ".join(messages) if messages else None
        nfe = self.non_field_errors()
        self._non_field_errors.value = " ".join(nfe)
        self._non_field_errors.visible = bool(nfe)
        self.refresh()

    def clear_errors(self):
        self.errors = {}
        self.show_errors()

    # ------------------------------------------------------------------
    # Render
    # ------------------------------------------------------------------
    @property
    def control(self) -> ft.Control:
        if self._control is None:
            self._control = self.render()
        return self._control

    def refresh(self):
        if self._control is not None:
            safe_update(self._control)

    def render(self, render_type: Optional[str] = None) -> ft.Control:
        render_type = render_type or self.render_type
        body = getattr(self, f"as_{render_type}")()
        return ft.Column([self._non_field_errors, body], spacing=self.spacing, tight=True)

    def _resolve(self, name: str) -> ft.Control:
        if name in self.fields:
            return self.widgets[name]
        method = getattr(self, name, None)
        if callable(method):
            return method()
        raise KeyError(f"'{name}' no es un campo ni un método de {type(self).__name__}")

    def as_plain(self) -> ft.Control:
        return ft.Column(list(self.widgets.values()), spacing=self.spacing, tight=True)

    def as_horizontal(self) -> ft.Control:
        rows = []
        for name, widget in self.widgets.items():
            label = widget.label
            widget.hide_label()
            widget.expand = True
            rows.append(
                ft.Row(
                    [
                        ft.Container(
                            ft.Text(label or "", weight=ft.FontWeight.W_500, text_align=ft.TextAlign.RIGHT),
                            width=self.label_width,
                            padding=ft.Padding.only(top=14),
                        ),
                        widget,
                    ],
                    vertical_alignment=ft.CrossAxisAlignment.START,
                    visible=widget.visible,
                )
            )
        return ft.Column(rows, spacing=self.spacing, tight=True)

    def as_inline(self) -> ft.Control:
        for widget in self.widgets.values():
            if widget.width is None:
                widget.width = self.inline_width
        return ft.Row(list(self.widgets.values()), wrap=True, spacing=self.spacing, run_spacing=self.spacing,
                      vertical_alignment=ft.CrossAxisAlignment.START)

    def as_grid(self) -> ft.Control:
        if not self.grid_representation:
            return self.as_plain()
        used = set()
        rows = []
        for row in self.grid_representation:
            columns = []
            for column in row:
                names = [column] if isinstance(column, str) else list(column)
                used.update(names)
                columns.append(
                    ft.Column(
                        [self._resolve(n) for n in names],
                        col={"xs": 12, "md": max(1, 12 // len(row))},
                        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                        spacing=self.spacing,
                    )
                )
            rows.append(ft.ResponsiveRow(columns, spacing=self.spacing))
        leftovers = [w for n, w in self.widgets.items() if n not in used]
        if leftovers:
            rows.append(ft.Column(leftovers, spacing=self.spacing))
        return ft.Column(rows, spacing=self.spacing, tight=True)

    # ------------------------------------------------------------------
    # Compatibilidad con los formularios JSON
    # ------------------------------------------------------------------
    @classmethod
    def from_json(cls, spec: dict) -> type:
        """Crea una clase de formulario a partir del formato de `form_example.json`."""
        from fletbatteries.forms import fields as f

        types = {
            "CharField": lambda i: f.CharField(max_length=i.get("max_length")),
            "IntegerField": lambda i: f.IntegerField(),
            "IntergerField": lambda i: f.IntegerField(),
            "ImageField": lambda i: f.ImageField(),
            "EmailField": lambda i: f.EmailField(max_length=i.get("max_length")),
            "PasswordField": lambda i: f.PasswordField(max_length=i.get("max_length")),
            "DateField": lambda i: f.DateField(min_date=i.get("min_date") or None, max_date=i.get("max_date") or None),
            "DateTimeField": lambda i: f.DateTimeField(min_date=i.get("min_date") or None,
                                                       max_date=i.get("max_date") or None),
            "SelectField": lambda i: f.ChoiceField(choices=i.get("choices", [])),
            "SelectMultipleField": lambda i: f.MultipleChoiceField(choices=i.get("choices", [])),
        }
        attrs = {"title": spec.get("title")}
        for item in spec["inputs"]:
            if item["type"] not in types:
                raise ValueError(f"Tipo de campo no soportado: {item['type']}")
            field = types[item["type"]](item)
            field.required = item.get("required", True)
            field.label = item.get("label")
            field.help_text = item.get("tooltip") or None
            field.list_display = item.get("visible_table", True)
            field.filter = item.get("filter", False)
            if not item.get("visible_form", True):
                field.widget_kwargs["visible"] = False
            attrs[item["name"]] = field
        return DeclarativeFieldsMetaclass(spec.get("name", "JsonForm"), (Form,), attrs)


class Form(BaseForm, metaclass=DeclarativeFieldsMetaclass):
    """Clase base para declarar formularios."""


__all__ = ["Form", "BaseForm", "DeclarativeFieldsMetaclass", "NON_FIELD_ERRORS", "ValidationError"]
