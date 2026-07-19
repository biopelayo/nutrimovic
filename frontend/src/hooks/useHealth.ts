import { useEffect, useState } from 'react';
import { getHealth } from '../api/foods';
import type { HealthStatus } from '../types';

type Connection = 'checking' | 'online' | 'offline';

interface HealthState {
  connection: Connection;
  health: HealthStatus | null;
}

/** Comprueba la disponibilidad del backend (GET /health) al arrancar. */
export function useHealth(): HealthState {
  const [state, setState] = useState<HealthState>({ connection: 'checking', health: null });

  useEffect(() => {
    const controller = new AbortController();
    getHealth(controller.signal)
      .then((health) => setState({ connection: 'online', health }))
      .catch((err: unknown) => {
        if ((err as Error).name === 'AbortError') return;
        setState({ connection: 'offline', health: null });
      });
    return () => controller.abort();
  }, []);

  return state;
}
