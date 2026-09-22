import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

export function Card({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <section
      className={cn(
        "rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)]",
        className,
      )}
    >
      {children}
    </section>
  );
}

export function CardHeader({
  title,
  description,
  action,
  icon,
}: {
  title: string;
  description?: string;
  action?: ReactNode;
  icon?: ReactNode;
}) {
  return (
    <header className="flex items-start justify-between gap-4 border-b border-[var(--color-border)] px-5 py-4">
      <div className="flex min-w-0 items-start gap-3">
        {icon ? <span className="mt-0.5 text-[var(--color-ink-subtle)]">{icon}</span> : null}
        <div className="min-w-0">
          <h2 className="truncate text-sm font-semibold tracking-tight">{title}</h2>
          {description ? (
            <p className="mt-1 text-xs leading-relaxed text-[var(--color-ink-muted)]">
              {description}
            </p>
          ) : null}
        </div>
      </div>
      {action}
    </header>
  );
}

export function CardBody({ children, className }: { children: ReactNode; className?: string }) {
  return <div className={cn("px-5 py-4", className)}>{children}</div>;
}
