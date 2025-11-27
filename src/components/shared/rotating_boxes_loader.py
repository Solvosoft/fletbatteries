import flet as ft
from flet import Rotate, Animation, border, alignment
from math import pi
import threading
import time


class AnimatedBox(ft.Container):
    def __init__(self, size: int, border_color: str, bg_color: str | None, rotate_angle: float, border_width: float = 2.5):
        super().__init__(
            width=size,
            height=size,
            border=border.all(border_width, border_color),
            bgcolor=bg_color,
            border_radius=2,
            rotate=Rotate(angle=rotate_angle, alignment=alignment.center),
            animate_rotation=Animation(700, ft.AnimationCurve.EASE_IN_OUT),
        )


class RotatingBoxesLoader(ft.Stack):

    def __init__(
        self,
        size: int = 100,
        color_a_border: str = "#e9665a",
        color_b_border: str = "#7df6dd",
        color_a_bg: str | None = None,
        color_b_bg: str | None = "#1f262f",
        text: str | None = "Loading...",
        text_size: int = 14,
        text_color: str = "white",
        step_seconds: float = 0.7,
        border_width: float = 2.5,
    ):
        super().__init__(alignment=ft.alignment.center)

        self.size = size
        self.color_a_border = color_a_border
        self.color_b_border = color_b_border
        self.color_a_bg = color_a_bg
        self.color_b_bg = color_b_bg
        self.text = text
        self.text_size = text_size
        self.text_color = text_color
        self.step_seconds = step_seconds
        self.border_width = border_width

        self.red_box = AnimatedBox(size, color_a_border, color_a_bg, 0, border_width)
        self.blue_box = AnimatedBox(size, color_b_border, color_b_bg, pi / 4, border_width)

        controls = [self.red_box, self.blue_box]
        if self.text is not None:
            controls.append(
                ft.Text(self.text, size=self.text_size, color=self.text_color, text_align=ft.TextAlign.CENTER)
            )
        self.controls = controls

        self._running = False
        self._thread: threading.Thread | None = None

    def did_mount(self):
        self._running = True
        self._thread = threading.Thread(target=self._animate_loop, daemon=True)
        self._thread.start()

    def will_unmount(self):
        self._running = False

    def _animate_loop(self):
        cw = pi / 4
        ccw = -2 * pi
        cnt = 0
        while self._running:
            if cnt <= 4:
                self.red_box.rotate = Rotate(angle=ccw, alignment=alignment.center)
                self.blue_box.rotate = Rotate(angle=cw, alignment=alignment.center)
                self.red_box.update()
                self.blue_box.update()
                cw += pi / 2
                ccw -= pi / 2
                cnt += 1
            elif cnt <= 10:
                cw -= pi / 2
                ccw += pi / 2
                self.red_box.rotate = Rotate(angle=ccw, alignment=alignment.center)
                self.blue_box.rotate = Rotate(angle=cw, alignment=alignment.center)
                self.red_box.update()
                self.blue_box.update()
                cnt += 1
            else:
                cnt = 0
            time.sleep(self.step_seconds)
