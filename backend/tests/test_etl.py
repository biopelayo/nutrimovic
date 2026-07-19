"""Tests del pipeline ETL de NutriMovic.

Cubren:
  - Construcción de la BD SQLite desde el seed y su lectura.
  - Idempotencia del orquestador.
  - Propagación de not_determined (nunca se guarda 0 por un hueco).
  - Mapeador USDA con una respuesta MOCK DE ESTRUCTURA (no dato nutricional real).
  - Fallo claro sin API key.
  - Fallo claro de los loaders BEDCA/CIQUAL cuando el fichero no existe.

IMPORTANTE: el JSON del fixture USDA es un MOCK de la ESTRUCTURA de la API FDC,
con valores inventados solo para probar el cableado del mapeador. No son datos
nutricionales reales y no deben usarse como tales.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from app.core.models import DataSource, FoodGroup, FoodState, MeasurementStatus
from app.etl import bedca_loader, build_db, ciqual_loader, usda_client


# ---------------------------------------------------------------------------
# Construcción y lectura de la BD desde el seed
# ---------------------------------------------------------------------------
def test_build_database_from_seed(tmp_path: Path) -> None:
    db_file = tmp_path / "nutrimovic_test.sqlite"
    report = build_db.build_database(db_file)

    assert db_file.exists()
    assert report.foods_written > 0
    assert report.values_written > 0

    seed_foods = build_db.load_seed_foods()
    assert report.foods_written == len(seed_foods)

    conn = sqlite3.connect(db_file)
    try:
        conn.row_factory = sqlite3.Row
        # Tablas de referencia sembradas.
        n_sources = conn.execute("SELECT COUNT(*) FROM sources").fetchone()[0]
        assert n_sources == 4
        n_defs = conn.execute("SELECT COUNT(*) FROM nutrient_defs").fetchone()[0]
        assert n_defs > 30  # el catálogo tiene decenas de nutrientes

        # Alimentos legibles.
        n_foods = conn.execute("SELECT COUNT(*) FROM foods").fetchone()[0]
        assert n_foods == report.foods_written

        # Un alimento concreto del seed con su composición.
        rice = conn.execute(
            "SELECT * FROM foods WHERE id = ?", ("seed_arroz_blanco_cocido",)
        ).fetchone()
        assert rice is not None
        assert rice["food_group"] == "starchy"
        assert rice["state"] == "cooked"
        assert rice["source"] == "seed_provisional"

        kcal = conn.execute(
            "SELECT amount, status FROM nutrient_values WHERE food_id = ? AND nutrient_id = ?",
            ("seed_arroz_blanco_cocido", "energy_kcal"),
        ).fetchone()
        assert kcal is not None
        assert kcal["amount"] == pytest.approx(130.0)
        assert kcal["status"] == "measured"
    finally:
        conn.close()


def test_build_database_is_idempotent(tmp_path: Path) -> None:
    db_file = tmp_path / "idem.sqlite"
    first = build_db.build_database(db_file)
    second = build_db.build_database(db_file)

    assert first.foods_written == second.foods_written
    assert first.values_written == second.values_written

    conn = sqlite3.connect(db_file)
    try:
        n_foods = conn.execute("SELECT COUNT(*) FROM foods").fetchone()[0]
        n_values = conn.execute("SELECT COUNT(*) FROM nutrient_values").fetchone()[0]
        assert n_foods == second.foods_written
        assert n_values == second.values_written
    finally:
        conn.close()


def test_not_determined_is_not_stored_as_zero(tmp_path: Path) -> None:
    """Un nutriente ausente en el seed no aparece en la BD (ni como 0)."""
    db_file = tmp_path / "nd.sqlite"
    build_db.build_database(db_file)

    conn = sqlite3.connect(db_file)
    try:
        # El arroz del seed no reporta vitamina B12: no debe existir fila.
        row = conn.execute(
            "SELECT * FROM nutrient_values WHERE food_id = ? AND nutrient_id = ?",
            ("seed_arroz_blanco_cocido", "vit_b12_ug"),
        ).fetchone()
        assert row is None
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Fusión con prioridad de fuente
# ---------------------------------------------------------------------------
def test_merge_prefers_higher_priority_and_fills_gaps() -> None:
    from app.core.models import Food, NutrientValue

    bedca_food = Food(
        id="x1", name_es="Alimento X", group=FoodGroup.OTHER, source=DataSource.BEDCA,
        nutrients={
            "protein_g": NutrientValue(nutrient_id="protein_g", amount=10.0,
                                       status=MeasurementStatus.MEASURED),
        },
    )
    usda_food = Food(
        id="x1", name_es="Food X", group=FoodGroup.OTHER, source=DataSource.USDA,
        nutrients={
            "protein_g": NutrientValue(nutrient_id="protein_g", amount=99.0,
                                       status=MeasurementStatus.MEASURED),
            "iron_mg": NutrientValue(nutrient_id="iron_mg", amount=2.0,
                                     status=MeasurementStatus.MEASURED),
        },
    )
    merged = build_db.merge_foods({"usda": [usda_food], "bedca": [bedca_food]})
    assert len(merged) == 1
    food = merged[0]
    # BEDCA (mayor prioridad) gana en el valor compartido.
    assert food.nutrients["protein_g"].amount == pytest.approx(10.0)
    # USDA rellena el hueco que BEDCA no tenía.
    assert food.nutrients["iron_mg"].amount == pytest.approx(2.0)


# ---------------------------------------------------------------------------
# Mapeador USDA con respuesta MOCK DE ESTRUCTURA
# ---------------------------------------------------------------------------
@pytest.fixture()
def mock_fdc_food() -> dict:
    """MOCK de la ESTRUCTURA de una respuesta /food/{fdcId} de FDC.

    Valores INVENTADOS solo para probar el mapeador. NO son datos reales.
    Incluye a propósito un nutriente fuera de catálogo (id 9999) para
    comprobar que se ignora.
    """
    return {
        "fdcId": 123456,
        "description": "MOCK FOOD (structure only)",
        "foodNutrients": [
            {"nutrient": {"id": 1008, "name": "Energy", "unitName": "KCAL"}, "amount": 100.0},
            {"nutrient": {"id": 1003, "name": "Protein", "unitName": "G"}, "amount": 5.5},
            {"nutrient": {"id": 1004, "name": "Total lipid (fat)", "unitName": "G"}, "amount": 0.0},
            {"nutrient": {"id": 9999, "name": "Nutriente fuera de catálogo", "unitName": "G"},
             "amount": 42.0},
            {"nutrient": {"id": 1089, "name": "Iron", "unitName": "MG"}, "amount": None},
        ],
    }


def test_map_usda_food_structure(mock_fdc_food: dict) -> None:
    food = usda_client.map_usda_food(mock_fdc_food, group=FoodGroup.PROTEIN,
                                     state=FoodState.RAW)
    assert food.id == "usda_123456"
    assert food.source == DataSource.USDA
    assert food.source_ref == "123456"
    assert food.group == FoodGroup.PROTEIN

    # Mapeo correcto de ids FDC -> nutrient_id canónico.
    assert food.nutrients["energy_kcal"].amount == pytest.approx(100.0)
    assert food.nutrients["protein_g"].amount == pytest.approx(5.5)
    # Un 0 explícito de FDC es un 0 real medido.
    assert food.nutrients["fat_g"].amount == pytest.approx(0.0)
    assert food.nutrients["fat_g"].status == MeasurementStatus.MEASURED

    # Nutriente fuera de catálogo (id 9999): ignorado.
    assert all(v.amount != 42.0 for v in food.nutrients.values())
    # Nutriente sin valor numérico (amount None): no se registra -> not_determined.
    assert "iron_mg" not in food.nutrients


def test_map_usda_food_search_shape() -> None:
    """La forma abreviada de /foods/search usa 'nutrientId' en vez de 'nutrient.id'."""
    raw = {
        "fdcId": 777,
        "description": "MOCK SEARCH ITEM",
        "foodNutrients": [
            {"nutrientId": 1008, "value": 88.0},
            {"nutrientId": 1003, "value": 3.3},
        ],
    }
    food = usda_client.map_usda_food(raw)
    assert food.nutrients["energy_kcal"].amount == pytest.approx(88.0)
    assert food.nutrients["protein_g"].amount == pytest.approx(3.3)


def test_usda_index_covers_catalog() -> None:
    """El índice inverso usa los usda_ids del catálogo canónico."""
    assert usda_client.USDA_ID_TO_NUTRIENT[1008] == "energy_kcal"
    assert usda_client.USDA_ID_TO_NUTRIENT[1003] == "protein_g"
    assert usda_client.USDA_ID_TO_NUTRIENT[1089] == "iron_mg"


# ---------------------------------------------------------------------------
# Fallos claros cuando faltan credenciales o ficheros
# ---------------------------------------------------------------------------
def test_get_api_key_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(usda_client.FDC_API_KEY_ENV, raising=False)
    with pytest.raises(usda_client.MissingApiKeyError):
        usda_client.get_api_key()


def test_usda_client_requires_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(usda_client.FDC_API_KEY_ENV, raising=False)
    with pytest.raises(usda_client.MissingApiKeyError):
        usda_client.UsdaClient()


def test_bedca_loader_missing_file(tmp_path: Path) -> None:
    with pytest.raises(bedca_loader.BedcaFileNotFoundError):
        bedca_loader.load_bedca_csv(tmp_path / "no_existe.csv")


def test_ciqual_loader_missing_file(tmp_path: Path) -> None:
    with pytest.raises(ciqual_loader.CiqualFileNotFoundError):
        ciqual_loader.load_ciqual_csv(tmp_path / "no_existe.csv")


# ---------------------------------------------------------------------------
# Loaders BEDCA/CIQUAL sobre un CSV mínimo de ESTRUCTURA
# ---------------------------------------------------------------------------
def test_bedca_loader_parses_structure(tmp_path: Path) -> None:
    """CSV MOCK de estructura BEDCA (valores inventados, no reales)."""
    csv_path = tmp_path / "bedca_mock.csv"
    csv_path.write_text(
        "id;nombre_es;grupo;estado;parte_comestible;energia_kcal;proteina_total;vitamina_c\n"
        "1;Alimento mock;fruit;raw;0,9;50;1,2;traces\n",
        encoding="utf-8",
    )
    foods = bedca_loader.load_bedca_csv(csv_path)
    assert len(foods) == 1
    food = foods[0]
    assert food.source == DataSource.BEDCA
    assert food.group == FoodGroup.FRUIT
    assert food.edible_portion_factor == pytest.approx(0.9)
    assert food.nutrients["energy_kcal"].amount == pytest.approx(50.0)
    assert food.nutrients["protein_g"].amount == pytest.approx(1.2)
    # "traces" -> trace, sin amount.
    assert food.nutrients["vit_c_mg"].status == MeasurementStatus.TRACE
    assert food.nutrients["vit_c_mg"].amount is None
