import os
from pathlib import Path

from dotenv import load_dotenv

from fletbatteries.data import set_default_database

SRC_DIR = Path(__file__).resolve().parent
BASE_DIR = SRC_DIR.parent
ASSETS_DIR = SRC_DIR / "assets"

load_dotenv(BASE_DIR / ".env")

DB_URL = os.environ.get("FLETBATTERIES_DB_URL", f"sqlite:///{BASE_DIR / 'template.db'}")
API_URL = os.environ.get("FLETBATTERIES_API_URL", "http://127.0.0.1:8000").rstrip("/") + "/"
# Permite abrir "/" directamente sin pasar por el login (útil para capturas/demos)
SKIP_LOGIN = os.environ.get("FLETBATTERIES_SKIP_LOGIN", "").lower() in ("1", "true", "yes")

# Base de datos que usan los managers de fletbatteries
DATABASE = set_default_database(DB_URL)
