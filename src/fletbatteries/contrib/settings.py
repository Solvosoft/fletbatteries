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


# ----------------------------------------------------------------------
# Administración (vista /admin/settings)
# ----------------------------------------------------------------------
def _settings_form():
    from fletbatteries import forms
    from fletbatteries.i18n import _

    class SettingForm(forms.Form):
        title = _("Setting")
        key = forms.CharField(label=_("Key"), max_length=200, help_text="theme.mode, app.name, …")
        value = forms.TextAreaField(label=_("Value (JSON)"), required=False,
                                    help_text=_('JSON value: "text", 10, true, ["a", "b"], {"k": 1}'))

        def initial_from_instance(self, instance):
            initial = super().initial_from_instance(instance)
            raw = initial.get("value")
            if raw:
                try:
                    initial["value"] = json.dumps(json.loads(raw), ensure_ascii=False, indent=2)
                except ValueError:
                    pass
            return initial

        def clean_value(self, value):
            if not value:
                return "null"
            try:
                return json.dumps(json.loads(value), ensure_ascii=False)
            except ValueError:
                raise forms.ValidationError(_("Enter a valid JSON value."))

    return SettingForm


def build_settings_crud():
    """Clase `SettingCRUD` (se crea al usarla para no importar el CRUD al cargar el módulo)."""
    import flet as ft

    from fletbatteries.crud.crud_view import CRUDView
    from fletbatteries.data.source import SQLAlchemySource
    from fletbatteries.i18n import _

    class SettingCRUD(CRUDView):
        title = _("Settings")
        name = _("setting")
        form_class = _settings_form()
        list_fields = ["key", "value"]
        filter_fields = ["key"]
        order_by = "key"
        route = "/admin/settings"
        icon = ft.Icons.TUNE

        def get_source(self):
            return SQLAlchemySource(SettingManager())

        def after_save(self, item, created):
            clear_settings_cache()

        def delete(self, item):
            result = super().delete(item)
            clear_settings_cache()
            return result

    return SettingCRUD


def __getattr__(name):
    if name == "SettingCRUD":
        return build_settings_crud()
    if name == "SettingForm":
        return _settings_form()
    raise AttributeError(name)
