"""Editor Markdown con vista previa (reemplaza a los editores WYSIWYG/TinyMCE de djgentelella)."""

import flet as ft

from fletbatteries.i18n import _
from fletbatteries.widgets.base import Widget


class MarkdownInput(Widget):
    def __init__(self, label=None, help_text=None, min_lines: int = 6, max_lines: int = 20, **kwargs):
        super().__init__(label=label, help_text=help_text, **kwargs)
        self.min_lines = min_lines
        self.editor = ft.TextField(label=label, helper=help_text, multiline=True, min_lines=min_lines,
                                   max_lines=max_lines, on_change=self._on_text)
        self.preview = ft.Markdown("", selectable=True, extension_set=ft.MarkdownExtensionSet.GITHUB_WEB)
        self.empty_text = ft.Text(_("Nothing to preview"), italic=True, color=ft.Colors.OUTLINE)
        # Altura fija con scroll propio: se dibuja bien en cualquier contenedor (incluso dentro de un diálogo)
        self.preview_box = ft.Container(
            content=ft.Column([self.preview], scroll=ft.ScrollMode.AUTO, horizontal_alignment=ft.CrossAxisAlignment.STRETCH),
            padding=12,
            height=max(120, min_lines * 28),
            border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
            border_radius=6,
            key="markdown_preview",
        )
        self.previewing = False
        self.write_button = ft.TextButton(_("Write"), icon=ft.Icons.EDIT, disabled=True,
                                          on_click=lambda e: self.show_preview(False))
        self.preview_button = ft.TextButton(_("Preview"), icon=ft.Icons.VISIBILITY,
                                            on_click=lambda e: self.show_preview(True))
        self.toolbar = ft.Row([
            self.write_button,
            self.preview_button,
            ft.Container(width=12),
            *[ft.IconButton(icon=icon, tooltip=hint, on_click=lambda e, w=wrap: self._wrap(w))
              for icon, hint, wrap in (
                  (ft.Icons.FORMAT_BOLD, "**", "**"),
                  (ft.Icons.FORMAT_ITALIC, "_", "_"),
                  (ft.Icons.CODE, "`", "`"),
              )],
            ft.IconButton(icon=ft.Icons.FORMAT_LIST_BULLETED, tooltip="- ", on_click=lambda e: self._append("\n- ")),
            ft.IconButton(icon=ft.Icons.TITLE, tooltip="# ", on_click=lambda e: self._append("\n## ")),
        ], spacing=0)
        self.body = ft.Container(content=self.editor)
        self.content = ft.Column([self.toolbar, self.body], spacing=4, tight=True,
                                 horizontal_alignment=ft.CrossAxisAlignment.STRETCH)

    def _on_text(self, e):
        self.preview.value = self.editor.value or ""
        self.changed(e)

    def _wrap(self, mark: str):
        self.editor.value = f"{self.editor.value or ''}{mark}{mark}"
        self._on_text(None)
        self.refresh()

    def _append(self, text: str):
        self.editor.value = f"{self.editor.value or ''}{text}"
        self._on_text(None)
        self.refresh()

    def show_preview(self, preview: bool):
        """Cambia entre el editor y la vista previa (se intercambia el contenido)."""
        self.previewing = preview
        text = self.editor.value or ""
        self.preview.value = text
        self.preview_box.content.controls = [self.preview] if text.strip() else [self.empty_text]
        self.body.content = self.preview_box if preview else self.editor
        self.write_button.disabled = not preview
        self.preview_button.disabled = preview
        self.refresh()

    def get_value(self):
        return self.editor.value or ""

    def set_value(self, value):
        self.editor.value = value or ""
        self.preview.value = self.editor.value

    def show_error(self, message):
        self.editor.error = message

    def apply_label(self, label):
        self.editor.label = label
