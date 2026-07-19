"""Loader de BEDCA (Base de Datos Española de Composición de Alimentos).

Fuente: BEDCA — Base de Datos Española de Composición de Alimentos
(https://www.bedca.net/), promovida por la AESAN y la Red BEDCA. Es la
referencia canónica para alimentos españoles y, por eso, la fuente de máxima
prioridad en NutriMovic (ver ``SOURCE_PRIORITY`` en config.py).

Formato de entrada
------------------
BEDCA se consulta por web y expone una exportación XML por su servicio de
consulta, además de exportaciones tabuladas que el usuario descarga. Este loader
parte de un fichero LOCAL tabulado (CSV) ya descargado; no hace scraping.

El catálogo canónico aún no trae ``bedca_ids`` rellenos, así que el mapeo de
columnas a ``nutrient_id`` vive aquí en ``BEDCA_COLUMN_MAP`` y DEBE verificarse
contra las cabeceras reales del fichero antes de un uso serio. Las cabeceras de
BEDCA dependen de cómo se exporte (código de componente vs. nombre); ajusta el
mapa a tu export.

Este loader no fabrica datos: columnas ausentes o celdas vacías se propagan como
``not_determined``; "trazas" como ``trace``.
"""
from __future__ import annotations

import csv
from pathlib import Path

from app.core.models import DataSource, Food, FoodGroup, FoodState, NutrientValue
from app.core.nutrients import NUTRIENTS_BY_ID
from app.etl.value_parsing import parse_cell

# ---------------------------------------------------------------------------
# Mapeo de columnas del CSV de BEDCA -> nutrient_id canónico.
# PROVISIONAL: verificar contra las cabeceras reales del export. Los nombres de
# componente de BEDCA suelen ser en español; aquí se usan claves indicativas.
# Clave = cabecera de columna en el CSV; valor = nutrient_id.
# ---------------------------------------------------------------------------
BEDCA_COLUMN_MAP: dict[str, str] = {
    "energia_kcal": "energy_kcal",
    "energia_kj": "energy_kj",
    "proteina_total": "protein_g",
    "grasa_total": "fat_g",
    "hidratos_carbono": "carbs_g",
    "fibra_dietetica": "fiber_g",
    "agua": "water_g",
    "alcohol": "alcohol_g",
    "acidos_grasos_saturados": "fat_saturated_g",
    "acidos_grasos_monoinsaturados": "fat_monounsaturated_g",
    "acidos_grasos_poliinsaturados": "fat_polyunsaturated_g",
    "colesterol": "cholesterol_mg",
    "azucares": "sugars_g",
    "almidon": "starch_g",
    "vitamina_a_rae": "vit_a_ug_rae",
    "vitamina_d": "vit_d_ug",
    "vitamina_e": "vit_e_mg",
    "vitamina_k": "vit_k_ug",
    "vitamina_c": "vit_c_mg",
    "tiamina": "vit_b1_mg",
    "riboflavina": "vit_b2_mg",
    "niacina": "vit_b3_mg_ne",
    "vitamina_b6": "vit_b6_mg",
    "folato": "vit_b9_ug_dfe",
    "vitamina_b12": "vit_b12_ug",
    "calcio": "calcium_mg",
    "hierro": "iron_mg",
    "magnesio": "magnesium_mg",
    "fosforo": "phosphorus_mg",
    "potasio": "potassium_mg",
    "sodio": "sodium_mg",
    "zinc": "zinc_mg",
    "cobre": "copper_mg",
    "manganeso": "manganese_mg",
    "selenio": "selenium_ug",
    "yodo": "iodine_ug",
}

# Columnas de identificación esperadas en el CSV.
COL_ID = "id"
COL_NAME = "nombre_es"
COL_GROUP = "grupo"
COL_STATE = "estado"
COL_EDIBLE = "parte_comestible"


class BedcaFileNotFoundError(FileNotFoundError):
    """El fichero BEDCA local no existe."""


def _row_to_food(row: dict[str, str]) -> Food:
    nutrients: dict[str, NutrientValue] = {}
    for column, nutrient_id in BEDCA_COLUMN_MAP.items():
        if nutrient_id not in NUTRIENTS_BY_ID:
            continue  # el mapa apunta a un nutriente fuera del catálogo: se ignora
        if column not in row:
            continue  # columna ausente en el fichero -> not_determined implícito
        value = parse_cell(nutrient_id, row.get(column))
        # Solo registramos lo que aporta información (measured/trace).
        if value.is_usable() or value.amount is not None:
            nutrients[nutrient_id] = value

    raw_group = (row.get(COL_GROUP) or "").strip().lower()
    group = FoodGroup(raw_group) if raw_group in FoodGroup._value2member_map_ else FoodGroup.OTHER

    raw_state = (row.get(COL_STATE) or "raw").strip().lower()
    state = FoodState(raw_state) if raw_state in FoodState._value2member_map_ else FoodState.RAW

    try:
        edible = float((row.get(COL_EDIBLE) or "1").replace(",", "."))
    except ValueError:
        edible = 1.0

    source_ref = (row.get(COL_ID) or "").strip() or None
    food_id = f"bedca_{source_ref}" if source_ref else f"bedca_{(row.get(COL_NAME) or 'sin_id').strip()}"

    return Food(
        id=food_id,
        name_es=(row.get(COL_NAME) or "").strip() or food_id,
        group=group,
        source=DataSource.BEDCA,
        source_ref=source_ref,
        state=state,
        edible_portion_factor=edible,
        nutrients=nutrients,
        verified=True,
    )


def load_bedca_csv(path: str | Path, *, delimiter: str = ";", encoding: str = "utf-8") -> list[Food]:
    """Parsea un CSV de BEDCA local a una lista de Food.

    Lanza ``BedcaFileNotFoundError`` con mensaje claro si el fichero no existe.
    No inventa datos: celdas vacías -> not_determined; "trazas" -> trace.
    """
    file_path = Path(path)
    if not file_path.exists():
        raise BedcaFileNotFoundError(
            f"No se encuentra el fichero BEDCA en «{file_path}». Descárgalo desde "
            f"https://www.bedca.net/ (exportación tabulada) y colócalo en esa ruta. "
            f"Sin fichero no hay datos y no se fabrica nada."
        )

    foods: list[Food] = []
    with file_path.open("r", encoding=encoding, newline="") as fh:
        reader = csv.DictReader(fh, delimiter=delimiter)
        for row in reader:
            foods.append(_row_to_food(row))
    return foods
