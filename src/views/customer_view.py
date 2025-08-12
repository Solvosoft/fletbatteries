import flet as ft
from components.shared.datatable import FBDataTable
from components.shared.modals import CrudModal

def build_view_customer(page: ft.Page, forms: []) -> ft.Container:

    form = None
    for form in forms:
        if form.name == "CustomerForm":
            form = form
    form_dialog = CrudModal(page)
    data = [
        {"id": 1, "name": "Ana", "last_name": "Gómez", "phone": 88888888, "email": "ana@gmail.com"},
        {"id": 2, "name": "Luis", "last_name": "Rojas", "phone": 55555555, "email": "luis@gmail.com"},
        {"id": 3, "name": "Eva", "last_name": "Zamora", "phone": 66666666, "email": "eva@gmail.com"},
        {"id": 4, "name": "Juan", "last_name": "Perez", "phone": 77777777, "email": "juan@gmail.com"},
        {"id": 5, "name": "Maria", "last_name": "Rodríguez", "phone": 88888888, "email": "maria@gmail.com"},
        {"id": 6, "name": "Ana", "last_name": "Gómez", "phone": 88888888, "email": "ana@gmail.com"},
        {"id": 7, "name": "Luis", "last_name": "Rojas", "phone": 55555555, "email": "luis@gmail.com"},
        {"id": 8, "name": "Eva", "last_name": "Zamora", "phone": 66666666, "email": "eva@gmail.com"},
        {"id": 9, "name": "Juan", "last_name": "Perez", "phone": 77777777, "email": "juan@gmail.com"},
        {"id": 10, "name": "Maria", "last_name": "Rodríguez", "phone": 88888888, "email": "maria@gmail.com"},
    ]

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
                customer = form.get_item()
                if customer["id"] == 0 or customer["id"] is None:
                    data.append(customer)
                else:
                    for i, item in enumerate(data):
                        if item["id"] == customer["id"]:
                            data[i] = customer
                            break
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