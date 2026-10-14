"""
Autenticación del API con tokens (`Authorization: Bearer <token>`).

    from fletbatteries.api import auth_router, crud_router, current_api_user, require_perms

    app.include_router(auth_router(prefix="/api/auth"))      # POST /token, DELETE /token
    app.include_router(crud_router(CustomerManager(), prefix="/api/customers", auth=True, perms="customers"))

    @app.get("/api/me")
    def me(user=Depends(current_api_user)):
        return {"username": user.username}

Los tokens se crean con `ApiTokenManager().issue(user_id, name)`, desde la
vista `/account/tokens` o con `POST /token` (usuario y contraseña; pasa por el
bloqueo por intentos fallidos del backend de la base de datos).
"""

from typing import Iterable, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from fletbatteries.auth.session import AuthUser


def _bearer(request: Request) -> Optional[str]:
    header = request.headers.get("Authorization") or ""
    scheme, _sep, token = header.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        return None
    return token.strip()


def current_api_user(request: Request) -> AuthUser:
    """Dependencia de FastAPI: usuario dueño del token o 401."""
    from fletbatteries.auth.tokens import authenticate_token

    cached = getattr(request.state, "fb_user", None)
    if cached is not None:
        return cached
    raw = _bearer(request)
    user = authenticate_token(raw) if raw else None
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid or missing token",
                            headers={"WWW-Authenticate": "Bearer"})
    request.state.fb_user = user
    return user


def require_perms(*perms: str, any_perm: bool = False):
    """Dependencia que exige un token válido y los permisos indicados (403 si faltan)."""
    wanted = [p for p in perms if p]

    def dependency(user: AuthUser = Depends(current_api_user)) -> AuthUser:
        if wanted and not user.has_perms(wanted, any_perm=any_perm):
            raise HTTPException(status_code=403, detail="Permission denied")
        return user

    return dependency


class TokenRequest(BaseModel):
    username: str
    password: str
    name: str = "API"
    days: Optional[int] = None


def auth_router(prefix: str = "/auth", tags: Optional[Iterable[str]] = None, backend=None) -> APIRouter:
    """
    `POST {prefix}/token` crea un token con usuario y contraseña;
    `DELETE {prefix}/token` revoca el token enviado en el header.
    """
    router = APIRouter(prefix=prefix, tags=list(tags or ["auth"]))

    @router.post("/token", status_code=201)
    def create_token(payload: TokenRequest):
        from fletbatteries.auth.backend import AuthError, DatabaseAuthBackend
        from fletbatteries.auth.tokens import ApiTokenManager

        auth_backend = backend or DatabaseAuthBackend()
        try:
            user = auth_backend.authenticate(payload.username, payload.password)
        except AuthError as e:
            raise HTTPException(status_code=429, detail=str(e))
        if user is None:
            raise HTTPException(status_code=401, detail="Invalid username or password")
        raw = ApiTokenManager().issue(user.id, payload.name, days=payload.days)
        return {"token": raw, "token_type": "bearer"}

    @router.delete("/token")
    def revoke_token(request: Request, user: AuthUser = Depends(current_api_user)):
        from fletbatteries.auth.tokens import ApiTokenManager

        ApiTokenManager().revoke_raw(_bearer(request))
        return {"revoked": True}

    @router.get("/me")
    def me(user: AuthUser = Depends(current_api_user)):
        return {"id": user.id, "username": user.username, "is_superuser": user.is_superuser,
                "permissions": sorted(user.permissions)}

    return router
