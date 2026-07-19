// Servicio de la calculadora estrella: POST /calculate.
import { apiPost } from './client';
import type { PortionResult } from '../types';

export interface CalculateRequest {
  food_id: string;
  grams: number;
  use_edible_portion: boolean;
}

export function calculatePortion(
  req: CalculateRequest,
  signal?: AbortSignal,
): Promise<PortionResult> {
  return apiPost<PortionResult>('/calculate', req, signal);
}
