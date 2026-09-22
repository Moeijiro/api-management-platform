/** Mirrors the Pydantic schemas served by the FastAPI backend. */

export interface User {
  id: number;
  email: string;
  created_at: string;
}

export interface ApiKey {
  id: number;
  name: string;
  prefix: string;
  enabled: boolean;
  rate_limit_per_minute: number;
  created_at: string;
  last_used_at: string | null;
  revoked_at: string | null;
}

export interface CreatedApiKey extends ApiKey {
  key: string;
  warning: string;
}

export interface RequestLog {
  id: number;
  api_key_id: number | null;
  api_key_label: string | null;
  method: string;
  path: string;
  status_code: number;
  response_time_us: number;
  response_time_ms: number;
  client_ip: string | null;
  error_code: string | null;
  created_at: string;
}

export interface RequestLogPage {
  items: RequestLog[];
  total: number;
  limit: number;
  offset: number;
}

export interface UsagePoint {
  bucket: string;
  total: number;
  errors: number;
}

export interface EndpointUsage {
  path: string;
  method: string;
  requests: number;
  avg_response_time_ms: number;
}

export interface UsageOverview {
  requests_today: number;
  requests_this_month: number;
  requests_total: number;
  success_rate: number | null;
  avg_response_time_ms: number | null;
  active_keys: number;
  total_keys: number;
  rate_limited_today: number;
  series: UsagePoint[];
  top_endpoints: EndpointUsage[];
}

export interface ApiErrorBody {
  error: {
    code: string;
    message: string;
    fields?: { field: string; message: string }[];
  };
}
