
from data.models import calendar_event

class EventManager:
    def __init__(self):
        self.events: list[calendar_event.Event] = []

    def add_event(self, event: calendar_event.Event):
        self.events.append(event)

    def remove_event(self, event_id: str):
        self.events = [ev for ev in self.events if ev.id != event_id]

    def get_events_for_week(self, week_days):
        return [ev for ev in self.events if ev.date in week_days]

    def get_events_for_day(self, day):
        return [ev for ev in self.events if ev.date == day]
