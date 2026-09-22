import { useState } from "react";
import { BookOpen, ExternalLink, Play } from "lucide-react";
import { api } from "@/lib/api";
import { PageHeader } from "@/components/PageHeader";
import { CodeBlock } from "@/components/CodeBlock";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { Field, Input } from "@/components/ui/Field";

const BASE = "http://localhost:8000";
const SAMPLE_KEY = "dev_live_xxxxxxxxxxxxxxxxxxxx";

const ENDPOINTS = [
  { method: "GET", path: "/v1/status", description: "Liveness check; confirms the key works." },
  { method: "GET", path: "/v1/profile", description: "Describes the key that made the call." },
  { method: "POST", path: "/v1/process", description: "Transforms a string (upper, lower, reverse, word_count)." },
  { method: "GET", path: "/v1/random", description: "A random integer between ?minimum and ?maximum." },
];

const SNIPPETS: Record<string, (key: string) => string> = {
  curl: (key) => `curl ${BASE}/v1/status \\
  -H "X-API-Key: ${key}"`,
  python: (key) => `import httpx

response = httpx.get(
    "${BASE}/v1/status",
    headers={"X-API-Key": "${key}"},
)
response.raise_for_status()
print(response.json())
print("remaining:", response.headers["X-RateLimit-Remaining"])`,
  javascript: (key) => `const response = await fetch("${BASE}/v1/status", {
  headers: { "X-API-Key": "${key}" },
});

if (response.status === 429) {
  const retryAfter = response.headers.get("Retry-After");
  throw new Error(\`Rate limited, retry in \${retryAfter}s\`);
}

console.log(await response.json());`,
};

export function Documentation() {
  const [tab, setTab] = useState<keyof typeof SNIPPETS>("curl");
  const [key, setKey] = useState("");
  const [result, setResult] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const run = async () => {
    setBusy(true);
    try {
      const response = await api.tryEndpoint(key.trim());
      setResult(
        JSON.stringify(
          { status: response.status, rate_limit: response.rateLimit, body: response.body },
          null,
          2,
        ),
      );
    } catch (error) {
      setResult(String(error));
    } finally {
      setBusy(false);
    }
  };

  return (
    <>
      <PageHeader
        title="API documentation"
        description="How to authenticate, what the endpoints do, and what the errors look like."
        actions={
          <div className="flex gap-2">
            <a href={`${BASE}/docs`} target="_blank" rel="noreferrer">
              <Button size="sm">
                OpenAPI
                <ExternalLink className="h-3.5 w-3.5" />
              </Button>
            </a>
            <a href={`${BASE}/redoc`} target="_blank" rel="noreferrer">
              <Button size="sm">
                ReDoc
                <ExternalLink className="h-3.5 w-3.5" />
              </Button>
            </a>
          </div>
        }
      />

      <div className="grid gap-4 lg:grid-cols-5">
        <Card className="lg:col-span-3">
          <CardHeader
            title="Authentication"
            description="Send your key in the X-API-Key header on every /v1 request."
            icon={<BookOpen className="h-4 w-4" />}
          />
          <CardBody className="space-y-4">
            <div className="flex gap-1">
              {(Object.keys(SNIPPETS) as Array<keyof typeof SNIPPETS>).map((name) => (
                <button
                  key={name}
                  onClick={() => setTab(name)}
                  className={
                    tab === name
                      ? "rounded-md bg-[var(--color-surface-raised)] px-2.5 py-1 text-xs font-medium"
                      : "rounded-md px-2.5 py-1 text-xs text-[var(--color-ink-muted)] hover:text-[var(--color-ink)]"
                  }
                >
                  {name}
                </button>
              ))}
            </div>
            <CodeBlock value={SNIPPETS[tab](SAMPLE_KEY)} />
            <p className="text-xs text-[var(--color-ink-muted)]">
              Successful responses carry <code className="font-mono">X-RateLimit-Limit</code>,{" "}
              <code className="font-mono">X-RateLimit-Remaining</code> and{" "}
              <code className="font-mono">X-RateLimit-Reset</code>; a refused one adds{" "}
              <code className="font-mono">Retry-After</code>.
            </p>
          </CardBody>
        </Card>

        <Card className="lg:col-span-2">
          <CardHeader title="Try it" description="Runs against this instance, and is logged like any other call." icon={<Play className="h-4 w-4" />} />
          <CardBody className="space-y-3">
            <Field label="API key" hint="Paste a key you created — it is not stored by the dashboard.">
              <Input
                value={key}
                onChange={(event) => setKey(event.target.value)}
                placeholder="dev_live_…"
                className="font-mono text-xs"
              />
            </Field>
            <Button variant="primary" size="sm" onClick={run} loading={busy} disabled={!key.trim()}>
              GET /v1/status
            </Button>
            {result ? <CodeBlock value={result} label="Response" /> : null}
          </CardBody>
        </Card>
      </div>

      <Card className="mt-4">
        <CardHeader title="Endpoints" description="The protected demo API." />
        <div className="divide-y divide-[var(--color-border)]">
          {ENDPOINTS.map((endpoint) => (
            <div key={endpoint.path} className="flex flex-wrap items-center gap-3 px-5 py-3">
              <Badge tone="accent" className="font-mono">
                {endpoint.method}
              </Badge>
              <span className="font-mono text-xs">{endpoint.path}</span>
              <span className="text-xs text-[var(--color-ink-muted)]">{endpoint.description}</span>
            </div>
          ))}
        </div>
      </Card>

      <Card className="mt-4">
        <CardHeader title="Errors" description="Every failure uses the same envelope, so one branch handles them all." />
        <CardBody className="grid gap-3 md:grid-cols-2">
          <CodeBlock
            label="401 · invalid key"
            value={`{
  "error": {
    "code": "invalid_api_key",
    "message": "The supplied API key is invalid or has been revoked."
  }
}`}
          />
          <CodeBlock
            label="429 · quota exceeded"
            value={`{
  "error": {
    "code": "rate_limit_exceeded",
    "message": "Rate limit of 60 requests per minute exceeded for this API key."
  }
}`}
          />
        </CardBody>
      </Card>
    </>
  );
}
