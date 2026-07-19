import { useMemo, useState } from 'react';
import {
  bmi,
  bmiCategory,
  idealWeightRange,
  waistHipRatio,
  energyTarget,
  macroTargets,
  ACTIVITY_LABEL,
  GOAL_LABEL,
  type ActivityLevel,
  type Goal,
  type Sex,
} from '../lib/clinical';
import {
  loadPatients,
  upsertPatient,
  deletePatient,
  emptyPatient,
  type Patient,
} from '../lib/patients';
import { MEALS } from '../lib/meals';
import { formatNumber } from '../lib/format';
import type { ResultValue } from '../types';

interface Props {
  dietGrams: Record<string, number>;
  dietTotals: Record<string, ResultValue>;
  onLoadDiet: (grams: Record<string, number>) => void;
}

const LEVEL_COLOR: Record<string, string> = {
  ok: 'text-emerald-700',
  warn: 'text-amber-700',
  bad: 'text-red-700',
  low: 'text-amber-700',
};

function num(totals: Record<string, ResultValue>, id: string): number {
  const v = totals[id];
  return v && v.status !== 'not_determined' ? v.amount ?? 0 : 0;
}

function pct(part: number, whole: number): number {
  return whole > 0 ? Math.round((part / whole) * 100) : 0;
}

export function PatientView({ dietGrams, dietTotals, onLoadDiet }: Props) {
  const [patients, setPatients] = useState<Patient[]>(() => loadPatients());
  const [p, setP] = useState<Patient>(() => emptyPatient());
  const [weight, setWeight] = useState<number>(65);
  const [waist, setWaist] = useState<number>(0);
  const [hip, setHip] = useState<number>(0);
  const [saved, setSaved] = useState(false);

  function set<K extends keyof Patient>(k: K, v: Patient[K]) {
    setP((prev) => ({ ...prev, [k]: v }));
    setSaved(false);
  }

  // Cálculos clínicos
  const bmiVal = bmi(weight, p.heightCm);
  const cat = bmiCategory(bmiVal);
  const idealRange = idealWeightRange(p.heightCm);
  const whr = waist > 0 && hip > 0 ? waistHipRatio(waist, hip, p.sex) : null;
  const energy = energyTarget(p.sex, weight, p.heightCm, p.ageYears, p.activity, p.goal);
  const macros = macroTargets(energy.target, p.proteinPerKg, weight, p.fatPct);

  // Comparación de la dieta (hoja de dieta) con los objetivos
  const dietKcal = num(dietTotals, 'energy_kcal');
  const dietProt = num(dietTotals, 'protein_g');
  const dietFat = num(dietTotals, 'fat_g');
  const dietCarb = num(dietTotals, 'carbs_g');
  const dietActive = Object.values(dietGrams).filter((g) => g > 0).length;

  const compareRows = [
    { label: 'Energía', unit: 'kcal', diet: dietKcal, target: energy.target },
    { label: 'Proteína', unit: 'g', diet: dietProt, target: macros.proteinG },
    { label: 'Grasa', unit: 'g', diet: dietFat, target: macros.fatG },
    { label: 'Hidratos', unit: 'g', diet: dietCarb, target: macros.carbsG },
  ];

  const trend = useMemo(() => {
    if (p.history.length < 2) return null;
    const first = p.history[0].weightKg;
    const last = p.history[p.history.length - 1].weightKg;
    return { delta: Math.round((last - first) * 10) / 10, first, last };
  }, [p.history]);

  function selectPatient(id: string) {
    if (id === '__general') {
      setP(emptyPatient());
      setWeight(65);
      return;
    }
    if (id === '__new') {
      setP(emptyPatient());
      setWeight(65);
      return;
    }
    const found = patients.find((x) => x.id === id);
    if (found) {
      setP(found);
      setWeight(found.history[found.history.length - 1]?.weightKg ?? 65);
      if (found.dietGrams) onLoadDiet(found.dietGrams);
    }
  }

  function registerVisit() {
    const entry = { date: new Date().toISOString(), weightKg: weight, waistCm: waist || undefined, hipCm: hip || undefined };
    set('history', [...p.history, entry]);
  }

  function setRecall(meal: string, val: string) {
    setP((prev) => ({ ...prev, recall24h: { ...(prev.recall24h || {}), [meal]: val } }));
    setSaved(false);
  }

  function saveAssignDiet() {
    const toSave: Patient = {
      ...p,
      name: p.name || 'Paciente sin nombre',
      dietGrams: { ...dietGrams },
      dietSavedAt: new Date().toISOString(),
    };
    const list = upsertPatient(toSave);
    setPatients(list);
    setP(toSave);
    setSaved(true);
  }

  function removePatient() {
    if (!patients.find((x) => x.id === p.id)) return;
    const list = deletePatient(p.id);
    setPatients(list);
    setP(emptyPatient());
    setWeight(65);
  }

  return (
    <div className="mx-auto max-w-6xl space-y-4">
      {/* Selector de consulta */}
      <div className="card flex flex-wrap items-center gap-3 p-3">
        <label className="text-sm font-semibold text-ink">Consulta:</label>
        <select
          className="field w-64"
          value={patients.find((x) => x.id === p.id) ? p.id : '__general'}
          onChange={(e) => selectPatient(e.target.value)}
        >
          <option value="__general">Consulta general (sin guardar)</option>
          <optgroup label="Pacientes guardados">
            {patients.map((x) => (
              <option key={x.id} value={x.id}>
                {x.name || 'Sin nombre'}
              </option>
            ))}
          </optgroup>
        </select>
        <button className="btn-ghost text-sm" onClick={() => selectPatient('__new')}>
          + Nuevo paciente
        </button>
        <div className="ml-auto flex items-center gap-2">
          {saved && <span className="text-sm text-emerald-700">Guardado ✓</span>}
          {patients.find((x) => x.id === p.id) && (
            <button className="btn-ghost text-sm text-red-600" onClick={removePatient}>
              Borrar
            </button>
          )}
          <button className="btn-primary text-sm" onClick={saveAssignDiet}>
            Asignar hoja de dieta y guardar
          </button>
        </div>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        {/* Ficha */}
        <section className="card p-4">
          <h3 className="mb-3 text-lg font-bold text-ink">Ficha del paciente</h3>
          <div className="grid grid-cols-2 gap-3">
            <Field label="Nombre" full>
              <input className="field" value={p.name} onChange={(e) => set('name', e.target.value)} />
            </Field>
            <Field label="Sexo">
              <select className="field" value={p.sex} onChange={(e) => set('sex', e.target.value as Sex)}>
                <option value="female">Mujer</option>
                <option value="male">Hombre</option>
              </select>
            </Field>
            <Field label="Edad (años)">
              <input type="number" className="field" value={p.ageYears} onChange={(e) => set('ageYears', +e.target.value)} />
            </Field>
            <Field label="Altura (cm)">
              <input type="number" className="field" value={p.heightCm} onChange={(e) => set('heightCm', +e.target.value)} />
            </Field>
            <Field label="Peso actual (kg)">
              <input type="number" className="field" value={weight} onChange={(e) => setWeight(+e.target.value)} />
            </Field>
            <Field label="Actividad">
              <select className="field" value={p.activity} onChange={(e) => set('activity', e.target.value as ActivityLevel)}>
                {Object.entries(ACTIVITY_LABEL).map(([k, v]) => (
                  <option key={k} value={k}>{v}</option>
                ))}
              </select>
            </Field>
            <Field label="Objetivo">
              <select className="field" value={p.goal} onChange={(e) => set('goal', e.target.value as Goal)}>
                {Object.entries(GOAL_LABEL).map(([k, v]) => (
                  <option key={k} value={k}>{v}</option>
                ))}
              </select>
            </Field>
            <Field label="Proteína (g/kg)">
              <input type="number" step="0.1" className="field" value={p.proteinPerKg} onChange={(e) => set('proteinPerKg', +e.target.value)} />
            </Field>
            <Field label="Grasa (% energía)">
              <input type="number" className="field" value={p.fatPct} onChange={(e) => set('fatPct', +e.target.value)} />
            </Field>
            <Field label="Cintura (cm)">
              <input type="number" className="field" value={waist || ''} onChange={(e) => setWaist(+e.target.value)} />
            </Field>
            <Field label="Cadera (cm)">
              <input type="number" className="field" value={hip || ''} onChange={(e) => setHip(+e.target.value)} />
            </Field>
          </div>
        </section>

        {/* Antropometría */}
        <section className="card p-4">
          <h3 className="mb-3 text-lg font-bold text-ink">Antropometría</h3>
          <dl className="space-y-2">
            <Metric label="IMC">
              <span className="font-semibold">{bmiVal ?? '—'}</span>
              {cat && <span className={`ml-2 text-sm font-medium ${LEVEL_COLOR[cat.level]}`}>{cat.label}</span>}
            </Metric>
            <Metric label="Peso saludable">
              {idealRange ? `${idealRange[0]}–${idealRange[1]} kg` : '—'}
            </Metric>
            <Metric label="Índice cintura/cadera">
              {whr ? (
                <>
                  <span className="font-semibold">{whr.ratio}</span>
                  <span className={`ml-2 text-sm ${whr.risk.includes('elevado') ? 'text-red-700' : 'text-emerald-700'}`}>{whr.risk}</span>
                </>
              ) : (
                <span className="text-ink-muted">introduce cintura y cadera</span>
              )}
            </Metric>
          </dl>

          <h4 className="mb-2 mt-4 text-sm font-semibold text-ink">Seguimiento (tracking)</h4>
          <button className="btn-ghost mb-2 text-sm" onClick={registerVisit}>
            Registrar visita de hoy ({weight} kg)
          </button>
          {p.history.length === 0 ? (
            <p className="text-sm text-ink-muted">Sin visitas registradas.</p>
          ) : (
            <table className="sheet">
              <thead>
                <tr>
                  <th className="text-left">Fecha</th>
                  <th className="text-right">Peso</th>
                  <th className="text-right">Cintura</th>
                </tr>
              </thead>
              <tbody>
                {p.history.map((h, i) => (
                  <tr key={i}>
                    <td>{new Date(h.date).toLocaleDateString('es-ES')}</td>
                    <td className="cell-num">{h.weightKg} kg</td>
                    <td className="cell-num">{h.waistCm ? `${h.waistCm} cm` : '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
          {trend && (
            <p className={`mt-2 text-sm font-medium ${trend.delta < 0 ? 'text-emerald-700' : trend.delta > 0 ? 'text-amber-700' : 'text-ink-soft'}`}>
              Variación: {trend.delta > 0 ? '+' : ''}{trend.delta} kg ({trend.first} → {trend.last} kg)
            </p>
          )}
        </section>

        {/* Objetivos */}
        <section className="card p-4">
          <h3 className="mb-3 text-lg font-bold text-ink">Necesidades y objetivos</h3>
          <dl className="space-y-2">
            <Metric label="Gasto basal (Mifflin-St Jeor)">{formatNumber(energy.bmr)} kcal</Metric>
            <Metric label="Gasto total (con actividad)">{formatNumber(energy.tdee)} kcal</Metric>
            <Metric label="Energía objetivo">
              <span className="font-semibold text-brand-dark">{formatNumber(energy.target)} kcal</span>
              {energy.floored && <span className="ml-2 text-xs text-amber-700">(suelo de seguridad)</span>}
            </Metric>
          </dl>
          <div className="mt-3 grid grid-cols-3 gap-2 text-center">
            {[
              { l: 'Proteína', g: macros.proteinG, pc: macros.proteinPct },
              { l: 'Grasa', g: macros.fatG, pc: macros.fatPct },
              { l: 'Hidratos', g: macros.carbsG, pc: macros.carbsPct },
            ].map((m) => (
              <div key={m.l} className="rounded-sm border border-line bg-surface p-2">
                <div className="text-xs text-ink-soft">{m.l}</div>
                <div className="text-lg font-bold text-ink">{m.g} g</div>
                <div className="text-xs text-ink-muted">{m.pc}%</div>
              </div>
            ))}
          </div>
        </section>

        {/* Comparación con la dieta */}
        <section className="card p-4">
          <h3 className="mb-1 text-lg font-bold text-ink">Dieta vs objetivos</h3>
          <p className="mb-3 text-xs text-ink-soft">
            Compara la hoja de dieta actual ({dietActive} alimentos en uso) con los objetivos del paciente.
          </p>
          {dietActive === 0 ? (
            <p className="text-sm text-ink-muted">
              Pon gramos en la pestaña <span className="font-medium text-ink">Hoja de dieta</span> para comparar.
            </p>
          ) : (
            <ul className="space-y-3">
              {compareRows.map((r) => {
                const p2 = pct(r.diet, r.target);
                const color = p2 >= 90 && p2 <= 110 ? 'bg-emerald-500' : p2 < 90 ? 'bg-amber-400' : 'bg-red-500';
                return (
                  <li key={r.label}>
                    <div className="mb-1 flex justify-between text-sm">
                      <span className="text-ink">{r.label}</span>
                      <span className="text-ink-soft">
                        {formatNumber(r.diet)} / {formatNumber(r.target)} {r.unit} · <span className="font-medium">{p2}%</span>
                      </span>
                    </div>
                    <div className="h-2 w-full overflow-hidden rounded-full bg-slate-100">
                      <div className={`h-full ${color}`} style={{ width: `${Math.min(p2, 100)}%` }} />
                    </div>
                  </li>
                );
              })}
            </ul>
          )}
        </section>
      </div>

      {/* Registro de consulta */}
      <div className="grid gap-4 lg:grid-cols-2">
        <section className="card p-4">
          <h3 className="mb-1 text-lg font-bold text-ink">Recordatorio de 24 horas</h3>
          <p className="mb-3 text-xs text-ink-soft">Lo que el paciente comió el día anterior, por comida.</p>
          <div className="space-y-2">
            {MEALS.map((m) => (
              <label key={m.id} className="block">
                <span className="mb-1 block text-xs font-medium text-ink-soft">{m.label}</span>
                <textarea
                  className="field min-h-[46px] resize-y"
                  value={p.recall24h?.[m.id] ?? ''}
                  onChange={(e) => setRecall(m.id, e.target.value)}
                  placeholder="Alimentos y cantidades aproximadas…"
                />
              </label>
            ))}
          </div>
        </section>

        <section className="card p-4">
          <h3 className="mb-1 text-lg font-bold text-ink">Notas de consulta</h3>
          <p className="mb-3 text-xs text-ink-soft">Evolución, indicaciones, adherencia, objetivos acordados.</p>
          <textarea
            className="field min-h-[360px] resize-y"
            value={p.notes ?? ''}
            onChange={(e) => set('notes', e.target.value)}
            placeholder="Anotaciones de la visita…"
          />
        </section>
      </div>

      <p className="px-1 text-center text-xs text-ink-muted">
        Apoya la decisión clínica; no sustituye al criterio del profesional sanitario. Los datos se guardan solo en este
        navegador.
      </p>
    </div>
  );
}

function Field({ label, children, full }: { label: string; children: React.ReactNode; full?: boolean }) {
  return (
    <label className={`block ${full ? 'col-span-2' : ''}`}>
      <span className="mb-1 block text-xs font-medium text-ink-soft">{label}</span>
      {children}
    </label>
  );
}

function Metric({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex items-center justify-between border-b border-line py-1.5">
      <dt className="text-sm text-ink-soft">{label}</dt>
      <dd className="text-ink">{children}</dd>
    </div>
  );
}
