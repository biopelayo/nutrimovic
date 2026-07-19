import { useEffect, useId, useRef, useState } from 'react';
import { useFoodSearch } from '../hooks/useFoodSearch';
import { FOOD_GROUP_LABELS, SOURCE_LABELS } from '../data/nutrients';
import { Spinner, ErrorBanner } from './ui';
import type { FoodSummary } from '../types';

interface Props {
  onSelect: (food: FoodSummary) => void;
  placeholder?: string;
  autoFocus?: boolean;
}

/** Buscador de alimentos con autocompletado (GET /foods/search). */
export function FoodSearch({ onSelect, placeholder, autoFocus }: Props) {
  const [query, setQuery] = useState('');
  const [open, setOpen] = useState(false);
  const [highlight, setHighlight] = useState(0);
  const { results, loading, error } = useFoodSearch(query);
  const listboxId = useId();
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => setHighlight(0), [results]);

  // Cerrar el desplegable al hacer clic fuera.
  useEffect(() => {
    function onClickOutside(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener('mousedown', onClickOutside);
    return () => document.removeEventListener('mousedown', onClickOutside);
  }, []);

  function choose(food: FoodSummary) {
    onSelect(food);
    setQuery('');
    setOpen(false);
  }

  function onKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (!open || results.length === 0) return;
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setHighlight((h) => Math.min(h + 1, results.length - 1));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setHighlight((h) => Math.max(h - 1, 0));
    } else if (e.key === 'Enter') {
      e.preventDefault();
      const food = results[highlight];
      if (food) choose(food);
    } else if (e.key === 'Escape') {
      setOpen(false);
    }
  }

  const showList = open && query.trim().length >= 2;

  return (
    <div ref={containerRef} className="relative">
      <label className="sr-only" htmlFor={`${listboxId}-input`}>
        Buscar alimento
      </label>
      <div className="relative">
        <span aria-hidden className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-ink-muted">
          {/* lupa */}
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="11" cy="11" r="7" />
            <line x1="21" y1="21" x2="16.65" y2="16.65" />
          </svg>
        </span>
        <input
          id={`${listboxId}-input`}
          className="field pl-10"
          type="text"
          role="combobox"
          aria-expanded={showList}
          aria-controls={listboxId}
          aria-autocomplete="list"
          autoFocus={autoFocus}
          value={query}
          placeholder={placeholder ?? 'Busca un alimento (p. ej. «lenteja», «salmón»)'}
          onChange={(e) => {
            setQuery(e.target.value);
            setOpen(true);
          }}
          onFocus={() => setOpen(true)}
          onKeyDown={onKeyDown}
        />
        {loading && (
          <span className="absolute right-3 top-1/2 -translate-y-1/2">
            <Spinner label="" />
          </span>
        )}
      </div>

      {showList && (
        <div
          id={listboxId}
          role="listbox"
          className="absolute z-20 mt-1 max-h-72 w-full overflow-auto rounded-lg border border-grid bg-white shadow-lg"
        >
          {error && <div className="p-2"><ErrorBanner message={error} /></div>}
          {!error && !loading && results.length === 0 && (
            <p className="px-4 py-3 text-sm text-ink-soft">Sin resultados para «{query}».</p>
          )}
          {results.map((food, i) => (
            <button
              key={food.id}
              role="option"
              aria-selected={i === highlight}
              className={`flex w-full items-center justify-between gap-3 px-4 py-2 text-left text-sm transition ${
                i === highlight ? 'bg-botanical-4' : 'hover:bg-botanical-4/60'
              }`}
              onMouseEnter={() => setHighlight(i)}
              onClick={() => choose(food)}
            >
              <span className="font-medium text-ink">{food.name_es}</span>
              <span className="flex shrink-0 items-center gap-2 text-xs text-ink-soft">
                <span className="rounded-full bg-botanical-4 px-2 py-0.5 text-botanical-dark">
                  {FOOD_GROUP_LABELS[food.group] ?? food.group}
                </span>
                <span>{SOURCE_LABELS[food.source] ?? food.source}</span>
              </span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
