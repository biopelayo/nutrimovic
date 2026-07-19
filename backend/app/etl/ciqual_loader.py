"""Loader de CIQUAL (tabla de composición de alimentos de ANSES, Francia).

Fuente: CIQUAL, gestionada por ANSES (https://ciqual.anses.fr/). Se descarga
el fichero oficial «Table Ciqual 2020» (un XLS de ~3,6 MB) y se coloca en
``data/raw/``. Este loader lee ese XLS directamente (hoja ``compo``) y también
admite un CSV equivalente.

En NutriMovic CIQUAL es fuente de refuerzo (tercera prioridad, tras BEDCA y
USDA) para rellenar micronutrientes que falten.

Formato de entrada
------------------
La tabla trae una fila por alimento y una columna por constituyente. Las celdas
usan coma decimal (convención francesa) y marcadores como ``traces``, ``-`` (no
reportado) y ``< X`` (por debajo del límite de cuantificación → traza). El
módulo ``value_parsing`` los interpreta. No se fabrica nada: hueco →
not_determined.

Resolución de columnas
----------------------
Las cabeceras están en francés, con acentos y a veces dobles espacios. Para no
depender de una transcripción exacta, las columnas se resuelven por
NORMALIZACIÓN: se quitan acentos, se pasa a minúsculas y se colapsan espacios.
Así, una cabecera mal transcrita en el mapa (por ejemplo sin tilde) sigue
casando con la real. ``CIQUAL_CANDIDATES`` asocia cada nutrient_id a una lista
de cabeceras candidatas EN ORDEN DE PREFERENCIA (la primera con dato gana); esto
permite, por ejemplo, tomar la energía del Reglamento UE y, si falta, la de
factores de Jones.
"""
from __future__ import annotations

import csv
import unicodedata
from pathlib import Path

from app.core.models import DataSource, Food, FoodGroup, FoodState, NutrientValue
from app.core.nutrients import NUTRIENTS_BY_ID
from app.etl.value_parsing import parse_cell

# ---------------------------------------------------------------------------
# Normalización de cabeceras
# ---------------------------------------------------------------------------
def _normalize(text: object) -> str:
    """Minúsculas sin acentos, con espacios colapsados y sin signos raros.

    Al eliminar los acentos, una tilde mal puesta o ausente en el mapa no impide
    el emparejamiento: ambos lados se normalizan igual.
    """
    s = str(text)
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.lower()
    out = []
    for ch in s:
        out.append(ch if ch.isalnum() else " ")
    return " ".join("".join(out).split())


# ---------------------------------------------------------------------------
# Candidatos de columna por nutrient_id (en orden de preferencia).
# La energía prioriza el Reglamento UE y cae a factores de Jones si falta.
# La proteína prioriza el factor de Jones y cae a N x 6,25.
# ---------------------------------------------------------------------------
CIQUAL_CANDIDATES: dict[str, list[str]] = {
    "energy_kcal": [
        "Energie, Règlement UE N° 1169/2011 (kcal/100 g)",
        "Energie, N x facteur Jones, avec fibres (kcal/100 g)",
    ],
    "energy_kj": [
        "Energie, Règlement UE N° 1169/2011 (kJ/100 g)",
        "Energie, N x facteur Jones, avec fibres (kJ/100 g)",
    ],
    "protein_g": [
        "Protéines, N x facteur de Jones (g/100 g)",
        "Protéines, N x 6.25 (g/100 g)",
    ],
    "fat_g": ["Lipides (g/100 g)"],
    "carbs_g": ["Glucides (g/100 g)"],
    "fiber_g": ["Fibres alimentaires (g/100 g)"],
    "water_g": ["Eau (g/100 g)"],
    "alcohol_g": ["Alcool (g/100 g)"],
    "ash_g": ["Cendres (g/100 g)"],
    "sugars_g": ["Sucres (g/100 g)"],
    "starch_g": ["Amidon (g/100 g)"],
    "polyols_g": ["Polyols totaux (g/100 g)"],
    "fat_saturated_g": ["AG saturés (g/100 g)"],
    "fat_monounsaturated_g": ["AG monoinsaturés (g/100 g)"],
    "fat_polyunsaturated_g": ["AG polyinsaturés (g/100 g)"],
    "cholesterol_mg": ["Cholestérol (mg/100 g)"],
    "calcium_mg": ["Calcium (mg/100 g)"],
    "copper_mg": ["Cuivre (mg/100 g)"],
    "iron_mg": ["Fer (mg/100 g)"],
    "magnesium_mg": ["Magnésium (mg/100 g)"],
    "manganese_mg": ["Manganèse (mg/100 g)"],
    "phosphorus_mg": ["Phosphore (mg/100 g)"],
    "potassium_mg": ["Potassium (mg/100 g)"],
    "sodium_mg": ["Sodium (mg/100 g)"],
    "zinc_mg": ["Zinc (mg/100 g)"],
    "selenium_ug": ["Sélénium (µg/100 g)"],
    "iodine_ug": ["Iode (µg/100 g)"],
    "vit_d_ug": ["Vitamine D (µg/100 g)"],
    "vit_e_mg": ["Vitamine E (mg/100 g)"],
    "vit_k_ug": ["Vitamine K1 (µg/100 g)"],
    "vit_c_mg": ["Vitamine C (mg/100 g)"],
    "vit_b1_mg": ["Vitamine B1 ou Thiamine (mg/100 g)"],
    "vit_b2_mg": ["Vitamine B2 ou Riboflavine (mg/100 g)"],
    "vit_b3_mg_ne": ["Vitamine B3 ou PP ou Niacine (mg/100 g)"],
    "vit_b5_mg": ["Vitamine B5 ou Acide pantothénique (mg/100 g)"],
    "vit_b6_mg": ["Vitamine B6 (mg/100 g)"],
    "vit_b9_ug_dfe": ["Vitamine B9 ou Folates totaux (µg/100 g)"],
    "vit_b12_ug": ["Vitamine B12 (µg/100 g)"],
}

# Compatibilidad hacia atrás: mapa plano cabecera->nutrient_id (primer candidato).
CIQUAL_COLUMN_MAP: dict[str, str] = {
    cols[0]: nid for nid, cols in CIQUAL_CANDIDATES.items()
}

# Columnas de identificación y taxonomía CIQUAL.
COL_ID = "alim_code"
COL_NAME = "alim_nom_fr"
COL_GROUP = "alim_grp_nom_fr"
COL_SUBGROUP = "alim_ssgrp_nom_fr"

# ---------------------------------------------------------------------------
# Clasificación de grupo SEEN/SED a partir de la taxonomía francesa de CIQUAL.
# Se examina el subgrupo (más fino) y luego el grupo, con reglas en orden de
# prioridad sobre el texto normalizado. Ante la duda, FoodGroup.OTHER.
# ---------------------------------------------------------------------------
_CIQUAL_GROUP_RULES: list[tuple[str, FoodGroup]] = [
    ("legumineuses", FoodGroup.LEGUME),
    ("coque", FoodGroup.NUTS),
    ("oleagineu", FoodGroup.NUTS),
    ("huile", FoodGroup.FAT),
    ("margarine", FoodGroup.FAT),
    ("beurre", FoodGroup.FAT),
    ("graisse", FoodGroup.FAT),
    ("matiere grasse", FoodGroup.FAT),
    ("charcuterie", FoodGroup.PROTEIN),
    ("viande", FoodGroup.PROTEIN),
    ("poisson", FoodGroup.PROTEIN),
    ("mollusque", FoodGroup.PROTEIN),
    ("crustace", FoodGroup.PROTEIN),
    ("produits de la mer", FoodGroup.PROTEIN),
    ("oeuf", FoodGroup.PROTEIN),
    ("carne", FoodGroup.PROTEIN),
    ("fromage", FoodGroup.DAIRY),
    ("lait", FoodGroup.DAIRY),
    ("produits laitiers", FoodGroup.DAIRY),
    ("creme", FoodGroup.DAIRY),
    ("pomme de terre", FoodGroup.STARCHY),
    ("tubercule", FoodGroup.STARCHY),
    ("pain", FoodGroup.STARCHY),
    ("pates riz et cereales", FoodGroup.STARCHY),
    ("cereales de petit", FoodGroup.STARCHY),
    ("barres cerealieres", FoodGroup.STARCHY),
    ("legume", FoodGroup.VEGETABLE),
    ("algue", FoodGroup.VEGETABLE),
    ("fruits", FoodGroup.FRUIT),
    ("chocolat", FoodGroup.SWEETS),
    ("confiserie", FoodGroup.SWEETS),
    ("confiture", FoodGroup.SWEETS),
    ("sucres", FoodGroup.SWEETS),
    ("biscuits sucres", FoodGroup.SWEETS),
    ("gateaux et patisseries", FoodGroup.SWEETS),
    ("viennoiserie", FoodGroup.SWEETS),
    ("glace", FoodGroup.SWEETS),
    ("sorbet", FoodGroup.SWEETS),
    ("dessert", FoodGroup.SWEETS),
    ("eaux", FoodGroup.BEVERAGE),
    ("boisson", FoodGroup.BEVERAGE),
    ("sauce", FoodGroup.SAUCES),
    ("condiment", FoodGroup.SAUCES),
    ("aides culinaires", FoodGroup.SAUCES),
    ("epice", FoodGroup.SAUCES),
    ("herbe", FoodGroup.SAUCES),
    ("sels", FoodGroup.SAUCES),
    ("ingredients divers", FoodGroup.SAUCES),
    ("plats composes", FoodGroup.PREPARED),
    ("pizza", FoodGroup.PREPARED),
    ("tarte", FoodGroup.PREPARED),
    ("crepe", FoodGroup.PREPARED),
    ("sandwich", FoodGroup.PREPARED),
    ("soupe", FoodGroup.PREPARED),
    ("feuilletee", FoodGroup.PREPARED),
    ("salades composees", FoodGroup.PREPARED),
    ("infantile", FoodGroup.PREPARED),
    ("plat", FoodGroup.PREPARED),
]


def classify_ciqual_food(group_fr: str, subgroup_fr: str) -> FoodGroup:
    """Deduce el FoodGroup SEEN/SED del grupo y subgrupo franceses de CIQUAL."""
    for text in (subgroup_fr, group_fr):
        norm = _normalize(text)
        for needle, group in _CIQUAL_GROUP_RULES:
            if needle in norm:
                return group
    return FoodGroup.OTHER


class CiqualFileNotFoundError(FileNotFoundError):
    """El fichero CIQUAL local no existe."""


def _resolve_columns(headers: list[str]) -> dict[str, list[str]]:
    """Empareja cada nutrient_id con las cabeceras REALES presentes (normalizando).

    Devuelve nutrient_id -> lista de cabeceras reales (en orden de preferencia)
    que existen en el fichero. Las cabeceras candidatas ausentes se descartan.
    """
    by_norm: dict[str, str] = {}
    for h in headers:
        by_norm.setdefault(_normalize(h), h)
    resolved: dict[str, list[str]] = {}
    for nutrient_id, candidates in CIQUAL_CANDIDATES.items():
        if nutrient_id not in NUTRIENTS_BY_ID:
            continue
        real_cols = [by_norm[_normalize(c)] for c in candidates if _normalize(c) in by_norm]
        if real_cols:
            resolved[nutrient_id] = real_cols
    return resolved


def _row_to_food(row: dict[str, object], resolved: dict[str, list[str]]) -> Food:
    nutrients: dict[str, NutrientValue] = {}
    for nutrient_id, real_cols in resolved.items():
        # Primer candidato con dato utilizable gana (energía UE > Jones, etc.).
        chosen: NutrientValue | None = None
        for col in real_cols:
            value = parse_cell(nutrient_id, row.get(col))
            if value.is_usable() or value.amount is not None:
                chosen = value
                break
            if chosen is None:
                chosen = value  # conserva el not_determined por si ninguno aporta
        if chosen is not None and (chosen.is_usable() or chosen.amount is not None):
            nutrients[nutrient_id] = chosen

    source_ref = str(row.get(COL_ID) or "").strip() or None
    # El código CIQUAL a veces llega como float ("24999.0"); normalízalo a entero.
    if source_ref and source_ref.endswith(".0"):
        source_ref = source_ref[:-2]
    name = str(row.get(COL_NAME) or "").strip()
    group_fr = str(row.get(COL_GROUP) or "").strip()
    subgroup_fr = str(row.get(COL_SUBGROUP) or "").strip()
    food_id = f"ciqual_{source_ref}" if source_ref else f"ciqual_{name or 'sin_id'}"

    return Food(
        id=food_id,
        name_es=name or food_id,
        group=classify_ciqual_food(group_fr, subgroup_fr),
        source=DataSource.CIQUAL,
        source_ref=source_ref,
        state=FoodState.RAW,
        edible_portion_factor=1.0,
        nutrients=nutrients,
        verified=True,
        subgroup=subgroup_fr or group_fr or None,
        image_name=None,
    )


def load_ciqual_xls(path: str | Path, *, sheet: str | int = "compo") -> list[Food]:
    """Parsea el XLS oficial de CIQUAL (hoja ``compo``) a una lista de Food.

    Requiere ``xlrd`` (formato .xls antiguo). No inventa datos: hueco →
    not_determined; ``traces`` / ``< X`` → trace.
    """
    import xlrd  # dependencia solo necesaria para .xls

    file_path = Path(path)
    if not file_path.exists():
        raise CiqualFileNotFoundError(
            f"No se encuentra el fichero CIQUAL en «{file_path}». Descárgalo desde "
            f"https://ciqual.anses.fr/ y colócalo ahí. Sin fichero no hay datos."
        )

    book = xlrd.open_workbook(str(file_path))
    sh = book.sheet_by_name(sheet) if isinstance(sheet, str) else book.sheet_by_index(sheet)
    headers = [str(sh.cell_value(0, c)) for c in range(sh.ncols)]
    resolved = _resolve_columns(headers)

    foods: list[Food] = []
    for r in range(1, sh.nrows):
        row = {headers[c]: sh.cell_value(r, c) for c in range(sh.ncols)}
        # Salta filas de "aliment moyen" agregadas y filas sin nombre real.
        name = str(row.get(COL_NAME) or "").strip()
        if not name:
            continue
        foods.append(_row_to_food(row, resolved))
    return foods


def load_ciqual_csv(path: str | Path, *, delimiter: str = ";", encoding: str = "utf-8-sig") -> list[Food]:
    """Parsea un CSV de CIQUAL local a una lista de Food.

    Lanza ``CiqualFileNotFoundError`` con mensaje claro si el fichero no existe.
    No inventa datos: hueco → not_determined; ``traces`` / ``< X`` → trace.
    """
    file_path = Path(path)
    if not file_path.exists():
        raise CiqualFileNotFoundError(
            f"No se encuentra el fichero CIQUAL en «{file_path}». Descárgalo desde "
            f"https://ciqual.anses.fr/ (exporta la tabla como CSV/XLS) y colócalo en "
            f"esa ruta. Sin fichero no hay datos y no se fabrica nada."
        )

    with file_path.open("r", encoding=encoding, newline="") as fh:
        reader = csv.DictReader(fh, delimiter=delimiter)
        headers = reader.fieldnames or []
        resolved = _resolve_columns(list(headers))
        foods: list[Food] = []
        for row in reader:
            foods.append(_row_to_food(dict(row), resolved))
    return foods
