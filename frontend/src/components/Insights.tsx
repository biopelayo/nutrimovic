import { useCoverage } from '../hooks/useCoverage';
import { macroSplit } from '../lib/nutrition';
import { NUTRIENTS_BY_ID, NUTRIENT_ORDER } from '../data/nutrients';
import { formatNumber } from '../lib/format';
import { Spinner, ErrorBanner } from './ui';
import type { ResultValue } from '../types';

/** Reparto de la energía por macronutriente (barra apilada P/G/HC). */
export function MacroSplitCard({ totals }: { totals: Record<string, ResultValue> }) {
  const split = macroSplit(totals);
  if (!split) {
    return (
      <div className="card p-4">
        <h3 className="mb-1 text-sm font-semibold text-ink">Reparto de energía</h3>
        <p className="text-sm text-ink-soft">Añade alimentos para ver el reparto de macronutrientes.</p>
      </div>
    );
  }
  const segs = [
    { label: 'Proteína', pct: split.proteinPct, cls: 'bg-group-protein' },
    { label: 'Grasa', pct: split.fatPct, cls: 'bg-group-fat' },
    { label: 'Hidratos', pct: split.carbsPct, cls: 'bg-group-starchy' },
    ...(split.alcoholPct > 0 ? [{ label: 'Alcohol', pct: split.alcoholPct, cls: 'bg-group-legume' }] : []),
  ];
  return (
    <div className="card p-4">
      <div className="mb-2 flex items-baseline justify-between">
        <h3 className="text-sm font-semibold text-ink">Reparto de energía</h3>
        <span className="text-sm text-ink-soft">{formatNumber(split.totalKcal)} kcal</span>
      </div>
      <div className="mb-3 flex h-3 overflow-hidden rounded-full">
        {segs.map((s) => (
          <div key={s.label} className={s.cls} style={{ width: `${s.pct}%` }} title={`${s.label} ${s.pct}%`} />
        ))}
      </div>
      <ul className="grid grid-cols-2 gap-x-4 gap-y-1 text-sm sm:grid-cols-4">
        {segs.map((s) => (
          <li key={s.label} className="flex items-center gap-1.5">
            <span className={`h-2.5 w-2.5 rounded-full ${s.cls}`} aria-hidden />
            <span className="text-ink-soft">{s.label}</span>
            <span className="ml-auto tabular-nums font-medium text-ink">{formatNumber(s.pct)}%</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

/** Cobertura frente al VRN (Reglamento UE 1169/2011) con barras por nutriente. */
export function CoveragePanel({ totals }: { totals: Record<string, ResultValue> }) {
  const { result, loading, error } = useCoverage(totals, null, true);

  const entries = result
    ? Object.values(result)
        .filter((c) => c.coverage_pct !== null)
        .sort((a, b) => (NUTRIENT_ORDER[a.nutrient_id] ?? 999) - (NUTRIENT_ORDER[b.nutrient_id] ?? 999))
    : [];

  return (
    <div className="card p-4">
      <div className="mb-3 flex items-baseline justify-between">
        <h3 className="text-sm font-semibold text-ink">Cobertura del VRN</h3>
        <span className="text-xs text-ink-muted">Reglamento UE 1169/2011</span>
      </div>
      {loading && <Spinner label="Calculando cobertura…" />}
      {error && <ErrorBanner message={error} />}
      {!loading && !error && entries.length === 0 && (
        <p className="text-sm text-ink-soft">
          Añade alimentos con vitaminas o minerales para ver la cobertura de referencia.
        </p>
      )}
      <ul className="space-y-2.5">
        {entries.map((c) => {
          const pct = c.coverage_pct ?? 0;
          const width = Math.min(pct, 100);
          const name = NUTRIENTS_BY_ID[c.nutrient_id]?.name_es ?? c.nutrient_id;
          const full = pct >= 100;
          return (
            <li key={c.nutrient_id}>
              <div className="mb-1 flex items-center justify-between text-sm">
                <span className="text-ink">{name}</span>
                <span className="tabular-nums text-ink-soft">{formatNumber(pct)}%</span>
              </div>
              <div className="h-2 w-full overflow-hidden rounded-full bg-slate-100">
                <div
                  className={`h-full rounded-full ${full ? 'bg-botanical-dark' : 'bg-botanical'}`}
                  style={{ width: `${width}%` }}
                />
              </div>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
