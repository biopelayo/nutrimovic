"""Configuración central de NutriMovic."""
from __future__ import annotations

from pathlib import Path

APP_NAME = "NutriMovic"
APP_VERSION = "0.1.0-dev"

# Rutas del proyecto.
BACKEND_DIR = Path(__file__).resolve().parents[2]
PROJECT_ROOT = BACKEND_DIR.parent
DATA_DIR = PROJECT_ROOT / "data"
SEED_DIR = DATA_DIR / "seed"
RAW_DIR = DATA_DIR / "raw"
DB_PATH = DATA_DIR / "nutrimovic.sqlite"

# Fichero oficial de CIQUAL (Table Ciqual 2020, ANSES) ya descargado en data/raw.
CIQUAL_XLS_PATH = RAW_DIR / "Ciqual_2020_FR.xls"

# Tipos de dato de USDA FoodData Central a cosechar (datos analíticos de calidad).
# "Foundation" son ~400 alimentos con analítica reciente; añadir "SR Legacy"
# amplía a la referencia clásica (~7800), a costa de más peticiones.
USDA_DATA_TYPES = ["Foundation"]

# Ruta al .env del backend (contiene FDC_API_KEY). Se carga de forma perezosa.
ENV_PATH = BACKEND_DIR / ".env"

# Prioridad de fuente por defecto para alimentos españoles:
# BEDCA primero, USDA para rellenar micros, CIQUAL como refuerzo.
SOURCE_PRIORITY = ["bedca", "usda", "ciqual", "seed_provisional"]


def load_env() -> None:
    """Carga variables de ``backend/.env`` (p. ej. FDC_API_KEY) si existe.

    Usa python-dotenv si está disponible; si no, hace un parseo mínimo. No
    sobrescribe variables ya presentes en el entorno y nunca registra la clave.
    """
    import os

    if not ENV_PATH.exists():
        return
    try:
        from dotenv import load_dotenv

        load_dotenv(ENV_PATH, override=False)
        return
    except ImportError:
        pass
    for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())
