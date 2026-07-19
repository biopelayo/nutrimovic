"""Repositorio de alimentos.

Carga el catálogo canónico desde la SQLite generada por el ETL
(``data/nutrimovic.sqlite``) cuando existe; si no, cae al seed JSON. En ambos
casos expone la MISMA interfaz pública (``get``, ``all``, ``count``, ``search``),
de modo que la API no cambia según de dónde vengan los datos.
"""
from __future__ import annotations

import json
import sqlite3
from functools import lru_cache

from app.core.config import DB_PATH, SEED_DIR
from app.core.models import (
    DataSource,
    Food,
    FoodGroup,
    FoodState,
    FoodSummaryExt,
    MeasurementStatus,
    NutrientValue,
)


class FoodRepository:
    def __init__(self, foods: dict[str, Food]):
        self._foods = foods

    def get(self, food_id: str) -> Food | None:
        return self._foods.get(food_id)

    def all(self) -> list[Food]:
        return list(self._foods.values())

    def count(self) -> int:
        return len(self._foods)

    def search(self, q: str = "", group: str | None = None, limit: int = 25) -> list[FoodSummaryExt]:
        q_norm = q.strip().lower()
        results: list[FoodSummaryExt] = []
        for food in self._foods.values():
            if group and food.group.value != group:
                continue
            if q_norm and q_norm not in food.name_es.lower():
                continue
            results.append(
                FoodSummaryExt(
                    id=food.id,
                    name_es=food.name_es,
                    group=food.group,
                    source=food.source,
                    subgroup=food.subgroup,
                    image_name=food.image_name,
                )
            )
            if len(results) >= limit:
                break
        return results


# ---------------------------------------------------------------------------
# Carga desde la SQLite canónica
# ---------------------------------------------------------------------------
def _load_sqlite_foods(db_path=DB_PATH) -> dict[str, Food]:
    """Reconstruye los Food (con su composición) desde la BD. Vacío si no hay BD."""
    if not db_path.exists():
        return {}
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        # Nutrientes por alimento.
        values_by_food: dict[str, dict[str, NutrientValue]] = {}
        for row in conn.execute(
            "SELECT food_id, nutrient_id, amount, status FROM nutrient_values"
        ):
            values_by_food.setdefault(row["food_id"], {})[row["nutrient_id"]] = NutrientValue(
                nutrient_id=row["nutrient_id"],
                amount=row["amount"],
                status=MeasurementStatus(row["status"]),
            )

        foods: dict[str, Food] = {}
        for row in conn.execute("SELECT * FROM foods"):
            keys = row.keys()
            food = Food(
                id=row["id"],
                name_es=row["name_es"],
                group=FoodGroup(row["food_group"]),
                source=DataSource(row["source"]),
                source_ref=row["source_ref"],
                state=FoodState(row["state"]),
                edible_portion_factor=row["edible_portion_factor"],
                verified=bool(row["verified"]),
                subgroup=row["subgroup"] if "subgroup" in keys else None,
                image_name=row["image_name"] if "image_name" in keys else None,
                allergens=(
                    json.loads(row["allergens"])
                    if "allergens" in keys and row["allergens"]
                    else []
                ),
                household_measure=(
                    row["household_measure"] if "household_measure" in keys else None
                ),
                nutrients=values_by_food.get(row["id"], {}),
            )
            foods[food.id] = food
        return foods
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Carga desde el seed JSON (respaldo si no hay BD)
# ---------------------------------------------------------------------------
def _load_seed_foods() -> dict[str, Food]:
    seed_file = SEED_DIR / "foods_seed.json"
    if not seed_file.exists():
        return {}
    raw = json.loads(seed_file.read_text(encoding="utf-8"))
    foods: dict[str, Food] = {}
    for item in raw.get("foods", []):
        for nutrient_id, value in item.get("nutrients", {}).items():
            value.setdefault("nutrient_id", nutrient_id)
        food = Food.model_validate(item)
        foods[food.id] = food
    return foods


def _load_foods() -> dict[str, Food]:
    """Prefiere el catálogo real de la SQLite; si no existe, usa el seed."""
    foods = _load_sqlite_foods()
    if foods:
        return foods
    return _load_seed_foods()


@lru_cache(maxsize=1)
def get_repository() -> FoodRepository:
    return FoodRepository(_load_foods())
