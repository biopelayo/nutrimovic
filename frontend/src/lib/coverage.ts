// Cobertura frente al VRN (Reglamento UE 1169/2011, Anexo XIII) calculada en
// cliente, para que la app funcione sin backend (build estático).
import { NUTRIENTS_BY_ID } from '../data/nutrients';
import type { CoverageMap, ResultValue } from '../types';
import { usableAmounts } from './nutrition';

// VRN del adulto medio (Reglamento UE 1169/2011). Clave = nutrient_id canónico.
export const VRN: Record<string, number> = {
  vit_a_ug_rae: 800,
  vit_d_ug: 5,
  vit_e_mg: 12,
  vit_k_ug: 75,
  vit_c_mg: 80,
  vit_b1_mg: 1.1,
  vit_b2_mg: 1.4,
  vit_b3_mg_ne: 16,
  vit_b5_mg: 6,
  vit_b6_mg: 1.4,
  vit_b7_ug: 50,
  vit_b9_ug_dfe: 200,
  vit_b12_ug: 2.5,
  calcium_mg: 800,
  iron_mg: 14,
  magnesium_mg: 375,
  phosphorus_mg: 700,
  potassium_mg: 2000,
  zinc_mg: 10,
  copper_mg: 1,
  manganese_mg: 2,
  selenium_ug: 55,
  iodine_ug: 150,
  chromium_ug: 40,
  molybdenum_ug: 50,
  fluoride_mg: 3.5,
};

/** Cobertura VRN de unos totales (cliente). Devuelve el mismo shape que el backend. */
export function coverageVRN(totals: Record<string, ResultValue>): CoverageMap {
  const amounts = usableAmounts(totals);
  const out: CoverageMap = {};
  for (const [id, ref] of Object.entries(VRN)) {
    const unit = NUTRIENTS_BY_ID[id]?.unit ?? '';
    const intake = amounts[id];
    out[id] = {
      nutrient_id: id,
      intake_amount: intake ?? null,
      reference_amount: ref,
      unit,
      coverage_pct: intake === undefined ? null : Math.round((intake / ref) * 1000) / 10,
      status: intake === undefined ? 'not_determined' : 'measured',
      reference_kind: 'vrn',
      note: null,
    };
  }
  return out;
}
