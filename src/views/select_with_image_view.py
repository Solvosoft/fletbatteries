import flet as ft
from components.shared.selects import AutoCompleteSelectImage, AutoCompleteSelectMultipleImage
from components.shared.modals import CrudModal
import requests

def build_view_select_with_image(page: ft.Page):

    try:
        response = requests.get("http://localhost:3000/images/random?count=10")
        response.raise_for_status()
        api_data = response.json()
        initial_data = {
            "results": {str(i+1): {"id": str(i+1), "image": item["url"]} for i, item in enumerate(api_data)}
        }
    except Exception as e:
        print("Error al obtener imágenes de la API:", e)
        initial_data = {
            "results": {
                str(i): {
                    "id": str(i),
                    "image": f"https://picsum.photos/200/300?random={i}"
                }
                for i in range(1, 11)
            }
        }

    modal = CrudModal(page)
    selected_items_store = []
    selected_single_item = None

    # ---- Manejo de selección múltiple ----
    def on_change_multi(select_component, selected_values, items):
        nonlocal selected_items_store
        selected_items_store = items

    # ---- Manejo de selección única ----
    def on_change_single(select_component, selected_value, item):
        nonlocal selected_single_item
        selected_single_item = item

    select_multi = AutoCompleteSelectMultipleImage(
        page,
        data=initial_data,
        label="Selecciona múltiples imágenes",
        on_change=on_change_multi,
    )

    select_image = AutoCompleteSelectImage(
        page,
        data=initial_data,
        label="Seleciona una imagen",
        on_change=on_change_single,
    )

    # ---- Contenedor de tarjetas ----
    cards_column = ft.Column(spacing=10)
    single_cards_column = ft.Column(spacing=10)

    # ---- Funciones CRUD compartidas ----
    def remove_card(card, container):
        if card in container.controls:
            container.controls.remove(card)
            page.update()
            return True
        return False

    def confirm_delete(card, container, tipo="grupo"):
        modal.open(
            kind="delete",
            title=f"Eliminar {tipo}",
            content_controls=[ft.Text(f"¿Estás seguro de eliminar este {tipo}?")],
            on_accept=lambda e=None, c=card, cont=container: remove_card(c, cont),
            success_text=f"{tipo.capitalize()} eliminado",
            error_text=f"No se pudo eliminar el {tipo}",
            width=520,
        )

    # ---- Guardar selección múltiple ----
    def save_multi_items(e):
        if not selected_items_store:
            return

        items_row = ft.Row(
            wrap=True,
            spacing=10,
            controls=[
                ft.Container(
                    content=ft.Image(src=item.get("image", ""), width=60, height=60),
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
                    ft.Text("Imágenes seleccionadas (grupo):", size=16, weight="bold"),
                    items_row,
                    btn_delete,
                ],
                spacing=10,
            ),
            padding=15,
            bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.ON_SURFACE),
            border_radius=10,
        )

        btn_delete.on_click = lambda e, c=card: confirm_delete(c, cards_column, "grupo")

        cards_column.controls.append(card)
        select_multi.clear()
        selected_items_store.clear()
        page.update()

    # ---- Guardar selección única ----
    def save_single_item(e):
        nonlocal selected_single_item 
        if not selected_single_item:
            return

        image_url = selected_single_item.get("image", "")

        item_display = ft.Container(
            content=ft.Image(src=image_url, width=80, height=80),
            alignment=ft.alignment.center,
            bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.ON_SURFACE),
            padding=10,
            border_radius=8,
        )

        btn_delete = ft.ElevatedButton(
            "Eliminar imagen",
            icon=ft.Icons.DELETE,
            icon_color=ft.Colors.RED,
        )

        card = ft.Container(
            content=ft.Column(
                [
                    ft.Text("Imagen seleccionada:", size=16, weight="bold"),
                    item_display,
                    btn_delete,
                ],
                spacing=10,
            ),
            padding=15,
            bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.ON_SURFACE),
            border_radius=10,
            width=200,
        )

        btn_delete.on_click = lambda e, c=card: confirm_delete(c, single_cards_column, "imagen")

        single_cards_column.controls.append(card)

        # Limpiar selección única
        select_image.clear()
        selected_single_item = None
        page.update()

    # ---- Construir layout ----
    return ft.Container(
        padding=20,
        expand=True,
        alignment=ft.alignment.top_center,
        content=ft.Column(
            [
                ft.Text("Select con imágenes", size=22, weight="bold"),
                # Sección múltiple
                ft.Text("Selección múltiple:", size=18, weight="bold"),
                select_multi.control,
                ft.ElevatedButton("Guardar grupo de imágenes", on_click=save_multi_items),
                ft.Text("Grupos guardados:", size=16, weight="bold"),
                cards_column,
                ft.Divider(height=30),

                # Sección única
                ft.Text("Selección única:", size=18, weight="bold"),
                select_image.control,
                ft.ElevatedButton("Guardar imagen única", on_click=save_single_item),
                ft.Text("Imágenes guardadas:", size=16, weight="bold"),
                single_cards_column,
            ],
            spacing=15,
            horizontal_alignment=ft.CrossAxisAlignment.START,  
            alignment=ft.MainAxisAlignment.START, 
            scroll=ft.ScrollMode.AUTO,
        ),
    )
