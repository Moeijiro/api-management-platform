import { createContext, useContext } from "react";
import type { User } from "@/lib/types";

export interface AuthValue {
  user: User | null;
  loading: boolean;
  registrationEnabled: boolean;
  defaultRateLimit: number;
  setUser: (user: User | null) => void;
  logout: () => Promise<void>;
}

/** Split from the provider so this module exports no components. */
export const AuthContext = createContext<AuthValue | null>(null);

export function useAuth(): AuthValue {
  const value = useContext(AuthContext);
  if (!value) throw new Error("useAuth must be used inside <AuthProvider>");
  return value;
}
