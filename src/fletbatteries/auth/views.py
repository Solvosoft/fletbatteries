"""
Vistas de autenticación: login, cambio y recuperación de contraseña, tokens
del API y administración de usuarios, grupos, permisos e intentos de ingreso.

Se registran con `app.add_account_views()` y `app.add_admin_views()`.
"""

import asyncio
import logging
from typing import Callable, Optional, Sequence

import flet as ft

from fletbatteries import forms
from fletbatteries.auth.backend import GroupManager, LoginAttemptManager, PermissionManager, UserManager
from fletbatteries.auth.session import get_user
from fletbatteries.crud.crud_view import CRUDView
from fletbatteries.data.source import SQLAlchemySource
from fletbatteries.i18n import _
from fletbatteries.utils import notify, safe_update
from fletbatteries.widgets.choices import FilteredSelectMultiple
from fletbatteries.widgets.datatable import Column, list_text

log = logging.getLogger(__name__)

MANAGE_PERMISSION = "auth.manage"


def build_login_view(on_login: Callable[[str, str], Optional[str]], title: str = "", logo: Optional[str] = None,
                     message: Optional[str] = None, on_forgot: Optional[Callable[[], None]] = None) -> ft.Control:
    """
    Formulario de ingreso. `on_login(usuario, contraseña)` devuelve `None` si
    entró o el mensaje de error que se debe mostrar. `message` se muestra arriba
    (p. ej. "La sesión venció") y `on_forgot` agrega el enlace "¿Olvidó su contraseña?".
    """
    username = ft.TextField(label=_("Username"), prefix_icon=ft.Icons.PERSON, key="login_username", autofocus=True)
    password = ft.TextField(label=_("Password"), prefix_icon=ft.Icons.PASSWORD, password=True,
                            can_reveal_password=True, key="login_password")
    error = ft.Text(message or "", color=ft.Colors.ERROR, visible=bool(message), key="login_error")

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
    extra = []
    if on_forgot is not None:
        extra.append(ft.TextButton(_("Forgot your password?"), on_click=lambda e: on_forgot(), key="login_forgot"))
    card = ft.Card(
        content=ft.Container(
            padding=24,
            width=420,
            content=ft.Column(
                [username, password, error,
                 ft.Button(content=_("Login"), icon=ft.Icons.LOGIN, on_click=submit, key="login_submit"), *extra],
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
    password = forms.PasswordField(label=_("Password"), required=False,
                                   help_text=_("Leave empty to keep the current password"))
    # Validadores de contraseña (None = los de `default_password_validators()`)
    password_validators: Optional[Sequence] = None
    is_active = forms.BooleanField(label=_("Active"), initial=True)
    is_superuser = forms.BooleanField(label=_("Superuser"))
    groups = forms.MultipleChoiceField(label=_("Groups"), choices=_group_choices, coerce=int, required=False,
                                       list_display=False)
    permissions = forms.MultipleChoiceField(label=_("Permissions"), choices=_permission_choices, coerce=int,
                                            required=False, widget=FilteredSelectMultiple, list_display=False)

    def clean_password(self, value):
        from fletbatteries.auth.password_validation import validate_password

        if value:
            user = {k: self.cleaned_data.get(k) for k in ("username", "first_name", "last_name", "email")}
            validate_password(value, user, self.password_validators)
        return value

    def clean(self):
        if self.instance is None and not self.cleaned_data.get("password") and "password" not in self.errors:
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


class LoginAttemptForm(forms.Form):
    title = _("Login attempt")
    username = forms.CharField(label=_("Username"))
    success = forms.BooleanField(label=_("Successful"))
    reason = forms.CharField(label=_("Reason"), required=False)
    created_at = forms.DateTimeField(label=_("Date"))


class LoginAttemptCRUD(CRUDView):
    """Registro de ingresos (solo lectura)."""

    title = _("Login attempts")
    name = _("login attempt")
    form_class = LoginAttemptForm
    actions = ("detail",)
    list_fields = ["created_at", "username", "success", "reason"]
    filter_fields = ["username", "success"]
    order_by = "-created_at"
    permissions = {"detail": MANAGE_PERMISSION}
    route = "/admin/logins"
    icon = ft.Icons.LOGIN

    def get_source(self):
        return SQLAlchemySource(LoginAttemptManager())


# ----------------------------------------------------------------------
# Cuenta del usuario
# ----------------------------------------------------------------------
def _app_option(page, name: str, default=None):
    """Opción de `FletBatteriesApp` de la sesión (si la página usa el app shell)."""
    from fletbatteries.app import shell_of

    shell = shell_of(page)
    return getattr(shell.app, name, default) if shell is not None else default


class PasswordChangeForm(forms.Form):
    title = _("Change password")
    old_password = forms.PasswordField(label=_("Current password"))
    new_password = forms.PasswordField(label=_("New password"))
    confirm = forms.PasswordField(label=_("Confirm new password"))

    def clean(self):
        new, confirm = self.cleaned_data.get("new_password"), self.cleaned_data.get("confirm")
        if new and confirm is not None and new != confirm:
            self.add_error("confirm", _("The two password fields didn't match."))
        return self.cleaned_data


def build_password_change_view(page: ft.Page, validators: Optional[Sequence] = None) -> ft.Control:
    """Vista para que el usuario cambie su propia contraseña."""
    from fletbatteries.auth.password_validation import password_help_texts
    from fletbatteries.forms.validators import ValidationError

    validators = validators if validators is not None else _app_option(page, "password_validators")
    form = PasswordChangeForm(render_type="plain")
    form.fields["new_password"].help_text = " ".join(password_help_texts(validators))

    def submit(e=None):
        if not form.is_valid():
            return
        user = get_user(page)
        data = form.cleaned_data
        try:
            if user is None or UserManager().get(user.id) is None:
                raise ValidationError(_("Your account cannot change its password here."))
            UserManager().change_password(user.id, data["old_password"], data["new_password"], validators)
        except ValidationError as err:
            if err.error_dict:
                for name, messages in err.error_dict.items():
                    form.add_error(name if name in form.fields else None, messages)
            else:
                form.add_error(None, err)
            form.show_errors()
            return
        form.clear()
        notify(page, _("Your password was changed."))

    return ft.Container(
        expand=True,
        padding=10,
        content=ft.Column(
            [
                ft.Text(_("Change password"), size=20),
                ft.Divider(),
                ft.Container(form.control, width=460),
                ft.Button(_("Change password"), icon=ft.Icons.LOCK_RESET, on_click=submit, key="password_change"),
            ],
            spacing=12,
            scroll=ft.ScrollMode.AUTO,
        ),
    )


def build_password_reset_view(page: ft.Page, service=None, on_back: Optional[Callable[[], None]] = None,
                              title: str = "") -> ft.Control:
    """
    Recuperar la contraseña en dos pasos: pedir el código (usuario o correo) y
    luego escribir el código y la nueva contraseña.
    """
    from fletbatteries.auth.reset import PasswordResetService
    from fletbatteries.forms.validators import ValidationError

    if service is None:
        service = PasswordResetService(validators=_app_option(page, "password_validators"),
                                       app_name=_app_option(page, "title", "") or "")
    identifier = ft.TextField(label=_("Username or email"), prefix_icon=ft.Icons.PERSON, key="reset_identifier")
    info = ft.Text("", visible=False, key="reset_info")
    error = ft.Text("", color=ft.Colors.ERROR, visible=False, key="reset_error")
    code = ft.TextField(label=_("Code"), prefix_icon=ft.Icons.PIN, key="reset_code", max_length=12)
    new_password = ft.TextField(label=_("New password"), password=True, can_reveal_password=True,
                                key="reset_new_password")
    confirm = ft.TextField(label=_("Confirm new password"), password=True, can_reveal_password=True,
                           key="reset_confirm")
    step2 = ft.Column([code, new_password, confirm], tight=True, spacing=12, visible=False)
    send_button = ft.Button(_("Send code"), icon=ft.Icons.SEND, key="reset_send")
    change_button = ft.Button(_("Change password"), icon=ft.Icons.LOCK_RESET, key="reset_submit", visible=False)
    done = {"value": False}

    def show(message: str = "", problem: str = ""):
        info.value, info.visible = message, bool(message)
        error.value, error.visible = problem, bool(problem)
        safe_update(card)

    async def send(e=None):
        value = (identifier.value or "").strip()
        if not value:
            return show(problem=_("This field is required."))
        try:
            await asyncio.to_thread(service.request_reset, value)
        except Exception:
            log.exception("No se pudo enviar el código de recuperación")
            return show(problem=_("The code could not be sent. Try again later."))
        step2.visible = True
        change_button.visible = True
        send_button.content = _("Send another code")
        show(_("If the account exists and has an email, we sent a code to it."))

    def change(e=None):
        for field in (code, new_password, confirm):
            field.error = None
        try:
            service.confirm_reset((identifier.value or "").strip(), code.value or "", new_password.value or "",
                                  confirm=confirm.value or "")
        except ValidationError as err:
            fields = {"code": code, "new_password": new_password, "confirm": confirm}
            general = []
            for name, messages in (err.error_dict or {"__all__": err.messages}).items():
                if name in fields:
                    fields[name].error = " ".join(messages)
                else:
                    general.extend(messages)
            return show(problem=" ".join(general))
        done["value"] = True
        step2.visible = change_button.visible = send_button.visible = identifier.visible = False
        show(_("Your password was changed. You can now log in."))

    send_button.on_click = send
    change_button.on_click = change
    back = ft.TextButton(_("Back to login"), icon=ft.Icons.ARROW_BACK, key="reset_back",
                         on_click=lambda e: on_back() if on_back else page.navigate("/login"))
    card = ft.Card(
        content=ft.Container(
            padding=24,
            width=420,
            content=ft.Column(
                [ft.Text(_("Reset password"), size=20, weight=ft.FontWeight.BOLD),
                 ft.Text(_("We will send a code to the email of your account."), size=12),
                 identifier, send_button, info, error, step2, change_button, back],
                tight=True,
                spacing=14,
                horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            ),
        ),
    )
    header = [ft.Text(title, size=22, weight=ft.FontWeight.BOLD)] if title else []
    return ft.Container(
        expand=True,
        alignment=ft.Alignment.CENTER,
        content=ft.Column([*header, card], tight=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                          alignment=ft.MainAxisAlignment.CENTER, scroll=ft.ScrollMode.AUTO),
    )


class ApiTokenForm(forms.Form):
    title = _("API token")
    name = forms.CharField(label=_("Name"), max_length=100, help_text=_("What or who will use this token"))
    days = forms.IntegerField(label=_("Expires in (days)"), required=False, min_value=1, list_display=False,
                              help_text=_("Leave empty so it does not expire"))
    prefix = forms.CharField(label=_("Prefix"), required=False, disabled=True)
    created_at = forms.DateTimeField(label=_("Created"), required=False, disabled=True)
    last_used_at = forms.DateTimeField(label=_("Last used"), required=False, disabled=True)
    expires_at = forms.DateTimeField(label=_("Expires"), required=False, disabled=True)
    revoked = forms.BooleanField(label=_("Revoked"), disabled=True)


class ApiTokenCRUD(CRUDView):
    """Tokens del API del usuario de la sesión: crear (se muestra una vez) y revocar."""

    title = _("API tokens")
    name = _("token")
    form_class = ApiTokenForm
    actions = ("create", "delete")
    list_fields = ["name", "prefix", "created_at", "last_used_at", "expires_at", "revoked"]
    order_by = "-created_at"
    route = "/account/tokens"
    icon = ft.Icons.KEY

    def __init__(self, page: ft.Page, **options):
        user = get_user(page)
        options.setdefault("fixed_filters", {"user_id": user.id if user else -1})
        super().__init__(page, **options)

    def get_source(self):
        from fletbatteries.auth.tokens import ApiTokenManager

        return SQLAlchemySource(ApiTokenManager())

    def get_form(self, item=None):
        form = super().get_form(item)
        if item is None:
            for name in ("prefix", "created_at", "last_used_at", "expires_at", "revoked"):
                form.fields.pop(name, None)
        return form

    def open_delete(self, item: dict):
        self.modal.open(
            kind="delete",
            title=_("Revoke token"),
            content_controls=[ft.Text(_("Programs using this token will stop working.")),
                              ft.Text(self.source.to_label(item), weight=ft.FontWeight.BOLD)],
            on_accept=lambda: self.delete(item),
            success_text=_("Token revoked"),
            accept_text=_("Revoke"),
            width=self.modal_width,
        )

    def save(self, form, item):
        from fletbatteries.auth.tokens import ApiTokenManager

        if not form.is_valid():
            return None
        user = get_user(self.page)
        if user is None or UserManager().get(user.id) is None:
            form.add_error(None, _("Your account cannot create API tokens."))
            form.show_errors()
            return None
        raw = ApiTokenManager().issue(user.id, form.cleaned_data["name"], days=form.cleaned_data.get("days"))
        self.reload()
        self.page.run_task(self._show_token, raw)
        return True

    async def _show_token(self, raw: str):
        await asyncio.sleep(0.1)
        field = ft.TextField(value=raw, read_only=True, key="api_token_value", multiline=True)

        async def copy(e):
            await ft.Clipboard().set(raw)
            notify(self.page, _("Copied to clipboard"))

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(_("New API token")),
            content=ft.Container(width=520, content=ft.Column(
                [ft.Text(_("Copy the token now: it will not be shown again.")), field], tight=True, spacing=12)),
        )
        from fletbatteries.utils import close_dialog

        dialog.actions = [ft.TextButton(_("Copy"), icon=ft.Icons.COPY, on_click=copy, key="api_token_copy"),
                          ft.Button(_("Close"), on_click=lambda e: close_dialog(dialog), key="api_token_close")]
        self.page.show_dialog(dialog)
