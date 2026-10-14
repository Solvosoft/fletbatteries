"""Modal genérico para crear, editar, eliminar o ver detalle de un registro."""

import logging
from typing import Callable, Literal, Optional

import flet as ft

from fletbatteries.i18n import _
from fletbatteries.utils import close_dialog, show_snackbar

ModalKind = Literal["create", "edit", "delete", "detail"]

log = logging.getLogger(__name__)


class CrudModal:
    """
    AlertDialog con estado "procesando" y SnackBar de resultado.

    `on_accept` devuelve `True` (éxito: cierra y muestra `success_text`),
    `False` (error: muestra `error_text` y deja el diálogo abierto), un `str`
    (error con ese mensaje) o `None` (deja el diálogo abierto sin mensaje, p.
    ej. porque el formulario tiene errores que ya se muestran en los campos).

    `success_action=(texto, callback)` agrega un botón al SnackBar de éxito
    (por ejemplo "Deshacer" después de eliminar).
    """

    def __init__(self, page: ft.Page):
        self.page = page
        self.dialog: Optional[ft.AlertDialog] = None
        self._btn_accept: Optional[ft.Control] = None
        self._btn_cancel: Optional[ft.Control] = None
        self._processing_row = ft.Row(
            controls=[ft.ProgressRing(width=18, height=18), ft.Text(_("Processing..."), size=12)],
            spacing=8,
            visible=False,
        )
        self._on_accept: Optional[Callable[[], Optional[bool]]] = None
        self._success_text = _("Operation successful")
        self._error_text = _("Sorry, an error occurred")
        self._success_action = None

    def open(
        self,
        kind: ModalKind,
        title: str,
        content_controls: list[ft.Control],
        on_accept: Optional[Callable[[], Optional[bool]]] = None,
        success_text: Optional[str] = None,
        error_text: Optional[str] = None,
        width: Optional[int] = 520,
        accept_text: Optional[str] = None,
        success_action: Optional[tuple] = None,
        actions: Optional[list] = None,
    ):
        self._on_accept = on_accept
        self._success_text = success_text or _("Operation successful")
        self._error_text = error_text or _("Sorry, an error occurred")
        self._success_action = success_action

        title_ctl = ft.Container(
            width=width,
            padding=ft.Padding.symmetric(horizontal=12, vertical=10),
            border=ft.Border.only(bottom=ft.BorderSide(2, ft.Colors.PRIMARY)),
            content=ft.Text(title, size=18, weight=ft.FontWeight.BOLD),
        )
        self._processing_row.visible = False
        body_column = ft.Column(
            tight=True,
            spacing=10,
            controls=[*content_controls, self._processing_row],
            scroll=ft.ScrollMode.AUTO,
        )
        content_ctl = ft.Container(width=width, padding=10, content=body_column)

        cancel_text = _("Close") if kind == "detail" else _("Cancel")
        self._btn_cancel = ft.TextButton(cancel_text, on_click=lambda e: self.close())

        self._btn_accept = None
        if kind in ("create", "edit", "delete") and on_accept is not None:
            label = accept_text or {"create": _("Save"), "edit": _("Update"), "delete": _("Delete")}[kind]
            style = ft.ButtonStyle(bgcolor=ft.Colors.ERROR, color=ft.Colors.ON_ERROR) if kind == "delete" else None
            self._btn_accept = ft.Button(label, on_click=self._on_accept_click, style=style)

        actions = [*(actions or []), self._btn_cancel]
        if self._btn_accept is not None:
            actions.append(self._btn_accept)

        self.dialog = ft.AlertDialog(
            modal=True,
            title=title_ctl,
            content=content_ctl,
            actions=actions,
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.show_dialog(self.dialog)

    def close(self):
        if self.dialog:
            close_dialog(self.dialog)

    # Compatibilidad con el nombre anterior
    _close = close

    def _set_processing(self, value: bool):
        if self._btn_cancel:
            self._btn_cancel.disabled = value
        if self._btn_accept:
            self._btn_accept.disabled = value
        self._processing_row.visible = value
        self.page.update()

    def _on_accept_click(self, e: ft.ControlEvent):
        if not self._on_accept:
            self.close()
            return

        self._set_processing(True)
        try:
            result = self._on_accept()
        except Exception:
            log.exception("Error en el callback del modal")
            result = False
        self._set_processing(False)

        if result is True:
            self.close()
            label, callback = self._success_action or (None, None)
            self.page.show_dialog(show_snackbar(self._success_text, success=True, action=label, on_action=callback))
        elif result is False:
            self.page.show_dialog(show_snackbar(self._error_text, success=False))
        elif isinstance(result, str):
            self.page.show_dialog(show_snackbar(result, success=False))
