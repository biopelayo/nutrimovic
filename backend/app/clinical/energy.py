"""Gasto energético y reparto de macronutrientes de NutriMovic.

Metabolismo basal (Mifflin-St Jeor y Harris-Benedict), gasto total diario
(TDEE), objetivo calórico según el objetivo de peso y reparto de proteína,
grasa e hidratos de carbono.

Todas las fórmulas son estimaciones poblacionales estándar. **Apoyan la
decisión clínica; no la sustituyen.** El profesional sanitario ajusta el
objetivo al paciente concreto y supervisa cualquier restricción calórica.
"""
from __future__ import annotations

from app.clinical.models import (
    ActivityLevel,
    EnergyTargets,
    Goal,
    MacroTargets,
    Sex,
)

# Energía metabolizable por gramo de macronutriente (factores de Atwater), kcal.
KCAL_PER_G_PROTEIN = 4.0
KCAL_PER_G_CARB = 4.0
KCAL_PER_G_FAT = 9.0

# Suelos de seguridad de ingesta calórica diaria recomendados para dietas
# hipocalóricas sin supervisión estrecha (kcal/día).
SAFETY_FLOOR_MALE = 1500.0
SAFETY_FLOOR_FEMALE = 1200.0


def bmr_mifflin(
    sex: Sex, weight_kg: float, height_cm: float, age_years: int
) -> float:
    """Metabolismo basal por la ecuación de Mifflin-St Jeor (1990), en kcal/día.

    Común: 10·peso(kg) + 6,25·talla(cm) − 5·edad(años).
    Constante final: +5 en hombres, −161 en mujeres.

    Ejemplo: varón de 30 años, 80 kg, 180 cm → 1780 kcal/día.
    """
    base = 10.0 * weight_kg + 6.25 * height_cm - 5.0 * age_years
    constant = 5.0 if sex is Sex.MALE else -161.0
    return round(base + constant, 1)


def bmr_harris_benedict(
    sex: Sex, weight_kg: float, height_cm: float, age_years: int
) -> float:
    """Metabolismo basal por Harris-Benedict revisada (Roza y Shizgal, 1984).

    Hombres: 88,362 + 13,397·peso + 4,799·talla − 5,677·edad.
    Mujeres: 447,593 + 9,247·peso + 3,098·talla − 4,330·edad.
    Peso en kg, talla en cm, edad en años. Devuelve kcal/día.
    """
    if sex is Sex.MALE:
        value = (
            88.362
            + 13.397 * weight_kg
            + 4.799 * height_cm
            - 5.677 * age_years
        )
    else:
        value = (
            447.593
            + 9.247 * weight_kg
            + 3.098 * height_cm
            - 4.330 * age_years
        )
    return round(value, 1)


def tdee(bmr: float, activity_level: ActivityLevel) -> float:
    """Gasto energético total diario: basal × factor de actividad (PAL).

    Factores: sedentario 1,2 · ligero 1,375 · moderado 1,55 · activo 1,725 ·
    muy activo 1,9. Devuelve kcal/día.
    """
    return round(bmr * activity_level.pal, 1)


def energy_target(
    tdee_kcal: float,
    goal: Goal,
    sex: Sex,
    deficit_kcal: float = 500.0,
    bmr_kcal: float | None = None,
) -> EnergyTargets:
    """Objetivo calórico diario según el objetivo de peso.

    Perder: TDEE − déficit. Mantener: TDEE. Ganar: TDEE + déficit (el mismo
    valor se usa como superávit). Se aplica un suelo de seguridad (≈ 1500 kcal
    en hombres, ≈ 1200 kcal en mujeres): si el objetivo cae por debajo, se
    eleva al suelo y se registra un aviso.
    """
    if deficit_kcal < 0:
        raise ValueError("El déficit debe indicarse como valor no negativo.")

    warnings: list[str] = []

    if goal is Goal.LOSE:
        applied_deficit = deficit_kcal
        raw_target = tdee_kcal - deficit_kcal
    elif goal is Goal.GAIN:
        applied_deficit = -deficit_kcal          # superávit = déficit negativo
        raw_target = tdee_kcal + deficit_kcal
    else:  # MAINTAIN
        applied_deficit = 0.0
        raw_target = tdee_kcal

    floor = SAFETY_FLOOR_MALE if sex is Sex.MALE else SAFETY_FLOOR_FEMALE
    floor_applied = False
    target = raw_target
    if target < floor:
        floor_applied = True
        warnings.append(
            f"El objetivo calculado ({raw_target:.0f} kcal) queda por debajo "
            f"del suelo de seguridad ({floor:.0f} kcal). Se eleva al suelo; "
            "una restricción mayor requiere supervisión profesional."
        )
        target = floor

    return EnergyTargets(
        bmr_kcal=bmr_kcal,
        tdee_kcal=round(tdee_kcal, 1),
        goal=goal,
        target_kcal=round(target, 1),
        deficit_kcal=round(applied_deficit, 1),
        safety_floor_kcal=floor,
        floor_applied=floor_applied,
        warnings=warnings,
    )


def macro_targets(
    kcal: float,
    protein_g_per_kg: float,
    weight_kg: float,
    fat_pct: float = 30.0,
) -> MacroTargets:
    """Reparto de macronutrientes para una ingesta calórica dada.

    Proteína fijada por gramos por kg de peso; grasa por porcentaje de la
    energía total; hidratos de carbono por diferencia. Se devuelven gramos,
    kcal y porcentaje de energía de cada macronutriente.

    Si los hidratos por diferencia salen negativos (proteína y grasa ya
    superan el total), se recorta la grasa y se avisa.
    """
    if kcal <= 0:
        raise ValueError("La ingesta calórica debe ser mayor que cero.")
    if not 0.0 <= fat_pct <= 100.0:
        raise ValueError("El porcentaje de grasa debe estar entre 0 y 100.")

    warnings: list[str] = []

    protein_g = protein_g_per_kg * weight_kg
    protein_kcal = protein_g * KCAL_PER_G_PROTEIN

    fat_kcal = kcal * fat_pct / 100.0
    carbs_kcal = kcal - protein_kcal - fat_kcal

    if protein_kcal > kcal:
        warnings.append(
            "La proteína prescrita ya supera la energía total; revisa los "
            "g/kg o las kcal objetivo."
        )

    if carbs_kcal < 0:
        # La grasa se ajusta a la energía que queda tras la proteína.
        warnings.append(
            "Proteína y grasa superan la energía total; se recorta la grasa "
            "para no dejar hidratos negativos."
        )
        fat_kcal = max(0.0, kcal - protein_kcal)
        carbs_kcal = kcal - protein_kcal - fat_kcal

    carbs_kcal = max(0.0, carbs_kcal)

    fat_g = fat_kcal / KCAL_PER_G_FAT
    carbs_g = carbs_kcal / KCAL_PER_G_CARB

    return MacroTargets(
        kcal=round(kcal, 1),
        protein_g=round(protein_g, 1),
        fat_g=round(fat_g, 1),
        carbs_g=round(carbs_g, 1),
        protein_kcal=round(protein_kcal, 1),
        fat_kcal=round(fat_kcal, 1),
        carbs_kcal=round(carbs_kcal, 1),
        protein_pct=round(protein_kcal / kcal * 100.0, 1),
        fat_pct=round(fat_kcal / kcal * 100.0, 1),
        carbs_pct=round(carbs_kcal / kcal * 100.0, 1),
        warnings=warnings,
    )
