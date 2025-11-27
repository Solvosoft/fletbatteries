import flet as ft
from components.shared.datatable import FBDataTable
from components.shared.modals import CrudModal
from controls.customer.customer_control import CustomerControl
from data.models.customer import Customer
from controls.utils import get_form


def build_view_customer(page: ft.Page, forms: []) -> ft.Container:
    form = get_form(forms, "CustomerForm")
    form_dialog = CrudModal(page)
    control = CustomerControl()
    customers = control.get_all_customers()
    data = [c.to_dict() for c in customers]

    def create_method():
        form.clean()
        form_dialog.open(
            kind="create",
            title=f"Agregar {form.title}",
            content_controls=form.get_inputs(),
            on_accept=submit,
            success_text="Guardado exitosamente",
            error_text="Error al guardar",
            width=600,
        )
        page.update()

    def update_method(item):
        form.clean()
        for field, value in item.items():
            for input in form.inputs:
                if input.name == field:
                    input.set_value(value)
        form_dialog.open(
            kind="edit",
            title=f"Editar {form.title}",
            content_controls=form.get_inputs(),
            on_accept=submit,
            success_text="Guardado exitosamente",
            error_text="Error al guardar",
            width=600,
        )
        page.update()

    def confirm_delete(item):
        customer = Customer.from_dict(item)
        control.delete_customer(customer.id)
        data.remove(item)
        datatable.reload(data)
        return True

    def delete_method(item):
        form_dialog.open(
            kind="delete",
            title=f"Eliminar {form.title}",
            content_controls=[ft.Text("¿Estás seguro de eliminar este registro?")],
            on_accept=lambda: confirm_delete(item),
            success_text="Producto eliminado",
            error_text="Error al eliminar producto",
            width=600,
        )
        page.update()

    def submit():
        if form.is_valid():
            try:
                customer = Customer.from_dict(form.get_item())
                if customer.id == 0 or customer.id is None:
                    customer = control.create_customer(customer.name, customer.last_name, customer.phone,
                                                       customer.email)
                    data.append(customer.to_dict())
                else:
                    customer = control.update_customer(customer.id, customer.name, customer.last_name, customer.phone,
                                                       customer.email)
                    for i, item in enumerate(data):  # actualizar en la tabla
                        if item["id"] == customer.id:
                            data[i] = customer.to_dict()
                datatable.reload(data)
                return True
            except Exception as ex:
                print(f"Error al agregar producto: {ex}")
                form_dialog.title = ft.Text(str(ex), color=ft.Colors.RED)
                page.update()
                return False
        page.update()
        return False

    actions = [
        lambda item: ft.ElevatedButton(
            content=ft.Icon(ft.Icons.EDIT),
            on_click=lambda e, it=item: update_method(it),
        ),
        lambda item: ft.ElevatedButton(
            content=ft.Icon(ft.Icons.DELETE),
            on_click=lambda e, it=item: delete_method(it),
        ),
    ]

    top_actions = [
        ft.ElevatedButton(
            content=ft.Icon(ft.Icons.ADD),
            on_click=lambda e: create_method(),
        )
    ]

    datatable = FBDataTable(data, form, title="Customers",
                            actions=actions, top_actions=top_actions)

    return ft.Container(
        expand=True,
        content=ft.Column(
            controls=[
                ft.Text("Customer", size=20),
                ft.Divider(),
                ft.Container(
                    content=datatable,
                    expand=True,
                    padding=10,
                    alignment=ft.alignment.center,
                )
            ],
            alignment=ft.alignment.top_center,
        )
    )
