import { useState } from "react";
import { Navigate } from "react-router-dom";
import { Zap } from "lucide-react";
import { api } from "@/lib/api";
import { useAuth } from "@/context/auth-context";
import { Button } from "@/components/ui/Button";
import { ErrorNote, Spinner } from "@/components/ui/Feedback";
import { Field, Input } from "@/components/ui/Field";

const POINTS = [
  "Keys are hashed — the raw value is shown once, at creation",
  "Every /v1 request is authenticated, rate limited and logged",
  "Usage figures are queries over your own request logs",
];

export function Login() {
  const { user, loading, registrationEnabled, setUser } = useAuth();
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  if (loading) return <Spinner label="Checking session" />;
  if (user) return <Navigate to="/dashboard" replace />;

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      setUser(
        mode === "login"
          ? await api.login(email, password)
          : await api.register(email, password),
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="relative z-10 flex min-h-full items-center justify-center px-4 py-12">
      <div className="w-full max-w-sm">
        <div className="mb-8 text-center">
          <span className="mx-auto mb-4 flex h-11 w-11 items-center justify-center rounded-xl bg-[var(--color-accent)]">
            <Zap className="h-5 w-5 text-[var(--color-accent-ink)]" />
          </span>
          <h1 className="text-lg font-semibold tracking-tight">API Management Platform</h1>
          <p className="mt-1.5 text-sm text-[var(--color-ink-muted)]">
            Issue API keys, call a protected API with them, and see exactly what happened.
          </p>
        </div>

        <form onSubmit={submit} className="space-y-4">
          {error ? <ErrorNote message={error} /> : null}
          <Field label="Email">
            <Input
              type="email"
              autoComplete="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              placeholder="you@example.com"
              required
            />
          </Field>
          <Field label="Password" hint={mode === "register" ? "At least 10 characters." : undefined}>
            <Input
              type="password"
              autoComplete={mode === "login" ? "current-password" : "new-password"}
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              required
            />
          </Field>
          <Button type="submit" variant="primary" className="w-full" loading={busy}>
            {mode === "login" ? "Sign in" : "Create account"}
          </Button>
        </form>

        {registrationEnabled ? (
          <p className="mt-4 text-center text-xs text-[var(--color-ink-muted)]">
            {mode === "login" ? "No account yet?" : "Already have an account?"}{" "}
            <button
              type="button"
              onClick={() => {
                setMode(mode === "login" ? "register" : "login");
                setError(null);
              }}
              className="text-[var(--color-accent)] hover:underline"
            >
              {mode === "login" ? "Register" : "Sign in"}
            </button>
          </p>
        ) : null}

        <ul className="mt-8 space-y-2 border-t border-[var(--color-border)] pt-6">
          {POINTS.map((point) => (
            <li key={point} className="flex gap-2 text-xs text-[var(--color-ink-muted)]">
              <span className="text-[var(--color-accent)]">·</span>
              {point}
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
