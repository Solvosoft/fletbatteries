import flet as ft


class WYSIWYGEditor(ft.Column):
    def __init__(self, label: str):
        super().__init__(spacing=10)
        self.styles = {"bold": False, "italic": False, "underline": False, "strike": False,
                       "align": "left", "color": ft.Colors.WHITE, "bg": None, "link_active": False}
        self.font_size = 16
        self.font_family = "Sans Serif"
        self._prev_color = ft.Colors.WHITE
        self.num_counter = 1


        self.toolbar = ft.Row([
            ft.Dropdown(width=100, options=[ft.dropdown.Option(str(s)) for s in [10,12,14,16,18,24,32]],
                        value=str(self.font_size), on_change=self.change_font_size),
            ft.Dropdown(width=120, options=[ft.dropdown.Option(f) for f in ["Sans Serif","Serif","Monospace"]],
                        value=self.font_family, on_change=self.change_font_family),
            ft.IconButton(icon=ft.Icons.FORMAT_BOLD, on_click=lambda e: self.toggle_style("bold")),
            ft.IconButton(icon=ft.Icons.FORMAT_ITALIC, on_click=lambda e: self.toggle_style("italic")),
            ft.IconButton(icon=ft.Icons.FORMAT_UNDERLINED, on_click=lambda e: self.toggle_style("underline")),
            ft.IconButton(icon=ft.Icons.STRIKETHROUGH_S, on_click=lambda e: self.toggle_style("strike")),
            ft.IconButton(icon=ft.Icons.ADD, on_click=lambda e: self.adjust_font_size(2)),
            ft.IconButton(icon=ft.Icons.REMOVE, on_click=lambda e: self.adjust_font_size(-2)),
            ft.IconButton(icon=ft.Icons.FORMAT_ALIGN_LEFT, on_click=lambda e: self.set_align("left")),
            ft.IconButton(icon=ft.Icons.FORMAT_ALIGN_CENTER, on_click=lambda e: self.set_align("center")),
            ft.IconButton(icon=ft.Icons.FORMAT_ALIGN_RIGHT, on_click=lambda e: self.set_align("right")),
            ft.IconButton(icon=ft.Icons.FORMAT_ALIGN_JUSTIFY, on_click=lambda e: self.set_align("justify")),
            ft.IconButton(icon=ft.Icons.FORMAT_LIST_BULLETED, on_click=lambda e: self.insert_bullet()),
            ft.IconButton(icon=ft.Icons.FORMAT_LIST_NUMBERED, on_click=lambda e: self.insert_numbered()),
            ft.IconButton(icon=ft.Icons.LINK, on_click=lambda e: self.toggle_link()),
            ft.IconButton(icon=ft.Icons.EMOJI_EMOTIONS, on_click=lambda e: self.insert_emoji("😊")),
            ft.IconButton(icon=ft.Icons.COLOR_LENS, on_click=lambda e: self.set_color(ft.Colors.RED)),
            ft.IconButton(icon=ft.Icons.FORMAT_COLOR_FILL, on_click=lambda e: self.set_bg(ft.Colors.YELLOW)),
        ], wrap=True, spacing=5)

        self.text_field = ft.TextField(label="Escribe aquí", multiline=True, expand=True, min_lines=8, border_color=ft.Colors.GREY_400, on_change=self.update_preview)
        self.preview_text = ft.Text("", size=self.font_size, font_family=self.font_family, color=self.styles["color"], selectable=False)
        self.preview_container = ft.Container(content=ft.Text(""), bgcolor=ft.Colors.GREY_900, padding=10, border_radius=5, expand=True)
        self.send_button = ft.ElevatedButton("Enviar", on_click=self.send_content)
        self.output_text = ft.Text("", selectable=True)
        self.output_container = ft.Container(content=ft.Text(""), padding=10, border=ft.border.all(1, ft.Colors.GREY_300), border_radius=5, bgcolor=ft.Colors.GREY_900, expand=True)

        self.controls.extend([
            ft.Text(label, size=16, weight="bold"),
            self.toolbar,
            self.text_field,
            ft.Text("Vista previa:", size=14, weight="bold"),
            self.preview_container,
            ft.Row([self.send_button]),
            ft.Text("Contenido enviado:", size=14, weight="bold"),
            self.output_container,
        ])


    def toggle_style(self, style):
        self.styles[style] = not self.styles[style]
        self.update_preview(None)
    def set_align(self, align):
        self.styles["align"] = align
        self.update_preview(None)
    def set_color(self, color):
        self.styles["color"] = None if self.styles["color"] == color else color
        self.update_preview(None)
    def set_bg(self, color):
        self.styles["bg"] = None if self.styles["bg"] == color else color
        self.update_preview(None)
    def toggle_link(self):
        if not self.styles["link_active"]:
            self._prev_color = self.styles["color"] or ft.Colors.WHITE
            self.styles["color"] = ft.Colors.BLUE
            self.styles["underline"] = True
            self.styles["link_active"] = True
        else:
            self.styles["color"] = self._prev_color
            self.styles["underline"] = False
            self.styles["link_active"] = False
        self.update_preview(None)
    def insert_bullet(self):
        self.text_field.value += ("\n" if self.text_field.value and not self.text_field.value.endswith("\n") else "") + "• "
        self.text_field.update(); self.update_preview(None)
    def insert_numbered(self):
        lines = self.text_field.value.split("\n")
        if lines and lines[-1].strip() == "": self.num_counter = 1
        line = f"{self.num_counter}. "
        self.text_field.value += ("\n" if self.text_field.value and not self.text_field.value.endswith("\n") else "") + line
        self.text_field.update(); self.update_preview(None); self.num_counter += 1
    def insert_emoji(self, emoji):
        self.text_field.value += (" " if self.text_field.value and not self.text_field.value.endswith(" ") else "") + emoji + " "
        self.text_field.update(); self.update_preview(None)
    def adjust_font_size(self, delta):
        self.font_size = max(8, self.font_size + delta)
        self.update_preview(None)
    def change_font_size(self, e):
        self.font_size = int(e.control.value)
        self.update_preview(None)
    def change_font_family(self, e):
        self.font_family = e.control.value
        self.update_preview(None)
    def _build_aligned_row(self, inner_container: ft.Container, align: str):
        left_spacer = ft.Container(expand=True)
        right_spacer = ft.Container(expand=True)
        inner_text: ft.Text = inner_container.content
        inner_container.expand = False; inner_text.expand = False
        inner_text.text_align = self.styles["align"]
        if align=="left": return ft.Row([inner_container, right_spacer], alignment=ft.MainAxisAlignment.CENTER)
        elif align=="center": return ft.Row([left_spacer, inner_container, right_spacer], alignment=ft.MainAxisAlignment.CENTER)
        elif align=="right": return ft.Row([left_spacer, inner_container], alignment=ft.MainAxisAlignment.CENTER)
        else: inner_container.expand=True; inner_text.expand=True; inner_text.text_align="justify"; return ft.Row([inner_container])
    def update_preview(self, e):
        text_value = self.text_field.value or ""
        decoration = None
        if self.styles["underline"] and self.styles["strike"]: decoration=ft.TextDecoration.UNDERLINE
        elif self.styles["underline"]: decoration=ft.TextDecoration.UNDERLINE
        elif self.styles["strike"]: decoration=ft.TextDecoration.LINE_THROUGH
        style=ft.TextStyle(size=self.font_size, font_family=self.font_family,
                           weight="bold" if self.styles["bold"] else "normal",
                           italic=self.styles["italic"],
                           decoration=decoration,
                           color=self.styles["color"] or ft.Colors.WHITE)
        self.preview_text.value=text_value
        self.preview_text.style=style
        try: self.preview_text.bgcolor=self.styles["bg"]
        except Exception: pass
        preview_inner = ft.Container(content=self.preview_text, padding=0)
        aligned=self._build_aligned_row(preview_inner, self.styles["align"])
        self.preview_container.content=aligned
        if getattr(self.preview_container, "page", None): self.preview_container.update()
    def send_content(self, e):
        text_value=self.text_field.value or ""
        decoration=None
        if self.styles["underline"] and self.styles["strike"]: decoration=ft.TextDecoration.UNDERLINE
        elif self.styles["underline"]: decoration=ft.TextDecoration.UNDERLINE
        elif self.styles["strike"]: decoration=ft.TextDecoration.LINE_THROUGH
        style=ft.TextStyle(size=self.font_size,font_family=self.font_family,
                           weight="bold" if self.styles["bold"] else "normal",
                           italic=self.styles["italic"],
                           decoration=decoration,
                           color=self.styles["color"] or ft.Colors.WHITE)
        self.output_text = ft.Text(text_value, selectable=True, style=style)
        try: self.output_text.bgcolor=self.styles["bg"]
        except Exception: pass
        output_inner=ft.Container(content=self.output_text,padding=0)
        aligned_out=self._build_aligned_row(output_inner,self.styles["align"])
        self.output_container.content=aligned_out
        if getattr(self.output_container, "page", None): self.output_container.update()



class WYSIWYGEditorMedia(WYSIWYGEditor):
    def __init__(self, label:str):
        super().__init__(label)

        self.photo_picker = ft.FilePicker(on_result=self._on_photo_picked)
        self.video_picker = ft.FilePicker(on_result=self._on_video_picked)
        self.toolbar.controls.append(
            ft.IconButton(icon=ft.Icons.IMAGE, tooltip="Subir Foto",
                          on_click=lambda e: self.photo_picker.pick_files(
                              allow_multiple=False, allowed_extensions=["jpg","png","jpeg"]))
        )
        self.toolbar.controls.append(
            ft.IconButton(icon=ft.Icons.VIDEO_FILE, tooltip="Subir Video",
                          on_click=lambda e: self.video_picker.pick_files(
                              allow_multiple=False, allowed_extensions=["mp4","avi","mov"]))
        )


        self.photo_image = None
        self.video_player = None

    def _on_photo_picked(self, e: ft.FilePickerResultEvent):
        if e.files:
            self.photo_image = ft.Image(src=e.files[0].path, width=200, height=200, fit=ft.ImageFit.CONTAIN)
            self.update_preview(None)

    def _on_video_picked(self, e: ft.FilePickerResultEvent):
        if e.files:
            self.video_player = ft.Video(src=e.files[0].path, width=300, height=200, autoplay=False, controls=True)
            self.update_preview(None)

    def update_preview(self, e):
        super().update_preview(e)
        controls = [self.preview_container.content]
        if self.photo_image:
            controls.append(self.photo_image)
        if self.video_player:
            controls.append(self.video_player)
        self.preview_container.content = ft.Column(controls)
        self.preview_container.update()

    def send_content(self, e):
        super().send_content(e)
        controls = [self.output_container.content]
        if self.photo_image:
            controls.append(self.photo_image)
        if self.video_player:
            controls.append(self.video_player)
        self.output_container.content = ft.Column(controls)
        self.output_container.update()


def main(page: ft.Page):
    page.title="Editor WYSIWYG con Preview y Envío"
    page.bgcolor=ft.Colors.BLACK; page.scroll="auto"

    editor1=WYSIWYGEditor("Editor con herramientas")
    editor2=WYSIWYGEditorMedia("Editor con herramientas + Foto/Video")

    page.overlay.append(editor2.photo_picker)
    page.overlay.append(editor2.video_picker)

    page.add(
        ft.Container(editor1, expand=True, padding=10),
        ft.Divider(),
        ft.Container(editor2, expand=True, padding=10)
    )

    editor1.update_preview(None)
    editor2.update_preview(None)

if __name__=="__main__":
    ft.app(target=main)