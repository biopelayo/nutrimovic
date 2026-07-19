"""Aplicación FastAPI de NutriMovic."""
from __future__ import annotations

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.core.config import APP_NAME, APP_VERSION
from app.core.models import Food, FoodSummaryExt, PlateItem, PlateResult, PortionResult
from app.data.repository import get_repository
from app.engine.aggregator import calculate_plate
from app.engine.calculator import calculate_portion
from app.exchanges.seen_sed import (
    ExchangeResult,
    exchanges_for_food,
    grams_per_exchange,
)
from app.reference.coverage import CoverageValue, coverage
from app.reference.profiles import Profile

app = FastAPI(title=APP_NAME, version=APP_VERSION)

# En desarrollo el frontend PWA corre en otro puerto (Vite). CORS abierto en dev.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    repo = get_repository()
    return {"status": "ok", "app": APP_NAME, "version": APP_VERSION, "foods_loaded": repo.count()}


@app.get("/foods/search", response_model=list[FoodSummaryExt])
def search_foods(q: str = "", group: str | None = None, limit: int = Query(100, le=500)) -> list[FoodSummaryExt]:
    return get_repository().search(q=q, group=group, limit=limit)


@app.get("/foods/all", response_model=list[Food])
def all_foods() -> list[Food]:
    """Todos los alimentos completos, para la hoja de dieta con todo precargado."""
    return get_repository().all()


@app.get("/foods/{food_id}", response_model=Food)
def get_food(food_id: str) -> Food:
    food = get_repository().get(food_id)
    if food is None:
        raise HTTPException(status_code=404, detail="Alimento no encontrado")
    return food


class CalculateRequest(BaseModel):
    food_id: str
    grams: float
    use_edible_portion: bool = True


@app.post("/calculate", response_model=PortionResult)
def calculate(req: CalculateRequest) -> PortionResult:
    food = get_repository().get(req.food_id)
    if food is None:
        raise HTTPException(status_code=404, detail="Alimento no encontrado")
    try:
        return calculate_portion(food, req.grams, req.use_edible_portion)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


class PlateRequest(BaseModel):
    items: list[PlateItem]


@app.post("/plate", response_model=PlateResult)
def plate(req: PlateRequest) -> PlateResult:
    try:
        return calculate_plate(req.items, get_repository())
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/exchanges/food/{food_id}", response_model=ExchangeResult)
def exchanges_food(food_id: str, grams: float = Query(..., ge=0)) -> ExchangeResult:
    food = get_repository().get(food_id)
    if food is None:
        raise HTTPException(status_code=404, detail="Alimento no encontrado")
    return exchanges_for_food(food, grams)


@app.get("/exchanges/table")
def exchanges_table(group: str | None = None) -> list[dict]:
    """Tabla directa: gramos de cada alimento equivalentes a 1 intercambio."""
    repo = get_repository()
    rows: list[dict] = []
    for food in repo.all():
        if group and food.group.value != group:
            continue
        rows.append(
            {
                "food_id": food.id,
                "name_es": food.name_es,
                "group": food.group.value,
                "grams_per_exchange": grams_per_exchange(food),
            }
        )
    return rows


class CoverageRequest(BaseModel):
    # Totales aportados por nutriente (p. ej. los totales de un plato o dieta).
    nutrients_totals: dict[str, float | None]
    # Si se omite el perfil, se usa el VRN del Reglamento UE 1169/2011.
    profile: Profile | None = None


@app.post("/reference/coverage", response_model=dict[str, CoverageValue])
def reference_coverage(req: CoverageRequest) -> dict[str, CoverageValue]:
    reference = req.profile if req.profile is not None else "vrn"
    return coverage(req.nutrients_totals, reference)
