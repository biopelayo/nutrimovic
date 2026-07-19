import { Fragment, useMemo, useState } from 'react';
import { NUTRIENTS, NUTRIENTS_BY_ID } from '../data/nutrients';
import { FOOD_GROUPS, GROUP_BY_ID } from '../data/foodGroups';
import { scaleFood, sumRows, MICRO_NUTRIENT_IDS } from '../lib/nutrition';
import { exchangesByMacro } from '../lib/exchanges';
import { allergenLabel } from '../lib/allergens';
import { formatNumber } from '../lib/format';
import { FoodThumb } from './FoodThumb';
import { SearchIcon, ChevronRight } from './Icons';
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
  const [closedGroups, setClosedGroups] = useState<Set<string>>(new Set());
  const [openSubs, setOpenSubs] = useState<Set<string>>(new Set());

  const qn = q.trim().toLowerCase();

  // Estructura completa por grupo -> subgrupo, y numeración global fija.
  const { byGroup, numById } = useMemo(() => {
    const all = new Map<string, Map<string, Food[]>>();
    for (const f of foods) {
      const sub = f.subgroup ?? 'General';
      if (!all.has(f.group)) all.set(f.group, new Map());
      const subs = all.get(f.group)!;
      if (!subs.has(sub)) subs.set(sub, []);
      subs.get(sub)!.push(f);
    }
    const num = new Map<string, number>();
    let n = 0;
    for (const g of FOOD_GROUPS) {
      const subs = all.get(g.id);
      if (!subs) continue;
      for (const [, items] of subs) for (const f of items) num.set(f.id, ++n);
    }
    if (!qn) return { byGroup: all, numById: num };
    // Filtrado por búsqueda.
    const filtered = new Map<string, Map<string, Food[]>>();
    for (const [gid, subs] of all) {
      const fsubs = new Map<string, Food[]>();
      for (const [sub, items] of subs) {
        const m = items.filter((f) => f.name_es.toLowerCase().includes(qn));
        if (m.length) fsubs.set(sub, m);
      }
      if (fsubs.size) filtered.set(gid, fsubs);
    }
    return { byGroup: filtered, numById: num };
  }, [foods, qn]);

  const active = foods.filter((f) => (gramsById[f.id] ?? 0) > 0);
  const totals = useMemo(
    () => sumRows(active.map((f) => scaleFood(f, gramsById[f.id] ?? 0))),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [foods, gramsById],
  );
  const totalKcal = totals['energy_kcal']?.amount ?? 0;
  const exTotals = useMemo(() => {
    let hc = 0, protein = 0, fat = 0;
    for (const f of active) {
      const m = exchangesByMacro(f, gramsById[f.id] ?? 0);
      hc += m.hc ?? 0; protein += m.protein ?? 0; fat += m.fat ?? 0;
    }
    const r = (x: number) => Math.round(x * 100) / 100;
    return { hc: r(hc), protein: r(protein), fat: r(fat) };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [foods, gramsById]);

  function toggleColumn(id: string) {
    onColumnsChange(columns.includes(id) ? columns.filter((c) => c !== id) : [...columns, id]);
  }
  function toggleGroup(g: string) {
    setClosedGroups((p) => { const n = new Set(p); n.has(g) ? n.delete(g) : n.add(g); return n; });
  }
  function toggleSub(key: string) {
    setOpenSubs((p) => { const n = new Set(p); n.has(key) ? n.delete(key) : n.add(key); return n; });
  }
  const nCols = columns.length + 6; // rownum + alimento + gramos + 3 int + columns

  return (
    <div className="card flex h-full flex-col overflow-hidden">
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-line px-4 py-2.5">
        <div>
          <h2 className="text-lg font-bold text-ink">Hoja de dieta</h2>
          <p className="text-[13px] text-ink-soft">
            <span className="font-semibold text-ink">{formatNumber(foods.length)}</span> alimentos precargados · abre un
            subgrupo y pon gramos o intercambios ·{' '}
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
                  <ColTgl key={n.id} id={n.id} active={columns.includes(n.id)} onToggle={toggleColumn} />
                ))}
                <p className="px-1 pb-1 pt-2 text-[11px] font-semibold uppercase text-ink-soft">Micronutrientes</p>
                {MICRO_NUTRIENT_IDS.map((id) => (
                  <ColTgl key={id} id={id} active={columns.includes(id)} onToggle={toggleColumn} />
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

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
              {byGroup.size === 0 && (
                <tr>
                  <td className="rownum" />
                  <td colSpan={nCols - 1} className="px-4 py-10 text-center text-sm text-ink-soft">
                    Sin coincidencias para «{q}».
                  </td>
                </tr>
              )}
              {FOOD_GROUPS.map((g) => {
                const subs = byGroup.get(g.id);
                if (!subs) return null;
                const count = [...subs.values()].reduce((s, a) => s + a.length, 0);
                const gOpen = qn ? true : !closedGroups.has(g.id);
                return (
                  <Fragment key={g.id}>
                    <tr className="cursor-pointer select-none" onClick={() => toggleGroup(g.id)}>
                      <td className="rownum" />
                      <td colSpan={nCols - 1} className="bg-excelhead font-bold text-ink" style={{ borderLeft: `4px solid ${g.color}` }}>
                        <span className="inline-flex items-center gap-1.5">
                          <ChevronRight className={`h-4 w-4 text-ink-muted transition ${gOpen ? 'rotate-90' : ''}`} />
                          {g.label}
                          <span className="rounded-sm bg-white px-1.5 text-[11px] font-normal tabular-nums text-ink-soft">{count}</span>
                        </span>
                      </td>
                    </tr>
                    {gOpen &&
                      [...subs.entries()].map(([sub, items]) => {
                        const key = `${g.id}::${sub}`;
                        const inUse = items.some((f) => (gramsById[f.id] ?? 0) > 0);
                        const sOpen = qn ? true : openSubs.has(key) || inUse;
                        return (
                          <Fragment key={key}>
                            <tr className="cursor-pointer select-none" onClick={() => toggleSub(key)}>
                              <td className="rownum" />
                              <td colSpan={nCols - 1} className="bg-slate-50 text-[13px] font-semibold text-ink-soft">
                                <span className="inline-flex items-center gap-1.5 pl-4">
                                  <ChevronRight className={`h-3.5 w-3.5 text-ink-muted transition ${sOpen ? 'rotate-90' : ''}`} />
                                  {sub}
                                  <span className="text-[11px] font-normal tabular-nums text-ink-muted">({items.length})</span>
                                </span>
                              </td>
                            </tr>
                            {sOpen &&
                              items.map((f) => (
                                <FoodRow
                                  key={f.id}
                                  food={f}
                                  num={numById.get(f.id) ?? 0}
                                  grams={gramsById[f.id] ?? 0}
                                  columns={columns}
                                  onGramsChange={onGramsChange}
                                />
                              ))}
                          </Fragment>
                        );
                      })}
                  </Fragment>
                );
              })}
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

function FoodRow({
  food,
  num,
  grams,
  columns,
  onGramsChange,
}: {
  food: Food;
  num: number;
  grams: number;
  columns: string[];
  onGramsChange: (id: string, grams: number) => void;
}) {
  const scaled = scaleFood(food, grams);
  const m = exchangesByMacro(food, grams);
  const gm = GROUP_BY_ID[food.group];
  const isActive = grams > 0;

  const setEx = (macroId: string, val: string) => {
    const nv = food.nutrients[macroId];
    if (!nv || nv.status === 'not_determined' || !nv.amount) return;
    const edible = food.edible_portion_factor ?? 1;
    const g = ((parseFloat(val) || 0) * 1000) / (nv.amount * edible);
    onGramsChange(food.id, Math.round(g * 10) / 10);
  };
  const exCell = (macroId: string, v: number | null, label: string) => (
    <td className="cell-num">
      <input
        type="number" min={0} step={0.5} className="ex-input"
        value={v === null ? '' : v} placeholder="·" disabled={v === null}
        onChange={(e) => setEx(macroId, e.target.value)}
        aria-label={`Intercambios de ${label} de ${food.name_es}`}
      />
    </td>
  );

  return (
    <tr className={isActive ? 'bg-brand-4/50' : undefined}>
      <td className="rownum">{num}</td>
      <td className="col-sticky text-left">
        <div className="flex items-center gap-2">
          <FoodThumb name={food.name_es} group={food.group} imageName={food.image_name} size={28} />
          <div className="leading-tight">
            <div className="flex items-center gap-1.5">
              <span className={isActive ? 'font-semibold text-ink' : 'text-ink'}>{food.name_es}</span>
              <span className={`chip ${food.state === 'cooked' ? 'bg-accent-4 text-accent' : 'bg-brand-4 text-brand-dark'}`}>
                {food.state === 'cooked' ? 'coc.' : 'crudo'}
              </span>
            </div>
            <div className="text-[11px] text-ink-muted">
              {gm?.label}
              {food.household_measure ? ` · ${food.household_measure}` : ''}
            </div>
            {food.allergens && food.allergens.length > 0 && (
              <div className="mt-0.5 flex flex-wrap gap-1">
                {food.allergens.map((a) => (
                  <span key={a} className="chip bg-accent-4 text-accent">{allergenLabel(a)}</span>
                ))}
              </div>
            )}
          </div>
        </div>
      </td>
      <td className="text-right">
        <input
          type="number" min={0} step={5} className="grams-input"
          value={grams > 0 ? grams : ''} placeholder="0"
          onChange={(e) => onGramsChange(food.id, parseFloat(e.target.value))}
          aria-label={`Gramos de ${food.name_es}`}
        />
      </td>
      {exCell('carbs_g', m.hc, 'hidratos')}
      {exCell('protein_g', m.protein, 'proteína')}
      {exCell('fat_g', m.fat, 'grasa')}
      {columns.map((id) => (
        <td key={id} className="cell-num">{cell(scaled[id])}</td>
      ))}
    </tr>
  );
}

function ColTgl({ id, active, onToggle }: { id: string; active: boolean; onToggle: (id: string) => void }) {
  const meta = NUTRIENTS_BY_ID[id];
  return (
    <label className="flex cursor-pointer items-center gap-2 rounded-sm px-1.5 py-1 text-sm hover:bg-surface">
      <input type="checkbox" checked={active} onChange={() => onToggle(id)} className="accent-brand" />
      <span className="text-ink">{meta?.name_es ?? id}</span>
      <span className="ml-auto text-xs text-ink-muted">{meta?.unit}</span>
    </label>
  );
}
