"""
Textos de ayuda editables (equivalente a `Help` / `PalleteWidget` de djgentelella).

    HelpButton("customers.list")   # icono "?" que muestra la ayuda guardada con esa llave

Quien tenga el permiso `help.change` puede editar el texto desde el mismo diálogo.
"""

from typing import Optional

import flet as ft
from sqlalchemy import Column, Integer, String, Text

from fletbatteries.auth.session import has_perm
from fletbatteries.data.db import Base
from fletbatteries.data.manager import BaseManager
from fletbatteries.i18n import _
from fletbatteries.utils import close_dialog

EDIT_PERMISSION = "help.change"


class HelpText(Base):
    __tablename__ = "fb_help"

    id = Column(Integer, primary_key=True)
    key = Column(String(200), unique=True, nullable=False)
    title = Column(String(200), nullable=True)
    text = Column(Text, nullable=False, default="")


class HelpManager(BaseManager):
    model = HelpText
    search_fields = ("key", "title", "text")
    unique_fields = ("key",)

    def get_help(self, key: str) -> Optional[HelpText]:
        return self.first(key=key)

    def set_help(self, key: str, text: str, title: Optional[str] = None) -> HelpText:
        obj = self.get_help(key)
        if obj is None:
            return self.create(key=key, text=text, title=title)
        return self.update(obj.id, text=text, title=title if title is not None else obj.title)


class HelpButton(ft.IconButton):
    def __init__(self, help_key: str, title: Optional[str] = None, manager: Optional[HelpManager] = None, **kwargs):
        super().__init__(icon=ft.Icons.HELP_OUTLINE, tooltip=_("Help"), key=f"help-{help_key}", **kwargs)
        self.help_key = help_key
        self.help_title = title
        self.manager = manager or HelpManager()
        self.on_click = self.open

    def open(self, e=None):
        page = self.page
        obj = self.manager.get_help(self.help_key)
        text = obj.text if obj else ""
        title = (obj.title if obj and obj.title else None) or self.help_title or _("Help")
        dialog = ft.AlertDialog(title=ft.Text(title))
        markdown = ft.Markdown(text or _("No help available."), selectable=True)
        editor = ft.TextField(value=text, multiline=True, min_lines=6, max_lines=14, visible=False,
                              key="help_editor")
        save_button = ft.TextButton(_("Save"), visible=False)
        actions = [ft.TextButton(_("Close"), on_click=lambda ev: close_dialog(dialog))]

        if has_perm(page, EDIT_PERMISSION):
            def edit(ev):
                editor.visible, save_button.visible, markdown.visible = True, True, False
                dialog.update()

            def save(ev):
                self.manager.set_help(self.help_key, editor.value or "", title=self.help_title)
                markdown.value = editor.value or _("No help available.")
                editor.visible, save_button.visible, markdown.visible = False, False, True
                dialog.update()

            save_button.on_click = save
            actions = [ft.TextButton(_("Edit help"), on_click=edit), save_button] + actions

        dialog.content = ft.Container(width=480, content=ft.Column([markdown, editor], tight=True,
                                                                   scroll=ft.ScrollMode.AUTO))
        dialog.actions = actions
        page.show_dialog(dialog)
