// Cálculo nutricional en cliente para el recálculo instantáneo tipo hoja de
// cálculo. Replica la regla del backend (contrato §2.2) para no depender de una
// petición por cada tecla. La cobertura VRN sí se pide al backend.
import type { Food, ResultValue, MeasurementStatus } from '../types';
import { NUTRIENTS, NUTRIENTS_BY_ID } from '../data/nutrients';

function round(n: number, d = 4): number {
  const f = 10 ** d;
  return Math.round(n * f) / f;
}

/** Escala la composición de un alimento (por 100 g) al gramaje indicado. */
export function scaleFood(food: Food, grams: number, useEdible = true): Record<string, ResultValue> {
  const safeGrams = Number.isFinite(grams) && grams > 0 ? grams : 0;
  const factor = useEdible ? food.edible_portion_factor : 1;
  const scale = (safeGrams * factor) / 100;
  const out: Record<string, ResultValue> = {};
  for (const [id, v] of Object.entries(food.nutrients)) {
    const unit = NUTRIENTS_BY_ID[id]?.unit ?? '';
    if (v.status === 'not_determined' || v.amount === null) {
      out[id] = { amount: null, unit, status: 'not_determined' };
    } else {
      out[id] = { amount: round(v.amount * scale), unit, status: v.status };
    }
  }
  return out;
}

/** Gramos de parte comestible de un gramaje bruto. */
export function edibleGrams(food: Food, grams: number, useEdible = true): number {
  return round(grams * (useEdible ? food.edible_portion_factor : 1), 2);
}

/**
 * Suma varias filas (cada una es un mapa nutriente→ResultValue) respetando la
 * regla de oro: solo cuentan los alimentos que aportan el nutriente; si alguno lo
 * aporta como no determinado, el total es no determinado (nunca 0 por hueco).
 */
export function sumRows(rows: Array<Record<string, ResultValue>>): Record<string, ResultValue> {
  const totals: Record<string, ResultValue> = {};
  const ids = new Set<string>();
  rows.forEach((r) => Object.keys(r).forEach((id) => ids.add(id)));

  for (const id of ids) {
    const contribs = rows.map((r) => r[id]).filter((v): v is ResultValue => v !== undefined);
    const unit = NUTRIENTS_BY_ID[id]?.unit ?? '';
    if (contribs.some((c) => c.status === 'not_determined')) {
      totals[id] = { amount: null, unit, status: 'not_determined' };
      continue;
    }
    const amount = round(contribs.reduce((s, c) => s + (c.amount ?? 0), 0));
    const status: MeasurementStatus = contribs.some((c) => c.status === 'measured')
      ? 'measured'
      : 'trace';
    totals[id] = { amount, unit, status };
  }
  return totals;
}

/** Cantidades utilizables (measured/trace) como {id: número}, para la cobertura. */
export function usableAmounts(totals: Record<string, ResultValue>): Record<string, number> {
  const out: Record<string, number> = {};
  for (const [id, v] of Object.entries(totals)) {
    if (v.status !== 'not_determined' && v.amount !== null) out[id] = v.amount;
  }
  return out;
}

export interface MacroSplit {
  proteinKcal: number;
  carbsKcal: number;
  fatKcal: number;
  alcoholKcal: number;
  totalKcal: number;
  proteinPct: number;
  carbsPct: number;
  fatPct: number;
  alcoholPct: number;
}

/** Reparto de energía por macronutriente (factores de Atwater 4/4/9/7). */
export function macroSplit(totals: Record<string, ResultValue>): MacroSplit | null {
  const g = (id: string) => (totals[id]?.status !== 'not_determined' ? totals[id]?.amount ?? 0 : 0);
  const proteinKcal = g('protein_g') * 4;
  const carbsKcal = g('carbs_g') * 4;
  const fatKcal = g('fat_g') * 9;
  const alcoholKcal = g('alcohol_g') * 7;
  const totalKcal = proteinKcal + carbsKcal + fatKcal + alcoholKcal;
  if (totalKcal <= 0) return null;
  return {
    proteinKcal,
    carbsKcal,
    fatKcal,
    alcoholKcal,
    totalKcal,
    proteinPct: round((proteinKcal / totalKcal) * 100, 1),
    carbsPct: round((carbsKcal / totalKcal) * 100, 1),
    fatPct: round((fatKcal / totalKcal) * 100, 1),
    alcoholPct: round((alcoholKcal / totalKcal) * 100, 1),
  };
}

/** Nutrientes que se muestran por defecto en las columnas de la hoja. */
export const DEFAULT_SHEET_NUTRIENTS: string[] = [
  'energy_kcal',
  'protein_g',
  'fat_g',
  'carbs_g',
  'fiber_g',
];

/** Todos los micronutrientes disponibles como columnas opcionales. */
export const MICRO_NUTRIENT_IDS: string[] = NUTRIENTS.filter(
  (n) => n.category === 'vitamin' || n.category === 'mineral',
).map((n) => n.id);
