import flet as ft

from fletbatteries.crud import CRUDView

from app_forms import UserForm
from data.manager.user_manager import UserManager


class UserCRUD(CRUDView):
    title = "Users"
    name = "usuario"
    manager = UserManager()
    form_class = UserForm
    list_fields = ["name", "email"]


def build_view_user(page: ft.Page) -> ft.Control:
    return UserCRUD(page).build()
