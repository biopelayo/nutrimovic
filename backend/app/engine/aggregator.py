"""Agregación de platos: suma de varios alimentos con sus gramajes.

Calcula el aporte de cada ítem (delegando en la calculadora por gramaje) y suma
los nutrientes a lo largo del plato respetando la regla de oro del contrato §1.2:
nunca se confunde 0 con ausencia de dato.

Regla de suma de estados (decisión de diseño, importante)
---------------------------------------------------------
Para cada nutriente se consideran solo los alimentos que **lo aportan**, es decir,
aquellos cuya composición incluye ese nutriente (la fuente lo reporta, con el
estado que sea). Un alimento que ni siquiera declara el nutriente no es un
contribuyente y no arrastra el total a `not_determined` (si lo hiciera, casi
ningún plato tendría totales utilizables, porque ninguna fuente reporta los ~45
nutrientes de todos los alimentos).

Entre los contribuyentes:
- Si **alguno** aporta el nutriente como `not_determined`, el total es
  `not_determined` con `amount=None`. No se trata como 0: la constancia de que el
  dato falta queda registrada en el propio estado del total.
- Si **todos** están medidos (`measured`/`trace`), el total es la suma de sus
  aportes. El estado resultante es `measured` si al menos uno es `measured`, y
  `trace` solo cuando todos son `trace`.
"""
from __future__ import annotations

from app.core.models import (
    MeasurementStatus,
    PlateItem,
    PlateResult,
    PortionResult,
    ResultValue,
)
from app.core.nutrients import unit_for
from app.engine.calculator import calculate_portion


def calculate_plate(items: list[PlateItem], repo) -> PlateResult:
    """Suma los nutrientes de varios alimentos con sus gramajes.

    `repo` es cualquier objeto con `get(food_id) -> Food | None` (el
    `FoodRepository` del proyecto lo cumple). Lanza `ValueError` si algún
    `food_id` no existe.
    """
    portions: list[PortionResult] = []
    total_grams = 0.0

    for item in items:
        food = repo.get(item.food_id)
        if food is None:
            raise ValueError(f"Alimento no encontrado: {item.food_id!r}")
        portions.append(calculate_portion(food, item.grams, use_edible_portion=True))
        total_grams += item.grams

    totals = _sum_nutrients(portions)

    return PlateResult(
        items=portions,
        totals=totals,
        total_grams=round(total_grams, 4),
    )


def _sum_nutrients(portions: list[PortionResult]) -> dict[str, ResultValue]:
    """Suma nutriente a nutriente aplicando la regla de propagación de estados."""
    # Conjunto de todos los nutrientes que aparecen en algún ítem (los que se aportan).
    nutrient_ids: list[str] = []
    seen: set[str] = set()
    for portion in portions:
        for nid in portion.nutrients:
            if nid not in seen:
                seen.add(nid)
                nutrient_ids.append(nid)

    totals: dict[str, ResultValue] = {}
    for nid in nutrient_ids:
        contributions = [
            portion.nutrients[nid] for portion in portions if nid in portion.nutrients
        ]
        unit = unit_for(nid)

        # Si algún contribuyente no está determinado, el total tampoco lo está.
        if any(c.status == MeasurementStatus.NOT_DETERMINED for c in contributions):
            totals[nid] = ResultValue(
                amount=None, unit=unit, status=MeasurementStatus.NOT_DETERMINED
            )
            continue

        total_amount = sum((c.amount or 0.0) for c in contributions)
        # measured domina sobre trace; trace solo si todos los aportes son trace.
        status = (
            MeasurementStatus.MEASURED
            if any(c.status == MeasurementStatus.MEASURED for c in contributions)
            else MeasurementStatus.TRACE
        )
        totals[nid] = ResultValue(amount=round(total_amount, 4), unit=unit, status=status)

    return totals
