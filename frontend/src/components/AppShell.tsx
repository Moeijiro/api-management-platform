import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { BookOpen, KeyRound, LayoutDashboard, LogOut, ScrollText, Settings, Zap } from "lucide-react";
import { useAuth } from "@/context/auth-context";
import { cn } from "@/lib/utils";

const NAV = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { to: "/keys", label: "API keys", icon: KeyRound },
  { to: "/logs", label: "Request logs", icon: ScrollText },
  { to: "/docs", label: "Documentation", icon: BookOpen },
  { to: "/settings", label: "Settings", icon: Settings },
];

export function AppShell() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  return (
    <div className="relative z-10 flex min-h-full flex-col md:flex-row">
      <aside className="flex shrink-0 flex-col gap-6 border-b border-[var(--color-border)] bg-[var(--color-surface)]/70 px-4 py-4 md:w-56 md:border-b-0 md:border-r md:py-6">
        <div className="flex items-center gap-2.5">
          <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-[var(--color-accent)]">
            <Zap className="h-4 w-4 text-[var(--color-accent-ink)]" />
          </span>
          <div className="leading-tight">
            <p className="text-sm font-semibold tracking-tight">API Platform</p>
            <p className="text-[11px] text-[var(--color-ink-subtle)]">developer console</p>
          </div>
        </div>

        <nav className="flex flex-wrap gap-1 md:flex-1 md:flex-col md:flex-nowrap">
          {NAV.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                cn(
                  "flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm transition-colors",
                  isActive
                    ? "bg-[var(--color-surface-raised)] text-[var(--color-ink)]"
                    : "text-[var(--color-ink-muted)] hover:bg-[var(--color-surface-raised)]/60 hover:text-[var(--color-ink)]",
                )
              }
            >
              <Icon className="h-4 w-4" />
              {label}
            </NavLink>
          ))}
        </nav>

        <div className="hidden items-center gap-2 rounded-lg border border-[var(--color-border)] px-3 py-2 md:flex">
          <div className="min-w-0 flex-1 leading-tight">
            <p className="truncate text-xs font-medium">{user?.email}</p>
            <p className="text-[11px] text-[var(--color-ink-subtle)]">signed in</p>
          </div>
          <button
            onClick={async () => {
              await logout();
              navigate("/login");
            }}
            aria-label="Sign out"
            className="rounded-md p-1.5 text-[var(--color-ink-subtle)] transition-colors hover:bg-[var(--color-surface-raised)] hover:text-[var(--color-ink)]"
          >
            <LogOut className="h-3.5 w-3.5" />
          </button>
        </div>
      </aside>

      <main className="min-w-0 flex-1">
        <div className="mx-auto w-full max-w-5xl px-4 py-6 sm:px-6 md:py-10">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
