"""Formularios con grupos de campos (pestañas, secciones, colapsables) y un wizard."""

import flet as ft

from fletbatteries import forms
from fletbatteries.utils import route_query


class EmployeeForm(forms.Form):
    title = "Empleado"
    fieldsets_style = "tabs"
    fieldsets = [
        ("Datos personales", {"fields": ["first_name", "last_name", "email"],
                              "description": "Datos básicos de la persona"}),
        ("Trabajo", {"fields": ["position", "start_date", "salary"],
                     "grid": [[["position"], ["start_date"]], [["salary"]]]}),
        ("Notas", {"fields": ["notes"]}),
    ]

    first_name = forms.CharField(label="Nombre", max_length=40)
    last_name = forms.CharField(label="Apellidos", max_length=60)
    email = forms.EmailField(label="Correo")
    position = forms.ChoiceField(label="Puesto", choices=[("dev", "Desarrollo"), ("ops", "Operaciones"),
                                                          ("sales", "Ventas")])
    start_date = forms.DateField(label="Fecha de ingreso")
    salary = forms.DecimalField(label="Salario", decimal_places=2, required=False)
    notes = forms.TextAreaField(label="Notas", required=False)


class PersonStep(forms.Form):
    name = forms.CharField(label="Nombre", max_length=60)
    email = forms.EmailField(label="Correo")
    is_company = forms.BooleanField(label="Es una empresa")


class AddressStep(forms.Form):
    city = forms.CharField(label="Ciudad")
    address = forms.TextAreaField(label="Dirección", required=False)


class CompanyStep(forms.Form):
    company = forms.CharField(label="Razón social")
    tax_id = forms.CharField(label="Cédula jurídica")


def build_view_wizard(page: ft.Page) -> ft.Control:
    style = route_query(page).get("style", "tabs")
    result = ft.Text(key="wizard_result")
    form_holder = ft.Container()
    state = {}

    def show(style_name):
        form_cls = type("EmployeeForm", (EmployeeForm,), {"fieldsets_style": style_name})
        state["form"] = form_cls()
        form_holder.content = state["form"].control
        page.update()

    def validate(e):
        form = state["form"]
        result.value = "Formulario válido" if form.is_valid() else "Hay errores"
        result.update()

    def finished(data):
        result.value = f"Wizard terminado: {data['name']}" + (f" ({data['company']})" if data.get("company") else "")
        result.update()

    wizard = forms.FormWizard(
        steps=[
            ("Persona", PersonStep),
            ("Dirección", AddressStep),
            ("Empresa", CompanyStep, lambda data: data.get("is_company")),
        ],
        on_finish=finished,
    )
    selector = ft.Dropdown(
        key="fieldsets_style",
        label="Estilo de grupos",
        value=style,
        width=220,
        options=[ft.DropdownOption("tabs", "Pestañas"), ft.DropdownOption("sections", "Secciones"),
                 ft.DropdownOption("collapsible", "Colapsables")],
        on_select=lambda e: show(e.control.value),
    )
    show(style)
    return ft.Container(
        expand=True,
        padding=10,
        content=ft.Column(
            [
                ft.Text("Grupos de campos", size=20),
                selector,
                ft.Container(form_holder, width=640),
                ft.Button("Validar", icon=ft.Icons.CHECK, on_click=validate, key="fieldsets_validate"),
                ft.Divider(),
                ft.Text("Wizard", size=20),
                ft.Container(wizard, width=640),
                result,
            ],
            scroll=ft.ScrollMode.AUTO,
            spacing=12,
        ),
    )
