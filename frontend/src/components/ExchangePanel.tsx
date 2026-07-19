import { exchangesByMacro } from '../lib/exchanges';
import { formatNumber } from '../lib/format';
import { FoodThumb } from './FoodThumb';
import type { SheetRow } from './NutritionSheet';

/**
 * Tabla de intercambios: por cada alimento, cuántos intercambios de HC, proteína
 * y grasa aporta su gramaje (1 intercambio = 10 g del macronutriente).
 */
export function ExchangePanel({ rows }: { rows: SheetRow[] }) {
  const totals = { hc: 0, protein: 0, fat: 0 };
  for (const r of rows) {
    const m = exchangesByMacro(r.food, r.grams);
    totals.hc += m.hc ?? 0;
    totals.protein += m.protein ?? 0;
    totals.fat += m.fat ?? 0;
  }

  return (
    <div className="card overflow-hidden">
      <div className="border-b border-line px-4 py-2.5">
        <h3 className="text-lg font-bold text-ink">Intercambios de alimentos</h3>
        <p className="text-[13px] text-ink-soft">
          Intercambios que aporta cada gramaje · 1 intercambio = 10 g del macronutriente
        </p>
      </div>
      {rows.length === 0 ? (
        <p className="px-4 py-6 text-center text-sm text-ink-soft">Añade alimentos para ver sus intercambios.</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="sheet">
            <thead>
              <tr>
                <th className="col-sticky text-left">Alimento</th>
                <th className="text-right">Gramos</th>
                <th className="text-right">Int. hidratos</th>
                <th className="text-right">Int. proteína</th>
                <th className="text-right">Int. grasa</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => {
                const m = exchangesByMacro(r.food, r.grams);
                const c = (x: number | null) =>
                  x === null ? <span className="text-ink-muted">N/D</span> : formatNumber(x);
                return (
                  <tr key={r.rowId}>
                    <td className="col-sticky text-left">
                      <div className="flex items-center gap-2.5">
                        <FoodThumb name={r.food.name_es} group={r.food.group} imageName={r.food.image_name} size={30} />
                        <span className="text-ink">{r.food.name_es}</span>
                      </div>
                    </td>
                    <td className="cell-num text-ink-soft">{formatNumber(r.grams || 0)}</td>
                    <td className="cell-num font-semibold text-brand-dark">{c(m.hc)}</td>
                    <td className="cell-num font-semibold text-brand-dark">{c(m.protein)}</td>
                    <td className="cell-num font-semibold text-brand-dark">{c(m.fat)}</td>
                  </tr>
                );
              })}
            </tbody>
            <tfoot>
              <tr className="font-semibold">
                <td className="col-sticky text-left text-ink">Total intercambios</td>
                <td />
                <td className="cell-num text-ink">{formatNumber(totals.hc)}</td>
                <td className="cell-num text-ink">{formatNumber(totals.protein)}</td>
                <td className="cell-num text-ink">{formatNumber(totals.fat)}</td>
              </tr>
            </tfoot>
          </table>
        </div>
      )}
    </div>
  );
}
