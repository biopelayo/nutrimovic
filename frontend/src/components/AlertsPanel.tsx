import { macroSplit } from '../lib/nutrition';
import { formatNumber } from '../lib/format';
import { allergenLabel } from '../lib/allergens';
import type { Food, ResultValue } from '../types';

type Level = 'ok' | 'warn' | 'bad' | 'nd';

const STYLE: Record<Level, { dot: string; text: string; label: string }> = {
  ok: { dot: 'bg-emerald-500', text: 'text-emerald-700', label: 'En objetivo' },
  warn: { dot: 'bg-amber-400', text: 'text-amber-700', label: 'Atención' },
  bad: { dot: 'bg-red-500', text: 'text-red-700', label: 'Fuera de objetivo' },
  nd: { dot: 'bg-ink-muted', text: 'text-ink-muted', label: 'Sin dato' },
};

interface Rule {
  id: string;
  label: string;
  kind: 'max' | 'min';
  limit: number;
  warnAt: number; // fracción del límite donde empieza el ámbar
  unit: string;
  note: string;
}

// Umbrales diarios de referencia para un adulto (orientativos, OMS / Reglamento UE).
const RULES: Rule[] = [
  { id: 'sodium_mg', label: 'Sodio', kind: 'max', limit: 2000, warnAt: 0.8, unit: 'mg', note: 'OMS: < 2 g/día (≈ 5 g de sal).' },
  { id: 'sugars_g', label: 'Azúcares', kind: 'max', limit: 90, warnAt: 0.8, unit: 'g', note: 'Referencia de etiquetado UE (azúcares totales).' },
  { id: 'fat_saturated_g', label: 'Grasas saturadas', kind: 'max', limit: 20, warnAt: 0.8, unit: 'g', note: 'Referencia de etiquetado UE.' },
  { id: 'fiber_g', label: 'Fibra', kind: 'min', limit: 25, warnAt: 0.8, unit: 'g', note: 'EFSA: ≥ 25 g/día en adultos.' },
];

function evaluate(rule: Rule, value: ResultValue | undefined): { level: Level; amount: number | null } {
  if (!value || value.status === 'not_determined' || value.amount === null) return { level: 'nd', amount: null };
  const a = value.amount;
  if (rule.kind === 'max') {
    if (a > rule.limit) return { level: 'bad', amount: a };
    if (a >= rule.limit * rule.warnAt) return { level: 'warn', amount: a };
    return { level: 'ok', amount: a };
  }
  // min
  if (a >= rule.limit) return { level: 'ok', amount: a };
  if (a >= rule.limit * rule.warnAt) return { level: 'warn', amount: a };
  return { level: 'bad', amount: a };
}

function macroLevel(pct: number, lo: number, hi: number): Level {
  if (pct >= lo && pct <= hi) return 'ok';
  if (pct >= lo - 5 && pct <= hi + 5) return 'warn';
  return 'bad';
}

export function AlertsPanel({
  totals,
  foods = [],
}: {
  totals: Record<string, ResultValue>;
  foods?: Food[];
}) {
  const hasData = Object.keys(totals).length > 0;
  const split = macroSplit(totals);

  // Alérgenos presentes en la dieta (unión de los de cada alimento en uso).
  const allergens = Array.from(new Set(foods.flatMap((f) => f.allergens ?? []))).sort();

  const macroRows = split
    ? [
        { label: 'Proteína', pct: split.proteinPct, level: macroLevel(split.proteinPct, 10, 35), rango: '10–35 %' },
        { label: 'Grasa', pct: split.fatPct, level: macroLevel(split.fatPct, 20, 35), rango: '20–35 %' },
        { label: 'Hidratos', pct: split.carbsPct, level: macroLevel(split.carbsPct, 45, 60), rango: '45–60 %' },
      ]
    : [];

  return (
    <div className="mx-auto max-w-4xl space-y-4">
      <div>
        <h2 className="font-display text-2xl font-semibold text-ink">Alertas y semáforo nutricional</h2>
        <p className="text-sm text-ink-soft">Sobre el total de la hoja de dieta. Umbrales orientativos para un adulto.</p>
      </div>

      {!hasData && (
        <div className="card p-8 text-center text-ink-soft">
          Añade alimentos en la pestaña <span className="font-medium text-ink">Plantilla</span> para evaluar la dieta.
        </div>
      )}

      {hasData && (
        <>
          <div className="card p-4">
            <h3 className="mb-3 font-display text-lg font-semibold text-ink">Reparto de macronutrientes</h3>
            <ul className="space-y-2">
              {macroRows.map((m) => {
                const s = STYLE[m.level];
                return (
                  <li key={m.label} className="flex items-center gap-3">
                    <span className={`h-2.5 w-2.5 rounded-full ${s.dot}`} aria-hidden />
                    <span className="w-24 text-ink">{m.label}</span>
                    <span className="tabular-nums font-medium text-ink">{formatNumber(m.pct)}%</span>
                    <span className="text-xs text-ink-muted">objetivo {m.rango}</span>
                    <span className={`ml-auto text-sm font-medium ${s.text}`}>{s.label}</span>
                  </li>
                );
              })}
            </ul>
          </div>

          <div className="card divide-y divide-line">
            {RULES.map((rule) => {
              const { level, amount } = evaluate(rule, totals[rule.id]);
              const s = STYLE[level];
              return (
                <div key={rule.id} className="flex items-center gap-3 p-4">
                  <span className={`h-2.5 w-2.5 rounded-full ${s.dot}`} aria-hidden />
                  <div className="flex-1">
                    <div className="flex items-baseline gap-2">
                      <span className="font-medium text-ink">{rule.label}</span>
                      <span className="text-xs text-ink-muted">
                        {rule.kind === 'max' ? 'máx.' : 'mín.'} {formatNumber(rule.limit)} {rule.unit}
                      </span>
                    </div>
                    <p className="text-xs text-ink-muted">{rule.note}</p>
                  </div>
                  <span className="tabular-nums font-medium text-ink">
                    {amount === null ? 'N/D' : `${formatNumber(amount)} ${rule.unit}`}
                  </span>
                  <span className={`w-36 text-right text-sm font-medium ${s.text}`}>{s.label}</span>
                </div>
              );
            })}
          </div>

          <div className="card p-4">
            <h3 className="mb-2 font-display text-lg font-semibold text-ink">Alérgenos en la dieta</h3>
            {allergens.length === 0 ? (
              <p className="text-sm text-ink-soft">No se han detectado alérgenos declarables en los alimentos en uso.</p>
            ) : (
              <div className="flex flex-wrap gap-2">
                {allergens.map((a) => (
                  <span key={a} className="chip bg-accent-4 px-2 py-1 text-[13px] text-accent">
                    {allergenLabel(a)}
                  </span>
                ))}
              </div>
            )}
            <p className="mt-2 text-xs text-ink-muted">
              Orientativo por composición del alimento; verifica siempre el etiquetado real del producto.
            </p>
          </div>
        </>
      )}
    </div>
  );
}
