import flet as ft
from components.shared.modals import CrudModal


def build_view_modals(page: ft.Page) -> ft.Container:
    modal = CrudModal(page)

    # Formularios demo
    create_name = ft.TextField(label="Nombre")
    create_email = ft.TextField(label="Email")

    def on_create():
        return bool(create_name.value.strip() and create_email.value.strip())

    edit_name = ft.TextField(label="Nombre", value="Ana")
    edit_email = ft.TextField(label="Email", value="ana@gmail.com")

    def on_edit():
        return True  # éxito

    def on_delete():
        return False  # error para probar

    detail_controls = [ft.Text("ID: 1"), ft.Text("Nombre: Ana"), ft.Text("Email: ana@gmail.com")]

    btn_create = ft.ElevatedButton(
        "Agregar", icon=ft.Icons.ADD,
        on_click=lambda e: modal.open(
            kind="create",
            title="Agregar usuario",
            content_controls=[create_name, create_email],
            on_accept=on_create,
            success_text="Usuario guardado",
            error_text="Faltan datos",
            width=600,
        ),
    )

    btn_edit = ft.ElevatedButton(
        "Editar", icon=ft.Icons.EDIT,
        on_click=lambda e: modal.open(
            kind="edit",
            title="Editar usuario",
            content_controls=[edit_name, edit_email],
            on_accept=on_edit,
            success_text="Usuario actualizado",
            error_text="No se pudo actualizar",
            width=600,
        ),
    )

    btn_delete = ft.ElevatedButton(
        "Eliminar", icon=ft.Icons.DELETE,
        style=ft.ButtonStyle(bgcolor=ft.Colors.RED_600, color=ft.Colors.WHITE),
        on_click=lambda e: modal.open(
            kind="delete",
            title="Eliminar usuario",
            content_controls=[ft.Text("¿Estás seguro de eliminar este registro?")],
            on_accept=on_delete,
            success_text="Usuario eliminado",
            error_text="No se pudo eliminar",
            width=520,
        ),
    )

    btn_detail = ft.OutlinedButton(
        "Detalle", icon=ft.Icons.REMOVE_RED_EYE_ROUNDED,
        on_click=lambda e: modal.open(
            kind="detail",
            title="Detalle de usuario",
            content_controls=detail_controls,
            on_accept=None,
            width=520,
        ),
    )

    return ft.Container(
        expand=True,
        content=ft.Column(
            controls=[
                ft.Text("Modals", size=20),
                ft.Divider(),
                ft.Container(
                    content=btn_create,
                    expand=True,
                    alignment=ft.alignment.center,
                ),
                ft.Divider(),
                ft.Container(
                    content=btn_edit,
                    expand=True,
                    alignment=ft.alignment.center,
                ),
                ft.Divider(),
                ft.Container(
                    content=btn_delete,
                    expand=True,
                    alignment=ft.alignment.center,
                ),
                ft.Divider(),
                ft.Container(
                    content=btn_detail,
                    expand=True,
                    alignment=ft.alignment.center,
                ),
            ],
            spacing=12,
            alignment=ft.alignment.center,
        ),
        alignment=ft.alignment.center,
        padding=10,
    )
