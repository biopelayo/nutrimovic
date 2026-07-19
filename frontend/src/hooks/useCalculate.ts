import { useEffect, useRef, useState } from 'react';
import { calculatePortion } from '../api/calculate';
import { ApiError } from '../api/client';
import { useDebounce } from './useDebounce';
import type { PortionResult } from '../types';

interface CalculateState {
  result: PortionResult | null;
  loading: boolean;
  error: string | null;
}

/**
 * Calcula la porcion (POST /calculate) cuando cambian alimento, gramos o la
 * opcion de parte comestible. Debounce sobre los gramos para no saturar la API
 * mientras el usuario teclea.
 */
export function useCalculate(
  foodId: string | null,
  grams: number,
  useEdiblePortion: boolean,
): CalculateState {
  const debouncedGrams = useDebounce(grams, 300);
  const [state, setState] = useState<CalculateState>({
    result: null,
    loading: false,
    error: null,
  });
  const controllerRef = useRef<AbortController | null>(null);

  useEffect(() => {
    controllerRef.current?.abort();
    if (!foodId || !Number.isFinite(debouncedGrams) || debouncedGrams <= 0) {
      setState({ result: null, loading: false, error: null });
      return;
    }
    const controller = new AbortController();
    controllerRef.current = controller;
    setState((s) => ({ ...s, loading: true, error: null }));

    calculatePortion(
      { food_id: foodId, grams: debouncedGrams, use_edible_portion: useEdiblePortion },
      controller.signal,
    )
      .then((result) => setState({ result, loading: false, error: null }))
      .catch((err: unknown) => {
        if ((err as Error).name === 'AbortError') return;
        const message = err instanceof ApiError ? err.message : 'Error al calcular la porción.';
        setState({ result: null, loading: false, error: message });
      });

    return () => controller.abort();
  }, [foodId, debouncedGrams, useEdiblePortion]);

  return state;
}
