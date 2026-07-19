"""Tests del módulo de referencias nutricionales (VRN + EFSA + cobertura)."""
from __future__ import annotations

import math

import pytest

from app.core.models import MeasurementStatus, ResultValue
from app.reference.coverage import coverage, vrn_reference
from app.reference.profiles import (
    ActivityLevel,
    LifeStage,
    Profile,
    Sex,
    efsa_reference_values,
)
from app.reference.vrn_ue import REFERENCE_INTAKES_UE, VRN_UE


# --------------------------------------------------------------------------
# VRN del Reglamento UE 1169/2011
# --------------------------------------------------------------------------
def test_vrn_valores_oficiales_conocidos():
    assert VRN_UE["vit_c_mg"] == 80.0
    assert VRN_UE["calcium_mg"] == 800.0
    assert VRN_UE["iron_mg"] == 14.0
    assert VRN_UE["vit_d_ug"] == 5.0
    assert VRN_UE["iodine_ug"] == 150.0


def test_sodio_no_tiene_vrn_en_parte_a():
    # El sodio NO tiene VRN en el Anexo XIII Parte A: no debe estar en VRN_UE.
    assert "sodium_mg" not in VRN_UE
    # Sí aparece en las ingestas de referencia (Parte B) como derivado de la sal.
    assert REFERENCE_INTAKES_UE["sodium_mg"] == 2400.0


# --------------------------------------------------------------------------
# Cobertura frente a VRN
# --------------------------------------------------------------------------
def test_cobertura_vitc_80mg_es_100pct_del_vrn():
    cov = coverage({"vit_c_mg": 80.0}, "vrn")
    assert cov["vit_c_mg"].coverage_pct == 100.0
    assert cov["vit_c_mg"].reference_amount == 80.0
    assert cov["vit_c_mg"].unit == "mg"
    assert cov["vit_c_mg"].status is MeasurementStatus.MEASURED


def test_cobertura_calcio_parcial():
    cov = coverage({"calcium_mg": 400.0}, "vrn")
    assert cov["calcium_mg"].coverage_pct == 50.0


def test_nutriente_sin_referencia_devuelve_none():
    # El colesterol no tiene VRN ni ingesta de referencia -> None, no 0.
    cov = coverage({"cholesterol_mg": 120.0}, "vrn")
    assert cov["cholesterol_mg"].reference_amount is None
    assert cov["cholesterol_mg"].coverage_pct is None
    assert cov["cholesterol_mg"].note is not None


def test_aporte_not_determined_propaga_none():
    rv = ResultValue(amount=None, unit="mg", status=MeasurementStatus.NOT_DETERMINED)
    cov = coverage({"vit_c_mg": rv}, "vrn")
    assert cov["vit_c_mg"].coverage_pct is None
    assert cov["vit_c_mg"].status is MeasurementStatus.NOT_DETERMINED


def test_aporte_cero_real_da_cero_pct():
    rv = ResultValue(amount=0.0, unit="mg", status=MeasurementStatus.MEASURED)
    cov = coverage({"vit_c_mg": rv}, "vrn")
    assert cov["vit_c_mg"].coverage_pct == 0.0


def test_acepta_resultvalue_y_numero_equivalentes():
    rv = ResultValue(amount=40.0, unit="mg", status=MeasurementStatus.MEASURED)
    cov_obj = coverage({"vit_c_mg": rv}, "vrn")
    cov_num = coverage({"vit_c_mg": 40.0}, "vrn")
    assert cov_obj["vit_c_mg"].coverage_pct == cov_num["vit_c_mg"].coverage_pct == 50.0


# --------------------------------------------------------------------------
# Selección de perfil (EFSA)
# --------------------------------------------------------------------------
def test_perfil_vitc_difiere_por_sexo():
    hombre = Profile(sex=Sex.MALE, age_years=35)
    mujer = Profile(sex=Sex.FEMALE, age_years=35)
    assert efsa_reference_values(hombre)["vit_c_mg"] == 110.0
    assert efsa_reference_values(mujer)["vit_c_mg"] == 95.0


def test_perfil_hierro_pre_y_posmenopausia():
    premeno = Profile(sex=Sex.FEMALE, age_years=30)
    posmeno = Profile(sex=Sex.FEMALE, age_years=60)
    assert efsa_reference_values(premeno)["iron_mg"] == 16.0
    assert efsa_reference_values(posmeno)["iron_mg"] == 11.0


def test_perfil_embarazo_sube_folato_y_yodo():
    normal = Profile(sex=Sex.FEMALE, age_years=30)
    embarazo = Profile(sex=Sex.FEMALE, age_years=30, life_stage=LifeStage.PREGNANCY)
    assert efsa_reference_values(normal)["vit_b9_ug_dfe"] == 330.0
    assert efsa_reference_values(embarazo)["vit_b9_ug_dfe"] == 600.0
    assert efsa_reference_values(embarazo)["iodine_ug"] == 200.0


def test_perfil_energia_depende_de_actividad():
    sedentario = Profile(sex=Sex.MALE, age_years=35, activity_level=ActivityLevel.SEDENTARY)
    activo = Profile(sex=Sex.MALE, age_years=35, activity_level=ActivityLevel.VERY_ACTIVE)
    e_sed = efsa_reference_values(sedentario)["energy_kcal"]
    e_act = efsa_reference_values(activo)["energy_kcal"]
    # 9,5 MJ * 238,83 ~= 2269 kcal ; 13,5 MJ ~= 3224 kcal
    assert e_sed == round(9.5 * 238.83, 0)
    assert e_act == round(13.5 * 238.83, 0)
    assert e_act > e_sed


def test_perfil_proteina_desde_peso():
    p = Profile(sex=Sex.MALE, age_years=35, reference_weight_kg=70.0)
    # 0,83 g/kg * 70 kg = 58,1 g
    assert efsa_reference_values(p)["protein_g"] == pytest.approx(58.1, abs=0.05)


def test_perfil_proteina_sin_peso_es_none():
    p = Profile(sex=Sex.MALE, age_years=35)  # sin peso de referencia
    assert efsa_reference_values(p)["protein_g"] is None


def test_perfil_menor_de_edad_sin_valores_por_prudencia():
    nino = Profile(sex=Sex.MALE, age_years=10)
    assert efsa_reference_values(nino) == {}


def test_cobertura_contra_perfil_efsa():
    mujer = Profile(sex=Sex.FEMALE, age_years=30)  # vit C ref = 95 mg
    cov = coverage({"vit_c_mg": 95.0}, mujer)
    assert cov["vit_c_mg"].coverage_pct == 100.0
    assert cov["vit_c_mg"].reference_kind == "efsa"


def test_niacina_y_tiamina_derivadas_de_energia():
    p = Profile(sex=Sex.MALE, age_years=35, activity_level=ActivityLevel.MODERATE)
    ref = efsa_reference_values(p)
    mj = 10.8  # hombre 30-39 a PAL 1,6
    assert ref["vit_b3_mg_ne"] == round(1.6 * mj, 2)
    assert ref["vit_b1_mg"] == round(0.1 * mj, 2)


# --------------------------------------------------------------------------
# Referencia combinada y errores
# --------------------------------------------------------------------------
def test_vrn_reference_combina_partes_a_y_b():
    ref = vrn_reference()
    assert ref["vit_c_mg"] == 80.0        # Parte A
    assert ref["energy_kcal"] == 2000.0   # Parte B
    assert ref["protein_g"] == 50.0       # Parte B


def test_referencia_string_invalida_lanza_error():
    with pytest.raises(ValueError):
        coverage({"vit_c_mg": 80.0}, "no_existe")


def test_union_incluye_nutriente_solo_en_referencia():
    # Sin aportes: los nutrientes de la referencia aparecen con intake None.
    cov = coverage({}, "vrn")
    assert cov["vit_c_mg"].intake_amount is None
    assert cov["vit_c_mg"].coverage_pct is None
    assert cov["vit_c_mg"].reference_amount == 80.0
