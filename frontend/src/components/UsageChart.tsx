import { useState } from "react";
import type { UsagePoint } from "@/lib/types";

/**
 * Requests per hour for the last 24 hours, drawn as inline SVG.
 *
 * A chart library would be ~50 KB for one bar chart; this is 60 lines, has no
 * dependencies, and scales with the container.
 */
export function UsageChart({ points }: { points: UsagePoint[] }) {
  const [hovered, setHovered] = useState<number | null>(null);
  const max = Math.max(1, ...points.map((point) => point.total));
  const width = 100;
  const height = 34;
  const gap = 0.35;
  const barWidth = width / points.length - gap;

  const active = hovered !== null ? points[hovered] : null;

  return (
    <div className="space-y-2">
      <svg
        viewBox={`0 0 ${width} ${height}`}
        preserveAspectRatio="none"
        role="img"
        aria-label="Requests per hour over the last 24 hours"
        className="h-36 w-full"
      >
        {/* Baseline and the midpoint gridline, drawn under the bars. */}
        <line x1="0" y1={height} x2={width} y2={height} stroke="var(--color-border)" strokeWidth="0.2" />
        <line
          x1="0"
          y1={height / 2}
          x2={width}
          y2={height / 2}
          stroke="var(--color-border)"
          strokeWidth="0.15"
          strokeDasharray="0.8 0.8"
        />
        {points.map((point, index) => {
          const total = Math.max(point.total, 0);
          const barHeight = (total / max) * (height - 2);
          const errorHeight = total ? (point.errors / max) * (height - 2) : 0;
          const x = index * (barWidth + gap);
          return (
            <g
              key={point.bucket}
              onMouseEnter={() => setHovered(index)}
              onMouseLeave={() => setHovered(null)}
            >
              {/* Full-height hit area so thin bars stay hoverable. */}
              <rect x={x} y={0} width={barWidth + gap} height={height} fill="transparent" />
              <rect
                x={x}
                y={height - barHeight}
                width={barWidth}
                height={barHeight}
                rx="0.3"
                fill={hovered === index ? "var(--color-ink)" : "var(--color-accent)"}
                opacity={total ? 1 : 0.15}
              />
              {errorHeight > 0 ? (
                <rect
                  x={x}
                  y={height - errorHeight}
                  width={barWidth}
                  height={errorHeight}
                  rx="0.3"
                  fill="var(--color-danger)"
                />
              ) : null}
            </g>
          );
        })}
      </svg>

      <div className="flex items-center justify-between text-[11px] text-[var(--color-ink-subtle)]">
        <span>{formatHour(points[0]?.bucket)}</span>
        <span className="text-[var(--color-ink-muted)]">
          {active
            ? `${formatHour(active.bucket)} · ${active.total} request${active.total === 1 ? "" : "s"}` +
              (active.errors ? ` · ${active.errors} failed` : "")
            : `peak ${max}/h`}
        </span>
        <span>now</span>
      </div>
    </div>
  );
}

function formatHour(bucket: string | undefined): string {
  if (!bucket) return "";
  // The backend sends naive UTC hour buckets.
  const date = new Date(`${bucket}Z`);
  return date.toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit" });
}
