"""Batería de tests del motor de cálculo de NutriMovic.

Cubre la calculadora por gramaje (regla de tres, parte comestible, casos límite),
la agregación de platos (suma con propagación de `not_determined`) y los cálculos
derivados de dietética (reparto de macros y cuadre energético).

Las Food de los tests son fixtures sintéticas: valores inventados solo para
ejercitar la lógica del motor, nunca datos nutricionales que vayan a la base real.
"""
from __future__ import annotations

import math

import pytest

from app.core.models import (
    Food,
    FoodGroup,
    DataSource,
    MeasurementStatus,
    NutrientValue,
    PlateItem,
)
from app.data.repository import FoodRepository
from app.engine.calculator import calculate_portion
from app.engine.aggregator import calculate_plate
from app.engine.derived import (
    macro_energy_split,
    energy_check,
)


# --------------------------------------------------------------------------- #
# Helpers de fixtures                                                          #
# --------------------------------------------------------------------------- #
def _nv(nid: str, amount: float | None, status: MeasurementStatus) -> NutrientValue:
    return NutrientValue(nutrient_id=nid, amount=amount, status=status)


def make_food(
    food_id: str,
    nutrients: dict[str, NutrientValue],
    *,
    edible_portion_factor: float = 1.0,
    group: FoodGroup = FoodGroup.OTHER,
) -> Food:
    return Food(
        id=food_id,
        name_es=food_id,
        group=group,
        source=DataSource.SEED_PROVISIONAL,
        edible_portion_factor=edible_portion_factor,
        nutrients=nutrients,
    )


MEASURED = MeasurementStatus.MEASURED
TRACE = MeasurementStatus.TRACE
ND = MeasurementStatus.NOT_DETERMINED


# --------------------------------------------------------------------------- #
# Calculadora por gramaje                                                      #
# --------------------------------------------------------------------------- #
def test_regla_de_tres_escala_lineal():
    """El valor por 100 g se escala linealmente con los gramos."""
    food = make_food("pan", {"energy_kcal": _nv("energy_kcal", 250.0, MEASURED)})
    res = calculate_portion(food, 200.0)
    assert res.nutrients["energy_kcal"].amount == pytest.approx(500.0)
    assert res.grams == 200.0
    assert res.grams_edible == 200.0


def test_parte_comestible_se_aplica_por_defecto():
    """Con parte comestible <1, los gramos aprovechables bajan y el nutriente también."""
    food = make_food(
        "platano",
        {"potassium_mg": _nv("potassium_mg", 350.0, MEASURED)},
        edible_portion_factor=0.68,
    )
    res = calculate_portion(food, 100.0, use_edible_portion=True)
    assert res.grams_edible == pytest.approx(68.0)
    assert res.nutrients["potassium_mg"].amount == pytest.approx(350.0 * 0.68)


def test_parte_comestible_se_ignora_si_se_pide():
    """Con use_edible_portion=False se usan los gramos brutos."""
    food = make_food(
        "platano",
        {"potassium_mg": _nv("potassium_mg", 350.0, MEASURED)},
        edible_portion_factor=0.68,
    )
    res = calculate_portion(food, 100.0, use_edible_portion=False)
    assert res.grams_edible == pytest.approx(100.0)
    assert res.nutrients["potassium_mg"].amount == pytest.approx(350.0)


def test_gramaje_cero_da_cero_en_medidos():
    """Gramaje 0 es válido: los medidos valen 0, los no determinados siguen None."""
    food = make_food(
        "queso",
        {
            "calcium_mg": _nv("calcium_mg", 800.0, MEASURED),
            "vit_d_ug": _nv("vit_d_ug", None, ND),
        },
    )
    res = calculate_portion(food, 0.0)
    assert res.grams_edible == 0.0
    assert res.nutrients["calcium_mg"].amount == 0.0
    assert res.nutrients["calcium_mg"].status == MEASURED
    assert res.nutrients["vit_d_ug"].amount is None
    assert res.nutrients["vit_d_ug"].status == ND


def test_gramaje_negativo_lanza_valueerror():
    food = make_food("agua", {"water_g": _nv("water_g", 100.0, MEASURED)})
    with pytest.raises(ValueError):
        calculate_portion(food, -50.0)


def test_gramaje_no_finito_lanza_valueerror():
    """NaN o infinito no son gramajes válidos."""
    food = make_food("agua", {"water_g": _nv("water_g", 100.0, MEASURED)})
    with pytest.raises(ValueError):
        calculate_portion(food, math.nan)
    with pytest.raises(ValueError):
        calculate_portion(food, math.inf)


def test_not_determined_se_propaga_en_gramaje():
    """Un valor no determinado nunca se convierte en 0 al escalar."""
    food = make_food("seta", {"selenium_ug": _nv("selenium_ug", None, ND)})
    res = calculate_portion(food, 300.0)
    assert res.nutrients["selenium_ug"].amount is None
    assert res.nutrients["selenium_ug"].status == ND


def test_trace_se_conserva():
    """El estado `trace` se conserva y su valor (~0) se escala."""
    food = make_food("lechuga", {"fat_g": _nv("fat_g", 0.1, TRACE)})
    res = calculate_portion(food, 200.0)
    assert res.nutrients["fat_g"].status == TRACE
    assert res.nutrients["fat_g"].amount == pytest.approx(0.2)


def test_unidad_se_rellena_desde_catalogo():
    food = make_food("pan", {"energy_kcal": _nv("energy_kcal", 250.0, MEASURED)})
    res = calculate_portion(food, 100.0)
    assert res.nutrients["energy_kcal"].unit == "kcal"


# --------------------------------------------------------------------------- #
# Agregación de platos                                                         #
# --------------------------------------------------------------------------- #
def _repo(*foods: Food) -> FoodRepository:
    return FoodRepository({f.id: f for f in foods})


def test_plato_suma_nutrientes_medidos():
    """Dos alimentos con un nutriente medido: el total es la suma y queda medido."""
    a = make_food("a", {"protein_g": _nv("protein_g", 10.0, MEASURED)})
    b = make_food("b", {"protein_g": _nv("protein_g", 20.0, MEASURED)})
    repo = _repo(a, b)
    res = calculate_plate([PlateItem(food_id="a", grams=100.0), PlateItem(food_id="b", grams=100.0)], repo)
    assert res.totals["protein_g"].amount == pytest.approx(30.0)
    assert res.totals["protein_g"].status == MEASURED
    assert res.total_grams == pytest.approx(200.0)
    assert len(res.items) == 2


def test_plato_propaga_not_determined():
    """Si un alimento aporta el nutriente como not_determined, el total es not_determined."""
    a = make_food("a", {"iron_mg": _nv("iron_mg", 2.0, MEASURED)})
    b = make_food("b", {"iron_mg": _nv("iron_mg", None, ND)})
    repo = _repo(a, b)
    res = calculate_plate([PlateItem(food_id="a", grams=100.0), PlateItem(food_id="b", grams=100.0)], repo)
    assert res.totals["iron_mg"].status == ND
    assert res.totals["iron_mg"].amount is None


def test_plato_solo_suma_alimentos_que_aportan():
    """Un alimento que no declara el nutriente no cuenta como contribuyente."""
    a = make_food("a", {"calcium_mg": _nv("calcium_mg", 120.0, MEASURED)})
    b = make_food("b", {"protein_g": _nv("protein_g", 8.0, MEASURED)})  # sin calcio
    repo = _repo(a, b)
    res = calculate_plate([PlateItem(food_id="a", grams=100.0), PlateItem(food_id="b", grams=100.0)], repo)
    # El calcio lo aporta solo `a`: total medido = solo su aporte.
    assert res.totals["calcium_mg"].status == MEASURED
    assert res.totals["calcium_mg"].amount == pytest.approx(120.0)
    # La proteína solo la aporta `b`.
    assert res.totals["protein_g"].amount == pytest.approx(8.0)


def test_plato_alimento_inexistente_lanza_valueerror():
    a = make_food("a", {"protein_g": _nv("protein_g", 10.0, MEASURED)})
    repo = _repo(a)
    with pytest.raises(ValueError):
        calculate_plate([PlateItem(food_id="fantasma", grams=100.0)], repo)


def test_plato_trace_no_degrada_a_not_determined():
    """Contribuyentes trace + measured siguen siendo un total utilizable (measured)."""
    a = make_food("a", {"fat_g": _nv("fat_g", 5.0, MEASURED)})
    b = make_food("b", {"fat_g": _nv("fat_g", 0.05, TRACE)})
    repo = _repo(a, b)
    res = calculate_plate([PlateItem(food_id="a", grams=100.0), PlateItem(food_id="b", grams=100.0)], repo)
    assert res.totals["fat_g"].status == MEASURED
    assert res.totals["fat_g"].amount == pytest.approx(5.05)


def test_plato_vacio_da_totales_vacios():
    res = calculate_plate([], _repo())
    assert res.items == []
    assert res.totals == {}
    assert res.total_grams == 0.0


# --------------------------------------------------------------------------- #
# Cálculos derivados                                                          #
# --------------------------------------------------------------------------- #
def test_reparto_macros_porcentaje_energia():
    """Reparto de macros: proteína×4, HC×4, grasa×9 kcal/g sobre el total."""
    # 25 g prot (100 kcal) + 50 g HC (200 kcal) + 20 g grasa (180 kcal) = 480 kcal.
    dist = macro_energy_split(protein_g=25.0, carbs_g=50.0, fat_g=20.0)
    assert dist.energy_from_macros_kcal == pytest.approx(480.0)
    assert dist.protein_pct == pytest.approx(100.0 / 480.0 * 100, abs=0.1)
    assert dist.carbs_pct == pytest.approx(200.0 / 480.0 * 100, abs=0.1)
    assert dist.fat_pct == pytest.approx(180.0 / 480.0 * 100, abs=0.1)
    # Los porcentajes suman ~100.
    assert dist.protein_pct + dist.carbs_pct + dist.fat_pct + dist.alcohol_pct == pytest.approx(100.0, abs=0.1)


def test_reparto_macros_incluye_alcohol():
    """El alcohol aporta 7 kcal/g al reparto."""
    dist = macro_energy_split(protein_g=0.0, carbs_g=0.0, fat_g=0.0, alcohol_g=10.0)
    assert dist.energy_from_macros_kcal == pytest.approx(70.0)
    assert dist.alcohol_pct == pytest.approx(100.0, abs=0.1)


def test_reparto_macros_todo_cero_no_divide_por_cero():
    dist = macro_energy_split(protein_g=0.0, carbs_g=0.0, fat_g=0.0)
    assert dist.energy_from_macros_kcal == 0.0
    assert dist.protein_pct == 0.0
    assert dist.carbs_pct == 0.0
    assert dist.fat_pct == 0.0


def test_cuadre_energia_dentro_de_tolerancia():
    """La energía declarada cuadra con la de los macros dentro de tolerancia."""
    # 5 g prot + 10 g HC + 5 g grasa = 20+40+45 = 105 kcal.
    chk = energy_check(declared_kcal=105.0, protein_g=5.0, carbs_g=10.0, fat_g=5.0)
    assert chk.computed_kcal == pytest.approx(105.0)
    assert chk.within_tolerance is True


def test_cuadre_energia_fuera_de_tolerancia():
    chk = energy_check(declared_kcal=100.0, protein_g=5.0, carbs_g=10.0, fat_g=15.0)
    # Computado = 20+40+135 = 195 kcal, muy lejos de 100.
    assert chk.computed_kcal == pytest.approx(195.0)
    assert chk.within_tolerance is False
