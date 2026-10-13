import flet as ft

from fletbatteries import forms
from fletbatteries.crud import CRUDView

from data.manager.abc_manager import ABCManager

A = [("1", "A1"), ("2", "A2")]


def b_choices(a):
    a_text = dict(A).get(a, "")
    return [(f"{a}1", f"B1 {a_text}"), (f"{a}2", f"B2 {a_text}")]


def c_choices(b_values):
    return [(f"{b}{n}", f"C{n} ({b})") for b in b_values for n in (1, 2)]


class RelatedForm(forms.Form):
    """Selects encadenados: B depende de A y C depende de B (como `data-related`)."""

    title = "Relaciones ABC"

    a = forms.ChoiceField(label="Select A", choices=A)
    b = forms.MultipleChoiceField(label="Select B", depends_on="a", related_choices=b_choices)
    c = forms.ChoiceField(label="Select C", depends_on="b", related_choices=c_choices)

    def save_data(self):
        data = self.cleaned_data
        a, b, c = (self.fields[n].display(data[n]) for n in ("a", "b", "c"))
        return {"name": f"A:{a} B:{b.replace(', ', ',')} C:{c}"}


class ABCCRUD(CRUDView):
    title = "ABC Groups"
    name = "relación"
    manager = ABCManager()
    form_class = RelatedForm
    list_fields = ["id", "name"]
    actions = ("create", "delete")


def build_view_autocompletes_related(page: ft.Page) -> ft.Control:
    return ABCCRUD(page).build()
