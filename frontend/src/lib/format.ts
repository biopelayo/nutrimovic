// Utilidades de formato en espanol (coma decimal) y presentacion de estados.
import type { ResultValue, MeasurementStatus } from '../types';

const nf = new Intl.NumberFormat('es-ES', { maximumFractionDigits: 2 });
const nf0 = new Intl.NumberFormat('es-ES', { maximumFractionDigits: 0 });

/** Numero con coma decimal y como mucho 2 decimales. */
export function formatNumber(value: number): string {
  // Enteros grandes (p. ej. energia en kcal) sin decimales para legibilidad.
  if (Math.abs(value) >= 100) return nf0.format(value);
  return nf.format(value);
}

/**
 * Convierte un valor calculado en texto de interfaz respetando la regla de oro:
 *  - not_determined -> "N/D" (nunca 0)
 *  - trace          -> "trazas"
 *  - measured       -> numero + unidad
 */
export function formatResultValue(value: ResultValue): { text: string; status: MeasurementStatus } {
  if (value.status === 'not_determined') return { text: 'N/D', status: value.status };
  if (value.status === 'trace') return { text: 'trazas', status: value.status };
  const amount = value.amount ?? 0;
  return { text: `${formatNumber(amount)} ${value.unit}`.trim(), status: value.status };
}

export const STATUS_LABEL: Record<MeasurementStatus, string> = {
  measured: 'Medido',
  trace: 'Trazas',
  not_determined: 'No determinado',
};
