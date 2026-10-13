"""
Historial de cambios (equivalente a `djgentelella.history`).

    class CustomerManager(HistoryMixin, BaseManager):
        model = Customer

Cada `create`, `update` y `delete` deja un `LogEntry` con el usuario y los
cambios. El usuario sale de `acting_as(user)` (los `CRUDView` lo hacen solos).
"""

import contextlib
import contextvars
import datetime
import json
from typing import Optional

import flet as ft
from sqlalchemy import Column, DateTime, Integer, String, Text

from fletbatteries import forms
from fletbatteries.auth.session import AuthUser
from fletbatteries.crud.crud_view import CRUDView
from fletbatteries.data.db import Base
from fletbatteries.data.manager import BaseManager, Query
from fletbatteries.i18n import _

ACTIONS = {
    "created": "Created",
    "updated": "Updated",
    "deleted": "Deleted",
    "restored": "Restore",
}

_current_user: contextvars.ContextVar[Optional[AuthUser]] = contextvars.ContextVar("fb_current_user", default=None)


@contextlib.contextmanager
def acting_as(user: Optional[AuthUser]):
    """Define el usuario que se registra en el historial (y en la papelera)."""
    token = _current_user.set(user)
    try:
        yield
    finally:
        _current_user.reset(token)


def current_user() -> Optional[AuthUser]:
    return _current_user.get()


class LogEntry(Base):
    __tablename__ = "fb_log_entries"

    id = Column(Integer, primary_key=True)
    model = Column(String(150), nullable=False, index=True)
    object_id = Column(String(64), nullable=False, index=True)
    object_repr = Column(String(300), nullable=False, default="")
    action = Column(String(20), nullable=False)
    changes = Column(Text, nullable=True)
    user_id = Column(Integer, nullable=True)
    username = Column(String(150), nullable=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.datetime.now, index=True)

    @property
    def changes_dict(self) -> dict:
        return json.loads(self.changes) if self.changes else {}


class LogEntryManager(BaseManager):
    model = LogEntry
    search_fields = ("object_repr", "username", "model")
    default_order = "-id"


def history_for(model_name: str, object_id) -> list[LogEntry]:
    return LogEntryManager().list(Query(size=0, filters={"model": model_name, "object_id": str(object_id)},
                                        order_by="-id")).items


class HistoryMixin:
    """Mezclar antes de `BaseManager`: registra los cambios en `fb_log_entries`."""

    history_exclude: tuple = ("password",)

    @property
    def history_name(self) -> str:
        return self.model.__name__

    def _log(self, s, obj, action: str, changes: Optional[dict] = None):
        user = current_user()
        clean = {k: [_jsonable(a), _jsonable(b)] for k, (a, b) in (changes or {}).items()
                 if k not in self.history_exclude}
        s.add(LogEntry(
            model=self.history_name,
            object_id=str(getattr(obj, self.pk_name)),
            object_repr=self.label_for(obj)[:300],
            action=action,
            changes=json.dumps(clean, ensure_ascii=False) if clean else None,
            user_id=user.id if user else None,
            username=user.username if user else None,
        ))

    def after_save(self, s, obj, created, changes):
        super().after_save(s, obj, created, changes)
        if created or changes:
            self._log(s, obj, "created" if created else "updated", changes)

    def before_delete(self, s, obj):
        super().before_delete(s, obj)
        self._log(s, obj, "deleted")

    def after_restore(self, s, obj):
        parent = getattr(super(), "after_restore", None)
        if parent:
            parent(s, obj)
        self._log(s, obj, "restored")

    def history(self, pk) -> list[LogEntry]:
        return history_for(self.history_name, pk)


def _jsonable(value):
    if isinstance(value, (datetime.date, datetime.datetime, datetime.time)):
        return value.isoformat()
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    return str(value)


def describe_changes(entry) -> str:
    changes = entry.changes_dict if isinstance(entry, LogEntry) else json.loads(entry.get("changes") or "{}")
    if not changes:
        return ""
    lines = []
    for field, (before, after) in changes.items():
        lines.append(f"{field}: {before if before not in (None, '') else '∅'} → {after}")
    return "\n".join(lines)


def history_controls(entries) -> list[ft.Control]:
    """Lista de cambios para mostrar en un modal."""
    if not entries:
        return [ft.Text(_("No records"), italic=True)]
    controls = []
    for e in entries:
        controls.append(ft.ListTile(
            leading=ft.Icon({"created": ft.Icons.ADD_CIRCLE_OUTLINE, "updated": ft.Icons.EDIT_OUTLINED,
                             "deleted": ft.Icons.DELETE_OUTLINE, "restored": ft.Icons.RESTORE}.get(e.action)),
            title=ft.Text(f"{_(ACTIONS.get(e.action, e.action))} · {e.username or '—'} · "
                          f"{e.timestamp.strftime('%d/%m/%Y %H:%M')}"),
            subtitle=ft.Text(describe_changes(e), size=12) if e.changes else None,
        ))
    return controls


# ----------------------------------------------------------------------
# Vista del historial
# ----------------------------------------------------------------------
class LogEntryForm(forms.Form):
    timestamp = forms.DateTimeField(label=_("Date"))
    username = forms.CharField(label=_("User"), required=False)
    action = forms.ChoiceField(label=_("Action"), choices=[(k, _(v)) for k, v in ACTIONS.items()])
    model = forms.CharField(label=_("Model"))
    object_repr = forms.CharField(label=_("Object"))
    changes = forms.CharField(label=_("Changes"), required=False, list_display=False)


class HistoryFilterForm(forms.Form):
    render_type = "inline"
    lookups = {"timestamp": "range"}

    model = forms.CharField(label=_("Model"), required=False)
    action = forms.ChoiceField(label=_("Action"), choices=[(k, _(v)) for k, v in ACTIONS.items()], required=False)
    username = forms.CharField(label=_("User"), required=False)
    timestamp = forms.DateRangeField(label=_("Date"), required=False)


class HistoryCRUD(CRUDView):
    title = _("History")
    name = _("History")
    form_class = LogEntryForm
    filter_form = HistoryFilterForm
    actions = ("detail",)
    route = "/history"
    icon = ft.Icons.HISTORY

    def get_source(self):
        from fletbatteries.data.source import SQLAlchemySource

        return SQLAlchemySource(LogEntryManager())

    def detail_controls(self, item: dict) -> list[ft.Control]:
        controls = super().detail_controls({**item, "changes": None})
        controls.append(ft.Text(describe_changes(item), selectable=True))
        return controls
