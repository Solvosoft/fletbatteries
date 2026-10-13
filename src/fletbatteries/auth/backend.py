"""Autenticación contra la base de datos y managers de usuarios, grupos y permisos."""

import datetime
from typing import Iterable, Optional

from fletbatteries.auth.models import Group, Permission, User
from fletbatteries.auth.passwords import hash_password, verify_password
from fletbatteries.auth.session import AuthUser
from fletbatteries.data.manager import BaseManager


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
    """Valida usuario y contraseña contra `fb_users`."""

    def __init__(self, manager: Optional[UserManager] = None):
        self.manager = manager or UserManager()

    def authenticate(self, username: str, password: str) -> Optional[AuthUser]:
        user = self.manager.get_by_username((username or "").strip())
        if user is None or not user.is_active or not verify_password(password, user.password):
            return None
        self.manager.update(user.id, last_login=datetime.datetime.now())
        return to_auth_user(self.manager.get(user.id))
