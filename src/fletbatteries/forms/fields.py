"""
Campos de formulario: convierten y validan el valor de un widget.

Cada `Field` sabe qué widget crear (`widget`), cómo convertir el valor del widget
a Python (`to_python`), cómo validarlo (`validate`, `validators`) y cómo
mostrarlo en una tabla (`display`).
"""

import copy
import inspect
import re
from datetime import date, datetime, time
from decimal import Decimal, InvalidOperation
from typing import Any, Callable, Optional, Sequence

from fletbatteries.forms.validators import (
    EMPTY_VALUES,
    MaxLengthValidator,
    MaxValueValidator,
    MinLengthValidator,
    MinValueValidator,
    ValidationError,
    validate_email,
    validate_url,
)
from fletbatteries.i18n import _
from fletbatteries.widgets import choices as choice_widgets
from fletbatteries.widgets import dates as date_widgets
from fletbatteries.widgets import files as file_widgets
from fletbatteries.widgets import inputs, selects, sliders
from fletbatteries.widgets.base import Widget
from fletbatteries.widgets.color import HEX_PATTERN, ColorInput
from fletbatteries.widgets.markdown import MarkdownInput


def _widget_accepts(widget_cls, name: str) -> bool:
    """True si algún `__init__` de la jerarquía del widget declara el parámetro `name`."""
    if not inspect.isclass(widget_cls):
        return True
    for klass in widget_cls.__mro__:
        if klass is Widget or not issubclass(klass, Widget):
            break
        init = klass.__dict__.get("__init__")
        if init and name in inspect.signature(init).parameters:
            return True
    return False


class Field:
    widget: Any = inputs.TextInput
    empty_value: Any = None
    default_error_messages = {"required": "This field is required."}
    _creation_counter = 0

    def __init__(
        self,
        *,
        required: bool = True,
        label: Optional[str] = None,
        help_text: Optional[str] = None,
        initial: Any = None,
        validators: Sequence[Callable] = (),
        widget: Any = None,
        widget_kwargs: Optional[dict] = None,
        disabled: bool = False,
        error_messages: Optional[dict] = None,
        list_display: bool = True,
        filter: bool = False,
        depends_on: Optional[str] = None,
        related_choices: Optional[Callable[[Any], Any]] = None,
        related_filter: Optional[str] = None,
    ):
        self.required = required
        # Campos dependientes (como `data-related` de djgentelella): cuando cambia
        # `depends_on`, las opciones se recalculan con `related_choices(valor_padre)`
        # o, en selects con `source`, se filtran con `{related_filter: valor_padre}`.
        self.depends_on = depends_on
        self.related_choices = related_choices
        self.related_filter = related_filter
        self.label = label
        self.help_text = help_text
        self.initial = initial
        self.validators = list(validators)
        if widget is not None:
            self.widget = widget
        self.widget_kwargs = dict(widget_kwargs or {})
        self.disabled = disabled
        self.error_messages = {}
        for klass in reversed(type(self).__mro__):
            self.error_messages.update(getattr(klass, "default_error_messages", {}))
        self.error_messages.update(error_messages or {})
        self.list_display = list_display
        self.filter = filter
        self.name: Optional[str] = None
        self.creation_counter = Field._creation_counter
        Field._creation_counter += 1

    def __deepcopy__(self, memo):
        # Copia superficial: las fuentes de datos (managers, APIs) no se deben clonar
        result = copy.copy(self)
        result.validators = list(self.validators)
        result.widget_kwargs = dict(self.widget_kwargs)
        memo[id(self)] = result
        return result

    def set_name(self, name: str):
        self.name = name
        if self.label is None:
            self.label = name.replace("_", " ").capitalize()

    # ------------------------------------------------------------------
    # Widget
    # ------------------------------------------------------------------
    def widget_attrs(self) -> dict:
        """Parámetros extra que el campo pasa al widget si este los acepta."""
        return {}

    def build_widget(self) -> Widget:
        kwargs = {"label": self.label, "help_text": self.help_text}
        for key, value in self.widget_attrs().items():
            if _widget_accepts(self.widget, key):
                kwargs[key] = value
        kwargs.update(self.widget_kwargs)
        widget = self.widget(**kwargs)
        widget.disabled = self.disabled or widget.disabled
        return widget

    def prepare_value(self, value):
        """Valor Python -> valor para el widget."""
        return value

    # ------------------------------------------------------------------
    # Limpieza y validación
    # ------------------------------------------------------------------
    def error(self, code: str, **params) -> ValidationError:
        return ValidationError(_(self.error_messages[code], **params))

    def to_python(self, value):
        return self.empty_value if value in EMPTY_VALUES else value

    def validate(self, value):
        if value in EMPTY_VALUES and self.required:
            raise self.error("required")

    def run_validators(self, value):
        if value in EMPTY_VALUES:
            return
        errors = []
        for validator in self.validators:
            try:
                validator(value)
            except ValidationError as e:
                errors.extend(e.messages)
        if errors:
            raise ValidationError(errors)

    def clean(self, value):
        value = self.to_python(value)
        self.validate(value)
        self.run_validators(value)
        return value

    def display(self, value) -> str:
        """Texto para mostrar el valor en tablas y detalles."""
        if value in EMPTY_VALUES:
            return ""
        return str(value)


class CharField(Field):
    empty_value = ""

    def __init__(self, *, max_length: Optional[int] = None, min_length: Optional[int] = None, strip: bool = True,
                 **kwargs):
        super().__init__(**kwargs)
        self.max_length = max_length
        self.min_length = min_length
        self.strip = strip
        if max_length is not None:
            self.validators.append(MaxLengthValidator(max_length))
        if min_length is not None:
            self.validators.append(MinLengthValidator(min_length))

    def widget_attrs(self):
        return {"max_length": self.max_length} if self.max_length else {}

    def to_python(self, value):
        if value in EMPTY_VALUES:
            return self.empty_value
        value = str(value)
        return value.strip() if self.strip else value


class TextAreaField(CharField):
    widget = inputs.Textarea


class EmailField(CharField):
    widget = inputs.EmailInput

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.validators.append(validate_email)


class URLField(CharField):
    widget = inputs.URLInput

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.validators.append(validate_url)


class PasswordField(CharField):
    widget = inputs.PasswordInput

    def __init__(self, **kwargs):
        kwargs.setdefault("strip", False)
        kwargs.setdefault("list_display", False)
        super().__init__(**kwargs)


class MaskedField(CharField):
    """Texto con máscara (`9` dígito, `a` letra, `*` alfanumérico). Valida que esté completo."""

    widget = inputs.MaskedInput
    default_error_messages = {"incomplete": "The value does not match the expected format."}

    def __init__(self, *, mask: Optional[str] = None, **kwargs):
        super().__init__(**kwargs)
        self.mask = mask if mask is not None else getattr(self.widget, "mask", "")

    def widget_attrs(self):
        return {"mask": self.mask} if self.mask else {}

    def validate(self, value):
        super().validate(value)
        if value and self.mask and not re.fullmatch(inputs.mask_regex(self.mask), value):
            raise self.error("incomplete")


class HiddenField(Field):
    widget = inputs.HiddenInput

    def __init__(self, **kwargs):
        kwargs.setdefault("required", False)
        kwargs.setdefault("list_display", False)
        super().__init__(**kwargs)


class IntegerField(Field):
    widget = inputs.NumberInput
    default_error_messages = {"invalid": "Enter a whole number."}

    def __init__(self, *, min_value=None, max_value=None, **kwargs):
        super().__init__(**kwargs)
        self.min_value, self.max_value = min_value, max_value
        if max_value is not None:
            self.validators.append(MaxValueValidator(max_value))
        if min_value is not None:
            self.validators.append(MinValueValidator(min_value))

    def widget_attrs(self):
        attrs = {}
        if self.min_value is not None:
            attrs["min"] = self.min_value
        if self.max_value is not None:
            attrs["max"] = self.max_value
        return attrs

    def _convert(self, value):
        if isinstance(value, bool):
            raise ValueError
        if isinstance(value, float) and value.is_integer():
            return int(value)
        return int(str(value).strip())

    def to_python(self, value):
        if value in EMPTY_VALUES or (isinstance(value, str) and not value.strip()):
            return None
        try:
            return self._convert(value)
        except (ValueError, TypeError, InvalidOperation):
            raise self.error("invalid")


class FloatField(IntegerField):
    widget = inputs.FloatInput
    default_error_messages = {"invalid": "Enter a number."}

    def _convert(self, value):
        return float(str(value).strip().replace(",", "."))


class DecimalField(IntegerField):
    widget = inputs.FloatInput
    default_error_messages = {"invalid": "Enter a number."}

    def __init__(self, *, decimal_places: Optional[int] = None, **kwargs):
        super().__init__(**kwargs)
        self.decimal_places = decimal_places

    def _convert(self, value):
        result = Decimal(str(value).strip().replace(",", "."))
        if not result.is_finite():
            raise ValueError
        if self.decimal_places is not None:
            result = result.quantize(Decimal(1).scaleb(-self.decimal_places))
        return result


class BooleanField(Field):
    """Si `required=True` el valor debe ser verdadero (casilla de "acepto")."""

    widget = inputs.CheckboxInput

    def __init__(self, **kwargs):
        kwargs.setdefault("required", False)
        super().__init__(**kwargs)

    def to_python(self, value):
        if isinstance(value, str):
            return value.lower() in ("1", "true", "yes", "on", "si", "sí")
        return bool(value)

    def validate(self, value):
        if not value and self.required:
            raise self.error("required")

    def display(self, value):
        return _("Yes") if value else _("No")


class NullBooleanField(BooleanField):
    widget = inputs.NullBooleanSelect

    def to_python(self, value):
        if value in (None, ""):
            return None
        return super().to_python(value)

    def validate(self, value):
        if value is None and self.required:
            raise self.error("required")

    def display(self, value):
        return "" if value is None else super().display(value)


class _BaseDateField(Field):
    widget = date_widgets.DateInput
    kind: type = date
    fmt = date_widgets.DATE_FORMAT
    default_error_messages = {"invalid": "Enter a valid date."}

    def to_python(self, value):
        if value in EMPTY_VALUES:
            return None
        parsed = date_widgets.parse_value(value, self.fmt, self.kind)
        if not isinstance(parsed, self.kind):
            raise self.error("invalid")
        return parsed

    def display(self, value):
        return date_widgets.format_value(value, self.fmt)


class DateField(_BaseDateField):
    default_error_messages = {
        "min_date": "The date must be on or after {min_date}.",
        "max_date": "The date must be on or before {max_date}.",
    }

    def __init__(self, *, min_date=None, max_date=None, **kwargs):
        super().__init__(**kwargs)
        self.min_date, self.max_date = min_date, max_date

    def widget_attrs(self):
        return {"min_date": self.min_date, "max_date": self.max_date}

    def validate(self, value):
        super().validate(value)
        if value is None:
            return
        day = value.date() if isinstance(value, datetime) else value
        lo = date_widgets.resolve_date(self.min_date, is_min=True)
        hi = date_widgets.resolve_date(self.max_date, is_min=False)
        if lo and day < lo:
            raise self.error("min_date", min_date=lo.strftime(date_widgets.DATE_FORMAT))
        if hi and day > hi:
            raise self.error("max_date", max_date=hi.strftime(date_widgets.DATE_FORMAT))


class DateTimeField(DateField):
    widget = date_widgets.DateTimeInput
    kind = datetime
    fmt = date_widgets.DATETIME_FORMAT
    default_error_messages = {"invalid": "Enter a valid date/time."}


class TimeField(_BaseDateField):
    widget = date_widgets.TimeInput
    kind = time
    fmt = date_widgets.TIME_FORMAT
    default_error_messages = {"invalid": "Enter a valid time."}


class DateRangeField(Field):
    """El valor es una tupla `(inicio, fin)`."""

    widget = date_widgets.DateRangeInput
    kind: type = date
    fmt = date_widgets.DATE_FORMAT
    default_error_messages = {
        "invalid": "Enter a valid date range.",
        "order": "The start date must be before the end date.",
    }

    def to_python(self, value):
        if value in EMPTY_VALUES:
            return None
        if not isinstance(value, (tuple, list)) or len(value) != 2:
            raise self.error("invalid")
        start, end = (date_widgets.parse_value(v, self.fmt, self.kind) for v in value)
        if not isinstance(start, self.kind) or not isinstance(end, self.kind):
            raise self.error("invalid")
        return start, end

    def validate(self, value):
        super().validate(value)
        if value and value[0] > value[1]:
            raise self.error("order")

    def display(self, value):
        if not value:
            return ""
        return f"{date_widgets.format_value(value[0], self.fmt)} - {date_widgets.format_value(value[1], self.fmt)}"


class DateTimeRangeField(DateRangeField):
    widget = date_widgets.DateTimeRangeInput
    kind = datetime
    fmt = date_widgets.DATETIME_FORMAT


class ChoiceField(Field):
    """
    Una opción de `choices`: lista `[(llave, texto)]`, dict o callable que los
    devuelva. `coerce` convierte la llave (texto) al tipo deseado.
    """

    widget = inputs.Select
    default_error_messages = {"invalid_choice": "Select a valid choice."}

    def __init__(self, *, choices=(), coerce: Callable = str, **kwargs):
        super().__init__(**kwargs)
        self._choices = choices
        self.coerce = coerce

    @property
    def choices(self) -> list[tuple[str, str]]:
        return inputs._normalize_choices(self._choices)

    @choices.setter
    def choices(self, value):
        self._choices = value

    def widget_attrs(self):
        return {"choices": self.choices}

    def prepare_value(self, value):
        return None if value is None else str(value)

    def to_python(self, value):
        if value in EMPTY_VALUES:
            return None
        return str(value)

    def validate(self, value):
        super().validate(value)
        if value is not None and value not in dict(self.choices):
            raise self.error("invalid_choice")

    def clean(self, value):
        value = super().clean(value)
        return None if value is None else self.coerce(value)

    def display(self, value):
        if value in EMPTY_VALUES:
            return ""
        return dict(self.choices).get(str(value), str(value))


class MultipleChoiceField(ChoiceField):
    widget = selects.AutocompleteSelectMultiple

    def prepare_value(self, value):
        return [str(v) for v in (value or [])]

    def to_python(self, value):
        if value in EMPTY_VALUES:
            return []
        return [str(v) for v in value]

    def validate(self, value):
        if not value and self.required:
            raise self.error("required")
        keys = dict(self.choices)
        if any(v not in keys for v in value):
            raise self.error("invalid_choice")

    def clean(self, value):
        value = Field.clean(self, value)
        return [self.coerce(v) for v in value]

    def display(self, value):
        texts = dict(self.choices)
        return ", ".join(texts.get(str(v), str(v)) for v in (value or []))


class TreeChoiceField(Field):
    """Selección en un árbol de `nodes` (`{"id", "text", "children"}`)."""

    widget = choice_widgets.TreeSelect
    default_error_messages = {"invalid_choice": "Select a valid choice."}

    def __init__(self, *, nodes=(), multiple: bool = False, coerce: Callable = str, **kwargs):
        super().__init__(**kwargs)
        self._nodes = nodes
        self.multiple = multiple
        self.coerce = coerce

    @property
    def nodes(self):
        return list(self._nodes() if callable(self._nodes) else self._nodes)

    def widget_attrs(self):
        return {"nodes": self.nodes, "multiple": self.multiple}

    def _texts(self) -> dict:
        found = {}

        def walk(nodes):
            for n in nodes:
                found[str(n["id"])] = str(n.get("text", n["id"]))
                walk(n.get("children") or [])

        walk(self.nodes)
        return found

    def to_python(self, value):
        if self.multiple:
            return [str(v) for v in (value or [])]
        return None if value in EMPTY_VALUES else str(value)

    def validate(self, value):
        super().validate(value)
        texts = self._texts()
        values = value if self.multiple else ([value] if value is not None else [])
        if any(v not in texts for v in values):
            raise self.error("invalid_choice")

    def clean(self, value):
        value = super().clean(value)
        if self.multiple:
            return [self.coerce(v) for v in value]
        return None if value is None else self.coerce(value)

    def display(self, value):
        texts = self._texts()
        values = value if self.multiple else ([value] if value not in EMPTY_VALUES else [])
        return ", ".join(texts.get(str(v), str(v)) for v in values or [])


def _default_coerce_key(value):
    text = str(value)
    return int(text) if text.lstrip("-").isdigit() else value


class ModelChoiceField(Field):
    """
    Un registro de una fuente de datos con búsqueda remota.

    `source` debe tener `lookup(skip, limit, q) -> dict` (formato select2) y
    `label_for(key) -> str | None` (por ejemplo un `DataSource`).
    """

    widget = selects.AutocompleteSelect
    default_error_messages = {"invalid_choice": "Select a valid choice."}

    def __init__(self, source=None, *, coerce: Callable = _default_coerce_key, **kwargs):
        super().__init__(**kwargs)
        self.source = source
        self.coerce = coerce

    def widget_attrs(self):
        return {"source": self.source}

    def prepare_value(self, value):
        return None if value is None else str(getattr(value, "id", value))

    def to_python(self, value):
        if value in EMPTY_VALUES:
            return None
        return self.coerce(value)

    def validate(self, value):
        super().validate(value)
        if value is not None and self.source is not None and self.source.label_for(value) is None:
            raise self.error("invalid_choice")

    def display(self, value):
        if value in EMPTY_VALUES:
            return ""
        key = getattr(value, "id", value)
        label = self.source.label_for(key) if self.source is not None else None
        return label if label is not None else str(value)


class ModelMultipleChoiceField(ModelChoiceField):
    widget = selects.AutocompleteSelectMultiple

    def prepare_value(self, value):
        return [str(getattr(v, "id", v)) for v in (value or [])]

    def to_python(self, value):
        return [self.coerce(v) for v in (value or [])]

    def validate(self, value):
        if not value and self.required:
            raise self.error("required")
        if self.source is not None and any(self.source.label_for(v) is None for v in value):
            raise self.error("invalid_choice")

    def display(self, value):
        return ", ".join(ModelChoiceField.display(self, v) for v in (value or []))


class FileField(Field):
    """
    El valor es un `UploadedFile`.

    - `upload_to`: carpeta donde `save_file` copia los archivos nuevos.
    - `media_url`: prefijo para mostrar los archivos guardados (p. ej. "image/"
      si `upload_to` es `assets/image`).

    Al editar, el valor inicial (el nombre guardado) se convierte en un
    `UploadedFile(stored=True)`: si el usuario no lo cambia, se conserva sin copiarlo.
    """

    widget = file_widgets.ClearableFileInput
    default_error_messages = {"extension": "Invalid file type."}

    def __init__(self, *, allowed_extensions: Optional[Sequence[str]] = None, upload_to=None,
                 media_url: Optional[str] = None, **kwargs):
        super().__init__(**kwargs)
        self.allowed_extensions = [e.lower().lstrip(".") for e in allowed_extensions] if allowed_extensions else None
        self.upload_to = upload_to
        self.media_url = media_url

    def widget_attrs(self):
        attrs = {"media_url": self.media_url}
        if self.allowed_extensions:
            attrs["allowed_extensions"] = self.allowed_extensions
        return attrs

    def prepare_value(self, value):
        if isinstance(value, str) and value:
            return file_widgets.UploadedFile.existing(value, self.upload_to, self.media_url)
        return value

    def to_python(self, value):
        if value in EMPTY_VALUES:
            return None
        if isinstance(value, str):
            return file_widgets.UploadedFile.existing(value, self.upload_to, self.media_url)
        return value

    def validate(self, value):
        super().validate(value)
        if value is not None and self.allowed_extensions and value.extension not in self.allowed_extensions:
            raise self.error("extension")

    def save_file(self, value) -> Optional[str]:
        """Copia el archivo a `upload_to` (solo si es nuevo) y devuelve el nombre guardado."""
        if value is None:
            return None
        if value.is_new and self.upload_to and (value.content is not None or value.path):
            value.save_to(self.upload_to)
        return value.name

    def display(self, value):
        return "" if value in EMPTY_VALUES else str(getattr(value, "name", value))


class ImageField(FileField):
    widget = file_widgets.ImageInput

    def __init__(self, **kwargs):
        kwargs.setdefault("allowed_extensions", ("jpg", "jpeg", "png", "gif", "webp"))
        super().__init__(**kwargs)


class ColorField(CharField):
    widget = ColorInput
    default_error_messages = {"invalid": "Enter a valid color (#RRGGBB)."}

    def to_python(self, value):
        value = super().to_python(value)
        return value.upper() if value else value

    def validate(self, value):
        super().validate(value)
        if value and not HEX_PATTERN.match(value):
            raise self.error("invalid")


class TagsField(Field):
    """Lista de etiquetas. Con `emails=True` solo acepta correos."""

    widget = choice_widgets.TaggingInput
    default_error_messages = {"invalid_email": "Enter a valid email address."}

    def __init__(self, *, emails: bool = False, suggestions=None, **kwargs):
        if emails and "widget" not in kwargs:
            kwargs["widget"] = choice_widgets.EmailTaggingInput
        super().__init__(**kwargs)
        self.emails = emails
        self.suggestions = suggestions

    def widget_attrs(self):
        return {"suggestions": self.suggestions} if self.suggestions else {}

    def to_python(self, value):
        if value in EMPTY_VALUES:
            return []
        if isinstance(value, str):
            value = value.split(",")
        return [str(v).strip() for v in value if str(v).strip()]

    def validate(self, value):
        if not value and self.required:
            raise self.error("required")
        if self.emails:
            for v in value:
                try:
                    validate_email(v)
                except ValidationError:
                    raise self.error("invalid_email")

    def display(self, value):
        return ", ".join(value or [])


class RangeField(Field):
    """Rango numérico `(inicio, fin)` con un slider doble."""

    widget = sliders.GridSlider

    def __init__(self, *, min_value: float = 0, max_value: float = 100, **kwargs):
        super().__init__(**kwargs)
        self.min_value, self.max_value = min_value, max_value

    def widget_attrs(self):
        return {"min": self.min_value, "max": self.max_value}

    def to_python(self, value):
        if value in EMPTY_VALUES:
            return None
        return tuple(value)

    def display(self, value):
        return "" if not value else f"{value[0]} – {value[1]}"


class MarkdownField(CharField):
    """Texto Markdown con editor y vista previa."""

    widget = MarkdownInput


class MapPointField(Field):
    """Punto en un mapa. El valor es el texto "lat,lng" (como `GTPointField`)."""

    default_error_messages = {"invalid": "Enter a valid point (latitude, longitude)."}

    @property
    def widget(self):  # se importa al usarlo: flet-map es opcional
        from fletbatteries.widgets.maps import MapPointInput

        return self.__dict__.get("_widget", MapPointInput)

    @widget.setter
    def widget(self, value):
        self.__dict__["_widget"] = value

    def to_python(self, value):
        from fletbatteries.widgets.maps import format_point, parse_point

        if value in EMPTY_VALUES:
            return None
        point = parse_point(value)
        if point is None:
            raise self.error("invalid")
        return format_point(point)
