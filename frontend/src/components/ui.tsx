// Primitivas de interfaz reutilizables (Sistema Visual Pelamovic).
import type { ReactNode } from 'react';
import type { MeasurementStatus } from '../types';
import { STATUS_LABEL } from '../lib/format';

export function Spinner({ label }: { label?: string }) {
  return (
    <span className="inline-flex items-center gap-2 text-sm text-ink-soft" role="status">
      <span
        aria-hidden
        className="h-4 w-4 animate-spin rounded-full border-2 border-botanical-3 border-t-botanical"
      />
      {label ?? 'Cargando…'}
    </span>
  );
}

export function ErrorBanner({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div
      role="alert"
      className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-warm/40 bg-warm/10 px-4 py-3 text-sm text-ink"
    >
      <span>{message}</span>
      {onRetry && (
        <button className="btn-ghost text-sm" onClick={onRetry}>
          Reintentar
        </button>
      )}
    </div>
  );
}

export function InfoBox({ children }: { children: ReactNode }) {
  return (
    <div className="rounded-lg border border-dashed border-botanical-2/50 bg-botanical-4/40 px-4 py-3 text-sm text-ink-soft">
      {children}
    </div>
  );
}

export function EmptyState({ title, hint }: { title: string; hint?: string }) {
  return (
    <div className="rounded-card border border-dashed border-grid px-6 py-10 text-center">
      <p className="font-medium text-ink">{title}</p>
      {hint && <p className="mt-1 text-sm text-ink-soft">{hint}</p>}
    </div>
  );
}

const DOT: Record<MeasurementStatus, string> = {
  measured: 'bg-botanical',
  trace: 'bg-warm',
  not_determined: 'bg-ink-muted',
};

/** Punto de color que indica el estado de medicion de un valor. */
export function StatusDot({ status }: { status: MeasurementStatus }) {
  return (
    <span
      className={`inline-block h-2 w-2 rounded-full ${DOT[status]}`}
      title={STATUS_LABEL[status]}
      aria-label={STATUS_LABEL[status]}
    />
  );
}
