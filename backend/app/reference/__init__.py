"""Módulo de referencias nutricionales de NutriMovic.

Expone dos sistemas de referencia complementarios:

- **VRN (Valores de Referencia de Nutrientes)** del Reglamento (UE) 1169/2011,
  Anexo XIII. Valor único para etiquetado (adulto medio). Ver `vrn_ue`.
- **Valores de referencia EFSA (Dietary Reference Values)** por perfil
  (sexo, edad, embarazo/lactancia, nivel de actividad). Más precisos para
  dietética. Ver `profiles`.

La función de cobertura vive en `coverage`.

------------------------------------------------------------------------------
AVISO / DISCLAIMER
Estos valores apoyan el diseño de dietas y la interpretación de etiquetas.
NO constituyen consejo médico ni nutricional individualizado y NO sustituyen la
valoración de un profesional sanitario (médico, dietista-nutricionista
colegiado). Las necesidades reales varían con el estado de salud, la
medicación, la composición corporal y otros factores clínicos.
------------------------------------------------------------------------------
"""
from __future__ import annotations

from app.reference.coverage import CoverageValue, coverage, vrn_reference
from app.reference.profiles import (
    ActivityLevel,
    LifeStage,
    Profile,
    Sex,
    efsa_reference_values,
)
from app.reference.vrn_ue import REFERENCE_INTAKES_UE, VRN_UE

DISCLAIMER_ES = (
    "Los valores de referencia (VRN del Reglamento UE 1169/2011 y DRV de EFSA) "
    "apoyan el diseño de dietas y la lectura de etiquetas. No son consejo médico "
    "ni sustituyen la valoración de un profesional sanitario."
)

__all__ = [
    "VRN_UE",
    "REFERENCE_INTAKES_UE",
    "Profile",
    "Sex",
    "LifeStage",
    "ActivityLevel",
    "efsa_reference_values",
    "coverage",
    "vrn_reference",
    "CoverageValue",
    "DISCLAIMER_ES",
]
