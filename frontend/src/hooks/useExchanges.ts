import { useEffect, useRef, useState } from 'react';
import { getFoodExchanges } from '../api/exchanges';
import { ApiError } from '../api/client';
import { useDebounce } from './useDebounce';
import type { ExchangeResult } from '../types';

interface ExchangeState {
  result: ExchangeResult | null;
  loading: boolean;
  error: string | null;
  /** true si el endpoint /exchanges no existe todavia (pendiente de integracion). */
  notImplemented: boolean;
}

const NOT_IMPLEMENTED = new Set([404, 405, 501]);

/** Intercambios que aporta un alimento en un gramaje (GET /exchanges/food/{id}). */
export function useExchanges(foodId: string | null, grams: number): ExchangeState {
  const debouncedGrams = useDebounce(grams, 300);
  const [state, setState] = useState<ExchangeState>({
    result: null,
    loading: false,
    error: null,
    notImplemented: false,
  });
  const controllerRef = useRef<AbortController | null>(null);

  useEffect(() => {
    controllerRef.current?.abort();
    if (!foodId || !Number.isFinite(debouncedGrams) || debouncedGrams <= 0) {
      setState({ result: null, loading: false, error: null, notImplemented: false });
      return;
    }
    const controller = new AbortController();
    controllerRef.current = controller;
    setState((s) => ({ ...s, loading: true, error: null, notImplemented: false }));

    getFoodExchanges(foodId, debouncedGrams, controller.signal)
      .then((result) =>
        setState({ result, loading: false, error: null, notImplemented: false }),
      )
      .catch((err: unknown) => {
        if ((err as Error).name === 'AbortError') return;
        const apiErr = err instanceof ApiError ? err : null;
        if (apiErr && NOT_IMPLEMENTED.has(apiErr.status)) {
          setState({ result: null, loading: false, error: null, notImplemented: true });
          return;
        }
        const message = apiErr ? apiErr.message : 'Error al obtener intercambios.';
        setState({ result: null, loading: false, error: message, notImplemented: false });
      });

    return () => controller.abort();
  }, [foodId, debouncedGrams]);

  return state;
}
