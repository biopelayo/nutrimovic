import { useEffect, useMemo, useRef, useState } from 'react';
import { Header } from './components/Header';
import { SheetTabs } from './components/SheetTabs';
import type { TabId } from './lib/tabs';
import { FoodBrowser } from './components/FoodBrowser';
import { NutritionSheet } from './components/NutritionSheet';
import type { SheetRow } from './components/NutritionSheet';
import { DietSheet } from './components/DietSheet';
import { SubstitutesPanel } from './components/SubstitutesPanel';
import { MacroSplitCard, CoveragePanel } from './components/Insights';
import { ExchangePanel } from './components/ExchangePanel';
import { AlertsPanel } from './components/AlertsPanel';
import { MealsView } from './components/MealsView';
import { PatientView } from './components/PatientView';
import { useHealth } from './hooks/useHealth';
import { getFood, getAllFoods } from './api/foods';
import { ErrorBanner } from './components/ui';
import { scaleFood, sumRows, DEFAULT_SHEET_NUTRIENTS } from './lib/nutrition';
import { DEFAULT_MEAL } from './lib/meals';
import type { MealId } from './lib/meals';
import type { Food, FoodSummary } from './types';

export default function App() {
  const { connection } = useHealth();
  const [tab, setTab] = useState<TabId>('plantilla');
  const [rows, setRows] = useState<SheetRow[]>([]);
  const [columns, setColumns] = useState<string[]>(DEFAULT_SHEET_NUTRIENTS);
  const counter = useRef(0);

  // Hoja de dieta: todos los alimentos precargados con su gramaje.
  const [allFoods, setAllFoods] = useState<Food[]>([]);
  const [allLoading, setAllLoading] = useState(true);
  const [allError, setAllError] = useState<string | null>(null);
  const [dietGrams, setDietGrams] = useState<Record<string, number>>({});
  const [dietColumns, setDietColumns] = useState<string[]>(DEFAULT_SHEET_NUTRIENTS);

  useEffect(() => {
    const controller = new AbortController();
    setAllLoading(true);
    getAllFoods(controller.signal)
      .then((res) => {
        setAllFoods(res);
        setAllLoading(false);
      })
      .catch((err: unknown) => {
        if ((err as Error).name === 'AbortError') return;
        setAllError('No se pudieron cargar los alimentos.');
        setAllLoading(false);
      });
    return () => controller.abort();
  }, []);

  function handleDietGrams(foodId: string, grams: number) {
    setDietGrams((prev) => ({ ...prev, [foodId]: Number.isFinite(grams) && grams > 0 ? grams : 0 }));
  }

  async function handleAdd(summary: FoodSummary) {
    try {
      const food = await getFood(summary.id);
      counter.current += 1;
      setRows((prev) => [...prev, { rowId: `r${counter.current}`, food, grams: 100, meal: DEFAULT_MEAL }]);
    } catch {
      /* el banner de conexión avisa si el backend está caído */
    }
  }

  function handleGramsChange(rowId: string, grams: number) {
    setRows((prev) => prev.map((r) => (r.rowId === rowId ? { ...r, grams } : r)));
  }
  function handleMealChange(rowId: string, meal: MealId) {
    setRows((prev) => prev.map((r) => (r.rowId === rowId ? { ...r, meal } : r)));
  }
  function handleRemove(rowId: string) {
    setRows((prev) => prev.filter((r) => r.rowId !== rowId));
  }

  const totals = useMemo(() => sumRows(rows.map((r) => scaleFood(r.food, r.grams))), [rows]);
  const addedIds = useMemo(() => new Set(rows.map((r) => r.food.id)), [rows]);

  // Totales de la Hoja de dieta (para comparar con los objetivos del paciente).
  const dietFoodsInUse = useMemo(() => allFoods.filter((f) => (dietGrams[f.id] ?? 0) > 0), [allFoods, dietGrams]);
  const dietTotals = useMemo(
    () => sumRows(dietFoodsInUse.map((f) => scaleFood(f, dietGrams[f.id] ?? 0))),
    [dietFoodsInUse, dietGrams],
  );

  return (
    <div className="flex h-screen flex-col bg-surface">
      <Header />

      {connection === 'offline' && (
        <div className="mx-auto w-full max-w-[1700px] px-5 pt-3">
          <ErrorBanner
            message="No se puede contactar con el servidor de datos. Arráncalo para cargar los alimentos."
            onRetry={() => window.location.reload()}
          />
        </div>
      )}

      {tab === 'plantilla' && (
        <div className="mx-auto flex w-full max-w-[1700px] flex-1 flex-col gap-3 overflow-hidden p-3 lg:flex-row lg:gap-4 lg:p-4">
          {/* Panel de alimentos (más grande) */}
          <div className="card h-80 shrink-0 overflow-hidden lg:h-full lg:w-[540px]">
            <FoodBrowser onAdd={handleAdd} addedIds={addedIds} />
          </div>

          {/* Plantilla + análisis */}
          <div className="flex-1 space-y-4 overflow-y-auto pb-4">
            <NutritionSheet
              rows={rows}
              columns={columns}
              totals={totals}
              onGramsChange={handleGramsChange}
              onMealChange={handleMealChange}
              onRemove={handleRemove}
              onColumnsChange={setColumns}
            />
            <ExchangePanel rows={rows} />
            <div className="grid gap-4 lg:grid-cols-2">
              <MacroSplitCard totals={totals} />
              <CoveragePanel totals={totals} />
            </div>
            <p className="px-1 text-center text-xs text-ink-muted">
              Datos provisionales (versión de prueba); el valor de referencia clínico exige validar la fuente.
              No sustituye al criterio del profesional sanitario.
            </p>
          </div>
        </div>
      )}

      {tab === 'dieta' && (
        <div className="mx-auto flex w-full max-w-[1700px] flex-1 flex-col gap-3 overflow-hidden p-3 lg:p-4">
          <div className="min-h-0 flex-1">
            <DietSheet
              foods={allFoods}
              gramsById={dietGrams}
              onGramsChange={handleDietGrams}
              columns={dietColumns}
              onColumnsChange={setDietColumns}
              loading={allLoading}
              error={allError}
            />
          </div>
          <SubstitutesPanel foods={allFoods} gramsById={dietGrams} />
        </div>
      )}

      {tab === 'paciente' && (
        <div className="mx-auto w-full max-w-[1700px] flex-1 overflow-y-auto p-4">
          <PatientView dietGrams={dietGrams} dietTotals={dietTotals} onLoadDiet={setDietGrams} />
        </div>
      )}

      {tab === 'comidas' && (
        <div className="mx-auto w-full max-w-[1700px] flex-1 overflow-y-auto p-4">
          <MealsView rows={rows} />
        </div>
      )}

      {tab === 'alertas' && (
        <div className="mx-auto w-full max-w-[1700px] flex-1 overflow-y-auto p-4">
          <AlertsPanel totals={dietTotals} foods={dietFoodsInUse} />
        </div>
      )}

      <SheetTabs active={tab} onSelect={setTab} />
    </div>
  );
}
