// Espejo del catalogo canonico de nutrientes (backend/app/core/nutrients.py).
// Se usa solo para etiquetar, agrupar y ordenar en la interfaz. El backend sigue
// siendo la fuente de verdad de los valores; aqui no hay datos nutricionales.
import type { NutrientCategory } from '../types';

export interface NutrientMeta {
  id: string;
  name_es: string;
  unit: string;
  category: NutrientCategory;
}

// El orden del array es el orden de presentacion.
export const NUTRIENTS: NutrientMeta[] = [
  // Energia
  { id: 'energy_kcal', name_es: 'Energía', unit: 'kcal', category: 'energy' },
  { id: 'energy_kj', name_es: 'Energía', unit: 'kJ', category: 'energy' },
  // Macronutrientes
  { id: 'protein_g', name_es: 'Proteína', unit: 'g', category: 'macro' },
  { id: 'fat_g', name_es: 'Grasa total', unit: 'g', category: 'macro' },
  { id: 'carbs_g', name_es: 'Hidratos de carbono', unit: 'g', category: 'macro' },
  { id: 'fiber_g', name_es: 'Fibra alimentaria', unit: 'g', category: 'macro' },
  { id: 'water_g', name_es: 'Agua', unit: 'g', category: 'macro' },
  { id: 'alcohol_g', name_es: 'Alcohol', unit: 'g', category: 'macro' },
  { id: 'ash_g', name_es: 'Cenizas', unit: 'g', category: 'macro' },
  // Desglose de grasas
  { id: 'fat_saturated_g', name_es: 'Ácidos grasos saturados', unit: 'g', category: 'fat_detail' },
  { id: 'fat_monounsaturated_g', name_es: 'Ácidos grasos monoinsaturados', unit: 'g', category: 'fat_detail' },
  { id: 'fat_polyunsaturated_g', name_es: 'Ácidos grasos poliinsaturados', unit: 'g', category: 'fat_detail' },
  { id: 'fat_trans_g', name_es: 'Ácidos grasos trans', unit: 'g', category: 'fat_detail' },
  { id: 'cholesterol_mg', name_es: 'Colesterol', unit: 'mg', category: 'fat_detail' },
  { id: 'omega3_g', name_es: 'Omega-3', unit: 'g', category: 'fat_detail' },
  { id: 'omega6_g', name_es: 'Omega-6', unit: 'g', category: 'fat_detail' },
  // Desglose de hidratos
  { id: 'sugars_g', name_es: 'Azúcares totales', unit: 'g', category: 'carb_detail' },
  { id: 'sugars_added_g', name_es: 'Azúcares añadidos', unit: 'g', category: 'carb_detail' },
  { id: 'starch_g', name_es: 'Almidón', unit: 'g', category: 'carb_detail' },
  { id: 'polyols_g', name_es: 'Polioles', unit: 'g', category: 'carb_detail' },
  // Vitaminas liposolubles
  { id: 'vit_a_ug_rae', name_es: 'Vitamina A', unit: 'µg RAE', category: 'vitamin' },
  { id: 'vit_d_ug', name_es: 'Vitamina D', unit: 'µg', category: 'vitamin' },
  { id: 'vit_e_mg', name_es: 'Vitamina E', unit: 'mg α-tocoferol', category: 'vitamin' },
  { id: 'vit_k_ug', name_es: 'Vitamina K', unit: 'µg', category: 'vitamin' },
  // Vitaminas hidrosolubles
  { id: 'vit_c_mg', name_es: 'Vitamina C', unit: 'mg', category: 'vitamin' },
  { id: 'vit_b1_mg', name_es: 'Tiamina (B1)', unit: 'mg', category: 'vitamin' },
  { id: 'vit_b2_mg', name_es: 'Riboflavina (B2)', unit: 'mg', category: 'vitamin' },
  { id: 'vit_b3_mg_ne', name_es: 'Niacina (B3)', unit: 'mg NE', category: 'vitamin' },
  { id: 'vit_b5_mg', name_es: 'Ácido pantoténico (B5)', unit: 'mg', category: 'vitamin' },
  { id: 'vit_b6_mg', name_es: 'Vitamina B6', unit: 'mg', category: 'vitamin' },
  { id: 'vit_b7_ug', name_es: 'Biotina (B7)', unit: 'µg', category: 'vitamin' },
  { id: 'vit_b9_ug_dfe', name_es: 'Folato (B9)', unit: 'µg DFE', category: 'vitamin' },
  { id: 'vit_b12_ug', name_es: 'Vitamina B12', unit: 'µg', category: 'vitamin' },
  // Minerales mayores
  { id: 'calcium_mg', name_es: 'Calcio', unit: 'mg', category: 'mineral' },
  { id: 'iron_mg', name_es: 'Hierro', unit: 'mg', category: 'mineral' },
  { id: 'magnesium_mg', name_es: 'Magnesio', unit: 'mg', category: 'mineral' },
  { id: 'phosphorus_mg', name_es: 'Fósforo', unit: 'mg', category: 'mineral' },
  { id: 'potassium_mg', name_es: 'Potasio', unit: 'mg', category: 'mineral' },
  { id: 'sodium_mg', name_es: 'Sodio', unit: 'mg', category: 'mineral' },
  { id: 'zinc_mg', name_es: 'Zinc', unit: 'mg', category: 'mineral' },
  { id: 'copper_mg', name_es: 'Cobre', unit: 'mg', category: 'mineral' },
  { id: 'manganese_mg', name_es: 'Manganeso', unit: 'mg', category: 'mineral' },
  // Oligoelementos
  { id: 'selenium_ug', name_es: 'Selenio', unit: 'µg', category: 'mineral' },
  { id: 'iodine_ug', name_es: 'Yodo', unit: 'µg', category: 'mineral' },
  { id: 'chromium_ug', name_es: 'Cromo', unit: 'µg', category: 'mineral' },
  { id: 'molybdenum_ug', name_es: 'Molibdeno', unit: 'µg', category: 'mineral' },
  { id: 'fluoride_mg', name_es: 'Flúor', unit: 'mg', category: 'mineral' },
];

export const NUTRIENTS_BY_ID: Record<string, NutrientMeta> = Object.fromEntries(
  NUTRIENTS.map((n) => [n.id, n]),
);

/** Orden de indice de cada nutriente para ordenar respuestas de la API. */
export const NUTRIENT_ORDER: Record<string, number> = Object.fromEntries(
  NUTRIENTS.map((n, i) => [n.id, i]),
);

export const CATEGORY_LABELS: Record<NutrientCategory, string> = {
  energy: 'Energía',
  macro: 'Macronutrientes',
  fat_detail: 'Desglose de grasas',
  carb_detail: 'Desglose de hidratos',
  vitamin: 'Vitaminas',
  mineral: 'Minerales y oligoelementos',
};

/** Agrupacion de macros vs micros para las dos grandes secciones de la UI. */
export const MACRO_CATEGORIES: NutrientCategory[] = ['energy', 'macro', 'fat_detail', 'carb_detail'];
export const MICRO_CATEGORIES: NutrientCategory[] = ['vitamin', 'mineral'];

export const FOOD_GROUP_LABELS: Record<string, string> = {
  dairy: 'Lácteos',
  starchy: 'Farináceos',
  fruit: 'Frutas',
  vegetable: 'Verduras',
  protein: 'Carnes, pescados y huevos',
  fat: 'Grasas',
  legume: 'Legumbres',
  nuts: 'Frutos secos',
  beverage: 'Bebidas',
  sweets: 'Dulces',
  sauces: 'Salsas',
  prepared: 'Preparados',
  other: 'Otros',
};

export const SOURCE_LABELS: Record<string, string> = {
  bedca: 'BEDCA',
  usda: 'USDA',
  ciqual: 'CIQUAL',
  seed_provisional: 'Provisional',
};
