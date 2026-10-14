"""
Autenticación contra la base de datos y managers de usuarios, grupos y permisos.

`DatabaseAuthBackend` registra cada intento de ingreso en `fb_login_attempts`
y bloquea al usuario por `lockout_minutes` después de `max_attempts` fallos
seguidos (`max_attempts=None` lo desactiva).
"""

import datetime
from typing import Iterable, Optional, Sequence

import sqlalchemy as sa

from fletbatteries.auth.models import Group, LoginAttempt, Permission, User
from fletbatteries.auth.passwords import hash_password, verify_password
from fletbatteries.auth.session import AuthUser
from fletbatteries.data.manager import BaseManager
from fletbatteries.i18n import _


class AuthError(Exception):
    """Ingreso rechazado con un mensaje para el usuario (p. ej. cuenta bloqueada)."""


class PermissionManager(BaseManager):
    model = Permission
    search_fields = ("codename", "name", "category")
    unique_fields = ("codename",)
    default_order = "codename"

    def ensure(self, codename: str, name: Optional[str] = None, category: Optional[str] = None) -> Permission:
        """Crea el permiso si no existe."""
        existing = self.first(codename=codename)
        if existing is not None:
            return existing
        return self.create(codename=codename, name=name or codename, category=category or codename.split(".")[0])

    def ensure_many(self, perms: Iterable) -> list[Permission]:
        result = []
        for perm in perms:
            if isinstance(perm, str):
                result.append(self.ensure(perm))
            else:
                result.append(self.ensure(*perm))
        return result


class GroupManager(BaseManager):
    model = Group
    search_fields = ("name",)
    unique_fields = ("name",)
    default_order = "name"


class UserManager(BaseManager):
    model = User
    search_fields = ("username", "first_name", "last_name", "email")
    unique_fields = ("username",)
    default_order = "username"

    def before_save(self, s, obj, data, created):
        # La contraseña se guarda con hash; vacía al editar = no cambiarla
        password = data.get("password")
        if password:
            data["password"] = hash_password(password)
        else:
            data.pop("password", None)

    def to_dict(self, obj) -> dict:
        data = super().to_dict(obj)
        data.pop("password", None)
        return data

    def create_user(self, username: str, password: str, **extra) -> User:
        return self.create(username=username, password=password, **extra)

    def create_superuser(self, username: str, password: str, **extra) -> User:
        return self.create(username=username, password=password, is_superuser=True, **extra)

    def get_by_username(self, username: str) -> Optional[User]:
        return self.first(username=username)

    def get_by_username_or_email(self, identifier: str) -> Optional[User]:
        identifier = (identifier or "").strip()
        if not identifier:
            return None
        return self.first(__or__=[{"username": identifier}, {"email__iexact": identifier}])

    def set_password(self, user_id, password: str):
        """Cambia la contraseña sin validar la anterior (recuperación, administración)."""
        self.update(user_id, password=password)

    def change_password(self, user_id, old_password: str, new_password: str, validators: Optional[Sequence] = None):
        """
        Cambia la contraseña del usuario si `old_password` es correcta. Lanza
        `ValidationError({campo: mensajes})` si algo no es válido.
        """
        from fletbatteries.auth.password_validation import validate_password
        from fletbatteries.forms.validators import ValidationError

        user = self.get(user_id)
        if user is None or not verify_password(old_password, user.password):
            raise ValidationError({"old_password": [_("Your old password was entered incorrectly.")]})
        try:
            validate_password(new_password, user, validators)
        except ValidationError as e:
            raise ValidationError({"new_password": e.messages})
        self.set_password(user_id, new_password)


class LoginAttemptManager(BaseManager):
    model = LoginAttempt
    search_fields = ("username", "reason")
    default_order = "-created_at"

    def record(self, username: str, success: bool, reason: Optional[str] = None):
        return self.create(username=(username or "")[:150], success=success, reason=reason)

    def recent_failures(self, username: str, minutes: int) -> list:
        """Fallos seguidos (desde el último ingreso exitoso) dentro de los últimos `minutes`."""
        since = datetime.datetime.now() - datetime.timedelta(minutes=minutes)
        with self.session() as s:
            last_ok = s.scalar(sa.select(sa.func.max(LoginAttempt.created_at)).where(
                LoginAttempt.username == username, LoginAttempt.success.is_(True)))
            stmt = sa.select(LoginAttempt).where(
                LoginAttempt.username == username, LoginAttempt.success.is_(False),
                LoginAttempt.created_at >= since)
            if last_ok is not None:
                stmt = stmt.where(LoginAttempt.created_at > last_ok)
            return list(s.scalars(stmt.order_by(LoginAttempt.created_at)))

    def clear_failures(self, username: str):
        """Desbloquea al usuario (p. ej. después de recuperar la contraseña)."""
        self.record(username, True, "unlocked")


def permissions_of(user: User) -> frozenset:
    perms = {p.codename for p in user.permissions}
    for group in user.groups:
        perms.update(p.codename for p in group.permissions)
    return frozenset(perms)


def to_auth_user(user: User) -> AuthUser:
    return AuthUser(
        id=user.id,
        username=user.username,
        is_superuser=bool(user.is_superuser),
        permissions=permissions_of(user),
        first_name=user.first_name or "",
        last_name=user.last_name or "",
        email=user.email or "",
    )


class DatabaseAuthBackend:
    """Valida usuario y contraseña contra `fb_users`, con bloqueo por intentos fallidos."""

    def __init__(self, manager: Optional[UserManager] = None, max_attempts: Optional[int] = 5,
                 lockout_minutes: int = 15, record_attempts: bool = True):
        self.manager = manager or UserManager()
        self.max_attempts = max_attempts
        self.lockout_minutes = lockout_minutes
        self.record_attempts = record_attempts
        self.attempts = LoginAttemptManager()

    def locked_minutes(self, username: str) -> int:
        """Minutos que faltan para desbloquear al usuario (0 si no está bloqueado)."""
        if not self.max_attempts:
            return 0
        failures = self.attempts.recent_failures(username, self.lockout_minutes)
        if len(failures) < self.max_attempts:
            return 0
        unlock = failures[-1].created_at + datetime.timedelta(minutes=self.lockout_minutes)
        remaining = (unlock - datetime.datetime.now()).total_seconds()
        return max(1, int(-(-remaining // 60))) if remaining > 0 else 0

    def _record(self, username: str, success: bool, reason: Optional[str] = None):
        if self.record_attempts:
            self.attempts.record(username, success, reason)

    def authenticate(self, username: str, password: str) -> Optional[AuthUser]:
        """
        Devuelve el usuario si las credenciales son válidas, `None` si no, o
        lanza `AuthError` si el usuario está bloqueado por intentos fallidos.
        """
        username = (username or "").strip()
        minutes = self.locked_minutes(username) if username else 0
        if minutes:
            self._record(username, False, "locked")
            raise AuthError(_("Too many failed attempts. Try again in {minutes} minutes.", minutes=minutes))
        user = self.manager.get_by_username(username)
        if user is None or not user.is_active or not verify_password(password, user.password):
            reason = "unknown_user" if user is None else "inactive" if not user.is_active else "bad_password"
            self._record(username, False, reason)
            return None
        self._record(username, True)
        self.manager.update(user.id, last_login=datetime.datetime.now())
        return to_auth_user(self.manager.get(user.id))

    def get_user(self, user_id) -> Optional[AuthUser]:
        """Usuario actualizado (permisos incluidos) o `None` si ya no existe o está inactivo."""
        user = self.manager.get(user_id)
        if user is None or not user.is_active:
            return None
        return to_auth_user(user)
