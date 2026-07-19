// Servicio de intercambios SEEN/SED: GET /exchanges/food/{id}?grams=
//
// ESTADO DE INTEGRACION: endpoint contratado (CONTRATOS.md 2 y 3) que puede no
// existir aun. El servicio esta tipado y listo; el componente ExchangeView
// muestra un aviso claro de "pendiente de integracion" cuando la API responde 404.
import { apiGet, buildQuery } from './client';
import type { ExchangeResult } from '../types';

export function getFoodExchanges(
  foodId: string,
  grams: number,
  signal?: AbortSignal,
): Promise<ExchangeResult> {
  const query = buildQuery({ grams });
  return apiGet<ExchangeResult>(`/exchanges/food/${encodeURIComponent(foodId)}${query}`, signal);
}
