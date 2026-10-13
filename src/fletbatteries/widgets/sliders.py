"""Sliders de rango, de un valor y la perilla numérica (knob)."""

import math
from typing import Optional

import flet as ft

from fletbatteries.widgets.base import LabeledWidget


def _fmt(value, decimals):
    return f"{value:.{decimals}f}" if decimals else str(int(round(value)))


class GridSlider(LabeledWidget):
    """Rango entre `min` y `max`. El valor es `(inicio, fin)`."""

    def __init__(self, label=None, help_text=None, min: float = 0, max: float = 100, divisions: Optional[int] = None,
                 decimals: int = 0, prefix: str = "", suffix: str = "", **kwargs):
        self.decimals = decimals
        self.prefix, self.suffix = prefix, suffix
        self.slider = ft.RangeSlider(min=min, max=max, start_value=min, end_value=max, divisions=divisions,
                                     on_change=self._on_slide)
        self.range_text = ft.Text(size=12)
        super().__init__(ft.Column([self.slider, self.range_text], spacing=0, tight=True),
                         label=label, help_text=help_text, **kwargs)
        self._sync()

    def _sync(self):
        start, end = self.get_value()
        self.range_text.value = (f"{self.prefix}{_fmt(start, self.decimals)}{self.suffix} – "
                                 f"{self.prefix}{_fmt(end, self.decimals)}{self.suffix}")

    def _on_slide(self, e):
        self._sync()
        self.refresh()
        self.changed(e)

    def _round(self, v):
        return round(v, self.decimals) if self.decimals else int(round(v))

    def get_value(self):
        return self._round(self.slider.start_value), self._round(self.slider.end_value)

    def set_value(self, value):
        start, end = value if value else (self.slider.min, self.slider.max)
        self.slider.start_value = float(start)
        self.slider.end_value = float(end)
        self._sync()


class SingleGridSlider(LabeledWidget):
    """Un solo valor entre `min` y `max`."""

    def __init__(self, label=None, help_text=None, min: float = 0, max: float = 100, divisions: Optional[int] = None,
                 decimals: int = 0, prefix: str = "", suffix: str = "", **kwargs):
        self.decimals = decimals
        self.prefix, self.suffix = prefix, suffix
        self.slider = ft.Slider(min=min, max=max, value=min, divisions=divisions, on_change=self._on_slide)
        self.value_text = ft.Text(size=12)
        super().__init__(ft.Row([ft.Container(self.slider, expand=True), self.value_text]),
                         label=label, help_text=help_text, **kwargs)
        self._sync()

    def _sync(self):
        self.value_text.value = f"{self.prefix}{_fmt(self.get_value(), self.decimals)}{self.suffix}"

    def _on_slide(self, e):
        self._sync()
        self.refresh()
        self.changed(e)

    def get_value(self):
        v = self.slider.value or 0
        return round(v, self.decimals) if self.decimals else int(round(v))

    def set_value(self, value):
        self.slider.value = float(self.slider.min if value in (None, "") else value)
        self._sync()


class NumberKnobInput(LabeledWidget):
    """
    Perilla numérica: anillo de progreso con el valor al centro. Se ajusta
    arrastrando verticalmente, con la rueda del mouse o con los botones −/+.
    """

    def __init__(self, label=None, help_text=None, min: float = 0, max: float = 100, step: float = 1,
                 size: int = 110, color=ft.Colors.PRIMARY, **kwargs):
        self.min, self.max, self.step = min, max, step
        self._value = min
        self.ring = ft.ProgressRing(value=0, width=size, height=size, stroke_width=10, color=color,
                                    bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST)
        self.value_text = ft.Text(size=size // 4, weight=ft.FontWeight.BOLD)
        dial = ft.GestureDetector(
            content=ft.Stack(
                [self.ring, ft.Container(self.value_text, width=size, height=size, alignment=ft.Alignment.CENTER)],
                width=size,
                height=size,
            ),
            on_vertical_drag_update=self._on_drag,
            on_scroll=self._on_scroll,
        )
        body = ft.Row(
            [
                ft.IconButton(icon=ft.Icons.REMOVE, on_click=lambda e: self.nudge(-1)),
                dial,
                ft.IconButton(icon=ft.Icons.ADD, on_click=lambda e: self.nudge(1)),
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            tight=True,
        )
        super().__init__(body, label=label, help_text=help_text, **kwargs)
        self._sync()

    def _clamp(self, v):
        v = min(self.max, max(self.min, v))
        steps = round((v - self.min) / self.step)
        return self.min + steps * self.step

    def _sync(self):
        span = (self.max - self.min) or 1
        self.ring.value = (self._value - self.min) / span
        is_int = float(self.step).is_integer() and float(self.min).is_integer()
        self.value_text.value = str(int(self._value)) if is_int else f"{self._value:g}"

    def nudge(self, steps: int):
        new = self._clamp(self._value + steps * self.step)
        if new != self._value:
            self._value = new
            self._sync()
            self.refresh()
            self.changed()

    def _on_drag(self, e):
        dy = getattr(e, "primary_delta", None)
        if dy is None:
            delta = getattr(e, "local_delta", None)
            dy = getattr(delta, "y", 0) if delta is not None else 0
        if dy:
            self.nudge(-int(math.copysign(1, dy)))

    def _on_scroll(self, e):
        delta = getattr(e, "scroll_delta", None)
        dy = getattr(delta, "y", 0) if delta is not None else 0
        if dy:
            self.nudge(-int(math.copysign(1, dy)))

    def get_value(self):
        is_int = float(self.step).is_integer() and float(self.min).is_integer()
        return int(self._value) if is_int else self._value

    def set_value(self, value):
        self._value = self._clamp(float(self.min if value in (None, "") else value))
        self._sync()
