interface Props {
  title: string;
  desc: string;
  bullets: string[];
}

/** Marcador de sección en preparación, con lo que incluirá. */
export function ComingSoon({ title, desc, bullets }: Props) {
  return (
    <div className="card mx-auto max-w-2xl p-8">
      <span className="chip bg-accent-4 text-accent">En preparación</span>
      <h2 className="mt-3 font-display text-2xl font-semibold text-ink">{title}</h2>
      <p className="mt-2 text-ink-soft">{desc}</p>
      <ul className="mt-4 space-y-2">
        {bullets.map((b) => (
          <li key={b} className="flex items-start gap-2 text-sm text-ink">
            <span className="mt-0.5 text-brand" aria-hidden>
              ✓
            </span>
            <span>{b}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
