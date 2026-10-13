import json

import flet as ft

from fletbatteries import forms
from fletbatteries import widgets as w
from fletbatteries.utils import route_query, run_after_mount

from settings import ASSETS_DIR

COUNTRIES = [("cr", "Costa Rica"), ("pa", "Panamá"), ("ni", "Nicaragua"), ("mx", "México"), ("co", "Colombia")]
CATEGORIES = [
    {"id": "tech", "text": "Tecnología", "children": [
        {"id": "web", "text": "Web"},
        {"id": "mobile", "text": "Móvil", "children": [{"id": "android", "text": "Android"},
                                                      {"id": "ios", "text": "iOS"}]},
    ]},
    {"id": "sci", "text": "Ciencia", "children": [{"id": "bio", "text": "Biología"}, {"id": "chem", "text": "Química"}]},
]


class NewCountryForm(forms.Form):
    code = forms.CharField(label="Código", max_length=2)
    name = forms.CharField(label="Nombre")


class WidgetsForm(forms.Form):
    title = "Catálogo de widgets"
    render_type = "grid"
    grid_representation = [
        [["name"], ["email"], ["website"]],
        [["age"], ["salary"], ["password"]],
        [["birth_date"], ["meeting_time"], ["appointment"]],
        [["vacation"], ["event_range"]],
        [["phone"], ["tax_id"], ["credit_card"]],
        [["country"], ["country_add"], ["countries"]],
        [["languages"], ["gender"], ["has_pet"]],
        [["accept_terms"], ["remote"], ["office"]],
        [["tags"], ["emails"], ["color"]],
        [["price_range"], ["volume"], ["rating"]],
        [["category"], ["topics"]],
        [["skills"]],
        [["avatar"], ["document"]],
        [["bio"]],
        [["notes"]],
    ]

    name = forms.CharField(label="Nombre", max_length=50, help_text="Máximo 50 caracteres")
    email = forms.EmailField(label="Correo")
    website = forms.URLField(label="Sitio web", required=False)
    age = forms.IntegerField(label="Edad", min_value=0, max_value=120)
    salary = forms.DecimalField(label="Salario", decimal_places=2, required=False)
    password = forms.PasswordField(label="Contraseña", min_length=6, required=False)
    birth_date = forms.DateField(label="Nacimiento", max_date="d0", required=False)
    meeting_time = forms.TimeField(label="Hora de reunión", required=False)
    appointment = forms.DateTimeField(label="Cita", required=False)
    vacation = forms.DateRangeField(label="Vacaciones", required=False)
    event_range = forms.DateTimeRangeField(label="Evento", required=False)
    phone = forms.MaskedField(label="Teléfono", widget=w.PhoneNumberMaskInput, required=False)
    tax_id = forms.MaskedField(label="Cédula", widget=w.TaxIDMaskInput, required=False)
    credit_card = forms.MaskedField(label="Tarjeta", widget=w.CreditCardMaskInput, required=False)
    country = forms.ChoiceField(label="País", choices=COUNTRIES, widget=w.AutocompleteSelect)
    country_add = forms.ChoiceField(
        label="País (con +)", choices=COUNTRIES, required=False, widget=w.SelectWithAdd,
        widget_kwargs={"add_form": NewCountryForm, "on_add": lambda data: (data["code"], data["name"])},
    )
    countries = forms.MultipleChoiceField(label="Países visitados", choices=COUNTRIES, required=False)
    languages = forms.MultipleChoiceField(
        label="Idiomas", choices=[("es", "Español"), ("en", "Inglés"), ("fr", "Francés")],
        widget=w.CheckboxSelectMultiple, required=False,
    )
    gender = forms.ChoiceField(label="Género", choices=[("f", "Femenino"), ("m", "Masculino"), ("o", "Otro")],
                               widget=w.RadioSelect, required=False)
    has_pet = forms.NullBooleanField(label="¿Tiene mascota?")
    accept_terms = forms.BooleanField(label="Acepto los términos", required=True)
    remote = forms.BooleanField(label="Trabajo remoto", widget=w.YesNoInput,
                                widget_kwargs={"show_on_no": ["office"]})
    office = forms.CharField(label="Oficina", required=False)
    tags = forms.TagsField(label="Etiquetas", required=False, suggestions=["python", "flet", "django", "fastapi"])
    emails = forms.TagsField(label="Correos en copia", emails=True, required=False)
    color = forms.ColorField(label="Color favorito", required=False)
    price_range = forms.RangeField(label="Rango de precio", min_value=0, max_value=1000, required=False)
    volume = forms.IntegerField(label="Volumen", widget=w.SingleGridSlider, min_value=0, max_value=10, required=False)
    rating = forms.IntegerField(label="Calificación", widget=w.NumberKnobInput, min_value=0, max_value=10,
                                required=False)
    category = forms.TreeChoiceField(label="Categoría", nodes=CATEGORIES, required=False)
    topics = forms.TreeChoiceField(label="Temas", nodes=CATEGORIES, multiple=True, required=False)
    skills = forms.MultipleChoiceField(
        label="Habilidades", widget=w.FilteredSelectMultiple, required=False,
        choices=[("py", "Python"), ("js", "JavaScript"), ("sql", "SQL"), ("go", "Go"), ("rs", "Rust")],
    )
    avatar = forms.ImageField(label="Avatar", required=False, upload_to=ASSETS_DIR / "image", media_url="image/")
    document = forms.FileField(label="Documento", allowed_extensions=["pdf", "txt"], required=False)
    bio = forms.TextAreaField(label="Biografía", required=False)
    notes = forms.MarkdownField(label="Notas (Markdown)", required=False)


def open_visual_state(form):
    """Pone los widgets interactivos en su estado abierto (para revisarlos con `make screenshots`)."""
    form["country"]._open_dropdown()
    form["countries"]._open_dropdown()
    form["notes"].show_preview(True)


def build_view_widgets(page: ft.Page) -> ft.Control:
    visual = route_query(page).get("visual") == "open"
    initial = {"remote": True}
    if visual:
        initial.update(avatar="ejemplo.jpg", notes="## Título\n\nTexto en **negrita** y una lista:\n\n- uno\n- dos")
    form = WidgetsForm(initial=initial)
    if visual:
        run_after_mount(page, lambda: open_visual_state(form))
    result = ft.Text(key="widgets_result", selectable=True)

    def validate(e):
        if form.is_valid():
            data = {k: form.fields[k].display(v) for k, v in form.cleaned_data.items()}
            result.value = json.dumps(data, ensure_ascii=False, indent=2)
            result.color = ft.Colors.GREEN_800
        else:
            result.value = f"Errores en: {', '.join(form.errors)}"
            result.color = ft.Colors.ERROR
        result.update()

    def reset(e):
        form.reset()
        result.value = ""
        page.update()

    return ft.Container(
        expand=True,
        padding=10,
        content=ft.Column(
            scroll=ft.ScrollMode.AUTO,
            controls=[
                ft.Text("Widgets", size=20),
                ft.Divider(),
                form.control,
                ft.Row([
                    ft.Button(content="Validar", icon=ft.Icons.CHECK, on_click=validate),
                    ft.TextButton("Limpiar", on_click=reset),
                ]),
                result,
            ],
        ),
    )
