"""Catálogo canónico de nutrientes de NutriMovic.

Fuente de verdad de qué nutrientes maneja el sistema y en qué unidad.
Los códigos de mapeo (usda_ids, bedca_ids, ciqual_ids) los completa el módulo ETL
al integrar cada fuente. Aquí quedan preparados y, donde se conocen, rellenados.
"""
from __future__ import annotations

from app.core.models import NutrientCategory, NutrientDef

# Orden estable: energía, macros, desglose de grasas, desglose de hidratos,
# vitaminas liposolubles, vitaminas hidrosolubles, minerales, oligoelementos.
NUTRIENTS: list[NutrientDef] = [
    # --- Energía ---
    NutrientDef(id="energy_kcal", name_es="Energía", unit="kcal", category=NutrientCategory.ENERGY, usda_ids=[1008]),
    NutrientDef(id="energy_kj", name_es="Energía", unit="kJ", category=NutrientCategory.ENERGY, usda_ids=[1062]),
    # --- Macronutrientes ---
    NutrientDef(id="protein_g", name_es="Proteína", unit="g", category=NutrientCategory.MACRO, usda_ids=[1003]),
    NutrientDef(id="fat_g", name_es="Grasa total", unit="g", category=NutrientCategory.MACRO, usda_ids=[1004]),
    NutrientDef(id="carbs_g", name_es="Hidratos de carbono", unit="g", category=NutrientCategory.MACRO, usda_ids=[1005]),
    NutrientDef(id="fiber_g", name_es="Fibra alimentaria", unit="g", category=NutrientCategory.MACRO, usda_ids=[1079]),
    NutrientDef(id="water_g", name_es="Agua", unit="g", category=NutrientCategory.MACRO, usda_ids=[1051]),
    NutrientDef(id="alcohol_g", name_es="Alcohol", unit="g", category=NutrientCategory.MACRO, usda_ids=[1018]),
    NutrientDef(id="ash_g", name_es="Cenizas", unit="g", category=NutrientCategory.MACRO, usda_ids=[1007]),
    # --- Desglose de grasas ---
    NutrientDef(id="fat_saturated_g", name_es="Ácidos grasos saturados", unit="g", category=NutrientCategory.FAT_DETAIL, usda_ids=[1258]),
    NutrientDef(id="fat_monounsaturated_g", name_es="Ácidos grasos monoinsaturados", unit="g", category=NutrientCategory.FAT_DETAIL, usda_ids=[1292]),
    NutrientDef(id="fat_polyunsaturated_g", name_es="Ácidos grasos poliinsaturados", unit="g", category=NutrientCategory.FAT_DETAIL, usda_ids=[1293]),
    NutrientDef(id="fat_trans_g", name_es="Ácidos grasos trans", unit="g", category=NutrientCategory.FAT_DETAIL, usda_ids=[1257]),
    NutrientDef(id="cholesterol_mg", name_es="Colesterol", unit="mg", category=NutrientCategory.FAT_DETAIL, usda_ids=[1253]),
    NutrientDef(id="omega3_g", name_es="Omega-3", unit="g", category=NutrientCategory.FAT_DETAIL),
    NutrientDef(id="omega6_g", name_es="Omega-6", unit="g", category=NutrientCategory.FAT_DETAIL),
    # --- Desglose de hidratos ---
    NutrientDef(id="sugars_g", name_es="Azúcares totales", unit="g", category=NutrientCategory.CARB_DETAIL, usda_ids=[2000]),
    NutrientDef(id="sugars_added_g", name_es="Azúcares añadidos", unit="g", category=NutrientCategory.CARB_DETAIL, usda_ids=[1235]),
    NutrientDef(id="starch_g", name_es="Almidón", unit="g", category=NutrientCategory.CARB_DETAIL, usda_ids=[1009]),
    NutrientDef(id="polyols_g", name_es="Polioles", unit="g", category=NutrientCategory.CARB_DETAIL),
    # --- Vitaminas liposolubles ---
    NutrientDef(id="vit_a_ug_rae", name_es="Vitamina A", unit="µg RAE", category=NutrientCategory.VITAMIN, usda_ids=[1106]),
    NutrientDef(id="vit_d_ug", name_es="Vitamina D", unit="µg", category=NutrientCategory.VITAMIN, usda_ids=[1114]),
    NutrientDef(id="vit_e_mg", name_es="Vitamina E", unit="mg α-tocoferol", category=NutrientCategory.VITAMIN, usda_ids=[1109]),
    NutrientDef(id="vit_k_ug", name_es="Vitamina K", unit="µg", category=NutrientCategory.VITAMIN, usda_ids=[1185]),
    # --- Vitaminas hidrosolubles ---
    NutrientDef(id="vit_c_mg", name_es="Vitamina C", unit="mg", category=NutrientCategory.VITAMIN, usda_ids=[1162]),
    NutrientDef(id="vit_b1_mg", name_es="Tiamina (B1)", unit="mg", category=NutrientCategory.VITAMIN, usda_ids=[1165]),
    NutrientDef(id="vit_b2_mg", name_es="Riboflavina (B2)", unit="mg", category=NutrientCategory.VITAMIN, usda_ids=[1166]),
    NutrientDef(id="vit_b3_mg_ne", name_es="Niacina (B3)", unit="mg NE", category=NutrientCategory.VITAMIN, usda_ids=[1167]),
    NutrientDef(id="vit_b5_mg", name_es="Ácido pantoténico (B5)", unit="mg", category=NutrientCategory.VITAMIN, usda_ids=[1170]),
    NutrientDef(id="vit_b6_mg", name_es="Vitamina B6", unit="mg", category=NutrientCategory.VITAMIN, usda_ids=[1175]),
    NutrientDef(id="vit_b7_ug", name_es="Biotina (B7)", unit="µg", category=NutrientCategory.VITAMIN, usda_ids=[1176]),
    NutrientDef(id="vit_b9_ug_dfe", name_es="Folato (B9)", unit="µg DFE", category=NutrientCategory.VITAMIN, usda_ids=[1177]),
    NutrientDef(id="vit_b12_ug", name_es="Vitamina B12", unit="µg", category=NutrientCategory.VITAMIN, usda_ids=[1178]),
    # --- Minerales mayores ---
    NutrientDef(id="calcium_mg", name_es="Calcio", unit="mg", category=NutrientCategory.MINERAL, usda_ids=[1087]),
    NutrientDef(id="iron_mg", name_es="Hierro", unit="mg", category=NutrientCategory.MINERAL, usda_ids=[1089]),
    NutrientDef(id="magnesium_mg", name_es="Magnesio", unit="mg", category=NutrientCategory.MINERAL, usda_ids=[1090]),
    NutrientDef(id="phosphorus_mg", name_es="Fósforo", unit="mg", category=NutrientCategory.MINERAL, usda_ids=[1091]),
    NutrientDef(id="potassium_mg", name_es="Potasio", unit="mg", category=NutrientCategory.MINERAL, usda_ids=[1092]),
    NutrientDef(id="sodium_mg", name_es="Sodio", unit="mg", category=NutrientCategory.MINERAL, usda_ids=[1093]),
    NutrientDef(id="zinc_mg", name_es="Zinc", unit="mg", category=NutrientCategory.MINERAL, usda_ids=[1095]),
    NutrientDef(id="copper_mg", name_es="Cobre", unit="mg", category=NutrientCategory.MINERAL, usda_ids=[1098]),
    NutrientDef(id="manganese_mg", name_es="Manganeso", unit="mg", category=NutrientCategory.MINERAL, usda_ids=[1101]),
    # --- Oligoelementos ---
    NutrientDef(id="selenium_ug", name_es="Selenio", unit="µg", category=NutrientCategory.MINERAL, usda_ids=[1103]),
    NutrientDef(id="iodine_ug", name_es="Yodo", unit="µg", category=NutrientCategory.MINERAL, usda_ids=[1100]),
    NutrientDef(id="chromium_ug", name_es="Cromo", unit="µg", category=NutrientCategory.MINERAL, usda_ids=[1096]),
    NutrientDef(id="molybdenum_ug", name_es="Molibdeno", unit="µg", category=NutrientCategory.MINERAL, usda_ids=[1102]),
    NutrientDef(id="fluoride_mg", name_es="Flúor", unit="mg", category=NutrientCategory.MINERAL, usda_ids=[1099]),
]

# Índices de acceso rápido.
NUTRIENTS_BY_ID: dict[str, NutrientDef] = {n.id: n for n in NUTRIENTS}


def get_nutrient(nutrient_id: str) -> NutrientDef | None:
    return NUTRIENTS_BY_ID.get(nutrient_id)


def unit_for(nutrient_id: str) -> str:
    n = NUTRIENTS_BY_ID.get(nutrient_id)
    return n.unit if n else ""
