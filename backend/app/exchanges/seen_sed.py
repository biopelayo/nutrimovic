"""Intercambios (raciones) del sistema español SEEN/SED.

Una ración de intercambio equivale a 10 g del macronutriente principal del grupo
del alimento:

- lácteos, farináceos, frutas y verduras -> hidratos de carbono (``carbs_g``)
- carnes, pescados y huevos -> proteína (``protein_g``)
- grasas -> grasa (``fat_g``)

Función directa
    Gramos de alimento equivalentes a 1 intercambio = 1000 / macro_por_100g.

Función inversa (la principal)
    Intercambios que aporta un gramaje = macro_en_ese_gramaje / 10.

Todos los gramajes se entienden sobre parte comestible (los valores del alimento
están dados por 100 g de parte comestible). El estado de medición se propaga: si
el macro de referencia es ``not_determined`` (o falta), el resultado no se rellena
con 0, sino que se devuelve ``None`` con una nota.
"""
from __future__ import annotations

from pydantic import BaseModel

from app.core.models import Food, FoodGroup, MeasurementStatus

# Una ración de intercambio = 10 g del macronutriente de referencia.
RATION_GRAMS: float = 10.0

# Precisión de salida.
_EXCHANGES_DECIMALS: int = 2
_GRAMS_DECIMALS: int = 1

# Grupo -> id del nutriente de referencia en el catálogo canónico.
# Solo los seis grupos SEEN/SED tienen ración de intercambio definida.
GROUP_REFERENCE_NUTRIENT: dict[FoodGroup, str] = {
    FoodGroup.DAIRY: "carbs_g",
    FoodGroup.STARCHY: "carbs_g",
    FoodGroup.FRUIT: "carbs_g",
    FoodGroup.VEGETABLE: "carbs_g",
    FoodGroup.PROTEIN: "protein_g",
    FoodGroup.FAT: "fat_g",
}


class ExchangeResult(BaseModel):
    """Resultado de la función inversa: intercambios que aporta un gramaje."""

    food_id: str
    name_es: str
    group: FoodGroup
    reference_nutrient_id: str | None
    grams: float
    exchanges: float | None = None
    status: MeasurementStatus = MeasurementStatus.NOT_DETERMINED
    note: str | None = None


class Substitution(BaseModel):
    """Alimento alternativo y gramaje que aporta los mismos intercambios."""

    food_id: str
    name_es: str
    group: FoodGroup
    grams: float | None = None
    exchanges: float = 0.0
    note: str | None = None


def reference_nutrient_for(group: FoodGroup) -> str | None:
    """Devuelve el id del macro de referencia del grupo, o ``None`` si no aplica."""
    return GROUP_REFERENCE_NUTRIENT.get(group)


def exchanges_for_food(food: Food, grams: float) -> ExchangeResult:
    """Cuántos intercambios aporta ``grams`` gramos de ``food`` (función inversa).

    ``exchanges = macro_en_ese_gramaje / 10``. Si el grupo no tiene ración de
    intercambio, o el macro de referencia es ``not_determined`` o falta, devuelve
    ``exchanges=None`` con una nota (nunca 0 por ausencia de dato).
    """
    if grams < 0:
        raise ValueError("El gramaje no puede ser negativo.")

    ref_id = reference_nutrient_for(food.group)
    if ref_id is None:
        return ExchangeResult(
            food_id=food.id,
            name_es=food.name_es,
            group=food.group,
            reference_nutrient_id=None,
            grams=grams,
            exchanges=None,
            status=MeasurementStatus.NOT_DETERMINED,
            note=(
                f"El grupo «{food.group.value}» no forma parte del sistema de "
                "raciones SEEN/SED."
            ),
        )

    value = food.nutrients.get(ref_id)
    if value is None or not value.is_usable() or value.amount is None:
        return ExchangeResult(
            food_id=food.id,
            name_es=food.name_es,
            group=food.group,
            reference_nutrient_id=ref_id,
            grams=grams,
            exchanges=None,
            status=MeasurementStatus.NOT_DETERMINED,
            note=(
                f"El macro de referencia «{ref_id}» no está determinado para este "
                "alimento; no se pueden calcular intercambios."
            ),
        )

    macro_in_grams = value.amount * (grams / 100.0)
    exchanges = round(macro_in_grams / RATION_GRAMS, _EXCHANGES_DECIMALS)
    return ExchangeResult(
        food_id=food.id,
        name_es=food.name_es,
        group=food.group,
        reference_nutrient_id=ref_id,
        grams=grams,
        exchanges=exchanges,
        status=value.status,
    )


def grams_per_exchange(food: Food) -> float | None:
    """Gramos de ``food`` equivalentes a 1 intercambio (función directa).

    ``gramos = 1000 / macro_por_100g``. Devuelve ``None`` si el grupo no tiene
    ración de intercambio o el macro de referencia no está determinado.
    """
    ref_id = reference_nutrient_for(food.group)
    if ref_id is None:
        return None

    value = food.nutrients.get(ref_id)
    if value is None or not value.is_usable() or value.amount is None or value.amount == 0:
        return None

    grams = (RATION_GRAMS * 100.0) / value.amount
    return round(grams, _GRAMS_DECIMALS)


def substitutions(
    food: Food, target_exchanges: float, candidates: list[Food]
) -> list[Substitution]:
    """Gramaje de cada alternativa para aportar ``target_exchanges`` intercambios.

    Solo se consideran candidatos intercambiables con ``food``, es decir, los que
    comparten el mismo macro de referencia (mismo tipo de ración). Se excluye el
    propio ``food``. Si un candidato tiene el macro sin determinar, se incluye con
    ``grams=None`` y una nota.
    """
    ref_id = reference_nutrient_for(food.group)
    if ref_id is None:
        return []

    subs: list[Substitution] = []
    for cand in candidates:
        if cand.id == food.id:
            continue
        if reference_nutrient_for(cand.group) != ref_id:
            continue

        per_exchange = grams_per_exchange(cand)
        if per_exchange is None:
            subs.append(
                Substitution(
                    food_id=cand.id,
                    name_es=cand.name_es,
                    group=cand.group,
                    grams=None,
                    exchanges=target_exchanges,
                    note=(
                        f"El macro de referencia «{ref_id}» no está determinado "
                        "para este alimento."
                    ),
                )
            )
            continue

        grams = round(per_exchange * target_exchanges, _GRAMS_DECIMALS)
        subs.append(
            Substitution(
                food_id=cand.id,
                name_es=cand.name_es,
                group=cand.group,
                grams=grams,
                exchanges=target_exchanges,
            )
        )
    return subs
