"""Orquestador del ETL: construye la base SQLite canónica de NutriMovic.

Aplica la prioridad de fuente de ``config.SOURCE_PRIORITY``
(bedca > usda > ciqual > seed_provisional): al fusionar alimentos que comparten
id, gana la fuente de mayor prioridad y las de menor solo rellenan huecos
(``not_determined``). Nunca se sobrescribe un valor útil ni se inventan datos.

Modo sin datos externos (por defecto en esta fase): construye la BD SOLO desde
el seed JSON (``data/seed/foods_seed.json``), de modo que el sistema tenga una
base funcional aunque no haya API key de USDA ni ficheros BEDCA/CIQUAL.

Es idempotente: cada ejecución reconstruye tablas y contenido dentro de una
transacción; correr dos veces deja el mismo estado.

Uso:
    python -m app.etl.build_db            # construye desde seed en data/nutrimovic.sqlite
    python -m app.etl.build_db --db ruta  # ruta de salida alternativa
"""
from __future__ import annotations

import argparse
import json
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path

from app.core.config import DB_PATH, SEED_DIR, SOURCE_PRIORITY
from app.core.models import DataSource, Food, MeasurementStatus, NutrientValue
from app.core.nutrients import NUTRIENTS

SCHEMA_PATH = Path(__file__).with_name("schema.sql")

# Nombre legible y nota de licencia por fuente (para la tabla sources).
_SOURCE_META: dict[str, tuple[str, str]] = {
    "bedca": ("Base de Datos Española de Composición de Alimentos (BEDCA)",
              "Uso con cita obligatoria; revisar términos para uso comercial."),
    "usda": ("USDA FoodData Central", "Dominio público (U.S. Government work)."),
    "ciqual": ("CIQUAL — ANSES (Francia)", "Licencia abierta Etalab 2.0; verificar."),
    "seed_provisional": ("Datos semilla provisionales", "Interno; no publicable como oficial."),
}


@dataclass
class BuildReport:
    """Resumen de una construcción de la BD."""

    db_path: Path
    foods_written: int = 0
    values_written: int = 0
    by_source: dict[str, int] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Carga del seed
# ---------------------------------------------------------------------------
def load_seed_foods(seed_dir: Path = SEED_DIR) -> list[Food]:
    """Carga los alimentos semilla desde el JSON. Lista vacía si no existe."""
    seed_file = seed_dir / "foods_seed.json"
    if not seed_file.exists():
        return []
    raw = json.loads(seed_file.read_text(encoding="utf-8"))
    foods: list[Food] = []
    for item in raw.get("foods", []):
        for nutrient_id, value in item.get("nutrients", {}).items():
            if isinstance(value, dict):
                value.setdefault("nutrient_id", nutrient_id)
        foods.append(Food.model_validate(item))
    return foods


# ---------------------------------------------------------------------------
# Fusión con prioridad de fuente
# ---------------------------------------------------------------------------
def _priority_of(source: DataSource | str) -> int:
    value = source.value if isinstance(source, DataSource) else source
    return SOURCE_PRIORITY.index(value) if value in SOURCE_PRIORITY else len(SOURCE_PRIORITY)


def _merge_nutrients(primary: dict[str, NutrientValue],
                     secondary: dict[str, NutrientValue]) -> dict[str, NutrientValue]:
    """Rellena en primary los nutrientes que le faltan (o son not_determined)
    con los de secondary (fuente de menor prioridad). No sobrescribe lo útil."""
    merged = dict(primary)
    for nutrient_id, value in secondary.items():
        current = merged.get(nutrient_id)
        if current is None or current.status == MeasurementStatus.NOT_DETERMINED:
            merged[nutrient_id] = value
    return merged


def merge_foods(foods_by_source: dict[str, list[Food]]) -> list[Food]:
    """Fusiona alimentos de varias fuentes respetando SOURCE_PRIORITY.

    Alimentos con el mismo id se combinan: gana el de mayor prioridad y los de
    menor solo rellenan huecos. Ids distintos coexisten. En modo seed-only esto
    devuelve simplemente los alimentos del seed.
    """
    ordered_sources = sorted(foods_by_source.keys(), key=_priority_of)
    canonical: dict[str, Food] = {}
    for source in ordered_sources:
        for food in foods_by_source[source]:
            existing = canonical.get(food.id)
            if existing is None:
                canonical[food.id] = food
            else:
                merged_nutrients = _merge_nutrients(existing.nutrients, food.nutrients)
                canonical[food.id] = existing.model_copy(update={"nutrients": merged_nutrients})
    return list(canonical.values())


# ---------------------------------------------------------------------------
# Escritura en SQLite
# ---------------------------------------------------------------------------
def apply_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))


def _clear_all_tables(conn: sqlite3.Connection) -> None:
    """Vacía las tablas respetando el orden de dependencias (hijos primero)."""
    conn.execute("DELETE FROM nutrient_values")
    conn.execute("DELETE FROM foods")
    conn.execute("DELETE FROM nutrient_defs")
    conn.execute("DELETE FROM sources")


def _seed_reference_tables(conn: sqlite3.Connection) -> None:
    for value in SOURCE_PRIORITY:
        name_es, license_note = _SOURCE_META.get(value, (value, ""))
        conn.execute(
            "INSERT INTO sources (id, name_es, priority, license_note) VALUES (?, ?, ?, ?)",
            (value, name_es, _priority_of(value), license_note),
        )
    for ndef in NUTRIENTS:
        conn.execute(
            "INSERT INTO nutrient_defs (id, name_es, unit, category) VALUES (?, ?, ?, ?)",
            (ndef.id, ndef.name_es, ndef.unit, ndef.category.value),
        )


def _write_foods(conn: sqlite3.Connection, foods: list[Food]) -> tuple[int, int, dict[str, int]]:
    values_written = 0
    by_source: dict[str, int] = {}
    for food in foods:
        conn.execute(
            "INSERT INTO foods (id, name_es, food_group, source, source_ref, state, "
            "edible_portion_factor, verified, subgroup, image_name) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                food.id, food.name_es, food.group.value, food.source.value,
                food.source_ref, food.state.value, food.edible_portion_factor,
                int(food.verified), food.subgroup, food.image_name,
            ),
        )
        by_source[food.source.value] = by_source.get(food.source.value, 0) + 1
        for nutrient_id, value in food.nutrients.items():
            conn.execute(
                "INSERT INTO nutrient_values (food_id, nutrient_id, amount, status) "
                "VALUES (?, ?, ?, ?)",
                (food.id, nutrient_id, value.amount, value.status.value),
            )
            values_written += 1
    return len(foods), values_written, by_source


def build_database(db_path: str | Path = DB_PATH,
                   foods_by_source: dict[str, list[Food]] | None = None) -> BuildReport:
    """Construye (o reconstruye) la SQLite canónica.

    Si ``foods_by_source`` es None, funciona en modo seed-only: carga solo el
    seed JSON. Para integrar fuentes reales, pásalas ya cargadas por sus loaders
    (p. ej. {"bedca": load_bedca_csv(...), "usda": [...]}), incluyendo el seed
    si se quiere como respaldo.
    """
    if foods_by_source is None:
        foods_by_source = {"seed_provisional": load_seed_foods()}

    foods = merge_foods(foods_by_source)

    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_path)
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        apply_schema(conn)
        with conn:  # transacción
            _clear_all_tables(conn)
            _seed_reference_tables(conn)
            foods_written, values_written, by_source = _write_foods(conn, foods)
    finally:
        conn.close()

    return BuildReport(
        db_path=db_path,
        foods_written=foods_written,
        values_written=values_written,
        by_source=by_source,
    )


def _main() -> None:
    parser = argparse.ArgumentParser(description="Construye la SQLite canónica de NutriMovic.")
    parser.add_argument("--db", default=str(DB_PATH), help="Ruta del fichero SQLite de salida.")
    args = parser.parse_args()

    report = build_database(args.db)
    print(f"BD construida en: {report.db_path}")
    print(f"Alimentos escritos: {report.foods_written}")
    print(f"Valores nutricionales escritos: {report.values_written}")
    print(f"Por fuente: {report.by_source}")


if __name__ == "__main__":
    _main()
