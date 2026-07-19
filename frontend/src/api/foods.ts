// Servicios de alimentos. La app es estática: los datos vienen del catálogo
// local (public/catalog.json) y toda la búsqueda/cálculo es en cliente.
import { allFoodsLocal, searchLocal, getFoodLocal } from '../lib/catalog';
import type { Food, FoodSummary, HealthStatus } from '../types';

export function searchFoods(
  q: string,
  opts: { group?: string; limit?: number } = {},
  _signal?: AbortSignal,
): Promise<FoodSummary[]> {
  return searchLocal(q, opts.limit ?? 25);
}

export function getFood(foodId: string, _signal?: AbortSignal): Promise<Food> {
  return getFoodLocal(foodId);
}

export function getAllFoods(_signal?: AbortSignal): Promise<Food[]> {
  return allFoodsLocal();
}

export function getHealth(_signal?: AbortSignal): Promise<HealthStatus> {
  return allFoodsLocal().then((f) => ({
    status: 'ok',
    app: 'NutriMovic',
    version: 'static',
    foods_loaded: f.length,
  }));
}
