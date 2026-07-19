import { TABS } from '../lib/tabs';
import type { TabId } from '../lib/tabs';

// Pestañas de hoja al estilo Excel, en la parte inferior del libro.
export function SheetTabs({ active, onSelect }: { active: TabId; onSelect: (t: TabId) => void }) {
  return (
    <div className="no-print flex items-stretch border-t border-line bg-surface">
      {TABS.map((t) => {
        const isActive = t.id === active;
        return (
          <button
            key={t.id}
            onClick={() => onSelect(t.id)}
            className={`sheet-tab ${isActive ? 'sheet-tab-active' : 'sheet-tab-inactive'}`}
            aria-current={isActive ? 'page' : undefined}
          >
            {t.label}
          </button>
        );
      })}
    </div>
  );
}
