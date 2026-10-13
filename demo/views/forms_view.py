import flet as ft

from fletbatteries import forms


class ContactForm(forms.Form):
    title = "Contacto"
    grid_representation = [
        [["first_name"], ["last_name"]],
        [["email", "phone"], ["message"]],
    ]

    first_name = forms.CharField(label="Nombre", max_length=40)
    last_name = forms.CharField(label="Apellidos", max_length=60, required=False)
    email = forms.EmailField(label="Correo")
    phone = forms.CharField(label="Teléfono", required=False)
    message = forms.TextAreaField(label="Mensaje", required=False)

    def clean_first_name(self, value):
        return value.title()

    def clean(self):
        data = self.cleaned_data
        if not data.get("phone") and not data.get("email"):
            raise forms.ValidationError("Indique un correo o un teléfono.")
        return data


class AddressForm(forms.Form):
    render_type = "inline"
    street = forms.CharField(label="Dirección")
    city = forms.CharField(label="Ciudad")


AddressFormSet = forms.formset_factory(AddressForm, extra=1, min_num=1, max_num=4)


def build_view_forms(page: ft.Page) -> ft.Control:
    holder = ft.Container()
    state = {"form": None}
    result = ft.Text(key="forms_result")

    def show(render_type):
        state["form"] = ContactForm(render_type=render_type)
        holder.content = state["form"].control
        page.update()

    def submit(e):
        form = state["form"]
        valid = form.is_valid() & formset.is_valid()
        if valid:
            result.value = f"OK: {form.cleaned_data['first_name']} con {len(formset.cleaned_data)} direcciones"
        else:
            result.value = "Hay errores"
        result.update()

    selector = ft.Dropdown(
        key="render_type",
        label="Render",
        value="grid",
        width=200,
        options=[ft.DropdownOption(r) for r in ("plain", "horizontal", "inline", "grid")],
        on_select=lambda e: show(e.control.value),
    )
    formset = AddressFormSet(title="Direcciones")
    state["form"] = ContactForm(render_type="grid")
    holder.content = state["form"].control

    return ft.Container(
        expand=True,
        padding=10,
        content=ft.Column(
            scroll=ft.ScrollMode.AUTO,
            controls=[
                ft.Text("Formularios", size=20),
                ft.Divider(),
                selector,
                holder,
                ft.Divider(),
                formset.control,
                ft.Button(content="Enviar", icon=ft.Icons.SEND, on_click=submit),
                result,
            ],
        ),
    )
