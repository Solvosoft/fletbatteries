"""
Formulario por pasos (wizard).

    wizard = FormWizard(
        steps=[
            ("Datos", PersonForm),
            ("Dirección", AddressForm),
            ("Empresa", CompanyForm, lambda data: data.get("is_company")),   # paso condicional
        ],
        on_finish=lambda data: save(data),      # data = wizard.cleaned_data (todos los pasos)
    )
    page.add(wizard)

Cada paso valida su formulario antes de avanzar. Al volver atrás se conservan
los valores. Para personalizar, se puede heredar y sobrescribir
`get_form_kwargs(index, data)` (p. ej. valores iniciales que dependen de pasos
anteriores) o `condition(index, data)`.
"""

from typing import Any, Callable, Optional, Sequence

import flet as ft

from fletbatteries.i18n import _
from fletbatteries.utils import safe_update


class FormWizard(ft.Column):
    def __init__(self, steps: Sequence[tuple], on_finish: Optional[Callable[[dict], Any]] = None,
                 on_cancel: Optional[Callable[[], Any]] = None, finish_text: Optional[str] = None,
                 initial: Optional[dict] = None, **kwargs):
        kwargs.setdefault("spacing", 16)
        kwargs.setdefault("tight", True)
        super().__init__(**kwargs)
        if not steps:
            raise ValueError("FormWizard necesita al menos un paso")
        self.steps = [self._normalize(step) for step in steps]
        self.on_finish = on_finish
        self.on_cancel = on_cancel
        self.finish_text = finish_text or _("Finish")
        self.initial = dict(initial or {})
        self.forms: dict[int, Any] = {}
        self.step_data: dict[int, dict] = {}
        self.current = 0
        self.finished = False

        self.indicator = ft.Row(wrap=True, spacing=8, run_spacing=8, key="wizard_steps")
        self.body = ft.Container(key="wizard_body")
        self.back_button = ft.TextButton(_("Back"), icon=ft.Icons.ARROW_BACK, on_click=lambda e: self.back(),
                                         key="wizard_back")
        self.next_button = ft.Button(_("Next"), icon=ft.Icons.ARROW_FORWARD, on_click=lambda e: self.next(),
                                     key="wizard_next")
        buttons = [self.back_button, self.next_button]
        if on_cancel is not None:
            buttons.insert(0, ft.TextButton(_("Cancel"), on_click=lambda e: self.on_cancel(), key="wizard_cancel"))
        self.controls = [self.indicator, ft.Divider(height=1), self.body,
                         ft.Row(buttons, alignment=ft.MainAxisAlignment.END)]
        self._show(0)

    @staticmethod
    def _normalize(step) -> dict:
        if isinstance(step, dict):
            return {"title": step.get("title", ""), "form": step["form"], "condition": step.get("condition")}
        title, form = step[0], step[1]
        condition = step[2] if len(step) > 2 else None
        return {"title": title, "form": form, "condition": condition}

    # ------------------------------------------------------------------
    # Hooks
    # ------------------------------------------------------------------
    @property
    def cleaned_data(self) -> dict:
        """`cleaned_data` de todos los pasos visitados (los posteriores sobrescriben)."""
        result = {}
        for index in sorted(self.step_data):
            if self.is_active(index):
                result.update(self.step_data[index])
        return result

    def get_form_kwargs(self, index: int, data: dict) -> dict:
        return {"initial": self.initial}

    def condition(self, index: int, data: dict) -> bool:
        condition = self.steps[index]["condition"]
        return bool(condition(data)) if condition else True

    def is_active(self, index: int) -> bool:
        before = {}
        for i in range(index):
            before.update(self.step_data.get(i, {}))
        return self.condition(index, before)

    # ------------------------------------------------------------------
    def get_form(self, index: int):
        if index not in self.forms:
            form = self.steps[index]["form"]
            if isinstance(form, type):
                form = form(**self.get_form_kwargs(index, self.cleaned_data))
            self.forms[index] = form
        return self.forms[index]

    @property
    def form(self):
        return self.get_form(self.current)

    def _next_index(self, start: int, step: int) -> Optional[int]:
        index = start + step
        while 0 <= index < len(self.steps):
            if self.is_active(index):
                return index
            index += step
        return None

    def _is_last(self) -> bool:
        return self._next_index(self.current, 1) is None

    def _render_indicator(self):
        chips = []
        number = 0
        for index, step in enumerate(self.steps):
            if index > self.current and not self.is_active(index):
                continue
            if index < self.current and index not in self.step_data:
                continue
            number += 1
            done = index < self.current
            current = index == self.current
            bubble = ft.Container(
                content=ft.Icon(ft.Icons.CHECK, size=14, color=ft.Colors.ON_PRIMARY) if done
                else ft.Text(str(number), size=12,
                             color=ft.Colors.ON_PRIMARY if current else ft.Colors.ON_SURFACE),
                width=24, height=24, border_radius=12, alignment=ft.Alignment.CENTER,
                bgcolor=ft.Colors.PRIMARY if (done or current) else ft.Colors.SURFACE_CONTAINER_HIGHEST,
            )
            chips.append(ft.Row(
                [bubble, ft.Text(step["title"], weight=ft.FontWeight.BOLD if current else None)],
                spacing=6, tight=True, key=f"wizard-step-{index}",
            ))
        self.indicator.controls = chips

    def _show(self, index: int):
        self.current = index
        self.body.content = self.get_form(index).control
        self.back_button.disabled = self._next_index(index, -1) is None
        last = self._is_last()
        self.next_button.content = self.finish_text if last else _("Next")
        self.next_button.icon = ft.Icons.CHECK if last else ft.Icons.ARROW_FORWARD
        self._render_indicator()
        safe_update(self)

    def next(self) -> bool:
        """Valida el paso actual y avanza (o termina). Devuelve False si hay errores."""
        form = self.form
        if not form.is_valid():
            return False
        self.step_data[self.current] = dict(form.cleaned_data)
        following = self._next_index(self.current, 1)
        if following is None:
            self.finished = True
            if self.on_finish:
                self.on_finish(self.cleaned_data)
            return True
        self._show(following)
        return True

    def back(self):
        previous = self._next_index(self.current, -1)
        if previous is not None:
            self._show(previous)

    def reset(self):
        self.forms = {}
        self.step_data = {}
        self.finished = False
        self._show(0)
