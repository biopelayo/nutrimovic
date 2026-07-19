"""Tests del módulo de intercambios (raciones) SEEN/SED.

Cubren:
- Mapeo grupo -> macro de referencia.
- Función directa: gramos de alimento equivalentes a 1 intercambio.
- Función inversa (la principal): intercambios que aporta un gramaje.
- Propagación de not_determined (el macro de referencia sin dato -> None, no 0).
- Grupo sin macro de referencia (p. ej. legume) -> None con nota.
- Sustituciones: gramaje de otros alimentos para los mismos intercambios.
"""
from __future__ import annotations

import pytest

from app.core.models import (
    DataSource,
    Food,
    FoodGroup,
    FoodState,
    MeasurementStatus,
    NutrientValue,
)
from app.data.repository import get_repository
from app.exchanges.seen_sed import (
    ExchangeResult,
    exchanges_for_food,
    grams_per_exchange,
    reference_nutrient_for,
    substitutions,
)


@pytest.fixture(scope="module")
def repo():
    return get_repository()


@pytest.fixture(scope="module")
def manzana(repo):
    return repo.get("seed_manzana_cruda")


@pytest.fixture(scope="module")
def pechuga(repo):
    return repo.get("seed_pechuga_pollo_cruda")


@pytest.fixture(scope="module")
def aceite(repo):
    return repo.get("seed_aceite_oliva_virgen_extra")


@pytest.fixture(scope="module")
def arroz(repo):
    return repo.get("seed_arroz_blanco_cocido")


@pytest.fixture(scope="module")
def leche(repo):
    return repo.get("seed_leche_entera")


@pytest.fixture(scope="module")
def lenteja(repo):
    return repo.get("seed_lenteja_cocida")


# --- Mapeo grupo -> macro de referencia ---


def test_reference_nutrient_fruit_es_hc():
    assert reference_nutrient_for(FoodGroup.FRUIT) == "carbs_g"


def test_reference_nutrient_protein_es_proteina():
    assert reference_nutrient_for(FoodGroup.PROTEIN) == "protein_g"


def test_reference_nutrient_fat_es_grasa():
    assert reference_nutrient_for(FoodGroup.FAT) == "fat_g"


def test_reference_nutrient_grupo_sin_racion_es_none():
    # legume no forma parte del sistema SEEN/SED de raciones.
    assert reference_nutrient_for(FoodGroup.LEGUME) is None


# --- Función directa: gramos por intercambio ---


def test_grams_per_exchange_manzana_por_hc(manzana):
    # carbs_g = 14 g/100 g -> 1000 / 14 = 71,4 g por intercambio.
    assert grams_per_exchange(manzana) == 71.4


def test_grams_per_exchange_pechuga_por_proteina(pechuga):
    # protein_g = 22,5 g/100 g -> 1000 / 22,5 = 44,4 g por intercambio.
    assert grams_per_exchange(pechuga) == 44.4


def test_grams_per_exchange_aceite_por_grasa(aceite):
    # fat_g = 99,9 g/100 g -> 1000 / 99,9 = 10,0 g por intercambio.
    assert grams_per_exchange(aceite) == 10.0


def test_grams_per_exchange_grupo_sin_racion_es_none(lenteja):
    assert grams_per_exchange(lenteja) is None


# --- Función inversa: intercambios que aporta un gramaje ---


def test_exchanges_manzana_150g(manzana):
    # 150 g de manzana -> carbs = 14 * 1,5 = 21 g -> 21 / 10 = 2,1 intercambios.
    res = exchanges_for_food(manzana, 150)
    assert isinstance(res, ExchangeResult)
    assert res.reference_nutrient_id == "carbs_g"
    assert res.exchanges == 2.1
    assert res.status == MeasurementStatus.MEASURED


def test_exchanges_pechuga_100g(pechuga):
    # 100 g -> proteína 22,5 g -> 2,25 intercambios de proteína.
    res = exchanges_for_food(pechuga, 100)
    assert res.reference_nutrient_id == "protein_g"
    assert res.exchanges == 2.25


def test_exchanges_aceite_10g(aceite):
    # 10 g de aceite -> grasa 9,99 g -> ~1 intercambio.
    res = exchanges_for_food(aceite, 10)
    assert res.reference_nutrient_id == "fat_g"
    assert res.exchanges == 1.0


def test_exchanges_gramaje_cero(manzana):
    res = exchanges_for_food(manzana, 0)
    assert res.exchanges == 0.0
    assert res.status == MeasurementStatus.MEASURED


def test_exchanges_gramaje_negativo_lanza(manzana):
    with pytest.raises(ValueError):
        exchanges_for_food(manzana, -5)


# --- Grupo sin macro de referencia ---


def test_exchanges_grupo_sin_racion_es_none(lenteja):
    res = exchanges_for_food(lenteja, 100)
    assert res.exchanges is None
    assert res.reference_nutrient_id is None
    assert res.note is not None


# --- Propagación de not_determined ---


def test_exchanges_macro_not_determined_es_none():
    # Alimento de grupo fruit pero con carbs_g sin determinar.
    food = Food(
        id="test_fruta_sin_hc",
        name_es="Fruta de prueba sin HC medido",
        group=FoodGroup.FRUIT,
        source=DataSource.SEED_PROVISIONAL,
        state=FoodState.RAW,
        nutrients={
            "carbs_g": NutrientValue(
                nutrient_id="carbs_g",
                amount=None,
                status=MeasurementStatus.NOT_DETERMINED,
            ),
        },
    )
    res = exchanges_for_food(food, 100)
    assert res.exchanges is None
    assert res.status == MeasurementStatus.NOT_DETERMINED
    assert res.note is not None


def test_exchanges_macro_ausente_es_none():
    # El macro de referencia ni siquiera está en el dict -> not_determined.
    food = Food(
        id="test_fruta_vacia",
        name_es="Fruta de prueba sin nutrientes",
        group=FoodGroup.FRUIT,
        source=DataSource.SEED_PROVISIONAL,
        nutrients={},
    )
    res = exchanges_for_food(food, 100)
    assert res.exchanges is None
    assert res.status == MeasurementStatus.NOT_DETERMINED


def test_grams_per_exchange_macro_not_determined_es_none():
    food = Food(
        id="test_fruta_sin_hc_2",
        name_es="Fruta de prueba sin HC",
        group=FoodGroup.FRUIT,
        source=DataSource.SEED_PROVISIONAL,
        nutrients={
            "carbs_g": NutrientValue(
                nutrient_id="carbs_g",
                amount=None,
                status=MeasurementStatus.NOT_DETERMINED,
            ),
        },
    )
    assert grams_per_exchange(food) is None


# --- Sustituciones ---


def test_substitutions_incluye_solo_mismo_macro(manzana, arroz, leche, pechuga, aceite):
    # manzana es HC; arroz y leche también son HC -> intercambiables.
    # pechuga (proteína) y aceite (grasa) no son intercambiables por HC.
    subs = substitutions(manzana, 2.0, [arroz, leche, pechuga, aceite])
    ids = {s.food_id for s in subs}
    assert "seed_arroz_blanco_cocido" in ids
    assert "seed_leche_entera" in ids
    assert "seed_pechuga_pollo_cruda" not in ids
    assert "seed_aceite_oliva_virgen_extra" not in ids


def test_substitutions_excluye_el_propio_alimento(manzana, arroz):
    subs = substitutions(manzana, 2.0, [manzana, arroz])
    ids = {s.food_id for s in subs}
    assert "seed_manzana_cruda" not in ids


def test_substitutions_gramaje_correcto(manzana, arroz):
    # 2 intercambios de HC en arroz (carbs 28 g/100 g):
    # 2 * 1000 / 28 = 71,4 g.
    subs = substitutions(manzana, 2.0, [arroz])
    assert len(subs) == 1
    assert subs[0].food_id == "seed_arroz_blanco_cocido"
    assert subs[0].grams == 71.4
    assert subs[0].exchanges == 2.0
