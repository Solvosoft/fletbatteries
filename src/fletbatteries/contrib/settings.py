"""
Configuración guardada en la base de datos (equivalente a `GentelellaSettings`).

    set_setting("theme.mode", "dark")
    get_setting("theme.mode", default="light")

Los valores se guardan como JSON y se cachean en memoria.
"""

import json
from typing import Any

from sqlalchemy import Column, Integer, String, Text

from fletbatteries.data.db import Base
from fletbatteries.data.manager import BaseManager


class Setting(Base):
    __tablename__ = "fb_settings"

    id = Column(Integer, primary_key=True)
    key = Column(String(200), unique=True, nullable=False)
    value = Column(Text, nullable=True)


class SettingManager(BaseManager):
    model = Setting
    search_fields = ("key",)
    unique_fields = ("key",)


_cache: dict[str, Any] = {}
_MISSING = object()


def get_setting(key: str, default: Any = None, manager: SettingManager = None) -> Any:
    if key in _cache:
        return _cache[key]
    obj = (manager or SettingManager()).first(key=key)
    if obj is None:
        return default
    value = json.loads(obj.value) if obj.value is not None else None
    _cache[key] = value
    return value


def set_setting(key: str, value: Any, manager: SettingManager = None):
    manager = manager or SettingManager()
    encoded = json.dumps(value)
    obj = manager.first(key=key)
    if obj is None:
        manager.create(key=key, value=encoded)
    else:
        manager.update(obj.id, value=encoded)
    _cache[key] = value


def clear_settings_cache():
    _cache.clear()
