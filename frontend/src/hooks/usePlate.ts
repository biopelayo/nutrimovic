import { useEffect, useRef, useState } from 'react';
import { fetchPlate, aggregatePortions } from '../api/plate';
import { calculatePortion } from '../api/calculate';
import { ApiError } from '../api/client';
import type { PlateResult, PlateItemInput } from '../types';

export interface PlateEntry extends PlateItemInput {
  /** id de fila local para React (los alimentos pueden repetirse). */
  key: string;
  name_es: string;
}

interface PlateState {
  result: PlateResult | null;
  loading: boolean;
  error: string | null;
  /** true si se ha sumado en cliente porque /plate no respondio. */
  usedFallback: boolean;
}

// Estados HTTP que indican "endpoint aun no implementado" -> conviene el respaldo.
const NOT_IMPLEMENTED = new Set([404, 405, 501, 400]);

/**
 * Calcula el total del plato. Intenta POST /plate; si el endpoint no existe,
 * suma en cliente combinando varias llamadas a /calculate (aggregatePortions).
 */
export function usePlate(entries: PlateEntry[], useEdiblePortion: boolean): PlateState {
  const [state, setState] = useState<PlateState>({
    result: null,
    loading: false,
    error: null,
    usedFallback: false,
  });
  const controllerRef = useRef<AbortController | null>(null);

  // Clave estable de dependencia (evita recalcular sin cambios reales).
  const depKey = entries.map((e) => `${e.food_id}:${e.grams}`).join('|') + `#${useEdiblePortion}`;

  useEffect(() => {
    controllerRef.current?.abort();
    const items = entries.filter((e) => Number.isFinite(e.grams) && e.grams > 0);
    if (items.length === 0) {
      setState({ result: null, loading: false, error: null, usedFallback: false });
      return;
    }
    const controller = new AbortController();
    controllerRef.current = controller;
    setState((s) => ({ ...s, loading: true, error: null }));

    const payload: PlateItemInput[] = items.map((e) => ({ food_id: e.food_id, grams: e.grams }));

    async function run() {
      try {
        const result = await fetchPlate(payload, controller.signal);
        setState({ result, loading: false, error: null, usedFallback: false });
      } catch (err) {
        if ((err as Error).name === 'AbortError') return;
        const apiErr = err instanceof ApiError ? err : null;
        // Si /plate no esta implementado, sumamos en cliente.
        if (!apiErr || NOT_IMPLEMENTED.has(apiErr.status)) {
          try {
            const portions = await Promise.all(
              items.map((e) =>
                calculatePortion(
                  { food_id: e.food_id, grams: e.grams, use_edible_portion: useEdiblePortion },
                  controller.signal,
                ),
              ),
            );
            setState({
              result: aggregatePortions(portions),
              loading: false,
              error: null,
              usedFallback: true,
            });
            return;
          } catch (err2) {
            if ((err2 as Error).name === 'AbortError') return;
            const msg =
              err2 instanceof ApiError ? err2.message : 'Error al calcular el plato.';
            setState({ result: null, loading: false, error: msg, usedFallback: false });
            return;
          }
        }
        setState({ result: null, loading: false, error: apiErr.message, usedFallback: false });
      }
    }
    void run();

    return () => controller.abort();
    // depKey resume food_id/grams/useEdiblePortion de todas las filas.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [depKey]);

  return state;
}
