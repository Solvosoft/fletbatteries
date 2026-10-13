import os
import tempfile
from pathlib import Path
from urllib.parse import urlsplit

import pytest

# La base de datos de pruebas debe configurarse antes de importar `settings`
_TMP_DIR = tempfile.mkdtemp(prefix="fletbatteries-tests-")
os.environ["FLETBATTERIES_DB_URL"] = f"sqlite:///{Path(_TMP_DIR) / 'test.db'}"
os.environ["FLETBATTERIES_API_URL"] = "http://testserver"

import requests  # noqa: E402

from tests.harness import AppHarness  # noqa: E402


def _create_schema():
    import scripts.init_db as init_db

    init_db.db.create_db()
    init_db.seed()


_create_schema()


@pytest.fixture(scope="session")
def api_client():
    from fastapi.testclient import TestClient

    from scripts.api import app

    with TestClient(app) as client:  # ejecuta el startup (datos iniciales)
        yield client


@pytest.fixture(autouse=True)
def route_requests_to_api(monkeypatch, api_client):
    """Las vistas que usan `requests` contra la API consultan el TestClient."""

    def make(method):
        def call(url, **kwargs):
            parts = urlsplit(url)
            path = parts.path + (f"?{parts.query}" if parts.query else "")
            kwargs.pop("timeout", None)
            return getattr(api_client, method)(path, **kwargs)

        return call

    for method in ("get", "post", "put", "delete", "patch"):
        monkeypatch.setattr(requests, method, make(method))


@pytest.fixture
async def app():
    from main import main

    harness = AppHarness(main)
    await harness.start()
    yield harness
    await harness.stop()


@pytest.fixture
async def logged_app(app):
    """App con un superusuario en la sesión, ya en la vista de inicio."""
    from fletbatteries.auth import AuthUser, login

    login(app.page, AuthUser(id=1, username="admin", is_superuser=True))
    await app.goto("/")
    return app
