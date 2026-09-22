import { useCallback, useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import { api } from "@/lib/api";
import type { User } from "@/lib/types";
import { AuthContext, type AuthValue } from "@/context/auth-context";

/** Resolves the session once at boot; `user === null` then means signed out. */
export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [registrationEnabled, setRegistrationEnabled] = useState(true);
  const [defaultRateLimit, setDefaultRateLimit] = useState(60);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    const config = await api.authConfig().catch(() => null);
    if (config) {
      setRegistrationEnabled(config.registration_enabled);
      setDefaultRateLimit(config.default_rate_limit_per_minute);
    }
    // A 401 here is the normal signed-out case, not an error to surface.
    setUser(await api.me().catch(() => null));
    setLoading(false);
  }, []);

  useEffect(() => {
    // oxlint-disable-next-line react/set-state-in-effect
    void load();
  }, [load]);

  const value = useMemo<AuthValue>(
    () => ({
      user,
      loading,
      registrationEnabled,
      defaultRateLimit,
      setUser,
      logout: async () => {
        await api.logout().catch(() => undefined);
        setUser(null);
      },
    }),
    [user, loading, registrationEnabled, defaultRateLimit],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
