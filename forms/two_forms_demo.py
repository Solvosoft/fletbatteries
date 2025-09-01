import flet as ft
from components.tinymce_widget import TinyMCEEditor


class TwoFormsDemo(ft.Column):  # <-- reemplazamos UserControl por Column
    def __init__(self, static_port: int):
        super().__init__(spacing=20)  # Column acepta props como spacing
        self.static_port = static_port

        # inicializamos los dos editores
        self.basic_editor = TinyMCEEditor(
            static_port=static_port,
            preset="basic",
            initial_value="<p>Editor básico listo.</p>",
            height=300,
        )

        self.advanced_editor = TinyMCEEditor(
            static_port=static_port,
            preset="advanced",
            initial_value="<h2>Editor avanzado</h2><p>Con más herramientas.</p>",
            height=420,
        )

        # construimos el layout aquí en vez de usar build()
        self.controls.append(
            ft.Text(
                "Demo: dos WYSIWYG en la misma vista (TinyMCE self-hosted)",
                size=20,
                weight=ft.FontWeight.BOLD,
            )
        )

        # cards
        self.controls.append(
            ft.ResponsiveRow(
                [
                    ft.Container(content=self._basic_card(), col={"xs": 12, "md": 6}),
                    ft.Container(content=self._advanced_card(), col={"xs": 12, "md": 6}),
                ],
                run_spacing=16,
            )
        )

    def _basic_card(self):
        def submit_basic(e):
            ft.toast("Enviando formulario básico…")
            print("[BÁSICO] HTML:", self.basic_editor.value())

        return ft.Card(
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Text("Formulario Básico", weight=ft.FontWeight.BOLD, size=18),
                        self.basic_editor,
                        ft.Row(
                            [
                                ft.ElevatedButton("Enviar básico", on_click=submit_basic),
                                ft.TextButton(
                                    "Deshabilitar",
                                    on_click=lambda _: self.basic_editor.set_disabled(True),
                                ),
                                ft.TextButton(
                                    "Habilitar",
                                    on_click=lambda _: self.basic_editor.set_disabled(False),
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.END,
                        ),
                    ],
                    tight=True,
                    spacing=12,
                ),
                padding=16,
            )
        )

    def _advanced_card(self):
        def submit_advanced(e):
            ft.toast("Enviando formulario avanzado…")
            print("[AVANZADO] HTML:", self.advanced_editor.value())

        return ft.Card(
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Text("Formulario Avanzado", weight=ft.FontWeight.BOLD, size=18),
                        self.advanced_editor,
                        ft.Row(
                            [
                                ft.ElevatedButton("Enviar avanzado", on_click=submit_advanced),
                                ft.TextButton(
                                    "Cargar demo HTML",
                                    on_click=lambda _: self.advanced_editor.set_value(
                                        "<p><em>Texto cargado por código</em></p>"
                                    ),
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.END,
                        ),
                    ],
                    tight=True,
                    spacing=12,
                ),
                padding=16,
            )
        )