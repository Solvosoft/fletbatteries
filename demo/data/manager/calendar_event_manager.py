from fletbatteries.data import BaseManager
from fletbatteries.widgets.calendar import CalendarEvent, EventStore

from data.models.calendar_event import Event

# Compatibilidad: el almacén en memoria del calendario vive en fletbatteries
EventManager = EventStore


class CalendarEventManager(BaseManager):
    """CRUD de eventos del calendario en la base de datos."""

    model = Event
    default_order = "start_time"

    def to_dict(self, obj) -> dict:
        return obj.to_dict()

    def get_all_events(self) -> list[dict]:
        return [ev.to_dict() for ev in self.get_all()]

    def create_event(self, data: dict) -> dict:
        event = CalendarEvent.from_json({**data, "id": None})
        fields = {k: v for k, v in dataclass_dict(event).items() if k != "id"}
        return self.create(**fields).to_dict()

    def update_event(self, event_id: int, data: dict) -> dict:
        event = CalendarEvent.from_json({**data, "id": event_id})
        fields = {k: v for k, v in dataclass_dict(event).items() if k != "id"}
        return self.update(event_id, **fields).to_dict()

    def delete_event(self, event_id: int) -> bool:
        return self.delete(event_id)


def dataclass_dict(event: CalendarEvent) -> dict:
    import dataclasses

    return dataclasses.asdict(event)
