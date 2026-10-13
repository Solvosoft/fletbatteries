import flet as ft
from flet import Rotate, Animation
from math import pi
import asyncio


class SpinnerLoader(ft.Column):

    def __init__(
        self,
        steps: int = 12,
        size: int = 120,
        arm_length: int = 34,
        thickness: int = 10,
        base_color: str = ft.Colors.BLACK,
        min_opacity: float = 0.2,
        interval: float = 0.08,
        text: str | None = "LOADING...",
        text_size: int = 16,
        text_weight: ft.FontWeight = ft.FontWeight.W_600,
        text_color: str = "#666666",
    ):
        super().__init__(spacing=10, horizontal_alignment=ft.CrossAxisAlignment.CENTER)

        self.steps = steps
        self.size = size
        self.arm_length = arm_length
        self.thickness = thickness
        self.base_color = base_color
        self.min_opacity = min_opacity
        self.interval = interval
        self.text = text
        self.text_size = text_size
        self.text_weight = text_weight
        self.text_color = text_color

        self._running = False

        self._ticks: list[ft.Container] = []
        for i in range(self.steps):
            bar = ft.Container(
                width=self.thickness,
                height=self.arm_length,
                bgcolor=self.base_color,
                border_radius=ft.BorderRadius.all(self.thickness // 2),
                opacity=1.0 if i == 0 else self.min_opacity,
            )
            canvas = ft.Container(
                width=self.size,
                height=self.size,
                alignment=ft.Alignment.TOP_CENTER,
                content=bar,
                rotate=Rotate(angle=(i * 2 * pi / self.steps)),
                animate_rotation=Animation(400, ft.AnimationCurve.LINEAR),
            )
            self._ticks.append(canvas)

        self._spinner = ft.Stack(
            width=self.size,
            height=self.size,
            controls=self._ticks,
            alignment=ft.Alignment.CENTER,
        )

        if self.text is not None:
            self._label = ft.Text(
                self.text,
                size=self.text_size,
                weight=self.text_weight,
                color=self.text_color,
                text_align=ft.TextAlign.CENTER,
            )
            self.controls = [self._spinner, self._label]
        else:
            self.controls = [self._spinner]

    def did_mount(self):
        self._running = True
        self.page.run_task(self._animate_loop)

    def will_unmount(self):
        self._running = False

    def set_text(self, value: str | None):
        self.text = value
        if value is None:
            if len(self.controls) == 2:
                self.controls = [self._spinner]
                self.update()
        else:
            if len(self.controls) == 1:
                self._label = ft.Text(
                    value,
                    size=self.text_size,
                    weight=self.text_weight,
                    color=self.text_color,
                    text_align=ft.TextAlign.CENTER,
                )
                self.controls = [self._spinner, self._label]
            else:
                self._label.value = value
            self.update()

    # animation
    async def _animate_loop(self):
        head = 0
        while self._running:
            for idx, tick in enumerate(self._ticks):
                d = (idx - head) % self.steps
                opacity = max(self.min_opacity, 1.0 - (d / (self.steps - 1)))
                tick.content.opacity = opacity
            try:
                self._spinner.update()
            except RuntimeError:
                # El loader ya no está en la página
                break
            head = (head + 1) % self.steps
            await asyncio.sleep(self.interval)
