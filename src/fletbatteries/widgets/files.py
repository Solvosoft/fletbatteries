"""Selección de archivos e imágenes (equivalentes a FileInput/ClearableFileInput)."""

import hashlib
import os
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Sequence

import flet as ft

from fletbatteries.i18n import _
from fletbatteries.widgets.base import LabeledWidget


@dataclass
class UploadedFile:
    """
    Archivo elegido por el usuario.

    En escritorio trae `path`; en web (o con `with_data=True`) trae `content`.

    Un archivo que ya estaba guardado (el valor al editar un registro) tiene
    `stored=True`: no se vuelve a copiar al guardar. `url` es el `src` para la
    vista previa (p. ej. "image/foto.png" relativo a los assets).
    """

    name: str
    path: Optional[str] = None
    size: Optional[int] = None
    content: Optional[bytes] = field(default=None, repr=False)
    stored: bool = False
    url: Optional[str] = None

    @property
    def is_new(self) -> bool:
        """True si el usuario lo acaba de elegir (hay que guardarlo)."""
        return not self.stored

    @classmethod
    def existing(cls, name: str, upload_to=None, media_url: Optional[str] = None) -> "UploadedFile":
        """Archivo ya guardado a partir de su nombre."""
        name = os.path.basename(str(name))
        path = str(Path(upload_to) / name) if upload_to else None
        return cls(name=name, path=path, stored=True, url=f"{media_url}{name}" if media_url is not None else None)

    def read(self) -> bytes:
        if self.content is not None:
            return self.content
        with open(self.path, "rb") as f:
            return f.read()

    def md5(self) -> str:
        return hashlib.md5(self.read()).hexdigest()

    def save_to(self, directory, name: Optional[str] = None) -> Path:
        """Copia el archivo a `directory` y devuelve la ruta destino (los ya guardados no se copian)."""
        directory = Path(directory)
        if self.stored:
            return directory / (name or self.name)
        directory.mkdir(parents=True, exist_ok=True)
        dest = directory / (name or os.path.basename(self.name))
        if self.content is not None:
            dest.write_bytes(self.content)
        elif self.path and os.path.abspath(self.path) != os.path.abspath(dest):
            shutil.copy(self.path, dest)
        return dest

    @property
    def extension(self) -> str:
        return os.path.splitext(self.name)[1].lower().lstrip(".")

    def __str__(self):
        return self.name


class FileInput(LabeledWidget):
    """
    Botón para elegir un archivo. El valor es un `UploadedFile` (o `None`).

    En modo web se piden los bytes (`with_data`) porque no hay ruta local.
    """

    icon = ft.Icons.UPLOAD_FILE
    button_text = None
    clearable = False
    file_type = ft.FilePickerFileType.ANY
    show_preview = False

    def __init__(self, label=None, help_text=None, allowed_extensions: Optional[Sequence[str]] = None,
                 with_data: Optional[bool] = None, media_url: Optional[str] = None, **kwargs):
        self.allowed_extensions = list(allowed_extensions) if allowed_extensions else None
        self.with_data = with_data
        self.media_url = media_url
        self._file: Optional[UploadedFile] = None
        self.button = ft.Button(content=self.button_text or _("Select file"), icon=self.icon, on_click=self.pick)
        self.file_text = ft.Text(_("No file selected"))
        self.clear_button = ft.IconButton(icon=ft.Icons.CLOSE, tooltip=_("Remove"), visible=False,
                                          on_click=lambda e: self.clear())
        self.preview = ft.Image(src="", width=96, height=96, fit=ft.BoxFit.COVER, border_radius=6, visible=False)
        body = ft.Column(
            [ft.Row([self.button, self.file_text, self.clear_button], spacing=10, wrap=True), self.preview],
            spacing=6,
            tight=True,
        )
        super().__init__(body, label=label, help_text=help_text, **kwargs)

    async def pick(self, e=None):
        page = self.app_page
        with_data = self.with_data if self.with_data is not None else bool(page and page.web)
        picker = ft.FilePicker()
        files = await picker.pick_files(
            allow_multiple=False,
            file_type=ft.FilePickerFileType.CUSTOM if self.allowed_extensions else self.file_type,
            allowed_extensions=self.allowed_extensions,
            with_data=with_data,
        )
        if not files:
            return
        f = files[0]
        self.set_value(UploadedFile(name=f.name, path=f.path, size=f.size, content=f.bytes))
        self.refresh()
        self.changed()

    def clear(self):
        self.set_value(None)
        self.refresh()
        self.changed()

    def get_value(self):
        return self._file

    def set_value(self, value):
        if isinstance(value, str) and value:
            # Un nombre/ruta como valor = archivo que ya estaba guardado
            value = UploadedFile.existing(value, media_url=self.media_url)
        self._file = value or None
        if self._file is None:
            self.file_text.value = _("No file selected")
        elif self._file.stored:
            self.file_text.value = _("Current file: {name}", name=self._file.name)
        else:
            self.file_text.value = _("Selected: {name}", name=self._file.name)
        self.clear_button.visible = bool(self._file) and self.clearable
        if self.show_preview:
            self.preview.src = self._preview_src() or ""
            self.preview.visible = bool(self.preview.src)

    def _preview_src(self):
        f = self._file
        if f is None:
            return None
        if f.content is not None:
            return f.content
        if f.url:
            return f.url
        if f.path and os.path.isabs(f.path) and os.path.exists(f.path):
            return f.path
        return None


class ClearableFileInput(FileInput):
    clearable = True


class ImageInput(ClearableFileInput):
    """Imagen con vista previa."""

    icon = ft.Icons.IMAGE
    file_type = ft.FilePickerFileType.IMAGE
    show_preview = True

    def __init__(self, label=None, allowed_extensions=("jpg", "jpeg", "png", "gif", "webp"), **kwargs):
        self.button_text = _("Select image")
        super().__init__(label=label, allowed_extensions=allowed_extensions, **kwargs)
