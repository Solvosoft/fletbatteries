from datetime import date, datetime

import flet as ft

from fletbatteries.crud import CRUDView
from fletbatteries.data import ListSource

from app_forms import EventForm

# Registros en memoria (se comparten mientras corre la app)
EVENTS = ListSource(
    [
        {"id": i, "name": f"Test {i}", "date": date(2023, 1, i), "datetime": datetime(2023, 1, i, 12, 0)}
        for i in range(1, 7)
    ]
)


class EventCRUD(CRUDView):
    title = "Test"
    name = "evento"
    source = EVENTS
    form_class = EventForm
    mode = "cards"


def build_view_test(page: ft.Page) -> ft.Control:
    return EventCRUD(page).build()
