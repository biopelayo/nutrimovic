// Metadatos por grupo de alimentos: etiqueta, color identitario y emoji de
// respaldo (solo se usa si un alimento no tiene foto real).
import type { FoodGroup } from '../types';

export interface GroupMeta {
  id: FoodGroup;
  label: string;
  fallback: string; // emoji de respaldo
  color: string; // hex del color identitario del grupo
}

export const FOOD_GROUPS: GroupMeta[] = [
  { id: 'dairy', label: 'Lácteos', fallback: '🥛', color: '#4C86C6' },
  { id: 'starchy', label: 'Cereales y derivados', fallback: '🌾', color: '#C99A3D' },
  { id: 'fruit', label: 'Frutas', fallback: '🍎', color: '#C85C7E' },
  { id: 'vegetable', label: 'Verduras y hortalizas', fallback: '🥦', color: '#5A9E5A' },
  { id: 'protein', label: 'Carnes, pescados y huevos', fallback: '🍗', color: '#C15B4B' },
  { id: 'fat', label: 'Grasas y aceites', fallback: '🫒', color: '#C7A93D' },
  { id: 'legume', label: 'Legumbres', fallback: '🫘', color: '#8A6FB0' },
  { id: 'nuts', label: 'Frutos secos y semillas', fallback: '🥜', color: '#9A6B3F' },
  { id: 'beverage', label: 'Bebidas', fallback: '🥤', color: '#3FA0A6' },
  { id: 'sweets', label: 'Azúcares y dulces', fallback: '🍯', color: '#C77BA0' },
  { id: 'sauces', label: 'Salsas y condimentos', fallback: '🥫', color: '#7FA34A' },
  { id: 'prepared', label: 'Platos preparados', fallback: '🍲', color: '#6B7280' },
  { id: 'other', label: 'Otros', fallback: '🍽️', color: '#A8A29E' },
];

export const GROUP_BY_ID: Record<string, GroupMeta> = Object.fromEntries(
  FOOD_GROUPS.map((g) => [g.id, g]),
);
