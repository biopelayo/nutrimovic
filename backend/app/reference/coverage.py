"""Cálculo de cobertura frente a una referencia (VRN o perfil EFSA).

% de cobertura = (nutriente aportado / valor de referencia) × 100.

Regla de oro (contrato NutriMovic): nunca se confunde 0 con ausencia de dato.
- Si el nutriente no tiene valor de referencia -> `coverage_pct = None`.
- Si el aporte llega como `not_determined` -> `coverage_pct = None` (se propaga).
- Un aporte real de 0 sí da 0 % (es un dato, no un hueco).

AVISO: apoya el diseño de dietas; no sustituye al profesional sanitario.
"""
from __future__ import annotations

from typing import Union

from pydantic import BaseModel

from app.core.models import MeasurementStatus
from app.core.nutrients import unit_for
from app.reference.profiles import Profile, efsa_reference_values
from app.reference.vrn_ue import REFERENCE_INTAKES_UE, VRN_UE

# Tipos de entrada admitidos para los totales aportados por nutriente.
IntakeLike = Union[float, int, "dict", object, None]
ReferenceLike = Union[str, Profile, dict]


class CoverageValue(BaseModel):
    """Cobertura de un nutriente frente a la referencia elegida."""

    nutrient_id: str
    intake_amount: float | None = None
    reference_amount: float | None = None
    unit: str = ""
    coverage_pct: float | None = None
    status: MeasurementStatus = MeasurementStatus.NOT_DETERMINED
    reference_kind: str = ""  # "vrn" | "efsa"
    note: str | None = None


def vrn_reference() -> dict[str, float]:
    """Referencia VRN combinada (Reglamento UE 1169/2011, Anexo XIII A + B).

    Une los VRN de vitaminas y minerales (Parte A) con las ingestas de
    referencia de energía y macros (Parte B). Es la referencia de etiquetado.
    """
    merged: dict[str, float] = {}
    merged.update(REFERENCE_INTAKES_UE)
    merged.update(VRN_UE)
    return merged


def _parse_intake(raw: IntakeLike) -> tuple[float | None, MeasurementStatus]:
    """Normaliza un aporte a (cantidad, estado).

    Acepta:
    - número -> (valor, MEASURED)
    - None -> (None, NOT_DETERMINED)
    - objeto/dict con `amount` y opcional `status` (p. ej. ResultValue).
    """
    if raw is None:
        return None, MeasurementStatus.NOT_DETERMINED
    if isinstance(raw, (int, float)):
        return float(raw), MeasurementStatus.MEASURED

    # dict o modelo con atributos
    amount = raw.get("amount") if isinstance(raw, dict) else getattr(raw, "amount", None)
    status = raw.get("status") if isinstance(raw, dict) else getattr(raw, "status", None)

    if status is None:
        status = (
            MeasurementStatus.NOT_DETERMINED if amount is None else MeasurementStatus.MEASURED
        )
    elif not isinstance(status, MeasurementStatus):
        status = MeasurementStatus(str(status))

    amount = None if amount is None else float(amount)
    return amount, status


def _resolve_reference(reference: ReferenceLike) -> tuple[dict[str, float | None], str]:
    """Devuelve (dict de referencia por nutrient_id, etiqueta de tipo)."""
    if isinstance(reference, str):
        key = reference.strip().lower()
        if key == "vrn":
            return dict(vrn_reference()), "vrn"
        raise ValueError(
            f"Referencia desconocida: {reference!r}. Use 'vrn' o un Profile."
        )
    if isinstance(reference, Profile):
        return efsa_reference_values(reference), "efsa"
    if isinstance(reference, dict):
        return dict(reference), "custom"
    raise TypeError(
        "reference debe ser 'vrn', un Profile o un dict de referencia."
    )


def coverage(
    totals: dict[str, IntakeLike],
    reference: ReferenceLike,
) -> dict[str, CoverageValue]:
    """% de cobertura por nutriente frente a `reference`.

    Args:
        totals: dict nutrient_id -> aporte. El aporte puede ser un número, un
            `ResultValue`/objeto con `amount`+`status`, un dict equivalente o
            None.
        reference: `'vrn'` para el VRN del Reglamento UE 1169/2011, un `Profile`
            para valores EFSA, o un dict nutrient_id -> valor de referencia.

    Returns:
        dict nutrient_id -> `CoverageValue`. Se incluye la unión de nutrientes
        presentes en `totals` y en la referencia. `coverage_pct` es `None` si
        falta referencia o si el aporte no es utilizable (not_determined).
    """
    ref_map, kind = _resolve_reference(reference)

    result: dict[str, CoverageValue] = {}
    nutrient_ids = set(totals) | set(ref_map)

    for nid in nutrient_ids:
        intake_amount, status = _parse_intake(totals.get(nid))
        ref_amount = ref_map.get(nid)

        pct: float | None = None
        note: str | None = None

        if ref_amount is None:
            note = "Sin valor de referencia para este nutriente y referencia."
        elif status is MeasurementStatus.NOT_DETERMINED or intake_amount is None:
            note = "Aporte no determinado: la cobertura se propaga como no disponible."
        elif ref_amount == 0:
            note = "Valor de referencia 0: cobertura no calculable."
        else:
            pct = round(intake_amount / ref_amount * 100.0, 1)

        result[nid] = CoverageValue(
            nutrient_id=nid,
            intake_amount=intake_amount,
            reference_amount=ref_amount,
            unit=unit_for(nid),
            coverage_pct=pct,
            status=status,
            reference_kind=kind,
            note=note,
        )

    return result


__all__ = ["CoverageValue", "coverage", "vrn_reference"]
