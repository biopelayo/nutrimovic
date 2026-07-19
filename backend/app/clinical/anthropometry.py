"""Antropometría del motor clínico de NutriMovic.

Índice de masa corporal (IMC), su categoría OMS, pesos de referencia,
índice cintura-cadera y variación de peso entre visitas.

Todas las fórmulas son estimaciones poblacionales estándar. **Apoyan la
decisión clínica; no la sustituyen.** El criterio del profesional sanitario,
la composición corporal real y la historia del paciente prevalecen sobre
cualquier número que devuelva este módulo.
"""
from __future__ import annotations

from app.clinical.models import (
    AnthroRecord,
    BMICategory,
    BodyMetrics,
    IdealWeight,
    RiskLevel,
    Sex,
    WaistHipRatio,
)

# Umbrales de IMC de la OMS (kg/m²). El límite superior del normopeso se toma
# en 24,9 por convención clínica; el corte real es < 25.
_BMI_UNDERWEIGHT = 18.5
_BMI_NORMAL_HIGH = 25.0
_BMI_OVERWEIGHT_HIGH = 30.0
_BMI_OBESITY_I_HIGH = 35.0
_BMI_OBESITY_II_HIGH = 40.0

# Límites del rango de peso saludable por IMC.
_BMI_HEALTHY_LOW = 18.5
_BMI_HEALTHY_HIGH = 24.9


def bmi(weight_kg: float, height_cm: float) -> float:
    """Índice de masa corporal: peso (kg) dividido por la talla (m) al cuadrado.

    Devuelve kg/m². Lanza `ValueError` si la talla no es positiva.
    """
    if height_cm <= 0:
        raise ValueError("La talla debe ser mayor que cero.")
    height_m = height_cm / 100.0
    return weight_kg / (height_m * height_m)


def bmi_category(bmi_value: float) -> BMICategory:
    """Clasifica un IMC en su categoría OMS.

    Cortes (kg/m²): < 18,5 bajo peso · 18,5–24,9 normopeso · 25–29,9 sobrepeso ·
    30–34,9 obesidad I · 35–39,9 obesidad II · ≥ 40 obesidad III.
    """
    if bmi_value < _BMI_UNDERWEIGHT:
        return BMICategory.UNDERWEIGHT
    if bmi_value < _BMI_NORMAL_HIGH:
        return BMICategory.NORMAL
    if bmi_value < _BMI_OVERWEIGHT_HIGH:
        return BMICategory.OVERWEIGHT
    if bmi_value < _BMI_OBESITY_I_HIGH:
        return BMICategory.OBESITY_I
    if bmi_value < _BMI_OBESITY_II_HIGH:
        return BMICategory.OBESITY_II
    return BMICategory.OBESITY_III


def _weight_for_bmi(target_bmi: float, height_cm: float) -> float:
    """Peso (kg) que corresponde a un IMC objetivo para una talla dada."""
    height_m = height_cm / 100.0
    return target_bmi * height_m * height_m


def ideal_weight(height_cm: float, sex: Sex) -> IdealWeight:
    """Peso teórico de referencia por varios métodos, en kg.

    Combina tres criterios y ofrece además un rango, porque ningún método es
    "el" peso ideal:

    - Rango saludable por IMC (18,5–24,9 kg/m²).
    - Fórmula de Lorentz (depende de la talla y el sexo).
    - Fórmula de Devine (talla en pulgadas sobre 5 pies, por sexo).

    El rango final abarca desde el mínimo hasta el máximo de todos los valores.
    """
    if height_cm <= 0:
        raise ValueError("La talla debe ser mayor que cero.")

    bmi_low = _weight_for_bmi(_BMI_HEALTHY_LOW, height_cm)
    bmi_high = _weight_for_bmi(_BMI_HEALTHY_HIGH, height_cm)

    # Lorentz: divisor 4 en hombres, 2 en mujeres.
    if sex is Sex.MALE:
        lorentz = height_cm - 100.0 - (height_cm - 150.0) / 4.0
    else:
        lorentz = height_cm - 100.0 - (height_cm - 150.0) / 2.0

    # Devine: base por sexo + 2,3 kg por cada pulgada por encima de 5 pies (60").
    inches_over_5ft = max(0.0, height_cm / 2.54 - 60.0)
    base = 50.0 if sex is Sex.MALE else 45.5
    devine = base + 2.3 * inches_over_5ft

    all_values = [bmi_low, bmi_high, lorentz, devine]
    return IdealWeight(
        lorentz_kg=round(lorentz, 1),
        devine_kg=round(devine, 1),
        bmi_low_kg=round(bmi_low, 1),
        bmi_high_kg=round(bmi_high, 1),
        range_low_kg=round(min(all_values), 1),
        range_high_kg=round(max(all_values), 1),
    )


def ideal_weight_range(height_cm: float) -> tuple[float, float]:
    """Rango de peso saludable por IMC (18,5–24,9 kg/m²), en kg.

    Atajo independiente del sexo cuando solo interesa el rango poblacional.
    Devuelve la tupla `(mínimo, máximo)`.
    """
    if height_cm <= 0:
        raise ValueError("La talla debe ser mayor que cero.")
    low = _weight_for_bmi(_BMI_HEALTHY_LOW, height_cm)
    high = _weight_for_bmi(_BMI_HEALTHY_HIGH, height_cm)
    return round(low, 1), round(high, 1)


def whr_risk(ratio: float, sex: Sex) -> RiskLevel:
    """Interpreta el índice cintura-cadera (ICC) según el sexo (cortes OMS).

    Hombres: < 0,90 bajo · 0,90–0,99 aumentado · ≥ 1,00 alto.
    Mujeres: < 0,80 bajo · 0,80–0,84 aumentado · ≥ 0,85 alto.
    """
    if sex is Sex.MALE:
        increased_cut, high_cut = 0.90, 1.00
    else:
        increased_cut, high_cut = 0.80, 0.85

    if ratio < increased_cut:
        return RiskLevel.LOW
    if ratio < high_cut:
        return RiskLevel.INCREASED
    return RiskLevel.HIGH


def waist_hip_ratio(waist_cm: float, hip_cm: float, sex: Sex) -> WaistHipRatio:
    """Índice cintura-cadera y su nivel de riesgo cardiometabólico.

    El ICC es el cociente entre el perímetro de cintura y el de cadera. Lanza
    `ValueError` si el perímetro de cadera no es positivo.
    """
    if hip_cm <= 0:
        raise ValueError("El perímetro de cadera debe ser mayor que cero.")
    ratio = waist_cm / hip_cm
    return WaistHipRatio(ratio=round(ratio, 3), risk=whr_risk(ratio, sex))


def weight_change_pct(prev_kg: float, cur_kg: float) -> float:
    """Variación porcentual de peso entre dos medidas: (actual − previo) / previo.

    Positivo = ganancia; negativo = pérdida. Lanza `ValueError` si el peso
    previo no es positivo. Se redondea a una cifra decimal.
    """
    if prev_kg <= 0:
        raise ValueError("El peso previo debe ser mayor que cero.")
    return round((cur_kg - prev_kg) / prev_kg * 100.0, 1)


def body_metrics(record: AnthroRecord, sex: Sex) -> BodyMetrics:
    """Consolida los indicadores antropométricos de una medición.

    Calcula IMC y su categoría siempre; añade peso de referencia y, si hay
    perímetros de cintura y cadera, el índice cintura-cadera. Los campos que
    dependen de datos ausentes quedan en None.
    """
    bmi_value = round(bmi(record.weight_kg, record.height_cm), 1)
    category = bmi_category(bmi_value)

    waist_hip = None
    if record.waist_cm is not None and record.hip_cm is not None:
        waist_hip = waist_hip_ratio(record.waist_cm, record.hip_cm, sex)

    return BodyMetrics(
        weight_kg=record.weight_kg,
        height_cm=record.height_cm,
        bmi=bmi_value,
        bmi_category=category,
        ideal_weight=ideal_weight(record.height_cm, sex),
        waist_hip=waist_hip,
        body_fat_pct=record.body_fat_pct,
    )
