"""
Pruebas de la librería sin la demo: usan sus propios modelos (`tests_lib.models`)
y una SQLite temporal por prueba. No importan nada de `demo/`.
"""

import flet as ft
import pytest

from fletbatteries.data import db as fb_db
from fletbatteries.data.db import Database, import_models

from tests_lib.models import LibBase


@pytest.fixture
def db(tmp_path):
    """Base de datos temporal (tablas del framework + las de prueba) como base por defecto."""
    from fletbatteries.contrib import email, settings

    previous = fb_db._default
    database = Database(f"sqlite:///{tmp_path / 'lib.db'}")
    import_models()
    fb_db.Base.metadata.create_all(bind=database.engine)
    LibBase.metadata.create_all(bind=database.engine)
    fb_db.set_default_database(database)
    settings.clear_settings_cache()
    outbox = email.MemoryBackend()
    email.configure_email(outbox)
    try:
        yield database
    finally:
        email.configure_email(None)
        settings.clear_settings_cache()
        fb_db._default = previous
        database.engine.dispose()


@pytest.fixture
def outbox(db):
    from fletbatteries.contrib.email import get_email_backend

    return get_email_backend().outbox


@pytest.fixture
def admin(db):
    from fletbatteries.auth.backend import UserManager

    return UserManager().create_superuser("root", "S3guro-root!", email="root@example.com", first_name="Root")


def build_app(**options):
    """App mínima con los CRUDs de prueba y las vistas del framework."""
    from fletbatteries.app import FletBatteriesApp

    from tests_lib.models import ItemManager
    from tests_lib.views import DocCRUD, ItemCRUD

    app = FletBatteriesApp(title="Lib", **options)
    app.add_view("/", lambda page: ft.Text("Inicio lib"), title="Inicio", icon=ft.Icons.HOME)
    app.add_crud(ItemCRUD, "/items", title="Items", icon=ft.Icons.LIST, badge=lambda page: ItemManager().count())
    app.add_crud(DocCRUD, "/docs", title="Docs", icon=ft.Icons.DESCRIPTION)
    app.add_account_views(password_reset=True)
    app.add_admin_views()
    return app


@pytest.fixture
async def lib_app(admin):
    """Harness con la app mínima y el superusuario `root` ya en la sesión."""
    from fletbatteries.auth import login
    from fletbatteries.auth.backend import to_auth_user

    from tests.harness import AppHarness

    app = build_app()
    harness = AppHarness(app.main)
    await harness.start()
    login(harness.page, to_auth_user(admin))
    await harness.goto("/")
    harness.fb_app = app
    yield harness
    await harness.stop()


async def start_app(app, route: str = "/"):
    from tests.harness import AppHarness

    harness = AppHarness(app.main, route=route)
    await harness.start()
    harness.fb_app = app
    return harness
