import { useMemo, useState } from 'react';
import { NUTRIENTS, NUTRIENTS_BY_ID } from '../data/nutrients';
import { FOOD_GROUPS, GROUP_BY_ID } from '../data/foodGroups';
import { scaleFood, sumRows, MICRO_NUTRIENT_IDS } from '../lib/nutrition';
import { exchangesByMacro } from '../lib/exchanges';
import { allergenLabel } from '../lib/allergens';
import { formatNumber } from '../lib/format';
import { FoodThumb } from './FoodThumb';
import { SearchIcon } from './Icons';
import { Spinner, ErrorBanner } from './ui';
import type { Food, ResultValue } from '../types';

interface Props {
  foods: Food[];
  gramsById: Record<string, number>;
  onGramsChange: (foodId: string, grams: number) => void;
  columns: string[];
  onColumnsChange: (cols: string[]) => void;
  loading: boolean;
  error: string | null;
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

function cell(v: ResultValue | undefined) {
  if (!v || v.status === 'not_determined') return <span className="text-ink-muted">N/D</span>;
  if (v.status === 'trace') return <span className="text-ink-muted">tr</span>;
  return <span>{formatNumber(v.amount ?? 0)}</span>;
}

export function DietSheet({ foods, gramsById, onGramsChange, columns, onColumnsChange, loading, error }: Props) {
  const [q, setQ] = useState('');
  const [pickerOpen, setPickerOpen] = useState(false);

  const qn = q.trim().toLowerCase();
  // Con miles de alimentos no se renderizan todos: sin búsqueda se muestran los
  // que están en uso; al buscar, las coincidencias (acotadas) + los en uso.
  const CAP = 300;
  const shown = useMemo(() => {
    const active = foods.filter((f) => (gramsById[f.id] ?? 0) > 0);
    if (!qn) return active;
    const matches = foods.filter((f) => f.name_es.toLowerCase().includes(qn)).slice(0, CAP);
    const ids = new Set(matches.map((f) => f.id));
    return [...matches, ...active.filter((f) => !ids.has(f.id))];
  }, [foods, qn, gramsById]);

  // Total de la dieta: solo los alimentos con gramaje > 0.
  const active = foods.filter((f) => (gramsById[f.id] ?? 0) > 0);
  const totals = useMemo(
    () => sumRows(active.map((f) => scaleFood(f, gramsById[f.id] ?? 0))),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [foods, gramsById],
  );
  const totalKcal = totals['energy_kcal']?.amount ?? 0;

  const exTotals = useMemo(() => {
    let hc = 0,
      protein = 0,
      fat = 0;
    for (const f of active) {
      const m = exchangesByMacro(f, gramsById[f.id] ?? 0);
      hc += m.hc ?? 0;
      protein += m.protein ?? 0;
      fat += m.fat ?? 0;
    }
    const r = (x: number) => Math.round(x * 100) / 100;
    return { hc: r(hc), protein: r(protein), fat: r(fat) };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [foods, gramsById]);

  function toggleColumn(id: string) {
    onColumnsChange(columns.includes(id) ? columns.filter((c) => c !== id) : [...columns, id]);
  }

  // Filas agrupadas por grupo con su número de inicio precomputado (puro, sin
  // efectos en render: evita que la numeración se descuadre).
  const groupsToRender = useMemo(() => {
    const out: { g: (typeof FOOD_GROUPS)[number]; items: Food[]; start: number }[] = [];
    let n = 0;
    for (const g of FOOD_GROUPS) {
      const items = shown.filter((f) => f.group === g.id);
      if (items.length === 0) continue;
      out.push({ g, items, start: n });
      n += items.length;
    }
    return out;
  }, [shown]);

  return (
    <div className="card flex h-full flex-col overflow-hidden">
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-line px-4 py-2.5">
        <div>
          <h2 className="text-lg font-bold text-ink">Hoja de dieta</h2>
          <p className="text-[13px] text-ink-soft">
            <span className="font-semibold text-ink">{formatNumber(foods.length)}</span> alimentos · pon gramos o
            intercambios (se recalculan entre sí) ·{' '}
            <span className="font-semibold text-ink">{active.length}</span> en uso ·{' '}
            <span className="font-semibold text-ink">{formatNumber(totalKcal)}</span> kcal
          </p>
        </div>
        <div className="flex items-center gap-2">
          <div className="relative">
            <span className="pointer-events-none absolute left-2.5 top-1/2 -translate-y-1/2 text-ink-muted">
              <SearchIcon className="h-4 w-4" />
            </span>
            <input
              className="field w-56 pl-8 text-[14px]"
              placeholder="Filtrar alimento…"
              value={q}
              onChange={(e) => setQ(e.target.value)}
              aria-label="Filtrar alimento"
            />
          </div>
          <div className="relative">
            <button className="btn-ghost text-sm" onClick={() => setPickerOpen((o) => !o)}>
              Columnas · {columns.length}
            </button>
            {pickerOpen && (
              <div className="absolute right-0 z-50 mt-1 max-h-96 w-72 overflow-y-auto rounded-card border border-line bg-paper p-2 shadow-panel">
                <p className="px-1 pb-1 text-[11px] font-semibold uppercase text-ink-soft">Macronutrientes</p>
                {NUTRIENTS.filter((n) => n.category === 'energy' || n.category === 'macro').map((n) => (
                  <label key={n.id} className="flex cursor-pointer items-center gap-2 rounded-sm px-1.5 py-1 text-sm hover:bg-surface">
                    <input type="checkbox" checked={columns.includes(n.id)} onChange={() => toggleColumn(n.id)} className="accent-brand" />
                    <span className="text-ink">{n.name_es}</span>
                    <span className="ml-auto text-xs text-ink-muted">{n.unit}</span>
                  </label>
                ))}
                <p className="px-1 pb-1 pt-2 text-[11px] font-semibold uppercase text-ink-soft">Micronutrientes</p>
                {MICRO_NUTRIENT_IDS.map((id) => {
                  const n = NUTRIENTS_BY_ID[id];
                  return (
                    <label key={id} className="flex cursor-pointer items-center gap-2 rounded-sm px-1.5 py-1 text-sm hover:bg-surface">
                      <input type="checkbox" checked={columns.includes(id)} onChange={() => toggleColumn(id)} className="accent-brand" />
                      <span className="text-ink">{n?.name_es ?? id}</span>
                      <span className="ml-auto text-xs text-ink-muted">{n?.unit}</span>
                    </label>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Totales visibles siempre (también al pie de la tabla) */}
      <div className="flex flex-wrap items-center gap-x-5 gap-y-1 border-b border-line bg-excelhead px-4 py-2 text-[13.5px]">
        <span className="font-bold text-ink">Total dieta</span>
        {columns.map((id) => {
          const meta = NUTRIENTS_BY_ID[id];
          return (
            <span key={id} className="text-ink-soft">
              {meta?.name_es}: <b className="tabular-nums text-ink">{cell(totals[id])}</b>{' '}
              <span className="text-ink-muted">{meta?.unit}</span>
            </span>
          );
        })}
      </div>

      <div className="min-h-0 flex-1 overflow-auto">
        {loading && <div className="p-4"><Spinner label="Cargando todos los alimentos…" /></div>}
        {error && <div className="p-3"><ErrorBanner message={error} /></div>}
        {!loading && !error && (
          <table className="sheet">
            <thead>
              <tr className="colletter">
                <th className="rownum" />
                {Array.from({ length: 5 + columns.length }, (_, i) => (
                  <th key={i}>{colLetter(i)}</th>
                ))}
              </tr>
              <tr>
                <th className="rownum" />
                <th className="col-sticky text-left">Alimento</th>
                <th className="text-right">Gramos</th>
                <th className="text-right">Int. HC</th>
                <th className="text-right">Int. P</th>
                <th className="text-right">Int. G</th>
                {columns.map((id) => {
                  const meta = NUTRIENTS_BY_ID[id];
                  return (
                    <th key={id} className="text-right">
                      <div>{meta?.name_es ?? id}</div>
                      <div className="font-normal normal-case text-ink-muted">{meta?.unit}</div>
                    </th>
                  );
                })}
              </tr>
            </thead>
            <tbody>
              {groupsToRender.length === 0 && (
                <tr>
                  <td className="rownum" />
                  <td colSpan={columns.length + 5} className="px-4 py-10 text-center text-sm text-ink-soft">
                    {qn
                      ? `Sin coincidencias para «${q}».`
                      : `Busca un alimento arriba para añadirlo a la dieta (${formatNumber(foods.length)} disponibles).`}
                  </td>
                </tr>
              )}
              {groupsToRender.map(({ g, items, start }) => (
                <GroupRows
                  key={g.id}
                  groupLabel={g.label}
                  groupColor={g.color}
                  span={columns.length + 5}
                  items={items}
                  start={start}
                  gramsById={gramsById}
                  onGramsChange={onGramsChange}
                  columns={columns}
                />
              ))}
            </tbody>
            <tfoot>
              <tr className="font-semibold">
                <td className="rownum" />
                <td className="col-sticky text-left text-ink">Total de la dieta</td>
                <td />
                <td className="cell-num text-ink">{formatNumber(exTotals.hc)}</td>
                <td className="cell-num text-ink">{formatNumber(exTotals.protein)}</td>
                <td className="cell-num text-ink">{formatNumber(exTotals.fat)}</td>
                {columns.map((id) => (
                  <td key={id} className="cell-num text-ink">{cell(totals[id])}</td>
                ))}
              </tr>
            </tfoot>
          </table>
        )}
      </div>
    </div>
  );
}

function GroupRows({
  groupLabel,
  groupColor,
  span,
  items,
  start,
  gramsById,
  onGramsChange,
  columns,
}: {
  groupLabel: string;
  groupColor: string;
  span: number;
  items: Food[];
  start: number;
  gramsById: Record<string, number>;
  onGramsChange: (id: string, grams: number) => void;
  columns: string[];
}) {
  return (
    <>
      <tr>
        <td className="rownum" />
        <td colSpan={span} className="bg-excelhead font-semibold text-ink" style={{ borderLeft: `4px solid ${groupColor}` }}>
          {groupLabel}
        </td>
      </tr>
      {items.map((f, i) => {
        const grams = gramsById[f.id] ?? 0;
        const scaled = scaleFood(f, grams);
        const gm = GROUP_BY_ID[f.group];
        const isActive = grams > 0;
        const n = start + i + 1;
        return (
          <tr key={f.id} className={isActive ? 'bg-brand-4/50' : undefined}>
            <td className="rownum">{n}</td>
            <td className="col-sticky text-left">
              <div className="flex items-center gap-2">
                <FoodThumb name={f.name_es} group={f.group} imageName={f.image_name} size={28} />
                <div className="leading-tight">
                  <div className="flex items-center gap-1.5">
                    <span className={isActive ? 'font-semibold text-ink' : 'text-ink'}>{f.name_es}</span>
                    <span className={`chip ${f.state === 'cooked' ? 'bg-accent-4 text-accent' : 'bg-brand-4 text-brand-dark'}`}>
                      {f.state === 'cooked' ? 'coc.' : 'crudo'}
                    </span>
                  </div>
                  <div className="text-[11px] text-ink-muted">
                    {gm?.label}
                    {f.subgroup ? ` · ${f.subgroup}` : ''}
                    {f.household_measure ? ` · ${f.household_measure}` : ''}
                  </div>
                  {f.allergens && f.allergens.length > 0 && (
                    <div className="mt-0.5 flex flex-wrap gap-1">
                      {f.allergens.map((a) => (
                        <span key={a} className="chip bg-accent-4 text-accent">
                          {allergenLabel(a)}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </td>
            <td className="text-right">
              <input
                type="number"
                min={0}
                step={5}
                className="grams-input"
                value={grams > 0 ? grams : ''}
                placeholder="0"
                onChange={(e) => onGramsChange(f.id, parseFloat(e.target.value))}
                aria-label={`Gramos de ${f.name_es}`}
              />
            </td>
            {(() => {
              const m = exchangesByMacro(f, grams);
              // Editar un intercambio calcula el gramaje que lo produce (función inversa).
              const setEx = (macroId: string, val: string) => {
                const nv = f.nutrients[macroId];
                if (!nv || nv.status === 'not_determined' || !nv.amount) return;
                const edible = f.edible_portion_factor ?? 1;
                const g = ((parseFloat(val) || 0) * 1000) / (nv.amount * edible);
                onGramsChange(f.id, Math.round(g * 10) / 10);
              };
              const cellEx = (macroId: string, v: number | null, label: string) => (
                <td className="cell-num">
                  <input
                    type="number"
                    min={0}
                    step={0.5}
                    className="ex-input"
                    value={v === null ? '' : v}
                    placeholder="·"
                    disabled={v === null}
                    onChange={(e) => setEx(macroId, e.target.value)}
                    aria-label={`Intercambios de ${label} de ${f.name_es}`}
                  />
                </td>
              );
              return (
                <>
                  {cellEx('carbs_g', m.hc, 'hidratos')}
                  {cellEx('protein_g', m.protein, 'proteína')}
                  {cellEx('fat_g', m.fat, 'grasa')}
                </>
              );
            })()}
            {columns.map((id) => (
              <td key={id} className="cell-num">{cell(scaled[id])}</td>
            ))}
          </tr>
        );
      })}
    </>
  );
}
