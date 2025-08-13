# controls/components/generic_card.py
import flet as ft

def GenericCard(
    content: list[ft.Control],
    actions: list[ft.Control],
    width=300,
    height=400,
):
    return ft.Container(
        content=ft.Card(
            ft.Container(
                content=ft.Column(
                    controls=[
                        *content,
                        ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            controls=actions,
                        )
                    ],
                    spacing=5,
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER
                ),
                padding=10,
                width=width,
            ),
            width=500,
        ),
        width=width + 20,
        height=height,
        padding=5,
    )
