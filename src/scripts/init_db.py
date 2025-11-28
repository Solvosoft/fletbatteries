#!/usr/bin/env python3

import sys
from data.manager.db_manager import DatabaseManager

# importar los modelos
from data.models.user import User
from data.models.product import Product
from data.models.customer import Customer
from data.models.country import Country
from data.models.person import Person
from data.models.community import Community
from data.models.person_group import PersonGroup
from data.models.abc import ABC

db = DatabaseManager()

def main():
    if len(sys.argv) != 2:
        print("Uso: python manage.py [create_db | reset_db | update_schema]")
        return

    cmd = sys.argv[1]

    if cmd == "create_db":
        db.create_db()
    elif cmd == "reset_db":
        confirm = input("⚠️ Esto eliminará todos los datos. ¿Estás seguro? (s/n): ")
        if confirm.lower() == "s":
            db.reset_db()
    elif cmd == "update_schema":
        db.update_schema()
    else:
        print(f"Comando desconocido: {cmd}")

if __name__ == "__main__":
    main()
