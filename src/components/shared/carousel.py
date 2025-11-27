
import flet as ft
import asyncio

class Carousel(ft.Container):
    def __init__(
        self,
        images,
        active_color=ft.Colors.BLACK,
        inactive_color=ft.Colors.RED,
        height=400,
        width=800,
        interval=3,  # segundos entre slides
        auto_play=True,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.images = images
        self.active_color = active_color
        self.inactive_color = inactive_color
        self.height = height
        self.width = width
        self.interval = interval
        self.auto_play = auto_play
        self.current_index = 0
        self._is_running = False

        self.image_controls = [
            ft.Image(
                src=img,
                fit=ft.ImageFit.FILL,
                width=self.width,
                height=self.height,
                opacity=1 if i == 0 else 0,
                animate_opacity=ft.Animation(500, ft.AnimationCurve.EASE_IN_OUT),
            )
            for i, img in enumerate(images)
        ]
        self.indicators = ft.Row(
            alignment=ft.MainAxisAlignment.CENTER,
            controls=[
                ft.Container(
                    width=10,
                    height=10,
                    border_radius=10,
                    bgcolor=self.active_color if i == 0 else self.inactive_color,
                    on_click=lambda e, idx=i: self.go_to_index(idx)
                )
                for i in range(len(self.images))
            ]
        )
        nav_buttons = ft.Row(
            controls=[
                ft.IconButton(
                    icon=ft.Icons.NAVIGATE_BEFORE,
                    on_click=lambda e: self.go_to_index(self.current_index - 1),
                ),
                ft.IconButton(
                    icon=ft.Icons.NAVIGATE_NEXT,
                    on_click=lambda e: self.go_to_index(self.current_index + 1),
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            expand=False
        )
        self.content = ft.Stack(
            controls=[
                *self.image_controls,
                ft.Container(
                    content=self.indicators,
                    alignment=ft.alignment.bottom_center,
                    padding=ft.padding.only(bottom=15),
                    expand=True
                ),
                ft.Container(
                    content=nav_buttons,
                    alignment=ft.alignment.center,
                    expand=True
                ),
            ]
        )

    def go_to_index(self, index):
        index %= len(self.images)
        for i, indicator in enumerate(self.indicators.controls):
            indicator.bgcolor = self.active_color if i == index else self.inactive_color
        for i, img in enumerate(self.image_controls):
            img.opacity = 1 if i == index else 0
        self.current_index = index
        self.update()

    async def _autoplay_loop(self, page: ft.Page):
        self._is_running = True
        try:
            while self._is_running:
                await asyncio.sleep(self.interval)
                # Si se destruyó el carrusel, detén
                if not self.visible or not self.page:
                    self._is_running = False
                    break
                self.go_to_index(self.current_index + 1)
        except Exception as ex:
            print("Autoplay stopped:", ex)

    def start_autoplay(self, page: ft.Page):
        # Arranca la tarea sólo si no está corriendo
        if self.auto_play and not self._is_running:
            page.run_task(self._autoplay_loop, page)

    def stop_autoplay(self):
        self._is_running = False