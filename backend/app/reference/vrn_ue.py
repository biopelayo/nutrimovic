"""Valores de Referencia de Nutrientes (VRN) del Reglamento (UE) 1169/2011.

Fuente: Reglamento (UE) n.º 1169/2011 del Parlamento Europeo y del Consejo, de
25 de octubre de 2011, sobre la información alimentaria facilitada al consumidor.
Anexo XIII.

- `VRN_UE`  -> Anexo XIII, Parte A, punto 1: «Vitaminas y minerales que pueden
  declararse y sus valores de referencia de nutrientes (VRN)». Valor único para
  el adulto medio, usado en el etiquetado.
- `REFERENCE_INTAKES_UE` -> Anexo XIII, Parte B: «Ingestas de referencia de
  energía y determinados nutrientes distintos de las vitaminas y los minerales
  (adultos)». Son las «cantidades diarias orientativas» del etiquetado.

Reglas seguidas:
- Solo se incluyen valores OFICIALES del reglamento.
- Se usan los `nutrient_id` canónicos de `app.core.nutrients` como clave.
- Los nutrientes de nuestro catálogo SIN VRN oficial no aparecen aquí
  (p. ej. el sodio no tiene VRN en la Parte A). No se inventan cifras.

AVISO: apoya el diseño de dietas y la lectura de etiquetas; no sustituye al
profesional sanitario.
"""
from __future__ import annotations

# --- Anexo XIII, Parte A, punto 1 (VRN de vitaminas y minerales) -------------
# Clave = nutrient_id canónico; valor = cantidad VRN en la unidad del catálogo.
# Los comentarios anotan el nombre y la unidad tal cual figuran en el reglamento.
VRN_UE: dict[str, float] = {
    # Vitaminas
    "vit_a_ug_rae": 800.0,   # Vitamina A: 800 µg
    "vit_d_ug": 5.0,         # Vitamina D: 5 µg
    "vit_e_mg": 12.0,        # Vitamina E: 12 mg
    "vit_k_ug": 75.0,        # Vitamina K: 75 µg
    "vit_c_mg": 80.0,        # Vitamina C: 80 mg
    "vit_b1_mg": 1.1,        # Tiamina: 1,1 mg
    "vit_b2_mg": 1.4,        # Riboflavina: 1,4 mg
    "vit_b3_mg_ne": 16.0,    # Niacina: 16 mg
    "vit_b5_mg": 6.0,        # Ácido pantoténico: 6 mg
    "vit_b6_mg": 1.4,        # Vitamina B6: 1,4 mg
    "vit_b7_ug": 50.0,       # Biotina: 50 µg
    "vit_b9_ug_dfe": 200.0,  # Ácido fólico: 200 µg
    "vit_b12_ug": 2.5,       # Vitamina B12: 2,5 µg
    # Minerales
    "potassium_mg": 2000.0,  # Potasio: 2000 mg
    "calcium_mg": 800.0,     # Calcio: 800 mg
    "phosphorus_mg": 700.0,  # Fósforo: 700 mg
    "magnesium_mg": 375.0,   # Magnesio: 375 mg
    "iron_mg": 14.0,         # Hierro: 14 mg
    "zinc_mg": 10.0,         # Zinc: 10 mg
    "copper_mg": 1.0,        # Cobre: 1 mg
    "manganese_mg": 2.0,     # Manganeso: 2 mg
    "selenium_ug": 55.0,     # Selenio: 55 µg
    "iodine_ug": 150.0,      # Yodo: 150 µg
    "chromium_ug": 40.0,     # Cromo: 40 µg
    "molybdenum_ug": 50.0,   # Molibdeno: 50 µg
    "fluoride_mg": 3.5,      # Flúor (fluoruro): 3,5 mg
}
# Nota sobre cobertura del catálogo:
# - Anexo XIII Parte A también fija Cloruro = 800 mg, que no está en nuestro
#   catálogo, por lo que se omite.
# - Sodio: NO tiene VRN en la Parte A. Se deja fuera a propósito (no es 0).

# --- Anexo XIII, Parte B (ingestas de referencia, adulto medio) --------------
# Energía y macronutrientes. Valores únicos orientativos del etiquetado.
REFERENCE_INTAKES_UE: dict[str, float] = {
    "energy_kj": 8400.0,       # Energía: 8400 kJ
    "energy_kcal": 2000.0,     # Energía: 2000 kcal
    "fat_g": 70.0,             # Grasas: 70 g
    "fat_saturated_g": 20.0,   # Ácidos grasos saturados: 20 g
    "carbs_g": 260.0,          # Hidratos de carbono: 260 g
    "sugars_g": 90.0,          # Azúcares: 90 g
    "protein_g": 50.0,         # Proteínas: 50 g
    # Sodio derivado de la sal de referencia (6 g de sal = 2400 mg de sodio,
    # aplicando el factor oficial 1 g sal = 400 mg Na del propio reglamento).
    "sodium_mg": 2400.0,       # Derivado de «Sal: 6 g»
}
# Nota: la Parte B declara «Sal: 6 g»; nuestro catálogo no tiene un nutriente
# `salt`, así que se expone el sodio equivalente (conversión determinista, no
# una cifra inventada). La fibra no figura entre las ingestas de referencia de
# la Parte B, por lo que no se incluye aquí (EFSA sí le asigna una AI: ver
# `profiles`).

__all__ = ["VRN_UE", "REFERENCE_INTAKES_UE"]
