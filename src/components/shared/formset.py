import flet as ft
from components.shared.form import GenerateForms
from controls.utils import show_snackbar

class Formset:
    def __init__(self, page, form, data, actions: [], title: str, delete_button = None,
                 card_width=420, card_height=380):
        self.page = page
        self.generate_forms = GenerateForms(self.page)
        self.form = self.generate_forms.clone(form.name)
        print(self.form)
        self.data = data
        self.actions = actions
        self.formset = []
        self.build_formset()
        self.title = title
        self._cards_column: ft.Column | None = None
        self.card_width = card_width
        self.aspect_ratio = self.card_width / card_height
        self.delete_button = delete_button

    def _iter_values(self):
        if isinstance(self.data, list):
            return self.data
        if isinstance(self.data, dict):
            if all(isinstance(v, dict) for v in self.data.values()):
                return list(self.data.values())
            return [self.data]
        return []

    def _build_card(self, form) -> ft.Card:
        return ft.Card(
            content=ft.Container(
                content=ft.Column(
                    alignment=ft.MainAxisAlignment.START,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=8,
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Text(form.title, size=20),
                                self.delete_button(form) if callable(self.delete_button) else ft.Container(),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                        ft.Column(controls=form.get_inputs()),
                        ft.Row(
                            controls=[factory(form) for factory in self.actions],
                        )
                    ],
                ),
                padding=10,
                width=400,
            ),
            shadow_color=ft.Colors.GREY_300,
            elevation=2.0,
        )

    def _render_cards(self):
        if self._cards_column is None:
            return
        self._cards_column.controls = [self._build_card(f) for f in self.formset]
        self._cards_column.update()

    def build_formset(self):
        self.formset = []
        for row in self._iter_values():
            f = self.generate_forms.clone(self.form.name)
            for fld in f.inputs:
                if fld.name in row:
                    fld.set_value(row[fld.name])
            self.formset.append(f)

    def add_item(self, *_):
        new_form = self.generate_forms.clone(self.form.name)
        self.formset.append(new_form)

        if self._cards_column is not None:
            self._cards_column.controls.append(self._build_card(new_form))
            self._cards_column.update()
        elif self.page is not None:
            # fallback
            self.page.update()

    def build_formset_view(self) -> ft.Container:
        self._cards_column = ft.GridView(
            expand=True,
            max_extent=self.card_width,
            child_aspect_ratio=self.aspect_ratio,
            spacing=8,
            run_spacing=8,
            controls=[self._build_card(f) for f in self.formset],
        )
        return ft.Container(
            expand=True,
            alignment=ft.alignment.top_center,
            content=ft.Column(
                spacing=16,
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                ft.Text(self.title, size=20, color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        padding=ft.Padding(20, 10, 20, 10),
                        bgcolor=ft.Colors.BLUE_GREY_900,
                        height=50,
                    ),
                    ft.Container(
                        expand=True,
                        content=self._cards_column,
                    ),
                    ft.Container(
                        alignment=ft.alignment.center,
                        content=ft.ElevatedButton(
                            content=ft.Icon(ft.Icons.ADD, size=30, color=ft.Colors.WHITE),
                            on_click=lambda e: self.add_item(),
                            tooltip="Add new item",
                            bgcolor=ft.Colors.GREEN_500,

                        ),
                        padding=10,
                    )
                ],
            ),
        )

    def refresh_view(self, *, new_data=None):
        if new_data is not None:
            self.data = new_data
            self.build_formset()
        if self.page is not None:
            self.page.update()
        self._render_cards()

