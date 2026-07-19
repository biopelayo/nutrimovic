import { useMemo } from 'react';
import { exchangesForFood, gramsPerExchange, referenceNutrient, REFERENCE_LABEL } from '../lib/exchanges';
import { formatNumber } from '../lib/format';
import { FoodThumb } from './FoodThumb';
import type { Food } from '../types';

interface Props {
  foods: Food[];
  gramsById: Record<string, number>;
}

/**
 * Sustituciones por intercambio: para cada alimento en uso, alimentos del mismo
 * grupo que aportan las mismas raciones (con su gramaje equivalente). Panel aparte
 * porque cada alimento genera una lista de alternativas.
 */
export function SubstitutesPanel({ foods, gramsById }: Props) {
  const rows = useMemo(() => {
    const active = foods.filter((f) => (gramsById[f.id] ?? 0) > 0 && referenceNutrient(f.group));
    return active
      .map((f) => {
        const ref = referenceNutrient(f.group)!;
        const exchanges = exchangesForFood(f, gramsById[f.id] ?? 0);
        if (exchanges === null || exchanges <= 0) return null;
        const subs = foods
          .filter((c) => c.id !== f.id && referenceNutrient(c.group) === ref)
          .map((c) => ({ food: c, grams: gramsPerExchange(c) }))
          .filter((x): x is { food: Food; grams: number } => x.grams !== null)
          .map((x) => ({ food: x.food, grams: Math.round(x.grams * exchanges * 10) / 10 }))
          .slice(0, 4);
        return { food: f, ref, exchanges, subs };
      })
      .filter(Boolean) as {
      food: Food;
      ref: string;
      exchanges: number;
      subs: { food: Food; grams: number }[];
    }[];
  }, [foods, gramsById]);

  return (
    <div className="card overflow-hidden">
      <div className="border-b border-line px-4 py-2.5">
        <h3 className="text-lg font-bold text-ink">Sustituciones por intercambio</h3>
        <p className="text-[13px] text-ink-soft">
          Alimentos que aportan las mismas raciones y puedes cambiar por otro del mismo grupo.
        </p>
      </div>
      {rows.length === 0 ? (
        <p className="px-4 py-6 text-center text-sm text-ink-soft">
          Pon gramos a alimentos de lácteos, farináceos, frutas, verduras, carnes/pescados o grasas para ver
          equivalencias.
        </p>
      ) : (
        <div className="max-h-72 overflow-y-auto divide-y divide-line">
          {rows.map((r) => (
            <div key={r.food.id} className="flex flex-wrap items-center gap-x-4 gap-y-2 px-4 py-2.5">
              <div className="flex min-w-[220px] items-center gap-2">
                <FoodThumb name={r.food.name_es} group={r.food.group} imageName={r.food.image_name} size={30} />
                <div className="leading-tight">
                  <div className="font-semibold text-ink">{r.food.name_es}</div>
                  <div className="text-[11px] text-ink-muted">
                    {formatNumber(gramsById[r.food.id] ?? 0)} g · {formatNumber(r.exchanges)} raciones de{' '}
                    {REFERENCE_LABEL[r.ref]}
                  </div>
                </div>
              </div>
              <span className="text-ink-muted">→</span>
              <div className="flex flex-1 flex-wrap gap-2">
                {r.subs.map((s) => (
                  <span
                    key={s.food.id}
                    className="inline-flex items-center gap-1.5 rounded-sm border border-line bg-surface px-2 py-1 text-[13px]"
                  >
                    <FoodThumb name={s.food.name_es} group={s.food.group} imageName={s.food.image_name} size={20} />
                    <span className="text-ink">{s.food.name_es}</span>
                    <b className="tabular-nums text-brand-dark">{formatNumber(s.grams)} g</b>
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
