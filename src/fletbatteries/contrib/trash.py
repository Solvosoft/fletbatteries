"""
Papelera / borrado lógico (equivalente a `DeletedWithTrash` de djgentelella).

    class Note(SoftDeleteMixin, Base): ...
    class NoteManager(TrashMixin, BaseManager):
        model = Note

    register_trash(NoteManager(), "Notas")

`delete()` marca `deleted_at` en vez de borrar; las consultas normales ignoran
lo eliminado. `TrashView` lista lo eliminado y permite restaurar o borrar
definitivamente.
"""

import datetime
from typing import Optional

import flet as ft
import sqlalchemy as sa
from sqlalchemy import Column, DateTime, String

from fletbatteries.data.manager import BaseManager, Page, Query
from fletbatteries.data.source import SQLAlchemySource
from fletbatteries.i18n import _
from fletbatteries.utils import notify, safe_update
from fletbatteries.widgets.datatable import Column as TableColumn
from fletbatteries.widgets.datatable import DataTable, RowAction
from fletbatteries.widgets.modals import CrudModal


class SoftDeleteMixin:
    """Columnas de borrado lógico para un modelo."""

    deleted_at = Column(DateTime, nullable=True, index=True)
    deleted_by = Column(String(150), nullable=True)


class TrashMixin:
    """Mezclar antes de `BaseManager` en managers de modelos con `SoftDeleteMixin`."""

    def base_query(self):
        return super().base_query().where(self.model.deleted_at.is_(None))

    def trashed_query(self):
        return sa.select(self.model).where(self.model.deleted_at.is_not(None))

    def perform_delete(self, s, obj):
        from fletbatteries.contrib.history import current_user

        user = current_user()
        obj.deleted_at = datetime.datetime.now()
        obj.deleted_by = user.username if user else None

    def list_deleted(self, query: Optional[Query] = None) -> Page:
        query = query or Query()
        with self.session() as s:
            stmt = self.apply_search(self.apply_filters(self.trashed_query(), query.filters), query.search)
            total = s.scalar(sa.select(sa.func.count()).select_from(stmt.order_by(None).subquery()))
            stmt = self.apply_order(stmt, query.order_by or "-deleted_at")
            if query.size:
                stmt = stmt.offset(query.offset).limit(query.size)
            items = list(s.scalars(stmt).unique())
        return Page(items=items, total=total or 0, page=query.page, size=query.size)

    def _get_trashed(self, s, pk):
        return s.scalars(self.trashed_query().where(self._column(self.pk_name) == pk)).unique().first()

    def restore(self, pk) -> bool:
        with self.session() as s:
            obj = self._get_trashed(s, pk)
            if obj is None:
                return False
            obj.deleted_at = None
            obj.deleted_by = None
            s.flush()
            if hasattr(self, "after_restore"):
                self.after_restore(s, obj)
            return True

    def hard_delete(self, pk) -> bool:
        with self.session() as s:
            obj = self._get_trashed(s, pk)
            if obj is None:
                return False
            s.delete(obj)
            return True


_registry: dict[str, BaseManager] = {}


def register_trash(manager: BaseManager, label: Optional[str] = None):
    if not isinstance(manager, TrashMixin):
        raise TypeError(f"{type(manager).__name__} no usa TrashMixin")
    _registry[label or manager.model.__name__] = manager


def trash_registry() -> dict[str, BaseManager]:
    return dict(_registry)


class TrashSource(SQLAlchemySource):
    """Fuente con los registros eliminados de un manager con `TrashMixin`."""

    def list(self, query: Query) -> Page:
        page = self.manager.list_deleted(query)
        return Page(items=[self._item(o) for o in page.items], total=page.total, page=page.page, size=page.size)

    def _item(self, obj) -> dict:
        data = self.to_dict(obj)
        data["__label__"] = self.manager.label_for(obj)
        return data

    def restore(self, pk) -> bool:
        return self.manager.restore(pk)

    def delete(self, pk) -> bool:
        return self.manager.hard_delete(pk)


def build_trash_view(page: ft.Page) -> ft.Control:
    """Vista de la papelera para todos los managers registrados con `register_trash`."""
    from fletbatteries.auth.session import get_user
    from fletbatteries.contrib.history import acting_as

    registry = trash_registry()
    if not registry:
        return ft.Text(_("No records"))
    modal = CrudModal(page)
    holder = ft.Container(expand=True)
    state = {}

    def restore(item):
        with acting_as(get_user(page)):
            ok = state["source"].restore(item["id"])
        notify(page, _("Restored successfully") if ok else _("Sorry, an error occurred"), ok)
        state["table"].reload()

    def delete(item):
        def accept():
            ok = state["source"].delete(item["id"])
            state["table"].reload()
            return ok

        modal.open("delete", _("Delete permanently"), [ft.Text(_("Are you sure you want to delete this record?")),
                                                       ft.Text(item["__label__"], weight=ft.FontWeight.BOLD)],
                   on_accept=accept, success_text=_("Deleted successfully"), accept_text=_("Delete permanently"))

    def show(label):
        source = state["source"] = TrashSource(registry[label])
        state["table"] = DataTable(
            source,
            columns=[
                TableColumn("__label__", label=_("Object"), sortable=False),
                TableColumn("deleted_at", label=_("Deleted"),
                            render=lambda v, i: v.strftime("%d/%m/%Y %H:%M") if v else ""),
                TableColumn("deleted_by", label=_("User")),
            ],
            actions=[
                RowAction(ft.Icons.RESTORE, _("Restore"), restore, name="restore"),
                RowAction(ft.Icons.DELETE_FOREVER, _("Delete permanently"), delete, name="purge",
                          color=ft.Colors.ERROR),
            ],
        )
        holder.content = state["table"]
        safe_update(holder)

    selector = ft.Dropdown(
        key="trash_model",
        label=_("Model"),
        width=260,
        value=next(iter(registry)),
        options=[ft.DropdownOption(label) for label in registry],
        on_select=lambda e: show(e.control.value),
    )
    show(selector.value)
    return ft.Container(
        expand=True,
        padding=10,
        content=ft.Column([ft.Text(_("Trash"), size=20), ft.Divider(), selector, holder], expand=True),
    )
