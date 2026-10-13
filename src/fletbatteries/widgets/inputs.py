"""Widgets básicos: texto, números, correo, URL, contraseña, máscaras, checkbox, yes/no y radios."""

import re
from typing import Iterable, Optional, Sequence

import flet as ft

from fletbatteries.i18n import _
from fletbatteries.widgets.base import LabeledWidget, Widget


class TextInput(Widget):
    """Campo de texto de una línea (base de los demás campos de texto)."""

    keyboard_type: Optional[ft.KeyboardType] = None
    password = False
    prefix_icon = None
    input_filter = None

    def __init__(
        self,
        label: Optional[str] = None,
        help_text: Optional[str] = None,
        hint_text: Optional[str] = None,
        max_length: Optional[int] = None,
        multiline: bool = False,
        min_lines: Optional[int] = None,
        max_lines: Optional[int] = None,
        prefix_icon=None,
        read_only: bool = False,
        width: Optional[float] = None,
        expand=None,
        **kwargs,
    ):
        super().__init__(label=label, help_text=help_text, width=width, expand=expand, **kwargs)
        self.field = ft.TextField(
            label=label,
            hint_text=hint_text,
            helper=help_text,
            max_length=max_length,
            multiline=multiline,
            min_lines=min_lines,
            max_lines=max_lines,
            keyboard_type=self.keyboard_type,
            password=self.password,
            can_reveal_password=self.password,
            prefix_icon=prefix_icon or self.prefix_icon,
            input_filter=self.input_filter,
            read_only=read_only,
            disabled=self.disabled,
            on_change=self._on_field_change,
        )
        self.content = self.field

    def _on_field_change(self, e):
        self.changed(e)

    def get_value(self):
        return self.field.value or ""

    def set_value(self, value):
        self.field.value = "" if value is None else str(value)

    def show_error(self, message):
        self.field.error = message

    def apply_label(self, label):
        self.field.label = label


class Textarea(TextInput):
    """Texto multilínea que crece con el contenido (autosize)."""

    def __init__(self, label=None, min_lines: int = 3, max_lines: int = 10, **kwargs):
        super().__init__(label=label, multiline=True, min_lines=min_lines, max_lines=max_lines, **kwargs)


class NumberInput(TextInput):
    """Número entero. El valor es el texto; el campo del formulario lo convierte."""

    keyboard_type = ft.KeyboardType.NUMBER
    input_filter = ft.InputFilter(regex_string=r"^-?\d*$", allow=True, replacement_string="")


class FloatInput(NumberInput):
    """Número decimal."""

    input_filter = ft.InputFilter(regex_string=r"^-?\d*[.,]?\d*$", allow=True, replacement_string="")


class EmailInput(TextInput):
    keyboard_type = ft.KeyboardType.EMAIL
    prefix_icon = ft.Icons.EMAIL_OUTLINED


class URLInput(TextInput):
    keyboard_type = ft.KeyboardType.URL
    prefix_icon = ft.Icons.LINK


class PasswordInput(TextInput):
    password = True
    prefix_icon = ft.Icons.LOCK_OUTLINE


class HiddenInput(Widget):
    """Guarda un valor sin mostrar nada (p. ej. el id del registro)."""

    def __init__(self, label=None, **kwargs):
        super().__init__(label=label, visible=False, **kwargs)
        self._value = None

    def get_value(self):
        return self._value

    def set_value(self, value):
        self._value = value


# ----------------------------------------------------------------------
# Máscaras (equivalente a Inputmask)
# ----------------------------------------------------------------------
MASK_TOKENS = {"9": r"\d", "a": r"[A-Za-z]", "*": r"[A-Za-z0-9]"}


def apply_mask(mask: str, raw: str) -> str:
    """
    Formatea `raw` con `mask`: `9` = dígito, `a` = letra, `*` = alfanumérico;
    cualquier otro carácter de la máscara es un literal que se inserta solo.
    """
    chars = [c for c in raw if c.isalnum()]
    out = []
    i = 0
    for token in mask:
        if i >= len(chars):
            break
        pattern = MASK_TOKENS.get(token)
        if pattern is None:
            out.append(token)
            continue
        # Salta caracteres que no calzan con el token
        while i < len(chars) and not re.fullmatch(pattern, chars[i]):
            i += 1
        if i >= len(chars):
            break
        out.append(chars[i])
        i += 1
    return "".join(out)


def mask_regex(mask: str) -> str:
    return "^" + "".join(MASK_TOKENS.get(c, re.escape(c)) for c in mask) + "$"


class MaskedInput(TextInput):
    """Texto con máscara de entrada. El valor es el texto formateado."""

    mask = ""

    def __init__(self, label=None, mask: Optional[str] = None, **kwargs):
        if mask is not None:
            self.mask = mask
        kwargs.setdefault("hint_text", self.mask.replace("9", "_").replace("a", "_").replace("*", "_"))
        super().__init__(label=label, max_length=None, **kwargs)

    def _on_field_change(self, e):
        formatted = apply_mask(self.mask, self.field.value or "")
        if formatted != self.field.value:
            self.field.value = formatted
            self.refresh()
        self.changed(e)

    def set_value(self, value):
        self.field.value = apply_mask(self.mask, "" if value is None else str(value))

    @property
    def is_complete(self) -> bool:
        return bool(re.fullmatch(mask_regex(self.mask), self.get_value()))


class DateMaskInput(MaskedInput):
    mask = "99/99/9999"


class DateTimeMaskInput(MaskedInput):
    mask = "99/99/9999 99:99"


class PhoneNumberMaskInput(MaskedInput):
    mask = "9999-9999"


class PhoneNumberTwoDigitMaskInput(MaskedInput):
    mask = "(99) 9999-9999"


class PhoneNumberFourDigitMaskInput(MaskedInput):
    mask = "(9999) 9999-9999"


class CreditCardMaskInput(MaskedInput):
    mask = "9999 9999 9999 9999"


class TaxIDMaskInput(MaskedInput):
    """Cédula física de Costa Rica (9-9999-9999)."""

    mask = "9-9999-9999"


class SerialNumberMaskInput(MaskedInput):
    mask = "****-****-****-****"


class EmailMaskInput(EmailInput):
    """Alias de EmailInput (en djgentelella es un Inputmask de correo)."""


# ----------------------------------------------------------------------
# Booleanos y opciones
# ----------------------------------------------------------------------
class CheckboxInput(Widget):
    def __init__(self, label=None, help_text=None, **kwargs):
        super().__init__(label=label, help_text=help_text, **kwargs)
        self.checkbox = ft.Checkbox(label=label, value=False, on_change=self.changed)
        self._error_text = ft.Text("", size=11, color=ft.Colors.ERROR, visible=False)
        self.content = ft.Column([self.checkbox, self._error_text], spacing=0, tight=True)

    def get_value(self):
        return bool(self.checkbox.value)

    def set_value(self, value):
        self.checkbox.value = bool(value)

    def show_error(self, message):
        self.checkbox.error = bool(message)
        self._error_text.value = message or ""
        self._error_text.visible = bool(message)

    def apply_label(self, label):
        self.checkbox.label = label


class YesNoInput(Widget):
    """
    Interruptor Sí/No que puede mostrar u ocultar otros controles.

    `show_on_yes` / `show_on_no` son nombres de campos (si el widget está en un
    `Form`) o controles. El formulario los resuelve con `bind_form`.
    """

    def __init__(
        self,
        label=None,
        help_text=None,
        show_on_yes: Sequence = (),
        show_on_no: Sequence = (),
        yes_text: Optional[str] = None,
        no_text: Optional[str] = None,
        **kwargs,
    ):
        super().__init__(label=label, help_text=help_text, **kwargs)
        self.show_on_yes = list(show_on_yes)
        self.show_on_no = list(show_on_no)
        self.yes_text = yes_text or _("Yes")
        self.no_text = no_text or _("No")
        self.switch = ft.Switch(value=False, on_change=self._on_switch)
        self.state_text = ft.Text(self.no_text)
        self._label = ft.Text(label or "", expand=True, visible=bool(label))
        self.content = ft.Row([self._label, self.switch, self.state_text], spacing=8)
        self._targets_yes: list[ft.Control] = []
        self._targets_no: list[ft.Control] = []

    def bind_form(self, form):
        self._targets_yes = [form.widgets[n] if isinstance(n, str) else n for n in self.show_on_yes]
        self._targets_no = [form.widgets[n] if isinstance(n, str) else n for n in self.show_on_no]
        self._sync_targets()

    def bind_controls(self, show_on_yes: Iterable[ft.Control] = (), show_on_no: Iterable[ft.Control] = ()):
        self._targets_yes = list(show_on_yes)
        self._targets_no = list(show_on_no)
        self._sync_targets()

    def _sync_targets(self):
        on = bool(self.switch.value)
        self.state_text.value = self.yes_text if on else self.no_text
        for ctrl in self._targets_yes:
            ctrl.visible = on
        for ctrl in self._targets_no:
            ctrl.visible = not on

    def _on_switch(self, e):
        self._sync_targets()
        self.refresh_targets()
        self.changed(e)

    def refresh_targets(self):
        from fletbatteries.utils import safe_update

        safe_update(self, *self._targets_yes, *self._targets_no)

    def get_value(self):
        return bool(self.switch.value)

    def set_value(self, value):
        self.switch.value = bool(value)
        self._sync_targets()

    def apply_label(self, label):
        self._label.value = label or ""
        self._label.visible = bool(label)


def _normalize_choices(choices) -> list[tuple[str, str]]:
    """Acepta [(key, text)], [key], {key: text} o un callable que devuelva cualquiera de esos."""
    if callable(choices):
        choices = choices()
    if isinstance(choices, dict):
        return [(str(k), str(v)) for k, v in choices.items()]
    result = []
    for c in choices or []:
        if isinstance(c, (tuple, list)):
            result.append((str(c[0]), str(c[1])))
        else:
            result.append((str(c), str(c)))
    return result


class Select(Widget):
    """Lista desplegable simple (Dropdown)."""

    def __init__(self, label=None, help_text=None, choices=(), width=None, expand=None, **kwargs):
        super().__init__(label=label, help_text=help_text, width=width, expand=expand, **kwargs)
        self.dropdown = ft.Dropdown(
            label=label,
            helper_text=help_text,
            options=[],
            on_select=self.changed,
            expand=True,
            editable=False,
        )
        self.set_choices(choices)
        self.content = self.dropdown

    def set_choices(self, choices):
        self.choices = _normalize_choices(choices)
        self.dropdown.options = [ft.DropdownOption(key=k, text=t) for k, t in self.choices]

    def get_value(self):
        return self.dropdown.value

    def set_value(self, value):
        self.dropdown.value = None if value in (None, "") else str(value)

    def show_error(self, message):
        self.dropdown.error_text = message

    def apply_label(self, label):
        self.dropdown.label = label


class RadioSelect(LabeledWidget):
    """Grupo de radios horizontal (o vertical con `vertical=True`)."""

    vertical = False

    def __init__(self, label=None, help_text=None, choices=(), vertical: Optional[bool] = None, **kwargs):
        if vertical is not None:
            self.vertical = vertical
        self.group = ft.RadioGroup(content=ft.Row(), on_change=self._on_group_change)
        super().__init__(self.group, label=label, help_text=help_text, **kwargs)
        self.set_choices(choices)

    def set_choices(self, choices):
        self.choices = _normalize_choices(choices)
        radios = [ft.Radio(value=k, label=t) for k, t in self.choices]
        self.group.content = ft.Column(radios, spacing=0) if self.vertical else ft.Row(radios, wrap=True)

    def _on_group_change(self, e):
        self.changed(e)

    def get_value(self):
        return self.group.value

    def set_value(self, value):
        self.group.value = None if value in (None, "") else str(value)


RadioHorizontalSelect = RadioSelect


class RadioVerticalSelect(RadioSelect):
    vertical = True


class NullBooleanSelect(RadioSelect):
    """Desconocido / Sí / No. El valor es `None`, `True` o `False`."""

    def __init__(self, label=None, **kwargs):
        kwargs.pop("choices", None)
        super().__init__(label=label, choices=[("", _("Unknown")), ("true", _("Yes")), ("false", _("No"))], **kwargs)
        self.group.value = ""

    def get_value(self):
        return {"true": True, "false": False}.get(self.group.value)

    def set_value(self, value):
        self.group.value = "" if value is None else ("true" if value else "false")


class CheckboxSelectMultiple(LabeledWidget):
    """Lista de checkboxes. El valor es la lista de llaves marcadas."""

    def __init__(self, label=None, help_text=None, choices=(), horizontal: bool = False, **kwargs):
        self.horizontal = horizontal
        self.box = ft.Row(wrap=True) if horizontal else ft.Column(spacing=0)
        super().__init__(self.box, label=label, help_text=help_text, **kwargs)
        self.set_choices(choices)

    def set_choices(self, choices):
        self.choices = _normalize_choices(choices)
        self.box.controls = [ft.Checkbox(label=t, data=k, value=False, on_change=self.changed) for k, t in self.choices]

    def get_value(self):
        return [c.data for c in self.box.controls if c.value]

    def set_value(self, value):
        selected = {str(v) for v in (value or [])}
        for c in self.box.controls:
            c.value = c.data in selected
