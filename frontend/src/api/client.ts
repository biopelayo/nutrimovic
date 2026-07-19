// Capa base de acceso a la API de NutriMovic.
// Base URL configurable por entorno; por defecto el backend FastAPI en desarrollo.
export const API_BASE_URL: string =
  (import.meta.env.VITE_API_BASE_URL as string | undefined)?.replace(/\/$/, '') ??
  'http://127.0.0.1:8000';

/** Error de API con informacion util para la interfaz. */
export class ApiError extends Error {
  status: number;
  /** true si el fallo es de red (backend caido, sin conexion), no una respuesta HTTP. */
  isNetwork: boolean;

  constructor(message: string, status: number, isNetwork = false) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.isNetwork = isNetwork;
  }
}

interface RequestOptions {
  method?: 'GET' | 'POST';
  body?: unknown;
  signal?: AbortSignal;
}

async function request<T>(path: string, opts: RequestOptions = {}): Promise<T> {
  const { method = 'GET', body, signal } = opts;
  let res: Response;
  try {
    res = await fetch(`${API_BASE_URL}${path}`, {
      method,
      headers: body ? { 'Content-Type': 'application/json' } : undefined,
      body: body ? JSON.stringify(body) : undefined,
      signal,
    });
  } catch (err) {
    if ((err as Error).name === 'AbortError') throw err;
    throw new ApiError(
      'No se ha podido contactar con el servidor. Comprueba que el backend está en marcha.',
      0,
      true,
    );
  }

  if (!res.ok) {
    // El backend responde {detail: "..."} en los errores.
    let detail = `Error ${res.status}`;
    try {
      const data = (await res.json()) as { detail?: string };
      if (data?.detail) detail = data.detail;
    } catch {
      // respuesta sin cuerpo JSON
    }
    throw new ApiError(detail, res.status);
  }

  // 204 sin contenido
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

export const apiGet = <T>(path: string, signal?: AbortSignal): Promise<T> =>
  request<T>(path, { method: 'GET', signal });

export const apiPost = <T>(path: string, body: unknown, signal?: AbortSignal): Promise<T> =>
  request<T>(path, { method: 'POST', body, signal });

/** Construye una query string omitiendo valores vacios. */
export function buildQuery(params: Record<string, string | number | undefined | null>): string {
  const q = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined && v !== null && v !== '') q.set(k, String(v));
  }
  const s = q.toString();
  return s ? `?${s}` : '';
}
