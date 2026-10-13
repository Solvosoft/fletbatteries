"""
Formsets: varios formularios iguales que se agregan y quitan en pantalla
(equivalente a `GTFormSet` + `formset.js`).

    AddressFormSet = formset_factory(AddressForm, extra=1, min_num=1)
    formset = AddressFormSet(initial=[{"street": "Calle 1"}])
    page.add(formset.control)
    if formset.is_valid():
        for data in formset.cleaned_data: ...
"""

from typing import Optional

import flet as ft

from fletbatteries.i18n import _
from fletbatteries.utils import safe_update


class BaseFormSet:
    form = None
    extra = 1
    min_num = 0
    max_num: Optional[int] = None
    can_delete = True
    title: Optional[str] = None
    render_type: Optional[str] = None

    def __init__(self, initial: Optional[list[dict]] = None, title: Optional[str] = None):
        if title:
            self.title = title
        self.forms = []
        self.errors: list[dict] = []
        self.non_form_errors: list[str] = []
        self.cleaned_data: list[dict] = []
        self._list = ft.Column(spacing=10)
        self._error_text = ft.Text("", color=ft.Colors.ERROR, visible=False)
        self.add_button = ft.TextButton(_("Add item"), icon=ft.Icons.ADD, on_click=lambda e: self.add_form())
        initial = list(initial or [])
        count = max(len(initial) + self.extra if not initial else len(initial), self.min_num)
        for i in range(count):
            self.add_form(initial[i] if i < len(initial) else None, refresh=False)
        self._control = None

    def _make_form(self, initial):
        return self.form(initial=initial, prefix=f"form-{len(self.forms)}", render_type=self.render_type)

    def _card(self, form):
        remove = ft.IconButton(
            icon=ft.Icons.DELETE_OUTLINE,
            tooltip=_("Remove"),
            visible=self.can_delete,
            on_click=lambda e, f=form: self.remove_form(f),
        )
        return ft.Container(
            border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
            border_radius=8,
            padding=10,
            content=ft.Row([ft.Container(form.control, expand=True), remove],
                           vertical_alignment=ft.CrossAxisAlignment.START),
        )

    def add_form(self, initial: Optional[dict] = None, refresh: bool = True):
        if self.max_num is not None and len(self.forms) >= self.max_num:
            return None
        form = self._make_form(initial)
        self.forms.append(form)
        self._list.controls.append(self._card(form))
        self._sync_buttons()
        if refresh:
            safe_update(self._list, self.add_button)
        return form

    def remove_form(self, form):
        if len(self.forms) <= self.min_num:
            return
        index = self.forms.index(form)
        self.forms.pop(index)
        self._list.controls.pop(index)
        self._sync_buttons()
        safe_update(self._list, self.add_button)

    def _sync_buttons(self):
        self.add_button.visible = self.max_num is None or len(self.forms) < self.max_num

    @property
    def control(self) -> ft.Control:
        if self._control is None:
            header = [ft.Text(self.title, size=16, weight=ft.FontWeight.BOLD)] if self.title else []
            self._control = ft.Column([*header, self._error_text, self._list, self.add_button], spacing=10, tight=True)
        return self._control

    def is_valid(self) -> bool:
        valid = [form.is_valid() for form in self.forms]
        self.errors = [form.errors for form in self.forms]
        self.cleaned_data = [form.cleaned_data for form in self.forms]
        self.non_form_errors = []
        try:
            self.clean()
        except Exception as e:  # ValidationError
            self.non_form_errors = list(getattr(e, "messages", [str(e)]))
        self._error_text.value = " ".join(self.non_form_errors)
        self._error_text.visible = bool(self.non_form_errors)
        safe_update(self._error_text)
        return all(valid) and not self.non_form_errors

    def clean(self):
        """Validación entre formularios; lanzar `ValidationError` para mostrar un error general."""


def formset_factory(form, extra: int = 1, min_num: int = 0, max_num: Optional[int] = None, can_delete: bool = True,
                    formset=BaseFormSet, **attrs) -> type:
    attrs.update(form=form, extra=extra, min_num=min_num, max_num=max_num, can_delete=can_delete)
    return type(f"{form.__name__}FormSet", (formset,), attrs)
