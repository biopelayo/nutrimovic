"""Utilidades compartidas para parsear valores de fuentes tabulares.

BEDCA y CIQUAL exportan celdas de texto donde hay que distinguir tres cosas:
número medido, traza y dato no reportado. Este módulo centraliza esa regla
para que ambos loaders la apliquen igual.
"""
from __future__ import annotations

from app.core.models import MeasurementStatus, NutrientValue

# Marcadores de "no determinado" habituales en BEDCA/CIQUAL.
_NOT_DETERMINED_TOKENS = {"", "-", "nd", "n.d.", "na", "n/a", "null", "none", "s/d"}
# Marcadores de traza.
_TRACE_TOKENS = {"traces", "trace", "tr", "traza", "trazas", "<lq", "<loq"}


def parse_cell(nutrient_id: str, raw_value: object) -> NutrientValue:
    """Convierte una celda cruda en un NutrientValue con el status correcto.

    Reglas:
      - Vacío o marcador de no reportado -> not_determined (amount None).
      - Marcador de traza o "<X"          -> trace (amount None; ~0 pero marcado).
      - Número (coma o punto decimal)     -> measured con su valor.
      - Cualquier otra cosa no parseable  -> not_determined (prudencia).
    """
    if raw_value is None:
        return NutrientValue(nutrient_id=nutrient_id, status=MeasurementStatus.NOT_DETERMINED)

    text = str(raw_value).strip()
    token = text.lower()

    if token in _NOT_DETERMINED_TOKENS:
        return NutrientValue(nutrient_id=nutrient_id, status=MeasurementStatus.NOT_DETERMINED)

    if token in _TRACE_TOKENS or token.startswith("<"):
        return NutrientValue(nutrient_id=nutrient_id, status=MeasurementStatus.TRACE)

    # Decimal europeo: coma como separador decimal, sin separador de millares.
    normalized = text.replace(" ", "").replace(",", ".")
    try:
        amount = float(normalized)
    except ValueError:
        return NutrientValue(nutrient_id=nutrient_id, status=MeasurementStatus.NOT_DETERMINED)

    return NutrientValue(
        nutrient_id=nutrient_id, amount=amount, status=MeasurementStatus.MEASURED
    )
