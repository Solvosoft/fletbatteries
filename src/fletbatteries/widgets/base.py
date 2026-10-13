"""
Contrato común de los widgets de entrada.

Todo widget es un control de Flet (se puede poner en cualquier layout) y además
expone:

- `value`: valor actual (get/set). El tipo depende del widget.
- `error`: texto de error que se muestra bajo el campo (`None` lo quita).
- `on_change`: callback `fn(widget)` que se llama cuando el usuario cambia el valor.
- `label`, `help_text`, `disabled`.

Las subclases implementan `get_value()`, `set_value(value)` y `show_error(msg)`.
"""

from typing import Any, Callable, Optional

import flet as ft

from fletbatteries.utils import get_page, safe_update


class Widget(ft.Container):
    """Base de los widgets de entrada de FletBatteries."""

    def __init__(
        self,
        label: Optional[str] = None,
        help_text: Optional[str] = None,
        on_change: Optional[Callable[["Widget"], Any]] = None,
        disabled: bool = False,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.label = label
        self.help_text = help_text
        self.disabled = disabled
        self._on_change = [on_change] if on_change else []
        self._error: Optional[str] = None

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------
    @property
    def value(self):
        return self.get_value()

    @value.setter
    def value(self, value):
        self.set_value(value)
        self.refresh()

    @property
    def error(self) -> Optional[str]:
        return self._error

    @error.setter
    def error(self, message: Optional[str]):
        self._error = message or None
        self.show_error(self._error)
        self.refresh()

    @property
    def on_change(self):
        return self._on_change[0] if self._on_change else None

    @on_change.setter
    def on_change(self, callback):
        self._on_change = [callback] if callback else []

    def add_change_listener(self, callback: Callable[["Widget"], Any]):
        self._on_change.append(callback)

    def hide_label(self):
        """Quita la etiqueta propia del widget (la usa el render horizontal del formulario)."""
        self.label = None
        self.apply_label(None)

    def refresh(self):
        safe_update(self)

    @property
    def app_page(self) -> Optional[ft.Page]:
        return get_page(self)

    # ------------------------------------------------------------------
    # A implementar por las subclases
    # ------------------------------------------------------------------
    def get_value(self):
        raise NotImplementedError

    def set_value(self, value):
        raise NotImplementedError

    def show_error(self, message: Optional[str]):
        pass

    def apply_label(self, label: Optional[str]):
        pass

    # ------------------------------------------------------------------
    # Helpers para subclases
    # ------------------------------------------------------------------
    def changed(self, e=None):
        """Notifica a los listeners que el valor cambió (llamar desde los handlers internos)."""
        if self._error:
            self.error = None
        for callback in list(self._on_change):
            callback(self)


class LabeledWidget(Widget):
    """
    Widget compuesto: etiqueta arriba, contenido y texto de ayuda/error abajo.

    Útil para widgets que no son un TextField (checkbox, radios, listas, etc.).
    """

    def __init__(self, body: ft.Control, label: Optional[str] = None, help_text: Optional[str] = None, **kwargs):
        super().__init__(label=label, help_text=help_text, **kwargs)
        self._label_text = ft.Text(label or "", size=12, weight=ft.FontWeight.W_500, visible=bool(label))
        self._help_text = ft.Text(help_text or "", size=11, color=ft.Colors.OUTLINE, visible=bool(help_text))
        self._error_text = ft.Text("", size=11, color=ft.Colors.ERROR, visible=False)
        self.body = body
        self.content = ft.Column(
            controls=[self._label_text, body, self._help_text, self._error_text],
            spacing=4,
            tight=True,
        )

    def show_error(self, message: Optional[str]):
        self._error_text.value = message or ""
        self._error_text.visible = bool(message)

    def apply_label(self, label: Optional[str]):
        self._label_text.value = label or ""
        self._label_text.visible = bool(label)
