// Catálogo servido de forma estática (public/catalog.json). Permite que la app
// funcione sin backend (GitHub Pages). Toda la búsqueda y el cálculo son en cliente.
import type { Food, FoodSummary } from '../types';

let cache: Food[] | null = null;
let loading: Promise<Food[]> | null = null;

function load(): Promise<Food[]> {
  if (cache) return Promise.resolve(cache);
  if (!loading) {
    loading = fetch(`${import.meta.env.BASE_URL}catalog.json`)
      .then((r) => {
        if (!r.ok) throw new Error('No se pudo cargar el catálogo.');
        return r.json();
      })
      .then((data: Food[]) => {
        cache = data;
        return data;
      });
  }
  return loading;
}

export async function allFoodsLocal(): Promise<Food[]> {
  return load();
}

export async function searchLocal(q: string, limit = 100): Promise<FoodSummary[]> {
  const foods = await load();
  const qn = q.trim().toLowerCase();
  const res: FoodSummary[] = [];
  for (const f of foods) {
    if (qn && !f.name_es.toLowerCase().includes(qn)) continue;
    res.push({
      id: f.id,
      name_es: f.name_es,
      group: f.group,
      source: f.source,
      subgroup: f.subgroup,
      image_name: f.image_name,
    });
    if (res.length >= limit) break;
  }
  return res;
}

export async function getFoodLocal(id: string): Promise<Food> {
  const foods = await load();
  const f = foods.find((x) => x.id === id);
  if (!f) throw new Error('Alimento no encontrado');
  return f;
}
