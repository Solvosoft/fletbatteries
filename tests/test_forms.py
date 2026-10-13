"""Pruebas unitarias de `fletbatteries.forms` y de los widgets (sin página)."""

import json
from datetime import date, datetime, time, timedelta
from decimal import Decimal

import flet as ft
import pytest
import sqlalchemy as sa
from sqlalchemy.orm import declarative_base

from fletbatteries import forms
from fletbatteries import widgets as w
from fletbatteries.i18n import _, get_language, set_language
from fletbatteries.widgets.dates import resolve_date
from fletbatteries.widgets.inputs import apply_mask


# ----------------------------------------------------------------------
# Fields
# ----------------------------------------------------------------------
def test_char_field_required_and_length():
    f = forms.CharField(max_length=5, min_length=2)
    with pytest.raises(forms.ValidationError) as e:
        f.clean("")
    assert e.value.messages == ["Este campo es obligatorio."]
    with pytest.raises(forms.ValidationError) as e:
        f.clean("abcdefg")
    assert "como máximo 5" in e.value.messages[0]
    with pytest.raises(forms.ValidationError):
        f.clean("a")
    assert f.clean("  abc ") == "abc"
    assert forms.CharField(required=False).clean("") == ""


def test_numeric_fields():
    assert forms.IntegerField().clean("42") == 42
    with pytest.raises(forms.ValidationError, match="número entero"):
        forms.IntegerField().clean("4.5")
    with pytest.raises(forms.ValidationError, match="menor o igual que 10"):
        forms.IntegerField(max_value=10).clean("11")
    assert forms.IntegerField(required=False).clean("") is None
    assert forms.FloatField().clean("3,5") == 3.5
    assert forms.DecimalField(decimal_places=2).clean("10.456") == Decimal("10.46")
    with pytest.raises(forms.ValidationError, match="Ingrese un número"):
        forms.DecimalField().clean("abc")


def test_email_url_fields():
    assert forms.EmailField().clean("ana@example.com") == "ana@example.com"
    with pytest.raises(forms.ValidationError, match="correo"):
        forms.EmailField().clean("ana@")
    assert forms.URLField().clean("https://flet.dev") == "https://flet.dev"
    with pytest.raises(forms.ValidationError, match="URL"):
        forms.URLField().clean("flet.dev")


def test_boolean_fields():
    assert forms.BooleanField().clean(False) is False
    with pytest.raises(forms.ValidationError):
        forms.BooleanField(required=True).clean(False)
    assert forms.NullBooleanField(required=False).clean(None) is None
    assert forms.NullBooleanField().clean(True) is True
    assert forms.BooleanField().display(True) == "Sí"


def test_date_fields():
    f = forms.DateField()
    assert f.clean("31/12/2024") == date(2024, 12, 31)
    assert f.clean("2024-12-31") == date(2024, 12, 31)
    assert f.clean(datetime(2024, 1, 2, 10)) == date(2024, 1, 2)
    with pytest.raises(forms.ValidationError, match="fecha válida"):
        f.clean("32/13/2024")
    assert forms.DateTimeField().clean("01/02/2024 13:30") == datetime(2024, 2, 1, 13, 30)
    assert forms.TimeField().clean("08:15") == time(8, 15)
    assert f.display(date(2024, 5, 1)) == "01/05/2024"


def test_date_limits_and_relative_codes():
    today = date.today()
    assert resolve_date("d7", is_min=True) == today - timedelta(days=7)
    assert resolve_date("d7", is_min=False) == today + timedelta(days=7)
    assert resolve_date("2025-01-31", is_min=True) == date(2025, 1, 31)
    assert resolve_date("", is_min=True) is None
    f = forms.DateField(max_date="d0")
    with pytest.raises(forms.ValidationError, match="igual o anterior"):
        f.clean(today + timedelta(days=1))
    f = forms.DateField(min_date=date(2020, 1, 1))
    with pytest.raises(forms.ValidationError, match="igual o posterior"):
        f.clean(date(2019, 12, 31))


def test_date_range_field():
    f = forms.DateRangeField()
    assert f.clean(("01/01/2024", "05/01/2024")) == (date(2024, 1, 1), date(2024, 1, 5))
    with pytest.raises(forms.ValidationError, match="anterior a la final"):
        f.clean((date(2024, 2, 1), date(2024, 1, 1)))
    with pytest.raises(forms.ValidationError, match="rango"):
        f.clean("texto")


def test_choice_fields():
    f = forms.ChoiceField(choices=[(1, "Uno"), (2, "Dos")], coerce=int)
    assert f.clean("2") == 2
    with pytest.raises(forms.ValidationError, match="opción válida"):
        f.clean("3")
    assert f.display(1) == "Uno"
    m = forms.MultipleChoiceField(choices={"a": "A", "b": "B"})
    assert m.clean(["a", "b"]) == ["a", "b"]
    with pytest.raises(forms.ValidationError):
        m.clean(["z"])
    assert m.display(["a", "b"]) == "A, B"
    # choices como callable (se evalúan al usar el campo)
    lazy = forms.ChoiceField(choices=lambda: [("x", "X")])
    assert lazy.clean("x") == "x"


def test_tree_tags_color_masked_fields():
    nodes = [{"id": "a", "text": "A", "children": [{"id": "a1", "text": "A1"}]}]
    assert forms.TreeChoiceField(nodes=nodes).clean("a1") == "a1"
    with pytest.raises(forms.ValidationError):
        forms.TreeChoiceField(nodes=nodes).clean("zz")
    assert forms.TreeChoiceField(nodes=nodes, multiple=True).display(["a", "a1"]) == "A, A1"

    assert forms.TagsField().clean("x, y") == ["x", "y"]
    with pytest.raises(forms.ValidationError, match="correo"):
        forms.TagsField(emails=True).clean(["nope"])

    assert forms.ColorField().clean("#00ff00") == "#00FF00"
    with pytest.raises(forms.ValidationError, match="color"):
        forms.ColorField().clean("verde")

    phone = forms.MaskedField(mask="9999-9999")
    assert phone.clean("8888-1234") == "8888-1234"
    with pytest.raises(forms.ValidationError, match="formato"):
        phone.clean("8888-12")


def test_file_field(tmp_path):
    f = forms.FileField(allowed_extensions=["txt"], upload_to=tmp_path / "uploads")
    upload = w.UploadedFile(name="nota.txt", content=b"hola")
    assert f.clean(upload) is upload
    assert f.save_file(upload) == "nota.txt"
    assert (tmp_path / "uploads" / "nota.txt").read_bytes() == b"hola"
    assert upload.md5() == "4d186321c1a7f0f354b297e8914ab240"
    with pytest.raises(forms.ValidationError, match="Tipo de archivo"):
        f.clean(w.UploadedFile(name="foto.exe", content=b""))


def test_apply_mask():
    assert apply_mask("9-9999-9999", "112345678") == "1-1234-5678"
    assert apply_mask("9999-9999", "88a88") == "8888"
    assert apply_mask("(99) 9999-9999", "50688881234") == "(50) 6888-8123"
    assert apply_mask("aaa-999", "abc123") == "abc-123"
    assert apply_mask("aaa-999", "ab1c23") == "abc-23"  # el 1 no es letra: se descarta


# ----------------------------------------------------------------------
# Form
# ----------------------------------------------------------------------
class SignupForm(forms.Form):
    username = forms.CharField(max_length=10)
    email = forms.EmailField(required=False)
    password = forms.PasswordField()
    password2 = forms.PasswordField(label="Confirmación")
    age = forms.IntegerField(required=False, initial=18)

    def clean_username(self, value):
        if value == "admin":
            raise forms.ValidationError("Nombre reservado")
        return value.lower()

    def clean(self):
        if self.cleaned_data.get("password") != self.cleaned_data.get("password2"):
            raise forms.ValidationError("Las contraseñas no coinciden.")
        return self.cleaned_data


def test_form_declares_fields_in_order():
    assert list(SignupForm.base_fields) == ["username", "email", "password", "password2", "age"]
    form = SignupForm()
    assert form.fields["username"].label == "Username"
    assert form.fields["password2"].label == "Confirmación"
    # Cada instancia tiene sus propios campos
    form.fields["username"].label = "Otro"
    assert SignupForm().fields["username"].label == "Username"


def test_form_validation_flow():
    form = SignupForm()
    assert form["age"].value == "18"  # inicial
    assert not form.is_valid()
    assert set(form.errors) == {"username", "password", "password2"}
    assert form["username"].error == "Este campo es obligatorio."

    form["username"].value = "Ana"
    form["password"].value = "x"
    form["password2"].value = "y"
    assert not form.is_valid()
    assert form.non_field_errors() == ["Las contraseñas no coinciden."]
    assert form["username"].error is None

    form["password2"].value = "x"
    assert form.is_valid()
    assert form.cleaned_data == {"username": "ana", "email": "", "password": "x", "password2": "x", "age": 18}

    form["username"].value = "admin"
    assert not form.is_valid()
    assert form.errors["username"] == ["Nombre reservado"]


def test_form_initial_instance_and_reset():
    class Obj:
        username = "luis"
        email = "luis@example.com"

    form = SignupForm(instance=Obj())
    assert form["username"].value == "luis"
    assert form["email"].value == "luis@example.com"
    form["username"].value = "otro"
    form.reset()
    assert form["username"].value == "luis"
    form.clear()
    assert form["username"].value == "" and form.instance is None
    assert form["age"].value == "18"  # el inicial del campo se conserva
    form.set_initial({"username": "nuevo"})
    assert form.data["username"] == "nuevo"


def test_form_inheritance_and_field_removal():
    class Base(forms.Form):
        a = forms.CharField()
        b = forms.CharField()

    class Child(Base):
        b = None
        c = forms.IntegerField()

    assert list(Child.base_fields) == ["a", "c"]


@pytest.mark.parametrize("render_type", ["plain", "horizontal", "inline", "grid"])
def test_form_render_types(render_type):
    class F(forms.Form):
        grid_representation = [[["a"], ["b"]], [["extra"]]]
        a = forms.CharField(label="Campo A")
        b = forms.CharField(label="Campo B")
        c = forms.CharField(label="Campo C")

        def extra(self):
            return ft.Text("bloque extra")

    form = F(render_type=render_type)
    control = form.control
    assert isinstance(control, ft.Column)
    if render_type == "grid":
        assert isinstance(control.controls[1].controls[0], ft.ResponsiveRow)
        # Los campos que no están en la grilla se agregan al final
        assert form["c"] in control.controls[1].controls[-1].controls
    if render_type == "horizontal":
        assert form["a"].label is None
    if render_type == "inline":
        assert form["a"].width == F.inline_width


def test_form_invalid_render_type():
    with pytest.raises(ValueError):
        SignupForm(render_type="otro")


def test_form_from_json():
    customer = json.loads("""{
        "name": "CustomerForm", "title": "Registro de Clientes",
        "inputs": [
            {"name": "id", "type": "IntergerField", "label": "ID", "required": false, "visible_form": false},
            {"name": "name", "type": "CharField", "label": "Nombre", "required": true, "max_length": 50,
             "filter": true},
            {"name": "email", "type": "EmailField", "label": "Correo", "required": true},
            {"name": "birth", "type": "DateField", "label": "Nacimiento", "required": false, "min_date": "y100"}
        ]
    }""")
    Form = forms.Form.from_json(customer)
    form = Form()
    assert form.title == customer["title"]
    assert set(form.fields) == {i["name"] for i in customer["inputs"]}
    assert form["id"].visible is False and form.fields["name"].filter
    assert form.fields["name"].max_length == 50 and not form.fields["birth"].required
    with pytest.raises(ValueError, match="no soportado"):
        forms.Form.from_json({"inputs": [{"name": "x", "type": "Nope"}]})


def test_yes_no_input_toggles_related_fields():
    class F(forms.Form):
        remote = forms.BooleanField(widget=w.YesNoInput, widget_kwargs={"show_on_no": ["office"],
                                                                         "show_on_yes": ["city"]})
        office = forms.CharField(required=False)
        city = forms.CharField(required=False)

    form = F()
    assert form["office"].visible is True and form["city"].visible is False
    form["remote"].value = True
    assert form["office"].visible is False and form["city"].visible is True


def test_formset():
    class Item(forms.Form):
        name = forms.CharField()

    ItemFormSet = forms.formset_factory(Item, extra=2, min_num=1, max_num=3)
    fs = ItemFormSet()
    assert len(fs.forms) == 2
    fs.add_form({"name": "c"})
    assert len(fs.forms) == 3
    assert fs.add_form() is None  # max_num
    assert fs.add_button.visible is False
    fs.remove_form(fs.forms[0])
    assert len(fs.forms) == 2
    assert not fs.is_valid()
    fs.forms[0]["name"].value = "a"
    assert fs.is_valid()
    assert fs.cleaned_data == [{"name": "a"}, {"name": "c"}]
    fs.remove_form(fs.forms[0])
    fs.remove_form(fs.forms[0])  # min_num = 1
    assert len(fs.forms) == 1

    initial = ItemFormSet(initial=[{"name": "x"}, {"name": "y"}])
    assert [f["name"].value for f in initial.forms] == ["x", "y"]


# ----------------------------------------------------------------------
# ModelForm
# ----------------------------------------------------------------------
Base = declarative_base()


class Thing(Base):
    __tablename__ = "things"
    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String(30), nullable=False)
    email = sa.Column(sa.String, nullable=True)
    notes = sa.Column(sa.Text)
    price = sa.Column(sa.Numeric(10, 2))
    active = sa.Column(sa.Boolean, default=True)
    born = sa.Column(sa.Date)
    kind = sa.Column(sa.Enum("a", "b", name="kind"))


def test_model_form_generates_fields():
    class ThingForm(forms.ModelForm):
        class Meta:
            model = Thing
            exclude = ["notes"]
            labels = {"name": "Nombre"}

    form = ThingForm()
    assert list(form.fields) == ["name", "email", "price", "active", "born", "kind"]
    assert isinstance(form.fields["name"], forms.CharField) and form.fields["name"].max_length == 30
    assert form.fields["name"].label == "Nombre" and form.fields["name"].required
    assert isinstance(form.fields["email"], forms.EmailField) and not form.fields["email"].required
    assert isinstance(form.fields["price"], forms.DecimalField)
    assert isinstance(form.fields["active"], forms.BooleanField)
    assert isinstance(form.fields["born"], forms.DateField)
    assert form.fields["kind"].choices == [("a", "a"), ("b", "b")]
    assert ThingForm.title == "Thing"


def test_model_form_declared_override_and_save():
    class ThingForm(forms.ModelForm):
        name = forms.CharField(label="Nombre propio", max_length=5)

        class Meta:
            model = Thing
            fields = ["name", "active"]

    form = ThingForm()
    assert form.fields["name"].label == "Nombre propio"
    form["name"].value = "Lápiz"
    assert form.is_valid()
    thing = form.save()
    assert isinstance(thing, Thing) and thing.name == "Lápiz"

    class FakeManager:
        def __init__(self):
            self.calls = []

        def create(self, **data):
            self.calls.append(("create", data))
            return Thing(id=1, **data)

        def update(self, pk, **data):
            self.calls.append(("update", pk, data))
            return Thing(id=pk, **data)

    manager = FakeManager()
    form = ThingForm(instance=Thing(id=7, name="Viejo", active=False))
    assert form["name"].value == "Viejo"
    form["name"].value = "Nuevo"
    assert form.is_valid()
    form.save(manager)
    assert manager.calls == [("update", 7, {"name": "Nuevo", "active": False})]


# ----------------------------------------------------------------------
# Widgets sin página
# ----------------------------------------------------------------------
def test_widgets_value_roundtrip():
    cases = [
        (w.TextInput(label="x"), "hola", "hola"),
        (w.NumberInput(), 5, "5"),
        (w.CheckboxInput(), True, True),
        (w.Select(choices=[("a", "A")]), "a", "a"),
        (w.RadioSelect(choices=["x", "y"]), "y", "y"),
        (w.NullBooleanSelect(), False, False),
        (w.CheckboxSelectMultiple(choices=["x", "y"]), ["y"], ["y"]),
        (w.DateInput(), date(2024, 3, 1), date(2024, 3, 1)),
        (w.DateRangeInput(), (date(2024, 1, 1), date(2024, 1, 2)), (date(2024, 1, 1), date(2024, 1, 2))),
        (w.TimeInput(), time(9, 30), time(9, 30)),
        (w.PhoneNumberMaskInput(), "88881234", "8888-1234"),
        (w.ColorInput(), "#abcdef", "#ABCDEF"),
        (w.TaggingInput(), ["a", "b"], ["a", "b"]),
        (w.GridSlider(min=0, max=10), (2, 8), (2, 8)),
        (w.SingleGridSlider(min=0, max=10), 3, 3),
        (w.NumberKnobInput(min=0, max=10), 7, 7),
        (w.AutocompleteSelect(choices=[(1, "Uno")]), "1", "1"),
        (w.AutocompleteSelectMultiple(choices=[(1, "Uno"), (2, "Dos")]), ["2"], ["2"]),
        (w.FilteredSelectMultiple(choices=["a", "b"]), ["b"], ["b"]),
        (w.TreeSelect(nodes=[{"id": "r", "text": "R", "children": [{"id": "c", "text": "C"}]}]), "c", "c"),
    ]
    for widget, value, expected in cases:
        widget.value = value
        assert widget.value == expected, type(widget).__name__


def test_widget_change_listeners_and_errors():
    widget = w.TextInput(label="Nombre")
    calls = []
    widget.on_change = lambda wd: calls.append(wd.value)
    widget.set_value("abc")
    widget.changed()
    assert calls == ["abc"]
    widget.error = "malo"
    assert widget.field.error == "malo"
    widget.changed()  # cambiar el valor quita el error
    assert widget.error is None


def test_i18n_switch_language():
    assert get_language() == "es"
    assert _("Save") == "Guardar"
    set_language("en")
    try:
        assert _("Save") == "Save"
        assert _("Add {name}", name="X") == "Add X"
        with pytest.raises(forms.ValidationError) as e:
            forms.CharField().clean("")
        assert e.value.messages == ["This field is required."]
    finally:
        set_language("es")


def test_file_field_with_existing_file(tmp_path):
    f = forms.ImageField(upload_to=tmp_path / "media", media_url="image/")
    initial = f.prepare_value("foto.png")
    assert initial.stored and not initial.is_new and initial.url == "image/foto.png"
    assert initial.path == str(tmp_path / "media" / "foto.png")
    cleaned = f.clean(initial)
    # Un archivo ya guardado no se copia otra vez (aunque no exista en disco)
    assert f.save_file(cleaned) == "foto.png"
    assert not (tmp_path / "media").exists()
    assert f.clean("otra.jpg").stored

    widget = f.build_widget()
    widget.value = initial
    assert widget.file_text.value == "Archivo actual: foto.png"
    assert widget.preview.src == "image/foto.png" and widget.preview.visible
    widget.value = w.UploadedFile(name="nueva.png", content=b"x")
    assert widget.file_text.value == "Seleccionado: nueva.png"
