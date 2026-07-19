"""Modelos del motor clínico de NutriMovic.

Tipos Pydantic para perfil de paciente, antropometría y objetivos energéticos.
Siguen el estilo de `app.core.models`: enums `str`, `BaseModel`, español correcto.

AVISO: estos modelos representan estimaciones de apoyo a la decisión clínica,
nunca un diagnóstico ni una prescripción. El profesional sanitario decide.
"""
from __future__ import annotations

from datetime import date
from enum import Enum

from pydantic import BaseModel, Field


class Sex(str, Enum):
    """Sexo biológico. Determina constantes de las fórmulas metabólicas."""

    MALE = "male"
    FEMALE = "female"


class ActivityLevel(str, Enum):
    """Nivel de actividad física con su factor PAL (Physical Activity Level).

    El PAL multiplica al metabolismo basal para estimar el gasto total (TDEE).
    Valores estándar usados en consulta.
    """

    SEDENTARY = "sedentary"
    LIGHT = "light"
    MODERATE = "moderate"
    ACTIVE = "active"
    VERY_ACTIVE = "very_active"

    @property
    def pal(self) -> float:
        """Factor multiplicador del metabolismo basal."""
        return _PAL_FACTORS[self]


_PAL_FACTORS: dict[ActivityLevel, float] = {
    ActivityLevel.SEDENTARY: 1.2,
    ActivityLevel.LIGHT: 1.375,
    ActivityLevel.MODERATE: 1.55,
    ActivityLevel.ACTIVE: 1.725,
    ActivityLevel.VERY_ACTIVE: 1.9,
}


class Goal(str, Enum):
    """Objetivo de peso del paciente."""

    LOSE = "lose"
    MAINTAIN = "maintain"
    GAIN = "gain"


class BMICategory(str, Enum):
    """Categorías de IMC según la OMS."""

    UNDERWEIGHT = "underweight"          # bajo peso, < 18,5
    NORMAL = "normal"                    # normopeso, 18,5–24,9
    OVERWEIGHT = "overweight"            # sobrepeso, 25–29,9
    OBESITY_I = "obesity_i"              # obesidad grado I, 30–34,9
    OBESITY_II = "obesity_ii"            # obesidad grado II, 35–39,9
    OBESITY_III = "obesity_iii"          # obesidad grado III, ≥ 40

    @property
    def label_es(self) -> str:
        return _BMI_LABELS[self]


_BMI_LABELS: dict[BMICategory, str] = {
    BMICategory.UNDERWEIGHT: "Bajo peso",
    BMICategory.NORMAL: "Normopeso",
    BMICategory.OVERWEIGHT: "Sobrepeso",
    BMICategory.OBESITY_I: "Obesidad grado I",
    BMICategory.OBESITY_II: "Obesidad grado II",
    BMICategory.OBESITY_III: "Obesidad grado III",
}


class RiskLevel(str, Enum):
    """Nivel de riesgo cardiometabólico asociado a un indicador antropométrico."""

    LOW = "low"
    INCREASED = "increased"
    HIGH = "high"

    @property
    def label_es(self) -> str:
        return {
            RiskLevel.LOW: "Riesgo bajo",
            RiskLevel.INCREASED: "Riesgo aumentado",
            RiskLevel.HIGH: "Riesgo alto",
        }[self]


# --------------------------------------------------------------------------- #
# Entradas: paciente y registros antropométricos
# --------------------------------------------------------------------------- #
class Patient(BaseModel):
    """Perfil del paciente en consulta.

    La edad puede darse directamente en `age_years` o derivarse de `birth_date`.
    `age()` resuelve la que corresponda, priorizando la fecha de nacimiento.
    """

    id: str
    name: str
    sex: Sex
    birth_date: date | None = None
    age_years: int | None = None
    height_cm: float | None = None
    notes: str | None = None

    def age(self, on: date | None = None) -> int | None:
        """Edad en años cumplidos.

        Usa `birth_date` si está disponible (calculada a la fecha `on`, hoy por
        defecto); si no, cae en `age_years`. Devuelve None si no hay ningún dato.
        """
        if self.birth_date is not None:
            ref = on or date.today()
            years = ref.year - self.birth_date.year
            # Resta un año si aún no ha llegado el cumpleaños de este año.
            if (ref.month, ref.day) < (self.birth_date.month, self.birth_date.day):
                years -= 1
            return years
        return self.age_years


class AnthroRecord(BaseModel):
    """Medición antropométrica puntual, con fecha.

    Los perímetros y el porcentaje graso son opcionales: no todos los pacientes
    los aportan en cada visita.
    """

    date: date
    weight_kg: float
    height_cm: float
    waist_cm: float | None = None
    hip_cm: float | None = None
    body_fat_pct: float | None = None


# --------------------------------------------------------------------------- #
# Resultados: antropometría
# --------------------------------------------------------------------------- #
class IdealWeight(BaseModel):
    """Peso teórico de referencia por varios métodos, en kg.

    Ningún método es "el" peso ideal: se ofrecen varios y un rango saludable por
    IMC para que el profesional interprete en contexto.
    """

    lorentz_kg: float
    devine_kg: float
    bmi_low_kg: float                    # límite inferior del rango sano (IMC 18,5)
    bmi_high_kg: float                   # límite superior del rango sano (IMC 24,9)
    range_low_kg: float                  # mínimo entre todos los métodos
    range_high_kg: float                 # máximo entre todos los métodos


class WaistHipRatio(BaseModel):
    """Índice cintura-cadera (ICC) y su interpretación de riesgo por sexo."""

    ratio: float
    risk: RiskLevel


class BodyMetrics(BaseModel):
    """Resumen antropométrico consolidado de una medición.

    Agrega los indicadores derivados de un `AnthroRecord`. Los campos que
    dependen de datos ausentes (perímetros) quedan en None.
    """

    weight_kg: float
    height_cm: float
    bmi: float
    bmi_category: BMICategory
    ideal_weight: IdealWeight | None = None
    waist_hip: WaistHipRatio | None = None
    body_fat_pct: float | None = None


# --------------------------------------------------------------------------- #
# Resultados: energía y macronutrientes
# --------------------------------------------------------------------------- #
class EnergyTargets(BaseModel):
    """Objetivo energético diario del paciente.

    Incluye el basal, el gasto total, el objetivo aplicado y las banderas de
    seguridad (si se activó el suelo mínimo de kcal).
    """

    bmr_kcal: float | None = None    # opcional: puede no conocerse al fijar el objetivo
    tdee_kcal: float
    goal: Goal
    target_kcal: float
    deficit_kcal: float = 0.0            # negativo = superávit; 0 = mantenimiento
    safety_floor_kcal: float | None = None
    floor_applied: bool = False
    warnings: list[str] = Field(default_factory=list)


class MacroTargets(BaseModel):
    """Reparto de macronutrientes para una ingesta calórica dada.

    Proteína fijada por g/kg de peso, grasa por porcentaje de la energía, e
    hidratos de carbono por diferencia. Se reportan gramos, kcal y % de cada uno.
    """

    kcal: float
    protein_g: float
    fat_g: float
    carbs_g: float
    protein_kcal: float
    fat_kcal: float
    carbs_kcal: float
    protein_pct: float
    fat_pct: float
    carbs_pct: float
    warnings: list[str] = Field(default_factory=list)
