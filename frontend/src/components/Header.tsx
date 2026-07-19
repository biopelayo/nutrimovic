import { useInstallPrompt } from '../hooks/useInstallPrompt';
import { LeafLogo } from './Icons';

// Barra superior: franja verde con el logo de hoja y el nombre.
export function Header() {
  const { canInstall, promptInstall } = useInstallPrompt();
  return (
    <header className="no-print flex items-center gap-2 bg-brand px-4 py-1.5 text-white">
      <LeafLogo className="h-5 w-5 text-white/90" />
      <h1 className="text-[15px] font-semibold tracking-tight">NutriMovic</h1>
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
