import { useState } from "react";
import { ScrollText } from "lucide-react";
import { api } from "@/lib/api";
import { useAsync } from "@/hooks/useAsync";
import { PageHeader } from "@/components/PageHeader";
import { StatusBadge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardHeader } from "@/components/ui/Card";
import { EmptyState, ErrorNote, Spinner } from "@/components/ui/Feedback";
import { Select } from "@/components/ui/Field";
import { absoluteTime, clockTime } from "@/lib/utils";

const PAGE_SIZE = 25;

export function Logs() {
  const [statusClass, setStatusClass] = useState("");
  const [method, setMethod] = useState("");
  const [keyId, setKeyId] = useState("");
  const [offset, setOffset] = useState(0);

  const keys = useAsync(() => api.keys(), []);
  const page = useAsync(
    () =>
      api.logs({
        limit: PAGE_SIZE,
        offset,
        status_class: statusClass || undefined,
        method: method || undefined,
        api_key_id: keyId ? Number(keyId) : undefined,
      }),
    [offset, statusClass, method, keyId],
  );

  const total = page.data?.total ?? 0;
  const pages = Math.max(1, Math.ceil(total / PAGE_SIZE));
  const current = Math.floor(offset / PAGE_SIZE) + 1;

  const filter = (setter: (value: string) => void) => (event: React.ChangeEvent<HTMLSelectElement>) => {
    setter(event.target.value);
    setOffset(0);
  };

  return (
    <>
      <PageHeader
        title="Request logs"
        description="Every call to /v1, including the ones that were refused."
      />

      {/* Filters live on their own row: three selects crowd a page header. */}
      <div className="mb-4 flex flex-wrap gap-2">
        <Select aria-label="Filter by status" className="w-32" value={statusClass} onChange={filter(setStatusClass)}>
          <option value="">Any status</option>
          <option value="2xx">2xx</option>
          <option value="4xx">4xx</option>
          <option value="5xx">5xx</option>
        </Select>
        <Select aria-label="Filter by method" className="w-32" value={method} onChange={filter(setMethod)}>
          <option value="">Any method</option>
          {["GET", "POST", "PUT", "PATCH", "DELETE"].map((verb) => (
            <option key={verb} value={verb}>
              {verb}
            </option>
          ))}
        </Select>
        <Select aria-label="Filter by API key" className="w-44" value={keyId} onChange={filter(setKeyId)}>
          <option value="">All keys</option>
          {keys.data?.map((key) => (
            <option key={key.id} value={key.id}>
              {key.name}
            </option>
          ))}
        </Select>
      </div>

      {page.error ? <ErrorNote message={page.error} /> : null}

      <Card>
        <CardHeader
          title={`${total.toLocaleString("en-US")} request${total === 1 ? "" : "s"}`}
          icon={<ScrollText className="h-4 w-4" />}
        />
        {page.loading ? <Spinner /> : null}
        {page.data && page.data.items.length === 0 && !page.loading ? (
          <EmptyState title="No matching requests" hint="Adjust the filters, or call the API." />
        ) : null}
        {page.data && page.data.items.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[46rem] border-collapse text-sm">
              <thead>
                <tr className="text-left text-[11px] uppercase tracking-wide text-[var(--color-ink-subtle)]">
                  <th className="px-5 py-2.5 font-medium">Time</th>
                  <th className="px-5 py-2.5 font-medium">Method</th>
                  <th className="px-5 py-2.5 font-medium">Endpoint</th>
                  <th className="px-5 py-2.5 font-medium">Status</th>
                  <th className="px-5 py-2.5 font-medium">Time</th>
                  <th className="px-5 py-2.5 font-medium">API key</th>
                </tr>
              </thead>
              <tbody>
                {page.data.items.map((log) => (
                  <tr key={log.id} className="border-t border-[var(--color-border)]">
                    <td
                      className="whitespace-nowrap px-5 py-2.5 font-mono text-[11px] text-[var(--color-ink-muted)]"
                      title={absoluteTime(log.created_at)}
                    >
                      {clockTime(log.created_at)}
                    </td>
                    <td className="px-5 py-2.5 font-mono text-[11px]">{log.method}</td>
                    <td className="px-5 py-2.5 font-mono text-xs">
                      {log.path}
                      {log.error_code ? (
                        <span className="ml-2 text-[11px] text-[var(--color-ink-subtle)]">
                          {log.error_code}
                        </span>
                      ) : null}
                    </td>
                    <td className="px-5 py-2.5">
                      <StatusBadge status={log.status_code} />
                    </td>
                    <td className="px-5 py-2.5 font-mono text-[11px] tabular-nums text-[var(--color-ink-muted)]">
                      {log.response_time_ms} ms
                    </td>
                    <td className="max-w-[12rem] truncate px-5 py-2.5 text-xs text-[var(--color-ink-muted)]">
                      {log.api_key_label ?? "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}
      </Card>

      {pages > 1 ? (
        <div className="mt-4 flex items-center justify-between text-xs text-[var(--color-ink-muted)]">
          <span>
            Page {current} of {pages}
          </span>
          <div className="flex gap-2">
            <Button size="sm" disabled={offset === 0} onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))}>
              Previous
            </Button>
            <Button
              size="sm"
              disabled={offset + PAGE_SIZE >= total}
              onClick={() => setOffset(offset + PAGE_SIZE)}
            >
              Next
            </Button>
          </div>
        </div>
      ) : null}
    </>
  );
}
