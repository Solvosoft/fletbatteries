"""
Línea de comandos de FletBatteries.

    fletbatteries init                         # crea la carpeta de migraciones
    fletbatteries makemigrations -m "mensaje"  # nueva revisión (autogenerada)
    fletbatteries migrate [revisión]           # aplica las migraciones (head por defecto)
    fletbatteries downgrade <revisión>
    fletbatteries stamp [revisión]             # marca una BD creada con create_all
    fletbatteries check                        # falla si los modelos tienen cambios sin migrar
    fletbatteries current
    fletbatteries createdb                     # create_all + stamp head (BD nueva)
    fletbatteries createsuperuser --username admin --email admin@example.com

Opciones comunes: `--db-url`, `--models a.models,b.models`, `--setup app.settings`,
`--migrations-dir`, `--pythonpath`. Si no se indican se leen del entorno o de
`[tool.fletbatteries]` en el `pyproject.toml` (ver `fletbatteries.data.migrations`).
También se puede ejecutar como `python -m fletbatteries`.
"""

import argparse
import getpass
import sys
from typing import Optional, Sequence


def _config(args):
    from fletbatteries.data.migrations import load_config

    def split(value):
        return [v.strip() for v in value.split(",") if v.strip()] if value is not None else None

    return load_config(db_url=args.db_url, models=split(args.models), setup=split(args.setup),
                       migrations_dir=args.migrations_dir, pythonpath=split(args.pythonpath))


def cmd_init(args):
    from fletbatteries.data import migrations

    path = migrations.init(_config(args))
    print(f"Carpeta de migraciones: {path}")


def cmd_makemigrations(args):
    from fletbatteries.data import migrations

    script = migrations.makemigrations(args.message, _config(args), autogenerate=not args.empty,
                                       empty_ok=args.empty)
    print(f"Revisión creada: {script.path}" if script is not None else "Sin cambios en los modelos.")


def cmd_migrate(args):
    from fletbatteries.data import migrations

    migrations.migrate(args.revision, _config(args))
    print(f"Base de datos en {args.revision}")


def cmd_downgrade(args):
    from fletbatteries.data import migrations

    migrations.downgrade(args.revision, _config(args))


def cmd_stamp(args):
    from fletbatteries.data import migrations

    migrations.stamp(args.revision, _config(args))
    print(f"Base de datos marcada en {args.revision}")


def cmd_check(args):
    from fletbatteries.data import migrations

    diffs = migrations.check(_config(args))
    if diffs:
        print("Hay cambios en los modelos sin migración:")
        for diff in diffs:
            print(f"  {diff}")
        return 1
    print("El esquema coincide con los modelos.")
    return 0


def cmd_current(args):
    from fletbatteries.data import migrations

    print(migrations.current(_config(args)) or "(sin migraciones aplicadas)")


def cmd_createdb(args):
    from fletbatteries.data import Database, migrations

    config = _config(args)
    url = migrations.prepare(config)
    Database(url).create_all()
    if any(config.versions_path.glob("*.py")):
        migrations.stamp("head", config)
    print("Tablas creadas.")


def cmd_createsuperuser(args):
    from fletbatteries.auth.backend import UserManager
    from fletbatteries.data import migrations, set_default_database

    url = migrations.prepare(_config(args))
    set_default_database(url)
    username = args.username or input("Usuario: ").strip()
    password = args.password or getpass.getpass("Contraseña: ")
    users = UserManager()
    if users.get_by_username(username) is not None:
        print(f"El usuario {username} ya existe.")
        return 1
    users.create_superuser(username, password, email=args.email or None)
    print(f"Superusuario {username} creado.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="fletbatteries", description="Herramientas de FletBatteries")
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--db-url")
    common.add_argument("--models", help="módulos de modelos separados por coma")
    common.add_argument("--setup", help="módulos a importar antes (configuración), separados por coma")
    common.add_argument("--migrations-dir")
    common.add_argument("--pythonpath", help="rutas extra separadas por coma")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("init", parents=[common], help="crear la carpeta de migraciones").set_defaults(func=cmd_init)
    p = sub.add_parser("makemigrations", parents=[common], help="crear una revisión")
    p.add_argument("-m", "--message", default="auto")
    p.add_argument("--empty", action="store_true", help="revisión vacía (sin autogenerar)")
    p.set_defaults(func=cmd_makemigrations)
    p = sub.add_parser("migrate", parents=[common], help="aplicar migraciones")
    p.add_argument("revision", nargs="?", default="head")
    p.set_defaults(func=cmd_migrate)
    p = sub.add_parser("downgrade", parents=[common], help="revertir migraciones")
    p.add_argument("revision")
    p.set_defaults(func=cmd_downgrade)
    p = sub.add_parser("stamp", parents=[common], help="marcar la revisión sin migrar")
    p.add_argument("revision", nargs="?", default="head")
    p.set_defaults(func=cmd_stamp)
    sub.add_parser("check", parents=[common], help="revisar cambios sin migrar").set_defaults(func=cmd_check)
    sub.add_parser("current", parents=[common], help="revisión actual").set_defaults(func=cmd_current)
    sub.add_parser("createdb", parents=[common], help="crear las tablas y marcar head").set_defaults(
        func=cmd_createdb)
    p = sub.add_parser("createsuperuser", parents=[common], help="crear un superusuario")
    p.add_argument("--username")
    p.add_argument("--password")
    p.add_argument("--email")
    p.set_defaults(func=cmd_createsuperuser)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args) or 0


if __name__ == "__main__":
    sys.exit(main())
