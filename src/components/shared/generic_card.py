# controls/components/generic_card.py
import flet as ft

def GenericCard(
    content: list[ft.Control],
    on_edit=None,
    on_delete=None,
    width=300,
):
    return ft.Container(
        content=ft.Card(
            ft.Container(
                content=ft.Column(
                    controls=[
                        *content,
                        ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            controls=[
                                ft.IconButton(
                                    icon=ft.Icons.EDIT,
                                    tooltip="Editar",
                                    on_click=on_edit
                                ),
                                ft.IconButton(
                                    icon=ft.Icons.DELETE,
                                    tooltip="Eliminar",
                                    icon_color=ft.Colors.RED,
                                    on_click=on_delete
                                ),
                            ]
                        )
                    ],
                    spacing=5,
                    alignment=ft.MainAxisAlignment.START,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER
                ),
                padding=10,
                width=width,
            )
        ),
        width=width + 20,
        padding=5,
    )
