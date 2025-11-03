import flet as ft
from components.shared.selects import AutoCompleteSelectMultipleImage
from components.shared.modals import CrudModal

def build_view_select_with_image(page: ft.Page):
    # ---- Datos estáticos ----
    initial_data = {
        "results": {
            "1": {"id": "1", "image": "https://i.pinimg.com/736x/ab/ed/e3/abede32914ec2e41ad41e1b17df49d85.jpg"},
            "2": {"id": "2",  "image": "https://i.pinimg.com/736x/ab/ed/e3/abede32914ec2e41ad41e1b17df49d85.jpg"},
            "3": {"id": "3",  "image": "https://i.pinimg.com/736x/ab/ed/e3/abede32914ec2e41ad41e1b17df49d85.jpg"},
            "4": {"id": "4",  "image": "https://i.pinimg.com/736x/ab/ed/e3/abede32914ec2e41ad41e1b17df49d85.jpg"},
            "5": {"id": "5",  "image": "https://i.pinimg.com/736x/ab/ed/e3/abede32914ec2e41ad41e1b17df49d85.jpg"},
            "6": {"id": "6",  "image": "https://i.pinimg.com/736x/ab/ed/e3/abede32914ec2e41ad41e1b17df49d85.jpg"},
            "7": {"id": "7",  "image": "https://i.pinimg.com/736x/ab/ed/e3/abede32914ec2e41ad41e1b17df49d85.jpg"},
            "8": {"id": "8", "image": "https://i.pinimg.com/736x/ab/ed/e3/abede32914ec2e41ad41e1b17df49d85.jpg"},
            "9": {"id": "9",  "image": "https://i.pinimg.com/736x/ab/ed/e3/abede32914ec2e41ad41e1b17df49d85.jpg"},
            "10": {"id": "10",  "image": "https://i.pinimg.com/736x/ab/ed/e3/abede32914ec2e41ad41e1b17df49d85.jpg"},
        
        }
    }

    modal = CrudModal(page)
    selected_items_store = []

    # ---- Manejo de selección ----
    def on_change(select_component, selected_values, items):
        nonlocal selected_items_store
        selected_items_store = items

    select_multi = AutoCompleteSelectMultipleImage(
        page,
        data=initial_data,
        label="Frutas con imágenes",
        on_change=on_change,
        value=[1,2,3,4,5]
    )

    # ---- Contenedor de tarjetas ----
    cards_column = ft.Column(spacing=10)

    def remove_card(card):
        if card in cards_column.controls:
            cards_column.controls.remove(card)
            page.update()
            print("Card eliminada")
            return True
        return False

    def confirm_delete(card):
        modal.open(
            kind="delete",
            title="Eliminar grupo",
            content_controls=[ft.Text("¿Estás seguro de eliminar este grupo de frutas?")],
            on_accept=lambda e=None, c=card: remove_card(c),
            success_text="Grupo eliminado",
            error_text="No se pudo eliminar",
            width=520,
        )

    def save_items(e):
        if not selected_items_store:
            return

        # Crear contenido con todas las frutas seleccionadas
        items_row = ft.Row(
            wrap=True,
            spacing=10,
            controls=[
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Image(src=item.get("image", ""), width=60, height=60),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    padding=5,
                    bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.ON_SURFACE),
                )
                for item in selected_items_store
            ],
        )

        btn_delete = ft.ElevatedButton(
            "Eliminar grupo",
            icon=ft.Icons.DELETE,
            icon_color=ft.Colors.RED,
        )

        card = ft.Container(
            content=ft.Column(
                [
                    ft.Text("Frutas seleccionadas:", size=16, weight="bold"),
                    items_row,
                    btn_delete
                ],
                spacing=10,
            ),
            padding=15,
            bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.ON_SURFACE),
            border_radius=10,
        )

        btn_delete.on_click = lambda e, c=card: confirm_delete(c)

        cards_column.controls.append(card)

        # Limpiar selección
        select_multi.clear()
        selected_items_store.clear()
        page.update()

    # ---- Construir layout ----
    return ft.Container(
        padding=20,
        expand=True,
        content=ft.Column(
            [
                ft.Text("Select con imágenes", size=20, weight="bold"),
                select_multi.control,
                ft.ElevatedButton("Guardar selección", on_click=save_items),
                ft.Text("Grupos guardados:", size=18, weight="bold"),
                cards_column,
            ],
            spacing=15,
        ),
    )
