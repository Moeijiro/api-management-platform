import { useState } from "react";
import { KeyRound, Plus, ShieldOff, Trash2 } from "lucide-react";
import { api } from "@/lib/api";
import { useAsync } from "@/hooks/useAsync";
import { useAuth } from "@/context/auth-context";
import { PageHeader } from "@/components/PageHeader";
import { CodeBlock } from "@/components/CodeBlock";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { EmptyState, ErrorNote, Spinner } from "@/components/ui/Feedback";
import { Field, Input } from "@/components/ui/Field";
import { absoluteTime, relativeTime } from "@/lib/utils";
import type { CreatedApiKey } from "@/lib/types";

export function ApiKeys() {
  const { defaultRateLimit } = useAuth();
  const { data, error, loading, reload } = useAsync(() => api.keys(), []);
  const [name, setName] = useState("");
  const [rateLimit, setRateLimit] = useState("");
  const [created, setCreated] = useState<CreatedApiKey | null>(null);
  const [busy, setBusy] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const create = async () => {
    setBusy(true);
    setFormError(null);
    try {
      setCreated(await api.createKey(name, rateLimit ? Number(rateLimit) : undefined));
      setName("");
      setRateLimit("");
      reload();
    } catch (err) {
      setFormError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  };

  const revoke = async (id: number, keyName: string) => {
    if (!confirm(`Revoke "${keyName}"? Calls using it stop working immediately.`)) return;
    await api.revokeKey(id).catch((err: Error) => setFormError(err.message));
    reload();
  };

  const remove = async (id: number, keyName: string) => {
    if (!confirm(`Delete "${keyName}"? Its request logs are kept.`)) return;
    await api.deleteKey(id).catch((err: Error) => setFormError(err.message));
    reload();
  };

  return (
    <>
      <PageHeader
        title="API keys"
        description="Keys authenticate the /v1 API. Only a SHA-256 digest is stored."
      />

      {error ? <ErrorNote message={error} /> : null}

      {created ? (
        <Card className="mb-4 border-[#343c73]">
          <CardHeader
            title="Copy your key now"
            description={created.warning}
            icon={<KeyRound className="h-4 w-4" />}
            action={
              <Button size="sm" variant="ghost" onClick={() => setCreated(null)}>
                Done
              </Button>
            }
          />
          <CardBody className="space-y-3">
            <CodeBlock value={created.key} />
            <CodeBlock
              label="Try it"
              value={`curl http://localhost:8000/v1/status \\\n  -H "X-API-Key: ${created.key}"`}
            />
          </CardBody>
        </Card>
      ) : null}

      <Card className="mb-4">
        <CardHeader title="Create a key" />
        <CardBody className="flex flex-wrap items-end gap-3">
          <div className="min-w-52 flex-1">
            <Field label="Name" hint="Where this key will be used.">
              <Input
                value={name}
                onChange={(event) => setName(event.target.value)}
                placeholder="Production backend"
                maxLength={64}
              />
            </Field>
          </div>
          <div className="w-40">
            <Field label="Rate limit" hint={`Default ${defaultRateLimit}/min.`}>
              <Input
                type="number"
                min={1}
                value={rateLimit}
                onChange={(event) => setRateLimit(event.target.value)}
                placeholder={String(defaultRateLimit)}
              />
            </Field>
          </div>
          <Button variant="primary" onClick={create} loading={busy} disabled={!name}>
            <Plus className="h-3.5 w-3.5" />
            Create key
          </Button>
        </CardBody>
        {formError ? (
          <CardBody className="pt-0">
            <ErrorNote message={formError} />
          </CardBody>
        ) : null}
      </Card>

      <Card>
        <CardHeader title="Your keys" description="A revoked key keeps its history and stays listed." />
        {loading ? <Spinner /> : null}
        {data && data.length === 0 ? (
          <EmptyState title="No API keys yet" hint="Create one to start calling the /v1 API." />
        ) : null}
        {data && data.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[42rem] border-collapse text-sm">
              <thead>
                <tr className="text-left text-[11px] uppercase tracking-wide text-[var(--color-ink-subtle)]">
                  <th className="px-5 py-2.5 font-medium">Name</th>
                  <th className="px-5 py-2.5 font-medium">Prefix</th>
                  <th className="px-5 py-2.5 font-medium">Limit</th>
                  <th className="px-5 py-2.5 font-medium">Last used</th>
                  <th className="px-5 py-2.5 font-medium">Status</th>
                  <th className="px-5 py-2.5" />
                </tr>
              </thead>
              <tbody>
                {data.map((key) => (
                  <tr key={key.id} className="border-t border-[var(--color-border)]">
                    <td className="px-5 py-3">
                      <p className="font-medium">{key.name}</p>
                      <p className="text-[11px] text-[var(--color-ink-subtle)]">
                        created {absoluteTime(key.created_at)}
                      </p>
                    </td>
                    <td className="px-5 py-3 font-mono text-xs text-[var(--color-ink-muted)]">
                      {key.prefix}…
                    </td>
                    <td className="px-5 py-3 font-mono text-xs tabular-nums">
                      {key.rate_limit_per_minute}/min
                    </td>
                    <td className="px-5 py-3 text-xs text-[var(--color-ink-muted)]">
                      {relativeTime(key.last_used_at)}
                    </td>
                    <td className="px-5 py-3">
                      {key.enabled ? (
                        <Badge tone="positive">active</Badge>
                      ) : (
                        <Badge tone="neutral">revoked</Badge>
                      )}
                    </td>
                    <td className="px-5 py-3">
                      <div className="flex justify-end gap-1">
                        {key.enabled ? (
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => revoke(key.id, key.name)}
                            aria-label={`Revoke ${key.name}`}
                          >
                            <ShieldOff className="h-3.5 w-3.5" />
                            Revoke
                          </Button>
                        ) : null}
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => remove(key.id, key.name)}
                          aria-label={`Delete ${key.name}`}
                        >
                          <Trash2 className="h-3.5 w-3.5" />
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}
      </Card>
    </>
  );
}
