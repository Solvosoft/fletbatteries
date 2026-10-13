"""
Notificaciones dentro de la app (equivalente a `djgentelella.notification`).

    create_notification(user_id, "Se aprobó su solicitud", level="success", link="/requests/4")

`NotificationBell` es la campana del navbar: muestra cuántas hay sin leer y
abre la lista; se actualiza al navegar y cada `poll_interval` segundos.
"""

import asyncio
import datetime
from typing import Callable, Optional

import flet as ft
from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text

from fletbatteries.auth.session import get_user
from fletbatteries.data.db import Base
from fletbatteries.data.manager import BaseManager, Query
from fletbatteries.i18n import _
from fletbatteries.utils import close_dialog, get_page, safe_update

LEVELS = {
    "info": (ft.Icons.INFO_OUTLINE, ft.Colors.BLUE_600),
    "success": (ft.Icons.CHECK_CIRCLE_OUTLINE, ft.Colors.GREEN_600),
    "warning": (ft.Icons.WARNING_AMBER, ft.Colors.AMBER_800),
    "error": (ft.Icons.ERROR_OUTLINE, ft.Colors.RED_600),
}


class Notification(Base):
    __tablename__ = "fb_notifications"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=True, index=True)  # None = app sin usuarios (sin login)
    message = Column(Text, nullable=False)
    level = Column(String(20), nullable=False, default="info")
    category = Column(String(100), nullable=True)
    link = Column(String(300), nullable=True)
    read = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.now)


class NotificationManager(BaseManager):
    model = Notification
    search_fields = ("message", "category")
    default_order = "-created_at"

    @staticmethod
    def _owner(user_id: Optional[int]) -> dict:
        return {"user_id": user_id} if user_id is not None else {"user_id__isnull": True}

    def for_user(self, user_id: Optional[int], unread_only: bool = False, size: int = 10) -> list:
        filters = self._owner(user_id)
        if unread_only:
            filters["read"] = False
        return self.list(Query(size=size, filters=filters, order_by="-id")).items

    def unread_count(self, user_id: Optional[int]) -> int:
        return self.count(read=False, **self._owner(user_id))

    def mark_read(self, notification_id: int):
        self.update(notification_id, read=True)

    def mark_all_read(self, user_id: Optional[int]):
        for n in self.for_user(user_id, unread_only=True, size=0):
            self.update(n.id, read=True)


def create_notification(user_id: Optional[int], message: str, level: str = "info", link: Optional[str] = None,
                        category: Optional[str] = None) -> Notification:
    if level not in LEVELS:
        raise ValueError(f"Nivel desconocido: {level}")
    return NotificationManager().create(user_id=user_id, message=message, level=level, link=link,
                                        category=category)


class NotificationBell(ft.Container):
    """Campana con contador; al hacer clic muestra las últimas notificaciones."""

    def __init__(self, poll_interval: Optional[float] = 30, manager: Optional[NotificationManager] = None,
                 on_navigate: Optional[Callable[[str], None]] = None, icon_color=ft.Colors.WHITE):
        super().__init__(key="notification_bell")
        self.manager = manager or NotificationManager()
        self.poll_interval = poll_interval
        self.on_navigate = on_navigate
        self.button = ft.IconButton(icon=ft.Icons.NOTIFICATIONS_OUTLINED, icon_color=icon_color,
                                    tooltip=_("Notifications"), on_click=self.open)
        self.badge_text = ft.Text("0", size=10, color=ft.Colors.WHITE)
        self.badge = ft.Container(self.badge_text, bgcolor=ft.Colors.RED_600, border_radius=8,
                                  padding=ft.Padding.symmetric(horizontal=5, vertical=1), right=4, top=4,
                                  visible=False)
        self.content = ft.Stack([self.button, self.badge])
        self.count = 0
        self._task = None

    def _user_id(self):
        page = get_page(self)
        user = get_user(page) if page else None
        return user.id if user else None

    def refresh(self):
        self.count = self.manager.unread_count(self._user_id())
        self.badge_text.value = str(self.count) if self.count < 100 else "99+"
        self.badge.visible = self.count > 0
        safe_update(self)

    def did_mount(self):
        self.refresh()
        if self.poll_interval:
            self._task = self.page.run_task(self._poll)

    def will_unmount(self):
        if self._task:
            self._task.cancel()
            self._task = None

    async def _poll(self):
        while True:
            await asyncio.sleep(self.poll_interval)
            try:
                self.refresh()
            except Exception:
                return

    def _item(self, n: Notification, dialog) -> ft.Control:
        icon, color = LEVELS.get(n.level, LEVELS["info"])

        def click(e):
            self.manager.mark_read(n.id)
            close_dialog(dialog)
            self.refresh()
            if n.link and self.on_navigate:
                self.on_navigate(n.link)

        return ft.ListTile(
            leading=ft.Icon(icon, color=color),
            title=ft.Text(n.message, weight=None if n.read else ft.FontWeight.BOLD),
            subtitle=ft.Text(n.created_at.strftime("%d/%m/%Y %H:%M"), size=11),
            on_click=click,
            key=f"notification-{n.id}",
        )

    def open(self, e=None):
        user_id = self._user_id()
        items = self.manager.for_user(user_id, size=10)
        dialog = ft.AlertDialog(title=ft.Text(_("Notifications")))

        def mark_all(ev):
            self.manager.mark_all_read(user_id)
            close_dialog(dialog)
            self.refresh()

        body = [self._item(n, dialog) for n in items] or [ft.Text(_("No notifications"), italic=True)]
        dialog.content = ft.Container(width=420, content=ft.Column(body, tight=True, scroll=ft.ScrollMode.AUTO))
        dialog.actions = [
            ft.TextButton(_("Mark all as read"), on_click=mark_all, disabled=not items),
            ft.TextButton(_("Close"), on_click=lambda ev: close_dialog(dialog)),
        ]
        self.page.show_dialog(dialog)
