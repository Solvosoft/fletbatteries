import flet as ft

from components.shared.generic_card import GenericCard


class GenericCardCRUD:
    def __init__(self, page: ft.Page, title: str, get_method, create_method,
                 update_method, delete_method, card_content: [], top_bar_color=ft.Colors.BLUE_GREY_900,
                 add_button_color=ft.Colors.AMBER, add_button=None):
        self.page = page
        self.title = title
        self.get_method = get_method
        self.create_method = create_method
        self.update_method = update_method
        self.delete_method = delete_method
        self.list_item = []
        self.list_item_container = None
        self.card_content = card_content
        self.selected_item_to_delete = None
        self.selected_item_to_update = None
        self.form_dialog = None

        if not add_button:
            self.add_button = ft.ElevatedButton(
                text="Agregar",
                icon=ft.Icons.ADD,
                bgcolor=add_button_color,
                color=ft.Colors.BLACK,
                on_click=self.create_method,
            )
        else:
            self.add_button = add_button

        self.top_bar_color = top_bar_color
        self.add_button_color = add_button_color

        self.delete_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("¿ELiminar?"),
            content=ft.Text("¿Estás seguro de que deseas eliminar este item?"),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: self.cancel_delete()),
                ft.TextButton("Eliminar", on_click= self.confirm_delete),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

    def on_add_item(self, e):
        #Limpiar formulario
        self.form_dialog.open = True
        self.page.update()

    def cancel_delete(self):
        self.delete_dialog.open = False
        self.page.update()

    def confirm_delete(self, e):
        item = self.selected_item_to_delete
        if product:
            try:
                self.delete_method(item)
                self.list_item.remove(item)
                self.product_list_container.controls = self.build_product_cards()
                self.product_list_container.update()
            except Exception as ex:
                print(f"Error al eliminar producto: {ex}")
            finally:
                self.selected_item_to_delete = None

    def on_select_item(self, item):
        self.selected_item_to_update = item

    def on_delete_item(self, item):
        self.selected_item_to_delete = item
        self.delete_dialog.title = ft.Text(f"Eliminar {self.title}")

    def submit(self):
        #validar el fomulario
        try:
            item = None #Obtner el item del formulario
            if not self.selected_item_to_update:
                item = self.create_method(item)
            else:
                item = self.update_method(item)
                self.list_item.remove(self.selected_item_to_update)

            self.list_item.append(item)
            self.form_dialog.open = False
            self.product_list_container.controls = self.build_product_cards()
            self.product_list_container.update()
            self.page.update()
        except Exception as ex:
            print(f"Error al agregar producto: {ex}")
            self.form_dialog.title = ft.Text(ex, color=ft.Colors.RED)
            self.page.update()

    def build_item_cards(self):
        try:
            self.list_item = self.get_method()
        except Exception as ex:
            print(f"Error al obtener {self.title}: {ex}")
            self.list_item = []

        return [
            GenericCard(
                content=self.card_content,
                on_edit=lambda e, i=item: self.on_select_item(i),
                on_delete=lambda e, i=item: self.on_delete_item(i),
                height=400,
            )
            for item in self.list_item
        ]

    def build_view(self) -> ft.Container:

        self.list_item_container = ft.GridView(
            expand=True,
            max_extent=300,
            child_aspect_ratio=0.6,
            spacing=20,
            run_spacing=15,
            controls=self.build_item_cards()
        )

        return ft.Container(
            expand=True,
            content=ft.Column(
                spacing=0,
                controls=[
                    ft.Container(
                        bgcolor=self.top_bar_color,
                        padding=ft.Padding(20, 10, 20, 10),
                        content=ft.Row(
                            controls=[
                                ft.Text(self.title, size=22, color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD),
                                ft.Container(expand=True),
                                self.add_button,
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        )
                    ),
                    ft.Container(
                        expand=True,
                        padding=20,
                        content=self.list_item_container,
                        alignment=ft.alignment.center,
                    )
                ]
            )
        )
