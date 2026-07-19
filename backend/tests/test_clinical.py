"""Tests del motor clínico de NutriMovic.

Cubren antropometría (IMC y categoría, peso de referencia, índice
cintura-cadera, variación de peso) y energía (Mifflin-St Jeor,
Harris-Benedict, TDEE, objetivo con déficit y suelo, reparto de macros).

Los valores de referencia (p. ej. Mifflin de un varón de 30 a / 80 kg / 180 cm
≈ 1780 kcal) son verificables a mano con las fórmulas estándar.
"""
from __future__ import annotations

from datetime import date

import pytest

from app.clinical import (
    ActivityLevel,
    AnthroRecord,
    BMICategory,
    Goal,
    RiskLevel,
    Sex,
    bmi,
    bmi_category,
    bmr_harris_benedict,
    bmr_mifflin,
    body_metrics,
    energy_target,
    ideal_weight,
    macro_targets,
    tdee,
    waist_hip_ratio,
    weight_change_pct,
)
from app.clinical.anthropometry import ideal_weight_range


# --------------------------------------------------------------------------- #
# IMC y categoría
# --------------------------------------------------------------------------- #
def test_bmi_valor_conocido() -> None:
    # 80 kg, 180 cm → 80 / 1,8² = 24,69
    assert bmi(80.0, 180.0) == pytest.approx(24.69, abs=0.01)


def test_bmi_talla_invalida() -> None:
    with pytest.raises(ValueError):
        bmi(70.0, 0.0)


@pytest.mark.parametrize(
    "value, expected",
    [
        (17.0, BMICategory.UNDERWEIGHT),
        (18.5, BMICategory.NORMAL),
        (22.0, BMICategory.NORMAL),
        (24.9, BMICategory.NORMAL),
        (25.0, BMICategory.OVERWEIGHT),
        (27.5, BMICategory.OVERWEIGHT),
        (30.0, BMICategory.OBESITY_I),
        (37.0, BMICategory.OBESITY_II),
        (41.0, BMICategory.OBESITY_III),
    ],
)
def test_bmi_category_cortes_oms(value: float, expected: BMICategory) -> None:
    assert bmi_category(value) is expected


def test_bmi_category_tiene_etiqueta_es() -> None:
    assert bmi_category(22.0).label_es == "Normopeso"


# --------------------------------------------------------------------------- #
# Peso de referencia
# --------------------------------------------------------------------------- #
def test_ideal_weight_range_por_imc() -> None:
    low, high = ideal_weight_range(180.0)
    # 18,5·1,8² = 59,94 ; 24,9·1,8² = 80,68
    assert low == pytest.approx(59.9, abs=0.1)
    assert high == pytest.approx(80.7, abs=0.1)
    assert low < high


def test_ideal_weight_incluye_metodos_y_rango() -> None:
    iw = ideal_weight(180.0, Sex.MALE)
    # Lorentz varón: 180 − 100 − (180−150)/4 = 72,5
    assert iw.lorentz_kg == pytest.approx(72.5, abs=0.1)
    # Devine varón: 50 + 2,3·(180/2,54 − 60) = 75,0
    assert iw.devine_kg == pytest.approx(75.0, abs=0.3)
    assert iw.bmi_low_kg == pytest.approx(59.9, abs=0.1)
    assert iw.bmi_high_kg == pytest.approx(80.7, abs=0.1)
    # El rango abarca desde el menor al mayor de los métodos.
    assert iw.range_low_kg <= min(iw.lorentz_kg, iw.devine_kg, iw.bmi_low_kg)
    assert iw.range_high_kg >= max(iw.lorentz_kg, iw.devine_kg, iw.bmi_high_kg)


def test_ideal_weight_difiere_por_sexo() -> None:
    hombre = ideal_weight(170.0, Sex.MALE)
    mujer = ideal_weight(170.0, Sex.FEMALE)
    # La mujer tiene menor base en Devine y menor Lorentz.
    assert mujer.devine_kg < hombre.devine_kg
    assert mujer.lorentz_kg < hombre.lorentz_kg


# --------------------------------------------------------------------------- #
# Índice cintura-cadera
# --------------------------------------------------------------------------- #
def test_waist_hip_ratio_hombre_alto() -> None:
    whr = waist_hip_ratio(100.0, 95.0, Sex.MALE)  # 1,05
    assert whr.ratio == pytest.approx(1.053, abs=0.001)
    assert whr.risk is RiskLevel.HIGH


def test_waist_hip_ratio_mujer_bajo() -> None:
    whr = waist_hip_ratio(70.0, 100.0, Sex.FEMALE)  # 0,70
    assert whr.risk is RiskLevel.LOW


def test_waist_hip_ratio_corte_por_sexo() -> None:
    # ICC de 0,86: bajo/normal en hombre, alto en mujer.
    hombre = waist_hip_ratio(86.0, 100.0, Sex.MALE)
    mujer = waist_hip_ratio(86.0, 100.0, Sex.FEMALE)
    assert hombre.risk is RiskLevel.LOW
    assert mujer.risk is RiskLevel.HIGH


def test_waist_hip_ratio_cadera_invalida() -> None:
    with pytest.raises(ValueError):
        waist_hip_ratio(90.0, 0.0, Sex.MALE)


# --------------------------------------------------------------------------- #
# Variación de peso
# --------------------------------------------------------------------------- #
def test_weight_change_pct_perdida() -> None:
    # De 100 a 95 kg → −5 %
    assert weight_change_pct(100.0, 95.0) == pytest.approx(-5.0)


def test_weight_change_pct_ganancia() -> None:
    assert weight_change_pct(80.0, 84.0) == pytest.approx(5.0)


def test_weight_change_pct_previo_invalido() -> None:
    with pytest.raises(ValueError):
        weight_change_pct(0.0, 70.0)


# --------------------------------------------------------------------------- #
# Metabolismo basal
# --------------------------------------------------------------------------- #
def test_bmr_mifflin_varon_referencia() -> None:
    # 10·80 + 6,25·180 − 5·30 + 5 = 1780
    assert bmr_mifflin(Sex.MALE, 80.0, 180.0, 30) == pytest.approx(1780.0, abs=0.5)


def test_bmr_mifflin_mujer_referencia() -> None:
    # 10·60 + 6,25·165 − 5·30 − 161 = 1320,25
    assert bmr_mifflin(Sex.FEMALE, 60.0, 165.0, 30) == pytest.approx(1320.25, abs=0.5)


def test_bmr_harris_benedict_varon() -> None:
    # 88,362 + 13,397·80 + 4,799·180 − 5,677·30 = 1853,6
    assert bmr_harris_benedict(Sex.MALE, 80.0, 180.0, 30) == pytest.approx(1853.6, abs=0.5)


def test_bmr_mifflin_menor_que_harris_no_obligatorio() -> None:
    # Simplemente comprueba que ambos devuelven valores plausibles y positivos.
    m = bmr_mifflin(Sex.MALE, 80.0, 180.0, 30)
    h = bmr_harris_benedict(Sex.MALE, 80.0, 180.0, 30)
    assert m > 1000 and h > 1000


# --------------------------------------------------------------------------- #
# TDEE
# --------------------------------------------------------------------------- #
def test_tdee_moderado() -> None:
    # 1780 · 1,55 = 2759
    assert tdee(1780.0, ActivityLevel.MODERATE) == pytest.approx(2759.0, abs=0.5)


def test_tdee_factores_crecientes() -> None:
    bmr = 1600.0
    valores = [tdee(bmr, a) for a in ActivityLevel]
    assert valores == sorted(valores)  # a más actividad, más gasto


# --------------------------------------------------------------------------- #
# Objetivo energético
# --------------------------------------------------------------------------- #
def test_energy_target_deficit_perdida() -> None:
    et = energy_target(2500.0, Goal.LOSE, Sex.MALE, deficit_kcal=500.0, bmr_kcal=1780.0)
    assert et.target_kcal == pytest.approx(2000.0)
    assert et.deficit_kcal == pytest.approx(500.0)
    assert et.floor_applied is False
    assert et.bmr_kcal == pytest.approx(1780.0)


def test_energy_target_mantenimiento() -> None:
    et = energy_target(2200.0, Goal.MAINTAIN, Sex.FEMALE)
    assert et.target_kcal == pytest.approx(2200.0)
    assert et.deficit_kcal == pytest.approx(0.0)


def test_energy_target_superavit() -> None:
    et = energy_target(2200.0, Goal.GAIN, Sex.MALE, deficit_kcal=400.0)
    assert et.target_kcal == pytest.approx(2600.0)
    assert et.deficit_kcal == pytest.approx(-400.0)  # superávit


def test_energy_target_suelo_seguridad_mujer() -> None:
    # TDEE bajo + déficit grande cae por debajo de 1200 → se eleva y avisa.
    et = energy_target(1500.0, Goal.LOSE, Sex.FEMALE, deficit_kcal=500.0)
    assert et.target_kcal == pytest.approx(1200.0)
    assert et.floor_applied is True
    assert et.safety_floor_kcal == pytest.approx(1200.0)
    assert len(et.warnings) == 1


def test_energy_target_suelo_seguridad_hombre() -> None:
    et = energy_target(1800.0, Goal.LOSE, Sex.MALE, deficit_kcal=500.0)
    assert et.target_kcal == pytest.approx(1500.0)
    assert et.floor_applied is True


def test_energy_target_deficit_negativo_falla() -> None:
    with pytest.raises(ValueError):
        energy_target(2000.0, Goal.LOSE, Sex.MALE, deficit_kcal=-100.0)


# --------------------------------------------------------------------------- #
# Reparto de macronutrientes
# --------------------------------------------------------------------------- #
def test_macro_targets_cuadra_en_kcal() -> None:
    m = macro_targets(2000.0, protein_g_per_kg=1.6, weight_kg=70.0, fat_pct=30.0)
    # Proteína: 1,6·70 = 112 g → 448 kcal
    assert m.protein_g == pytest.approx(112.0)
    assert m.protein_kcal == pytest.approx(448.0)
    # Grasa: 30 % de 2000 = 600 kcal → 66,7 g
    assert m.fat_kcal == pytest.approx(600.0)
    assert m.fat_g == pytest.approx(66.7, abs=0.1)
    # Hidratos por diferencia: 2000 − 448 − 600 = 952 kcal → 238 g
    assert m.carbs_kcal == pytest.approx(952.0)
    assert m.carbs_g == pytest.approx(238.0, abs=0.1)
    # La suma de kcal de los macros reconstruye el total.
    assert m.protein_kcal + m.fat_kcal + m.carbs_kcal == pytest.approx(2000.0, abs=0.5)


def test_macro_targets_porcentajes_suman_100() -> None:
    m = macro_targets(2200.0, protein_g_per_kg=1.8, weight_kg=75.0, fat_pct=35.0)
    total_pct = m.protein_pct + m.fat_pct + m.carbs_pct
    assert total_pct == pytest.approx(100.0, abs=0.5)


def test_macro_targets_proteina_excesiva_avisa() -> None:
    # Proteína desmesurada supera la energía total → hidratos recortados a 0 y aviso.
    m = macro_targets(1000.0, protein_g_per_kg=5.0, weight_kg=80.0, fat_pct=30.0)
    assert m.carbs_g == pytest.approx(0.0)
    assert m.warnings  # hay al menos un aviso


def test_macro_targets_kcal_invalida() -> None:
    with pytest.raises(ValueError):
        macro_targets(0.0, protein_g_per_kg=1.5, weight_kg=70.0)


# --------------------------------------------------------------------------- #
# Consolidado antropométrico
# --------------------------------------------------------------------------- #
def test_body_metrics_completo() -> None:
    rec = AnthroRecord(
        date=date(2026, 7, 18),
        weight_kg=80.0,
        height_cm=180.0,
        waist_cm=90.0,
        hip_cm=100.0,
        body_fat_pct=18.0,
    )
    bm = body_metrics(rec, Sex.MALE)
    assert bm.bmi == pytest.approx(24.7, abs=0.1)
    assert bm.bmi_category is BMICategory.NORMAL
    assert bm.ideal_weight is not None
    assert bm.waist_hip is not None
    assert bm.waist_hip.ratio == pytest.approx(0.9, abs=0.001)
    assert bm.body_fat_pct == pytest.approx(18.0)


def test_body_metrics_sin_perimetros() -> None:
    rec = AnthroRecord(date=date(2026, 7, 18), weight_kg=95.0, height_cm=170.0)
    bm = body_metrics(rec, Sex.FEMALE)
    assert bm.bmi_category is BMICategory.OBESITY_I  # 95/1,7² = 32,9
    assert bm.waist_hip is None
