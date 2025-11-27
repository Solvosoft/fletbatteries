import flet as ft
from typing import Callable, Optional, Literal
from controls.utils import show_snackbar

ModalKind = Literal["create", "edit", "delete", "detail"]


class CrudModal:
    def __init__(self, page: ft.Page):
        self.page = page
        self.dialog: Optional[ft.AlertDialog] = None
        self._btn_accept: Optional[ft.Control] = None
        self._btn_cancel: Optional[ft.Control] = None
        self._processing_row = ft.Row(
            controls=[ft.ProgressRing(width=18, height=18), ft.Text("Procesando...", size=12)],
            spacing=8,
            visible=False,
        )
        self._on_accept: Optional[Callable[[], Optional[bool]]] = None
        self._success_text = "Operación exitosa"
        self._error_text = "Lo sentimos, ocurrió un error"

    def open(
        self,
        kind: ModalKind,
        title: str,
        content_controls: list[ft.Control],
        on_accept: Optional[Callable[[], Optional[bool]]] = None,
        success_text: str = "Operación exitosa",
        error_text: str = "Lo sentimos, ocurrió un error",
        width: Optional[int] = 520,
    ):
        self._on_accept = on_accept
        self._success_text = success_text
        self._error_text = error_text

        # ancho efectivo
        title_ctl = ft.Container(
            width=width,
            padding=ft.padding.symmetric(horizontal=12, vertical=10),
            border=ft.border.only(bottom=ft.BorderSide(2, ft.Colors.PRIMARY)),
            content=ft.Text(title, size=18, weight=ft.FontWeight.BOLD),
        )

        body_column = ft.Column(
            tight=True,
            spacing=10,
            controls=[*content_controls, self._processing_row],
            scroll=ft.ScrollMode.AUTO,  # por si el contenido crece
        )
        content_ctl = ft.Container(width=width, padding=10, content=body_column)

        cancel_text = "Cerrar" if kind == "detail" else "Cancelar"
        self._btn_cancel = ft.TextButton(cancel_text, on_click=lambda e: self._close())

        self._btn_accept = None
        if kind in ("create", "edit", "delete") and on_accept is not None:
            label = "Guardar" if kind == "create" else ("Actualizar" if kind == "edit" else "Eliminar")
            style = None
            if kind == "delete":
                style = ft.ButtonStyle(bgcolor=ft.Colors.RED_600, color=ft.Colors.WHITE)
            self._btn_accept = ft.ElevatedButton(label, on_click=self._on_accept_click, style=style)

        actions = [self._btn_cancel] if self._btn_accept is None else [self._btn_cancel, self._btn_accept]

        self.dialog = ft.AlertDialog(
            modal=True,
            title=title_ctl,
            content=content_ctl,
            actions=actions,
            actions_alignment=ft.MainAxisAlignment.END,
        )


        self.page.open(self.dialog)

    def _close(self):
        if self.dialog:
            self.page.close(self.dialog)

    def _set_processing(self, value: bool):
        if self._btn_cancel:
            self._btn_cancel.disabled = value
        if self._btn_accept:
            self._btn_accept.disabled = value
        self._processing_row.visible = value
        self.page.update()

    def _on_accept_click(self, e: ft.ControlEvent):
        if not self._on_accept:
            self._close()
            return

        self._set_processing(True)
        try:
            result = self._on_accept()  # True / False / None
        except Exception as ex:
            print(f"[CrudModal] Error en callback: {ex}")
            result = False
        self._set_processing(False)

        if result:
            self._close()

        if result is True:
            self._show_snackbar(self._success_text, success=True)
        elif result is False:
            self._show_snackbar(self._error_text, success=False)

    def _show_snackbar(self, message: str, success: bool):
        snack = show_snackbar(message, success)
        self.page.open(snack)

