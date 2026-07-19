import { useMemo } from 'react';
import { coverageVRN } from '../lib/coverage';
import type { CoverageMap, ResultValue } from '../types';

interface CoverageState {
  result: CoverageMap | null;
  loading: boolean;
  error: string | null;
}

/**
 * Cobertura VRN (Reglamento UE 1169/2011) calculada en cliente. Instantánea y
 * sin backend, para el build estático. `profile` se reserva para futuras
 * referencias EFSA por perfil.
 */
export function useCoverage(
  totals: Record<string, ResultValue> | null,
  _profile: unknown | null = null,
  enabled = true,
): CoverageState {
  const result = useMemo(() => {
    if (!enabled || !totals || Object.keys(totals).length === 0) return null;
    return coverageVRN(totals);
  }, [totals, enabled]);

  return { result, loading: false, error: null };
}
