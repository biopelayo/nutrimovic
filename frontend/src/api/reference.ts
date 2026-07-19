// Servicio de cobertura frente a VRN/EFSA: POST /reference/coverage.
// El backend devuelve un mapa nutrient_id -> CoverageValue con `coverage_pct`.
// `profile` omitido o null => VRN del Reglamento UE 1169/2011 (etiquetado).
import { apiPost } from './client';
import type { CoverageMap } from '../types';

export interface CoverageRequest {
  nutrients_totals: Record<string, number | null>;
  profile?: unknown | null;
}

export function fetchCoverage(req: CoverageRequest, signal?: AbortSignal): Promise<CoverageMap> {
  return apiPost<CoverageMap>('/reference/coverage', req, signal);
}
