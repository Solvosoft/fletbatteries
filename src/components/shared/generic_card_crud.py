import flet as ft

from components.shared.generic_card import GenericCard
from components.shared.rotating_boxes_loader import RotatingBoxesLoader

class GenericCardCRUD:
    def __init__(self, page: ft.Page, title: str, get_method, get_method_by_id, create_method,
                 update_method, delete_method, card_content: [], form_name: str, forms: [],
                 top_bar_color=ft.Colors.BLUE_GREY_900, add_button_color=ft.Colors.GREEN_700, add_color=ft.Colors.WHITE,
                 add_button=None, page_size = 25, card_width=300, card_height=400, aspect_ratio=0.7):
        self.page = page
        self.title = title
        self.get_method = get_method
        self.get_method_by_id = get_method_by_id
        self.create_method = create_method
        self.update_method = update_method
        self.delete_method = delete_method
        self.list_item = []
        self.list_item_container = None
        self.page_number = 1
        self.page_size = page_size
        self.more_items = True
        self.is_loading = False
        self.card_content = card_content
        self.selected_item_to_delete = None
        self.selected_item_to_update = None
        self.form_name = form_name
        self.forms = forms
        self.form = None
        self.card_width = card_width
        self.card_height = card_height
        self.aspect_ratio = aspect_ratio
        self.spinner = RotatingBoxesLoader(
                size=40,
                color_a_border="#e9665a",
                color_b_border="#7df6dd",
                color_a_bg=None,
                color_b_bg="#1f262f",
                text="Loading...",
                text_size=7,
                text_color="white",
                step_seconds=0.7,
                border_width=2.5,
            )
        self.spinner.visible = False
        for form in self.forms:
            if form.name == self.form_name:
                self.form = form

        if not add_button:
            self.add_button = ft.ElevatedButton(
                text="Agregar",
                icon=ft.Icons.ADD,
                bgcolor=add_button_color,
                color=add_color,
                on_click=self.on_add_item,
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
                ft.TextButton("Eliminar", on_click=self.confirm_delete),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self.form_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(f"Agregar {self.form.title}"),
            content=ft.Column(
                controls=self.form.get_inputs(),
                tight=True,
                spacing=10
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: self.close_dialog()),
                ft.ElevatedButton("Guardar", on_click=self.submit),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self.page.overlay.append(self.form_dialog)

    def on_add_item(self, e):
        self.form.clean()
        self.form_dialog.open = True
        self.page.update()

    def cancel_delete(self):
        self.delete_dialog.open = False
        self.page.update()

    def close_dialog(self):
        self.form_dialog.open = False
        self.page.update()

    def confirm_delete(self, e):
        item = self.selected_item_to_delete
        if item:
            try:
                self.delete_method(item)
                self.list_item.remove(item)
                self.list_item_container.controls = self.build_item_cards()
                self.list_item_container.update()
                self.delete_dialog.open = False
                self.page.update()
            except Exception as ex:
                print(f"Error al eliminar producto: {ex}")
            finally:
                self.selected_item_to_delete = None

    def on_delete_item(self, item):
        self.page.overlay.append(self.delete_dialog)
        self.selected_item_to_delete = item
        self.delete_dialog.open = True
        self.page.update()

    def on_select_item(self, item):
        self.selected_item_to_update = self.get_method_by_id(item['id'])
        for field, value in item.items():
            for input in self.form.inputs:
                if input.name == field:
                    input.set_value(value)
        self.form_dialog.open = True
        self.page.update()

    def submit(self, e):
        if self.form.is_valid():
            try:
                item = self.form.get_item()
                if item["id"] == 0 or item["id"] is None:
                    item = self.create_method(item)
                else:
                    item = self.update_method(item)
                    self.list_item.remove(self.selected_item_to_update)
                self.form.activate_on_upload()
                self.list_item.append(item)
                self.form_dialog.open = False
                self.list_item_container.controls = self.build_item_cards()
                self.list_item_container.update()
                self.page.update()
            except Exception as ex:
                print(f"Error al agregar producto: {ex}")
                self.form_dialog.title = ft.Text(str(ex), color=ft.Colors.RED)
                self.page.update()
        self.page.update()

    def load_next_page(self):
        if not self.is_loading and self.more_items:
            self.is_loading = True
            self.spinner.visible = True
            self.page.update()
            try:
                self.page_number += 1
                result = self.get_method(self.page_number, self.page_size)
                if not result:
                    self.more_items = False
                    self.spinner.visible = False
                    self.page.update()
                    return
                if len(result) < self.page_size:
                    self.more_items = False
                self.list_item.extend(result)
                self.list_item_container.controls = self.build_item_cards()
                self.list_item_container.update()
                self.spinner.visible = False
                self.page.update()
            finally:
                self.is_loading = False

    def _on_grid_scroll(self, e: ft.OnScrollEvent):
        threshold = 200
        if e.pixels is not None and e.max_scroll_extent is not None:
            if e.pixels >= e.max_scroll_extent - threshold:
                self.load_next_page()

    def build_item_cards(self):
        return [
            GenericCard(
                content=self.card_content(item),
                on_edit=lambda e, i=item: self.on_select_item(i),
                on_delete=lambda e, i=item: self.on_delete_item(i),
                width=self.card_width,
                height=self.card_height,
            )
            for item in self.list_item

        ]

    def build_view(self) -> ft.Container:

        self.list_item = self.get_method(self.page_number, self.page_size)

        self.list_item_container = ft.GridView(
            expand=True,
            max_extent=self.card_width,
            child_aspect_ratio=self.aspect_ratio,
            spacing=20,
            run_spacing=15,
            on_scroll=self._on_grid_scroll,
            on_scroll_interval=100,
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
                                ft.Row(
                                    controls=[
                                        ft.Text(self.title, size=22, color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD),
                                        self.spinner,
                                    ]
                                ),
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
                    ),
                ]
            )
        )
