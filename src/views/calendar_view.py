import flet as ft
from components.shared.calendar import Calendar
from data.manager.calendar_event_manager import CalendarEventManager


def build_view_calendar(page):
    manager = CalendarEventManager()

    try:
        data = manager.get_all_events()
    except Exception as e:
        print("Error fetching calendar events:", e)
        data = []

    def event_to_dict(event):
        return {
            "title": event.title,
            "start_time": event.start_time.isoformat(),
            "end_time": event.end_time.isoformat(),
            "description": event.description,
            "location": event.location,
            "color": event.color,
        }

    def add_event(event):
        return manager.create_event(event_to_dict(event))

    def remove_event(event_id):
        manager.delete_event(event_id)

    def update_event(event):
        return manager.update_event(event.id, event_to_dict(event))

    return ft.Container(
        content=Calendar(data=data, add_event=add_event, remove_event=remove_event, update_event=update_event),
        expand=True,
    )
