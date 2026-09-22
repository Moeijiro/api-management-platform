import { useNavigate } from "react-router-dom";
import { LogOut, ShieldCheck, SlidersHorizontal } from "lucide-react";
import { api } from "@/lib/api";
import { useAsync } from "@/hooks/useAsync";
import { useAuth } from "@/context/auth-context";
import { PageHeader } from "@/components/PageHeader";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { absoluteTime } from "@/lib/utils";

export function Settings() {
  const { user, defaultRateLimit, logout } = useAuth();
  const navigate = useNavigate();
  const usage = useAsync(() => api.usage(), []);

  return (
    <>
      <PageHeader title="Settings" description="Your account and how this instance is configured." />

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader title="Account" icon={<ShieldCheck className="h-4 w-4" />} />
          <CardBody className="space-y-4 text-xs">
            <Row label="Email">{user?.email}</Row>
            <Row label="Member since">{absoluteTime(user?.created_at ?? null)}</Row>
            <Row label="Password">
              <Badge tone="positive">scrypt, salted</Badge>
            </Row>
            <Row label="Session">HttpOnly cookie, signed (JWT)</Row>
            <p className="leading-relaxed text-[var(--color-ink-muted)]">
              API keys cannot reach the management API — a leaked key can call{" "}
              <code className="font-mono">/v1</code> and nothing else.
            </p>
            <Button
              variant="danger"
              size="sm"
              onClick={async () => {
                await logout();
                navigate("/login");
              }}
            >
              <LogOut className="h-3.5 w-3.5" />
              Sign out
            </Button>
          </CardBody>
        </Card>

        <Card>
          <CardHeader title="Limits" icon={<SlidersHorizontal className="h-4 w-4" />} />
          <CardBody className="space-y-4 text-xs">
            <Row label="Default rate limit">{defaultRateLimit} requests / minute</Row>
            <Row label="Window">60 seconds, sliding</Row>
            <Row label="Active keys">
              {usage.data ? `${usage.data.active_keys} of ${usage.data.total_keys}` : "—"}
            </Row>
            <Row label="Rate limited today">{usage.data?.rate_limited_today ?? "—"}</Row>
            <p className="leading-relaxed text-[var(--color-ink-muted)]">
              Each key can be given its own quota when it is created. Limits are enforced per
              key, so one noisy integration cannot spend another one's budget.
            </p>
          </CardBody>
        </Card>
      </div>
    </>
  );
}

function Row({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex items-center justify-between gap-4 border-b border-[var(--color-border)] pb-2.5 last:border-0">
      <span className="text-[var(--color-ink-subtle)]">{label}</span>
      <span className="text-right">{children}</span>
    </div>
  );
}
