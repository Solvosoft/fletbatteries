import flet as ft

from fletbatteries.data import SQLAlchemySource
from fletbatteries.widgets.calendar import Calendar

from data.manager.calendar_event_manager import CalendarEventManager


def build_view_calendar(page):
    return ft.Container(content=Calendar(source=SQLAlchemySource(CalendarEventManager())), expand=True)
