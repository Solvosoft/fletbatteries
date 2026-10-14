"""
Tokens del API (opacos, guardados como hash en `fb_api_tokens`).

    raw = ApiTokenManager().issue(user_id, "Script de reportes", days=90)   # se muestra una sola vez
    user = authenticate_token(raw)                                         # AuthUser o None

El token tiene la forma `fbt_<prefijo>_<secreto>`; el prefijo sirve para
reconocerlo en la lista sin mostrar el secreto. Revocar marca `revoked`.
"""

import datetime
import hashlib
import hmac
import secrets
from typing import Optional

from fletbatteries.auth.models import ApiToken
from fletbatteries.auth.session import AuthUser
from fletbatteries.data.manager import BaseManager

TOKEN_PREFIX = "fbt"


def hash_token(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


class ApiTokenManager(BaseManager):
    model = ApiToken
    search_fields = ("name", "prefix")
    default_order = "-created_at"

    def to_dict(self, obj) -> dict:
        data = super().to_dict(obj)
        data.pop("key_hash", None)
        data.pop("user", None)
        return data

    def issue(self, user_id, name: str, days: Optional[int] = None) -> str:
        """Crea un token y devuelve el valor completo (no se puede volver a consultar)."""
        prefix = secrets.token_hex(4)
        raw = f"{TOKEN_PREFIX}_{prefix}_{secrets.token_urlsafe(32)}"
        expires = datetime.datetime.now() + datetime.timedelta(days=days) if days else None
        self.create(user_id=user_id, name=name, prefix=prefix, key_hash=hash_token(raw), expires_at=expires)
        return raw

    def revoke(self, pk) -> bool:
        if self.get(pk) is None:
            return False
        self.update(pk, revoked=True)
        return True

    def revoke_raw(self, raw: str) -> bool:
        token = self.first(key_hash=hash_token(raw or ""))
        return self.revoke(token.id) if token is not None else False

    def perform_delete(self, s, obj):
        # Borrar un token = revocarlo (queda el registro)
        obj.revoked = True

    def find_valid(self, raw: str) -> Optional[ApiToken]:
        if not raw or not raw.startswith(f"{TOKEN_PREFIX}_"):
            return None
        digest = hash_token(raw)
        token = self.first(key_hash=digest)
        if token is None or token.revoked or not hmac.compare_digest(token.key_hash, digest):
            return None
        if token.expires_at is not None and token.expires_at < datetime.datetime.now():
            return None
        return token


def authenticate_token(raw: str, touch: bool = True) -> Optional[AuthUser]:
    """Usuario dueño del token (con sus permisos actuales) o `None` si el token no es válido."""
    from fletbatteries.auth.backend import UserManager, to_auth_user

    manager = ApiTokenManager()
    token = manager.find_valid(raw)
    if token is None:
        return None
    user = UserManager().get(token.user_id)
    if user is None or not user.is_active:
        return None
    if touch:
        manager.update(token.id, last_used_at=datetime.datetime.now())
    return to_auth_user(user)
