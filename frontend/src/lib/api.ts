/**
 * One fetch wrapper for the dashboard.
 *
 * The session is an HttpOnly cookie, so requests only need `credentials:
 * "include"`. API keys are never stored in the browser — they authenticate
 * `/v1`, and the dashboard shows a key exactly once, right after it is made.
 */

import type {
  ApiErrorBody,
  ApiKey,
  CreatedApiKey,
  RequestLogPage,
  UsageOverview,
  User,
} from "./types";

const BASE = import.meta.env.VITE_API_BASE_URL ?? "";

export class ApiError extends Error {
  status: number;
  code: string;

  constructor(status: number, code: string, message: string) {
    super(message);
    this.status = status;
    this.code = code;
  }
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch(`${BASE}${path}`, {
    credentials: "include",
    headers: init.body ? { "Content-Type": "application/json" } : undefined,
    ...init,
  });

  if (response.status === 204) return undefined as T;

  const payload = await response.json().catch(() => null);
  if (!response.ok) {
    // Every backend error uses the same envelope, so one branch handles them all.
    const body = payload as ApiErrorBody | null;
    const fields = body?.error?.fields?.map((f) => `${f.field}: ${f.message}`).join("; ");
    throw new ApiError(
      response.status,
      body?.error?.code ?? "error",
      fields || body?.error?.message || response.statusText,
    );
  }
  return payload as T;
}

export interface LogQuery {
  limit?: number;
  offset?: number;
  status?: number;
  status_class?: string;
  method?: string;
  api_key_id?: number;
}

function query(params: Record<string, unknown>): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== "" && value !== null) search.set(key, String(value));
  }
  const text = search.toString();
  return text ? `?${text}` : "";
}

export const api = {
  authConfig: () =>
    request<{ registration_enabled: boolean; default_rate_limit_per_minute: number }>(
      "/auth/config",
    ),
  me: () => request<User>("/auth/me"),
  register: (email: string, password: string) =>
    request<User>("/auth/register", { method: "POST", body: JSON.stringify({ email, password }) }),
  login: (email: string, password: string) =>
    request<User>("/auth/login", { method: "POST", body: JSON.stringify({ email, password }) }),
  logout: () => request<void>("/auth/logout", { method: "POST" }),

  keys: () => request<ApiKey[]>("/api/keys"),
  createKey: (name: string, rateLimit?: number) =>
    request<CreatedApiKey>("/api/keys", {
      method: "POST",
      body: JSON.stringify({ name, rate_limit_per_minute: rateLimit ?? null }),
    }),
  revokeKey: (id: number) => request<ApiKey>(`/api/keys/${id}/revoke`, { method: "POST" }),
  deleteKey: (id: number) => request<void>(`/api/keys/${id}`, { method: "DELETE" }),

  logs: (params: LogQuery = {}) => request<RequestLogPage>(`/api/logs${query(params)}`),
  usage: () => request<UsageOverview>("/api/usage"),

  /** Used by the documentation page to run the example against /v1 live. */
  tryEndpoint: async (key: string) => {
    const response = await fetch(`${BASE}/v1/status`, { headers: { "X-API-Key": key } });
    return {
      status: response.status,
      rateLimit: {
        limit: response.headers.get("X-RateLimit-Limit"),
        remaining: response.headers.get("X-RateLimit-Remaining"),
        reset: response.headers.get("X-RateLimit-Reset"),
      },
      body: await response.json().catch(() => null),
    };
  },
};
