import type { InputHTMLAttributes, ReactNode, SelectHTMLAttributes } from "react";
import { cn } from "@/lib/utils";

const CONTROL =
  "w-full rounded-lg border border-[var(--color-border-strong)] bg-[var(--color-canvas)] px-3 py-2 " +
  "text-sm text-[var(--color-ink)] placeholder:text-[var(--color-ink-subtle)] " +
  "focus:border-[var(--color-accent)] focus:outline-none disabled:opacity-50";

export function Field({
  label,
  hint,
  children,
}: {
  label: string;
  hint?: ReactNode;
  children: ReactNode;
}) {
  return (
    <label className="block space-y-1.5">
      <span className="text-xs font-medium text-[var(--color-ink-muted)]">{label}</span>
      {children}
      {hint ? <span className="block text-[11px] text-[var(--color-ink-subtle)]">{hint}</span> : null}
    </label>
  );
}

export function Input({ className, ...rest }: InputHTMLAttributes<HTMLInputElement>) {
  return <input className={cn(CONTROL, className)} {...rest} />;
}

export function Select({ className, ...rest }: SelectHTMLAttributes<HTMLSelectElement>) {
  return <select className={cn(CONTROL, "appearance-none", className)} {...rest} />;
}
