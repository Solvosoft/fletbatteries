from data.models import calendar_event
from data.manager.db_manager import DatabaseManager


class EventManager:
    """Eventos en memoria de la semana mostrada por el calendario."""

    def __init__(self):
        self.events: list[calendar_event.Event] = []

    def add_event(self, event: calendar_event.Event):
        self.events.append(event)

    def remove_event(self, event_id):
        self.events = [ev for ev in self.events if ev.id != event_id]

    def get_events_for_week(self, week_days):
        return [ev for ev in self.events if ev.start_time.date() in week_days]

    def get_events_for_day(self, day):
        return [ev for ev in self.events if ev.start_time.date() == day]


class CalendarEventManager:
    """CRUD de eventos del calendario en la base de datos."""

    def __init__(self):
        self.dbm = DatabaseManager()

    def get_all_events(self):
        db = self.dbm.get_session()
        try:
            events = db.query(calendar_event.Event).order_by(calendar_event.Event.start_time).all()
            return [ev.to_dict() for ev in events]
        finally:
            self.dbm.close_session(db)

    def create_event(self, data: dict):
        db = self.dbm.get_session()
        try:
            event = calendar_event.Event.from_json({**data, "id": None})
            db.add(event)
            db.commit()
            db.refresh(event)
            return event.to_dict()
        finally:
            self.dbm.close_session(db)

    def update_event(self, event_id: int, data: dict):
        db = self.dbm.get_session()
        try:
            event = db.query(calendar_event.Event).filter(calendar_event.Event.id == event_id).first()
            if not event:
                raise ValueError("Evento no encontrado")
            updated = calendar_event.Event.from_json({**data, "id": event_id})
            for attr in ("title", "start_time", "end_time", "color", "description", "location"):
                setattr(event, attr, getattr(updated, attr))
            db.commit()
            db.refresh(event)
            return event.to_dict()
        finally:
            self.dbm.close_session(db)

    def delete_event(self, event_id: int):
        db = self.dbm.get_session()
        try:
            event = db.query(calendar_event.Event).filter(calendar_event.Event.id == event_id).first()
            if not event:
                return False
            db.delete(event)
            db.commit()
            return True
        finally:
            self.dbm.close_session(db)
