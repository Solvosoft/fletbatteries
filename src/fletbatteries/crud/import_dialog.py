"""
Diálogo para importar un CSV: elegir archivo, revisar la vista previa (con los
errores por fila) e importar las filas válidas.

    ImportDialog(page, CSVImporter(CustomerForm, source, key_field="email"),
                 on_done=lambda counts: table.reload()).open()
"""

import logging
from pathlib import Path
from typing import Callable, Optional

import flet as ft

from fletbatteries.data.importer import CSVImporter, ImportResult
from fletbatteries.i18n import _
from fletbatteries.utils import close_dialog, notify, safe_update

log = logging.getLogger(__name__)

PREVIEW_ROWS = 50


class ImportDialog:
    def __init__(self, page: ft.Page, importer: CSVImporter, title: Optional[str] = None,
                 on_done: Optional[Callable[[dict], None]] = None, wrap: Optional[Callable] = None,
                 width: int = 760):
        self.app_page = page
        self.importer = importer
        self.title = title or _("Import CSV")
        self.on_done = on_done
        # `wrap()` devuelve un context manager para guardar (p. ej. acting_as(usuario))
        self.wrap = wrap
        self.width = width
        self.result: Optional[ImportResult] = None
        self.file_name = ""

        self.file_text = ft.Text(_("No file selected"), italic=True, key="import_file_text")
        self.summary = ft.Text("", key="import_summary", visible=False)
        self.error_text = ft.Text("", color=ft.Colors.ERROR, visible=False, key="import_error")
        self.preview_area = ft.Column([], tight=True, spacing=6)
        self.import_button = ft.Button(_("Import"), icon=ft.Icons.UPLOAD, disabled=True, on_click=self._on_import,
                                       key="import_run")
        self.dialog: Optional[ft.AlertDialog] = None

    # ------------------------------------------------------------------
    def open(self):
        body = ft.Column(
            [
                ft.Text(_("Columns are matched by field name or label. Rows with errors are skipped."), size=12),
                ft.Row(
                    [
                        ft.Button(_("Select CSV file"), icon=ft.Icons.FILE_OPEN, on_click=self.pick,
                                  key="import_pick"),
                        ft.TextButton(_("Download template"), icon=ft.Icons.DOWNLOAD,
                                      on_click=self.download_template, key="import_template"),
                    ],
                    wrap=True,
                ),
                self.file_text,
                self.error_text,
                self.summary,
                self.preview_area,
            ],
            tight=True,
            spacing=10,
            scroll=ft.ScrollMode.AUTO,
        )
        self.dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(self.title, size=18, weight=ft.FontWeight.BOLD),
            content=ft.Container(body, width=self.width, height=460),
            actions=[ft.TextButton(_("Close"), on_click=lambda e: self.close(), key="import_close"),
                     self.import_button],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.app_page.show_dialog(self.dialog)

    def close(self):
        if self.dialog is not None:
            close_dialog(self.dialog)

    # ------------------------------------------------------------------
    async def pick(self, e=None):
        files = await ft.FilePicker().pick_files(
            allow_multiple=False,
            file_type=ft.FilePickerFileType.CUSTOM,
            allowed_extensions=["csv", "txt"],
            with_data=bool(self.app_page.web),
        )
        if not files:
            return
        f = files[0]
        data = f.bytes
        if data is None and f.path:
            data = Path(f.path).read_bytes()
        self.load(f.name, data or b"")

    def load(self, name: str, data: bytes):
        """Lee el archivo y muestra la vista previa (también se puede llamar directamente)."""
        self.file_name = name
        self.file_text.value = _("Selected: {name}", name=name)
        self.result = self.importer.preview(data)
        self._render_preview()

    def _render_preview(self):
        result = self.result
        self.error_text.visible = bool(result.error)
        self.error_text.value = result.error or ""
        self.summary.visible = result.error is None
        self.summary.value = _("{new} new, {updated} to update, {errors} with errors",
                               new=result.to_create, updated=result.to_update, errors=len(result.invalid_rows))
        if result.unknown_columns:
            self.summary.value += "\n" + _("Ignored columns: {columns}", columns=", ".join(result.unknown_columns))
        self.import_button.disabled = not result.valid_rows
        self.preview_area.controls = self._preview_table() if result.rows else []
        safe_update(self.dialog)

    def _preview_table(self) -> list[ft.Control]:
        fields = self.importer.import_fields()
        names = list(dict.fromkeys(self.result.columns.values()))
        columns = [ft.DataColumn(ft.Text(_("Line"))), ft.DataColumn(ft.Text(_("Status")))]
        columns += [ft.DataColumn(ft.Text(fields[n].label if n in fields else n)) for n in names]
        rows = []
        for row in self.result.rows[:PREVIEW_ROWS]:
            status = (ft.Text(_("Update") if row.action == "update" else _("New"), color=ft.Colors.PRIMARY)
                      if row.valid else ft.Text(row.error_text(), color=ft.Colors.ERROR, size=12))
            cells = [ft.DataCell(ft.Text(str(row.line))), ft.DataCell(status)]
            reverse = {v: k for k, v in self.result.columns.items()}
            cells += [ft.DataCell(ft.Text(str(row.raw.get(reverse.get(n), "") or ""))) for n in names]
            rows.append(ft.DataRow(cells=cells))
        controls: list[ft.Control] = [ft.Row([ft.DataTable(columns=columns, rows=rows)], scroll=ft.ScrollMode.AUTO)]
        if len(self.result.rows) > PREVIEW_ROWS:
            controls.append(ft.Text(_("Showing {shown} of {total} rows", shown=PREVIEW_ROWS,
                                      total=len(self.result.rows)), italic=True, size=12))
        return controls

    def run(self) -> dict:
        if self.wrap is not None:
            with self.wrap():
                return self.importer.run(self.result)
        return self.importer.run(self.result)

    def _on_import(self, e=None):
        if not self.result or not self.result.valid_rows:
            return
        counts = self.run()
        self.close()
        message = _("Import finished: {created} created, {updated} updated, {failed} failed",
                    created=counts["created"], updated=counts["updated"], failed=counts["failed"])
        notify(self.app_page, message, success=counts["failed"] == 0)
        if self.on_done:
            self.on_done(counts)

    async def download_template(self, e=None):
        from fletbatteries.widgets.datatable import save_bytes

        await save_bytes(self.app_page, "template.csv", self.importer.template_csv())
