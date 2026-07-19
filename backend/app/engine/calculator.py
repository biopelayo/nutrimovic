"""Motor de cálculo por gramaje (esbozo base).

Implementación mínima funcional de la funcionalidad estrella: dado un alimento y
un peso en gramos, devuelve el valor de cada nutriente para ese peso. El agente
del motor robustece este módulo (agregación de platos, factores de cocción,
casos límite) y añade la batería de tests.
"""
from __future__ import annotations

import math

from app.core.models import (
    Food,
    MeasurementStatus,
    PortionResult,
    ResultValue,
)
from app.core.nutrients import unit_for


def calculate_portion(food: Food, grams: float, use_edible_portion: bool = True) -> PortionResult:
    """Calcula los nutrientes de `food` para `grams` gramos.

    Regla (contrato §2.2): amount = value_per_100g * (grams_edible / 100),
    con grams_edible = grams * edible_portion_factor cuando `use_edible_portion`.

    El estado (measured/trace/not_determined) se propaga: un valor no determinado
    en la base nunca se rellena con 0, y un gramaje 0 sí produce 0 en los medidos.
    """
    if not math.isfinite(grams):
        raise ValueError("El gramaje debe ser un número finito.")
    if grams < 0:
        raise ValueError("El gramaje no puede ser negativo.")

    factor = food.edible_portion_factor if use_edible_portion else 1.0
    grams_edible = grams * factor
    scale = grams_edible / 100.0

    nutrients: dict[str, ResultValue] = {}
    for nutrient_id, value in food.nutrients.items():
        unit = unit_for(nutrient_id)
        if value.is_usable() and value.amount is not None:
            nutrients[nutrient_id] = ResultValue(
                amount=round(value.amount * scale, 4),
                unit=unit,
                status=value.status,
            )
        else:
            nutrients[nutrient_id] = ResultValue(
                amount=None, unit=unit, status=MeasurementStatus.NOT_DETERMINED
            )

    return PortionResult(
        food_id=food.id,
        name_es=food.name_es,
        grams=grams,
        grams_edible=round(grams_edible, 2),
        nutrients=nutrients,
    )
