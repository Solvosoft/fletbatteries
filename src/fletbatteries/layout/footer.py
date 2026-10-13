from typing import Optional, Sequence

import flet as ft


class Footer(ft.Container):
    def __init__(self, text: str = "", logo: Optional[str] = None, links: Sequence[tuple[str, str]] = (),
                 bgcolor=ft.Colors.BLUE_GREY_900, color=ft.Colors.WHITE):
        controls = []
        if logo:
            controls.append(ft.Image(src=logo, width=32, height=32))
        controls.append(ft.Text(text, color=color, size=12))
        controls.append(ft.Container(expand=True))
        controls += [ft.IconButton(icon=ft.Icons.LINK, tooltip=title, url=url, icon_color=color) for title, url in links]
        super().__init__(
            height=48,
            bgcolor=bgcolor,
            padding=ft.Padding.symmetric(horizontal=20),
            content=ft.Row(controls, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        )
