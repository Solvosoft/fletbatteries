"""Validadores, from_text/validate_data, ModelForm con relaciones, fieldsets, wizard e i18n."""

import datetime

import flet as ft
import pytest

from fletbatteries import forms
from fletbatteries.forms import validators as v
from fletbatteries.i18n import _, get_default_language, get_format, get_language, ngettext, set_default_language

from tests_lib.models import Item


def test_new_validators():
    v.SlugValidator()("mi-slug_1")
    v.IPAddressValidator()("192.168.0.1")
    v.IPAddressValidator()("::1")
    v.PhoneValidator()("+506 8888-1234")
    v.ProhibitNullCharactersValidator()("hola")
    for validator, value in [(v.SlugValidator(), "con espacio"), (v.IPAddressValidator("ipv4"), "::1"),
                             (v.IPAddressValidator(), "999.1.1.1"), (v.PhoneValidator(), "12"),
                             (v.PhoneValidator(), "abc"), (v.ProhibitNullCharactersValidator(), "a\x00b")]:
        with pytest.raises(v.ValidationError):
            validator(value)

    class File:
        size = 2048

    with pytest.raises(v.ValidationError) as info:
        v.MaxFileSizeValidator(1024)(File())
    assert "1.0 KB" in info.value.messages[0]
    v.MaxFileSizeValidator(4096)(File())


def test_password_validation():
    from fletbatteries.auth.password_validation import (
        MinimumLengthValidator,
        password_help_texts,
        validate_password,
    )

    validate_password("Un4-clave-larga")
    for bad in ("corta", "12345678901", "password123"):
        with pytest.raises(v.ValidationError):
            validate_password(bad)
    with pytest.raises(v.ValidationError):
        validate_password("ana.perez.2024", user={"username": "anaperez", "email": "ana.perez@x.com"})
    validate_password("1234", validators=[MinimumLengthValidator(4)])
    assert password_help_texts()


class OrderForm(forms.Form):
    kind = forms.ChoiceField(choices=[("a", "Tipo A"), ("b", "Tipo B")])
    tags = forms.MultipleChoiceField(choices=[("x", "Equis"), ("y", "Ye")], required=False)
    date = forms.DateField()
    amount = forms.DecimalField(decimal_places=2)
    paid = forms.BooleanField()
    labels = forms.TagsField(required=False)

    def clean(self):
        if self.cleaned_data.get("amount") is not None and self.cleaned_data["amount"] < 0:
            self.add_error("amount", "negativo")
        return self.cleaned_data


def test_validate_data_from_text_without_widgets():
    form = OrderForm()
    cleaned, errors = form.validate_data(
        {"kind": "tipo b", "tags": "Equis; y", "date": "31/12/2024", "amount": "10,5", "paid": "sí",
         "labels": "uno, dos"}, from_text=True)
    assert errors == {}
    assert cleaned == {"kind": "b", "tags": ["x", "y"], "date": datetime.date(2024, 12, 31),
                       "amount": __import__("decimal").Decimal("10.50"), "paid": True, "labels": ["uno", "dos"]}
    assert form._widgets is None  # no creó widgets
    cleaned, errors = form.validate_data({"kind": "c", "date": "x", "amount": "-1"}, from_text=True)
    assert set(errors) == {"kind", "date", "amount"}


def test_model_form_maps_relations(db):
    from fletbatteries.forms.fields import ModelChoiceField, ModelMultipleChoiceField

    from tests_lib.models import CategoryManager

    class ItemForm(forms.ModelForm):
        class Meta:
            model = Item
            fields = ["name", "category_id", "tags"]

    form = ItemForm()
    assert isinstance(form.fields["category_id"], ModelChoiceField)
    assert form.fields["category_id"].label == "Category"
    assert isinstance(form.fields["tags"], ModelMultipleChoiceField)
    assert form.fields["name"].max_length == 50
    cat = CategoryManager().create(name="Libros")
    cleaned, errors = form.validate_data({"name": "x", "category_id": "Libros", "tags": ""}, from_text=True)
    assert errors == {} and cleaned["category_id"] == cat.id
    # "__all__" no incluye relaciones (solo columnas)
    class AllForm(forms.ModelForm):
        class Meta:
            model = Item
            fields = "__all__"

    assert "tags" not in AllForm.base_fields and "category_id" in AllForm.base_fields


class ProfileForm(forms.Form):
    fieldsets_style = "tabs"
    fieldsets = [
        ("Personal", {"fields": ["name", "email"], "description": "Datos"}),
        ("Trabajo", {"fields": ["company"], "grid": [[["company"], ["role"]]]}),
    ]
    name = forms.CharField()
    email = forms.EmailField()
    company = forms.CharField()
    role = forms.CharField(required=False)  # sin grupo: va al último


@pytest.mark.parametrize("style", ["tabs", "sections", "collapsible"])
def test_fieldsets_render_and_mark_errors(style):
    form = type("F", (ProfileForm,), {"fieldsets_style": style})()
    control = form.control
    assert control is not None
    groups = form.fieldset_groups()
    assert [g[2] for g in groups] == [["name", "email"], ["company", "role"]]
    form["name"].value = "Ana"
    form["email"].value = "ana@x.com"
    assert not form.is_valid()  # falta company (segundo grupo)
    parts = form._fieldset_parts
    assert not parts[0]["error_icon"].visible and parts[1]["error_icon"].visible
    if style == "tabs":
        assert form._tabs.selected_index == 1
        assert parts[1]["container"].visible and not parts[0]["container"].visible
    if style == "collapsible":
        assert parts[1]["tile"].expanded


def test_wizard_steps_condition_and_finish():
    class A(forms.Form):
        name = forms.CharField()
        company = forms.BooleanField()

    class B(forms.Form):
        city = forms.CharField()

    class C(forms.Form):
        tax_id = forms.CharField()

    done = {}
    wizard = forms.FormWizard([("A", A), ("Empresa", C, lambda d: d.get("company")), ("B", B)],
                              on_finish=lambda data: done.update(data))
    assert wizard.current == 0 and wizard.back_button.disabled
    assert not wizard.next()  # nombre obligatorio
    wizard.form["name"].value = "Ana"
    assert wizard.next() and wizard.current == 2  # salta "Empresa"
    assert wizard.next_button.content == _("Finish")
    wizard.back()
    assert wizard.current == 0 and wizard.form["name"].value == "Ana"  # conserva el valor
    wizard.form["company"].value = True
    wizard.next()
    assert wizard.current == 1
    wizard.form["tax_id"].value = "3-101"
    wizard.next()
    wizard.form["city"].value = "San José"
    assert wizard.next() and wizard.finished
    assert done == {"name": "Ana", "company": True, "tax_id": "3-101", "city": "San José"}


def test_ngettext_and_formats():
    assert ngettext("{n} record deleted.", "{n} records deleted.", 1) == "1 registro eliminado."
    assert ngettext("{n} record deleted.", "{n} records deleted.", 3) == "3 registros eliminados."
    assert get_format("date") == "%d/%m/%Y"
    assert get_format("date", "en") == "%m/%d/%Y"
    set_default_language("en")
    try:
        field = forms.DateField()
        assert field.display(datetime.date(2024, 12, 31)) == "12/31/2024"
        assert field.clean("12/31/2024") == datetime.date(2024, 12, 31)
    finally:
        set_default_language("es")
    assert forms.DateField().display(datetime.date(2024, 12, 31)) == "31/12/2024"


async def test_language_is_per_session(db):
    from fletbatteries.app import FletBatteriesApp

    from tests.harness import AppHarness

    app = FletBatteriesApp(login_required=False, languages=[("es", "Español"), ("en", "English")])
    app.add_view("/", lambda page: ft.Text(_("Save"), key="saved"), title="Inicio")
    first = await AppHarness(app.main).start()
    second = await AppHarness(app.main).start()
    try:
        assert first.find_one(key="saved").value == "Guardar"
        await first.click(first.find_one(key="language-en"))
        assert get_language(first.page) == "en" and get_language(second.page) == "es"
        assert first.find_one(key="saved").value == "Save"
        await second.goto("/")
        assert second.find_one(key="saved").value == "Guardar"
        first.assert_no_errors()
        second.assert_no_errors()
    finally:
        await first.stop()
        await second.stop()
    # El idioma por defecto (el de las sesiones nuevas) no cambió
    assert get_default_language() == "es"
