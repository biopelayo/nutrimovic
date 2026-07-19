import { useMemo, useState } from 'react';
import { NUTRIENTS, NUTRIENTS_BY_ID } from '../data/nutrients';
import { GROUP_BY_ID } from '../data/foodGroups';
import { scaleFood, MICRO_NUTRIENT_IDS } from '../lib/nutrition';
import { formatNumber } from '../lib/format';
import { MEALS } from '../lib/meals';
import type { MealId } from '../lib/meals';
import { FoodThumb } from './FoodThumb';
import type { Food, ResultValue } from '../types';

export interface SheetRow {
  rowId: string;
  food: Food;
  grams: number;
  meal: MealId;
}

interface Props {
  rows: SheetRow[];
  columns: string[];
  totals: Record<string, ResultValue>;
  onGramsChange: (rowId: string, grams: number) => void;
  onMealChange: (rowId: string, meal: MealId) => void;
  onRemove: (rowId: string) => void;
  onColumnsChange: (columns: string[]) => void;
}

function cell(value: ResultValue | undefined) {
  if (!value || value.status === 'not_determined') return <span className="text-ink-muted">N/D</span>;
  if (value.status === 'trace') return <span className="text-ink-muted">trazas</span>;
  return <span>{formatNumber(value.amount ?? 0)}</span>;
}

const LETTERS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
function colLetter(i: number): string {
  let s = '';
  let n = i;
  do {
    s = LETTERS[n % 26] + s;
    n = Math.floor(n / 26) - 1;
  } while (n >= 0);
  return s;
}

export function NutritionSheet({
  rows,
  columns,
  totals,
  onGramsChange,
  onMealChange,
  onRemove,
  onColumnsChange,
}: Props) {
  const [pickerOpen, setPickerOpen] = useState(false);

  const scaledRows = useMemo(
    () => rows.map((r) => ({ ...r, scaled: scaleFood(r.food, r.grams) })),
    [rows],
  );
  const totalGrams = rows.reduce((s, r) => s + (Number.isFinite(r.grams) ? r.grams : 0), 0);

  function toggleColumn(id: string) {
    onColumnsChange(columns.includes(id) ? columns.filter((c) => c !== id) : [...columns, id]);
  }

  return (
    <div className="card overflow-hidden">
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-line px-4 py-3">
        <div>
          <h2 className="font-display text-lg font-semibold text-ink">Hoja de dieta</h2>
          <p className="text-xs text-ink-soft">
            {rows.length} alimentos · {formatNumber(totalGrams)} g · escribe los gramos y se recalcula al instante
          </p>
        </div>
        <div className="relative">
          <button className="btn-ghost text-sm" onClick={() => setPickerOpen((o) => !o)}>
            Columnas · {columns.length}
          </button>
          {pickerOpen && (
            <div className="absolute right-0 z-50 mt-1 max-h-96 w-72 overflow-y-auto rounded-card border border-line bg-paper p-2 shadow-panel">
              <p className="px-1 pb-1 text-[11px] font-semibold uppercase text-ink-soft">Macronutrientes</p>
              {NUTRIENTS.filter((n) => n.category === 'energy' || n.category === 'macro').map((n) => (
                <ColumnToggle key={n.id} id={n.id} active={columns.includes(n.id)} onToggle={toggleColumn} />
              ))}
              <p className="px-1 pb-1 pt-2 text-[11px] font-semibold uppercase text-ink-soft">Micronutrientes</p>
              {MICRO_NUTRIENT_IDS.map((id) => (
                <ColumnToggle key={id} id={id} active={columns.includes(id)} onToggle={toggleColumn} />
              ))}
            </div>
          )}
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="sheet">
          <thead>
            <tr className="colletter">
              <th className="rownum" />
              {Array.from({ length: 4 + columns.length }, (_, i) => (
                <th key={i}>{colLetter(i)}</th>
              ))}
            </tr>
            <tr>
              <th className="rownum" />
              <th className="col-sticky text-left">Alimento</th>
              <th className="text-right">Gramos</th>
              <th className="text-left">Comida</th>
              {columns.map((id) => {
                const meta = NUTRIENTS_BY_ID[id];
                return (
                  <th key={id} className="text-right">
                    <div>{meta?.name_es ?? id}</div>
                    <div className="font-normal normal-case text-ink-muted">{meta?.unit}</div>
                  </th>
                );
              })}
              <th aria-label="Acciones" />
            </tr>
          </thead>
          <tbody>
            {scaledRows.length === 0 && (
              <tr>
                <td colSpan={columns.length + 5} className="col-sticky">
                  <div className="px-2 py-12 text-center text-sm text-ink-soft">
                    La hoja está vacía. Marca alimentos en el panel de la izquierda para añadirlos.
                  </div>
                </td>
              </tr>
            )}
            {scaledRows.map((r, rowIndex) => {
              const g = GROUP_BY_ID[r.food.group];
              return (
                <tr key={r.rowId}>
                  <td className="rownum">{rowIndex + 1}</td>
                  <td className="col-sticky text-left">
                    <div className="flex items-center gap-2.5">
                      <FoodThumb name={r.food.name_es} group={r.food.group} imageName={r.food.image_name} size={36} />
                      <div className="leading-tight">
                        <div className="flex items-center gap-1.5">
                          <span className="font-medium text-ink">{r.food.name_es}</span>
                          <span
                            className={`chip ${
                              r.food.state === 'cooked' ? 'bg-accent-4 text-accent' : 'bg-brand-4 text-brand-dark'
                            }`}
                          >
                            {r.food.state === 'cooked' ? 'cocido' : 'crudo'}
                          </span>
                        </div>
                        <div className="text-[11px] text-ink-muted">
                          {g?.label}
                          {r.food.subgroup ? ` · ${r.food.subgroup}` : ''}
                        </div>
                      </div>
                    </div>
                  </td>
                  <td className="text-right">
                    <input
                      type="number"
                      min={0}
                      step={5}
                      className="grams-input"
                      value={Number.isFinite(r.grams) ? r.grams : ''}
                      onChange={(e) => onGramsChange(r.rowId, parseFloat(e.target.value))}
                      aria-label={`Gramos de ${r.food.name_es}`}
                    />
                  </td>
                  <td className="text-left">
                    <select
                      className="rounded-lg border border-line bg-paper px-2 py-1.5 text-[13px] text-ink outline-none focus:border-brand focus:ring-4 focus:ring-brand/10"
                      value={r.meal}
                      onChange={(e) => onMealChange(r.rowId, e.target.value as MealId)}
                      aria-label={`Comida de ${r.food.name_es}`}
                    >
                      {MEALS.map((m) => (
                        <option key={m.id} value={m.id}>
                          {m.label}
                        </option>
                      ))}
                    </select>
                  </td>
                  {columns.map((id) => (
                    <td key={id} className="cell-num">
                      {cell(r.scaled[id])}
                    </td>
                  ))}
                  <td className="text-center">
                    <button
                      className="text-ink-muted transition hover:text-accent"
                      onClick={() => onRemove(r.rowId)}
                      title="Quitar de la hoja"
                      aria-label={`Quitar ${r.food.name_es}`}
                    >
                      ✕
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
          {scaledRows.length > 0 && (
            <tfoot>
              <tr className="font-semibold">
                <td className="rownum" />
                <td className="col-sticky text-left">
                  <span className="text-ink">Total del día</span>
                </td>
                <td className="cell-num text-ink">{formatNumber(totalGrams)}</td>
                <td />
                {columns.map((id) => (
                  <td key={id} className="cell-num text-ink">
                    {cell(totals[id])}
                  </td>
                ))}
                <td />
              </tr>
            </tfoot>
          )}
        </table>
      </div>
    </div>
  );
}

function ColumnToggle({
  id,
  active,
  onToggle,
}: {
  id: string;
  active: boolean;
  onToggle: (id: string) => void;
}) {
  const meta = NUTRIENTS_BY_ID[id];
  return (
    <label className="flex cursor-pointer items-center gap-2 rounded-lg px-1.5 py-1 text-sm hover:bg-surface">
      <input type="checkbox" checked={active} onChange={() => onToggle(id)} className="accent-brand" />
      <span className="text-ink">{meta?.name_es ?? id}</span>
      <span className="ml-auto text-xs text-ink-muted">{meta?.unit}</span>
    </label>
  );
}
