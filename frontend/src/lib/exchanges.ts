// Intercambios (raciones) SEEN/SED en cliente. Réplica de la lógica del backend
// (app/exchanges/seen_sed.py): 1 ración = 10 g del macronutriente de referencia.
import type { Food, FoodGroup } from '../types';

const RATION_G = 10;

export const GROUP_REFERENCE: Partial<Record<FoodGroup, string>> = {
  dairy: 'carbs_g',
  starchy: 'carbs_g',
  fruit: 'carbs_g',
  vegetable: 'carbs_g',
  protein: 'protein_g',
  fat: 'fat_g',
};

export const REFERENCE_LABEL: Record<string, string> = {
  carbs_g: 'hidratos',
  protein_g: 'proteína',
  fat_g: 'grasa',
};

export function referenceNutrient(group: FoodGroup): string | null {
  return GROUP_REFERENCE[group] ?? null;
}

/**
 * Intercambios por los TRES macronutrientes de un gramaje. Cada intercambio = 10 g
 * del macro. P. ej. 100 g de espárragos ≈ 0,2 HC · 0,2 proteína · 0 grasa.
 * `null` si el macro no está determinado para ese alimento.
 */
export interface MacroExchanges {
  hc: number | null;
  protein: number | null;
  fat: number | null;
}

export function exchangesByMacro(food: Food, grams: number): MacroExchanges {
  const g = Number.isFinite(grams) && grams > 0 ? grams : 0;
  // Sobre parte comestible, igual que el cálculo de nutrientes (coherencia).
  const edible = g * (food.edible_portion_factor ?? 1);
  const val = (id: string): number | null => {
    const v = food.nutrients[id];
    if (!v || v.status === 'not_determined' || v.amount === null) return null;
    return Math.round((v.amount * (edible / 100)) / RATION_G * 100) / 100;
  };
  return { hc: val('carbs_g'), protein: val('protein_g'), fat: val('fat_g') };
}

function usableAmount(food: Food, id: string): number | null {
  const v = food.nutrients[id];
  if (!v || v.status === 'not_determined' || v.amount === null) return null;
  return v.amount;
}

/** Intercambios que aporta `grams` de `food`, o null si no aplica. */
export function exchangesForFood(food: Food, grams: number): number | null {
  const ref = referenceNutrient(food.group);
  if (!ref) return null;
  const per100 = usableAmount(food, ref);
  if (per100 === null) return null;
  const g = Number.isFinite(grams) && grams > 0 ? grams : 0;
  return Math.round((per100 * (g / 100)) / RATION_G * 100) / 100;
}

/** Gramos de `food` equivalentes a 1 intercambio, o null si no aplica. */
export function gramsPerExchange(food: Food): number | null {
  const ref = referenceNutrient(food.group);
  if (!ref) return null;
  const per100 = usableAmount(food, ref);
  if (per100 === null || per100 === 0) return null;
  return Math.round(((RATION_G * 100) / per100) * 10) / 10;
}
