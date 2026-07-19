// Servicio del constructor de plato: POST /plate.
//
// ESTADO DE INTEGRACION: el endpoint /plate esta en el contrato (CONTRATOS.md 2)
// pero puede no estar implementado aun en el backend. `fetchPlate` intenta la API;
// si no responde, `aggregatePortions` hace la suma en cliente a partir de varias
// llamadas a /calculate. El hook usePlate encadena ambos automaticamente.
import { apiPost } from './client';
import type { PlateItemInput, PlateResult, PortionResult, ResultValue, MeasurementStatus } from '../types';

export function fetchPlate(items: PlateItemInput[], signal?: AbortSignal): Promise<PlateResult> {
  return apiPost<PlateResult>('/plate', { items }, signal);
}

/**
 * Suma en cliente de varios PortionResult (respaldo mientras /plate no exista).
 *
 * Regla de estado (provisional, conservadora): para cada nutriente
 *  - si algun item lo tiene como `not_determined` -> el total es `not_determined`
 *    (no se puede garantizar el total con una contribucion desconocida);
 *  - si no, `measured` si hay algun medido, en otro caso `trace`.
 * Los importes suman solo valores medidos o en trazas (null cuenta como 0).
 */
export function aggregatePortions(portions: PortionResult[]): PlateResult {
  const totals: Record<string, ResultValue> = {};
  const totalGrams = portions.reduce((acc, p) => acc + p.grams, 0);

  for (const portion of portions) {
    for (const [id, value] of Object.entries(portion.nutrients)) {
      const current = totals[id];
      if (!current) {
        totals[id] = {
          amount: value.status === 'not_determined' ? null : value.amount ?? 0,
          unit: value.unit,
          status: value.status,
        };
        continue;
      }
      const nextStatus: MeasurementStatus =
        current.status === 'not_determined' || value.status === 'not_determined'
          ? 'not_determined'
          : current.status === 'measured' || value.status === 'measured'
            ? 'measured'
            : 'trace';
      const nextAmount =
        nextStatus === 'not_determined'
          ? null
          : (current.amount ?? 0) + (value.status === 'not_determined' ? 0 : value.amount ?? 0);
      totals[id] = { amount: nextAmount, unit: current.unit || value.unit, status: nextStatus };
    }
  }

  return { items: portions, totals, total_grams: totalGrams };
}
