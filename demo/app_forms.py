"""Formularios de la demo construidos con fletbatteries.forms."""

from fletbatteries import forms
from fletbatteries import widgets as w
from fletbatteries.data import APISource

from data.models.customer import Customer
from data.models.product import Product
from data.models.user import User
from settings import API_URL, ASSETS_DIR


class CustomerForm(forms.ModelForm):
    title = "Clientes"
    render_type = "grid"
    grid_representation = [[["name"], ["last_name"]], [["email"], ["phone"]]]

    phone = forms.MaskedField(label="Teléfono", widget=w.PhoneNumberMaskInput, required=False)

    class Meta:
        model = Customer
        fields = ["name", "last_name", "email", "phone"]
        labels = {"name": "Nombre", "last_name": "Apellidos", "email": "Correo"}


class ProductForm(forms.ModelForm):
    title = "Productos"

    image = forms.ImageField(label="Imagen", upload_to=ASSETS_DIR / "image", media_url="image/")

    class Meta:
        model = Product
        fields = ["name", "code", "price", "image"]
        labels = {"name": "Nombre", "code": "Código", "price": "Precio"}


class UserForm(forms.ModelForm):
    title = "Usuarios"

    password = forms.PasswordField(label="Contraseña", min_length=4, required=False, list_display=False,
                                   help_text="Déjela vacía para no cambiarla")

    class Meta:
        model = User
        fields = ["name", "email", "password"]
        labels = {"name": "Nombre", "email": "Correo"}

    def initial_from_instance(self, instance):
        initial = super().initial_from_instance(instance)
        initial.pop("password", None)  # nunca se muestra el hash
        return initial

    def clean(self):
        if self.instance is None and not self.cleaned_data.get("password"):
            self.add_error("password", "Este campo es obligatorio.")
        return self.cleaned_data


class EventForm(forms.Form):
    """Formulario de la vista /test: registros en memoria con fechas."""

    title = "Eventos de prueba"
    render_type = "horizontal"

    name = forms.CharField(label="Nombre", max_length=60)
    date = forms.DateField(label="Fecha", min_date="y1", max_date="y1")
    datetime = forms.DateTimeField(label="Fecha y hora")


def api_source(endpoint: str) -> APISource:
    return APISource(f"{API_URL}api/{endpoint}")


class PersonGroupForm(forms.Form):
    title = "Grupos de personas"
    render_type = "grid"
    grid_representation = [[["name"], ["country_id"]], [["people"], ["communities"]]]

    name = forms.CharField(label="Nombre", max_length=80)
    country_id = forms.ModelChoiceField(api_source("countries"), label="País")
    people = forms.ModelMultipleChoiceField(api_source("persons"), label="Personas", required=False)
    communities = forms.ModelMultipleChoiceField(api_source("communities"), label="Comunidades", required=False)
