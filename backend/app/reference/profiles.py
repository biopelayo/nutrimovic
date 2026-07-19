"""Perfiles y valores de referencia dietéticos (DRV) de EFSA.

Fuente: EFSA, «Summary of Dietary Reference Values – version 4 (September 2017)»
(Panel NDA). Recopila los PRI (Population Reference Intake) y AI (Adequate
Intake) publicados por EFSA para la población de la UE.

Qué es qué:
- PRI: ingesta que cubre las necesidades del 97,5 % de la población.
- AI : ingesta adecuada estimada cuando no puede fijarse un PRI.

Diseño:
- Solo se codifican valores que EFSA publica de forma explícita. Donde EFSA no
  fija un valor único (p. ej. grasa total e hidratos, que se dan como rango de
  % de energía), el nutriente NO recibe un valor absoluto por perfil: queda como
  `None` (no disponible) y el rango se documenta aparte en `EFSA_MACRO_RANGES`.
- Energía, niacina y tiamina dependen de la energía/actividad: se calculan a
  partir de las tablas EFSA (energía por edad, sexo y PAL; niacina 1,6 mg NE/MJ;
  tiamina 0,1 mg/MJ).
- La proteína se calcula con el PRI EFSA de 0,83 g/kg de peso corporal y día,
  multiplicado por el peso de referencia del perfil (parámetro explícito, no una
  cifra inventada). Sin peso -> `None`.

Cobertura del catálogo: EFSA no fija DRV para grasa total, AGS, AGM, AGP,
colesterol, azúcares, almidón, alcohol, agua-como-humedad ni algunos
oligoelementos (cromo: EFSA considera que no procede fijar AI/PRI). Esos quedan
como no disponibles.

AVISO: apoya el diseño de dietas; no sustituye al profesional sanitario.
"""
from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field

KCAL_PER_MJ = 238.83  # 1 MJ = 238,83 kcal (EFSA)


class Sex(str, Enum):
    MALE = "male"
    FEMALE = "female"


class LifeStage(str, Enum):
    NONE = "none"
    PREGNANCY = "pregnancy"
    LACTATION = "lactation"


class ActivityLevel(str, Enum):
    """Nivel de actividad física (PAL) de las tablas de energía de EFSA."""

    SEDENTARY = "sedentary"      # PAL 1,4
    MODERATE = "moderate"        # PAL 1,6
    ACTIVE = "active"            # PAL 1,8
    VERY_ACTIVE = "very_active"  # PAL 2,0


PAL_VALUE: dict[ActivityLevel, float] = {
    ActivityLevel.SEDENTARY: 1.4,
    ActivityLevel.MODERATE: 1.6,
    ActivityLevel.ACTIVE: 1.8,
    ActivityLevel.VERY_ACTIVE: 2.0,
}


class Profile(BaseModel):
    """Perfil de la persona para elegir los valores de referencia EFSA."""

    sex: Sex
    age_years: int = Field(ge=0, le=120)
    life_stage: LifeStage = LifeStage.NONE
    activity_level: ActivityLevel = ActivityLevel.MODERATE
    # Peso de referencia para calcular la proteína (0,83 g/kg/día). Opcional:
    # sin él, la proteína queda como no disponible en lugar de inventarse.
    reference_weight_kg: float | None = Field(default=None, gt=0, le=300)


# ---------------------------------------------------------------------------
# Tabla 1 EFSA: Requerimiento medio de energía (MJ/día) por edad, sexo y PAL.
# Índices por banda de edad adulta. EFSA no calcula energía para >= 80 años.
# ---------------------------------------------------------------------------
_ENERGY_AGE_BANDS: list[tuple[int, int]] = [
    (18, 29), (30, 39), (40, 49), (50, 59), (60, 69), (70, 79)
]
# energía_MJ[PAL][sexo] -> lista alineada con _ENERGY_AGE_BANDS
_ENERGY_MJ: dict[ActivityLevel, dict[Sex, list[float]]] = {
    ActivityLevel.SEDENTARY: {
        Sex.MALE: [9.8, 9.5, 9.3, 9.2, 8.4, 8.3],
        Sex.FEMALE: [7.9, 7.6, 7.5, 7.5, 6.8, 6.8],
    },
    ActivityLevel.MODERATE: {
        Sex.MALE: [11.2, 10.8, 10.7, 10.5, 9.6, 9.5],
        Sex.FEMALE: [9.0, 8.7, 8.6, 8.5, 7.8, 7.7],
    },
    ActivityLevel.ACTIVE: {
        Sex.MALE: [12.6, 12.2, 12.0, 11.9, 10.9, 10.7],
        Sex.FEMALE: [10.1, 9.8, 9.7, 9.6, 8.8, 8.7],
    },
    ActivityLevel.VERY_ACTIVE: {
        Sex.MALE: [14.0, 13.5, 13.4, 13.2, 12.1, 11.9],
        Sex.FEMALE: [11.2, 10.8, 10.7, 10.7, 9.7, 9.6],
    },
}

# Incrementos de energía EFSA (MJ/día) para embarazo (por trimestre) y lactancia.
# Como el perfil no distingue trimestre, para embarazo se documenta pero no se
# suma automáticamente; para lactancia se aplica el valor único de EFSA.
_ENERGY_PREGNANCY_MJ = {"trimester_1": 0.29, "trimester_2": 1.1, "trimester_3": 2.1}
_ENERGY_LACTATION_MJ = 2.1  # 0-6 meses posparto (~ +500 kcal/día)

# Coeficientes EFSA dependientes de la energía.
_NIACIN_MG_NE_PER_MJ = 1.6   # PRI niacina
_THIAMIN_MG_PER_MJ = 0.1     # PRI tiamina
_PROTEIN_PRI_G_PER_KG = 0.83  # PRI proteína adultos (>= 18 años)

# Nivel de fitatos asumido para el zinc (mg/día). EFSA da el PRI de zinc en
# función de la ingesta de fitatos; 300 mg/día representa una dieta mixta típica.
ZINC_PHYTATE_LEVEL_MG = 300

# Menopausia asumida a los 51 años para elegir el PRI de hierro en mujeres.
MENOPAUSE_AGE = 51


def _energy_mj(profile: Profile) -> float | None:
    """Energía de referencia (MJ/día) para el perfil, o None si no aplica."""
    if profile.age_years < 18 or profile.age_years > 79:
        return None  # EFSA no publica energía para <18 aquí ni para >=80
    idx = next(
        (i for i, (lo, hi) in enumerate(_ENERGY_AGE_BANDS) if lo <= profile.age_years <= hi),
        None,
    )
    if idx is None:
        return None
    base = _ENERGY_MJ[profile.activity_level][profile.sex][idx]
    if profile.sex is Sex.FEMALE and profile.life_stage is LifeStage.LACTATION:
        return base + _ENERGY_LACTATION_MJ
    # Embarazo: incremento dependiente del trimestre; se deja la base y se
    # documenta el suplemento en _ENERGY_PREGNANCY_MJ (no se estima aquí).
    return base


def _adult(age: int) -> bool:
    return age >= 18


def _efsa_adult_micros(profile: Profile) -> dict[str, float | None]:
    """PRI/AI EFSA de vitaminas y minerales para adultos (>= 18), por perfil.

    Devuelve solo lo que EFSA fija de forma explícita. Bandas por edad:
    calcio (18-24 vs >=25) y hierro en mujeres (pre/posmenopausia).
    """
    sex = profile.sex
    stage = profile.life_stage
    age = profile.age_years
    v: dict[str, float | None] = {}

    # --- Vitaminas (Tablas 9 y 11) ---
    if sex is Sex.MALE:
        v["vit_e_mg"] = 13.0        # AI alfa-tocoferol
        v["vit_a_ug_rae"] = 750.0   # PRI (EFSA: µg RE)
        v["vit_b6_mg"] = 1.7        # PRI
        v["vit_c_mg"] = 110.0       # PRI
    else:
        v["vit_e_mg"] = 11.0
        if stage is LifeStage.PREGNANCY:
            v["vit_a_ug_rae"] = 700.0
            v["vit_b6_mg"] = 1.8
            v["vit_c_mg"] = 105.0
        elif stage is LifeStage.LACTATION:
            v["vit_a_ug_rae"] = 1300.0
            v["vit_b6_mg"] = 1.7
            v["vit_c_mg"] = 155.0
        else:
            v["vit_a_ug_rae"] = 650.0
            v["vit_b6_mg"] = 1.6
            v["vit_c_mg"] = 95.0

    # Comunes / con variación por estado
    v["vit_k_ug"] = 70.0    # AI
    v["vit_d_ug"] = 15.0    # AI (síntesis cutánea mínima asumida)
    v["vit_b2_mg"] = _riboflavin(sex, stage)   # PRI
    v["vit_b5_mg"] = _pantothenic(stage)       # AI
    v["vit_b7_ug"] = _biotin(stage)            # AI
    v["vit_b12_ug"] = _cobalamin(stage)        # AI
    v["vit_b9_ug_dfe"] = _folate(stage)        # PRI

    # --- Minerales (Tablas 5 y 7) ---
    v["calcium_mg"] = 1000.0 if age <= 24 else 950.0   # PRI
    v["iodine_ug"] = 200.0 if stage in (LifeStage.PREGNANCY, LifeStage.LACTATION) else 150.0  # AI
    v["manganese_mg"] = 3.0     # AI
    v["molybdenum_ug"] = 65.0   # AI
    v["phosphorus_mg"] = 550.0  # AI
    v["selenium_ug"] = 85.0 if stage is LifeStage.LACTATION else 70.0  # AI
    v["potassium_mg"] = 4000.0 if stage is LifeStage.LACTATION else 3500.0  # AI

    if sex is Sex.MALE:
        v["fluoride_mg"] = 3.4   # AI
        v["copper_mg"] = 1.6     # AI
        v["magnesium_mg"] = 350.0  # AI
        v["iron_mg"] = 11.0      # PRI
        v["zinc_mg"] = 9.4       # PRI a fitatos 300 mg/d
    else:
        v["fluoride_mg"] = 2.9
        v["magnesium_mg"] = 300.0
        base_zinc = 7.5  # PRI mujer a fitatos 300 mg/d
        if stage is LifeStage.PREGNANCY:
            v["copper_mg"] = 1.5
            v["iron_mg"] = 16.0
            v["zinc_mg"] = base_zinc + 1.6
        elif stage is LifeStage.LACTATION:
            v["copper_mg"] = 1.5
            v["iron_mg"] = 16.0
            v["zinc_mg"] = base_zinc + 2.9
        else:
            v["copper_mg"] = 1.3
            # Hierro: premenopausia 16 mg, posmenopausia 11 mg (PRI)
            v["iron_mg"] = 16.0 if age < MENOPAUSE_AGE else 11.0
            v["zinc_mg"] = base_zinc

    # --- Fibra y agua (Tabla 3, AI) ---
    v["fiber_g"] = 25.0  # AI adultos
    # Agua total EFSA (bebidas + humedad de alimentos), L/día -> g.
    if stage is LifeStage.PREGNANCY:
        v["water_g"] = 2300.0
    elif stage is LifeStage.LACTATION:
        v["water_g"] = 2700.0
    else:
        v["water_g"] = 2500.0 if sex is Sex.MALE else 2000.0

    return v


def _riboflavin(sex: Sex, stage: LifeStage) -> float:
    if sex is Sex.FEMALE and stage is LifeStage.PREGNANCY:
        return 1.9
    if sex is Sex.FEMALE and stage is LifeStage.LACTATION:
        return 2.0
    return 1.6


def _pantothenic(stage: LifeStage) -> float:
    return 7.0 if stage is LifeStage.LACTATION else 5.0


def _biotin(stage: LifeStage) -> float:
    return 45.0 if stage is LifeStage.LACTATION else 40.0


def _cobalamin(stage: LifeStage) -> float:
    if stage is LifeStage.PREGNANCY:
        return 4.5
    if stage is LifeStage.LACTATION:
        return 5.0
    return 4.0


def _folate(stage: LifeStage) -> float:
    if stage is LifeStage.PREGNANCY:
        return 600.0
    if stage is LifeStage.LACTATION:
        return 500.0
    return 330.0


def efsa_reference_values(profile: Profile) -> dict[str, float | None]:
    """Valores de referencia EFSA para el `profile`, por `nutrient_id`.

    Clave = nutrient_id canónico; valor = cantidad de referencia en la unidad
    del catálogo, o `None` si EFSA no fija un valor único para ese nutriente y
    perfil (no se inventa). Solo adultos (>= 18 años) tienen set completo; en
    menores se devuelven los nutrientes como no disponibles por prudencia.
    """
    values: dict[str, float | None] = {}

    if not _adult(profile.age_years):
        # Fuera del alcance validado de este módulo: no se arriesgan cifras.
        return values

    values.update(_efsa_adult_micros(profile))

    # Energía (kcal y kJ) desde la tabla EFSA.
    mj = _energy_mj(profile)
    if mj is not None:
        values["energy_kcal"] = round(mj * KCAL_PER_MJ, 0)
        values["energy_kj"] = round(mj * 1000.0, 0)
        # Niacina y tiamina, dependientes de la energía.
        values["vit_b3_mg_ne"] = round(_NIACIN_MG_NE_PER_MJ * mj, 2)
        values["vit_b1_mg"] = round(_THIAMIN_MG_PER_MJ * mj, 2)
    else:
        values["energy_kcal"] = None
        values["energy_kj"] = None
        values["vit_b3_mg_ne"] = None
        values["vit_b1_mg"] = None

    # Proteína: 0,83 g/kg/día × peso de referencia (si se conoce).
    if profile.reference_weight_kg is not None:
        base = _PROTEIN_PRI_G_PER_KG * profile.reference_weight_kg
        # Suplementos EFSA (PRI) en embarazo/lactancia, g/día.
        if profile.life_stage is LifeStage.PREGNANCY:
            # Trimestre no especificado: se usa el suplemento medio del 3.er
            # trimestre no es correcto por defecto; se deja la base y el
            # suplemento se documenta. Para no infraestimar de forma silenciosa,
            # se marca proteína base (el motor puede añadir por trimestre).
            values["protein_g"] = round(base, 1)
        elif profile.life_stage is LifeStage.LACTATION:
            values["protein_g"] = round(base + 19.0, 1)  # +19 g/d PRI
        else:
            values["protein_g"] = round(base, 1)
    else:
        values["protein_g"] = None

    return values


# ---------------------------------------------------------------------------
# Rangos de referencia EFSA para macronutrientes expresados como % de energía
# (Reference Intake ranges). No son valores únicos de cobertura; se documentan
# para que la capa dietética los use como banda objetivo.
# ---------------------------------------------------------------------------
EFSA_MACRO_RANGES: dict[str, tuple[float, float] | str] = {
    "fat_g": (20.0, 35.0),          # % energía total
    "carbs_g": (45.0, 60.0),        # % energía total
    "fat_saturated_g": "as low as possible",
    "sugars_added_g": "as low as possible",
}

# Perfiles de ejemplo listos para usar (con peso de referencia documentado).
PRESET_PROFILES: dict[str, Profile] = {
    "hombre_adulto_moderado": Profile(
        sex=Sex.MALE, age_years=35, activity_level=ActivityLevel.MODERATE,
        reference_weight_kg=70.0,
    ),
    "mujer_adulta_moderada": Profile(
        sex=Sex.FEMALE, age_years=35, activity_level=ActivityLevel.MODERATE,
        reference_weight_kg=60.0,
    ),
    "mujer_embarazo": Profile(
        sex=Sex.FEMALE, age_years=30, life_stage=LifeStage.PREGNANCY,
        activity_level=ActivityLevel.MODERATE, reference_weight_kg=65.0,
    ),
    "mujer_lactancia": Profile(
        sex=Sex.FEMALE, age_years=30, life_stage=LifeStage.LACTATION,
        activity_level=ActivityLevel.MODERATE, reference_weight_kg=65.0,
    ),
    "hombre_mayor_sedentario": Profile(
        sex=Sex.MALE, age_years=68, activity_level=ActivityLevel.SEDENTARY,
        reference_weight_kg=72.0,
    ),
}

__all__ = [
    "Sex",
    "LifeStage",
    "ActivityLevel",
    "Profile",
    "efsa_reference_values",
    "EFSA_MACRO_RANGES",
    "PRESET_PROFILES",
    "KCAL_PER_MJ",
]
