#!/usr/bin/env python3

import sys

# Modelos de fletbatteries (usuarios, configuración, notificaciones, ayuda, historial, papelera)
import fletbatteries.auth.models  # noqa: F401
import fletbatteries.contrib.help  # noqa: F401
import fletbatteries.contrib.history  # noqa: F401
import fletbatteries.contrib.notifications  # noqa: F401
import fletbatteries.contrib.settings  # noqa: F401

from fletbatteries.data import migrations

from data.manager.db_manager import DatabaseManager

# Modelos de la demo
from data.models.user import User  # noqa: F401
from data.models.product import Product  # noqa: F401
from data.models.customer import Customer  # noqa: F401
from data.models.country import Country  # noqa: F401
from data.models.person import Person  # noqa: F401
from data.models.community import Community  # noqa: F401
from data.models.person_group import PersonGroup  # noqa: F401
from data.models.abc import ABC  # noqa: F401
from data.models.calendar_event import Event  # noqa: F401
from data.models.note import Note  # noqa: F401

db = DatabaseManager()

# Usuario y permisos de la demo (solo para desarrollo: cambie la contraseña)
DEMO_ADMIN = ("admin", "admin")
DEMO_PERMISSIONS = [
    ("auth.manage", "Administrar usuarios y permisos"),
    ("help.change", "Editar los textos de ayuda"),
]


def seed():
    from fletbatteries.auth.backend import PermissionManager, UserManager

    PermissionManager().ensure_many(DEMO_PERMISSIONS)
    users = UserManager()
    if users.get_by_username(DEMO_ADMIN[0]) is None:
        users.create_superuser(*DEMO_ADMIN, first_name="Admin")


def main():
    if len(sys.argv) != 2:
        print("Uso: python init_db.py [create_db | reset_db | update_schema]")
        return

    cmd = sys.argv[1]

    if cmd == "create_db":
        db.create_db()
        # La BD nueva ya tiene el esquema completo: se marca con la última migración
        migrations.stamp("head")
        seed()
    elif cmd == "reset_db":
        confirm = input("⚠️ Esto eliminará todos los datos. ¿Estás seguro? (s/n): ")
        if confirm.lower() == "s":
            db.reset_db()
            migrations.stamp("head")
            seed()
    elif cmd == "update_schema":
        migrations.migrate("head")
        seed()
    else:
        print(f"Comando desconocido: {cmd}")


if __name__ == "__main__":
    main()
