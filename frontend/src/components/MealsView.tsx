import { useMemo } from 'react';
import { MEALS } from '../lib/meals';
import { scaleFood, sumRows } from '../lib/nutrition';
import { formatNumber } from '../lib/format';
import { FoodThumb } from './FoodThumb';
import type { SheetRow } from './NutritionSheet';
import type { ResultValue } from '../types';

function kcalOf(totals: Record<string, ResultValue>): number {
  const v = totals['energy_kcal'];
  return v && v.status !== 'not_determined' ? v.amount ?? 0 : 0;
}
function g(totals: Record<string, ResultValue>, id: string): number {
  const v = totals[id];
  return v && v.status !== 'not_determined' ? v.amount ?? 0 : 0;
}

export function MealsView({ rows }: { rows: SheetRow[] }) {
  const scaled = useMemo(() => rows.map((r) => ({ r, s: scaleFood(r.food, r.grams) })), [rows]);
  const grandTotals = useMemo(() => sumRows(scaled.map((x) => x.s)), [scaled]);
  const grandKcal = kcalOf(grandTotals);

  if (rows.length === 0) {
    return (
      <div className="mx-auto max-w-4xl">
        <div className="card p-8 text-center text-ink-soft">
          Añade alimentos en la pestaña <span className="font-medium text-ink">Plantilla</span> y asígnalos a cada
          comida para ver el reparto del día.
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-4xl space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="font-display text-2xl font-semibold text-ink">Reparto por comidas</h2>
          <p className="text-sm text-ink-soft">
            Total del día: {formatNumber(grandKcal)} kcal · {rows.length} alimentos
          </p>
        </div>
        <button className="btn-primary no-print" onClick={() => window.print()}>
          Guardar PDF
        </button>
      </div>

      {MEALS.map((meal) => {
        const items = scaled.filter((x) => x.r.meal === meal.id);
        if (items.length === 0) return null;
        const mt = sumRows(items.map((x) => x.s));
        const kcal = kcalOf(mt);
        const pct = grandKcal > 0 ? (kcal / grandKcal) * 100 : 0;
        return (
          <div key={meal.id} className="card overflow-hidden">
            <div className="flex items-center justify-between border-b border-line bg-surface/60 px-4 py-2.5">
              <h3 className="flex items-center gap-2 text-lg font-semibold text-ink">
                <span className="h-3 w-3 rounded-sm bg-brand" aria-hidden /> {meal.label}
              </h3>
              <div className="text-sm text-ink-soft">
                <span className="font-semibold text-ink">{formatNumber(kcal)}</span> kcal ·{' '}
                <span className="font-medium">{formatNumber(pct)}%</span>
                <span className="text-ink-muted"> (objetivo {meal.targetPct}%)</span>
              </div>
            </div>
            <table className="sheet">
              <tbody>
                {items.map(({ r, s }) => (
                  <tr key={r.rowId}>
                    <td className="col-sticky text-left">
                      <div className="flex items-center gap-2.5">
                        <FoodThumb name={r.food.name_es} group={r.food.group} imageName={r.food.image_name} size={30} />
                        <span className="text-ink">{r.food.name_es}</span>
                      </div>
                    </td>
                    <td className="cell-num text-ink-soft">{formatNumber(r.grams)} g</td>
                    <td className="cell-num">{formatNumber(kcalOf(s))} kcal</td>
                    <td className="cell-num">{formatNumber(g(s, 'protein_g'))} P</td>
                    <td className="cell-num">{formatNumber(g(s, 'fat_g'))} G</td>
                    <td className="cell-num">{formatNumber(g(s, 'carbs_g'))} HC</td>
                  </tr>
                ))}
              </tbody>
              <tfoot>
                <tr className="font-semibold">
                  <td className="col-sticky text-left text-ink">Subtotal</td>
                  <td />
                  <td className="cell-num text-ink">{formatNumber(kcal)} kcal</td>
                  <td className="cell-num text-ink">{formatNumber(g(mt, 'protein_g'))} P</td>
                  <td className="cell-num text-ink">{formatNumber(g(mt, 'fat_g'))} G</td>
                  <td className="cell-num text-ink">{formatNumber(g(mt, 'carbs_g'))} HC</td>
                </tr>
              </tfoot>
            </table>
          </div>
        );
      })}
    </div>
  );
}
