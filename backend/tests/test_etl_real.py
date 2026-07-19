"""Tests del ETL con datos reales (USDA y CIQUAL) y del catálogo canónico.

Filosofía:
  - Los tests que necesitan RED (API de USDA) o el FICHERO CIQUAL se SALTAN
    limpiamente si no están disponibles, para que la batería pase en cualquier
    entorno (CI sin red incluido).
  - El mapeo de USDA se comprueba con una respuesta REAL de muestra guardada como
    fixture (estructura y valores tal como los devuelve FDC), sin llamar a la red.
  - La carga del catálogo SQLite se prueba construyéndolo desde fuentes en
    memoria y leyéndolo con el repositorio.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from app.core.models import DataSource, FoodGroup, MeasurementStatus
from app.etl import build_db, ciqual_loader, usda_client
from app.etl.usda_client import classify_usda_food, map_usda_food

CIQUAL_XLS = Path(__file__).resolve().parents[2] / "data" / "raw" / "Ciqual_2020_FR.xls"


# ---------------------------------------------------------------------------
# Mapeo de una respuesta REAL de USDA (muestra guardada, sin red)
# ---------------------------------------------------------------------------
# Recorte real de /foods (format=full) para "Apples, gala, with skin, raw"
# (fdcId 2117387). Valores tal como los devuelve FDC. La energía de este
# alimento Foundation viene por factores de Atwater (2048), no como 1008.
REAL_USDA_APPLE = {
    "fdcId": 2117387,
    "description": "Apples, gala, with skin, raw",
    "foodCategory": {"id": 9, "code": "0900", "description": "Fruits and Fruit Juices"},
    "foodNutrients": [
        {"nutrient": {"id": 1003, "number": "203", "name": "Protein", "unitName": "g"},
         "amount": 0.163},
        {"nutrient": {"id": 1004, "number": "204", "name": "Total lipid (fat)", "unitName": "g"},
         "amount": 0.155},
        {"nutrient": {"id": 1005, "number": "205", "name": "Carbohydrate, by difference",
                      "unitName": "g"}, "amount": 14.8},
        {"nutrient": {"id": 1051, "number": "255", "name": "Water", "unitName": "g"},
         "amount": 84.6},
        {"nutrient": {"id": 1087, "number": "301", "name": "Calcium, Ca", "unitName": "mg"},
         "amount": 5.61},
        {"nutrient": {"id": 2048, "number": "958",
                      "name": "Energy (Atwater Specific Factors)", "unitName": "kcal"},
         "amount": 60.6},
    ],
}


def test_map_real_usda_food_with_atwater_energy() -> None:
    group, subgroup = classify_usda_food(REAL_USDA_APPLE)
    food = map_usda_food(REAL_USDA_APPLE, group=group, subgroup=subgroup)

    assert food.id == "usda_2117387"
    assert food.source == DataSource.USDA
    assert food.verified is True
    # Clasificación por categoría USDA.
    assert food.group == FoodGroup.FRUIT
    assert food.subgroup == "Fruits and Fruit Juices"
    # Macros reales mapeados.
    assert food.nutrients["protein_g"].amount == pytest.approx(0.163)
    assert food.nutrients["carbs_g"].amount == pytest.approx(14.8)
    assert food.nutrients["calcium_mg"].amount == pytest.approx(5.61)
    # Energía por respaldo Atwater (2048) -> energy_kcal.
    assert food.nutrients["energy_kcal"].amount == pytest.approx(60.6)
    assert food.nutrients["energy_kcal"].status == MeasurementStatus.MEASURED


def test_classify_usda_egg_is_protein() -> None:
    egg = {"fdcId": 1, "description": "Eggs, Grade A, Large, egg whole",
           "foodCategory": {"description": "Dairy and Egg Products"}, "foodNutrients": []}
    group, _ = classify_usda_food(egg)
    assert group == FoodGroup.PROTEIN


def test_classify_usda_search_shape_string_category() -> None:
    # En /foods/search la categoría es una cadena, no un dict.
    veg = {"fdcId": 2, "description": "Carrots, raw",
           "foodCategory": "Vegetables and Vegetable Products", "foodNutrients": []}
    group, subgroup = classify_usda_food(veg)
    assert group == FoodGroup.VEGETABLE
    assert subgroup == "Vegetables and Vegetable Products"


# ---------------------------------------------------------------------------
# CIQUAL real (se salta si no está el fichero descargado)
# ---------------------------------------------------------------------------
@pytest.mark.skipif(not CIQUAL_XLS.exists(), reason="Fichero CIQUAL no descargado")
def test_load_ciqual_xls_real() -> None:
    foods = ciqual_loader.load_ciqual_xls(CIQUAL_XLS)
    assert len(foods) > 2000  # la tabla 2020 trae ~3186 alimentos
    # Todos son de fuente CIQUAL y verificados.
    assert all(f.source == DataSource.CIQUAL for f in foods)
    # La mayoría llevan proteína y energía reales.
    with_protein = sum(1 for f in foods if "protein_g" in f.nutrients)
    assert with_protein > len(foods) * 0.9
    # La clasificación deja pocos "other".
    others = sum(1 for f in foods if f.group == FoodGroup.OTHER)
    assert others < len(foods) * 0.1


def test_ciqual_column_resolution_normalizes_headers() -> None:
    # Cabeceras con doble espacio y sin tilde deben resolverse igual.
    headers = [
        "alim_code", "alim_nom_fr", "alim_grp_nom_fr", "alim_ssgrp_nom_fr",
        "Energie, Reglement UE N 1169/2011  (kcal/100 g)",  # sin tildes, doble espacio
        "Proteines, N x facteur de Jones (g/100 g)",
        "Lipides (g/100 g)",
    ]
    resolved = ciqual_loader._resolve_columns(headers)
    assert "energy_kcal" in resolved
    assert "protein_g" in resolved
    assert "fat_g" in resolved


# ---------------------------------------------------------------------------
# Catálogo SQLite: construcción con fuentes reales en memoria + lectura por repo
# ---------------------------------------------------------------------------
def test_build_and_read_catalog_with_usda_and_ciqual(tmp_path: Path) -> None:
    from app.core.models import Food, NutrientValue

    usda_food = map_usda_food(REAL_USDA_APPLE, group=FoodGroup.FRUIT,
                              subgroup="Fruits and Fruit Juices", image_name="Apples")
    ciqual_food = Food(
        id="ciqual_13000", name_es="Pomme crue", group=FoodGroup.FRUIT,
        source=DataSource.CIQUAL, source_ref="13000", subgroup="fruits",
        nutrients={
            "iron_mg": NutrientValue(nutrient_id="iron_mg", amount=0.12,
                                     status=MeasurementStatus.MEASURED),
        },
    )
    db_file = tmp_path / "catalog.sqlite"
    report = build_db.build_database(
        db_file, foods_by_source={"usda": [usda_food], "ciqual": [ciqual_food]}
    )
    assert report.foods_written == 2

    # subgroup e image_name persistidos en la BD.
    conn = sqlite3.connect(db_file)
    try:
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM foods WHERE id = ?", ("usda_2117387",)).fetchone()
        assert row["subgroup"] == "Fruits and Fruit Juices"
        assert row["image_name"] == "Apples"
    finally:
        conn.close()

    # El repositorio lee ese catálogo y expone la interfaz habitual.
    from app.data import repository

    repo = repository.FoodRepository(repository._load_sqlite_foods(db_file))
    assert repo.count() == 2
    apple = repo.get("usda_2117387")
    assert apple is not None
    assert apple.image_name == "Apples"
    assert apple.nutrients["energy_kcal"].amount == pytest.approx(60.6)
    summaries = repo.search("pomme")
    assert any(s.id == "ciqual_13000" for s in summaries)
