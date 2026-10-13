"""
Autenticación y permisos.

- `login(page, user)`, `logout(page)`, `get_user(page)`, `has_perm(page, perm)`: sesión de Flet.
- `DatabaseAuthBackend().authenticate(username, password)`: usuarios en la base de datos.
- `UserManager`, `GroupManager`, `PermissionManager`: administración.
"""

from fletbatteries.auth.passwords import hash_password, verify_password  # noqa: F401
from fletbatteries.auth.session import AuthUser, get_user, has_perm, has_perms, login, logout  # noqa: F401


def __getattr__(name):
    # Carga perezosa: los modelos solo se importan si se usan
    if name in ("DatabaseAuthBackend", "UserManager", "GroupManager", "PermissionManager", "to_auth_user"):
        from fletbatteries.auth import backend

        return getattr(backend, name)
    if name in ("User", "Group", "Permission"):
        from fletbatteries.auth import models

        return getattr(models, name)
    raise AttributeError(name)
