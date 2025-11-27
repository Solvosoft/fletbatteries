import flet as ft

from components.shared.generic_card import GenericCard
from components.shared.rotating_boxes_loader import RotatingBoxesLoader
from assets.fontawesome.fontawesome import get_icon



class GenericCardCRUD:
    def __init__(self, page: ft.Page, data, title: str, form, card_content: [], card_actions, top_actions,
                 top_bar_color=ft.Colors.BLUE_GREY_900, page_size=25, card_width=300, card_height=400, aspect_ratio=0.7):
        self.page = page
        self.title = title
        self.data = data
        self.list_item_container = None
        self.page_number = 0
        self.page_size = page_size
        self.more_items = True
        self.is_loading = False
        self.card_content = card_content
        self.card_actions = card_actions
        self.top_actions = top_actions
        self.form = form
        self.card_width = card_width
        self.card_height = card_height
        self.aspect_ratio = aspect_ratio
        self.spinner = RotatingBoxesLoader(
            size=30,
            color_a_border="#e9665a",
            color_b_border="#7df6dd",
            color_a_bg=None,
            color_b_bg="#1f262f",
            text="Loading...",
            text_size=6,
            text_color="white",
            step_seconds=0.7,
            border_width=2.5,
        )
        self.spinner.visible = False
        self.top_bar_color = top_bar_color
        self.form.activate_on_filter(self.filter_list)

    def _materialize_items(self):
        if isinstance(self.data, list):
            items = self.data
        else:
            items = list(self.data.values())
        self._all_items = items
        self._total = len(items)
        self.more_items = self._total > (self.page_number * self.page_size)

    def reset_pagination(self):
        self.page_number = 0
        self.more_items = True
        self.spinner.visible = False
        self._materialize_items()
        self.load_next_page()

    def reload(self, data = None):
        if data is not None:
            self.data = data
        self.list_item_container.controls = []
        self.reset_pagination()

    def load_next_page(self):
        if not self.is_loading and self.more_items:
            self.is_loading = True
            self.spinner.visible = True
            self.page.update()
            try:
                if not hasattr(self, "_all_items"):
                    self._materialize_items()

                self.page_number += 1

                start = (self.page_number - 1) * self.page_size
                end = start + self.page_size
                page_items = self._all_items[start:end]

                if not page_items:
                    self.more_items = False
                    self.spinner.visible = False
                    self.page.update()
                    return

                if end >= self._total:
                    self.more_items = False

                new_controls = self.build_item_cards(page_items)

                self.list_item_container.controls.extend(new_controls)
                if self.list_item_container.page:
                    self.list_item_container.update()
            finally:
                self.spinner.visible = False
                self.page.update()
                self.is_loading = False

    def _on_grid_scroll(self, e: ft.OnScrollEvent):
        threshold = 200
        if e.pixels is not None and e.max_scroll_extent is not None:
            if e.pixels >= e.max_scroll_extent - threshold:
                print("on_grid_scroll")
                self.load_next_page()

    def build_item_cards(self, items):
        return [
            GenericCard(
                content=self.card_content(item),
                actions=[factory(item) for factory in self.card_actions],
                width=self.card_width,
                height=self.card_height,
            )
            for item in items

        ]

    def filter_list(self, value, key):
        source = getattr(self, "data", []) or []
        filtered = []

        is_value_number = isinstance(value, (int, float)) and not isinstance(value, bool)
        value_str = str(value).lower() if not is_value_number else None

        for item in source:
            if not isinstance(item, dict) or key not in item:
                continue

            item_val = item[key]

            if is_value_number and isinstance(item_val, (int, float)) and not isinstance(item_val, bool):
                if item_val == value:
                    filtered.append(item)
                continue

            item_val_str = "" if item_val is None else str(item_val)
            try:
                if value_str in item_val_str.lower():
                    filtered.append(item)
            except Exception:
                continue

        self.list_item_container.controls = self.build_item_cards(filtered)
        self.list_item_container.update()

    def clear_filters(self):
        self.form.clear_filters()
        self.page.update()
        self.page_number = 1
        self.more_items = True
        self.load_next_page()
        self.reset_pagination()
        self.list_item_container.update()

    def build_view(self) -> ft.Container:
        self.list_item_container = ft.GridView(
            expand=True,
            max_extent=self.card_width,
            child_aspect_ratio=self.aspect_ratio,
            spacing=20,
            run_spacing=15,
            on_scroll=self._on_grid_scroll,
            on_scroll_interval=100,
            controls=[],
        )
        container =  ft.Container(
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
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        )
                    ),
                    ft.Container(
                        expand=False,
                        padding=5,
                        content=ft.Column(
                            controls=[
                                ft.Row(
                                    controls=[
                                        ft.ElevatedButton(
                                            content=get_icon("eraser", color="black", size=15),
                                            on_click=lambda e: self.clear_filters(),
                                        ),
                                        ft.Row(
                                            controls=self.top_actions,
                                        )

                                    ],
                                    alignment=ft.MainAxisAlignment.CENTER,
                                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                ),
                                ft.Row(
                                    controls=self.form.get_filters(),
                                    wrap=True,
                                ),
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            alignment=ft.MainAxisAlignment.CENTER,
                        ),
                        alignment=ft.alignment.center,
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
        self.load_next_page()
        return container
