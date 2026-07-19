// Cálculo clínico en cliente (espejo de backend/app/clinical). Fórmulas estándar
// verificables: IMC (OMS), Mifflin-St Jeor, TDEE, objetivos y reparto de macros.

export type Sex = 'male' | 'female';
export type Goal = 'lose' | 'maintain' | 'gain';
export type ActivityLevel = 'sedentary' | 'light' | 'moderate' | 'active' | 'very_active';

export const PAL: Record<ActivityLevel, number> = {
  sedentary: 1.2,
  light: 1.375,
  moderate: 1.55,
  active: 1.725,
  very_active: 1.9,
};

export const ACTIVITY_LABEL: Record<ActivityLevel, string> = {
  sedentary: 'Sedentario',
  light: 'Actividad ligera',
  moderate: 'Actividad moderada',
  active: 'Activo',
  very_active: 'Muy activo',
};

export const GOAL_LABEL: Record<Goal, string> = {
  lose: 'Perder peso',
  maintain: 'Mantener',
  gain: 'Ganar peso',
};

function round(n: number, d = 1): number {
  const f = 10 ** d;
  return Math.round(n * f) / f;
}

export function bmi(weightKg: number, heightCm: number): number | null {
  if (weightKg <= 0 || heightCm <= 0) return null;
  const m = heightCm / 100;
  return round(weightKg / (m * m), 1);
}

export interface BmiCat {
  label: string;
  level: 'low' | 'ok' | 'warn' | 'bad';
}
export function bmiCategory(value: number | null): BmiCat | null {
  if (value === null) return null;
  if (value < 18.5) return { label: 'Bajo peso', level: 'warn' };
  if (value < 25) return { label: 'Normopeso', level: 'ok' };
  if (value < 30) return { label: 'Sobrepeso', level: 'warn' };
  if (value < 35) return { label: 'Obesidad grado I', level: 'bad' };
  if (value < 40) return { label: 'Obesidad grado II', level: 'bad' };
  return { label: 'Obesidad grado III', level: 'bad' };
}

/** Rango de peso saludable por IMC 18,5–24,9. */
export function idealWeightRange(heightCm: number): [number, number] | null {
  if (heightCm <= 0) return null;
  const m = heightCm / 100;
  return [round(18.5 * m * m, 1), round(24.9 * m * m, 1)];
}

/** Índice cintura/cadera + riesgo por sexo (cortes OMS). */
export function waistHipRatio(waist: number, hip: number, sex: Sex): { ratio: number; risk: string } | null {
  if (waist <= 0 || hip <= 0) return null;
  const ratio = round(waist / hip, 2);
  const high = sex === 'male' ? 0.9 : 0.85;
  return { ratio, risk: ratio >= high ? 'Riesgo elevado' : 'Riesgo bajo' };
}

export function bmrMifflin(sex: Sex, weightKg: number, heightCm: number, ageYears: number): number {
  const base = 10 * weightKg + 6.25 * heightCm - 5 * ageYears;
  return round(base + (sex === 'male' ? 5 : -161), 0);
}

export function tdee(bmr: number, activity: ActivityLevel): number {
  return round(bmr * PAL[activity], 0);
}

export interface EnergyTargets {
  bmr: number;
  tdee: number;
  target: number;
  floored: boolean; // se aplicó el suelo de seguridad
}
export function energyTarget(
  sex: Sex,
  weightKg: number,
  heightCm: number,
  ageYears: number,
  activity: ActivityLevel,
  goal: Goal,
  deficit = 500,
): EnergyTargets {
  const bmr = bmrMifflin(sex, weightKg, heightCm, ageYears);
  const t = tdee(bmr, activity);
  let target = goal === 'lose' ? t - deficit : goal === 'gain' ? t + deficit : t;
  const floor = sex === 'male' ? 1500 : 1200;
  let floored = false;
  if (target < floor) {
    target = floor;
    floored = true;
  }
  return { bmr, tdee: t, target: round(target, 0), floored };
}

export interface MacroTargets {
  proteinG: number;
  fatG: number;
  carbsG: number;
  proteinPct: number;
  fatPct: number;
  carbsPct: number;
}
export function macroTargets(kcal: number, proteinPerKg: number, weightKg: number, fatPct = 30): MacroTargets {
  const proteinG = round(proteinPerKg * weightKg, 1);
  const proteinKcal = proteinG * 4;
  let fatKcal = (kcal * fatPct) / 100;
  let carbsKcal = kcal - proteinKcal - fatKcal;
  if (carbsKcal < 0) {
    fatKcal = Math.max(0, kcal - proteinKcal);
    carbsKcal = 0;
  }
  return {
    proteinG,
    fatG: round(fatKcal / 9, 1),
    carbsG: round(carbsKcal / 4, 1),
    proteinPct: round((proteinKcal / kcal) * 100, 0),
    fatPct: round((fatKcal / kcal) * 100, 0),
    carbsPct: round((carbsKcal / kcal) * 100, 0),
  };
}
