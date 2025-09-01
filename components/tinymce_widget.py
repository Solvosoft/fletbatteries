import flet as ft
import json
from urllib.parse import urlencode


class TinyMCEEditor(ft.Column):  # reemplazamos UserControl
    def __init__(
        self,
        static_port: int,
        name: str = "editor",
        preset: str = "basic",
        initial_value: str = "",
        image_upload_url: str | None = None,
        video_upload_url: str | None = None,
        height: int = 400,
        disabled: bool = False,
        on_change=None,
    ):
        super().__init__()
        self.static_port = static_port
        self.name = name
        self.preset = preset
        self.initial_value = initial_value
        self.image_upload_url = image_upload_url
        self.video_upload_url = video_upload_url
        self.height = height
        self.disabled = disabled
        self.on_change = on_change
        self._value = self.initial_value
        self._wv: ft.WebView | None = None

        # construir WebView
        params = {
            "name": self.name,
            "preset": self.preset,
            "initial": self.initial_value,
            "image_upload": self.image_upload_url,
            "video_upload": self.video_upload_url,
            "disabled": json.dumps(self.disabled),
        }
        url = f"http://127.0.0.1:{self.static_port}/editor.html?" + urlencode(params)

        self._wv = ft.WebView(
            url=url,
            width="infinite",
            height=self.height,
        )

        # asignar el handler después
        self._wv.on_web_message = self._handle_message

        # agregamos el WebView al Column
        self.controls.append(self._wv)

    def value(self) -> str:
        return self._value

    def set_value(self, html: str):
        self._value = html or ""
        if self._wv is not None:
            msg = {"type": "setContent", "name": self.name, "value": self._value}
            self._wv.post_message(json.dumps(msg))
        self.update()

    def set_disabled(self, disabled: bool = True):
        self.disabled = disabled
        if self._wv is not None:
            msg = {"type": "setDisabled", "name": self.name, "value": bool(disabled)}
            self._wv.post_message(json.dumps(msg))
        self.update()

    def _handle_message(self, e):
        try:
            data = json.loads(e.data)
        except Exception:
            return

        if data.get("type") == "contentChange" and data.get("name") == self.name:
            self._value = data.get("value", "")
            if callable(self.on_change):
                self.on_change(self._value)
        elif data.get("type") == "ready" and data.get("name") == self.name:
            if self._value:
                self.set_value(self._value)
            if self.disabled:
                self.set_disabled(True)