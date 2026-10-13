import datetime

import pytest

from data.manager.calendar_event_manager import CalendarEventManager, EventManager
from data.manager.product_manager import ProductManager
from data.manager.country_manager import CountryManager
from data.models.calendar_event import Event


def test_product_crud():
    pm = ProductManager()
    created = pm.create_product("P-100", "Producto", 10.5, "ejemplo.jpg")
    assert pm.get_product_by_id(created["id"])["name"] == "Producto"

    with pytest.raises(ValueError):
        pm.create_product("P-100", "Duplicado", 1, "x.jpg")

    updated = pm.update_product(created["id"], "P-100", "Producto 2", 20, "ejemplo.jpg")
    assert updated["name"] == "Producto 2"
    assert pm.delete_product(created["id"]) is True
    assert pm.delete_product(created["id"]) is False


def test_country_create_and_list():
    cm = CountryManager()
    country = cm.create(name="Tierra de Prueba")
    assert any(c.id == country.id for c in cm.get_all())


def test_calendar_event_crud():
    manager = CalendarEventManager()
    start = datetime.datetime(2026, 10, 13, 9, 0)
    created = manager.create_event({
        "title": "Demo",
        "start_time": start.isoformat(),
        "end_time": (start + datetime.timedelta(hours=1)).isoformat(),
        "color": "#ff0000",
    })
    assert created["id"]

    updated = manager.update_event(created["id"], {**created, "title": "Demo 2"})
    assert updated["title"] == "Demo 2"
    assert any(e["title"] == "Demo 2" for e in manager.get_all_events())

    assert manager.delete_event(created["id"]) is True
    assert manager.delete_event(created["id"]) is False


def test_event_from_json_and_week_filter():
    monday = datetime.date(2026, 10, 12)
    week = [monday + datetime.timedelta(days=i) for i in range(7)]
    em = EventManager()
    em.add_event(Event.from_json({"id": 1, "title": "a", "start_time": "2026-10-14T10:00:00", "end_time": "2026-10-14T11:00:00"}))
    em.add_event(Event.from_json({"id": 2, "title": "b", "start_time": "2026-10-20T10:00:00", "end_time": "2026-10-20T11:00:00"}))
    assert [e.title for e in em.get_events_for_week(week)] == ["a"]
    em.remove_event(1)
    assert em.get_events_for_week(week) == []
