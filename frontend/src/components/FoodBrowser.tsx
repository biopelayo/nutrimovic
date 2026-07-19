import { useEffect, useMemo, useState } from 'react';
import { searchFoods } from '../api/foods';
import { useDebounce } from '../hooks/useDebounce';
import { FOOD_GROUPS } from '../data/foodGroups';
import { FoodThumb } from './FoodThumb';
import { SearchIcon, CheckIcon, ChevronRight } from './Icons';
import { Spinner, ErrorBanner } from './ui';
import type { FoodSummary } from '../types';

interface Props {
  onAdd: (food: FoodSummary) => void;
  addedIds: Set<string>;
}

/**
 * Navegador visual de alimentos: clasificación por grupo → subgrupo, con foto real
 * grande. Cada alimento es una tarjeta; al pulsarla se añade a la hoja.
 */
export function FoodBrowser({ onAdd, addedIds }: Props) {
  const [q, setQ] = useState('');
  const debouncedQ = useDebounce(q, 200);
  const [foods, setFoods] = useState<FoodSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [collapsed, setCollapsed] = useState<Set<string>>(new Set());

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError(null);
    searchFoods(debouncedQ, { limit: 500 }, controller.signal)
      .then((res) => {
        setFoods(res);
        setLoading(false);
      })
      .catch((err: unknown) => {
        if ((err as Error).name === 'AbortError') return;
        setError('No se pudieron cargar los alimentos.');
        setLoading(false);
      });
    return () => controller.abort();
  }, [debouncedQ]);

  const byGroup = useMemo(() => {
    const map = new Map<string, Map<string, FoodSummary[]>>();
    for (const f of foods) {
      const sub = f.subgroup ?? 'General';
      if (!map.has(f.group)) map.set(f.group, new Map());
      const subs = map.get(f.group)!;
      if (!subs.has(sub)) subs.set(sub, []);
      subs.get(sub)!.push(f);
    }
    return map;
  }, [foods]);

  function toggle(id: string) {
    setCollapsed((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  }

  const groupsWithFoods = FOOD_GROUPS.filter((g) => (byGroup.get(g.id)?.size ?? 0) > 0);

  return (
    <aside className="flex h-full flex-col">
      <div className="border-b border-line px-4 pb-3 pt-4">
        <div className="mb-2 flex items-baseline justify-between">
          <h2 className="text-lg font-bold text-ink">Alimentos</h2>
          <span className="text-sm text-ink-muted">{foods.length}</span>
        </div>
        <div className="relative">
          <span className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-ink-muted">
            <SearchIcon className="h-5 w-5" />
          </span>
          <input
            className="field pl-10 text-[15px]"
            placeholder="Buscar alimento…"
            value={q}
            onChange={(e) => setQ(e.target.value)}
            aria-label="Buscar alimento"
          />
        </div>
      </div>

      <div className="flex-1 overflow-y-auto px-2.5 py-2">
        {loading && (
          <div className="p-3">
            <Spinner label="Cargando alimentos…" />
          </div>
        )}
        {error && (
          <div className="p-2">
            <ErrorBanner message={error} />
          </div>
        )}
        {!loading && !error && groupsWithFoods.length === 0 && (
          <p className="p-3 text-sm text-ink-soft">Sin resultados para «{q}».</p>
        )}

        {groupsWithFoods.map((g) => {
          const subs = byGroup.get(g.id)!;
          const count = [...subs.values()].reduce((s, arr) => s + arr.length, 0);
          const isOpen = !collapsed.has(g.id);
          return (
            <section key={g.id} className="mb-2">
              <button
                className="flex w-full items-center gap-2.5 rounded-sm px-2 py-2.5 text-left transition hover:bg-surface"
                onClick={() => toggle(g.id)}
                aria-expanded={isOpen}
                style={{ borderLeft: `4px solid ${g.color}` }}
              >
                <span className="flex-1 text-[15px] font-bold text-ink">{g.label}</span>
                <span className="rounded-sm bg-surface px-2 py-0.5 text-xs tabular-nums text-ink-soft">{count}</span>
                <ChevronRight className={`h-4 w-4 text-ink-muted transition ${isOpen ? 'rotate-90' : ''}`} />
              </button>

              {isOpen &&
                [...subs.entries()].map(([sub, items]) => (
                  <div key={sub} className="mb-2 pl-2">
                    <p className="px-1 py-1 text-[11px] font-semibold uppercase tracking-wide text-ink-muted">{sub}</p>
                    <div className="grid grid-cols-2 gap-2">
                      {items.map((f) => {
                        const added = addedIds.has(f.id);
                        return (
                          <button
                            key={f.id}
                            onClick={() => onAdd(f)}
                            title={added ? 'Añadir otra vez' : 'Añadir a la hoja'}
                            aria-label={`Añadir ${f.name_es} a la hoja`}
                            className={`group relative flex items-center gap-2.5 rounded-sm border p-2 text-left transition ${
                              added ? 'border-brand bg-brand-4' : 'border-line bg-paper hover:border-brand hover:bg-surface'
                            }`}
                          >
                            <FoodThumb name={f.name_es} group={f.group} imageName={f.image_name} size={52} />
                            <span className="line-clamp-2 flex-1 text-[13.5px] font-medium leading-tight text-ink">
                              {f.name_es}
                            </span>
                            {added && (
                              <span className="absolute right-1 top-1 grid h-4 w-4 place-items-center rounded-full bg-brand text-white">
                                <CheckIcon className="h-3 w-3" />
                              </span>
                            )}
                          </button>
                        );
                      })}
                    </div>
                  </div>
                ))}
            </section>
          );
        })}
      </div>
    </aside>
  );
}
