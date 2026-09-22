import type { ReactNode } from "react";

export function StatTile({
  label,
  value,
  hint,
}: {
  label: string;
  value: ReactNode;
  hint?: string;
}) {
  return (
    <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] px-4 py-3">
      <p className="text-[11px] uppercase tracking-wide text-[var(--color-ink-subtle)]">{label}</p>
      <p className="mt-1 font-mono text-xl tabular-nums">{value}</p>
      {hint ? <p className="mt-0.5 text-[11px] text-[var(--color-ink-muted)]">{hint}</p> : null}
    </div>
  );
}
