import { useEffect, useRef, useState } from 'react';
import { searchFoods } from '../api/foods';
import { ApiError } from '../api/client';
import { useDebounce } from './useDebounce';
import type { FoodSummary } from '../types';

interface FoodSearchState {
  results: FoodSummary[];
  loading: boolean;
  error: string | null;
}

/** Autocompletado de alimentos con debounce y cancelacion de peticiones. */
export function useFoodSearch(query: string, group?: string): FoodSearchState {
  const debounced = useDebounce(query.trim(), 250);
  const [state, setState] = useState<FoodSearchState>({
    results: [],
    loading: false,
    error: null,
  });
  const controllerRef = useRef<AbortController | null>(null);

  useEffect(() => {
    controllerRef.current?.abort();
    if (debounced.length < 2) {
      setState({ results: [], loading: false, error: null });
      return;
    }
    const controller = new AbortController();
    controllerRef.current = controller;
    setState((s) => ({ ...s, loading: true, error: null }));

    searchFoods(debounced, { group, limit: 25 }, controller.signal)
      .then((results) => setState({ results, loading: false, error: null }))
      .catch((err: unknown) => {
        if ((err as Error).name === 'AbortError') return;
        const message = err instanceof ApiError ? err.message : 'Error al buscar alimentos.';
        setState({ results: [], loading: false, error: message });
      });

    return () => controller.abort();
  }, [debounced, group]);

  return state;
}
