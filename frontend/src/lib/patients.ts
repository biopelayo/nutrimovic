// Persistencia local de pacientes (localStorage). Permite consulta general (sin
// paciente) o consulta por paciente con su histórico de antropometría y su dieta.
import type { Sex, Goal, ActivityLevel } from './clinical';

export interface AnthroEntry {
  date: string; // ISO
  weightKg: number;
  waistCm?: number;
  hipCm?: number;
}

export interface Patient {
  id: string;
  name: string;
  sex: Sex;
  ageYears: number;
  heightCm: number;
  activity: ActivityLevel;
  goal: Goal;
  proteinPerKg: number;
  fatPct: number;
  history: AnthroEntry[]; // seguimiento entre visitas (más reciente al final)
  dietGrams?: Record<string, number>; // hoja de dieta asignada
  dietSavedAt?: string;
  notes?: string; // notas de consulta (evolución, indicaciones)
  recall24h?: Record<string, string>; // recordatorio de 24 h por comida
  updatedAt: string;
}

const KEY = 'nutrimovic_patients';

export function loadPatients(): Patient[] {
  try {
    const raw = localStorage.getItem(KEY);
    return raw ? (JSON.parse(raw) as Patient[]) : [];
  } catch {
    return [];
  }
}

export function savePatients(list: Patient[]): void {
  localStorage.setItem(KEY, JSON.stringify(list));
}

export function upsertPatient(p: Patient): Patient[] {
  const list = loadPatients();
  const i = list.findIndex((x) => x.id === p.id);
  const next = { ...p, updatedAt: new Date().toISOString() };
  if (i >= 0) list[i] = next;
  else list.push(next);
  savePatients(list);
  return list;
}

export function deletePatient(id: string): Patient[] {
  const list = loadPatients().filter((p) => p.id !== id);
  savePatients(list);
  return list;
}

export function newPatientId(): string {
  return `p_${Date.now().toString(36)}_${Math.floor(Math.random() * 1e6).toString(36)}`;
}

export function emptyPatient(): Patient {
  return {
    id: newPatientId(),
    name: '',
    sex: 'female',
    ageYears: 40,
    heightCm: 165,
    activity: 'moderate',
    goal: 'maintain',
    proteinPerKg: 1.2,
    fatPct: 30,
    history: [],
    updatedAt: new Date().toISOString(),
  };
}
