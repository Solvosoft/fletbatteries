import flet as ft

from fletbatteries.auth import get_user


def build_view_profile(page: ft.Page) -> ft.Container:
    user = get_user(page)
    rows = []
    if user:
        rows = [
            ft.ListTile(leading=ft.Icon(ft.Icons.PERSON), title=ft.Text(user.display_name),
                        subtitle=ft.Text(user.username)),
            ft.ListTile(leading=ft.Icon(ft.Icons.EMAIL), title=ft.Text(user.email or "—")),
            ft.ListTile(leading=ft.Icon(ft.Icons.VERIFIED_USER),
                        title=ft.Text("Superusuario" if user.is_superuser else
                                      ", ".join(sorted(user.permissions)) or "Sin permisos")),
        ]
    return ft.Container(
        expand=True,
        padding=10,
        content=ft.Column([ft.Text("Profile", size=20), *rows], alignment=ft.MainAxisAlignment.START),
    )
