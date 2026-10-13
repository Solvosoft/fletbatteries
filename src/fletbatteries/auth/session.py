"""Usuario de la sesión y verificación de permisos."""

import dataclasses
from typing import Iterable, Optional

USER_KEY = "fletbatteries.user"


@dataclasses.dataclass(frozen=True)
class AuthUser:
    """Usuario autenticado guardado en la sesión de Flet (sin sesión de base de datos)."""

    id: int
    username: str
    is_superuser: bool = False
    permissions: frozenset = frozenset()
    first_name: str = ""
    last_name: str = ""
    email: str = ""

    @property
    def display_name(self) -> str:
        full = f"{self.first_name} {self.last_name}".strip()
        return full or self.username

    def has_perm(self, perm: Optional[str]) -> bool:
        return perm is None or self.is_superuser or perm in self.permissions

    def has_perms(self, perms: Iterable[str], any_perm: bool = False) -> bool:
        perms = list(perms)
        if not perms:
            return True
        check = any if any_perm else all
        return check(self.has_perm(p) for p in perms)


def _store(page):
    return page.session.store


def get_user(page) -> Optional[AuthUser]:
    try:
        return _store(page).get(USER_KEY)
    except (AttributeError, RuntimeError):
        return None


def login(page, user: AuthUser):
    _store(page).set(USER_KEY, user)


def logout(page):
    store = _store(page)
    if store.contains_key(USER_KEY):
        store.remove(USER_KEY)


def has_perm(page, perm: Optional[str]) -> bool:
    if perm is None:
        return True
    user = get_user(page)
    return bool(user and user.has_perm(perm))


def has_perms(page, perms: Iterable[str], any_perm: bool = False) -> bool:
    perms = list(perms or [])
    if not perms:
        return True
    user = get_user(page)
    return bool(user and user.has_perms(perms, any_perm=any_perm))
