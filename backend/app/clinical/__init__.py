"""Motor clínico de NutriMovic.

Perfil de paciente, antropometría y objetivos energéticos. Es la base del
cálculo de la dieta personalizada para consulta de nutrición y endocrino.

AVISO CLÍNICO
-------------
Las fórmulas de este módulo (IMC, peso ideal, gasto energético, reparto de
macronutrientes) son estimaciones poblacionales estándar. **Apoyan la decisión
clínica; no la sustituyen.** El juicio del profesional sanitario, la historia
del paciente y las pruebas complementarias siempre prevalecen sobre cualquier
número que devuelva este motor.
"""
from __future__ import annotations

from app.clinical.anthropometry import (
    bmi,
    bmi_category,
    body_metrics,
    ideal_weight,
    waist_hip_ratio,
    whr_risk,
    weight_change_pct,
)
from app.clinical.energy import (
    bmr_harris_benedict,
    bmr_mifflin,
    energy_target,
    macro_targets,
    tdee,
)
from app.clinical.models import (
    ActivityLevel,
    AnthroRecord,
    BMICategory,
    BodyMetrics,
    EnergyTargets,
    Goal,
    IdealWeight,
    MacroTargets,
    Patient,
    RiskLevel,
    Sex,
    WaistHipRatio,
)

DISCLAIMER = (
    "Estas estimaciones apoyan la decisión clínica; no la sustituyen. "
    "El criterio del profesional sanitario prevalece."
)

__all__ = [
    "ActivityLevel",
    "AnthroRecord",
    "BMICategory",
    "BodyMetrics",
    "DISCLAIMER",
    "EnergyTargets",
    "Goal",
    "IdealWeight",
    "MacroTargets",
    "Patient",
    "RiskLevel",
    "Sex",
    "WaistHipRatio",
    "bmi",
    "bmi_category",
    "bmr_harris_benedict",
    "bmr_mifflin",
    "body_metrics",
    "energy_target",
    "ideal_weight",
    "macro_targets",
    "tdee",
    "waist_hip_ratio",
    "weight_change_pct",
    "whr_risk",
]
