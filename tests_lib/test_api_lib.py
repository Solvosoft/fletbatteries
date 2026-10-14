"""API con tokens: auth_router y crud_router(auth=True, perms=...)."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from fletbatteries.api import auth_router, crud_router
from fletbatteries.auth.backend import PermissionManager, UserManager
from fletbatteries.auth.tokens import ApiTokenManager
from fletbatteries.data import APISource, Query
from fletbatteries.forms.validators import ValidationError

from tests_lib.models import CategoryManager


@pytest.fixture
def client(db):
    app = FastAPI()
    app.include_router(auth_router(prefix="/api/auth"))
    app.include_router(crud_router(CategoryManager(), prefix="/api/categories", auth=True, perms="categories"))
    app.include_router(crud_router(CategoryManager(), prefix="/api/open"))
    with TestClient(app) as c:
        yield c


@pytest.fixture
def reader(db):
    perms = PermissionManager().ensure_many(["categories.view"])
    return UserManager().create_user("lector", "Lector-clave-1", permissions=[p.id for p in perms])


def bearer(token):
    return {"Authorization": f"Bearer {token}"}


def test_token_auth_and_permissions(client, admin, reader):
    CategoryManager().create(name="Libros")
    assert client.get("/api/categories").status_code == 401
    assert client.get("/api/categories", headers=bearer("fbt_mal_token")).status_code == 401
    # Token por usuario y contraseña
    assert client.post("/api/auth/token", json={"username": "lector", "password": "mala"}).status_code == 401
    response = client.post("/api/auth/token", json={"username": "lector", "password": "Lector-clave-1",
                                                     "name": "cli"})
    assert response.status_code == 201
    token = response.json()["token"]
    assert client.get("/api/auth/me", headers=bearer(token)).json()["permissions"] == ["categories.view"]
    listing = client.get("/api/categories", headers=bearer(token))
    assert listing.status_code == 200 and listing.json()["total"] == 1
    # Sin permiso de crear
    assert client.post("/api/categories", json={"name": "X"}, headers=bearer(token)).status_code == 403
    # El superusuario puede todo
    admin_token = ApiTokenManager().issue(admin.id, "admin")
    created = client.post("/api/categories", json={"name": "Música"}, headers=bearer(admin_token))
    assert created.status_code == 201
    # Errores de validación por campo
    dup = client.post("/api/categories", json={"name": "Música"}, headers=bearer(admin_token))
    assert dup.status_code == 400 and "name" in dup.json()["detail"]["errors"]
    # Revocar
    assert client.delete("/api/auth/token", headers=bearer(token)).status_code == 200
    assert client.get("/api/categories", headers=bearer(token)).status_code == 401
    # El router sin auth sigue abierto
    assert client.get("/api/open").status_code == 200


def test_token_endpoint_respects_lockout(client, admin):
    for _i in range(5):
        client.post("/api/auth/token", json={"username": "root", "password": "mala"})
    locked = client.post("/api/auth/token", json={"username": "root", "password": "S3guro-root!"})
    assert locked.status_code == 429


def test_api_source_with_token(client, admin, reader):
    CategoryManager().create(name="Arte")

    class Session:
        def __getattr__(self, method):
            def call(url, **kwargs):
                kwargs.pop("timeout", None)
                return getattr(client, method)(url.replace("http://testserver", ""), **kwargs)

            return call

    anonymous = APISource("http://testserver/api/categories", session=Session())
    with pytest.raises(PermissionError):
        anonymous.list(Query())
    source = APISource("http://testserver/api/categories", session=Session(),
                       token=ApiTokenManager().issue(admin.id, "ui"))
    assert source.list(Query()).total == 1
    with pytest.raises(ValidationError) as info:
        source.create({"name": "Arte"})
    assert "name" in info.value.error_dict
    with pytest.raises(ValueError):
        source.list(Query(filters={"__or__": [{"name": "x"}]}))
