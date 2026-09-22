import { useState } from "react";
import { Check, Copy } from "lucide-react";
import { copyToClipboard } from "@/lib/utils";

/** A snippet with a copy button — used for keys, curl and code samples. */
export function CodeBlock({ value, label }: { value: string; label?: string }) {
  const [copied, setCopied] = useState(false);

  return (
    <div className="relative">
      {label ? (
        <p className="mb-1.5 text-[11px] uppercase tracking-wide text-[var(--color-ink-subtle)]">
          {label}
        </p>
      ) : null}
      <pre className="overflow-x-auto rounded-lg border border-[var(--color-border)] bg-[var(--color-canvas)] p-3 pr-12 font-mono text-[11px] leading-relaxed text-[var(--color-ink-muted)]">
        {value}
      </pre>
      <button
        type="button"
        onClick={async () => {
          if (await copyToClipboard(value)) {
            setCopied(true);
            setTimeout(() => setCopied(false), 1500);
          }
        }}
        aria-label="Copy to clipboard"
        className="absolute right-2 bottom-2 rounded-md border border-[var(--color-border-strong)] bg-[var(--color-surface-raised)] p-1.5 text-[var(--color-ink-muted)] transition-colors hover:text-[var(--color-ink)]"
      >
        {copied ? (
          <Check className="h-3.5 w-3.5 text-[var(--color-positive)]" />
        ) : (
          <Copy className="h-3.5 w-3.5" />
        )}
      </button>
    </div>
  );
}
