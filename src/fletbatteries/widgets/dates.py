"""Widgets de fecha, hora y rangos (equivalentes a los datetimepicker/daterangepicker de djgentelella)."""

from datetime import date, datetime, time, timedelta
from typing import Optional, Union

import flet as ft
from dateutil.relativedelta import relativedelta

from fletbatteries.widgets.base import Widget

DATE_FORMAT = "%d/%m/%Y"
TIME_FORMAT = "%H:%M"
DATETIME_FORMAT = f"{DATE_FORMAT} {TIME_FORMAT}"
RANGE_SEPARATOR = " - "

DateSpec = Union[date, datetime, str, None]


def resolve_date(spec: DateSpec, is_min: bool, today: Optional[date] = None) -> Optional[date]:
    """
    Convierte un límite en fecha. Acepta una fecha, ISO (`2025-01-31`) o un
    código relativo a hoy: `d7` (días), `m1` (meses), `y1` (años). Para el
    mínimo el código se resta y para el máximo se suma.
    """
    if spec in (None, ""):
        return None
    if isinstance(spec, datetime):
        return spec.date()
    if isinstance(spec, date):
        return spec
    today = today or date.today()
    unit, amount = spec[0].lower(), spec[1:]
    if unit in "dmy" and amount.lstrip("-").isdigit():
        n = int(amount) * (-1 if is_min else 1)
        delta = {"d": timedelta(days=n), "m": relativedelta(months=n), "y": relativedelta(years=n)}[unit]
        return today + delta
    try:
        return date.fromisoformat(spec)
    except ValueError:
        return None


def parse_value(value, fmt: str, kind: type):
    """Convierte texto a date/datetime/time; devuelve el texto si no se puede (lo valida el formulario)."""
    if value in (None, ""):
        return None
    if isinstance(value, kind) and not (kind is date and isinstance(value, datetime)):
        return value
    if kind is date and isinstance(value, datetime):
        return value.date()
    if isinstance(value, str):
        text = value.strip()
        for f in (fmt, "%Y-%m-%d" if kind is date else None, "%Y-%m-%dT%H:%M:%S" if kind is datetime else None):
            if not f:
                continue
            try:
                parsed = datetime.strptime(text, f)
            except ValueError:
                continue
            if kind is date:
                return parsed.date()
            if kind is time:
                return parsed.time()
            return parsed
        if kind is datetime:
            try:
                return datetime.fromisoformat(text)
            except ValueError:
                pass
        return text
    return value


def format_value(value, fmt: str) -> str:
    if value in (None, ""):
        return ""
    if isinstance(value, (date, datetime, time)):
        return value.strftime(fmt)
    return str(value)


class _PickerInput(Widget):
    """TextField editable con un botón que abre el selector nativo."""

    fmt = DATE_FORMAT
    kind: type = date
    icon = ft.Icons.CALENDAR_MONTH

    def __init__(
        self,
        label=None,
        help_text=None,
        fmt: Optional[str] = None,
        min_date: DateSpec = None,
        max_date: DateSpec = None,
        width=None,
        expand=None,
        **kwargs,
    ):
        super().__init__(label=label, help_text=help_text, width=width, expand=expand, **kwargs)
        if fmt:
            self.fmt = fmt
        self.min_date = resolve_date(min_date, is_min=True)
        self.max_date = resolve_date(max_date, is_min=False)
        self.picker_button = ft.IconButton(icon=self.icon, on_click=self.open_picker)
        self.field = ft.TextField(
            label=label,
            helper=help_text,
            hint_text=datetime(2000, 12, 31, 23, 59).strftime(self.fmt),
            suffix=self.picker_button,
            on_change=self.changed,
        )
        self.content = self.field

    def open_picker(self, e=None):
        raise NotImplementedError

    def get_value(self):
        return parse_value(self.field.value, self.fmt, self.kind)

    def set_value(self, value):
        self.field.value = format_value(parse_value(value, self.fmt, self.kind), self.fmt)

    def show_error(self, message):
        self.field.error = message

    def apply_label(self, label):
        self.field.label = label

    def _set_from_picker(self, value):
        self.set_value(value)
        self.refresh()
        self.changed()

    def _date_picker(self, on_change):
        current = self.get_value()
        if isinstance(current, datetime):
            current = current.date()
        if not isinstance(current, date):
            current = None
        kwargs = {}
        if self.min_date:
            kwargs["first_date"] = datetime.combine(self.min_date, time())
        if self.max_date:
            kwargs["last_date"] = datetime.combine(self.max_date, time())
        return ft.DatePicker(
            value=datetime.combine(current, time()) if current else None,
            on_change=on_change,
            **kwargs,
        )


class DateInput(_PickerInput):
    def open_picker(self, e=None):
        def on_change(ev):
            value = ev.control.value
            if value:
                self._set_from_picker(value.date() if isinstance(value, datetime) else value)

        self.app_page.show_dialog(self._date_picker(on_change))


class TimeInput(_PickerInput):
    fmt = TIME_FORMAT
    kind = time
    icon = ft.Icons.ACCESS_TIME

    def open_picker(self, e=None):
        current = self.get_value()

        def on_change(ev):
            if ev.control.value:
                self._set_from_picker(ev.control.value)

        picker = ft.TimePicker(on_change=on_change)
        if isinstance(current, time):
            picker.value = current
        self.app_page.show_dialog(picker)


class DateTimeInput(_PickerInput):
    """Fecha y hora: abre el selector de fecha y luego el de hora."""

    fmt = DATETIME_FORMAT
    kind = datetime

    def open_picker(self, e=None):
        current = self.get_value()
        current_time = current.time() if isinstance(current, datetime) else time(8, 0)

        def on_time(ev, picked_date):
            picked_time = ev.control.value or current_time
            self._set_from_picker(datetime.combine(picked_date, picked_time))

        def on_date(ev):
            value = ev.control.value
            if not value:
                return
            picked_date = value.date() if isinstance(value, datetime) else value
            # Sin hora, el valor queda con la hora actual o las 08:00
            self._set_from_picker(datetime.combine(picked_date, current_time))
            time_picker = ft.TimePicker(value=current_time, on_change=lambda ev2: on_time(ev2, picked_date))
            self.app_page.show_dialog(time_picker)

        self.app_page.show_dialog(self._date_picker(on_date))


class DateRangeInput(_PickerInput):
    """Rango de fechas. El valor es una tupla `(inicio, fin)` o `None`."""

    def get_value(self):
        text = (self.field.value or "").strip()
        if not text:
            return None
        parts = [p.strip() for p in text.split(RANGE_SEPARATOR.strip())]
        if len(parts) != 2:
            return text
        start, end = (parse_value(p, self.fmt, date) for p in parts)
        if not isinstance(start, date) or not isinstance(end, date):
            return text
        return start, end

    def set_value(self, value):
        if not value:
            self.field.value = ""
        elif isinstance(value, (tuple, list)) and len(value) == 2:
            start, end = (parse_value(v, self.fmt, date) for v in value)
            self.field.value = f"{format_value(start, self.fmt)}{RANGE_SEPARATOR}{format_value(end, self.fmt)}"
        else:
            self.field.value = str(value)

    def open_picker(self, e=None):
        current = self.get_value()
        kwargs = {}
        if isinstance(current, tuple):
            kwargs["start_value"] = datetime.combine(current[0], time())
            kwargs["end_value"] = datetime.combine(current[1], time())
        if self.min_date:
            kwargs["first_date"] = datetime.combine(self.min_date, time())
        if self.max_date:
            kwargs["last_date"] = datetime.combine(self.max_date, time())

        def on_change(ev):
            start, end = ev.control.start_value, ev.control.end_value
            if start and end:
                as_date = lambda d: d.date() if isinstance(d, datetime) else d  # noqa: E731
                self._set_from_picker((as_date(start), as_date(end)))

        self.app_page.show_dialog(ft.DateRangePicker(on_change=on_change, **kwargs))


class DateTimeRangeInput(Widget):
    """Rango de fecha y hora: dos `DateTimeInput`. El valor es `(inicio, fin)`."""

    def __init__(self, label=None, help_text=None, start_label=None, end_label=None, **kwargs):
        super().__init__(label=label, help_text=help_text, **kwargs)
        self.start = DateTimeInput(label=start_label or (f"{label} ↦" if label else None), expand=True)
        self.end = DateTimeInput(label=end_label or (f"↤ {label}" if label else None), expand=True)
        self.start.add_change_listener(self.changed)
        self.end.add_change_listener(self.changed)
        self._error_text = ft.Text("", size=11, color=ft.Colors.ERROR, visible=False)
        self.content = ft.Column([ft.Row([self.start, self.end]), self._error_text], spacing=2, tight=True)

    def get_value(self):
        start, end = self.start.get_value(), self.end.get_value()
        if start is None and end is None:
            return None
        return start, end

    def set_value(self, value):
        start, end = value if value else (None, None)
        self.start.set_value(start)
        self.end.set_value(end)

    def show_error(self, message):
        self._error_text.value = message or ""
        self._error_text.visible = bool(message)
