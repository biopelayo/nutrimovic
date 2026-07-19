// Tipos del frontend que reflejan el contrato de API (CONTRATOS.md, seccion 2)
// y los modelos de backend/app/core/models.py. Fuente de verdad: el backend.

export type MeasurementStatus = 'measured' | 'trace' | 'not_determined';

export type DataSource = 'bedca' | 'usda' | 'ciqual' | 'seed_provisional';

export type FoodState = 'raw' | 'cooked';

export type FoodGroup =
  | 'dairy'
  | 'starchy'
  | 'fruit'
  | 'vegetable'
  | 'protein'
  | 'fat'
  | 'legume'
  | 'nuts'
  | 'beverage'
  | 'sweets'
  | 'sauces'
  | 'prepared'
  | 'other';

export type NutrientCategory =
  | 'energy'
  | 'macro'
  | 'fat_detail'
  | 'carb_detail'
  | 'vitamin'
  | 'mineral';

/** Valor por 100 g de un alimento. */
export interface NutrientValue {
  nutrient_id: string;
  amount: number | null;
  status: MeasurementStatus;
}

export interface Food {
  id: string;
  name_es: string;
  group: FoodGroup;
  source: DataSource;
  source_ref: string | null;
  state: FoodState;
  edible_portion_factor: number;
  nutrients: Record<string, NutrientValue>;
  verified: boolean;
  subgroup?: string | null;
  image_name?: string | null;
  allergens?: string[];
  household_measure?: string | null;
}

/** Version ligera para resultados de busqueda (GET /foods/search). */
export interface FoodSummary {
  id: string;
  name_es: string;
  group: FoodGroup;
  source: DataSource;
  subgroup?: string | null;
  image_name?: string | null;
}

/** Valor calculado para un gramaje concreto. */
export interface ResultValue {
  amount: number | null;
  unit: string;
  status: MeasurementStatus;
}

/** Respuesta de POST /calculate (calculadora estrella). */
export interface PortionResult {
  food_id: string;
  name_es: string;
  grams: number;
  grams_edible: number;
  nutrients: Record<string, ResultValue>;
}

/** Item de plato para POST /plate. */
export interface PlateItemInput {
  food_id: string;
  grams: number;
}

/** Respuesta de POST /plate. */
export interface PlateResult {
  items: PortionResult[];
  totals: Record<string, ResultValue>;
  total_grams: number;
}

// --- Intercambios (contrato seccion 3). Refleja la respuesta real del backend. ---
export interface ExchangeResult {
  food_id: string;
  name_es: string;
  group: FoodGroup;
  /** nutriente de referencia del grupo (p. ej. 'carbs_g', 'protein_g', 'fat_g'). */
  reference_nutrient_id: string;
  grams: number;
  /** numero de intercambios que aporta ese gramaje. */
  exchanges: number | null;
  status: MeasurementStatus;
  note: string | null;
}

// --- Cobertura VRN/EFSA (endpoint /reference/coverage). Refleja el modelo real
// del backend: dict nutrient_id -> CoverageValue. ---
export interface CoverageValue {
  nutrient_id: string;
  intake_amount: number | null;
  reference_amount: number | null;
  unit: string;
  coverage_pct: number | null;
  status: MeasurementStatus;
  reference_kind: string; // 'vrn' | 'efsa' | 'custom'
  note: string | null;
}

export type CoverageMap = Record<string, CoverageValue>;

export interface HealthStatus {
  status: string;
  app?: string;
  version: string;
  foods_loaded: number;
}
