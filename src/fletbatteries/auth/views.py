"""Vista de login y administración de usuarios, grupos y permisos."""

from typing import Callable, Optional

import flet as ft

from fletbatteries import forms
from fletbatteries.auth.backend import GroupManager, PermissionManager, UserManager
from fletbatteries.crud.crud_view import CRUDView
from fletbatteries.data.source import SQLAlchemySource
from fletbatteries.i18n import _
from fletbatteries.widgets.choices import FilteredSelectMultiple
from fletbatteries.widgets.datatable import Column, list_text

MANAGE_PERMISSION = "auth.manage"


def build_login_view(on_login: Callable[[str, str], Optional[str]], title: str = "", logo: Optional[str] = None
                     ) -> ft.Control:
    """
    Formulario de ingreso. `on_login(usuario, contraseña)` devuelve `None` si
    entró o el mensaje de error que se debe mostrar.
    """
    username = ft.TextField(label=_("Username"), prefix_icon=ft.Icons.PERSON, key="login_username", autofocus=True)
    password = ft.TextField(label=_("Password"), prefix_icon=ft.Icons.PASSWORD, password=True,
                            can_reveal_password=True, key="login_password")
    error = ft.Text("", color=ft.Colors.ERROR, visible=False, key="login_error")

    def submit(e=None):
        message = on_login(username.value or "", password.value or "")
        if message:
            error.value = message
            error.visible = True
            password.value = ""
            error.page.update()

    password.on_submit = submit
    username.on_submit = lambda e: password.focus()
    header = []
    if logo:
        header.append(ft.Image(src=logo, width=120, height=120))
    header.append(ft.Text(title or _("Login"), size=22, weight=ft.FontWeight.BOLD))
    card = ft.Card(
        content=ft.Container(
            padding=24,
            width=420,
            content=ft.Column(
                [username, password, error,
                 ft.Button(content=_("Login"), icon=ft.Icons.LOGIN, on_click=submit, key="login_submit")],
                tight=True,
                spacing=14,
                horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            ),
        ),
    )
    return ft.Container(
        expand=True,
        alignment=ft.Alignment.CENTER,
        content=ft.Column([*header, card], tight=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                          alignment=ft.MainAxisAlignment.CENTER),
    )


# ----------------------------------------------------------------------
# Administración
# ----------------------------------------------------------------------
def _permission_choices():
    return [(str(p.id), f"{p.name} ({p.codename})") for p in PermissionManager().get_all()]


def _group_choices():
    return [(str(g.id), g.name) for g in GroupManager().get_all()]


class UserAdminForm(forms.Form):
    title = _("User")
    render_type = "grid"
    grid_representation = [
        [["username"], ["email"]],
        [["first_name"], ["last_name"]],
        [["password"], ["is_active", "is_superuser"]],
        [["groups"]],
        [["permissions"]],
    ]

    username = forms.CharField(label=_("Username"), max_length=150)
    email = forms.EmailField(label="Email", required=False)
    first_name = forms.CharField(label=_("First name"), required=False)
    last_name = forms.CharField(label=_("Last name"), required=False)
    password = forms.PasswordField(label=_("Password"), required=False, min_length=4,
                                   help_text=_("Leave empty to keep the current password"))
    is_active = forms.BooleanField(label=_("Active"), initial=True)
    is_superuser = forms.BooleanField(label=_("Superuser"))
    groups = forms.MultipleChoiceField(label=_("Groups"), choices=_group_choices, coerce=int, required=False,
                                       list_display=False)
    permissions = forms.MultipleChoiceField(label=_("Permissions"), choices=_permission_choices, coerce=int,
                                            required=False, widget=FilteredSelectMultiple, list_display=False)

    def clean(self):
        if self.instance is None and not self.cleaned_data.get("password"):
            self.add_error("password", _("This field is required."))
        return self.cleaned_data


class GroupAdminForm(forms.Form):
    title = _("Group")
    name = forms.CharField(label=_("Name"), max_length=150)
    permissions = forms.MultipleChoiceField(label=_("Permissions"), choices=_permission_choices, coerce=int,
                                            required=False, widget=FilteredSelectMultiple, list_display=False)


class PermissionAdminForm(forms.Form):
    title = _("Permission")
    codename = forms.CharField(label=_("Code"), max_length=100, help_text="app.action")
    name = forms.CharField(label=_("Name"), max_length=200)
    category = forms.CharField(label=_("Category"), max_length=100, required=False)


class UserAdminCRUD(CRUDView):
    title = _("Users")
    name = _("user")
    form_class = UserAdminForm
    list_fields = ["username", "first_name", "last_name", "email", "is_active", "is_superuser"]
    filter_fields = ["username", "email", "is_active"]
    permissions = {a: MANAGE_PERMISSION for a in ("create", "edit", "delete", "detail")}
    route = "/admin/users"
    icon = ft.Icons.MANAGE_ACCOUNTS

    def get_source(self):
        return SQLAlchemySource(UserManager())


class GroupAdminCRUD(CRUDView):
    title = _("Groups")
    name = _("group")
    form_class = GroupAdminForm
    list_fields = ["name", Column("permissions", label=_("Permissions"), sortable=False,
                                  render=lambda value, item: list_text(
                                      [PermissionManager().get(p).codename for p in value or []]))]
    permissions = {a: MANAGE_PERMISSION for a in ("create", "edit", "delete", "detail")}
    route = "/admin/groups"
    icon = ft.Icons.GROUPS

    def get_source(self):
        return SQLAlchemySource(GroupManager())


class PermissionAdminCRUD(CRUDView):
    title = _("Permissions")
    name = _("permission")
    form_class = PermissionAdminForm
    list_fields = ["codename", "name", "category"]
    filter_fields = ["category"]
    permissions = {a: MANAGE_PERMISSION for a in ("create", "edit", "delete", "detail")}
    route = "/admin/permissions"
    icon = ft.Icons.KEY

    def get_source(self):
        return SQLAlchemySource(PermissionManager())
