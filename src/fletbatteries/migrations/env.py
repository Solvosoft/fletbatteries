"""`env.py` genérico de Alembic para FletBatteries (ver `fletbatteries.data.migrations`)."""

from alembic import context

from fletbatteries.data.migrations import run_env

run_env(context)
