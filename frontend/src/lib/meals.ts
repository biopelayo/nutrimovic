// Reparto de la dieta por comidas del día.
export type MealId = 'desayuno' | 'media_manana' | 'comida' | 'merienda' | 'cena';

export interface MealMeta {
  id: MealId;
  label: string;
  icon: string;
  targetPct: number; // reparto orientativo de energía por comida
}

export const MEALS: MealMeta[] = [
  { id: 'desayuno', label: 'Desayuno', icon: '☕', targetPct: 25 },
  { id: 'media_manana', label: 'Media mañana', icon: '🍎', targetPct: 10 },
  { id: 'comida', label: 'Comida', icon: '🍽️', targetPct: 35 },
  { id: 'merienda', label: 'Merienda', icon: '🥪', targetPct: 10 },
  { id: 'cena', label: 'Cena', icon: '🌙', targetPct: 20 },
];

export const MEAL_BY_ID: Record<MealId, MealMeta> = Object.fromEntries(
  MEALS.map((m) => [m.id, m]),
) as Record<MealId, MealMeta>;

export const DEFAULT_MEAL: MealId = 'comida';
