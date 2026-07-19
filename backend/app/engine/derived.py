"""Cálculos derivados útiles para dietética.

Dos utilidades sobre valores ya calculados:

1. `macro_energy_split`: reparto de macronutrientes en porcentaje de la energía,
   usando los factores de Atwater (kcal por gramo):
       proteína = 4, hidratos = 4, grasa = 9, alcohol = 7.

2. `energy_check`: valida que la energía declarada de un alimento o plato cuadra
   con la que se obtiene de sus macros, dentro de una tolerancia. Útil para
   detectar errores de codificación en la base o incoherencias de la fuente.

Ambas trabajan con gramos en float y devuelven dataclasses tipadas. No tocan los
modelos canónicos: son helpers internos del motor.
"""
from __future__ import annotations

from dataclasses import dataclass

# Factores de Atwater en kcal por gramo.
KCAL_PER_G_PROTEIN = 4.0
KCAL_PER_G_CARBS = 4.0
KCAL_PER_G_FAT = 9.0
KCAL_PER_G_ALCOHOL = 7.0


@dataclass(frozen=True)
class MacroEnergyDistribution:
    """Reparto de la energía por macronutriente, en % del total energético."""

    protein_pct: float
    carbs_pct: float
    fat_pct: float
    alcohol_pct: float
    energy_from_macros_kcal: float


@dataclass(frozen=True)
class EnergyCheck:
    """Resultado del cuadre entre energía declarada y energía de los macros."""

    declared_kcal: float
    computed_kcal: float
    difference_kcal: float          # declarada − computada
    within_tolerance: bool


def macro_energy_split(
    protein_g: float,
    carbs_g: float,
    fat_g: float,
    alcohol_g: float = 0.0,
    *,
    ndigits: int = 1,
) -> MacroEnergyDistribution:
    """Reparte la energía entre los macros y devuelve el % de cada uno.

    Si no hay energía de macros (todo 0), devuelve porcentajes 0 sin dividir por 0.
    """
    kcal_protein = protein_g * KCAL_PER_G_PROTEIN
    kcal_carbs = carbs_g * KCAL_PER_G_CARBS
    kcal_fat = fat_g * KCAL_PER_G_FAT
    kcal_alcohol = alcohol_g * KCAL_PER_G_ALCOHOL
    total = kcal_protein + kcal_carbs + kcal_fat + kcal_alcohol

    if total <= 0.0:
        return MacroEnergyDistribution(0.0, 0.0, 0.0, 0.0, 0.0)

    return MacroEnergyDistribution(
        protein_pct=round(kcal_protein / total * 100, ndigits),
        carbs_pct=round(kcal_carbs / total * 100, ndigits),
        fat_pct=round(kcal_fat / total * 100, ndigits),
        alcohol_pct=round(kcal_alcohol / total * 100, ndigits),
        energy_from_macros_kcal=round(total, ndigits),
    )


def energy_check(
    declared_kcal: float,
    protein_g: float,
    carbs_g: float,
    fat_g: float,
    alcohol_g: float = 0.0,
    *,
    tolerance_pct: float = 5.0,
    tolerance_abs_kcal: float = 10.0,
) -> EnergyCheck:
    """Comprueba que la energía declarada cuadra con la de los macros.

    La tolerancia efectiva es la mayor entre un porcentaje de la energía declarada
    y un mínimo absoluto en kcal, para no ser demasiado estricto con valores bajos.
    """
    computed = (
        protein_g * KCAL_PER_G_PROTEIN
        + carbs_g * KCAL_PER_G_CARBS
        + fat_g * KCAL_PER_G_FAT
        + alcohol_g * KCAL_PER_G_ALCOHOL
    )
    difference = declared_kcal - computed
    tolerance = max(tolerance_abs_kcal, abs(declared_kcal) * tolerance_pct / 100.0)

    return EnergyCheck(
        declared_kcal=round(declared_kcal, 4),
        computed_kcal=round(computed, 4),
        difference_kcal=round(difference, 4),
        within_tolerance=abs(difference) <= tolerance,
    )
