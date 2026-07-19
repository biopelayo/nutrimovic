"""Modelos canónicos compartidos de NutriMovic.

Fuente de verdad de los tipos de datos. Todos los módulos (motor, intercambios,
ETL, API) importan desde aquí. No duplicar estas definiciones en otro sitio.
"""
from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class MeasurementStatus(str, Enum):
    """Estado de un valor nutricional. Distingue cero real de ausencia de dato."""

    MEASURED = "measured"
    TRACE = "trace"
    NOT_DETERMINED = "not_determined"


class DataSource(str, Enum):
    BEDCA = "bedca"
    USDA = "usda"
    CIQUAL = "ciqual"
    SEED_PROVISIONAL = "seed_provisional"


class FoodState(str, Enum):
    RAW = "raw"
    COOKED = "cooked"


class FoodGroup(str, Enum):
    # Grupos SEEN/SED
    DAIRY = "dairy"
    STARCHY = "starchy"
    FRUIT = "fruit"
    VEGETABLE = "vegetable"
    PROTEIN = "protein"
    FAT = "fat"
    # Auxiliares para cobertura completa
    LEGUME = "legume"
    NUTS = "nuts"
    BEVERAGE = "beverage"
    SWEETS = "sweets"
    SAUCES = "sauces"
    PREPARED = "prepared"
    OTHER = "other"


class NutrientCategory(str, Enum):
    ENERGY = "energy"
    MACRO = "macro"
    FAT_DETAIL = "fat_detail"
    CARB_DETAIL = "carb_detail"
    VITAMIN = "vitamin"
    MINERAL = "mineral"


class NutrientDef(BaseModel):
    """Definición de un nutriente del catálogo canónico."""

    id: str
    name_es: str
    unit: str
    category: NutrientCategory
    usda_ids: list[int] = Field(default_factory=list)
    bedca_ids: list[str] = Field(default_factory=list)
    ciqual_ids: list[str] = Field(default_factory=list)


class NutrientValue(BaseModel):
    """Valor de un nutriente para un alimento, por 100 g de parte comestible."""

    nutrient_id: str
    amount: float | None = None
    status: MeasurementStatus = MeasurementStatus.NOT_DETERMINED

    def is_usable(self) -> bool:
        return self.status in (MeasurementStatus.MEASURED, MeasurementStatus.TRACE)


class Food(BaseModel):
    """Alimento con su composición por 100 g de parte comestible."""

    id: str
    name_es: str
    group: FoodGroup
    source: DataSource
    source_ref: str | None = None
    state: FoodState = FoodState.RAW
    edible_portion_factor: float = 1.0
    nutrients: dict[str, NutrientValue] = Field(default_factory=dict)
    verified: bool = False
    # Clasificación científica fina dentro del grupo (p. ej. "Pescado azul").
    subgroup: str | None = None
    # Nombre del ingrediente en TheMealDB para la foto real (p. ej. "Chicken Breast").
    image_name: str | None = None
    # Alérgenos declarables (UE): "gluten", "lactosa", "huevo", "pescado",
    # "crustaceos", "moluscos", "frutos_secos", "cacahuetes", "soja", "sesamo", "sulfitos".
    allergens: list[str] = Field(default_factory=list)
    # Medida casera habitual (estilo Moreiras): p. ej. "1 vaso (200 g)".
    household_measure: str | None = None


class FoodSummary(BaseModel):
    """Versión ligera para resultados de búsqueda."""

    id: str
    name_es: str
    group: FoodGroup
    source: DataSource


class FoodSummaryExt(FoodSummary):
    """Resumen con subgrupo e imagen, para el navegador de alimentos."""

    subgroup: str | None = None
    image_name: str | None = None


class ResultValue(BaseModel):
    """Valor calculado para un gramaje concreto."""

    amount: float | None = None
    unit: str
    status: MeasurementStatus = MeasurementStatus.NOT_DETERMINED


class PortionResult(BaseModel):
    """Resultado de la calculadora por gramaje."""

    food_id: str
    name_es: str
    grams: float
    grams_edible: float
    nutrients: dict[str, ResultValue] = Field(default_factory=dict)


class PlateItem(BaseModel):
    food_id: str
    grams: float


class PlateResult(BaseModel):
    items: list[PortionResult] = Field(default_factory=list)
    totals: dict[str, ResultValue] = Field(default_factory=dict)
    total_grams: float = 0.0
