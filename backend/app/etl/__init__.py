"""Pipeline de datos (ETL) de NutriMovic.

Prepara la ingesta de las tres fuentes de composición de alimentos
(BEDCA, USDA FoodData Central, CIQUAL) a una base SQLite canónica
coherente con ``app.core.models`` y ``app.core.nutrients``.

Módulos:
    - ``schema.sql``      : esquema SQLite canónico.
    - ``usda_client``     : cliente de la API FoodData Central + mapeador a Food.
    - ``bedca_loader``    : parser de exportaciones BEDCA locales a Food.
    - ``ciqual_loader``   : parser del fichero CIQUAL (ANSES) local a Food.
    - ``build_db``        : orquestador; construye la SQLite canónica.

Ningún módulo fabrica datos nutricionales: los huecos se propagan como
``not_determined`` y nunca se rellenan con 0.
"""
from __future__ import annotations

SCHEMA_FILENAME = "schema.sql"
