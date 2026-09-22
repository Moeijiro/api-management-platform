import { Link } from "react-router-dom";
import { Activity, ArrowRight } from "lucide-react";
import { api } from "@/lib/api";
import { useAsync } from "@/hooks/useAsync";
import { PageHeader } from "@/components/PageHeader";
import { StatTile } from "@/components/StatTile";
import { UsageChart } from "@/components/UsageChart";
import { StatusBadge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { EmptyState, ErrorNote, Spinner } from "@/components/ui/Feedback";
import { clockTime, formatNumber } from "@/lib/utils";

export function Dashboard() {
  const usage = useAsync(() => api.usage(), []);
  const recent = useAsync(() => api.logs({ limit: 6 }), []);

  return (
    <>
      <PageHeader
        title="Overview"
        description="Every figure is a query over your own request logs — nothing is seeded."
        actions={
          <Link to="/logs">
            <Button size="sm">
              Request logs
              <ArrowRight className="h-3.5 w-3.5" />
            </Button>
          </Link>
        }
      />

      {usage.error ? <ErrorNote message={usage.error} /> : null}
      {usage.loading ? <Spinner label="Loading usage" /> : null}

      {usage.data ? (
        <>
          <div className="mb-4 grid grid-cols-2 gap-3 lg:grid-cols-5">
            <StatTile
              label="Requests today"
              value={formatNumber(usage.data.requests_today)}
              hint={`${formatNumber(usage.data.requests_this_month)} this month`}
            />
            <StatTile
              label="Total requests"
              value={formatNumber(usage.data.requests_total)}
            />
            <StatTile
              label="Success rate"
              value={usage.data.success_rate !== null ? `${usage.data.success_rate}%` : "—"}
              hint={
                usage.data.rate_limited_today
                  ? `${usage.data.rate_limited_today} rate limited today`
                  : undefined
              }
            />
            <StatTile
              label="Avg response"
              value={
                usage.data.avg_response_time_ms !== null
                  ? `${usage.data.avg_response_time_ms} ms`
                  : "—"
              }
            />
            <StatTile
              label="Active keys"
              value={usage.data.active_keys}
              hint={`${usage.data.total_keys} total`}
            />
          </div>

          <Card className="mb-4">
            <CardHeader
              title="Requests per hour"
              description="The last 24 hours. Failed requests are stacked in red."
              icon={<Activity className="h-4 w-4" />}
            />
            <CardBody>
              <UsageChart points={usage.data.series} />
            </CardBody>
          </Card>
        </>
      ) : null}

      <div className="grid gap-4 lg:grid-cols-5">
        <Card className="lg:col-span-3">
          <CardHeader
            title="Recent requests"
            action={
              <Link
                to="/logs"
                className="text-xs text-[var(--color-ink-muted)] hover:text-[var(--color-ink)]"
              >
                All logs
              </Link>
            }
          />
          {recent.loading ? (
            <Spinner />
          ) : recent.data && recent.data.items.length > 0 ? (
            <div className="divide-y divide-[var(--color-border)]">
              {recent.data.items.map((log) => (
                <div key={log.id} className="flex items-center gap-3 px-5 py-2.5 text-sm">
                  <StatusBadge status={log.status_code} />
                  <span className="w-12 shrink-0 font-mono text-[11px] text-[var(--color-ink-muted)]">
                    {log.method}
                  </span>
                  <span className="min-w-0 flex-1 truncate font-mono text-xs">{log.path}</span>
                  <span className="shrink-0 font-mono text-[11px] text-[var(--color-ink-muted)]">
                    {log.response_time_ms} ms
                  </span>
                  <span className="hidden shrink-0 text-[11px] text-[var(--color-ink-subtle)] sm:block">
                    {clockTime(log.created_at)}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <EmptyState
              title="No requests yet"
              hint="Create an API key and call /v1/status to see traffic here."
            />
          )}
        </Card>

        <Card className="lg:col-span-2">
          <CardHeader title="Top endpoints" description="Busiest paths, with their average latency." />
          {usage.data && usage.data.top_endpoints.length > 0 ? (
            <div className="divide-y divide-[var(--color-border)]">
              {usage.data.top_endpoints.map((endpoint) => (
                <div
                  key={`${endpoint.method} ${endpoint.path}`}
                  className="flex items-center gap-3 px-5 py-2.5"
                >
                  <span className="w-10 shrink-0 font-mono text-[11px] text-[var(--color-ink-muted)]">
                    {endpoint.method}
                  </span>
                  <span className="min-w-0 flex-1 truncate font-mono text-xs">{endpoint.path}</span>
                  <span className="shrink-0 text-xs tabular-nums">{endpoint.requests}</span>
                  <span className="hidden shrink-0 font-mono text-[11px] text-[var(--color-ink-subtle)] sm:block">
                    {endpoint.avg_response_time_ms} ms
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <EmptyState title="Nothing yet" />
          )}
        </Card>
      </div>
    </>
  );
}
