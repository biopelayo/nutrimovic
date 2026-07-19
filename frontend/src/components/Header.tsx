import { useInstallPrompt } from '../hooks/useInstallPrompt';

// Barra superior al estilo Excel: franja verde con el nombre del libro.
export function Header() {
  const { canInstall, promptInstall } = useInstallPrompt();
  return (
    <header className="no-print flex items-center gap-3 bg-brand px-4 py-1.5 text-white">
      <h1 className="text-[15px] font-semibold tracking-tight">NutriMovic</h1>
      <span className="text-[12px] text-white/70">— libro de dieta</span>
      <div className="ml-auto">
        {canInstall && (
          <button
            className="rounded-sm border border-white/40 px-2.5 py-1 text-[12px] font-medium hover:bg-white/10"
            onClick={promptInstall}
          >
            Instalar
          </button>
        )}
      </div>
    </header>
  );
}
